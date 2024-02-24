from apps.users.helpers import (
    get_cluster_domain_and_refresh_token,
    get_user_profile
)
from apps.workspaces.models import FyleCredential, Workspace
from fyle_rest_auth.models import User

from django.test import RequestFactory


def test_get_cluster_domain_and_refresh_token(
    db,
    mocker,
    test_connection,
    create_temp_workspace,
    add_fyle_credentials
):
    """
    Test get_cluster_domain_and_refresh_token
    """
    workspace_id = 1
    user_id = "usqywo0f3nBY"

    user = User.objects.get(user_id=user_id)
    workspace = Workspace.objects.get(id=workspace_id)

    workspace.user.set([user])
    workspace.save()

    cluster_domain, refresh_token = get_cluster_domain_and_refresh_token(user)

    assert cluster_domain == 'https://dummy_cluster_domain.com'
    assert refresh_token == 'dummy_refresh_token'

    fyle_credentials = FyleCredential.objects.get(workspace__user=user)
    fyle_credentials.delete()

    cluster_domain, refresh_token = get_cluster_domain_and_refresh_token(user)

    assert cluster_domain == 'https://staging.fyle.tech'
    assert refresh_token == 'Dummy.Refresh.Token'


def test_get_user_profile(
    db,
    test_connection,
    create_temp_workspace,
    add_fyle_credentials
):
    """
    Test get_user_profile
    """
    user_id = "usqywo0f3nBY"
    user = User.objects.get(user_id=user_id)

    request = RequestFactory().get('/')
    request.user = user

    user_profile = get_user_profile(request=request)

    assert user_profile['data']['user']['email'] == 'ashwin.t@fyle.in'
