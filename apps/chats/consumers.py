from channels.generic.websocket import AsyncJsonWebsocketConsumer
import json


class SomeConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()


    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = await self.decode_json(text_data)
        message_type = data.get('type')
        sender = data.get('sender')
        if message_type == 'chat.message':
            message = data.get('message')
            await self.chat_message(message, sender)
        elif message_type == 'chat.status':
            status = data.get('status')
            await self.chat_status(status, sender)

    async def chat_message(self, message, sender):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'send_message',
                'message': message,
                'sender': sender,
            }
        )

    async def chat_status(self, status, sender):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'send_status',
                'status': status,
                'sender': sender,
            }
        )

    async def send_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat.message',
            'message': event['message'],
            'sender': event['sender'],
        }))

    async def send_status(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat.status',
            'status': event['status'],
            'sender': event['sender'],
        }))
