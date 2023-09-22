"""
Sage Desktop Categories
"""
from sage_desktop_sdk.core.client import Client


class Accounts(Client):
    """Class for Accounts APIs."""

    GET_ACCOUNTS = '/GeneralLedger/Api/V1/Account.svc/accounts'

    def get(self):
        """
        Get all Attachables
        :return: List of Dicts in Attachable Schema
        """
        return self._query_get_all(Accounts.GET_ACCOUNTS)
