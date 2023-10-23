
from django.urls import path

from apps.sage300.views import ImportSage300AttributesView, Sage300FieldsView


urlpatterns = [
    path('import_attributes/', ImportSage300AttributesView.as_view(), name='import-sage300-attributes'),
    path('fields/', Sage300FieldsView.as_view(), name='sage300-fields')
]
