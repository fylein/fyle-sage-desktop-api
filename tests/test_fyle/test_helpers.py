import pytest
from requests import Response
from apps.fyle.helpers import (
    Q,
    construct_expense_filter,
    get_fyle_orgs,
    get_request,
    post_request,
    construct_expense_filter_query,
)
from apps.fyle.models import ExpenseFilter
from tests.test_fyle.fixtures import fixtures as data


def test_get_fyle_orgs(mocker):
    mocker.patch(
        'apps.fyle.helpers.get_request',
        return_value={
            'data': [
                {
                    'id': 1,
                    'name': 'Fyle Org 1'
                }
            ]
        }
    )

    fyle_org = get_fyle_orgs(
        refresh_token='refresh_token',
        cluster_domain='cluster_domain'
    )

    assert fyle_org.get('data')[0].get('id') == 1
    assert fyle_org.get('data')[0].get('name') == 'Fyle Org 1'


def test_get_request(mocker):
    mock_response = Response()
    mock_response.status_code = 200
    mock_response._content = b'{"data": "1234"}'

    mocker.patch(
        'apps.fyle.helpers.requests.get',
        return_value=mock_response
    )

    mocker.patch(
        'apps.fyle.helpers.get_access_token',
        return_value='access_token'
    )

    response = get_request(
        url='https://api.fyle.tech/api/v7/cluster/',
        params={
            'id': 1,
            'is_active': True
        },
        refresh_token='refresh_token',
    )

    assert response.get('data') == "1234"

    mock_response.status_code = 400
    mock_response._content = b'{"error": "error"}'

    try:
        response = get_request(
            url='https://api.fyle.tech/api/v7/cluster/',
            params={
                'id': 1,
                'is_active': True
            },
            refresh_token = 'refresh_token',
        )
    except Exception as e:
        assert str(e) == '{"error": "error"}'


def test_post_request(mocker):
    mock_response = Response()
    mock_response.status_code = 200
    mock_response._content = b'{"data": "1234"}'

    mocker.patch(
        'apps.fyle.helpers.requests.post',
        return_value=mock_response
    )

    mocker.patch(
        'apps.fyle.helpers.get_access_token',
        return_value='access_token'
    )

    response = post_request(
        url='https://api.fyle.tech/api/v7/cluster/',
        body={
            'id': 1,
            'is_active': True
        },
        refresh_token='refresh_token',
    )

    assert response.get('data') == "1234"

    mock_response.status_code = 400
    mock_response._content = b'{"error": "error"}'

    try:
        response = post_request(
            url='https://api.fyle.tech/api/v7/cluster/',
            body={
                'id': 1,
                'is_active': True
            },
            refresh_token='refresh_token',
        )
    except Exception as e:
        assert str(e) == '{"error": "error"}'


def test_construct_expense_filter_query(
    db,
    mocker
):
    expense_payload_data = data["expense_filter_payload"]

    expense_payload_req = []

    for expense_payload in expense_payload_data:
        expense_filter = mocker.MagicMock(spec=ExpenseFilter)
        expense_filter.condition = expense_payload.get('condition')
        expense_filter.rank = expense_payload.get('rank')
        expense_filter.join_by = expense_payload.get('join_by')
        expense_filter.custom_field_type = expense_payload.get('custom_field_type')
        expense_filter.is_custom = expense_payload.get('is_custom')
        expense_filter.operator = expense_payload.get('operator')
        expense_filter.values = expense_payload.get('values')
        expense_filter.workspace_id = expense_payload.get('workspace_id')

        expense_payload_req.append(expense_filter)

    returned_filter = construct_expense_filter_query(expense_filters=expense_payload_req)

    assert str(returned_filter) == "(OR: ('custom_properties__some_field__isnull', True), ('custom_properties__some_field__exact', None), ('custom_properties__employee_id__not_in', [12, 13]), ('custom_properties__is_email_sent__not_in', False))"


