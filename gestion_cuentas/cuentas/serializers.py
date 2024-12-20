from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Cliente, Proveedor, Factura
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Notificacion

Usuario = get_user_model()

# Serializer para el modelo Usuario
class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'rol']

# Serializer para el modelo Cliente
class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = '__all__'

# Serializer para el modelo Proveedor
class ProveedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proveedor
        fields = '__all__'

# Serializer para el modelo Factura
class FacturaSerializer(serializers.ModelSerializer):
    cliente = ClienteSerializer(read_only=True)  # Incluye detalles del cliente
    proveedor = ProveedorSerializer(read_only=True)

    class Meta:
        model = Factura
        fields = '__all__'

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Agregar datos personalizados al token
        token['username'] = user.username
        token['role'] = user.rol  # Asegúrate de que el modelo Usuario tiene el campo 'rol'

        return token

class NotificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacion
        fields = '__all__'