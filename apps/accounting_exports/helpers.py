from apps.accounting_exports.models import AccountingExport
from apps.fyle.models import Expense
import django_filters


class AdvanceSearchFilter(django_filters.FilterSet):
    def filter_queryset(self, queryset):
        or_filtered_queryset = queryset.none()
        or_filter_fields = getattr(self.Meta, 'or_fields', [])
        or_field_present = False

        for field_name in self.Meta.fields:
            value = self.data.get(field_name)
            if value:
                if field_name == 'is_skipped':
                    value = True if str(value) == 'true' else False

                if field_name in ('status__in', 'type__in', 'id__in'):
                    value_lt = value.split(',')
                    filter_instance = self.filters[field_name]
                    queryset = filter_instance.filter(queryset, value_lt)
                else:
                    filter_instance = self.filters[field_name]
                    queryset = filter_instance.filter(queryset, value)

        for field_name in or_filter_fields:
            value = self.data.get(field_name)
            if value:
                or_field_present = True
                filter_instance = self.filters[field_name]
                field_filtered_queryset = filter_instance.filter(queryset, value)
                or_filtered_queryset |= field_filtered_queryset

        if or_field_present:
            queryset = queryset & or_filtered_queryset
            return queryset

        return queryset


class AccountingExportSearchFilter(AdvanceSearchFilter):
    id__in = django_filters.CharFilter(lookup_expr='in', field_name='id')
    exported_at__gte = django_filters.DateTimeFilter(lookup_expr='gte', field_name='exported_at')
    exported_at__lte = django_filters.DateTimeFilter(lookup_expr='lte', field_name='exported_at')
    status__in = django_filters.CharFilter(lookup_expr='in', field_name='status')
    type__in = django_filters.CharFilter(lookup_expr='in', field_name='type')
    expenses__expense_number = django_filters.CharFilter(field_name='expenses__expense_number', lookup_expr='icontains')
    expenses__employee_name = django_filters.CharFilter(field_name='expenses__employee_name', lookup_expr='icontains')
    expenses__employee_email = django_filters.CharFilter(field_name='expenses__employee_email', lookup_expr='icontains')
    expenses__claim_number = django_filters.CharFilter(field_name='expenses__claim_number', lookup_expr='icontains')

    class Meta:
        model = AccountingExport
        fields = ['exported_at__gte', 'exported_at__lte', 'status__in', 'type__in', 'id__in']
        or_fields = ['expenses__expense_number', 'expenses__employee_name', 'expenses__employee_email', 'expenses__claim_number']


class ExpenseSearchFilter(AdvanceSearchFilter):
    org_id = django_filters.CharFilter()
    is_skipped = django_filters.BooleanFilter()
    updated_at__gte = django_filters.DateTimeFilter(lookup_expr='gte', field_name='updated_at')
    updated_at__lte = django_filters.DateTimeFilter(lookup_expr='lte', field_name='updated_at')
    expense_number = django_filters.CharFilter(field_name='expense_number', lookup_expr='icontains')
    employee_name = django_filters.CharFilter(field_name='employee_name', lookup_expr='icontains')
    employee_email = django_filters.CharFilter(field_name='employee_email', lookup_expr='icontains')
    claim_number = django_filters.CharFilter(field_name='claim_number', lookup_expr='icontains')

    class Meta:
        model = Expense
        fields = ['org_id', 'is_skipped', 'updated_at__gte', 'updated_at__lte']
        or_fields = ['expense_number', 'employee_name', 'employee_email', 'claim_number']
