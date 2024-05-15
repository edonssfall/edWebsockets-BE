from middlewares.middleware_helpers import receive_user, check_response, get_or_create_user
from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from dotenv import load_dotenv
import requests
import os

load_dotenv()
User = get_user_model()
backend_auth = os.getenv("BACKEND_AUTH_HOST")


class TokenAuthMiddleware(BaseMiddleware):
    """
    Middleware to authenticate the user
    from the first Django service
    for websocket connections
    """
    async def __call__(self, scope, receive, send):
        cookies = dict(scope['cookies'])
        if 'access' in cookies:
            # Send a request to the auth Django service to authenticate the user
            response = receive_user(backend_auth, cookies)
            response = await check_response(response)
            scope = await get_or_create_user(response, scope)
        elif 'refresh' in cookies:
            # Send a request to the first Django service to refresh the token
            response = requests.post(
                f'{backend_auth}/token/refresh',
                data={'refresh': cookies['refresh']},
            )
            if response.status_code == 200:
                response = response.json()
                response = receive_user(backend_auth, response)
                response = await check_response(response)
                scope = await get_or_create_user(response, scope)
        return await super().__call__(scope, receive, send)
