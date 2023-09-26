"""
Sage Desktop Jobs
"""
from sage_desktop_sdk.core.client import Client


class Jobs(Client):
    """Class for Jobs APIs."""

    GET_JOBS = '/JobCosting/Api/V1/JobCost.svc/jobs'
    GET_COST_CODES = '/JobCosting/Api/V1/JobCost.svc/costcodes'
    GET_CATEGORIES = '/JobCosting/Api/V1/JobCost.svc/categories'


    def get_all_jobs(self):
        """
        Get all Jobs
        :return: List of Dicts in Jobs Schema
        """
        return self._query_get_all(Jobs.GET_JOBS)

    
    def get_all_costcodes(self):
        """
        Get all Cost Codes
        :return: List of Dicts in cost code Schema
        """
        return self._query_get_all(Jobs.GET_COST_CODES)


    def get_all_categoreis(self):
        """
        Get all Categories
        :return: List of Dicts in Cstegories Schema
        """
        return self._query_get_all(Jobs.GET_CATEGORIES)
