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

    response = api_client.get(url, {'status__in': 'IN_PROGRESS'})
    assert response.status_code == 200
    response = json.loads(response.content)

    assert dict_compare_keys(response, data['accounting_export_response']) == [], 'accounting export api return diffs in keys'

    url = reverse('accounting-exports-count', kwargs={'workspace_id': 1})

    response = api_client.get(url, {'status__in': 'IN_PROGRESS'})
    assert response.status_code == 200
    response = json.loads(response.content)

    assert response['count'] == 2, 'accounting export count api return diffs in keys'


def test_get_accounting_export_summary(api_client, test_connection, create_temp_workspace, add_fyle_credentials, add_accounting_export_summary):
    url = reverse('accounting-exports-summary', kwargs={'workspace_id': 1})

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))

    response = api_client.get(url + '?start_date=2023-10-27T04:53:59.287618Z')
    assert response.status_code == 200
    response = json.loads(response.content)
    assert dict_compare_keys(response, data['accounting_export_summary_response']) == [], 'expense group api return diffs in keys'


def test_get_accounting_export_summary_2(api_client, test_connection, create_temp_workspace, add_fyle_credentials, add_accounting_export_summary):
    url = reverse('accounting-exports-summary', kwargs={'workspace_id': 1})

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))

    response = api_client.get(url)
    assert response.status_code == 200
    response = json.loads(response.content)

    fixture = data['accounting_export_summary_response'].copy()
    fixture['repurposed_successful_count'] = None
    fixture['repurposed_failed_count'] = None
    fixture['repurposed_last_exported_at'] = None

    assert dict_compare_keys(response, fixture) == [], 'expense group api return diffs in keys'


def test_get_errors(api_client, test_connection, create_temp_workspace, add_fyle_credentials, add_errors):
    """
    Test get errors
    """
    url = reverse('errors', kwargs={'workspace_id': 1})

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))

    response = api_client.get(url)
    assert response.status_code == 200
    response = json.loads(response.content)
    assert dict_compare_keys(response, data['errors_response']) == [], 'expense group api return diffs in keys'
