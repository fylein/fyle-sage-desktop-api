from requests import Response
from apps.fyle.helpers import (
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
