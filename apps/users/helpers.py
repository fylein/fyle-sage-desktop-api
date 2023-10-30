from typing import Tuple

from fyle_rest_auth.models import AuthToken
from fyle_integrations_platform_connector import PlatformConnector

from apps.workspaces.models import FyleCredential
from apps.fyle.helpers import get_cluster_domain


def get_cluster_domain_and_refresh_token(user) -> Tuple[str, str]:
    """
    Get cluster domain and refresh token from User
    """
    fyle_credentials = FyleCredential.objects.filter(workspace__user=user).first()

    if fyle_credentials:
        refresh_token = fyle_credentials.refresh_token
        cluster_domain = fyle_credentials.cluster_domain
    else:
        refresh_token = AuthToken.objects.get(user__user_id=user).refresh_token
        cluster_domain = get_cluster_domain(refresh_token)

    return cluster_domain, refresh_token


def get_user_profile(request):
    """
    Get user profile
    """
    refresh_token = AuthToken.objects.get(user__user_id=request.user).refresh_token
    cluster_domain, _ = get_cluster_domain_and_refresh_token(request.user)

    fyle_credentials = FyleCredential(
        cluster_domain=cluster_domain,
        refresh_token=refresh_token
    )

    platform = PlatformConnector(fyle_credentials)
    employee_profile = platform.connection.v1beta.spender.my_profile.get()

    return employee_profile
