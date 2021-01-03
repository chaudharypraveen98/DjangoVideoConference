import json

from channels.consumer import AsyncConsumer
from channels.db import database_sync_to_async

from chat.models import Thread


class ChatConsumer(AsyncConsumer):
    async def websocket_connect(self, event):
        print("websocket connected", event)
        other_user = self.scope['url_route']['kwargs']['username']
        user = self.scope['user']
        thread_object = await self.get_thread(user, other_user)
        chat_room = f"thread_{thread_object.id}"
        self.chat_room = chat_room
        await self.channel_layer.group_add(
            chat_room,
            self.channel_name
        )
        # await asyncio.sleep(5)
        # await self.send({
        #     'type': 'websocket.send',
        #     'text': 'Hello world'
        # })
        # await asyncio.sleep(5)
        # await self.send({
        #     'type': 'websocket.close'
        # })
        await self.send({
            'type': 'websocket.accept'
        })

    async def websocket_receive(self, event):
        # when someone send a message
        print("websocket receive", event)
        # websocket receive {'type': 'websocket.receive', 'text': '{"message":"lol"}'}
        front_text = event.get('text', None)
        if front_text is not None:
            user = self.scope['user']
            username = 'default'
            if user.is_authenticated:
                username = user.username
            loaded_dict_data = json.loads(front_text)
            msg = loaded_dict_data.get('message')
            echo_data = {
                'message': msg,
                'user': username
            }

            # broadcast the message event to be sent
            await self.channel_layer.group_send(
                self.chat_room,
                {
                    'type': "chat_message",
                    'text': json.dumps(echo_data)
                }
            )
            # For sending to one person
            # await self.send({
            #     'type': 'websocket.send',
            #     'text': json.dumps(echo_data)
            # })

    async def chat_message(self, event):
        # send the actual message
        print("message", event)
        await self.send({
            'type': 'websocket.send',
            'text': event["text"]
        })

    async def websocket_disconnect(self, event):
        print("websocket disconnected", event)

    @database_sync_to_async
    def get_thread(self, user, other_username):
        return Thread.objects.get_or_new(user, other_username)[0]
