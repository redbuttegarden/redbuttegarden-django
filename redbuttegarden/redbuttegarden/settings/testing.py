from .base import *
import os

# Overridden so we don't use cas
INSTALLED_APPS = [
    'axe',
    'concerts',
    'custom_user',
    'events',
    'home',
    'journal',
    'search',
    'shop',

    'wagtail.contrib.forms',
    "wagtail.contrib.frontend_cache",
    'wagtail.contrib.postgres_search',
    'wagtail.contrib.redirects',
    'wagtail.contrib.routable_page',
    'wagtail.contrib.settings',
    "wagtail.contrib.table_block",
    'wagtail.embeds',
    'wagtail.sites',
    'wagtail.users',
    'wagtail.snippets',
    'wagtail.documents',
    'wagtail.images',
    'wagtail.search',
    'wagtail.admin',
    'wagtail.core',

    #'cas',  # Disabled for testing
    'corsheaders',
    'modelcluster',
    'storages',
    'taggit',
    'wagtailaccessibility',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

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
        'NAME': 'github_actions',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': '127.0.0.1',
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
