"""
Django settings for final_project project.

Generated by 'django-admin startproject' using Django 5.0.6.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

from pathlib import Path
import os
from dotenv import load_dotenv
import logging
import time
load_dotenv()
from datetime import datetime

from pythonjsonlogger import jsonlogger

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from .custom_loggings import CustomJSONFormatter

BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
""" DEBUG = True

ALLOWED_HOSTS = ['*'] """


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'search',
    'storages',
    'django_apscheduler',
    'drf_yasg',
]

APSCHEDULER_DATETIME_FORMAT = "N j, Y, f:s a"  # Default
SCHEDULER_DEFAULT = True



MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'final_project.middlewares.LoggingMiddleware',  # 추가된 미들웨어
]


ROOT_URLCONF = 'final_project.urls'

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

WSGI_APPLICATION = 'final_project.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

#DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.sqlite3',
#        'NAME': BASE_DIR / 'db.sqlite3',
#    }
#}
#
DATABASES = {
    'default': {
        'ENGINE': os.getenv('ENGINE'),
        'NAME': os.getenv('NAME'),
        'USER': os.getenv('USER'),
        'PASSWORD': os.getenv('PASSWORD'),
        'HOST': os.getenv('HOST'),
        'PORT': os.getenv('PORT'),
        #'CONN_MAX_AGE': 300,
    },
    'replica': {
        'ENGINE': os.getenv('ENGINE'),
        'NAME': os.getenv('NAME'),
        'USER': os.getenv('USER'),
        'PASSWORD': os.getenv('PASSWORD'),
        'HOST': os.getenv('READ_HOST'),
        'PORT': os.getenv('PORT'),
        #'CONN_MAX_AGE': 300,
    }
}
DATABASE_ROUTERS = ['final_project.db_routers.MasterSlaveRouter']



# Redis 주석
CACHES = {
    'default': {
        'BACKEND': os.getenv("REDIS_BACKEND"),
        'LOCATION': os.getenv("REDIS_LOCATION"),
        'OPTIONS': {
            'CLIENT_CLASS': os.getenv("CLIENT_CLASS"),
            'PASSWORD': os.getenv("REDIS_PASSWORD"),  
        }
    }
}






AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

 
AWS_REGION = os.getenv('AWS_REGION')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')


AWS_S3_CUSTOM_DOMAIN = '%s.s3.%s.amazonaws.com' % (AWS_STORAGE_BUCKET_NAME,AWS_REGION)
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
MEDIA_ROOT = os.path.join(BASE_DIR, 'path/to/store/my/files/')
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760


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


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Seoul'

USE_I18N = True

USE_TZ = False #True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# otel_logging.py에서 OpenTelemetryHandler 가져오기
from .otel_logging import OpenTelemetryHandler

# OpenTelemetry 리소스 설정
SERVICE_NAME = "dapanda"
OTLP_ENDPOINT = os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT', 'http://localhost:4317')

# Tracer 설정
resource = Resource(attributes={"service.name": SERVICE_NAME})
trace_provider = TracerProvider(resource=resource)
trace_processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=OTLP_ENDPOINT))
trace_provider.add_span_processor(trace_processor)
trace.set_tracer_provider(trace_provider)

# Logger 설정
log_exporter = OTLPLogExporter(endpoint=OTLP_ENDPOINT)
log_processor = BatchLogRecordProcessor(log_exporter)
log_provider = LoggerProvider(resource=resource)
log_provider.add_log_record_processor(log_processor)

# 로깅 핸들러 설정
otel_logging_handler = LoggingHandler(logger_provider=log_provider)





# 로그 메세지에 날짜를 포함시키기 위해서 사전에 선언
now = datetime.now()
str_now = now.strftime('%y-%m-%d')

# settings.py

# settings.py






# logging 설정
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': CustomJSONFormatter,
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
        'file': {
            'class': 'logging.FileHandler',
            'formatter': 'json',
            'filename': f'django_{datetime.now().strftime("%Y-%m-%d")}.log',
            'encoding': 'utf-8',  # UTF-8 인코딩 지정
        },
        'otel': {
            '()': lambda: OpenTelemetryHandler(otel_logging_handler),  # OpenTelemetry 로그 핸들러 사용
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file', 'otel'],
            'level': 'INFO',
        },
        'django.server': {
            'handlers': ['console', 'file', 'otel'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}







# 기타 Django 설정
DEBUG = False #True
ALLOWED_HOSTS = ['*']

