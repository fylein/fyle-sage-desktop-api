"""
Sage Desktop Python Connector
"""
from .apis import Accounts, Vendors, Jobs, Commitments, Documents, OperationStatus, Categories, CostCodes, DirectCosts, EventFailures
from .core.client import Client


class SageDesktopSDK:
    """
    Sage Desktop SDK
    """

    def __init__(self, api_key: str, api_secret: str,  user_name: str, password: str, identifier: str):
        """
        Initialize connection to Sage300
            :param api_key: Sage API Key
            :param api_secret: Sage Desktop Api Secret
            :param user_name: Sage Desktop user name
            :param password: Sage Desktop user password
            :param identifier: Sage Desktop Identifier
        """

        self.__api_key = api_key
        self.__api_secret = api_secret
        self.__user_name = user_name
        self.__password = password
        self.__identifier = identifier

        self.client = Client()
        self.accounts = Accounts()
        self.vendors = Vendors()
        self.jobs = Jobs()
        self.commitments = Commitments()
        self.documents = Documents()
        self.operation_status = OperationStatus()
        self.categories = Categories()
        self.cost_codes = CostCodes()
        self.direct_costs = DirectCosts()
        self.event_failures = EventFailures()

        self.update_api_url()
        self.update_user_id_and_password()
        self.update_cookie()

    def update_user_id_and_password(self):
        self.client.set_user_id_and_password(self.__user_name, self.__password)
        self.accounts.set_user_id_and_password(self.__user_name, self.__password)
        self.vendors.set_user_id_and_password(self.__user_name, self.__password)
        self.jobs.set_user_id_and_password(self.__user_name, self.__password)
        self.commitments.set_user_id_and_password(self.__user_name, self.__password)
        self.documents.set_user_id_and_password(self.__user_name, self.__password)
        self.operation_status.set_user_id_and_password(self.__user_name, self.__password)
        self.cost_codes.set_user_id_and_password(self.__user_name, self.__password)
        self.categories.set_user_id_and_password(self.__user_name, self.__password)
        self.direct_costs.set_user_id_and_password(self.__user_name, self.__password)
        self.event_failures.set_user_id_and_password(self.__user_name, self.__password)

    def update_api_url(self):
        self.client.set_api_url(self.__identifier)
        self.accounts.set_api_url(self.__identifier)
        self.vendors.set_api_url(self.__identifier)
        self.jobs.set_api_url(self.__identifier)
        self.commitments.set_api_url(self.__identifier)
        self.documents.set_api_url(self.__identifier)
        self.operation_status.set_api_url(self.__identifier)
        self.cost_codes.set_api_url(self.__identifier)
        self.categories.set_api_url(self.__identifier)
        self.direct_costs.set_api_url(self.__identifier)
        self.event_failures.set_api_url(self.__identifier)

    def update_cookie(self):
        cookie = self.client.update_cookie(self.__api_key, self.__api_secret)
        self.accounts.set_cookie(cookie)
        self.vendors.set_cookie(cookie)
        self.jobs.set_cookie(cookie)
        self.commitments.set_cookie(cookie)
        self.documents.set_cookie(cookie)
        self.operation_status.set_cookie(cookie)
        self.cost_codes.set_cookie(cookie)
        self.categories.set_cookie(cookie)
        self.direct_costs.set_cookie(cookie)
        self.event_failures.set_cookie(cookie)
