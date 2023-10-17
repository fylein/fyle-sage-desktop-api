from rest_framework import serializers

from .models import Sage300Credentials


class Sage300CredentialSerializer(serializers.ModelSerializer):
    """
    Sage300 credential serializer
    """
    class Meta:
        model = Sage300Credentials
        fields = '__all__'
