from django.urls import reverse
from rest_framework import status
from tests.test_mappings.fixtures import data
from tests.helper import dict_compare_keys


def test_paginated_destination_attributes_view(db, api_client, test_connection, create_temp_workspace, add_project_mappings):
    """
    Test paginated destination attributes view
    """
    workspace_id = 1
    # url = f'/api/workspaces/{workspace_id}/mappings/paginated_destination_attributes/?limit=100&offset=0&attribute_type={attribute_type}&active=true&value={value}'

    url = reverse('paginated_destination_attributes_view', args=[workspace_id])

    # Test with no value matching the data
    params = {
        'limit': 100,
        'offset': 0,
        'attribute_type': 'JOB',
        'active': 'true',
        'value': 'Something not in the data'
    }

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))

    response = api_client.get(url, params)
    assert response.status_code == status.HTTP_200_OK
    assert dict_compare_keys(response.json(), data['paginated_destination_attributes_view_response_1']) == [], 'paginated destination attributes view api return diffs in keys'

    # Test with value (code) in the data
    params.update(value='123')

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))

    response = api_client.get(url, params)
    assert response.status_code == status.HTTP_200_OK
    assert dict_compare_keys(response.json(), data['paginated_destination_attributes_view_response_2']) == [], 'paginated destination attributes view api return diffs in keys'

    # Test with value (name) in the data
    params.update(value='cre')

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))

    response = api_client.get(url, params)
    assert response.status_code == status.HTTP_200_OK
    assert dict_compare_keys(response.json(), data['paginated_destination_attributes_view_response_2']) == [], 'paginated destination attributes view api return diffs in keys'
