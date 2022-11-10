"""
For production in AWS environment
"""

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

SECRET_KEY = os.environ.get('SECRET_KEY')

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ['0.0.0.0',
                 'aflamznow5.execute-api.us-west-2.amazonaws.com',  # Newer AWS Account
                 'd7zmakezevavl.cloudfront.net',
                 'redbuttegarden.org', 'www.redbuttegarden.org', 'train.redbuttegarden.org']
# TODO - Allow dev-shop here when we want to continue working on that

BASE_URL = 'https://redbuttegarden.org'

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

# Static files
AWS_STORAGE_BUCKET_NAME = 'zappa-web-static'
AWS_S3_REGION_NAME = 'us-west-2'
AWS_S3_FILE_OVERWRITE = True
STATIC_BUCKET = 'zappa-web-static'
STATICFILES_STORAGE = 'home.custom_storages.StaticStorage'
MEDIA_BUCKET = 'zappa-web-static'
DEFAULT_FILE_STORAGE = 'home.custom_storages.MediaStorage'
AWS_S3_CUSTOM_DOMAIN = 'd7zmakezevavl.cloudfront.net'
STATIC_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, 'static')
MEDIA_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, 'media')

AWS_ACCESS_KEY_ID = os.environ.get('STATIC_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('STATIC_SECRET_ACCESS_KEY')

WAGTAILFRONTENDCACHE = {
    'cloudfront': {
        'BACKEND': 'wagtail.contrib.frontend_cache.backends.CloudfrontBackend',
        'DISTRIBUTION_ID': {
            'redbuttegarden.org': 'ESBVN4MRCUVZJ',
            # TODO - Re-enable after adding dev-shop in ALLOWED_HOSTS
            # 'dev-shop.redbuttegarden.org': 'E1ILRLJZBMHT88',
            'train.redbuttegarden.org': 'EV5FN74YZ4XU0',
        },
    },
}

# Keep our policy as strict as possible
CSP_DEFAULT_SRC = ("'self'",
                   "'unsafe-inline'",
                   'redbuttegarden.org',
                   'd7zmakezevavl.cloudfront.net',
                   'aflamznow5.execute-api.us-west-2.amazonaws.com',
                   'zappa-web-code.s3.amazonaws.com',
                   'zappa-web-static.s3.amazonaws.com')
CSP_STYLE_SRC = ("'self'",
                 "'unsafe-inline'",
                 'redbuttegarden.org',
                 'd7zmakezevavl.cloudfront.net',
                 'fonts.googleapis.com',
                 'maxcdn.bootstrapcdn.com',
                 'aflamznow5.execute-api.us-west-2.amazonaws.com',
                 'zappa-web-code.s3.amazonaws.com',
                 'zappa-web-static.s3.amazonaws.com')
CSP_SCRIPT_SRC = ("'self'",
                  "'unsafe-inline'",
                  'redbuttegarden.org',
                  'd7zmakezevavl.cloudfront.net',
                  'www.googletagmanager.com',
                  'www.google-analytics.com',
                  'maxcdn.bootstrapcdn.com',
                  'ajax.googleapis.com',
                  'connect.facebook.net',
                  'aflamznow5.execute-api.us-west-2.amazonaws.com',
                  'zappa-web-code.s3.amazonaws.com',
                  'zappa-web-static.s3.amazonaws.com')
CSP_FONT_SRC = ("'self'",
                'redbuttegarden.org',
                'd7zmakezevavl.cloudfront.net',
                'fonts.gstatic.com',
                'maxcdn.bootstrapcdn.com',
                'aflamznow5.execute-api.us-west-2.amazonaws.com',
                'zappa-web-code.s3.amazonaws.com',
                'zappa-web-static.s3.amazonaws.com')
CSP_IMG_SRC = ("'self'",
               'redbuttegarden.org',
               'd7zmakezevavl.cloudfront.net',
               'www.gravatar.com',
               'aflamznow5.execute-api.us-west-2.amazonaws.com',
               'zappa-web-code.s3.amazonaws.com',
               'zappa-web-static.s3.amazonaws.com')

CORS_ALLOWED_ORIGINS = [
    'https://aflamznow5.execute-api.us-west-2.amazonaws.com',
    'https://zappa-web-code.s3.amazonaws.com',
    'https://zappa-web-static.s3.amazonaws.com',
    'd7zmakezevavl.cloudfront.net',
    'http://0.0.0.0:8000',
]

CORS_ORIGIN_ALLOW_ALL = False
CSRF_TRUSTED_ORIGINS = ALLOWED_HOSTS

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
            'level': 'ERROR',
        },
    },
}
