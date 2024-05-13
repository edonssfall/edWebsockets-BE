from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone
from chats.models import Status

User = get_user_model()


@database_sync_to_async
def set_status_async(username, online):
    """
    Set the status of the user to online or offline.
    """
    user = User.objects.get(username=username)
    status, created = Status.objects.get_or_create(user=user)
    if not online:
        status.last_seen = timezone.now()
    status.online = online
    status.save()


@database_sync_to_async
def filter_users(search_query):
    """
    Filter users by search query.
    """
    users = User.objects.filter(username__icontains=search_query)
    return [{
        'id': user.id,
        'username': user.username
    } for user in users]
