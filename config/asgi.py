"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""
from chats.consumers import SearchConsumer, ConnectionConsumer, ChatConsumer
from channels.routing import ProtocolTypeRouter, URLRouter
from middlewares.websocket_auth import TokenAuthMiddleware
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from dotenv import load_dotenv
from django.urls import path
import os


load_dotenv()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', os.getenv('DJANGO_SETTINGS_MODULE'))

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter([
            path('ws/user/<str:username>', TokenAuthMiddleware(ConnectionConsumer.as_asgi()), name='username'),
            path('ws/chat/<str:room_name>', TokenAuthMiddleware(ChatConsumer.as_asgi()), name='chat'),
            path('ws/search', SearchConsumer.as_asgi(), name='search'),
        ])
    )
})

