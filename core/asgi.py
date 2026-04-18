
import os
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from django.urls import path
from services.consumers import NotificationConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),

    "websocket": URLRouter([
        path("ws/notifications/", NotificationConsumer.as_asgi()),
    ]),
})