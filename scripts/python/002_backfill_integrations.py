from apps.workspaces.models import Workspace
from apps.workspaces.triggers import AdvancedSettingsTriggers

workspaces = Workspace.objects.filter(onboarding_state='COMPLETE')
for workspace in workspaces:
    print(workspace.id, workspace.name, sep=' | ')
    AdvancedSettingsTriggers.post_to_integration_settings(workspace.id, True)
