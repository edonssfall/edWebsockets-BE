from chats.models import Status, User
from django.contrib.sites import requests


def refresh_access_token(refresh_token):
    url = 'http://localhost/api/token/refresh/'
    data = {'refresh': refresh_token}
    response = requests.post(url, data=data)

    if response.status_code == 200:
        return response.json().get('access')
    else:
        return None

async def set_user_online(user: User):
    status, created = Status.objects.get_or_create(user=user)
    status.online = True
    status.save()

async def set_user_offline(user: User):
    status = Status.objects.get(user=user)
    status.online = False
    status.save()

async def update_user_status(username, new_status):
    status, created = Status.objects.get_or_create(user__username=username)
    status.online = new_status
    status.save()