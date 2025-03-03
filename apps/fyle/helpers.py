import json
from typing import List

import requests
from django.conf import settings
from django.db.models import Q
from fyle_integrations_platform_connector import PlatformConnector
from rest_framework.exceptions import ValidationError

from apps.accounting_exports.models import AccountingExport
from apps.fyle.constants import DEFAULT_FYLE_CONDITIONS
from apps.fyle.models import ExpenseFilter
from apps.workspaces.models import ExportSetting, FyleCredential, Workspace


def construct_expense_filter(expense_filter):
    constructed_expense_filter = {}
    # If the expense filter is a custom field
    if expense_filter.is_custom:
        # If the operator is not isnull
        if expense_filter.operator != 'isnull':
            # If the custom field is of type SELECT and the operator is not_in
            if expense_filter.custom_field_type == 'SELECT' and expense_filter.operator == 'not_in':
                # Construct the filter for the custom property
                filter1 = {
                    f'custom_properties__{expense_filter.condition}__in': expense_filter.values
                }
                # Invert the filter using the ~Q operator and assign it to the constructed expense filter
                constructed_expense_filter = ~Q(**filter1)
            else:
                # If the custom field is of type NUMBER, convert the values to integers
                if expense_filter.custom_field_type == 'NUMBER':
                    expense_filter.values = [int(value) for value in expense_filter.values]
                # If the expense filter is a custom field and the operator is yes or no(checkbox)
                if expense_filter.custom_field_type == 'BOOLEAN':
                    expense_filter.values[0] = True if expense_filter.values[0] == 'true' else False
                # Construct the filter for the custom property
                filter1 = {
                    f'custom_properties__{expense_filter.condition}__{expense_filter.operator}':
                        expense_filter.values[0] if len(expense_filter.values) == 1 and expense_filter.operator != 'in'
                        else expense_filter.values
                }
                # Assign the constructed filter to the constructed expense filter
                constructed_expense_filter = Q(**filter1)

        # If the expense filter is a custom field and the operator is isnull
        elif expense_filter.operator == 'isnull':
            # Determine the value for the isnull filter based on the first value in the values list
            expense_filter_value: bool = True if expense_filter.values[0].lower() == 'true' else False
            # Construct the isnull filter for the custom property
            filter1 = {
                f'custom_properties__{expense_filter.condition}__isnull': expense_filter_value
            }
            # Construct the exact filter for the custom property
            filter2 = {
                f'custom_properties__{expense_filter.condition}__exact': None
            }
            if expense_filter_value:
                # If the isnull filter value is True, combine the two filters using the | operator and assign it to the constructed expense filter
                constructed_expense_filter = Q(**filter1) | Q(**filter2)
            else:
                # If the isnull filter value is False, invert the exact filter using the ~Q operator and assign it to the constructed expense filter
                constructed_expense_filter = ~Q(**filter2)
    # for category non-custom field with not_in as operator, to check this later on
    elif expense_filter.condition == 'category' and expense_filter.operator == 'not_in' and not expense_filter.is_custom:
        # construct the filter
        filter1 = {
            f'{expense_filter.condition}__in': expense_filter.values
        }
        # Invert the filter using the ~Q operator and assign it to the constructed expense filter
        constructed_expense_filter = ~Q(**filter1)
    # For all non-custom fields
    else:
        # Construct the filter for the non-custom field
        filter1 = {
            f'{expense_filter.condition}__{expense_filter.operator}':
                expense_filter.values[0] if len(expense_filter.values) == 1 and expense_filter.operator != 'in'
                else expense_filter.values
        }
        # Assign the constructed filter to the constructed expense filter
        constructed_expense_filter = Q(**filter1)

    # Return the constructed expense filter
    return constructed_expense_filter


def construct_expense_filter_query(expense_filters: List[ExpenseFilter]):
    final_filter = None
    join_by = None

    for expense_filter in expense_filters:
        constructed_expense_filter = construct_expense_filter(expense_filter)

        # If this is the first filter, set it as the final filter
        if expense_filter.rank == 1:
            final_filter = (constructed_expense_filter)

        # If join by is AND, OR
        elif expense_filter.rank != 1:
            if join_by == 'AND':
                final_filter = final_filter & (constructed_expense_filter)
            else:
                final_filter = final_filter | (constructed_expense_filter)

        # Set the join type for the additonal filter
        join_by = expense_filter.join_by

    return final_filter


