"""
Django settings for sage_desktop_api project.

Generated by 'django-admin startproject' using Django 3.1.14.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""
import os
import sys
from logging.config import dictConfig

import dj_database_url

from sage_desktop_api.logging_middleware import WorkerIDFilter
from sage_desktop_api.sentry import Sentry

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True if os.environ.get('DEBUG') == 'True' else False

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS').split(',')

ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Installed Apps
    'rest_framework',
    'corsheaders',
    'django_q',
    'fyle_rest_auth',
    'django_filters',
    'fyle_accounting_mappings',
    'fyle_accounting_library.fyle_platform',
    'fyle_accounting_library.rabbitmq',
    'fyle_integrations_imports',

    # User Created Apps
    'apps.users',
    'apps.workspaces',
    'apps.fyle',
    'apps.sage300',
    'apps.accounting_exports',
    'apps.mappings',
    'apps.internal'
]

MIDDLEWARE = [
    'request_logging.middleware.LoggingMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'sage_desktop_api.urls'
APPEND_SLASH = False

AUTH_USER_MODEL = 'users.User'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


FYLE_REST_AUTH_SERIALIZERS = {
    'USER_DETAILS_SERIALIZER': 'apps.users.serializers.UserSerializer'
}

FYLE_REST_AUTH_SETTINGS = {
    'async_update_user': True
}

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
        'apps.workspaces.permissions.WorkspacePermissions'
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'fyle_rest_auth.authentication.FyleJWTAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 100,
    'DEFAULT_THROTTLE_CLASSES': [
        'sage_desktop_api.throttles.PerUserPathThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'per_user_path': '30/second'
    }
}

SERVICE_NAME = os.environ.get('SERVICE_NAME')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '{levelname} %s {asctime} {name} {worker_id} {message}' % SERVICE_NAME, 'style': '{'
        },
        'verbose': {
            'format': '{levelname} %s {asctime} {module} {message} ' % SERVICE_NAME, 'style': '{'
        },
        'requests': {
            'format': 'request {levelname} %s {asctime} {message}' % SERVICE_NAME, 'style': '{'
        }
    },
    'filters': {
        'worker_id': {
            '()': WorkerIDFilter,
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'filters': ['worker_id'],
        },
        'request_logs': {
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'formatter': 'requests'
        },
        'debug_logs': {
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'formatter': 'verbose'
        }
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'django.request': {'handlers': ['request_logs'], 'propagate': False}
    },
}

dictConfig(LOGGING)

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'auth_cache',
    }
}

Q_CLUSTER = {
    'name': 'sage_desktop_api',
    'save_limit': 0,
    'retry': 2592000,
    'timeout': 86400,
    'catch_up': False,
    'workers': 4,
    # How many tasks are kept in memory by a single cluster.
    # Helps balance the workload and the memory overhead of each individual cluster
    'queue_limit': 10,
    'cached': False,
    'orm': 'default',
    'ack_failures': True,
    'poll': 5,
    'max_attempts': 1,
    'attempt_count': 1,
    # The number of tasks a worker will process before recycling.
    # Useful to release memory resources on a regular basis.
    'recycle': 50,
    # The maximum resident set size in kilobytes before a worker will recycle and release resources.
    # Useful for limiting memory usage.
    'max_rss': 100000  # 100mb
}


WSGI_APPLICATION = 'sage_desktop_api.wsgi.application'

SERVICE_NAME = os.environ.get('SERVICE_NAME')


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases
DATABASES = {
    'default': dj_database_url.config()
}

DATABASES['default']['DISABLE_SERVER_SIDE_CURSORS'] = True

DATABASES['cache_db'] = {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': 'cache.db'
}

DATABASE_ROUTERS = ['sage_desktop_api.cache_router.CacheRouter']

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Fyle Settings
API_URL = os.environ.get('API_URL')
FYLE_TOKEN_URI = os.environ.get('FYLE_TOKEN_URI')
FYLE_CLIENT_ID = os.environ.get('FYLE_CLIENT_ID')
FYLE_CLIENT_SECRET = os.environ.get('FYLE_CLIENT_SECRET')
FYLE_BASE_URL = os.environ.get('FYLE_BASE_URL')
FYLE_JOBS_URL = os.environ.get('FYLE_JOBS_URL')
FYLE_APP_URL = os.environ.get('APP_URL')
FYLE_EXPENSE_URL = os.environ.get('FYLE_APP_URL')
INTEGRATIONS_SETTINGS_API = os.environ.get('INTEGRATIONS_SETTINGS_API')

# Sage300 Settings
SD_API_KEY = os.environ.get('SD_API_KEY')
SD_API_SECRET = os.environ.get('SD_API_SECRET')

# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = '/static/'

CORS_ORIGIN_ALLOW_ALL = True

# Sentry
Sentry.init()

CORS_ALLOW_HEADERS = ['sentry-trace', 'authorization', 'content-type']
