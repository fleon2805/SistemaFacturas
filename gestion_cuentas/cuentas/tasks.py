from celery import shared_task
from datetime import date, timedelta
from .models import Factura
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.mail import send_mail
from .models import Notificacion


@shared_task
def actualizar_estados_facturas():
    hoy = date.today()
    facturas_pendientes = Factura.objects.filter(estado='PENDIENTE')
    facturas_vencidas = []

    for factura in facturas_pendientes:
        if factura.fecha_vencimiento < hoy:
            factura.estado = 'VENCIDA'
            facturas_vencidas.append(factura)
        elif factura.fecha_vencimiento >= hoy:
            factura.estado = 'PENDIENTE'
        factura.save()

    # Enviar notificación si hay facturas vencidas
    if facturas_vencidas:
        notificar_facturas_vencidas()

def notificar_facturas_vencidas():
    channel_layer = get_channel_layer()
    message = "Tienes facturas vencidas o próximas a vencer."

    # Enviar notificación al grupo
    async_to_sync(channel_layer.group_send)(
        "notifications",
        {
            "type": "send_notification",
            "message": message,
        }
    )


@shared_task
def notificar_facturas():
    hoy = date.today()
    tres_dias_despues = hoy + timedelta(days=3)

    facturas_por_vencer = Factura.objects.filter(
        estado='PENDIENTE',
        fecha_vencimiento__lte=tres_dias_despues,
        fecha_vencimiento__gte=hoy
    )

    facturas_vencidas = Factura.objects.filter(
        estado='PENDIENTE',
        fecha_vencimiento__lt=hoy
    )

    for factura in facturas_por_vencer:
        Notificacion.objects.create(
            mensaje=f"Factura {factura.numero} está por vencer el {factura.fecha_vencimiento}."
        )

    for factura in facturas_vencidas:
        Notificacion.objects.create(
            mensaje=f"Factura {factura.numero} ya venció el {factura.fecha_vencimiento}."
        )

    return "Notificaciones generadas."