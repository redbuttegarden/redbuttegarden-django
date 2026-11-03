from .local import *

INSTALLED_APPS.remove('debug_toolbar')

MIDDLEWARE.remove('debug_toolbar.middleware.DebugToolbarMiddleware')

# Base URL to use when referring to full URLs within the Wagtail admin backend -
# e.g. in notification emails. Don't include '/admin' or a trailing slash
BASE_URL = 'http://localhost'

# Disable CAS related settings for testing
MIDDLEWARE_CLASSES = ()
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache'
    }
}

SECRET_KEY = 'Testing'
ALLOWED_HOSTS = ['localhost', '0.0.0.0']

# Tests render templates directly without running collectstatic. Avoid coupling
# them to a stale, ignored manifest while retaining manifest storage in every
# deployed environment.
STORAGES = {
    **STORAGES,
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
    },
}
