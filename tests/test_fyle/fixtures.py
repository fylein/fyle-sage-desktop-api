fixtures = {
    'get_my_profile': {
        'data': {
            'org': {
                'currency': 'USD',
                'domain': 'fyleforqvd.com',
                'id': 'orNoatdUnm1w',
                'name': 'Fyle For MS Dynamics Demo',
            },
            'org_id': 'orNoatdUnm1w',
            'roles': [
                'FYLER',
                'VERIFIER',
                'PAYMENT_PROCESSOR',
                'FINANCE',
                'ADMIN',
                'AUDITOR',
            ],
            'user': {
                'email': 'ashwin.t@fyle.in',
                'full_name': 'Joanna',
                'id': 'usqywo0f3nBY'
            },
            'user_id': 'usqywo0f3nBY',
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
    }
}
