"""fyle_sage_desktop URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
1. Add an import: from my_app import views
2. Add a URL to urlpatterns: path('', views.home, name='home')
Class-based views
1. Add an import: from other_app.views import Home
2. Add a URL to urlpatterns: path('', Home.as_view(), name='home')
Including another URLconf
1. Import the include() function: from django.urls import include, path
2. Add a URL to urlpatterns: path('blog/', include('blog.urls'))
"""

from django.urls import path
import itertools

from apps.fyle.views import (
    ImportFyleAttributesView,
    ExpenseFilterView,
    ExpenseFilterDeleteView,
    CustomFieldView,
    FyleFieldsView,
    DependentFieldSettingView,
    ExportableAccountingExportView,
    AccountingExportSyncView,
    SkippedExpenseView,
    WebhookCallbackView
)


accounting_exports_path = [
    path('exportable_accounting_exports/', ExportableAccountingExportView.as_view(), name='exportable-accounting-exports'),
    path('accounting_exports/sync/', AccountingExportSyncView.as_view(), name='sync-accounting-exports'),
]

other_paths = [
    path('expense_filters/<int:pk>/', ExpenseFilterDeleteView.as_view(), name='expense-filters'),
    path('expense_filters/', ExpenseFilterView.as_view(), name='expense-filters'),
    path('expense_fields/', CustomFieldView.as_view(), name='fyle-expense-fields'),
    path('fields/', FyleFieldsView.as_view(), name='fyle-fields'),
    path('dependent_field_settings/', DependentFieldSettingView.as_view(), name='dependent-field'),
    path('expenses/', SkippedExpenseView.as_view(), name='expenses'),
    path('webhook_callback/', WebhookCallbackView.as_view(), name='webhook-callback'),
]

fyle_dimension_paths = [
    path('import_attributes/', ImportFyleAttributesView.as_view(), name='import-fyle-attributes')
]

urlpatterns = list(itertools.chain(accounting_exports_path, fyle_dimension_paths, other_paths))
