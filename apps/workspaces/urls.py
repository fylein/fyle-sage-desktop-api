"""sage_desktop_api URL Configuration
The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include

from apps.workspaces.views import (
    ReadyView,
    WorkspaceView,
    Sage300CredsView,
    ImportSettingView,
    ExportSettingView,
    AdvancedSettingView,
    WorkspaceAdminsView,
    TriggerExportsView,
    ImportCodeFieldView
)


workspace_app_paths = [
    path('', WorkspaceView.as_view(), name='workspaces'),
    path('ready/', ReadyView.as_view(), name='ready'),
    path('<int:workspace_id>/credentials/sage300/', Sage300CredsView.as_view(), name='sage300-creds'),
    path('<int:workspace_id>/exports/trigger/', TriggerExportsView.as_view(), name='trigger-exports'),
    path('<int:workspace_id>/export_settings/', ExportSettingView.as_view(), name='export-settings'),
    path('<int:workspace_id>/import_settings/import_code_fields_config/', ImportCodeFieldView.as_view(), name='import-code-fields-config'),
    path('<int:workspace_id>/import_settings/', ImportSettingView.as_view(), name='import-settings'),
    path('<int:workspace_id>/advanced_settings/', AdvancedSettingView.as_view(), name='advanced-settings'),
    path('<int:workspace_id>/admins/', WorkspaceAdminsView.as_view(), name='admin'),
]

other_app_paths = [
    path('<int:workspace_id>/sage300/', include('apps.sage300.urls')),
    path('<int:workspace_id>/fyle/', include('apps.fyle.urls')),
    path('<int:workspace_id>/accounting_exports/', include('apps.accounting_exports.urls')),
    path('<int:workspace_id>/mappings/', include('apps.mappings.urls'))
]

urlpatterns = []
urlpatterns.extend(workspace_app_paths)
urlpatterns.extend(other_app_paths)
