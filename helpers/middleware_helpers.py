from channels.db import database_sync_to_async
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
import requests

User = get_user_model()


def receive_user(host, token):
    return requests.get(
        f'{host}/profile/is-logged',
        headers={'Authorization': f"Bearer {token['access']}"},
    )


@database_sync_to_async
def get_user_async(email):
    return User.objects.get(email=email)


@database_sync_to_async
def create_user_async(username, email):
    return User.objects.create(
        username=username['username'],
        email=email
    )


async def check_response(response, scope):
    if response.status_code == 200:
        session_data = response.json()
        key, value = scope['query_string'].decode('utf-8').split('=')
        username = {key: value}
        email = session_data['email']

        async def get_user():
            user = await get_user_async(email)
            return user

        async def create_user():
            user = await create_user_async(username, email)
            return user

        try:
            user = await get_user()
        except User.DoesNotExist:
            user = await create_user()

        scope['user'] = user
    return scope
