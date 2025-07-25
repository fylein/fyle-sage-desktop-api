import logging
import os
import signal

# isort: off
from workers.export.actions import handle_exports
# isort: on

from common.event import BaseEvent
from common.qconnector import RabbitMQConnector
from consumer.event_consumer import EventConsumer
from fyle_accounting_library.fyle_platform.enums import RoutingKeyEnum
from fyle_accounting_library.rabbitmq.data_class import RabbitMQData
from fyle_accounting_library.rabbitmq.helpers import create_cache_table
from fyle_accounting_library.rabbitmq.models import FailedEvent

logger = logging.getLogger('workers')


class ExportWorker(EventConsumer):
    """
    Export Worker
    """
    def __init__(self, *, qconnector_cls: RabbitMQConnector, **kwargs):
        """
        Initialize
        """
        super().__init__(qconnector_cls=qconnector_cls, **kwargs)

    def process_message(self, routing_key: str, event: BaseEvent, delivery_tag: int) -> None:
        """
        Process message
        """
        payload_dict = event.new
        try:
            logger.info('Processing task for workspace - %s with routing key - %s and payload - %s with delivery tag - %s', payload_dict['workspace_id'], routing_key, payload_dict, delivery_tag)

            handle_exports(payload_dict['data'])
            self.qconnector.acknowledge_message(delivery_tag)
            logger.info('Task processed successfully for workspace - %s with routing key - %s and delivery tag - %s', payload_dict['workspace_id'], routing_key, delivery_tag)
        except Exception as e:
            self.handle_exception(routing_key, payload_dict, e, delivery_tag)

    def handle_exception(self, routing_key: str, payload_dict: dict, error: Exception, delivery_tag: int) -> None:
        """
        Handle exception
        """
        logger.error('Error while handling exports for workspace - %s, error: %s', payload_dict, str(error))

        payload_dict['retry_count'] = payload_dict.get('retry_count', 0) + 1

        FailedEvent.objects.create(
            routing_key=routing_key,
            payload=payload_dict,
            error_traceback=str(error),
            workspace_id=payload_dict['workspace_id'] if payload_dict.get('workspace_id') else None
        )

        if payload_dict['retry_count'] < 2:
            logger.info('Publishing new message with incremented retry count')
            data = RabbitMQData(
                new=payload_dict
            )
            self.qconnector.publish(RoutingKeyEnum.EXPORT, data.to_json())

            self.qconnector.reject_message(delivery_tag, requeue=False)
        else:
            logger.info('Max retries reached, dropping message')
            self.qconnector.reject_message(delivery_tag, requeue=False)

    def shutdown(self, _: int, __: int) -> None:
        """
        Shutdown
        """
        logger.info('Received signal %s, shutting down...', _)
        super().shutdown()


def consume() -> None:
    """
    Consume
    """
    create_cache_table()

    rabbitmq_url = os.environ.get('RABBITMQ_URL')

    export_worker = ExportWorker(
        rabbitmq_url=rabbitmq_url,
        rabbitmq_exchange='sage_desktop_exchange',
        queue_name='sage_desktop_queue',
        binding_keys=RoutingKeyEnum.EXPORT,
        qconnector_cls=RabbitMQConnector,
        event_cls=BaseEvent
    )

    signal.signal(signal.SIGTERM, export_worker.shutdown)
    signal.signal(signal.SIGINT, export_worker.shutdown)

    export_worker.connect()
    export_worker.start_consuming()


if __name__ == "__main__":
    consume()
