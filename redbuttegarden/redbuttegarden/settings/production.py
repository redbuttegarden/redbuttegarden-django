"""
For production in AWS environment
"""

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

SECRET_KEY = os.environ.get('SECRET_KEY')

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ['0.0.0.0',
                 'davlmcslie.execute-api.us-east-1.amazonaws.com',  # Newer AWS Account
                 'd1mg1drmxhfql.cloudfront.net',
                 'redbuttegarden.org', 'www.redbuttegarden.org', 'train.redbuttegarden.org',
                 'dev-shop.redbuttegarden.org']

BASE_URL = 'https://redbuttegarden.org'

# Needed to increase from default of 1000 for bulk deleting models from Django admin
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('PG_DB'),
        'USER': os.environ.get('PG_USER'),
        'PASSWORD': os.environ.get('PG_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': 5432,
    }
}

# Email Settings
EMAIL_BACKEND = 'django_ses.SESBackend'
AWS_SES_ACCESS_KEY_ID = os.environ.get('SES_ACCESS_KEY')
AWS_SES_SECRET_ACCESS_KEY = os.environ.get('SES_SECRET_ACCESS_KEY')
AWS_SES_REGION_NAME = 'us-east-1'
AWS_SES_REGION_ENDPOINT = 'email.us-east-1.amazonaws.com'
AWS_SES_RETURN_PATH = os.environ.get('IT_EMAIL')
WAGTAILADMIN_NOTIFICATION_FROM_EMAIL = 'admin@redbuttegarden.org'
WAGTAILADMIN_NOTIFICATION_USE_HTML = True

# Static files and storage settings
AWS_S3_CUSTOM_DOMAIN = 'redbuttegarden.org'
STATIC_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, 'static')
MEDIA_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, 'media')
STORAGES = {
    'default': {
        'BACKEND': 'storages.backends.s3boto3.S3Boto3Storage',
        'OPTIONS': {
            'bucket_name': 'rbg-web-static',
            'location': 'media',
            'region_name': 'us-east-1',
            'access_key': os.environ.get('STATIC_ACCESS_KEY_ID'),
            'secret_key': os.environ.get('STATIC_SECRET_ACCESS_KEY'),
        },
    },
    'staticfiles': {
        'BACKEND': 'storages.backends.s3boto3.S3Boto3Storage',
        'OPTIONS': {
            'bucket_name': 'rbg-web-static',
            'location': 'static',
            'region_name': 'us-east-1',
            'access_key': os.environ.get('STATIC_ACCESS_KEY_ID'),
            'secret_key': os.environ.get('STATIC_SECRET_ACCESS_KEY'),
        },
    },
}

WAGTAILFRONTENDCACHE = {
    'mainsite': {
        'BACKEND': 'home.custom_cache_backend.CustomCloudfrontBackend',
        'DISTRIBUTION_ID': 'E3VPUBUC4O7PM0',
        'HOSTNAMES': ['redbuttegarden.org']
    },
    'wwwsite': {
        'BACKEND': 'home.custom_cache_backend.CustomCloudfrontBackend',
        'DISTRIBUTION_ID': 'E3VPUBUC4O7PM0',
        'HOSTNAMES': ['www.redbuttegarden.org']
    },
    'training': {
        'BACKEND': 'home.custom_cache_backend.CustomCloudfrontBackend',
        'DISTRIBUTION_ID': 'ESBVN4MRCUVZJ',
        'HOSTNAMES': ['train.redbuttegarden.org']
    },
}

# Keep our policy as strict as possible
CSP_DEFAULT_SRC = ("'self'",
                   "'unsafe-inline'",
                   'redbuttegarden.org',
                   'www.redbuttegarden.org',
                   'train.redbuttegarden.org',
                   'd1mg1drmxhfql.cloudfront.net',
                   'aflamznow5.execute-api.us-west-2.amazonaws.com',
                   'rbg-web-code.s3.amazonaws.com',
                   'rbg-web-static.s3.amazonaws.com')
CSP_STYLE_SRC = ("'self'",
                 "'unsafe-inline'",
                 'redbuttegarden.org',
                 'www.redbuttegarden.org',
                 'train.redbuttegarden.org',
                 'd1mg1drmxhfql.cloudfront.net',
                 'fonts.googleapis.com',
                 'maxcdn.bootstrapcdn.com',
                 'davlmcslie.execute-api.us-east-1.amazonaws.com',
                 'rbg-web-code.s3.amazonaws.com',
                 'rbg-web-static.s3.amazonaws.com')
CSP_SCRIPT_SRC = ("'self'",
                  "'unsafe-inline'",
                  'redbuttegarden.org',
                  'www.redbuttegarden.org',
                  'train.redbuttegarden.org',
                  'd1mg1drmxhfql.cloudfront.net',
                  'www.googletagmanager.com',
                  'www.google-analytics.com',
                  'maxcdn.bootstrapcdn.com',
                  'ajax.googleapis.com',
                  'connect.facebook.net',
                  'davlmcslie.execute-api.us-east-1.amazonaws.com',
                  'rbg-web-code.s3.amazonaws.com',
                  'rbg-web-static.s3.amazonaws.com')
CSP_FONT_SRC = ("'self'",
                'redbuttegarden.org',
                'www.redbuttegarden.org',
                'train.redbuttegarden.org',
                'd1mg1drmxhfql.cloudfront.net',
                'fonts.gstatic.com',
                'maxcdn.bootstrapcdn.com',
                'davlmcslie.execute-api.us-east-1.amazonaws.com',
                'rbg-web-code.s3.amazonaws.com',
                'rbg-web-static.s3.amazonaws.com')
CSP_IMG_SRC = ("'self'",
               'redbuttegarden.org',
               'www.redbuttegarden.org',
               'train.redbuttegarden.org',
               'd1mg1drmxhfql.cloudfront.net',
               'www.gravatar.com',
               'davlmcslie.execute-api.us-east-1.amazonaws.com',
               'rbg-web-code.s3.amazonaws.com',
               'rbg-web-static.s3.amazonaws.com')

CORS_ALLOWED_ORIGINS = [
    'redbuttegarden.org',
    'www.redbuttegarden.org',
    'train.redbuttegarden.org',
    'davlmcslie.execute-api.us-east-1.amazonaws.com',
    'https://rbg-web-code.s3.amazonaws.com',
    'https://rbg-web-static.s3.amazonaws.com',
    'd1mg1drmxhfql.cloudfront.net',
    'http://0.0.0.0:8000',
]

CORS_ORIGIN_ALLOW_ALL = False
CSRF_TRUSTED_ORIGINS = ['https://' + domain for domain in ALLOWED_HOSTS]

DEAD_SIMPLE_CHAT_ROOM_ID = 'zjaQPcy7v'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'console': {
            'format': '%(name)-12s %(levelname)-8s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'console',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
