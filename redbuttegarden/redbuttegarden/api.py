from wagtail.api.v2.views import BaseAPIViewSet, PagesAPIViewSet
from wagtail.api.v2.router import WagtailAPIRouter
from wagtail.images.api.v2.views import ImagesAPIViewSet
from wagtail.documents.api.v2.views import DocumentsAPIViewSet
from rest_framework.permissions import AllowAny

# Create the router. "wagtailapi" is the URL namespace
api_router = WagtailAPIRouter('wagtailapi')

class CustomBaseAPIViewSet(BaseAPIViewSet):
    permission_classes = [AllowAny]

class CustomPagesAPIViewSet(PagesAPIViewSet, CustomBaseAPIViewSet):
    pass

class CustomImagesAPIViewSet(ImagesAPIViewSet, CustomBaseAPIViewSet):
    pass

class CustomDocumentsAPIViewSet(DocumentsAPIViewSet, CustomBaseAPIViewSet):
    pass


# Add the three endpoints using the "register_endpoint" method.
# The first parameter is the name of the endpoint (such as pages, images). This
# is used in the URL of the endpoint
# The second parameter is the endpoint class that handles the requests
api_router.register_endpoint('pages', CustomPagesAPIViewSet)
api_router.register_endpoint('images', CustomImagesAPIViewSet)
api_router.register_endpoint('documents', CustomDocumentsAPIViewSet)
