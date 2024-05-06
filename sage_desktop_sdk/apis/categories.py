"""
Sage Desktop Categories
"""
from sage_desktop_sdk.core.client import Client


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
        endpoint = Categories.GET_CATEGORIES + '?page={0}'
        if version:
            # Append the version query parameter if provided
            query_params = f'&version={version}'
            endpoint += query_params

        # Query the API to get all job categories
        categories = self._query_get_all_generator(endpoint, is_paginated=True)
        yield categories
