"""
Workspace Serializers
"""
from rest_framework import serializers

from django.core.cache import cache
from fyle_rest_auth.helpers import get_fyle_admin
from fyle_rest_auth.models import AuthToken

from apps.fyle.helpers import get_cluster_domain

from .models import (
    User,
    Workspace,
    FyleCredential,
    Sage300Credentials
)


class WorkspaceSerializer(serializers.ModelSerializer):
    """
    Workspace serializer
    """
    class Meta:
        model = Workspace
        fields = '__all__'
        read_only_fields = ('id', 'name', 'org_id', 'fyle_currency', 'created_at', 'updated_at', 'user')

    def create(self, validated_data):
        """
        Update workspace
        """
        access_token = self.context['request'].META.get('HTTP_AUTHORIZATION')
        user = self.context['request'].user

        # Getting user profile using the access token
        fyle_user = get_fyle_admin(access_token.split(' ')[1], None)

        # getting name, org_id, currency of Fyle User
        name = fyle_user['data']['org']['name']
        org_id = fyle_user['data']['org']['id']
        fyle_currency = fyle_user['data']['org']['currency']

        # Checking if workspace already exists
        workspace = Workspace.objects.filter(org_id=org_id).first()

        if workspace:
            # Adding user relation to workspace
            workspace.user.add(User.objects.get(user_id=user))
            cache.delete(str(workspace.id))
        else:
            workspace = Workspace.objects.create(
                name=name,
                org_id=org_id,
                fyle_currency=fyle_currency
            )

            workspace.user.add(User.objects.get(user_id=user))

            auth_tokens = AuthToken.objects.get(user__user_id=user)

            cluster_domain = get_cluster_domain(auth_tokens.refresh_token)

            FyleCredential.objects.update_or_create(
                refresh_token=auth_tokens.refresh_token,
                workspace_id=workspace.id,
                cluster_domain=cluster_domain
            )

        return workspace


class Sage300CredentialSerializer(serializers.ModelSerializer):
    """
    Sage300 credential serializer
    """
    class Meta:
        model = Sage300Credentials
        fields = '__all__'
