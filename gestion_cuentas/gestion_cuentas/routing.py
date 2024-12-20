from django.urls import re_path
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from cuentas.consumers import NotificationConsumer  # Cambia esto si tu consumer está en otro lugar

application = ProtocolTypeRouter({
    "websocket": AuthMiddlewareStack(
        URLRouter([
            re_path(r"ws/notifications/$", NotificationConsumer.as_asgi()),
        ])
    ),
})
