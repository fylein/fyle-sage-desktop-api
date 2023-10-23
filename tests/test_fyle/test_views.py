import pytest
import json
from django.urls import reverse

from tests.helper import dict_compare_keys
from tests.test_fyle.fixtures import fixtures as fyle_fixtures


@pytest.mark.django_db(databases=["default"])
def test_fyle_expense_fields(
    api_client,
    test_connection,
    create_temp_workspace,
    add_fyle_credentials,
    add_sage300_creds,
    mocker,
):
    workspace_id = 1

    access_token = test_connection.access_token
    url = reverse("fyle-expense-fields", kwargs={"workspace_id": workspace_id})

    mocker.patch(
        "fyle.platform.apis.v1beta.admin.expense_fields.list_all",
        return_value=fyle_fixtures["get_all_custom_fields"],
    )

    api_client.credentials(HTTP_AUTHORIZATION="Bearer {}".format(access_token))

    response = api_client.get(url)
    assert response.status_code == 200
    response = json.loads(response.content)

    assert (
        dict_compare_keys(response, fyle_fixtures["fyle_expense_custom_fields"]) == []
    ), "expense group api return diffs in keys"
