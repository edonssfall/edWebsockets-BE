from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from chats.models import Status
import requests

User = get_user_model()


def receive_user(host: str, token: dict) -> requests.Response:
    """
    Get the user data from the AUTH-backend.
    """
    return requests.get(
        f'{host}/own-profile',
        headers={'Authorization': f'Bearer {token["access"]}'},
    )


@database_sync_to_async
def create_user_async(username: str, email: str) -> User:
    """
    Create a new user.
    Create a new status for the user.
    """
    user = User.objects.create(
        username=username,
        email=email
    )
    Status.objects.create(user=user, online=True)
    return user


@database_sync_to_async
def get_user_async(email: str) -> User:
    """
    Get the user by email.
    """
    return User.objects.get(email=email)


async def check_response(response: requests.Response) -> dict:
    """
    Check the response from the AUTH-backend.
    """
    if response.status_code != 200:
        raise Exception('Invalid response status code')
    return response.json()

async def get_or_create_user(session_data: dict, scope: dict) -> dict:
    """
    Get or create a user based on the session data.
    """
    email = session_data['user']['email']
    username = scope.get('url_route')['kwargs']['username']

    try:
        user = await get_user_async(email)
    except User.DoesNotExist:
        user = await create_user_async(username, email)

    scope['user'] = user
    scope['cookies']['access'] = session_data['access']
    scope['cookies']['refresh'] = session_data['refresh']

    return scope
