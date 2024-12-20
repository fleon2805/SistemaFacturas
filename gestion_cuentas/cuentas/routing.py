from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path(r'ws/notifications/$', consumers.NotificationConsumer.as_asgi()),
]
