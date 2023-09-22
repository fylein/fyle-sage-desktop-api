"""
Sage Desktop Python Connector
"""
import json
import base64
import requests

from .exceptions import *
from .apis import Accounts
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

        self.update_user_id_and_password()
        self.update_api_url()
        self.update_cookie()
    
    
    def update_user_id_and_password(self):

        self.client.set_user_id_and_password(self.__user_name, self.__password)
        self.accounts.set_user_id_and_password(self.__user_name, self.__password)
    
    def update_api_url(self):

        self.client.set_api_url(self.__indentifier)
        self.accounts.set_api_url(self.__indentifier)

    def update_cookie(self):
    
        self.client.set_authentication_cookie(self.__api_key, self.__api_secret)
        self.accounts.set_authentication_cookie(self.__api_key, self.__api_secret)
        
