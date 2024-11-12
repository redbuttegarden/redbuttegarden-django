from wagtail.contrib.frontend_cache.backends import CloudfrontBackend


class CustomCloudfrontBackend(CloudfrontBackend):
    def _create_invalidation(self, distribution_id, paths):
        paths = tuple(paths)
        super()._create_invalidation(distribution_id, paths)
