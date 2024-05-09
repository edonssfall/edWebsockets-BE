from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from apps.chats.models import Status

User = get_user_model()


@database_sync_to_async
def create_user_async(username, email):
    user = User.objects.create(
        username=username,
        email=email
    )
    Status.objects.create(user=user, online=True)
    return user
