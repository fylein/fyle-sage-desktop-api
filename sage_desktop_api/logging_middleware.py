import logging
import random
import string
import os


logger = logging.getLogger(__name__)
logger.level = logging.WARNING


def generate_worker_id():
    return 'worker_' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))


def set_worker_id_in_env():
    worker_id = generate_worker_id()
    os.environ['WORKER_ID'] = worker_id


def get_logger():
    if 'WORKER_ID' not in os.environ:
        set_worker_id_in_env()
    worker_id = os.environ['WORKER_ID']
    extra = {'worker_id': worker_id}
    updated_logger = logging.LoggerAdapter(logger, extra)
    updated_logger.setLevel(logging.INFO)

    return updated_logger


class WorkerIDFilter(logging.Filter):
    def filter(self, record):
        worker_id = getattr(record, 'worker_id', '')
        record.worker_id = worker_id
        return True
