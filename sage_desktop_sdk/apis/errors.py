"""
Sage Desktop Operation Status
"""
from sage_desktop_sdk.core.client import Client


class Errors(Client):
    """Class for Errors API."""

    GET_STATUS = 'Synchronization/EventService.svc/events/failures'

    def get(self):
        """
        Get all Errors
        :return: List of Dicts in Errors Schema
        """
        erros = self._post_request(Errors.GET_STATUS)
        return erros
