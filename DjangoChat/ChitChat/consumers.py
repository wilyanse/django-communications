# consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatRoom, Message
from django.contrib.auth.models import User

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        # Add user to the group for the chat room
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Remove user from group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json.get('message', '')
        sender = self.scope['user']  # current logged-in user

        room = await self.get_room(self.room_name)

        # If there's a file URL (for the uploaded file), send it along with the message
        attachment_url = text_data_json.get('attachment', None)

        # Save the message
        await self.save_message(room, sender, message, attachment_url)

        # Send the message to the group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': sender.username,
                'attachment': attachment_url  # Send attachment info if present
            }
        )

    async def chat_message(self, event):
        message = event['message']
        sender = event['sender']
        attachment = event.get('attachment', None)  # Get attachment URL if present

        await self.send(text_data=json.dumps({
            'message': message,
            'sender': sender,
            'attachment': attachment  # Send the attachment URL to the frontend
        }))

    @database_sync_to_async
    def get_room(self, room_name):
        user_ids = room_name.split('_')
        user1 = User.objects.get(id=int(user_ids[0]))
        user2 = User.objects.get(id=int(user_ids[1]))
        return ChatRoom.objects.get_or_create(user1=user1, user2=user2)[0]

    @database_sync_to_async
    def save_message(self, room, sender, message, attachment_url=None):
        Message.objects.create(room=room, sender=sender, content=message, attachment=attachment_url)

class CallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        data = json.loads(text_data)
        decision = data.get('decision')

        if decision == 'accept':
            # Notify server to accept the call
            await self.channel_layer.group_send(
                'call_group', {'type': 'call.accepted'}
            )
        elif decision == 'reject':
            # Notify server to reject the call
            await self.channel_layer.group_send(
                'call_group', {'type': 'call.rejected'}
            )

    async def call_accepted(self, event):
        await self.send(text_data=json.dumps({'status': 'accepted'}))

    async def call_rejected(self, event):
        await self.send(text_data=json.dumps({'status': 'rejected'}))