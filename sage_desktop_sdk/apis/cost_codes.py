"""
Sage Desktop Cost Codes
"""
from sage_desktop_sdk.core.client import Client
from sage_desktop_sdk.core.schema.read_only import CostCode


class CostCodes(Client):
    """Class for Cost Code APIs."""

    GET_COST_CODE = '/JobCosting/Api/V1/JobCost.svc/jobs/costcodes'

    def get_all_costcodes(self, version: int = None):
        """
        Get all cost codes.

        :param version: API version
        :type version: int

        :return: A generator yielding cost codes in the Cost Code Schema
        :rtype: generator of CostCode objects
        """
        if version:
            # Append the version query parameter if provided
            query_params = '?version={0}'.format(version)
            endpoint = CostCodes.GET_COST_CODE + query_params
        else:
            endpoint = CostCodes.GET_COST_CODE

        # Query the API to get all cost codes
        cost_codes = self._query_get_all(endpoint)

        for cost_code in cost_codes:
            # Convert each cost code dictionary to a CostCode object and yield it
            yield CostCode.from_dict(cost_code)
