from django.urls import path

from apps.workspaces.views import Sage300CredsView


urlpatterns = [
    path('<int:workspace_id>/credentials/sage_300/', Sage300CredsView.as_view(), name='sage300-creds'),
]
