from django.urls import path

from apps.fyle.views import CustomFieldView

urlpatterns = [
    path('expense_fields/', CustomFieldView.as_view(), name='fyle-expense-fields'),
]
