"""
Sage Desktop Categories
"""
from sage_desktop_sdk.core.client import Client
from sage_desktop_sdk.core.schema.read_only import Account


class Accounts(Client):
    """Class for Accounts APIs."""

    GET_ACCOUNTS = '/GeneralLedger/Api/V1/Account.svc/accounts'


    def get_all(self):
        """
        Get all Attachables
        :return: List of Dicts in Attachable Schema
        """

        accounts = self._query_get_all(Accounts.GET_ACCOUNTS)        
        for account in accounts:
            yield Account.from_dict(account)
