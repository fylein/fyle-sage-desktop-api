
from django.urls import path

from apps.sage300.views import ImportSage300AttributesView


urlpatterns = [
    path('import_attributes/', ImportSage300AttributesView.as_view(), name='import-sage300-attributes'),
]
