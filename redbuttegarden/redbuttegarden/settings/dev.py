"""
For testing in AWS environment
"""

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

SECRET_KEY = os.environ.get('SECRET_KEY')

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ['0.0.0.0', 'pzr1yumqbe.execute-api.us-east-1.amazonaws.com', 'dev.redbuttegarden.org']

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
MY_S3_BUCKET = "zappa-rbg-dev-static-east"

STATICFILES_STORAGE = "django_s3_storage.storage.StaticS3Storage"  # Based on Zappa docs
AWS_S3_BUCKET_NAME_STATIC = MY_S3_BUCKET  # Based on Zappa docs
AWS_S3_BUCKET_NAME = MY_S3_BUCKET  # Based on django_s3_storage docs
DEFAULT_FILE_STORAGE = "django_s3_storage.storage.S3Storage"  # Based on django_s3_storage docs

# These next two lines will serve the static files directly
# from the s3 bucket
AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % MY_S3_BUCKET
STATIC_URL = "https://%s/" % AWS_S3_CUSTOM_DOMAIN

AWS_S3_BUCKET_AUTH = False
AWS_S3_MAX_AGE_SECONDS = 60 * 60 * 24 * 365  # 1 year.
# The AWS region to connect to.
AWS_REGION = "us-east-1"

# The AWS access key to use.
AWS_ACCESS_KEY_ID = os.environ.get("STATIC_ACCESS_KEY_ID")

# The AWS secret access key to use.
AWS_SECRET_ACCESS_KEY = os.environ.get("STATIC_SECRET_ACCESS_KEY")