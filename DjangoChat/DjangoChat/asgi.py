# myproject/asgi.py
import os
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
import ChitChat.routing  # routing for your app

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DjangoChat.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                ChitChat.routing.websocket_urlpatterns
            )
        )
    ),
})
