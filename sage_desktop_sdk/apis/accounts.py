"""
Sage Desktop Categories
"""
from sage_desktop_sdk.core.client import Client
from sage_desktop_sdk.core.schema.read_only import Account


class Accounts(Client):
    """Class for Accounts APIs."""

    GET_ACCOUNTS = '/GeneralLedger/Api/V1/Account.svc/accounts'

    @classmethod
    def generate_accounts(cls, account_data):
        for account in account_data:
            yield Account(
                id=account['Id'],
                code=account['Code'],
                version=account['Version'],
                is_active=account['IsActive'],
                is_archived=account['IsArchived'],
                name=account['Name'],
            )

    def get_all(self):
        """
        Get all Attachables
        :return: List of Dicts in Attachable Schema
        """

        accounts = self._query_get_all(Accounts.GET_ACCOUNTS)        
        return self.generate_accounts(accounts)
