from django.urls import path

from .views import ConnectSage300View


urlpatterns = [
    path('<int:workspace_id>/credentials/sage_300/delete/', ConnectSage300View.as_view({'post': 'delete'}), name='sage300-delete'),
    path('<int:workspace_id>/credentials/sage_300/', ConnectSage300View.as_view({'post': 'post', 'get': 'get'}), name='sage300-creds')
]
