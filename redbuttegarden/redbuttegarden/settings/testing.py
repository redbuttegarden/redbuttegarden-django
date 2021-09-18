from .base import *
import os

# Overridden so we don't use cas
INSTALLED_APPS.remove('cas')
INSTALLED_APPS.insert(0, 'wagtail.contrib.search_promotions')  # https://github.com/wagtail/wagtail/issues/1824

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Not using postgres for testing so we disable postgres_search backend
WAGTAILSEARCH_BACKENDS = {
    'default': {
        'BACKEND': 'wagtail.search.backends.db',
    },
}

# Base URL to use when referring to full URLs within the Wagtail admin backend -
# e.g. in notification emails. Don't include '/admin' or a trailing slash
BASE_URL = 'http://localhost'

# Disable CAS related settings for testing
MIDDLEWARE_CLASSES = ()
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)

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

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache'
    }
}

SECRET_KEY = 'Testing'
ALLOWED_HOSTS = ['localhost', '0.0.0.0']
