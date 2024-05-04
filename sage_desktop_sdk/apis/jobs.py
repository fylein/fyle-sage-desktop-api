"""
Sage Desktop Jobs
"""
from sage_desktop_sdk.core.client import Client


class Jobs(Client):
    """Class for Jobs APIs."""

    GET_JOBS = '/JobCosting/Api/V1/JobCost.svc/jobs'
    GET_COST_CODES = '/JobCosting/Api/V1/JobCost.svc/costcodes'
    GET_CATEGORIES = '/JobCosting/Api/V1/JobCost.svc/categories'

    def get_all_jobs(self, version: int = None):
        """
        Get all jobs.

        :param version: API version
        :type version: int

        :return: A generator yielding jobs in the Jobs Schema
        :rtype: generator of Job objects
        """
        endpoint = Jobs.GET_JOBS + '?page={0}'
        if version:
            # Append the version query parameter if provided
            query_params = f'&version={version}'
            endpoint += query_params

        # Query the API to get all jobs
        jobs = self._query_get_all_generator(endpoint, is_paginated=True)
        yield jobs

    def get_standard_costcodes(self, version: int = None):
        """
        Get all standard cost codes.

        :param version: API version
        :type version: int

        :return: A generator yielding standard cost codes in the Cost Code Schema
        :rtype: generator of StandardCostCode objects
        """
        endpoint = Jobs.GET_COST_CODES + '?page={0}'
        if version:
            # Append the version query parameter if provided
            query_params = f'&version={version}'
            endpoint += query_params

        # Query the API to get all jobs
        cost_codes = self._query_get_all_generator(endpoint, is_paginated=True)
        yield cost_codes

    def get_standard_categories(self, version: int = None):
        """
        Get all standard categories.

        :param version: API version
        :type version: int

        :return: A generator yielding standard categories in the Categories Schema
        :rtype: generator of StandardCategory objects
        """
        endpoint = Jobs.GET_CATEGORIES + '?page={0}'
        if version:
            # Append the version query parameter if provided
            query_params = f'&version={version}'
            endpoint += query_params

        # Query the API to get all jobs
        categories = self._query_get_all_generator(endpoint, is_paginated=True)
        yield categories
