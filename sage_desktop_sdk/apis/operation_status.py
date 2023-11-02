"""
Sage Desktop Operation Status
"""
from sage_desktop_sdk.core.client import Client
from sage_desktop_sdk.core.schema.read_only import OperationStatusResponse


class OperationStatus(Client):
    """Class for Operation Status API."""

    GET_STATUS = '/Synchronization/RequestService.svc/status/{}'

    def get(self, export_id: str):
        """
        Get all Jobs
        :return: List of Dicts in Jobs Schema
        """
        operation_status: OperationStatusResponse = self._post_request(OperationStatus.GET_STATUS.format(export_id))
        return operation_status
