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

        list_of_accounts = []
        accounts = self._query_get_all(Accounts.GET_ACCOUNTS)

        for account in accounts:
            chart_of_accounts = Account(
                id=account['Id'],
                code=account['Code'],
                version=account['Version'],
                cost_requirement=account['CostRequirement'],
                description=account['Description'],
                is_active=account['isActive'],
                is_archived=account['isArchived'],
                name=account['Name'],
                parent_code=account['ParentCode'],
                parent_id=account['ParentId'],
                parent_name=account['ParentName']
            )
            list_of_accounts.append(chart_of_accounts)

        return list_of_accounts
