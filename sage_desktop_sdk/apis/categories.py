"""
Sage Desktop Categories
"""
from sage_desktop_sdk.core.client import Client
from sage_desktop_sdk.core.schema.read_only import Category


class Categories(Client):
    """Class for Jobs APIs."""

    GET_CATEGORIES = '/JobCosting/Api/V1/JobCost.svc/jobs/categories'

    def get_all_categories(self):
        """
        Get all Jobs
        :return: List of Dicts in Jobs Schema
        """
        categories = self._query_get_all(Categories.GET_CATEGORIES)
        for category in categories:
            print('catefor', category)
            yield Category.from_dict(category)
