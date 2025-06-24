from rest_framework.serializers import ValidationError
from rest_framework.views import Response
from apps.workspaces.models import Sage300Credential
from apps.workspaces.tasks import patch_integration_settings


def assert_valid(condition: bool, message: str) -> Response or None:
    """
    Assert conditions
    :param condition: Boolean condition
    :param message: Bad request message
    :return: Response or None
    """
    if not condition:
        raise ValidationError(detail={
            'message': message
        })


class LookupFieldMixin:
    lookup_field = 'workspace_id'

    def filter_queryset(self, queryset):
        if self.lookup_field in self.kwargs:
            lookup_value = self.kwargs[self.lookup_field]
            filter_kwargs = {self.lookup_field: lookup_value}
            queryset = queryset.filter(**filter_kwargs)
        return super().filter_queryset(queryset)


def invalidate_sage300_credentials(workspace_id, sage300_credentials=None):
    if not sage300_credentials:
        sage300_credentials = Sage300Credential.objects.filter(workspace_id=workspace_id, is_expired=False).first()

    if sage300_credentials:
        if not sage300_credentials.is_expired:
            patch_integration_settings(workspace_id, is_token_expired=True)
            sage300_credentials.is_expired = True
            sage300_credentials.save()
