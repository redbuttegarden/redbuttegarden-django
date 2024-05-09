"""
For testing in AWS environment
"""

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

SECRET_KEY = os.environ.get('SECRET_KEY')

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ['0.0.0.0', 'rbg-web-dev.redbutte.utah.edu', 'dev-shop.redbutte.utah.edu',
                 'chow-whole-hugely.ngrok-free.app']

BASE_URL = 'https://dev.redbuttegarden.org'
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

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
AWS_STORAGE_BUCKET_NAME = 'zappa-rbg-dev-static-east'
AWS_S3_REGION_NAME = 'us-east-1'
AWS_S3_FILE_OVERWRITE = False
STATIC_BUCKET = 'zappa-rbg-dev-static-east'
STATICFILES_STORAGE = 'home.custom_storages.StaticStorage'
MEDIA_BUCKET = 'zappa-rbg-dev-static-east'
DEFAULT_FILE_STORAGE = 'home.custom_storages.MediaStorage'
AWS_S3_CUSTOM_DOMAIN = 'dhsyi82ptcyu5.cloudfront.net'
STATIC_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, 'static')
MEDIA_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, 'media')

WAGTAILFRONTENDCACHE = {
    'cloudfront': {
        'BACKEND': 'wagtail.contrib.frontend_cache.backends.CloudfrontBackend',
        'DISTRIBUTION_ID': {
            'dev.redbuttegarden.org': 'E5BZL9629SKXT',
            'dev-shop.redbuttegarden.org': 'E1ILRLJZBMHT88',
            'dev-train.redbuttegarden.org': 'EV5FN74YZ4XU0',
        },
    },
}

# Keep our policy as strict as possible
CSP_DEFAULT_SRC = ("'self'",
                   "'unsafe-inline'",
                   'dev.redbuttegarden.org',
                   'dhsyi82ptcyu5.cloudfront.net',
                   'pzr1yumqbe.execute-api.us-east-1.amazonaws.com',
                   'zappa-rbg-dev.s3.amazonaws.com',
                   'zappa-rbg-dev-static-east.s3.amazonaws.com')
CSP_STYLE_SRC = ("'self'",
                 "'unsafe-inline'",
                 'dev.redbuttegarden.org',
                 'dhsyi82ptcyu5.cloudfront.net',
                 'fonts.googleapis.com',
                 'maxcdn.bootstrapcdn.com',
                 'pzr1yumqbe.execute-api.us-east-1.amazonaws.com',
                 'zappa-rbg-dev.s3.amazonaws.com',
                 'zappa-rbg-dev-static-east.s3.amazonaws.com')
CSP_SCRIPT_SRC = ("'self'",
                  "'unsafe-inline'",
                  'dev.redbuttegarden.org',
                  'dhsyi82ptcyu5.cloudfront.net',
                  'www.googletagmanager.com',
                  'www.google-analytics.com',
                  'maxcdn.bootstrapcdn.com',
                  'ajax.googleapis.com',
                  'connect.facebook.net',
                  'pzr1yumqbe.execute-api.us-east-1.amazonaws.com',
                  'zappa-rbg-dev.s3.amazonaws.com',
                  'zappa-rbg-dev-static-east.s3.amazonaws.com')
CSP_FONT_SRC = ("'self'",
                'dev.redbuttegarden.org',
                'dhsyi82ptcyu5.cloudfront.net',
                'fonts.gstatic.com',
                'maxcdn.bootstrapcdn.com',
                'pzr1yumqbe.execute-api.us-east-1.amazonaws.com',
                'zappa-rbg-dev.s3.amazonaws.com',
                'zappa-rbg-dev-static-east.s3.amazonaws.com')
CSP_IMG_SRC = ("'self'",
               'dev.redbuttegarden.org',
               'dhsyi82ptcyu5.cloudfront.net',
               'www.gravatar.com',
               'pzr1yumqbe.execute-api.us-east-1.amazonaws.com',
               'zappa-rbg-dev.s3.amazonaws.com',
               'zappa-rbg-dev-static-east.s3.amazonaws.com')

# CORS_ALLOWED_ORIGINS = [
#     "https://pzr1yumqbe.execute-api.us-east-1.amazonaws.com",
#     "https://zappa-rbg-dev-static-east.s3.amazonaws.com",
#     "http://0.0.0.0:8000",
# ]

CORS_ORIGIN_ALLOW_ALL = True
CSRF_TRUSTED_ORIGINS = ['http://' + domain for domain in ALLOWED_HOSTS] + ['https://' + domain for domain in
                                                                           ALLOWED_HOSTS]

# Only the dev version uses a proxy so this setting isn't required for prod
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

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
