"""
MURA SDK Exceptions

Custom exceptions for the MURA SDK.
"""


class MuraError(Exception):
    """Base exception for all MURA errors"""
    pass


class MuraAPIError(MuraError):
    """Error from the MURA API"""
    def __init__(self, message: str, status_code: int = None, response: dict = None):
        self.status_code = status_code
        self.response = response
        super().__init__(message)


class MuraConnectionError(MuraError):
    """Failed to connect to MURA network"""
    pass


class MuraAuthenticationError(MuraError):
    """Invalid API key or authentication failed"""
    pass


class MuraValidationError(MuraError):
    """Invalid request data"""
    pass


class MuraTimeoutError(MuraError):
    """Request timed out"""
    pass


class NoSuppliersFoundError(MuraError):
    """No suppliers found for the request"""
    pass


class ComplianceError(MuraError):
    """Compliance check failed with blockers"""
    def __init__(self, message: str, blockers: list = None):
        self.blockers = blockers or []
        super().__init__(message)


class QuoteError(MuraError):
    """Error getting quotes from suppliers"""
    pass


class RegistrationError(MuraError):
    """Failed to register agent in the network"""
    pass
