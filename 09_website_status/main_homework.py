import requests
from requests import Response


def normalise_url(url: str) -> str:
    """Ensure the URL has a scheme."""
    return url if url.startswith(('http://', 'https://')) else f'https://{url}'


def check_website(url: str, timeout: int = 10) -> dict | None:
    """Check a website and return diagnostic data."""
    url = normalise_url(url)

    try:
        response: Response = requests.get(url, timeout=timeout)
    except Exception as error:
        return {'error': str(error), 'url': url}

    return {
        'url': url,
        'status_code': response.status_code,
        'reason': response.reason,
        'elapsed_time': response.elapsed.total_seconds(),
        'content_type': response.headers.get('Content-Type', ''),
        'encoding': response.encoding,
        'headers': dict(response.headers),
    }


def display_website(data: dict) -> None:
    """Display website diagnostic data."""
    print(f"\n=== Website diagnostics for {data['url']} ===")

    if 'error' in data:
        print(f"ERROR: {data['error']}")
        return

    print(f"Status code  : {data['status_code']} ({data['reason']})")
    print(f"Elapsed time : {data['elapsed_time']}s")
    print(f"Content-Type : {data['content_type']}")
    print(f"Encoding     : {data['encoding'] or 'n/a'}")
    print("Headers      :")

    for key, value in data['headers'].items():
        print(f"  • {key}: {value}")


if __name__ == '__main__':
    result = check_website('www.amazon.com')
    display_website(result)
