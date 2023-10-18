import json
import pytest       # noqa
from django.urls import reverse

from apps.workspaces.models import Workspace, Sage300Credentials


def test_post_of_workspace(api_client, test_connection):
    '''
    Test post of workspace
    '''
    url = reverse(
        'workspaces'
    )

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))
    response = api_client.post(url)

    workspace = Workspace.objects.filter(org_id='orNoatdUnm1w').first()

    assert response.status_code == 201
    assert workspace.name == response.data['name']
    assert workspace.org_id == response.data['org_id']
    assert workspace.fyle_currency == response.data['fyle_currency']

    response = json.loads(response.content)

    response = api_client.post(url)
    assert response.status_code == 201


def test_get_of_workspace(api_client, test_connection):
    '''
    Test get of workspace
    '''
    url = reverse(
        'workspaces'
    )

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))
    response = api_client.get(url)

    assert response.status_code == 400
    assert response.data['message'] == 'org_id is missing'

    response = api_client.get('{}?org_id=orNoatdUnm1w'.format(url))

    assert response.status_code == 400
    assert response.data['message'] == 'Workspace not found or the user does not have access to workspaces'

    response = api_client.post(url)
    response = api_client.get('{}?org_id=orNoatdUnm1w'.format(url))

    assert response.status_code == 200
    assert response.data['name'] == 'Fyle For MS Dynamics Demo'
    assert response.data['org_id'] == 'orNoatdUnm1w'
    assert response.data['fyle_currency'] == 'USD'


def test_post_of_sage300_creds(api_client, test_connection, mocker):
    '''
    Test post of sage300 creds
    '''
    url = reverse(
        'workspaces'
    )

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))
    response = api_client.post(url)

    url = reverse(
        'sage300-creds', kwargs={
            'workspace_id': response.data['id']
        }
    )

    payload = { 
        'identifier': "indentifier",
        'password': "passeord", 
        'username': "username",
        'workspace': response.data['id']
    }
    
    mocker.patch(
        'sage_desktop_sdk.core.client.Client.update_cookie',
        return_value={'text': {'Result': 2}}
    )

    response = api_client.post(url, payload)
    assert response.status_code == 201


def test_get_of_sage300_creds(api_client, test_connection):
    '''
    Test get of workspace
    '''

    url = reverse(
        'workspaces'
    )

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))
    response = api_client.post(url)

    url = reverse(
        'sage300-creds', kwargs={
            'workspace_id': response.data['id']
        }
    )

    Sage300Credentials.objects.create(
            identifier='identifier',
            username='username',
            password='password',
            workspace_id=response.data['id'],
            api_key='apiley',
            api_secret='apisecret'
        )


    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))
    response = api_client.get(url)

    assert response.status_code == 200
    assert response.data['username'] == 'username'
    assert response.data['password'] == 'password'
