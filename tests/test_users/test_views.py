import pytest
from django.urls import reverse


@pytest.mark.django_db(databases=['default'])
def test_setup():
    assert 1 == 1


def test_get_user_profile(
    db,
    api_client,
    test_connection,
    create_temp_workspace,
    add_fyle_credentials
):
    """
    Test get user profile
    """
    access_token = test_connection.access_token
    url = reverse('user_profile')

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access_token))

    response = api_client.get(url)
    assert response.status_code == 200
    assert response.data['data']['user']['email'] == 'ashwin.t@fyle.in'


def test_get_fyle_orgs(
    db,
    mocker,
    api_client,
    test_connection,
    create_temp_workspace,
    add_fyle_credentials
):
    """
    Test get user profile
    """
    access_token = test_connection.access_token
    url = reverse('fyle_orgs')

    mocker.patch('apps.users.views.get_fyle_orgs', return_value=[{'id': 1, 'name': 'Fyle Org 1'}])

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access_token))

    response = api_client.get(url)
    assert response.status_code == 200
    assert response.data[0]['id'] == 1
    assert response.data[0]['name'] == 'Fyle Org 1'
