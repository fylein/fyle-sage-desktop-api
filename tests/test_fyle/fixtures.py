fixtures = {
    "get_my_profile": {
        "data": {
            "org": {
                "currency": "USD",
                "domain": "fyleforqvd.com",
                "id": "orNoatdUnm1w",
                "name": "Fyle For MS Dynamics Demo",
            },
            "org_id": "orNoatdUnm1w",
            "roles": [
                "FYLER",
                "VERIFIER",
                "PAYMENT_PROCESSOR",
                "FINANCE",
                "ADMIN",
                "AUDITOR",
            ],
            "user": {
                "email": "ashwin.t@fyle.in",
                "full_name": "Joanna",
                "id": "usqywo0f3nBY",
            },
            "user_id": "usqywo0f3nBY",
        }
    },
    "expense_filters_response": {
        "count": 2,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": 1,
                "condition": "employee_email",
                "operator": "in",
                "values": ["ashwinnnnn.t@fyle.in", "admin1@fyleforleaf.in"],
                "rank": "1",
                "workspace": 1,
                "join_by": "AND",
                "is_custom": False,
                "custom_field_type": "SELECT",
                "created_at": "2023-01-04T17:48:16.064064Z",
                "updated_at": "2023-01-05T08:05:23.660746Z",
                "workspace": 1,
            },
            {
                "id": 2,
                "condition": "spent_at",
                "operator": "lt",
                "values": ['2020-04-20 23:59:59+00'],
                "rank": "2",
                "workspace": 1,
                "join_by": None,
                "is_custom": False,
                "custom_field_type": "SELECT",
                "created_at": "2023-01-04T17:48:16.064064Z",
                "updated_at": "2023-01-05T08:05:23.660746Z",
                "workspace": 1,
            },
        ],
    },
    'accounting_export_response': {
        "count":2,
        "next":"None",
        "previous":"None",
        "results":[
            {
                "id":2,
                "created_at":"2023-10-26T03:24:43.513291Z",
                "updated_at":"2023-10-26T03:24:43.513296Z",
                "type":"FETCH_EXPENSES",
                "fund_source":"",
                "mapping_errors":"None",
                "task_id":"None",
                "description":[],
                "status":"IN_PROGRESS",
                "detail":[],
                "sage_300_errors":[],
                "exported_at":"None",
                "workspace":1,
                "expenses":[]
            },
            {
                "id":1,
                "created_at":"2023-10-26T03:24:43.511973Z",
                "updated_at":"2023-10-26T03:24:43.511978Z",
                "type":"FETCH_EXPENSES",
                "fund_source":"",
                "mapping_errors":"None",
                "task_id":"None",
                "description":[],
                "status":"IN_PROGRESS",
                "detail":[],
                "sage_300_errors":[],
                "exported_at":"None",
                "workspace":1,
                "expenses":[]
            }
        ]
    },
    "fyle_expense_custom_fields": [
        {"field_name": "employee_email", "type": "SELECT", "is_custom": False},
        {"field_name": "claim_number", "type": "TEXT", "is_custom": False},
        {"field_name": "report_title", "type": "TEXT", "is_custom": False},
        {"field_name": "spent_at", "type": "DATE", "is_custom": False},
        {"field_name": "Class", "type": "SELECT", "is_custom": True},
        {"field_name": "Fyle Categories", "type": "SELECT", "is_custom": True},
        {"field_name": "Operating System", "type": "SELECT", "is_custom": True},
        {"field_name": "User Dimension", "type": "SELECT", "is_custom": True},
        {"field_name": "Asdasdas", "type": "SELECT", "is_custom": True},
        {"field_name": "Nilesh Custom Field", "type": "SELECT", "is_custom": True},
    ],
    "get_all_custom_fields": [
        {
            "data": [
                {
                    "category_ids": [142151],
                    "code": None,
                    "column_name": "text_column6",
                    "created_at": "2021-10-22T07:50:04.613487+00:00",
                    "default_value": None,
                    "field_name": "Class",
                    "id": 197380,
                    "is_custom": True,
                    "is_enabled": True,
                    "is_mandatory": False,
                    "options": ["Servers", "Home", "Office"],
                    "org_id": "orGcBCVPijjO",
                    "placeholder": "Select Class",
                    "seq": 1,
                    "type": "SELECT",
                    "updated_at": "2023-01-01T05:35:26.345303+00:00",
                },
            ]
        }
    ],
}
