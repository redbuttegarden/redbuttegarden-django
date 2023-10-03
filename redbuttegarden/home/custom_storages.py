from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class SecurityTokenWorkaroundS3Boto3Storage(S3Boto3Storage):
    def _get_security_token(self):
        return None


class MediaStorage(SecurityTokenWorkaroundS3Boto3Storage):
    bucket_name = settings.STATIC_BUCKET
    location = 'media'


class StaticStorage(SecurityTokenWorkaroundS3Boto3Storage):
    bucket_name = settings.MEDIA_BUCKET
    location = 'static'