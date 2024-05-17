from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from chats.models import Status, Room, Message
from django.utils import timezone

User = get_user_model()


@database_sync_to_async
def set_username_async(username: str, user: User):
    """
    Set the status of the user to online or offline.
    """
    user = User.objects.get(email=user.email)
    user.username = username
    user.save()

@database_sync_to_async
def set_status_async(username: str, online: bool):
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
def filter_users(search_query: str) -> list:
    """
    Filter users by search query.
    """
    users = User.objects.filter(username__icontains=search_query)
    return [{
        'id': user.id,
        'username': user.username
    } for user in users]


@database_sync_to_async
def create_or_get_room(user: str) -> Room:
    """
    Create a new chat room or get the existing one.
    """
    user = User.objects.get(username=user)
    room, _ = Room.objects.get_or_create()
    room.users.add(user)
    room.save()
    return room


# TODO: Implement this method. now hardcoded timestamp from frontend
@database_sync_to_async
def save_message(room_name: str, message: dict) -> Message:
    """
    Save the message to the database.
    """
    return Message.objects.get_or_create(
        room_uuid=room_name,
        sender=User.objects.get(username=message['sender']),
        timestamp=message.get('timestamp', None),
        content=message.get('content'),
        file=message.get('file', None),
    )


@database_sync_to_async
def get_status(user: User) -> Status:
    """
    Helper method to get the status of the user.
    """
    return Status.objects.get(user=user)
