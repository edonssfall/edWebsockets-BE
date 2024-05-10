from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from django.utils import timezone
from chats.models import Status
import requests

User = get_user_model()


def receive_user(host, token):
    return requests.get(
        f'{host}/own-profile',
        headers={'Authorization': f'Bearer {token["access"]}'},
    )


@database_sync_to_async
def create_user_async(username, email):
    user = User.objects.create(
        username=username,
        email=email
    )
    Status.objects.create(user=user, online=True)
    return user


@database_sync_to_async
def get_user_async(email):
    return User.objects.get(email=email)


@database_sync_to_async
def set_status_async(username, online):
    user = User.objects.get(username=username)
    status, created = Status.objects.get_or_create(user=user)
    if not online:
        status.last_seen = timezone.now()
    status.online = online
    status.save()


async def check_response(response, scope):
    if response.status_code == 200:
        session_data = response.json()
        scope['cookies']['access'] = session_data['access']
        scope['cookies']['refresh'] = session_data['refresh']
        email = session_data['user']['email']

        async def get_user():
            user = await get_user_async(email)
            return user

        async def create_user():
            username = scope.get('url_route')['kwargs']['username']
            user = await create_user_async(username, email)
            return user

        try:
            user = await get_user()
        except User.DoesNotExist:
            user = await create_user()

        scope['user'] = user
    return scope
