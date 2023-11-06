"""
Sage Desktop Categories
"""
from sage_desktop_sdk.core.client import Client
from sage_desktop_sdk.core.schema.read_only import Category


class Categories(Client):
    """Class for Jobs APIs."""

    GET_CATEGORIES = '/JobCosting/Api/V1/JobCost.svc/jobs/categories'

    def get_all_categories(self, version: int = None):
        """
        Get all job categories.

        :param version: API version
        :type version: int

        :return: A generator yielding job categories in the Jobs Schema
        :rtype: generator of Category objects
        """
        if version:
            # Append the version query parameter if provided
            query_params = '?version={0}'.format(version)
            endpoint = Categories.GET_CATEGORIES + query_params
        else:
            endpoint = Categories.GET_CATEGORIES

        # Query the API to get all job categories
        categories = self._query_get_all(endpoint)

        for category in categories:
            # Convert each category dictionary to a Category object and yield it
            yield Category.from_dict(category)
