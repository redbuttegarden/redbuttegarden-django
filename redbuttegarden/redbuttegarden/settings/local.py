from .dev import *

DEBUG = True

INSTALLED_APPS.insert(0, 'debug_toolbar')

MIDDLEWARE.insert(8, 'debug_toolbar.middleware.DebugToolbarMiddleware')

ALLOWED_HOSTS += ['train.localhost', 'localhost', 'testserver', '127.0.0.1', 'rbg-it-web-dev.redbutte.utah.edu']

BASE_URL = 'http://rbg-it-web-dev.redbutte.utah.edu:8000'

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

# Webpack Loader - https://github.com/django-webpack/django-webpack-loader
WEBPACK_LOADER = {
    'DEFAULT': {
        'BUNDLE_DIR_NAME': 'build/',
        'CACHE': not DEBUG,
        'STATS_FILE': os.path.join(BASE_DIR, '..', 'frontend', 'webpack-stats.json'),
        'POLL_INTERVAL': 0.1,
        'IGNORE': [r'.+\.hot-update.js', r'.+\.map'],
    }
}
