from .dev import *

# Use local static file storage when running locally
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'
STATIC_URL = '/static/'
MEDIA_URL = '/media/'

# Disable cloudfront invalidations when running locally
WAGTAILFRONTENDCACHE = {}
