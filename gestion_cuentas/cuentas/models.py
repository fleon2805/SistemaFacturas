from django.contrib.auth.models import AbstractUser, User
from django.db import models
from datetime import date
from django.conf import settings

# Modelo de Usuario
class Usuario(AbstractUser):
    ROLES = [
        ('ADMIN', 'Administrador'),
        ('CONTADOR', 'Contador'),
        ('GERENTE', 'Gerente'),
    ]
    rol = models.CharField(max_length=20, choices=ROLES)

    def __str__(self):
        return f"{self.username} ({self.get_rol_display()})"

# Modelo de Cliente
class Cliente(models.Model):
    nombre = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre

# Modelo de Proveedor
class Proveedor(models.Model):
    nombre = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre


class Factura(models.Model):
    ESTADOS = [
        ('PAGADA', 'Pagada'),
        ('PENDIENTE', 'Pendiente'),
        ('VENCIDA', 'Vencida'),
    ]

    numero = models.CharField(max_length=50, unique=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, null=True, blank=True)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, null=True, blank=True)
    fecha_emision = models.DateField()
    fecha_vencimiento = models.DateField()
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')

    def actualizar_estado(self):
        if self.estado != 'PAGADA':
            hoy = date.today()
            if hoy > self.fecha_vencimiento:
                self.estado = 'VENCIDA'
            elif hoy <= self.fecha_vencimiento:
                self.estado = 'PENDIENTE'
            self.save()

    def __str__(self):
        return f"Factura {self.numero}"
    

class Notificacion(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notificaciones")
    mensaje = models.TextField()
    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notificación para {self.usuario.username}: {self.mensaje}"