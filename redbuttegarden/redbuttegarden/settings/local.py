"""
For local testing
"""

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

environ.Env.read_env('.env.local')

SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ['127.0.0.1', '0.0.0.0']

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('PG_DB'),
        'USER': env('PG_USER'),
        'PASSWORD': '"rjncjxGE9KCxu9ULoe7rnL8nBAttmkT5bLrzWjienNKS6caDTjZGLYfkPfQF"',
        'HOST': env('DB_HOST'),
        'PORT': 5432,
    }
}
