"""
Sage Desktop Categories
"""
from sage_desktop_sdk.core.client import Client
from sage_desktop_sdk.core.schema.read_only import Account


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
        if version:
            # Append the version query parameter if provided
            query_params = '?version={0}'.format(version)
            endpoint = Accounts.GET_ACCOUNTS + query_params
        else:
            endpoint = Accounts.GET_ACCOUNTS

        # Query the API to get all accounts
        accounts = self._query_get_all(endpoint)
        for account in accounts:
            yield Account.from_dict(account)
