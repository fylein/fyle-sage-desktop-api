
import logging
import requests
import json
from typing import List, Dict, Generator
from sage_desktop_sdk.exceptions import (
    InvalidUserCredentials,
    InvalidWebApiClientCredentials,
    UserAccountLocked,
    WebApiClientLocked,
    WrongParamsError,
    NotAcceptableClientError,
    NotFoundItemError,
    SageDesktopSDKError,
    InternalServerError
)

logger = logging.getLogger(__name__)

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

    def set_cookie(self, cookie: str):
        self.__cookie = cookie

    def update_cookie(self, api_key: str, api_secret: str):
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
            'Content-type': 'application/json'
        }

        api_data = json.dumps({
            "ApiKey": api_key,
            "ApiSecret": api_secret,
            "Password": self.__user_password,
            "Username": self.__user_id
        })

        authentication_url = self.__api_url + '/Api/Security/V3/Session.svc/authenticate'
        result = requests.request("POST", url=authentication_url, headers=request_header, data=api_data)
        try:
            response = json.loads(result.text)

            if response['Result'] == 5:
                cookie = result.headers.get('Set-Cookie')
                self.__cookie = cookie
                return cookie

            if response['Result'] == 1:
                raise InvalidUserCredentials('Invalid User Credentials')

            if response['Result'] == 2:
                raise InvalidWebApiClientCredentials('Invalid Webapp Client')

            if response['Result'] == 3:
                raise UserAccountLocked('User Account Locked')

            if response['Result'] == 4:
                raise WebApiClientLocked('Web API client Locked')

        except Exception as e:
            raise SageDesktopSDKError("Error while connecting with hh2 | {0}".format(e))

    def _query_get_all_generator(self, url: str, is_paginated: bool = False) -> Generator[Dict, None, None]:
        """
        Gets all the objects of a particular type for query type GET calls
        :param url: GET URL of object
        :param object_type: type of object
        :param is_paginated: is paginated
        :return: Generator of objects
        """
        page_number = 0

        request_url = '{0}{1}'.format(self.__api_url, url)
        api_headers = {
            'Cookie': self.__cookie,
            'Accept': 'application/json'
        }

        while True:
            try:
                if is_paginated:
                    response = requests.get(url=request_url.format(page_number), headers=api_headers)
                else:
                    response = requests.get(url=request_url, headers=api_headers)

                data = json.loads(response.text)

                logger.debug('Response for get request for url: %s, %s', request_url, response.text)

                if not data:
                    break

                yield data

                if is_paginated:
                    page_number += 1
                else:
                    break

            except requests.exceptions.HTTPError as err:
                logger.info('Response for get request for url: %s, %s', url, err.response.text)
                if err.response.status_code == 400:
                    raise WrongParamsError('Some of the parameters are wrong', response.text)

                if err.response.status_code == 406:
                    raise NotAcceptableClientError('Forbidden, the user has insufficient privilege', response.text)

                if err.response.status_code == 404:
                    raise NotFoundItemError('Not found item with ID', response.text)

                if err.response.status_code == 500:
                    raise InternalServerError('Internal server error', response.text)

                raise SageDesktopSDKError('Error: {0}'.format(err.response.status_code), response.text)

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

        if response.status_code == 200:
            logger.debug('Response for get request for url: %s, %s', request_url, response.text)
            data = json.loads(response.text)
            return data

        logger.info('Response for get request for url: %s, %s', url, response.text)
        if response.status_code == 400:
            raise WrongParamsError('Some of the parameters are wrong', response.text)

        if response.status_code == 406:
            raise NotAcceptableClientError('Forbidden, the user has insufficient privilege', response.text)

        if response.status_code == 404:
            raise NotFoundItemError('Not found item with ID', response.text)

        if response.status_code == 500:
            raise InternalServerError('Internal server error', response.text)

        raise SageDesktopSDKError('Error: {0}'.format(response.status_code), response.text)

    def _query_get_by_id(self, url: str) -> List[Dict]:
        """
        Gets the object of a particular id
        :param url: GET URL of object
        :param id: id of object
        :return: list of objects
        """

        request_url = '{0}{1}'.format(self.__api_url, url)
        api_headers = {
            'Cookie': self.__cookie,
            'Accept': 'application/json'
        }

        response = requests.get(url=request_url, headers=api_headers)

        if response.status_code == 200:
            logger.debug('Response for get request for url: %s, %s', request_url, response.text)
            data = json.loads(response.text)
            return data

        logger.info('Response for get request for url: %s, %s', url, response.text)
        if response.status_code == 400:
            raise WrongParamsError('Some of the parameters are wrong', response.text)

        if response.status_code == 406:
            raise NotAcceptableClientError('Forbidden, the user has insufficient privilege', response.text)

        if response.status_code == 404:
            raise NotFoundItemError('Not found item with ID', response.text)

        if response.status_code == 500:
            raise InternalServerError('Internal server error', response.text)

        raise SageDesktopSDKError('Error: {0}'.format(response.status_code), response.text)

    def _post_request(self, url: str, data=None) -> Dict:
        """
        Gets all the objects of a particular type for query type GET calls
        :param url: GET URL of object
        :param object_type: type of object
        :return: list of objects
        """
        request_url = '{0}{1}'.format(self.__api_url, url)
        api_headers = {
            'Cookie': self.__cookie,
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

        response = requests.post(url=request_url, headers=api_headers, data=data)
        logger.debug('Payload for post request: %s', data)

        if response.status_code == 200:
            logger.debug('Response for post request: %s', response.text)
            return json.loads(response.text)

        logger.info('Response for post request: %s', response.text)
        if response.status_code == 400:
            raise WrongParamsError('Some of the parameters are wrong', json.loads(response.text))

        if response.status_code == 406:
            raise NotAcceptableClientError('Forbidden, the user has insufficient privilege', response.text)

        if response.status_code == 404:
            raise NotFoundItemError('Not found item with ID', response.text)

        if response.status_code == 500:
            raise InternalServerError('Internal server error', response.text)

        raise SageDesktopSDKError('Error: {0}'.format(response.status_code), response.text)
