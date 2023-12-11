"""
Sage Desktop SDK Exceptions
"""


class SageDesktopSDKError(Exception):
    """The base exception class for SageSdk.

    Parameters:
        msg (str): Short description of the error.
        response: Error response from the API call.
    """

    def __init__(self, msg, response=None):
        super(SageDesktopSDKError, self).__init__(msg)
        self.message = msg
        self.response = response

    def __str__(self):
        return repr(self.message)


class NotAcceptableClientError(SageDesktopSDKError):
    """Wrong client secret and/or refresh token, 406 error."""


class WrongParamsError(SageDesktopSDKError):
    """Some of the parameters (HTTP params or request body) are wrong, 400 error."""


class NotFoundItemError(SageDesktopSDKError):
    """Not found the item from URL, 404 error."""


class InternalServerError(SageDesktopSDKError):
    """The rest QBOSDK errors, 500 error."""


class InvalidUserCredentials(SageDesktopSDKError):
    """InvalidUserCredentials"""


class InvalidWebApiClientCredentials(SageDesktopSDKError):
    """InvalidWebApiClientCredentials"""


class UserAccountLocked(SageDesktopSDKError):
    """UserAccountLocked"""
    

class WebApiClientLocked(SageDesktopSDKError):
    """WebApiClientLocked"""