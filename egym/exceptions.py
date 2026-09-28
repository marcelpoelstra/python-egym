class EgymError(Exception):
    """Base class for all python-egym errors."""


class DiscoveryError(EgymError):
    """The gym's Netpulse base URL could not be found from the email address."""


class AuthenticationError(EgymError):
    """Login was refused, or a request was still refused after one renewal."""

    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


class ApiError(EgymError):
    """The API answered with a status outside 2xx."""

    def __init__(self, status_code, url, text):
        super().__init__(f"{status_code} from {url}: {text[:200]}")
        self.status_code = status_code
        self.url = url
        self.text = text
