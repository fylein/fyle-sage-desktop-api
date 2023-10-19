import json
from django.urls import reverse

from apps.workspaces.models import Sage300Credentials, Workspace

def test_sync_dimensions(api_client, test_connection, mocker, create_temp_workspace, add_sage300_creds):
    workspace_id = 1

    access_token = test_connection.access_token
    url = reverse(
        'import-attributes', kwargs={
            'workspace_id': workspace_id
        }
    )

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access_token))

    mocker.patch(
        'apps.sage300.helpers.sync_dimensions',
        return_value=None
    )

    response = api_client.post(url)
    assert response.status_code == 201

    sage_intacct_credentials = Sage300Credentials.objects.get(workspace_id=workspace_id)
    sage_intacct_credentials.delete()

    response = api_client.post(url)
    assert response.status_code == 400

    response = json.loads(response.content)
    assert response['message'] == 'Sage300 credentials not found / invalid in workspace'
