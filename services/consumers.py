import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .models import Booking, ChatMessage, Notification
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger(__name__)


# -------------------------------
# 🔔 NOTIFICATION CONSUMER
# -------------------------------
class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")

        if not user or not user.is_authenticated:
            await self.close()
            return

        # 🔥 user-specific group
        self.group_name = f"notifications_{user.id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_notification(self, event):
        await self.send(text_data=json.dumps({
            "message": event["message"],
            "link": event.get("link", "#"),
            "id": event.get("id"),
        }))


# -------------------------------
# 💬 CHAT CONSUMER
# -------------------------------
class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.booking_id = self.scope["url_route"]["kwargs"]["booking_id"]
        self.room_group_name = f"chat_{self.booking_id}"
        self.user = self.scope.get("user")

        if not self.user or not self.user.is_authenticated:
            await self.close()
            return

        if not await self._user_can_access_booking():
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            payload = json.loads(text_data)
        except json.JSONDecodeError:
            return

        message = (payload.get("message") or "").strip()
        if not message:
            return

        # 🔥 SAVE MESSAGE
        chat_message = await self._create_chat_message(message)
        if chat_message is None:
            return

        # 🔥 SEND TO CHAT ROOM
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": chat_message.message,
                "sender": chat_message.sender.username,
                "timestamp": chat_message.timestamp.strftime("%H:%M"),
            },
        )

        # ===================================================
        # 🔥🔥🔥 MAIN LOGIC (CHAT → NOTIFICATION)
        # ===================================================

        receiver_id = await self._get_receiver_id()

        # 🔥 Create DB notification
        await self._create_notification(receiver_id, message)

        # 🔥 Send real-time notification
        await self.channel_layer.group_send(
            f"notifications_{receiver_id}",
            {
                "type": "send_notification",
                "message": f"{self.user.username}: {message[:25]}",
                "link": f"/services/chat/{self.booking_id}/",
            },
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "message": event["message"],
            "sender": event["sender"],
            "timestamp": event.get("timestamp"),
        }))

    # -------------------------------
    # 🔒 ACCESS CHECK
    # -------------------------------
    @database_sync_to_async
    def _user_can_access_booking(self):
        try:
            booking = Booking.objects.select_related("customer", "service__vendor").get(
                id=self.booking_id
            )
        except Booking.DoesNotExist:
            return False

        return self.user.id in {booking.customer_id, booking.service.vendor_id}

    # -------------------------------
    # 💾 SAVE MESSAGE
    # -------------------------------
    @database_sync_to_async
    def _create_chat_message(self, message):
        try:
            booking = Booking.objects.select_related("customer", "service__vendor").get(
                id=self.booking_id
            )
        except Booking.DoesNotExist:
            return None

        if self.user.id not in {booking.customer_id, booking.service.vendor_id}:
            return None

        return ChatMessage.objects.create(
            booking=booking,
            sender=self.user,
            message=message,
        )

    # -------------------------------
    # 🎯 GET RECEIVER
    # -------------------------------
    @database_sync_to_async
    def _get_receiver_id(self):
        booking = Booking.objects.get(id=self.booking_id)

        if self.user.id == booking.customer_id:
            return booking.service.vendor_id
        else:
            return booking.customer_id

    # -------------------------------
    # 🔔 CREATE NOTIFICATION
    # -------------------------------
    @database_sync_to_async
    def _create_notification(self, user_id, message):
        booking = Booking.objects.select_related("service").get(id=self.booking_id)
        user = User.objects.get(id=user_id)

        preview = message[:30] + ("..." if len(message) > 30 else "")

        Notification.objects.create(
            user=user,
            message=f"{self.user.username} ({booking.service.title}): {preview}",
            link=f"/services/chat/{self.booking_id}/",
            is_read=False
        )