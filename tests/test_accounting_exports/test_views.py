import json
from django.urls import reverse
from tests.helper import dict_compare_keys
from tests.test_fyle.fixtures import fixtures as data


def test_get_accounting_exports(api_client, test_connection, create_temp_workspace, add_fyle_credentials, add_accounting_export_expenses):
    """
    Test get accounting exports
    """
    url = reverse('accounting-exports', kwargs={'workspace_id': 1})

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))

    response = api_client.get(url)
    assert response.status_code == 200
    response = json.loads(response.content)

    assert dict_compare_keys(response, data['accounting_export_response']) == [], 'expense group api return diffs in keys'
