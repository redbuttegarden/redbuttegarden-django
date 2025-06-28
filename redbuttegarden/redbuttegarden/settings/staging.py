"""
For staging in AWS environment
"""
from .production import *

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ['staging.redbuttegarden.org',
                 os.environ.get('LAMBDA_ENDPOINT_URL')]

BASE_URL = 'https://staging.redbuttegarden.org'

# Static files
AWS_STORAGE_BUCKET_NAME = 'rbg-static-staging'
STATIC_BUCKET = AWS_STORAGE_BUCKET_NAME
MEDIA_BUCKET = AWS_STORAGE_BUCKET_NAME
AWS_S3_CUSTOM_DOMAIN = 'staging.redbuttegarden.org'
STATIC_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, 'static')
MEDIA_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, 'media')

WAGTAILFRONTENDCACHE = {
    'mainsite': {
        'BACKEND': 'home.custom_cache_backend.CustomCloudfrontBackend',
        'DISTRIBUTION_ID': os.environ.get('CLOUDFRONT_DISTRIBUTION_ID', ''),
        'HOSTNAMES': ['staging.redbuttegarden.org']
    },
}

# Keep our policy as strict as possible
CSP_DEFAULT_SRC = ("'self'",
                   "'unsafe-inline'",
                   'rbg-code-staging.s3.amazonaws.com',
                   'rbg-static-staging.s3.amazonaws.com',
                   'staging.redbuttegarden.org',)
CSP_STYLE_SRC = ("'self'",
                 "'unsafe-inline'",
                 'fonts.googleapis.com',
                 'maxcdn.bootstrapcdn.com',
                 'rbg-code-staging.s3.amazonaws.com',
                 'rbg-static-staging.s3.amazonaws.com',
                 'staging.redbuttegarden.org',)
CSP_SCRIPT_SRC = ("'self'",
                  "'unsafe-inline'",
                  'www.googletagmanager.com',
                  'www.google-analytics.com',
                  'maxcdn.bootstrapcdn.com',
                  'ajax.googleapis.com',
                  'connect.facebook.net',
                  'rbg-code-staging.s3.amazonaws.com',
                  'rbg-static-staging.s3.amazonaws.com',
                  'staging.redbuttegarden.org',)
CSP_FONT_SRC = ("'self'",
                'fonts.gstatic.com',
                'maxcdn.bootstrapcdn.com',
                'rbg-code-staging.s3.amazonaws.com',
                'rbg-static-staging.s3.amazonaws.com',
                'staging.redbuttegarden.org',)
CSP_IMG_SRC = ("'self'",
               'www.gravatar.com',
               'rbg-code-staging.s3.amazonaws.com',
               'rbg-static-staging.s3.amazonaws.com',
               'staging.redbuttegarden.org',)

CORS_ALLOWED_ORIGINS = [
    'https://staging.redbuttegarden.org',
]
