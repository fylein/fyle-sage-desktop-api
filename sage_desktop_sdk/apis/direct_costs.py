"""
Sage Desktop Direct Cost
"""
import json
from sage_desktop_sdk.core.client import Client


class DirectCosts(Client):
    """Class for Direct Cost APIs."""

    POST_DIRECT_COST = '/JobCosting/Api/V1/JobTransaction.svc/transactions/direct-costs'
    EXPORT_DIRECT_COST = '/JobCosting/Api/V1/JobTransaction.svc/job/transaction/synchronize?id={}'

    def post_direct_cost(self, data: dict):
        """
        Get Vendor Types
        :return: id of exported direct cost
        """
        return self._post_request(DirectCosts.POST_DIRECT_COST, data=json.dumps(data))

    def export_direct_cost(self, export_id: str):
        """
        Export Document to Sage300
        """
        return self._post_request(DirectCosts.EXPORT_DIRECT_COST.format(export_id))
