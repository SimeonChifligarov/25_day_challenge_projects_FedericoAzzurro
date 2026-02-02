import asyncio
from dataclasses import dataclass
from time import perf_counter
from typing import Literal
import threading

import requests
from requests import Response

Outcome = Literal["ok", "timeout", "error"]

_DEFAULT_REQUEST_TIMEOUT = 5.0
_DEFAULT_BATCH_TIMEOUT = 5.0
_DEFAULT_CONCURRENCY = 20

_thread_local = threading.local()


def normalize_url(url: str) -> str:
    return url if url.startswith(("http://", "https://")) else f"https://{url}"


def _get_session() -> requests.Session:
    session = getattr(_thread_local, "session", None)
    if session is None:
        session = requests.Session()
        _thread_local.session = session
    return session


def _session_get(url: str, timeout: float) -> Response:
    return _get_session().get(url, timeout=timeout)


@dataclass(slots=True, frozen=True)
class WebsiteResponse:
    url: str
    outcome: Outcome
    status: int | None
    reason: str
    response_time: float  # seconds (total time for this task)


async def check_website(
        url: str,
        *,
        request_timeout: float,
        semaphore: asyncio.Semaphore,
) -> WebsiteResponse:
    start = perf_counter()

    try:
        async with semaphore:
            response: Response = await asyncio.to_thread(
                _session_get, url, request_timeout
            )
        elapsed = perf_counter() - start
        return WebsiteResponse(url, "ok", response.status_code, response.reason, elapsed)

    except requests.exceptions.Timeout:
        elapsed = perf_counter() - start
        return WebsiteResponse(url, "timeout", None, "request timeout", elapsed)

    except (
            requests.exceptions.ConnectionError,
            requests.exceptions.InvalidURL,
            requests.exceptions.SSLError,
    ) as e:
        elapsed = perf_counter() - start
        return WebsiteResponse(url, "error", None, f"{type(e).__name__}: {e}", elapsed)

    except requests.exceptions.RequestException as e:
        elapsed = perf_counter() - start
        return WebsiteResponse(url, "error", None, f"{type(e).__name__}: {e}", elapsed)

    except Exception as e:
        elapsed = perf_counter() - start
        return WebsiteResponse(url, "error", None, f"{type(e).__name__}: {e}", elapsed)


def _print_result(result: WebsiteResponse, url_width: int) -> None:
    url = result.url.ljust(url_width)
    t = f"{result.response_time:.2f}s"

    if result.outcome == "ok":
        print(f"{url}  ✅ ONLINE  ({result.status} {result.reason})  in {t}")
        return

    if result.outcome == "timeout":
        print(f"{url}  ⏱️ TIMEOUT ({result.reason})  after {t}")
        return

    print(f"{url}  ❌ ERROR   ({result.reason})  after {t}")


def _print_summary(results: list[WebsiteResponse]) -> None:
    ok = sum(r.outcome == "ok" for r in results)
    timeouts = sum(r.outcome == "timeout" for r in results)
    errors = sum(r.outcome == "error" for r in results)

    print("\nSummary:")
    print(f"  Online:   {ok}")
    print(f"  Timeouts: {timeouts}")
    print(f"  Errors:   {errors}")

    slowest = sorted(results, key=lambda r: r.response_time, reverse=True)[:3]
    if slowest:
        print("\nSlowest:")
        for r in slowest:
            print(f"  {r.url} ({r.response_time:.2f}s)")


async def check_websites(
        urls: list[str],
        *,
        request_timeout: float = _DEFAULT_REQUEST_TIMEOUT,
        batch_timeout: float = _DEFAULT_BATCH_TIMEOUT,
        concurrency: int = _DEFAULT_CONCURRENCY,
) -> None:
    normalized_urls = [normalize_url(u) for u in urls]
    url_width = max(len(u) for u in normalized_urls) if normalized_urls else 0

    semaphore = asyncio.Semaphore(concurrency)
    batch_start = perf_counter()

    tasks = {
        asyncio.create_task(
            check_website(u, request_timeout=request_timeout, semaphore=semaphore)
        ): u
        for u in normalized_urls
    }

    done, pending = await asyncio.wait(tasks.keys(), timeout=batch_timeout)

    results: list[WebsiteResponse] = []

    # Print finished tasks in completion-ish order (by observed duration).
    done_results = [task.result() for task in done]
    done_results.sort(key=lambda r: r.response_time)
    for r in done_results:
        _print_result(r, url_width)
        results.append(r)

    # Anything still pending after batch_timeout is "too long"
    if pending:
        elapsed = perf_counter() - batch_start
        for task in pending:
            url = tasks[task]
            timeout_result = WebsiteResponse(
                url=url,
                outcome="timeout",
                status=None,
                reason=f"batch timeout (> {batch_timeout:.2f}s)",
                response_time=elapsed,
            )
            _print_result(timeout_result, url_width)
            results.append(timeout_result)

        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)

    _print_summary(results)


async def main() -> None:
    urls: list[str] = [
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

    print(f"Checking {len(urls)} websites...\n")
    await check_websites(
        urls,
        request_timeout=5.0,  # per-website HTTP timeout
        batch_timeout=5.0,  # overall batch wall-clock timeout
        concurrency=20,  # max simultaneous checks
    )
    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
