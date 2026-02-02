"""
Async website checker (advanced-but-practical version).

Features:
- True asyncio orchestration + bounded concurrency
- Blocking HTTP via requests executed in a dedicated ThreadPoolExecutor
- Per-request timeout + overall batch timeout
- Response time per website
- Lists which websites were too slow (batch timeout)
- Robust error handling, structured results, logging, small CLI
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum
from time import perf_counter
from typing import Iterable, Mapping

import requests
from requests import Response
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class Outcome(str, Enum):
    OK = "ok"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass(slots=True, frozen=True)
class WebsiteResult:
    url: str
    outcome: Outcome
    status: int | None
    reason: str
    response_time: float  # seconds


@dataclass(slots=True, frozen=True)
class CheckerConfig:
    request_timeout: float = 5.0  # per-website HTTP timeout (seconds)
    batch_timeout: float = 5.0  # overall wall-clock timeout (seconds)
    concurrency: int = 20  # max parallel checks
    retries: int = 1  # retry count for transient failures
    user_agent: str = "website-checker/1.0"


_thread_local = threading.local()


def normalize_url(url: str) -> str:
    return url if url.startswith(("http://", "https://")) else f"https://{url}"


def _build_session(*, retries: int, user_agent: str) -> requests.Session:
    session = requests.Session()

    retry = Retry(
        total=retries,
        backoff_factor=0.2,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET", "HEAD"),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=50, pool_maxsize=50)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    session.headers.update({"User-Agent": user_agent})
    return session


def _get_session(config: CheckerConfig) -> requests.Session:
    """
    One Session per thread (thread-local) so we get connection pooling safely.
    """
    session = getattr(_thread_local, "session", None)
    if session is None:
        session = _build_session(retries=config.retries, user_agent=config.user_agent)
        _thread_local.session = session
    return session


def _sync_get(url: str, config: CheckerConfig) -> Response:
    session = _get_session(config)
    return session.get(url, timeout=config.request_timeout)


async def _run_with_optional_timeout(coro: asyncio.Future, timeout_s: float):
    """
    Uses asyncio.timeout on Python 3.11+, otherwise falls back to wait_for.
    """
    timeout_cm = getattr(asyncio, "timeout", None)
    if timeout_cm is not None:
        async with timeout_cm(timeout_s):
            return await coro
    return await asyncio.wait_for(coro, timeout=timeout_s)


class WebsiteChecker:
    def __init__(self, config: CheckerConfig, logger: logging.Logger | None = None) -> None:
        self._config = config
        self._log = logger or logging.getLogger("website_checker")
        self._semaphore = asyncio.Semaphore(config.concurrency)
        self._executor = ThreadPoolExecutor(
            max_workers=config.concurrency,
            thread_name_prefix="website-check",
        )

    async def __aenter__(self) -> "WebsiteChecker":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        self._executor.shutdown(wait=True, cancel_futures=True)

    async def check_one(self, url: str) -> WebsiteResult:
        url = normalize_url(url)
        start = perf_counter()

        try:
            async with self._semaphore:
                loop = asyncio.get_running_loop()
                response: Response = await loop.run_in_executor(
                    self._executor, _sync_get, url, self._config
                )
            elapsed = perf_counter() - start
            return WebsiteResult(url, Outcome.OK, response.status_code, response.reason, elapsed)

        except requests.exceptions.Timeout:
            elapsed = perf_counter() - start
            return WebsiteResult(url, Outcome.TIMEOUT, None, "request timeout", elapsed)

        except (
                requests.exceptions.ConnectionError,
                requests.exceptions.InvalidURL,
                requests.exceptions.SSLError,
        ) as e:
            elapsed = perf_counter() - start
            return WebsiteResult(url, Outcome.ERROR, None, f"{type(e).__name__}: {e}", elapsed)

        except requests.exceptions.RequestException as e:
            elapsed = perf_counter() - start
            return WebsiteResult(url, Outcome.ERROR, None, f"{type(e).__name__}: {e}", elapsed)

        except Exception as e:
            elapsed = perf_counter() - start
            return WebsiteResult(url, Outcome.ERROR, None, f"{type(e).__name__}: {e}", elapsed)

    async def check_many(self, urls: Iterable[str]) -> list[WebsiteResult]:
        normalized = [normalize_url(u) for u in urls]
        tasks: dict[asyncio.Task[WebsiteResult], str] = {
            asyncio.create_task(self.check_one(u)): u for u in normalized
        }

        results: list[WebsiteResult] = []
        batch_start = perf_counter()

        async def collect_results() -> None:
            # Stream results as tasks complete
            for task in asyncio.as_completed(tasks.keys()):
                result = await task
                results.append(result)
                self._log.info(self.format_result(result, width=max(map(len, normalized), default=0)))

        try:
            await _run_with_optional_timeout(collect_results(), self._config.batch_timeout)

        except asyncio.TimeoutError:
            elapsed = perf_counter() - batch_start

            pending_tasks = [t for t in tasks if not t.done()]
            pending_urls = [tasks[t] for t in pending_tasks]

            for t in pending_tasks:
                t.cancel()
            await asyncio.gather(*pending_tasks, return_exceptions=True)

            width = max(map(len, normalized), default=0)
            for url in pending_urls:
                timeout_result = WebsiteResult(
                    url=url,
                    outcome=Outcome.TIMEOUT,
                    status=None,
                    reason=f"batch timeout (> {self._config.batch_timeout:.2f}s)",
                    response_time=elapsed,
                )
                results.append(timeout_result)
                self._log.info(self.format_result(timeout_result, width=width))

        return results

    @staticmethod
    def format_result(result: WebsiteResult, *, width: int) -> str:
        url = result.url.ljust(width)
        t = f"{result.response_time:.2f}s"

        if result.outcome is Outcome.OK:
            return f"{url}  ✅ ONLINE  ({result.status} {result.reason})  in {t}"
        if result.outcome is Outcome.TIMEOUT:
            return f"{url}  ⏱️ TIMEOUT ({result.reason})  after {t}"
        return f"{url}  ❌ ERROR   ({result.reason})  after {t}"


def print_summary(results: list[WebsiteResult]) -> None:
    ok = sum(r.outcome is Outcome.OK for r in results)
    timeouts = sum(r.outcome is Outcome.TIMEOUT for r in results)
    errors = sum(r.outcome is Outcome.ERROR for r in results)

    print("\nSummary:")
    print(f"  Online:   {ok}")
    print(f"  Timeouts: {timeouts}")
    print(f"  Errors:   {errors}")

    slowest = sorted(results, key=lambda r: r.response_time, reverse=True)[:3]
    if slowest:
        print("\nSlowest:")
        for r in slowest:
            print(f"  {r.url} ({r.response_time:.2f}s)")


def build_logger(verbose: bool) -> logging.Logger:
    logger = logging.getLogger("website_checker")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    handler.setFormatter(logging.Formatter("%(message)s"))

    logger.handlers.clear()
    logger.addHandler(handler)
    logger.propagate = False
    return logger


DEFAULT_URLS = [
    "www.indently.io",
    "www.apple.com",
    "www.facebook.com",
    "nonexistent-website-404.com",
    "www.instagram.com",
    "www.reddit.com",
    "www.wikipedia.org",
    "www.fail-website.com",
    "www.amazon.com",
    "www.linkedin.com",
    "www.microsoft.com",
    "www.github.com",
]


async def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Async website availability checker.")
    parser.add_argument("urls", nargs="*", help="Websites to check (e.g. example.com)")
    parser.add_argument("--request-timeout", type=float, default=5.0, help="Per-request timeout (seconds)")
    parser.add_argument("--batch-timeout", type=float, default=5.0, help="Overall timeout (seconds)")
    parser.add_argument("--concurrency", type=int, default=20, help="Max concurrent checks")
    parser.add_argument("--retries", type=int, default=1, help="Retries for transient errors")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    args = parser.parse_args(argv)

    urls = args.urls or DEFAULT_URLS
    print(f"Checking {len(urls)} websites...\n")

    logger = build_logger(args.verbose)
    config = CheckerConfig(
        request_timeout=args.request_timeout,
        batch_timeout=args.batch_timeout,
        concurrency=args.concurrency,
        retries=args.retries,
    )

    async with WebsiteChecker(config, logger) as checker:
        results = await checker.check_many(urls)

    print_summary(results)
    print("\nDone!")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
