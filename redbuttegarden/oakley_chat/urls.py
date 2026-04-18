from django.urls import path

from .data_views import garden_events_data, plants_data
from .views import chat_page, chat_proxy, healthcheck, send_chat


app_name = "oakley_chat"

urlpatterns = [
    path("", chat_page, name="chat_page"),
    path("data/events/", garden_events_data, name="garden_events_data"),
    path("data/plants/", plants_data, name="plants_data"),
    path("health/", healthcheck, name="healthcheck"),
    path("proxy/", chat_proxy, name="chat_proxy"),
    path("send/", send_chat, name="send_chat"),
]