def post_request(url, body, refresh_token=None):
    """
    Create a HTTP post request.
    """
    access_token = None
    api_headers = {
        'Content-Type': 'application/json',
    }
    if refresh_token:
        access_token = get_access_token(refresh_token)
        api_headers['Authorization'] = 'Bearer {0}'.format(access_token)

    response = requests.post(
        url,
        headers=api_headers,
        data=json.dumps(body)
    )

    if response.status_code in (200, 201):
        return json.loads(response.text)
    else:
        raise Exception(response.text)


def get_request(url, params, refresh_token):
    """
    Create a HTTP get request.
    """
    access_token = get_access_token(refresh_token)
    api_headers = {
        'content-type': 'application/json',
        'Authorization': 'Bearer {0}'.format(access_token)
    }
    api_params = {}

    for k in params:
        # ignore all unused params
        if not params[k] is None:
            p = params[k]

            # convert boolean to lowercase string
            if isinstance(p, bool):
                p = str(p).lower()

            api_params[k] = p

    response = requests.get(
        url,
        headers=api_headers,
        params=api_params
    )

    if response.status_code == 200:
        return json.loads(response.text)
    else:
        raise Exception(response.text)


def get_access_token(refresh_token: str) -> str:
    """
    Get access token from fyle
    """
    api_data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': settings.FYLE_CLIENT_ID,
        'client_secret': settings.FYLE_CLIENT_SECRET
    }

    return post_request(settings.FYLE_TOKEN_URI, body=api_data)['access_token']


def get_cluster_domain(refresh_token: str) -> str:
    """
    Get cluster domain name from fyle
    :param refresh_token: (str)
    :return: cluster_domain (str)
    """
    cluster_api_url = '{0}/oauth/cluster/'.format(settings.FYLE_BASE_URL)

    return post_request(cluster_api_url, {}, refresh_token)['cluster_domain']


def get_expense_fields(workspace_id: int):
    """
    Get expense custom fields from fyle
    :param workspace_id: (int)
    :return: list of custom expense fields
    """

    fyle_credentails = FyleCredential.objects.get(workspace_id=workspace_id)
    platform = PlatformConnector(fyle_credentails)
    custom_fields = platform.expense_custom_fields.list_all()

    response = []
    response.extend(DEFAULT_FYLE_CONDITIONS)
    for custom_field in custom_fields:
        if custom_field['type'] in ('SELECT', 'NUMBER', 'TEXT', 'BOOLEAN'):
            response.append({
                'field_name': custom_field['field_name'],
                'type': custom_field['type'],
                'is_custom': custom_field['is_custom']
            })

    return response


def get_fyle_orgs(refresh_token: str, cluster_domain: str):
    """
    Get fyle orgs of a user
    """
    api_url = '{0}/api/orgs/'.format(cluster_domain)

    return get_request(api_url, {}, refresh_token)


def sync_dimensions(fyle_credentials: FyleCredential) -> None:
    platform = PlatformConnector(fyle_credentials)

    platform.import_fyle_dimensions()


def connect_to_platform(workspace_id: int) -> PlatformConnector:
    fyle_credentials: FyleCredential = FyleCredential.objects.get(workspace_id=workspace_id)

    return PlatformConnector(fyle_credentials=fyle_credentials)


def get_exportable_accounting_exports_ids(workspace_id: int):
    """
    Get List of accounting exports ids
    """

    export_setting = ExportSetting.objects.get(workspace_id=workspace_id)
    fund_source = []

    if export_setting.reimbursable_expenses_export_type:
        fund_source.append('PERSONAL')
    if export_setting.credit_card_expense_export_type:
        fund_source.append('CCC')

    accounting_export_ids = AccountingExport.objects.filter(
        workspace_id=workspace_id,
        exported_at__isnull=True,
        fund_source__in=fund_source
    ).values_list('id', flat=True)

    return accounting_export_ids


def assert_valid_request(workspace_id:int, org_id:str):
    """
    Assert if the request is valid by checking
    the url_workspace_id and fyle_org_id workspace
    """
    workspace = Workspace.objects.get(org_id=org_id)
    if workspace.id != workspace_id:
        raise ValidationError('Workspace mismatch')
