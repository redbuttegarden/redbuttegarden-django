from .dev import *

DEBUG = True

# Use local static file storage when running locally
AWS_STORAGE_BUCKET_NAME = ''
AWS_S3_REGION_NAME = 'us-east-1'
STATIC_BUCKET = ''
MEDIA_BUCKET = ''
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
AWS_S3_CUSTOM_DOMAIN = ''
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'
STATIC_URL = '/static/'
MEDIA_URL = '/media/'

AWS_ACCESS_KEY_ID = 'FOO'
AWS_SECRET_ACCESS_KEY = 'BAR'

# Disable cloudfront invalidations when running locally
WAGTAILFRONTENDCACHE = {}
