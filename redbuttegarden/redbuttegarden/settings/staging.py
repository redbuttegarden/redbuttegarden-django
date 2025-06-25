"""
For staging in AWS environment
"""
import os

from .production import *

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ['staging.redbuttegarden.org']

BASE_URL = 'https://staging.redbuttegarden.org'

# Static files
AWS_STORAGE_BUCKET_NAME = 'rbg-static-staging'

AWS_ACCESS_KEY_ID = os.environ.get('STATIC_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('STATIC_SECRET_ACCESS_KEY')

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
                   'redbuttegarden.org',
                   'www.redbuttegarden.org',
                   'train.redbuttegarden.org',
                   'd1mg1drmxhfql.cloudfront.net',
                   'aflamznow5.execute-api.us-west-2.amazonaws.com',
                   'rbg-web-code.s3.amazonaws.com',
                   'rbg-web-static.s3.amazonaws.com',
                   'staging.redbuttegarden.org',)
CSP_STYLE_SRC = ("'self'",
                 "'unsafe-inline'",
                 'redbuttegarden.org',
                 'www.redbuttegarden.org',
                 'train.redbuttegarden.org',
                 'd1mg1drmxhfql.cloudfront.net',
                 'fonts.googleapis.com',
                 'maxcdn.bootstrapcdn.com',
                 'davlmcslie.execute-api.us-east-1.amazonaws.com',
                 'rbg-web-code.s3.amazonaws.com',
                 'rbg-web-static.s3.amazonaws.com',
                 'staging.redbuttegarden.org',)
CSP_SCRIPT_SRC = ("'self'",
                  "'unsafe-inline'",
                  'redbuttegarden.org',
                  'www.redbuttegarden.org',
                  'train.redbuttegarden.org',
                  'd1mg1drmxhfql.cloudfront.net',
                  'www.googletagmanager.com',
                  'www.google-analytics.com',
                  'maxcdn.bootstrapcdn.com',
                  'ajax.googleapis.com',
                  'connect.facebook.net',
                  'davlmcslie.execute-api.us-east-1.amazonaws.com',
                  'rbg-web-code.s3.amazonaws.com',
                  'rbg-web-static.s3.amazonaws.com',
                  'staging.redbuttegarden.org',)
CSP_FONT_SRC = ("'self'",
                'redbuttegarden.org',
                'www.redbuttegarden.org',
                'train.redbuttegarden.org',
                'd1mg1drmxhfql.cloudfront.net',
                'fonts.gstatic.com',
                'maxcdn.bootstrapcdn.com',
                'davlmcslie.execute-api.us-east-1.amazonaws.com',
                'rbg-web-code.s3.amazonaws.com',
                'rbg-web-static.s3.amazonaws.com',
                'staging.redbuttegarden.org',)
CSP_IMG_SRC = ("'self'",
               'redbuttegarden.org',
               'www.redbuttegarden.org',
               'train.redbuttegarden.org',
               'd1mg1drmxhfql.cloudfront.net',
               'www.gravatar.com',
               'davlmcslie.execute-api.us-east-1.amazonaws.com',
               'rbg-web-code.s3.amazonaws.com',
               'rbg-web-static.s3.amazonaws.com'
               'staging.redbuttegarden.org',)

CORS_ALLOWED_ORIGINS = [
    'redbuttegarden.org',
    'www.redbuttegarden.org',
    'train.redbuttegarden.org',
    'davlmcslie.execute-api.us-east-1.amazonaws.com',
    'https://rbg-web-code.s3.amazonaws.com',
    'https://rbg-web-static.s3.amazonaws.com',
    'd1mg1drmxhfql.cloudfront.net',
    'http://0.0.0.0:8000',
    'staging.redbuttegarden.org',
]