@pytest.mark.django_db()
def test_construct_expense_filter():
    # employee-email-is-equal
    expense_filter = ExpenseFilter(condition='employee_email', operator='in', values=['killua.z@fyle.in', 'naruto.u@fyle.in'], rank=1)
    constructed_expense_filter = construct_expense_filter(expense_filter)

    filter_1 = {'employee_email__in': ['killua.z@fyle.in', 'naruto.u@fyle.in']}
    response = Q(**filter_1)

    assert constructed_expense_filter == response

    # employee-email-is-equal-one-email-only
    expense_filter = ExpenseFilter(condition='employee_email', operator='in', values=['killua.z@fyle.in'], rank=1)
    constructed_expense_filter = construct_expense_filter(expense_filter)

    filter_1 = {'employee_email__in': ['killua.z@fyle.in']}
    response = Q(**filter_1)

    assert constructed_expense_filter == response

    # claim-number-is-equal
    expense_filter = ExpenseFilter(condition='claim_number', operator='in', values=['ajdnwjnadw', 'ajdnwjnlol'], rank=1)
    constructed_expense_filter = construct_expense_filter(expense_filter)

    filter_1 = {'claim_number__in': ['ajdnwjnadw', 'ajdnwjnlol']}
    response = Q(**filter_1)

    assert constructed_expense_filter == response

    # claim-number-is-equal-one-claim_number-only
    expense_filter = ExpenseFilter(condition='claim_number', operator='in', values=['ajdnwjnadw'], rank=1)
    constructed_expense_filter = construct_expense_filter(expense_filter)

    filter_1 = {'claim_number__in': ['ajdnwjnadw']}
    response = Q(**filter_1)

    assert constructed_expense_filter == response

    # report-name-is-equal
    expense_filter = ExpenseFilter(condition='report_title', operator='iexact', values=['#17:  Dec 2022'], rank=1)
    constructed_expense_filter = construct_expense_filter(expense_filter)

    filter_1 = {'report_title__iexact': '#17:  Dec 2022'}
    response = Q(**filter_1)

    assert constructed_expense_filter == response

    # report-name-contains
    expense_filter = ExpenseFilter(condition='report_title', operator='icontains', values=['Dec 2022'], rank=1)
    constructed_expense_filter = construct_expense_filter(expense_filter)

    filter_1 = {'report_title__icontains': 'Dec 2022'}
    response = Q(**filter_1)

    assert constructed_expense_filter == response

    # spent-at-is-before
    expense_filter = ExpenseFilter(condition='spent_at', operator='lt', values=['2020-04-20 23:59:59+00'], rank=1)
    constructed_expense_filter = construct_expense_filter(expense_filter)

    filter_1 = {'spent_at__lt': '2020-04-20 23:59:59+00'}
    response = Q(**filter_1)

    assert constructed_expense_filter == response

    # spent-at-is-on-or-before
    expense_filter = ExpenseFilter(condition='spent_at', operator='lte', values=['2020-04-20 23:59:59+00'], rank=1)
    constructed_expense_filter = construct_expense_filter(expense_filter)

    filter_1 = {'spent_at__lte': '2020-04-20 23:59:59+00'}
    response = Q(**filter_1)

    assert constructed_expense_filter == response

    # category_in
    expense_filter = ExpenseFilter(
        condition = 'category',
        operator = 'in',
        values = ['anish'],
        rank = 1
    )
    constructed_expense_filter = construct_expense_filter(expense_filter)

    filter_1 = {'category__in':['anish']}
    response = Q(**filter_1)

    assert constructed_expense_filter == response

    # category_not_in
    expense_filter = ExpenseFilter(
        condition = 'category',
        operator = 'not_in',
        values = ['anish', 'singh'],
        rank = 1
    )
    constructed_expense_filter = construct_expense_filter(expense_filter)

    filter_1 = {'category__in':['anish', 'singh']}
    response = ~Q(**filter_1)

    assert constructed_expense_filter == response

    # custom-properties-number-is-equal
    expense_filter = ExpenseFilter(condition='Gon Number', operator='in', values=[102, 108], rank=1, is_custom=True)
    constructed_expense_filter = construct_expense_filter(expense_filter)

    filter_1 = {'custom_properties__Gon Number__in': [102, 108]}
    response = Q(**filter_1)

    assert constructed_expense_filter == response

    # custom-properties-number-is-not-empty
    expense_filter = ExpenseFilter(condition='Gon Number', operator='isnull', values=['False'], rank=1, is_custom=True)
    constructed_expense_filter = construct_expense_filter(expense_filter)

    filter_1 = {'custom_properties__Gon Number__exact': None}
    response = ~Q(**filter_1)

    assert constructed_expense_filter == response

    # custom-properties-number-is--empty
    expense_filter = ExpenseFilter(condition='Gon Number', operator='isnull', values=['True'], rank=1, is_custom=True)
    constructed_expense_filter = construct_expense_filter(expense_filter)

    filter_1 = {'custom_properties__Gon Number__isnull': True}
    filter_2 = {'custom_properties__Gon Number__exact': None}
    response = Q(**filter_1) | Q(**filter_2)

    assert constructed_expense_filter == response

    # custom-properties-text-is-equal
    expense_filter = ExpenseFilter(condition='Killua Text', operator='in', values=['hunter', 'naruto', 'sasuske'], rank=1, is_custom=True)
    constructed_expense_filter = construct_expense_filter(expense_filter)

    filter_1 = {'custom_properties__Killua Text__in': ['hunter', 'naruto', 'sasuske']}
    response = Q(**filter_1)

    assert constructed_expense_filter == response

    # custom-properties-text-is-not-empty
    expense_filter = ExpenseFilter(condition='Killua Text', operator='isnull', values=['False'], rank=1, is_custom=True)
    constructed_expense_filter = construct_expense_filter(expense_filter)

    filter_1 = {'custom_properties__Killua Text__exact': None}
    response = ~Q(**filter_1)

    assert constructed_expense_filter == response

    # custom-properties-text-is--empty
    expense_filter = ExpenseFilter(condition='Killua Text', operator='isnull', values=['True'], rank=1, is_custom=True)
    constructed_expense_filter = construct_expense_filter(expense_filter)

    filter_1 = {'custom_properties__Killua Text__isnull': True}
    filter_2 = {'custom_properties__Killua Text__exact': None}
    response = Q(**filter_1) | Q(**filter_2)

    assert constructed_expense_filter == response

    # custom-properties-select-is-equal
    expense_filter = ExpenseFilter(condition='Kratos', operator='in', values=['BOOK', 'Dev-D'], rank=1, is_custom=True)
    constructed_expense_filter = construct_expense_filter(expense_filter)

    filter_1 = {'custom_properties__Kratos__in': ['BOOK', 'Dev-D']}
    response = Q(**filter_1)

    assert constructed_expense_filter == response

    # custom-properties-select-is-equal-one-value
    expense_filter = ExpenseFilter(condition='Kratos', operator='in', values=['BOOK'], rank=1, is_custom=True)
    constructed_expense_filter = construct_expense_filter(expense_filter)

    filter_1 = {'custom_properties__Kratos__in': ['BOOK']}
    response = Q(**filter_1)

    assert constructed_expense_filter == response

    # custom-properties-select-is-not-empty
    expense_filter = ExpenseFilter(condition='Kratos', operator='isnull', values=['False'], rank=1, is_custom=True)
    constructed_expense_filter = construct_expense_filter(expense_filter)

    filter_1 = {'custom_properties__Kratos__exact': None}
    response = ~Q(**filter_1)

    assert constructed_expense_filter == response

    # custom-properties-select-is--empty
    expense_filter = ExpenseFilter(condition='Kratos', operator='isnull', values=['True'], rank=1, is_custom=True)
    constructed_expense_filter = construct_expense_filter(expense_filter)

    filter_1 = {'custom_properties__Kratos__isnull': True}
    filter_2 = {'custom_properties__Kratos__exact': None}
    response = Q(**filter_1) | Q(**filter_2)

    assert constructed_expense_filter == response
