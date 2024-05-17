"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""
from chats.consumers import ConnectionConsumer, ChatConsumer
from channels.routing import ProtocolTypeRouter, URLRouter
from middlewares.websocket_auth import TokenAuthMiddleware
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from django.urls import path, re_path
from dotenv import load_dotenv
import os

load_dotenv()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', os.getenv('DJANGO_SETTINGS_MODULE'))

# urls for the websocket
application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter([
            re_path(r'^ws/(?P<username>[a-zA-Z0-9]*)/?$', TokenAuthMiddleware(ConnectionConsumer.as_asgi()), name='user'),
            path('ws/chat/<str:room_name>', TokenAuthMiddleware(ChatConsumer.as_asgi()), name='chat'),
        ])
    )
})
