from .dev import *

DEBUG = True

INSTALLED_APPS.insert(0, 'debug_toolbar')

MIDDLEWARE.insert(8, 'debug_toolbar.middleware.DebugToolbarMiddleware')

ALLOWED_HOSTS += ['train.localhost', 'localhost', 'testserver', '127.0.0.1', 'rbg-it-web-dev.redbutte.utah.edu']

BASE_URL = 'http://rbg-it-web-dev.redbutte.utah.edu:8000'

# Use AWS S3 test bucket for storage when running locally
# Static files and storage settings
AWS_S3_CUSTOM_DOMAIN = 'rbg-it-web-dev.redbutte.utah.edu'
STATIC_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, 'static')
MEDIA_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, 'media')
STORAGES = {
    'default': {
        'BACKEND': 'home.custom_storages.MediaStorage',
        'OPTIONS': {
            'region_name': 'us-east-1',
            'bucket_name': 'rbg-web-static-testing',
            'access_key': os.environ.get('STATIC_ACCESS_KEY_ID'),
            'secret_key': os.environ.get('STATIC_SECRET_ACCESS_KEY'),
        },
    },
    'staticfiles': {
        'BACKEND': 'home.custom_storages.StaticStorage',
        'OPTIONS': {
            'region_name': 'us-east-1',
            'bucket_name': 'rbg-web-static-testing',
            'access_key': os.environ.get('STATIC_ACCESS_KEY_ID'),
            'secret_key': os.environ.get('STATIC_SECRET_ACCESS_KEY'),
        },
    },
}

# Disable cloudfront invalidations when running locally
WAGTAILFRONTENDCACHE = {}

# Django Toolbar settings
# We just always show the toolbar to make it easier for our docker environment
def show_toolbar(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return False
    return True

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': 'redbuttegarden.settings.local.show_toolbar',
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
