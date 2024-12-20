from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UsuarioViewSet,
    ClienteViewSet,
    ProveedorViewSet,
    FacturaViewSet,
    NotificacionesView,
    exportar_facturas_csv,
    importar_facturas_csv,
    obtener_totales,
    obtener_totales_detallados,
    proyeccion_flujo_caja,
    montos_por_mes,
    facturas_vencidas,
    importar_facturas,
    exportar_facturas_pdf,
    exportar_facturas_excel,
    obtener_notificaciones,
    marcar_notificacion_leida,
)

# Configuración del router para los ViewSets
router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet)
router.register(r'clientes', ClienteViewSet)
router.register(r'proveedores', ProveedorViewSet)
router.register(r'facturas', FacturaViewSet)

# Agregar las rutas de exportación e importación
urlpatterns = [
    path('facturas/importar/', importar_facturas, name='importar_facturas'),
    path('facturas/totales/', obtener_totales, name='obtener_totales'),
    path('facturas/exportar-pdf/', exportar_facturas_pdf, name='exportar_facturas_pdf'),
    path('facturas/exportar-excel/', exportar_facturas_excel, name='exportar_facturas_excel'),
    path('notificaciones/', obtener_notificaciones, name='obtener_notificaciones'),
    path('notificaciones/<int:id>/leer/', marcar_notificacion_leida, name='marcar_notificacion_leida'),
    path('facturas/totales-detallados/', obtener_totales_detallados, name='obtener_totales_detallados'),
    path('facturas/proyeccion/', proyeccion_flujo_caja, name='proyeccion_flujo_caja'),
    path('facturas/montos-por-mes/', montos_por_mes, name='montos_por_mes'),
    path('facturas/vencidas/', facturas_vencidas, name='facturas_vencidas'),
    path('', include(router.urls)),  # Incluye las rutas de los ViewSets
    
]
