"""
Sage Desktop Cost Codes
"""
from sage_desktop_sdk.core.client import Client


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
        endpoint = CostCodes.GET_COST_CODE + '?page={0}'
        if version:
            # Append the version query parameter if provided
            query_params = f'&version={version}'
            endpoint += query_params

        # Query the API to get all cost codes
        cost_codes = self._query_get_all_generator(endpoint, is_paginated=True)
        yield cost_codes
