"""
Sage Desktop Jobs
"""
from sage_desktop_sdk.core.client import Client
from sage_desktop_sdk.core.schema.read_only import Jobs, CostCode, Category


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
        jobs =  self._query_get_all(Jobs.GET_JOBS)
        for job in jobs:
            yield Jobs.from_dict(job)


    def get_all_costcodes(self):
        """
        Get all Cost Codes
        :return: List of Dicts in cost code Schema
        """
        costcodes =  self._query_get_all(Jobs.GET_COST_CODES)
        for costcode in costcodes:
            yield CostCode.from_dict(costcode)


    def get_all_categoreis(self):
        """
        Get all Categories
        :return: List of Dicts in Cstegories Schema
        """
        categories =  self._query_get_all(Jobs.GET_CATEGORIES)
        for category in categories:
            yield Category.from_dict(category)
