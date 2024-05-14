"""
Sage Desktop Categories
"""
from sage_desktop_sdk.core.client import Client


class Accounts(Client):
    """Class for Accounts APIs."""

    GET_ACCOUNTS = '/GeneralLedger/Api/V1/Account.svc/accounts'

    def get_all(self, version: int = None):
        """
        Get all accounts.
        :param version: API version
        :type version: int
        :return: A generator yielding accounts in the Attachable Schema
        :rtype: generator of Account objects
        """
        endpoint = Accounts.GET_ACCOUNTS
        if version:
            # Append the version query parameter if provided
            query_params = f'?version={version}'
            endpoint += query_params

        # Query the API to get all accounts
        accounts = self._query_get_all_generator(endpoint)
        yield accounts
