from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from chats.utils import set_status_async
from chats.models import Room, Message
import json

User = get_user_model()


class ConnectionConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.username = self.scope['url_route']['kwargs']['username']

        await self.channel_layer.group_add(
            self.username,
            self.channel_name
        )

        await set_status_async(self.username, True)
        chats = await self.get_chats(self.scope['user'])

        await self.accept()

        await self.send_tokens()
        await self.send(text_data=json.dumps({
            'chats': chats
        }))

    async def disconnect(self, close_code):
        await set_status_async(self.username, False)
        await self.channel_layer.group_discard(self.username, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        search_query = data.get('search_query', None)
        chat = data.get('chat', None)

        if search_query:
            users = await self.filter_users(search_query)
            await self.send(text_data=json.dumps({
                'users': users
            }))
        elif chat:
            room = await self.create_or_get_room(chat)
            await self.send(text_data=json.dumps({
                'room_uuid': str(room.uuid)
            }))

    @database_sync_to_async
    def create_or_get_room(self, user):
        user = User.objects.get(username=user)
        room, _ = Room.objects.get_or_create()
        room.users.add(user.id)
        room.users.add(self.scope['user'].id)
        return room

    @database_sync_to_async
    def get_chats(self, user):
        chats = []
        for chat in Room.objects.filter(users=user.id):
            chat_data = {}
            chat_data['uuid'] = str(chat.uuid)
            chat_data['description'] = chat.description
            users = []
            for user in chat.users.all():
                if user != self.scope['user']:
                    users.append({
                        'id': user.id,
                        'username': user.username,
                        'avatar': user.avatar.url if user.avatar else None
                    })
                chat_data['users'] = users
            message = Message.objects.filter(room_uuid=chat.uuid).last()
            if message:
                chat_data['last_message'] = message.content
                chat_data['timestamp'] = message.timestamp.astimezone().strftime('%Y-%m-%d %H:%M:%S')
            chats.append(chat_data)
        return chats

    async def send_tokens(self):
        await self.send(text_data=json.dumps({
            'access': self.scope['cookies']['access'],
            'refresh': self.scope['cookies']['refresh'],
        }))


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = self.room_name

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        messages = await self.get_messages()

        await self.accept()

        await self.send_messages(messages)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = await self.decode_json(text_data)
        message_type = data.get('type', None)
        if message_type == 'chat.content':
            await self.save_message(data)
            await self.chat_message(data)
        elif message_type == 'chat.status':
            await self.chat_status(data)

    async def chat_message(self, data):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat.message',
                'content': data.get('content'),
                'sender': data.get('sender'),
            }
        )

    async def chat_status(self, data):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat.status',
                'status': data.get('status'),
                'sender': data.get('sender'),
            }
        )

    @database_sync_to_async
    def get_messages(self):
        messages = []
        for message in Message.objects.filter(room_uuid=self.room_name):
            message_data = {}
            if message.file:
                message_data['file'] = message.file.url
            if message.content:
                message_data['content'] = message.content
            message_data['timestamp'] = message.timestamp.astimezone().strftime('%Y-%m-%d %H:%M:%S')
            message_data['sender'] = message.sender.username
            messages.append(message_data)
        return messages

    async def send_messages(self, messages):
        await self.send(text_data=json.dumps({
            'messages': messages,
        }))

    # TODO: Implement this method. now hardcoded timestamp from frontend
    @database_sync_to_async
    def save_message(self, message):
        Message.objects.get_or_create(
            room_uuid=self.room_name,
            sender=User.objects.get(username=message['sender']),
            timestamp=message.get('timestamp', None),
            content=message.get('content'),
            file=message.get('file', None),
        )
