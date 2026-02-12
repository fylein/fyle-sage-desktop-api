from unittest.mock import Mock, patch

import pytest
from common.event import BaseEvent
from fyle_accounting_library.rabbitmq.models import FailedEvent

from workers.actions import handle_tasks
from workers.helpers import get_routing_key, publish_to_rabbitmq, RoutingKeyEnum, WorkerActionEnum
from workers.worker import Worker, main


@pytest.fixture
def mock_qconnector():
    return Mock()


@pytest.fixture
def export_worker(mock_qconnector):
    worker = Worker(
        rabbitmq_url='mock_url',
        rabbitmq_exchange='mock_exchange',
        queue_name='mock_queue',
        binding_keys=['mock.binding.key'],
        qconnector_cls=Mock(return_value=mock_qconnector),
        event_cls=BaseEvent
    )
    worker.qconnector = mock_qconnector
    worker.event_cls = BaseEvent
    return worker


@pytest.mark.django_db
def test_handle_tasks_action_none():
    """Test handle_tasks with None action"""
    payload = {'action': None, 'data': {'workspace_id': 1}}
    result = handle_tasks(payload)
    assert result is None


@pytest.mark.django_db
def test_handle_tasks_invalid_action():
    """Test handle_tasks with invalid action"""
    payload = {'action': 'INVALID_ACTION_THAT_DOES_NOT_EXIST', 'data': {'workspace_id': 1}}
    result = handle_tasks(payload)
    assert result is None


@pytest.mark.django_db
def test_handle_tasks_method_none():
    """Test handle_tasks when method is not in ACTION_METHOD_MAP"""
    with patch('workers.actions.ACTION_METHOD_MAP', {}):
        payload = {'action': 'EXPORT.P0.DASHBOARD_SYNC', 'data': {'workspace_id': 1}}
        result = handle_tasks(payload)
        assert result is None


@pytest.mark.django_db
def test_handle_tasks_success():
    """Test handle_tasks with valid action"""
    with patch('workers.actions.import_string') as mock_import_string:
        mock_func = Mock()
        mock_import_string.return_value = mock_func

        payload = {
            'action': 'EXPORT.P0.DASHBOARD_SYNC',
            'data': {'workspace_id': 1, 'triggered_by': 'DASHBOARD_SYNC'}
        }
        handle_tasks(payload)

        mock_import_string.assert_called_once_with('apps.workspaces.tasks.export_to_sage300')
        mock_func.assert_called_once_with(workspace_id=1, triggered_by='DASHBOARD_SYNC')


@pytest.mark.django_db
def test_handle_tasks_expense_state_change():
    """Test handle_tasks for expense state change action"""
    with patch('workers.actions.import_string') as mock_import_string:
        mock_func = Mock()
        mock_import_string.return_value = mock_func

        payload = {
            'action': WorkerActionEnum.EXPENSE_STATE_CHANGE.value,
            'data': {
                'workspace_id': 1,
                'report_id': 'rptest123',
                'is_state_change_event': True,
                'report_state': 'APPROVED'
            }
        }
        handle_tasks(payload)

        mock_import_string.assert_called_once_with('apps.fyle.tasks.import_expenses')
        mock_func.assert_called_once_with(
            workspace_id=1,
            report_id='rptest123',
            is_state_change_event=True,
            report_state='APPROVED'
        )


@pytest.mark.django_db
def test_process_message_success(export_worker):
    """Test successful message processing"""
    with patch('workers.worker.handle_tasks') as mock_handle_tasks:
        mock_handle_tasks.return_value = None

        routing_key = 'test.routing.key'
        payload_dict = {
            'workspace_id': 123,
            'action': 'test_action',
            'data': {'some': 'data'}
        }
        event = BaseEvent()
        event.from_dict({'new': payload_dict})

        export_worker.process_message(routing_key, event, 1)

        mock_handle_tasks.assert_called_once_with(payload_dict)
        export_worker.qconnector.acknowledge_message.assert_called_once_with(1)


@pytest.mark.django_db
def test_process_message_exception(export_worker):
    """Test message processing with exception"""
    with patch('workers.worker.handle_tasks') as mock_handle_tasks:
        mock_handle_tasks.side_effect = Exception('Test error')

        routing_key = 'test.routing.key'
        payload_dict = {
            'workspace_id': 123,
            'action': 'test_action',
            'data': {'some': 'data'}
        }
        event = BaseEvent()
        event.from_dict({'new': payload_dict})

        export_worker.process_message(routing_key, event, 1)

        mock_handle_tasks.assert_called_once_with(payload_dict)


