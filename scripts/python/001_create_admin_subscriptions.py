# Create admin subscriptions for existing workspaces

from apps.workspaces.tasks import async_create_admin_subcriptions
from apps.workspaces.models import Workspace

workspaces = Workspace.objects.filter(onboarding_state='COMPLETE').all()

for workspace in workspaces:
    try:
        async_create_admin_subcriptions(workspace.id)
    except Exception as e:
        print('Error while creating admin subscriptions for workspace - {} with ID - {}'.format(workspace.name, workspace.id))
        print(e.__dict__)
