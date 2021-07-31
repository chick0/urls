from urllib.parse import urlparse


class UrlVerifyFail(Exception):
    def __init__(self, message):
        super().__init__(message)


def url_verifier(url: str) -> str:
    if len(url) > 2000:
        raise UrlVerifyFail(message="URL is too long. Please try again less than 2000 characters.")

    url = urlparse(url=url)
    allow_schemes = [
        "http",
        "https",
    ]

    if url.scheme not in allow_schemes:
        raise UrlVerifyFail(message=f"'{url.scheme}' is an unacceptable scheme.")

    return url.geturl()