@pytest.mark.django_db
def test_handle_exception(export_worker):
    """Test exception handling and FailedEvent creation"""
    routing_key = 'test.routing.key'
    payload_dict = {
        'data': {'some': 'data'},
        'workspace_id': 123
    }
    try:
        raise Exception('Test error')
    except Exception as error:
        export_worker.handle_exception(routing_key, payload_dict, error, 1)

    failed_event = FailedEvent.objects.get(
        routing_key=routing_key,
        workspace_id=123
    )
    assert failed_event.payload == payload_dict
    assert 'Test error' in failed_event.error_traceback
    assert 'Exception: Test error' in failed_event.error_traceback


@pytest.mark.django_db
def test_handle_exception_with_retry(export_worker):
    """Test exception handling with retry logic"""
    routing_key = 'test.routing.key'
    payload_dict = {
        'data': {'some': 'data'},
        'workspace_id': 123,
        'retry_count': 0
    }

    with patch.object(export_worker.qconnector, 'publish') as mock_publish:
        with patch.object(export_worker.qconnector, 'reject_message') as mock_reject:
            try:
                raise Exception('Test error')
            except Exception as error:
                export_worker.handle_exception(routing_key, payload_dict, error, 1)

            # Should publish retry message
            assert mock_publish.called
            mock_reject.assert_called_once_with(1, requeue=False)

            # Check retry count incremented
            failed_event = FailedEvent.objects.get(routing_key=routing_key, workspace_id=123)
            assert failed_event.payload['retry_count'] == 1


def test_shutdown(export_worker):
    """Test worker shutdown"""
    with patch.object(export_worker, 'shutdown', wraps=export_worker.shutdown) as mock_shutdown:
        export_worker.shutdown(_=15, __=None)  # SIGTERM = 15
        mock_shutdown.assert_called_once_with(_=15, __=None)


@patch('workers.worker.signal.signal')
@patch('workers.worker.Worker')
@patch('workers.worker.create_cache_table')
def test_consume(mock_create_cache_table, mock_worker_class, mock_signal):
    """Test consume function"""
    mock_worker = Mock()
    mock_worker_class.return_value = mock_worker

    with patch.dict('os.environ', {'RABBITMQ_URL': 'test_url'}):
        from workers.worker import consume
        consume(queue_name='sage_desktop_export.p0')

    mock_create_cache_table.assert_called_once()
    mock_worker.connect.assert_called_once()
    mock_worker.start_consuming.assert_called_once()
    assert mock_signal.call_count == 2


@patch('workers.worker.consume')
@patch('workers.worker.argparse.ArgumentParser.parse_args')
def test_main(mock_parse_args, mock_consume):
    """Test main entry point"""
    mock_args = Mock()
    mock_args.queue_name = 'sage_desktop_export.p0'
    mock_parse_args.return_value = mock_args

    main()

    mock_consume.assert_called_once_with(queue_name='sage_desktop_export.p0')


def test_get_routing_key_valid():
    """Test get_routing_key with valid queue names"""
    assert get_routing_key('sage_desktop_import') == RoutingKeyEnum.IMPORT
    assert get_routing_key('sage_desktop_utility') == RoutingKeyEnum.UTILITY
    assert get_routing_key('sage_desktop_export.p0') == RoutingKeyEnum.EXPORT_P0
    assert get_routing_key('sage_desktop_export.p1') == RoutingKeyEnum.EXPORT_P1


def test_get_routing_key_invalid_queue():
    """Test get_routing_key with invalid queue name"""
    with pytest.raises(ValueError) as exc_info:
        get_routing_key('invalid_queue_name')
    assert 'Unknown queue name: invalid_queue_name' in str(exc_info.value)


@pytest.mark.django_db
def test_publish_to_rabbitmq(mocker):
    """Test publish_to_rabbitmq helper function"""
    mock_rabbitmq = Mock()
    mock_get_instance = mocker.patch(
        'workers.helpers.RabbitMQConnection.get_instance',
        return_value=mock_rabbitmq
    )

    payload = {
        'workspace_id': 1,
        'action': WorkerActionEnum.DASHBOARD_SYNC.value,
        'data': {'workspace_id': 1}
    }

    publish_to_rabbitmq(payload, RoutingKeyEnum.EXPORT_P0.value)

    mock_get_instance.assert_called_once()
    mock_rabbitmq.publish.assert_called_once()
