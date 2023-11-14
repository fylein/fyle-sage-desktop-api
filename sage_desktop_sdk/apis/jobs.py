"""
Sage Desktop Jobs
"""
from sage_desktop_sdk.core.client import Client
from sage_desktop_sdk.core.schema.read_only import Job, StandardCategory, StandardCostCode


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
        if version:
            # Append the version query parameter if provided
            query_params = '?version={0}'.format(version)
            endpoint = Jobs.GET_JOBS + query_params
        else:
            endpoint = Jobs.GET_JOBS

        # Query the API to get all jobs
        jobs = self._query_get_all(endpoint)

        for job in jobs:
            # Convert each job dictionary to a Job object and yield it
            yield Job.from_dict(job)

    def get_standard_costcodes(self, version: int = None):
        """
        Get all standard cost codes.

        :param version: API version
        :type version: int

        :return: A generator yielding standard cost codes in the Cost Code Schema
        :rtype: generator of StandardCostCode objects
        """
        if version:
            # Append the version query parameter if provided
            query_params = '?version={0}'.format(version)
            endpoint = Jobs.GET_COST_CODES + query_params
        else:
            endpoint = Jobs.GET_COST_CODES

        # Query the API to get all standard cost codes
        costcodes = self._query_get_all(endpoint)

        for costcode in costcodes:
            # Convert each cost code dictionary to a StandardCostCode object and yield it
            yield StandardCostCode.from_dict(costcode)

    def get_standard_categories(self, version: int = None):
        """
        Get all standard categories.

        :param version: API version
        :type version: int

        :return: A generator yielding standard categories in the Categories Schema
        :rtype: generator of StandardCategory objects
        """
        if version:
            # Append the version query parameter if provided
            query_params = '?version={0}'.format(version)
            endpoint = Jobs.GET_CATEGORIES + query_params
        else:
            endpoint = Jobs.GET_CATEGORIES

        # Query the API to get all standard categories
        categories = self._query_get_all(endpoint)

        for category in categories:
            # Convert each category dictionary to a StandardCategory object and yield it
            yield StandardCategory.from_dict(category)
