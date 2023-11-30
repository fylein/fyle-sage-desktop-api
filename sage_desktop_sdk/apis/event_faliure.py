"""
Sage Desktop Event Faliure
"""
from sage_desktop_sdk.core.client import Client


class EventFaliures(Client):
    """Class for Event Faliure API."""

    GET_STATUS = '/Synchronization/EventService.svc/events/failures?entity={}'

    def get(self, export_id: str):
        """
        Get all Jobs
        :return: List of Dicts in Jobs Schema
        """
        event_faliure = self._post_request(EventFaliures.GET_STATUS.format(export_id))
        return event_faliure
