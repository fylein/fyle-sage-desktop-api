"""
Sage Desktop Direct Cost
"""
import json
from sage_desktop_sdk.core.client import Client


class DirectCost(Client):
    """Class for Direct Cost APIs."""

    POST_DIRECT_COST = '/JobCosting/Api/V1/JobTransaction.svc/transactions/direct-costs'

    def post_document(self, data: dict):
        """
        Get Vendor Types
        :return: List of Dicts in Vendor Types Schema
        """
        return self._post_request(DirectCost.POST_DIRECT_COST, data=json.dumps(data.__dict__))
