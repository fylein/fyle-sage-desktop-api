"""
Sage Desktop Cost Codes
"""
from sage_desktop_sdk.core.client import Client
from sage_desktop_sdk.core.schema.read_only import CostCode


class CostCodes(Client):
    """Class for Cost Code APIs."""

    GET_COST_CODE = '/JobCosting/Api/V1/JobCost.svc/jobs/costcodes'

    def get_all_costcodes(self):
        """
        Get all Cost Code
        :return: List of Dicts in Cost Code Schema
        """
        cost_codes = self._query_get_all(CostCodes.GET_COST_CODE)
        for cost_code in cost_codes:
            yield CostCode.from_dict(cost_code)
