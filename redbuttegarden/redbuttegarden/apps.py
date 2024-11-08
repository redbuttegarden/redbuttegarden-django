from wagtail.users.apps import WagtailUsersAppConfig


class CustomUsersAppConfig(WagtailUsersAppConfig):
    user_viewset = "custom_user.viewsets.UserViewSet"
