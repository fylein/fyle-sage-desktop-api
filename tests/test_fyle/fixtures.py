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
                "type":"FETCHING_REIMBURSABLE_EXPENSES",
                "fund_source":"",
                "mapping_errors":"None",
                "task_id":"None",
                "description":[],
                "status":"IN_PROGRESS",
                "detail":[],
                "sage300_errors":[],
                "exported_at":"None",
                "workspace":1,
                "export_id": 123,
                "expenses":[]
            },
            {
                "id":1,
                "created_at":"2023-10-26T03:24:43.511973Z",
                "updated_at":"2023-10-26T03:24:43.511978Z",
                "type":"FETCHING_CREDIT_CARD_EXPENENSES",
                "fund_source":"",
                "mapping_errors":"None",
                "task_id":"None",
                "description":[],
                "status":"IN_PROGRESS",
                "detail":[],
                "sage300_errors":[],
                "exported_at":"None",
                "export_id": 123,
                "workspace":1,
                "expenses":[]
            }
        ]
    },
    "errors_response": {
        "count":3,
        "next":"None",
        "previous":"None",
        "results":[
            {
                "id":1,
                "created_at":"2023-10-26T03:47:16.864421Z",
                "updated_at":"2023-10-26T03:47:16.864428Z",
                "type":"EMPLOYEE_MAPPING",
                "is_resolved": "false",
                "error_title":"Employee Mapping Error",
                "error_detail":"Employee Mapping Error",
                "workspace":1,
                "accounting_export":"None",
                "expense_attribute":"None"
            },
            {
                "id":2,
                "created_at":"2023-10-26T03:47:16.865103Z",
                "updated_at":"2023-10-26T03:47:16.865108Z",
                "type":"CATEGORY_MAPPING",
                "is_resolved": "false",
                "error_title":"Category Mapping Error",
                "error_detail":"Category Mapping Error",
                "workspace":1,
                "accounting_export":"None",
                "expense_attribute":"None"
            },
            {
                "id":3,
                "created_at":"2023-10-26T03:47:16.865303Z",
                "updated_at":"2023-10-26T03:47:16.865307Z",
                "type":"SAGE300_ERROR",
                "is_resolved": "false",
                "error_title":"Sage Error",
                "error_detail":"Sage Error",
                "workspace":1,
                "accounting_export":"None",
                "expense_attribute":"None"
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
    "fyle_fields_response": [
        {
            'attribute_type': 'COST_CENTER',
            'display_name': 'Cost Center',
            'is_dependant': False
        },
        {
            'attribute_type': 'PROJECT',
            'display_name': 'Project',
            'is_dependant': False
        }
    ],
    'accounting_export_summary_response': {
        "id":1,
        "created_at":"2023-10-27T04:53:59.287745Z",
        "updated_at":"2023-10-27T04:53:59.287750Z",
        "last_exported_at":"2023-10-27T04:53:59.287618Z",
        "next_export_at":"2023-10-27T04:53:59.287619Z",
        "export_mode":"AUTO",
        "total_accounting_export_count":10,
        "successful_accounting_export_count":5,
        "failed_accounting_export_count":5,
        "workspace":1
    },
    "import_settings_payload": {
        "import_settings": {
            "import_categories": True,
            "import_vendors_as_merchants": True,
        },
        "mapping_settings": [
            {
                "source_field": "COST_CENTER",
                "destination_field": "DEPARTMENT",
                "import_to_fyle": True,
                "is_custom": False,
                "source_placeholder": "cost center",
            },
            {
                "source_field": "PROJECT",
                "destination_field": "JOB",
                "import_to_fyle": True,
                "is_custom": False,
                "source_placeholder": "project",
            },
        ],
        "dependent_field_settings": {
            "cost_code_field_name": "Cost Code Jake Jellenahal",
            "cost_code_placeholder": "this is a dummy placeholder for cost code",
            "cost_category_field_name": "Cost Type Logan paul",
            "cost_category_placeholder": "this sia is dummy placeholder for cost type",
            "is_import_enabled": True,
        },
    },
    "import_settings_without_mapping": {
        "import_settings": {
            "import_categories": True,
            "import_vendors_as_merchants": True,
        },
        "mapping_settings": [
            {
                "source_field": "CLASS",
                "destination_field": "CUSTOMER",
                "import_to_fyle": True,
                "is_custom": True,
                "source_placeholder": "class",
            }
        ],
        "dependent_field_settings": None,
    },
    "import_settings_schedule_check": {
        "import_settings": {
            "import_categories": True,
            "import_vendors_as_merchants": True,
        },
        "mapping_settings": [
            {
                "source_field": "PROJECT",
                "destination_field": "PROJECT",
                "import_to_fyle": True,
                "is_custom": False,
                "source_placeholder": "Select Project",
            }
        ],
        "dependent_field_settings": None,
    },
    "response": {
        "import_settings": {
            "import_categories": True,
            "import_vendors_as_merchants": True,
        },
        "mapping_settings": [
            {
                "source_field": "COST_CENTER",
                "destination_field": "CLASS",
                "import_to_fyle": True,
                "is_custom": False,
                "source_placeholder": "",
            },
            {
                "source_field": "PROJECT",
                "destination_field": "DEPARTMENT",
                "import_to_fyle": True,
                "is_custom": False,
                "source_placeholder": "",
            },
            {
                "source_field": "CLASS",
                "destination_field": "CUSTOMER",
                "import_to_fyle": True,
                "is_custom": True,
                "source_placeholder": "",
            },
        ],
        "workspace_id": 9,
        "dependent_field_settings": {
            "cost_code_field_name": "Cost Code Jake Jellenahal",
            "cost_code_placeholder": "this is a dummy placeholder for cost code",
            "cost_category_field_name": "Cost Type Logan paul",
            "cost_category_placeholder": "this sia is dummy placeholder for cost type",
            "is_import_enabled": True,
        },
    },
    "invalid_general_mappings": {
        "import_settings": {
            "import_categories": True,
            "import_vendors_as_merchants": True,
        },
        "mapping_settings": [
            {
                "source_field": "COST_CENTER",
                "destination_field": "DEPARTMENT",
                "import_to_fyle": True,
                "is_custom": False,
                "source_placeholder": "cost center",
            }
        ],
        "dependent_field_settings": None,
    },
    "invalid_mapping_settings": {
        "import_settings": {
            "import_categories": True,
            "import_vendors_as_merchants": True,
        },
        "mapping_settings": None,
        "dependent_field_settings": None,
    },
}
