from dataclasses import dataclass
from typing import Dict, Optional

import requests
from requests import Response


@dataclass
class WebsiteDiagnostics:
    url: str
    status_code: int
    reason: str
    elapsed_time: float
    content_type: str
    encoding: Optional[str]
    headers: Dict[str, str]


def normalise_url(url: str) -> str:
    """Ensure the URL contains a valid HTTP scheme."""
    return url if url.startswith(("http://", "https://")) else f"https://{url}"


def check_website(url: str, timeout: int = 10) -> Optional[WebsiteDiagnostics]:
    """
    Perform a website request and return diagnostics data.

    Returns None if the request fails.
    """
    url = normalise_url(url)

    try:
        response: Response = requests.get(url, timeout=timeout)
    except requests.RequestException as exc:
        print(f"ERROR: {exc}")
        return None

    return WebsiteDiagnostics(
        url=url,
        status_code=response.status_code,
        reason=response.reason,
        elapsed_time=response.elapsed.total_seconds(),
        content_type=response.headers.get("Content-Type", ""),
        encoding=response.encoding,
        headers=dict(response.headers),
    )


def display_website(data: WebsiteDiagnostics) -> None:
    """Display website diagnostics information in the console."""
    print(f"\n=== Website diagnostics for {data.url} ===")
    print(f"Status code  : {data.status_code} ({data.reason})")
    print(f"Elapsed time : {data.elapsed_time:.3f}s")
    print(f"Content-Type : {data.content_type}")
    print(f"Encoding     : {data.encoding or 'n/a'}")
    print("Headers      :")
    for key, value in data.headers.items():
        print(f"  • {key}: {value}")


if __name__ == "__main__":
    diagnostics = check_website("www.amazon.com")
    if diagnostics:
        display_website(diagnostics)
