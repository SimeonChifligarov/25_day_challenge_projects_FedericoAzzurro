import asyncio
from asyncio import TimeoutError
from dataclasses import dataclass
from time import perf_counter

import requests
from requests import Response


def normalize_url(url: str) -> str:
    return url if url.startswith(("http://", "https://")) else f"https://{url}"


# 1. Model the data
@dataclass(slots=True)
class WebsiteResponse:
    url: str
    status: int | None
    reason: str
    response_time: float | None  # seconds


# 2. Check an individual website
async def check_website(url: str, request_timeout: float) -> WebsiteResponse:
    start = perf_counter()

    # Will raise a Timeout Error (from check_websites overall timeout):
    # if url == "https://www.fail-website.com":
    #     await asyncio.sleep(10)

    try:
        response: Response = await asyncio.to_thread(
            requests.get, url, timeout=request_timeout
        )
        elapsed = perf_counter() - start
        return WebsiteResponse(url, response.status_code, response.reason, elapsed)
    except requests.exceptions.Timeout:
        elapsed = perf_counter() - start
        return WebsiteResponse(url, None, "timeout", elapsed)
    except Exception as e:
        elapsed = perf_counter() - start
        return WebsiteResponse(url, None, str(e), elapsed)


def print_result(result: WebsiteResponse) -> None:
    t = "?" if result.response_time is None else f"{result.response_time:.2f}s"

    if result.status is not None:
        print(f"{result.url}: ✅ ONLINE ({result.status} {result.reason}) in {t}")
        return

    label = "⏱️ TIMEOUT" if "timeout" in result.reason.lower() else "❌ ERROR"
    print(f"{result.url}: {label} ({result.reason}) after {t}")


# 3. Check multiple websites
async def check_websites(urls: list[str], timeout: float = 5.0) -> None:
    normalized_urls = [normalize_url(url) for url in urls]

    tasks = {
        asyncio.create_task(check_website(url, request_timeout=timeout)): url
        for url in normalized_urls
    }

    timed_out = False
    try:
        for completed_task in asyncio.as_completed(tasks, timeout=timeout):
            result: WebsiteResponse = await completed_task
            print_result(result)
    except TimeoutError:
        timed_out = True
    finally:
        if timed_out:
            pending = [task for task in tasks if not task.done()]
            if pending:
                print("Timeout reached — these websites took too long:")
                for task in pending:
                    url = tasks[task]
                    print(f"{url}: ⏱️ TIMEOUT (> {timeout:.2f}s)")
                    task.cancel()
                await asyncio.gather(*pending, return_exceptions=True)


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

    print(f"Checking {len(urls)} websites...")
    await check_websites(urls)
    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
