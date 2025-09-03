# api/errors.py
import os

LOCALE = os.getenv("ERROR_LOCALE", "es").lower()

def _(es: str, en: str) -> str:
    return es if LOCALE.startswith("es") else en

class ProviderError(Exception):
    status_code = 500
    def __init__(self, detail: str | None = None):
        self.detail = detail or _("Upstream provider error.", "We encountered an issue with the upstream provider. Please try again in a few moments.")

class AuthError(ProviderError):
    status_code = 401
    def __init__(self, detail: str | None = None):
        super().__init__(detail or _("Invalid API key.", "The API key provided is invalid. Check your credentials and try again."))

class PermissionError(ProviderError):
    status_code = 403
    def __init__(self, detail: str | None = None):
        super().__init__(detail or _("Permission denied for this model.", "You don't have permission to use this model. Contact support for access."))

class BadRequestError(ProviderError):
    status_code = 400
    def __init__(self, detail: str | None = None):
        super().__init__(detail or _("Invalid request to provider.", "The request to the provider was malformed. Please review the request parameters."))

class RateLimited(ProviderError):
    status_code = 429
    def __init__(self, detail: str | None = None):
        super().__init__(detail or _("Rate limit or quota exceeded.", "You have exceeded your rate limit or quota. Please wait a moment before trying again."))

class UpstreamTimeout(ProviderError):
    status_code = 504
    def __init__(self, detail: str | None = None):
        super().__init__(detail or _("Upstream timeout.", "The upstream service timed out. This may be a temporary issue."))

class Unavailable(ProviderError):
    status_code = 503
    def __init__(self, detail: str | None = None):
        super().__init__(detail or _("Service unavailable.", "The service is temporarily unavailable. Please try again soon."))

class UpstreamNetwork(ProviderError):
    status_code = 502
    def __init__(self, detail: str | None = None):
        super().__init__(detail or _("Network error to provider.", "A network error occurred while communicating with the provider."))