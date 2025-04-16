from apps.fyle.queue import async_handle_webhook_callback


# This test is just for cov
def test_async_handle_webhook_callback(db, create_temp_workspace):
    """
    Test async_handle_webhook_callback
    """
    body = {
        "action": "ADMIN_APPROVED",
        "data": {
            "id": "rpG6L7AoSHvW",
            "org_id": "riseabovehate1",
            "state": "PAYMENT_PROCESSING"
        }
    }

    async_handle_webhook_callback(body, 1)

    body['action'] = 'ACCOUNTING_EXPORT_INITIATED'
    async_handle_webhook_callback(body, 1)

    body['action'] = 'UPDATED_AFTER_APPROVAL'
    async_handle_webhook_callback(body, 1)
