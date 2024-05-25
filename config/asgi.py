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
    'websocket': AuthMiddlewareStack(TokenAuthMiddleware(
        URLRouter([
            re_path(r'^(?P<username>[a-zA-Z0-9]*)/?$', ConnectionConsumer.as_asgi(), name='user'),
            path('chat/<str:room_name>', ChatConsumer.as_asgi(), name='chat'),
        ])
    ))
})
