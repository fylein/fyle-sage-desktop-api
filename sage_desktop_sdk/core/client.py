
import requests
import json
from typing import List, Dict

class Client:
    """
    This is base class for all API classes
    """
    
    def __init__(self, url: str = None):
        
        self.__api_url = None
        self.__user_id = None
        self.__user_password = None
        self.__cookie = None


    def set_user_id_and_password(self, user_id: str, user_password: str):
        """
        Set the user_id and user_password for APIs
        :param user_id: user id
        :param user_password: user password
        :return: None
        """
        self.__user_id = user_id
        self.__user_password = user_password


    def set_api_url(self, indentifier: str):
        """
        Set the api url and indentifier for APIs
        :param identifier: indentifier
        :return: None
        """
        self.__api_url = "https://{0}".format(indentifier)


    def set_authentication_cookie(self, api_key: str, api_secret: str):
        """
        Sets the cookies for APIs
        :param api_key: Sage API Key
        :param api_secret: Sage Desktop Api Secret
        :param user_name: Sage Desktop user name
        :param password: Sage Desktop user password
        :param indentifier: Sage Desktop Indentifier
        :return: cookie
        """

        request_header = {
            'Accept': 'application/json',
            'Content-type': 'application/json',
        }

        api_data = json.dumps({ 
            "ApiKey": api_key, 
            "ApiSecret": api_secret, 
            "Password": self.__user_password, 
            "Username": self.__user_id
        })

        authentication_url = self.__api_url + '/Api/Security/V3/Session.svc/authenticate'
        response = requests.request("POST", url=authentication_url, headers=request_header, data=api_data)
        return response.headers.get('Set-Cookie')


    def set_cookie(self, cookie: str):
        self.__cookie = cookie
 

    def _query_get_all(self, url: str) -> List[Dict]:
        """
        Gets all the objects of a particular type for query type GET calls
        :param url: GET URL of object
        :param object_type: type of object
        :return: list of objects
        """
    
        request_url = '{0}{1}'.format(self.__api_url, url)

        api_headers = {
            'Cookie': self.__cookie,
            'Accept': 'application/json'
        }

        response = requests.get(url=request_url, headers=api_headers)
        return response
