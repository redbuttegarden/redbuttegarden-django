from storages.backends.s3boto3 import S3Boto3Storage


class SecurityTokenWorkaroundS3Boto3Storage(S3Boto3Storage):
    def _get_security_token(self):
        return None


class MediaStorage(SecurityTokenWorkaroundS3Boto3Storage):
    location = 'media'


class StaticStorage(SecurityTokenWorkaroundS3Boto3Storage):
    location = 'static'