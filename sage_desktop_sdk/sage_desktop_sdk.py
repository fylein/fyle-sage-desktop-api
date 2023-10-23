"""
Sage Desktop Python Connector
"""
from .exceptions import *
from .apis import Accounts, Vendors, Jobs, Commitments, Documents, OperationStatus
from .core.client import Client


class SageDesktopSDK:
    """
    Sage Desktop SDK
    """
    
    def __init__(self, api_key: str, api_secret: str,  user_name: str, password: str, indentifier: str):
        """
        Initialize connection to Sage Intacct
            :param api_key: Sage API Key
            :param api_secret: Sage Desktop Api Secret
            :param user_name: Sage Desktop user name
            :param password: Sage Desktop user password
            :param indentifier: Sage Desktop Indentifier
        """
        
        self.__api_key = api_key
        self.__api_secret = api_secret
        self.__user_name = user_name
        self.__password = password
        self.__indentifier = indentifier
        
        self.client = Client()
        self.accounts = Accounts()
        self.vendors = Vendors()
        self.jobs = Jobs()
        self.commitments = Commitments()
        self.documents = Documents()
        self.operation_status = OperationStatus()

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


    def update_api_url(self):
        self.client.set_api_url(self.__indentifier)
        self.accounts.set_api_url(self.__indentifier)
        self.vendors.set_api_url(self.__indentifier)
        self.jobs.set_api_url(self.__indentifier)
        self.commitments.set_api_url(self.__indentifier)
        self.documents.set_api_url(self.__indentifier)
        self.operation_status.set_api_url(self.__indentifier)


    def update_cookie(self):
        self.client.update_cookie(self.__api_key, self.__api_secret)
        self.accounts.update_cookie(self.__api_key, self.__api_secret)
        self.vendors.update_cookie(self.__api_key, self.__api_secret)
        self.jobs.update_cookie(self.__api_key, self.__api_secret)
        self.commitments.update_cookie(self.__api_key, self.__api_secret)
        self.documents.update_cookie(self.__api_key, self.__api_secret)
        self.operation_status.update_cookie(self.__api_key, self.__api_secret)
