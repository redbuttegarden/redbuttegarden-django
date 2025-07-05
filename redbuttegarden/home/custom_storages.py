from django.conf import settings
from django.contrib.staticfiles.storage import ManifestFilesMixin
from storages.backends.s3boto3 import S3Boto3Storage


class MediaStorage(S3Boto3Storage):
    """
    Storage for media files (user uploads), no manifest or cache-busting.
    """
    bucket_name = settings.STATIC_BUCKET
    location = 'media'
    file_overwrite = False


class StaticStorage(ManifestFilesMixin, S3Boto3Storage):
    """
    Combines ManifestStaticFilesStorage (for cache-busting) with S3Boto3Storage.
    """
    bucket_name = settings.STATIC_BUCKET
    location = 'static'
    file_overwrite = True
