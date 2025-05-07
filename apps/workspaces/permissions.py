import logging

from django.core.cache import cache
from rest_framework import permissions

from apps.users.models import User
from apps.workspaces.models import Workspace

logger = logging.getLogger(__name__)
logger.level = logging.INFO


class WorkspacePermissions(permissions.BasePermission):
    """
    Permission check for users <> workspaces
    """

    def validate_and_cache(self, workspace_users: list, user: User, workspace_id: str, payload: dict, cache_users: bool = False) -> bool:
        """
        Validate and cache workspace users
        :param workspace_users: Workspace users
        :param user: User
        :param workspace_id: Workspace ID
        :param cache_users: Cache users flag
        :return: Boolean
        """
        if user.id in workspace_users:
            if cache_users:
                cache.set(workspace_id, workspace_users, 172800)
            return True

        logger.error(f'User {user.id} is not allowed to access workspace {workspace_id}')
        logger.info(f'Permission was cached earlier: {not cache_users}')
        logger.info(f'Allowed users: {workspace_users}')
        logger.info(f'Payload: {payload}')

        cache.delete(str(workspace_id))

        return False

    def has_permission(self, request: any, view: any) -> bool:
        """
        Check if user has permission
        :param request: Request
        :param view: View
        :return Boolean
        """
        workspace_id = str(view.kwargs.get("workspace_id"))
        user = request.user
        workspace_users = cache.get(workspace_id)

        if workspace_users:
            return self.validate_and_cache(workspace_users, user, workspace_id, request.data)
        else:
            workspace_users = Workspace.objects.filter(pk=workspace_id).values_list("user", flat=True)
            return self.validate_and_cache(workspace_users, user, workspace_id, request.data, True)
