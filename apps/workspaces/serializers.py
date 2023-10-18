from rest_framework import serializers
from django.conf import settings

from .models import Sage300Credentials
from sage_desktop_sdk.sage_desktop_sdk import SageDesktopSDK
from sage_desktop_sdk.exceptions import (
    UserAccountLocked,
    InvalidUserCredentials,
    InvalidWebApiClientCredentials,
    WebApiClientLocked
)


class Sage300CredentialSerializer(serializers.ModelSerializer):
    """
    Sage300 credential serializer
    """
    class Meta:
        model = Sage300Credentials
        fields = '__all__'


class Sage300CredentialSerializer(serializers.ModelSerializer):
    
    api_key = serializers.CharField(required=False)
    api_secret = serializers.CharField(required=False)

    class Meta:
        model = Sage300Credentials
        fields = '__all__'

    def create(self, validated_data):
        try:
            username = validated_data.get('username')
            password = validated_data.get('password')
            identifier = validated_data.get('identifier')
            workspace = validated_data.get('workspace')
            sd_api_key = settings.SD_API_KEY
            sd_api_secret = settings.SD_API_SECRET

            # Initialize SageDesktopSDK or perform necessary actions.
            SageDesktopSDK(
                api_key=sd_api_key,
                api_secret=sd_api_secret,
                user_name=username,
                password=password,
                indentifier=identifier
            )

            # Save the Sage300Credentials instance and update the workspace
            instance = Sage300Credentials.objects.create(
                username=username,
                password=password,
                identifier=identifier,
                api_key=sd_api_key,
                api_secret=sd_api_secret,
                workspace=workspace
            )

            workspace.onboarding_state = 'EXPORT_SETTINGS'
            workspace.save()

            return instance

        except (InvalidUserCredentials, InvalidWebApiClientCredentials, UserAccountLocked, WebApiClientLocked) as e:
            raise serializers.ValidationError(str(e))
