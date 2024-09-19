from django.urls import path, include, re_path
from . import consumers
# the empty string routes to ChatConsumer, which manages the chat functionality.
websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<room_name>\w+)/$', consumers.ChatConsumer.as_asgi()),
]