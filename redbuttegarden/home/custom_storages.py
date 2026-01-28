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

    def get_object_parameters(self, name):
        params = super().get_object_parameters(name) or {}

        key = name.lower()

        # The manifest filename produced by ManifestStaticFilesStorage
        if key.endswith('staticfiles.json') or key.endswith('/staticfiles.json'):
            params.update({
                'CacheControl': 'no-cache, must-revalidate, max-age=0',
            })
        elif '.'.join(key.split('.')[-2:]).isalnum():  # example pattern
            params.setdefault('CacheControl', 'max-age=31536000, public, immutable')

        return params
