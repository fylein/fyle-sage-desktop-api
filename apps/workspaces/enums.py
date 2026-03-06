from enum import Enum


class LocalCacheKeyEnum(Enum):
    FEATURE_CONFIG_IS_JOB_STATUS_SYNC_ENABLED = 'feature_config:is_job_status_sync_enabled:{workspace_id}'
