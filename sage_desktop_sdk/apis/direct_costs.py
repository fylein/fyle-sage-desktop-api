"""
Sage Desktop Direct Cost
"""
import json
from sage_desktop_sdk.core.client import Client


class DirectCosts(Client):
    """Class for Direct Cost APIs."""

    POST_DIRECT_COST = '/JobCosting/Api/V1/JobTransaction.svc/transactions/direct-costs'

    def post_direct_cost(self, data: dict):
        """
        Get Vendor Types
        :return: id of exported direct cost
        """
        return self._post_request(DirectCosts.POST_DIRECT_COST, data=json.dumps(data))
