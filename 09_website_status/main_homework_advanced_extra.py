from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Union
from urllib.parse import urlsplit, urlunsplit

import requests
from requests import Response


# -----------------------------
# Models
# -----------------------------
@dataclass(frozen=True, slots=True)
class WebsiteDiagnostics:
    original_url: str
    normalised_url: str
    final_url: str
    method: str
    allow_redirects: bool

    status_code: int
    reason: str
    reachable: bool

    elapsed_time: float
    content_type: str
    encoding: Optional[str]

    content_length_header: Optional[int]
    content_length_bytes: Optional[int]

    server: Optional[str]
    date: Optional[str]

    redirect_chain: List[str]
    headers: Dict[str, str]


@dataclass(frozen=True, slots=True)
class WebsiteError:
    original_url: str
    normalised_url: str
    error_type: str
    message: str


WebsiteResult = Union[WebsiteDiagnostics, WebsiteError]


# -----------------------------
# URL helpers
# -----------------------------
def normalise_url(url: str) -> str:
    """
    Ensure a URL has a scheme and is well-formed using urllib.parse.

    Examples:
      - "example.com" -> "https://example.com"
      - "example.com/path" -> "https://example.com/path"
      - "https://example.com" stays unchanged
    """
    raw = url.strip()
    parts = urlsplit(raw)

    # If scheme is missing, urlsplit treats "example.com" as path.
    if not parts.scheme:
        parts = urlsplit(f"https://{raw}")

    # If netloc is still empty, try moving path into netloc (very edge-y inputs).
    if not parts.netloc and parts.path:
        # Example: "https://example.com" already fine. But if netloc empty,
        # treat the first path segment as netloc.
        candidate = parts.path
        parts = parts._replace(path="", netloc=candidate)

    return urlunsplit(parts)


# -----------------------------
# Core logic
# -----------------------------
def _is_reachable(status_code: int) -> bool:
    # "reachable" in a simple diagnostics context: got an HTTP response (2xx or 3xx)
    return 200 <= status_code < 400


def _to_int(value: str | None) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def check_website(
        url: str,
        *,
        timeout: int = 10,
        allow_redirects: bool = True,
        prefer_head: bool = True,
) -> WebsiteResult:
    """
    Check a website and return structured diagnostics.

    - Uses HEAD by default (lighter), with fallback to GET if HEAD is not supported or fails.
    - Differentiates common request error types.
    - Captures redirect chain and final URL.
    """
    original_url = url
    normalised = normalise_url(url)

    method_used = "HEAD" if prefer_head else "GET"

    def _request(method: str) -> Response:
        return requests.request(
            method=method,
            url=normalised,
            timeout=timeout,
            allow_redirects=allow_redirects,
        )

    try:
        response: Response
        try:
            response = _request("HEAD" if prefer_head else "GET")
        except requests.RequestException:
            # If HEAD preferred but fails, fallback to GET once.
            if prefer_head:
                response = _request("GET")
                method_used = "GET"
            else:
                raise

    except requests.Timeout as exc:
        return WebsiteError(
            original_url=original_url,
            normalised_url=normalised,
            error_type="Timeout",
            message=str(exc),
        )
    except requests.ConnectionError as exc:
        return WebsiteError(
            original_url=original_url,
            normalised_url=normalised,
            error_type="ConnectionError",
            message=str(exc),
        )
    except requests.RequestException as exc:
        return WebsiteError(
            original_url=original_url,
            normalised_url=normalised,
            error_type="RequestException",
            message=str(exc),
        )

    headers: Dict[str, str] = dict(response.headers)
    redirect_chain = [r.url for r in response.history] + [response.url]

    content_length_header = _to_int(headers.get("Content-Length"))
    server = headers.get("Server")
    date = headers.get("Date")

    # Only compute actual bytes if body is present (GET) or server returned something anyway.
    # For HEAD it will typically be None.
    content_length_bytes: Optional[int]
    if response.content:
        content_length_bytes = len(response.content)
    else:
        content_length_bytes = None

    return WebsiteDiagnostics(
        original_url=original_url,
        normalised_url=normalised,
        final_url=response.url,
        method=method_used,
        allow_redirects=allow_redirects,
        status_code=response.status_code,
        reason=response.reason,
        reachable=_is_reachable(response.status_code),
        elapsed_time=response.elapsed.total_seconds(),
        content_type=headers.get("Content-Type", ""),
        encoding=response.encoding,
        content_length_header=content_length_header,
        content_length_bytes=content_length_bytes,
        server=server,
        date=date,
        redirect_chain=redirect_chain,
        headers=headers,
    )


# -----------------------------
# Display
# -----------------------------
def display_website(
        result: WebsiteResult,
        *,
        show_headers: bool = True,
        sort_headers: bool = True,
        highlight_common_headers: bool = True,
) -> None:
    """
    Display diagnostics or errors.

    Provides:
    - verbosity controls
    - header sorting
    - "common headers first" view for readability
    """
    if isinstance(result, WebsiteError):
        print(f"\n=== Website diagnostics for {result.normalised_url} ===")
        print("Result       : ERROR")
        print(f"Type         : {result.error_type}")
        print(f"Message      : {result.message}")
        return

    data = result
    print(f"\n=== Website diagnostics for {data.normalised_url} ===")
    print(f"Original URL : {data.original_url}")
    print(f"Final URL    : {data.final_url}")
    print(f"Method       : {data.method} (allow_redirects={data.allow_redirects})")
    print(f"Reachable    : {'yes' if data.reachable else 'no'}")
    print(f"Status code  : {data.status_code} ({data.reason})")
    print(f"Elapsed time : {data.elapsed_time:.3f}s")
    print(f"Content-Type : {data.content_type}")
    print(f"Encoding     : {data.encoding or 'n/a'}")

    if data.content_length_header is not None:
        print(f"Content-Length (header): {data.content_length_header} bytes")
    else:
        print("Content-Length (header): n/a")

    if data.content_length_bytes is not None:
        print(f"Content-Length (body)  : {data.content_length_bytes} bytes")
    else:
        print("Content-Length (body)  : n/a")

    print(f"Server       : {data.server or 'n/a'}")
    print(f"Date         : {data.date or 'n/a'}")

    if data.redirect_chain:
        print("Redirects    :")
        for i, u in enumerate(data.redirect_chain, start=1):
            marker = " (final)" if i == len(data.redirect_chain) else ""
            print(f"  {i}. {u}{marker}")

    if not show_headers:
        return

    print("Headers      :")

    common_keys = [
        "Content-Type",
        "Content-Length",
        "Cache-Control",
        "Expires",
        "ETag",
        "Last-Modified",
        "Server",
        "Date",
        "Set-Cookie",
        "Location",
    ]

    printed = set()

    def _print_header(k: str, v: str) -> None:
        print(f"  • {k}: {v}")

    if highlight_common_headers:
        for key in common_keys:
            if key in data.headers:
                _print_header(key, data.headers[key])
                printed.add(key)

        remaining = {k: v for k, v in data.headers.items() if k not in printed}
    else:
        remaining = data.headers

    if sort_headers:
        for key in sorted(remaining):
            _print_header(key, remaining[key])
    else:
        for key, value in remaining.items():
            _print_header(key, value)


# -----------------------------
# Example usage
# -----------------------------
if __name__ == "__main__":
    result = check_website(
        "www.amazon.com",
        timeout=10,
        allow_redirects=True,
        prefer_head=True,
    )
    display_website(
        result,
        show_headers=True,
        sort_headers=True,
        highlight_common_headers=True,
    )
