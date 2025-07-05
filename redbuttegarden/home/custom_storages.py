from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class MediaStorage(S3Boto3Storage):
    bucket_name = settings.STATIC_BUCKET
    location = 'media'
    custom_domain = 'staging.redbuttegarden.org'


class StaticStorage(S3Boto3Storage):
    bucket_name = settings.STATIC_BUCKET
    location = 'static'
    custom_domain = 'staging.redbuttegarden.org'
