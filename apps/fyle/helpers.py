import json
import requests
from django.conf import settings

from fyle_integrations_platform_connector import PlatformConnector

from apps.workspaces.models import FyleCredential
from apps.fyle.constants import DEFAULT_FYLE_CONDITIONS


def post_request(url, body, refresh_token=None):
    """
    Create a HTTP post request.
    """
    access_token = None
    api_headers = {
        'Content-Type': 'application/json',
    }
    if refresh_token:
        access_token = get_access_token(refresh_token)
        api_headers['Authorization'] = 'Bearer {0}'.format(access_token)

    response = requests.post(
        url,
        headers=api_headers,
        data=body
    )

    if response.status_code == 200:
        return json.loads(response.text)
    else:
        raise Exception(response.text)


def get_request(url, params, refresh_token):
    """
    Create a HTTP get request.
    """
    access_token = get_access_token(refresh_token)
    api_headers = {
        'content-type': 'application/json',
        'Authorization': 'Bearer {0}'.format(access_token)
    }
    api_params = {}

    for k in params:
        # ignore all unused params
        if not params[k] is None:
            p = params[k]

            # convert boolean to lowercase string
            if isinstance(p, bool):
                p = str(p).lower()

            api_params[k] = p

    response = requests.get(
        url,
        headers=api_headers,
        params=api_params
    )

    if response.status_code == 200:
        return json.loads(response.text)
    else:
        raise Exception(response.text)


def get_access_token(refresh_token: str) -> str:
    """
    Get access token from fyle
    """
    api_data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': settings.FYLE_CLIENT_ID,
        'client_secret': settings.FYLE_CLIENT_SECRET
    }

    return post_request(settings.FYLE_TOKEN_URI, body=json.dumps(api_data))['access_token']


def get_cluster_domain(refresh_token: str) -> str:
    """
    Get cluster domain name from fyle
    :param refresh_token: (str)
    :return: cluster_domain (str)
    """
    cluster_api_url = '{0}/oauth/cluster/'.format(settings.FYLE_BASE_URL)

    return post_request(cluster_api_url, {}, refresh_token)['cluster_domain']


def get_expense_fields(workspace_id: int):
    """
    Get expense custom fields from fyle
    :param workspace_id: (int)
    :return: list of custom expense fields
    """

    fyle_credentails = FyleCredential.objects.get(workspace_id=workspace_id)
    platform = PlatformConnector(fyle_credentails)
    custom_fields = platform.expense_custom_fields.list_all()

    response = []
    response.extend(DEFAULT_FYLE_CONDITIONS)
    for custom_field in custom_fields:
        if custom_field['type'] in ('SELECT', 'NUMBER', 'TEXT', 'BOOLEAN'):
            response.append({
                'field_name': custom_field['field_name'],
                'type': custom_field['type'],
                'is_custom': custom_field['is_custom']
            })

    return response


def get_fyle_orgs(refresh_token: str, cluster_domain: str):
    """
    Get fyle orgs of a user
    """
    api_url = '{0}/api/orgs/'.format(cluster_domain)

    return get_request(api_url, {}, refresh_token)


def connect_to_platform(workspace_id: int) -> PlatformConnector:
    fyle_credentials: FyleCredential = FyleCredential.objects.get(workspace_id=workspace_id)

    return PlatformConnector(fyle_credentials=fyle_credentials)
