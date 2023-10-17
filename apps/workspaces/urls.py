from django.urls import path

from .views import (
    ConnectSage300View,
    ImportSettingView,
    AdvancedSettingView
)


urlpatterns = [
    path('<int:workspace_id>/credentials/sage_300/delete/', ConnectSage300View.as_view({'post': 'delete'}), name='sage300-delete'),
    path('<int:workspace_id>/credentials/sage_300/', ConnectSage300View.as_view({'post': 'post', 'get': 'get'}), name='sage300-creds'),
    path('<int:workspace_id>/export_settings/', ImportSettingView.as_view(), name='import-settings'),
    path('<int:workspace_id>/export_settings/', AdvancedSettingView.as_view(), name='advanced-settings')
]
