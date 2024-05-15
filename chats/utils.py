from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from chats.models import Status, Room
from django.utils import timezone

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


@database_sync_to_async
def create_or_get_room(user):
    """
    Create a new chat room or get the existing one.
    """
    user = User.objects.get(username=user)
    room, _ = Room.objects.get_or_create()
    room.users.add(user.id)
    return room