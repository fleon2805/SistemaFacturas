from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.shortcuts import redirect
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer
import csv
from .models import Cliente, Proveedor, Factura
from .serializers import UsuarioSerializer, ClienteSerializer, ProveedorSerializer, FacturaSerializer
from django.db.models import Sum, Count
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.decorators import action
from datetime import date, timedelta
from django.db.models.functions import TruncMonth
from django.db.models import Q
import pandas as pd
from django.http import JsonResponse
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfgen import canvas
import openpyxl
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from .models import Notificacion
from rest_framework.views import APIView
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now
from django.shortcuts import get_object_or_404
from .serializers import NotificacionSerializer

Usuario = get_user_model()

# Viewset para el modelo Usuario
class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated]

# Viewset para el modelo Cliente
class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]

# Viewset para el modelo Proveedor
class ProveedorViewSet(viewsets.ModelViewSet):
    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer
    permission_classes = [IsAuthenticated]

class NotificacionesView(APIView):
    def get(self, request):
        notificaciones = Notificacion.objects.filter(leido=False).order_by('-fecha_creacion')
        data = [{"id": n.id, "mensaje": n.mensaje, "fecha": n.fecha_creacion} for n in notificaciones]
        return Response(data)

@api_view(['POST'])
def marcar_notificacion_leida(request, pk):
    try:
        notificacion = Notificacion.objects.get(pk=pk)
        notificacion.marcar_leido()
        return Response({"mensaje": "Notificación marcada como leída."})
    except Notificacion.DoesNotExist:
        return Response({"error": "Notificación no encontrada."}, status=404)

# Viewset para el modelo Factura con filtros
class FacturaViewSet(viewsets.ModelViewSet):
    queryset = Factura.objects.select_related('cliente', 'proveedor').all()
    serializer_class = FacturaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['estado', 'cliente', 'fecha_emision', 'fecha_vencimiento','proveedor']  # Campos filtrables
    
    @action(detail=False, methods=['get'], url_path='cobrar')
    def facturas_por_cobrar(self, request):
        facturas = Factura.objects.filter(cliente__isnull=False, proveedor__isnull=True)
        serializer = self.get_serializer(facturas, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='pagar')
    def facturas_por_pagar(self, request):
        facturas = Factura.objects.filter(cliente__isnull=True, proveedor__isnull=False)
        serializer = self.get_serializer(facturas, many=True)
        return Response(serializer.data)

# Función para exportar facturas en formato CSV
def exportar_facturas_csv(request):
    """
    Exporta todas las facturas en formato CSV.
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="facturas.csv"'

    # Configurar el escritor CSV
    writer = csv.writer(response)
    writer.writerow(['Número', 'Cliente', 'Fecha de Emisión', 'Fecha de Vencimiento', 'Monto', 'Estado'])

    # Extraer las facturas y escribirlas en el CSV
    facturas = Factura.objects.select_related('cliente').all()  # Optimiza consultas con select_related
    for factura in facturas:
        writer.writerow([
            factura.numero,
            factura.cliente.nombre if factura.cliente else 'Sin cliente',
            factura.fecha_emision,
            factura.fecha_vencimiento,
            factura.monto,
            factura.estado
        ])

    return response


# Función para importar facturas desde un archivo CSV
def importar_facturas_csv(request):
    """
    Importa facturas desde un archivo CSV cargado por el usuario.
    """
    if request.method == 'POST' and request.FILES.get('archivo', None):
        archivo = request.FILES['archivo']
        reader = csv.reader(archivo.read().decode('utf-8').splitlines())
        next(reader)  # Omitir encabezados

        for row in reader:
            numero, cliente_nombre, fecha_emision, fecha_vencimiento, monto, estado = row
            # Obtener o crear el cliente
            cliente, _ = Cliente.objects.get_or_create(nombre=cliente_nombre)
            # Crear la factura
            Factura.objects.create(
                numero=numero,
                cliente=cliente,
                fecha_emision=fecha_emision,
                fecha_vencimiento=fecha_vencimiento,
                monto=monto,
                estado=estado
            )

    return redirect('facturas_list')  # Cambia según la vista o URL de tu aplicación


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    
    

@api_view(['GET'])
def obtener_totales(request):
    try:
        monto_por_cobrar = Factura.objects.filter(cliente__isnull=False, proveedor__isnull=True).aggregate(total=Sum('monto'))['total'] or 0
        monto_por_pagar = Factura.objects.filter(proveedor__isnull=False, cliente__isnull=True).aggregate(total=Sum('monto'))['total'] or 0
        return Response({
            "monto_por_cobrar": monto_por_cobrar,
            "monto_por_pagar": monto_por_pagar
        })
    except Exception as e:
        return Response({"error": str(e)}, status=500)
    
@api_view(['GET'])
def obtener_totales_detallados(request):
    try:
        monto_por_cobrar = Factura.objects.filter(cliente__isnull=False, proveedor__isnull=True).aggregate(total=Sum('monto'))['total'] or 0
        monto_por_pagar = Factura.objects.filter(proveedor__isnull=False, cliente__isnull=True).aggregate(total=Sum('monto'))['total'] or 0
        facturas_vencidas = Factura.objects.filter(estado='VENCIDA').count()
        return Response({
            "monto_por_cobrar": monto_por_cobrar,
            "monto_por_pagar": monto_por_pagar,
            "facturas_vencidas": facturas_vencidas
        })
    except Exception as e:
        return Response({"error": str(e)}, status=500)
    
@api_view(['GET'])
def proyeccion_flujo_caja(request):
    try:
        hoy = date.today()
        proyeccion_cobrar = Factura.objects.filter(
            cliente__isnull=False, proveedor__isnull=True,
            fecha_vencimiento__gte=hoy, fecha_vencimiento__lte=hoy + timedelta(days=30)
        ).aggregate(total=Sum('monto'))['total'] or 0

        proyeccion_pagar = Factura.objects.filter(
            proveedor__isnull=False, cliente__isnull=True,
            fecha_vencimiento__gte=hoy, fecha_vencimiento__lte=hoy + timedelta(days=30)
        ).aggregate(total=Sum('monto'))['total'] or 0

        return Response({
            "proyeccion_cobrar": proyeccion_cobrar,
            "proyeccion_pagar": proyeccion_pagar
        })
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(['GET'])
def montos_por_mes(request):
    try:
        # Agrupar facturas por mes
        montos_por_mes = (
            Factura.objects.annotate(mes=TruncMonth('fecha_vencimiento'))
            .values('mes')
            .annotate(
                total_cobrar=Sum('monto', filter=Q(cliente__isnull=False)),
                total_pagar=Sum('monto', filter=Q(proveedor__isnull=False))
            )
            .order_by('mes')
        )

        # Convertir a lista para el formato esperado
        montos_por_mes = list(montos_por_mes)
        return Response(montos_por_mes)
    except Exception as e:
        return Response({"error": str(e)}, status=500)
    
@api_view(['GET'])
def facturas_vencidas(request):
    try:
        # Filtrar facturas vencidas
        facturas_vencidas = Factura.objects.filter(estado='VENCIDA').values(
            'id', 'numero', 'cliente__nombre', 'monto', 'fecha_vencimiento'
        )

        # Crear una lista con los datos necesarios
        data = [
            {
                'id': factura['id'],
                'numero': factura['numero'],
                'cliente': factura['cliente__nombre'] or 'Sin Cliente',
                'monto': factura['monto'],
                'fecha_vencimiento': factura['fecha_vencimiento']
            }
            for factura in facturas_vencidas
        ]

        return Response(data)
    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(['POST'])
def importar_facturas(request):
    if request.method == "POST" and request.FILES.get("archivo"):
        archivo = request.FILES["archivo"]
        try:
            # Cargar el archivo según la extensión
            if archivo.name.endswith('.csv'):
                datos = pd.read_csv(archivo)
            elif archivo.name.endswith(('.xls', '.xlsx')):
                datos = pd.read_excel(archivo)
            else:
                return JsonResponse({"error": "Formato de archivo no soportado"}, status=400)

            errores = []  # Lista para registrar errores
            for _, fila in datos.iterrows():
                try:
                    cliente = None
                    proveedor = None

                    # Validar y obtener el cliente si existe
                    if pd.notna(fila.get("cliente")):  # Verificar que no sea NaN
                        cliente = Cliente.objects.filter(id=int(fila["cliente"])).first()
                        if not cliente:
                            raise ValueError(f"Cliente con ID {fila['cliente']} no encontrado.")

                    # Validar y obtener el proveedor si existe
                    if pd.notna(fila.get("proveedor")):  # Verificar que no sea NaN
                        proveedor = Proveedor.objects.filter(id=int(fila["proveedor"])).first()
                        if not proveedor:
                            raise ValueError(f"Proveedor con ID {fila['proveedor']} no encontrado.")

                    # Crear la factura
                    Factura.objects.create(
                        numero=str(fila.get("numero", "")).strip(),
                        cliente=cliente,
                        proveedor=proveedor,
                        fecha_emision=fila.get("fecha_emision"),
                        fecha_vencimiento=fila.get("fecha_vencimiento"),
                        monto=float(fila.get("monto", 0)),
                        estado=fila.get("estado", "PENDIENTE"),
                    )
                except Exception as e:
                    errores.append({
                        "fila": fila.to_dict(),
                        "error": str(e)
                    })

            if errores:
                return JsonResponse({
                    "mensaje": "Algunas facturas no se pudieron importar.",
                    "errores": errores
                }, status=400)

            return JsonResponse({"mensaje": "Facturas importadas exitosamente"})
        except Exception as e:
            print(f"Error general: {e}")
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Método no permitido"}, status=405)

@api_view(['GET'])
def exportar_facturas_pdf(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="facturas.pdf"'

    # Crear el documento PDF
    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []

    # Título del documento
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import getSampleStyleSheet

    styles = getSampleStyleSheet()
    title = Paragraph("Listado de Facturas", styles['Title'])
    elements.append(title)

    # Encabezados de la tabla
    encabezados = [
        "Número", "Cliente", "Proveedor", 
        "Fecha Emisión", "Fecha Vencimiento", "Monto", "Estado"
    ]

    # Datos de la tabla
    facturas = Factura.objects.all()
    datos = [
        [
            factura.numero, 
            factura.cliente.nombre if factura.cliente else "Sin cliente",
            factura.proveedor.nombre if factura.proveedor else "Sin proveedor",
            factura.fecha_emision.strftime("%Y-%m-%d"),
            factura.fecha_vencimiento.strftime("%Y-%m-%d"),
            f"S/. {factura.monto:.2f}",
            factura.estado
        ]
        for factura in facturas
    ]

    # Crear la tabla
    tabla = Table([encabezados] + datos, colWidths=[70, 100, 100, 90, 90, 70, 70])
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),  # Fondo para encabezados
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),  # Color del texto en encabezados
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Centrar el texto
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Fuente en encabezados
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),  # Espaciado en encabezados
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),  # Fondo para filas
        ('GRID', (0, 0), (-1, -1), 1, colors.black),  # Bordes de tabla
    ]))

    elements.append(tabla)

    # Construir el PDF
    doc.build(elements)
    return response

@api_view(['GET'])
def exportar_facturas_excel(request):
    facturas = Factura.objects.all().values(
        'numero', 'cliente__nombre', 'proveedor__nombre',
        'fecha_emision', 'fecha_vencimiento', 'monto', 'estado'
    )
    df = pd.DataFrame(facturas)
    df.rename(columns={
        'cliente__nombre': 'Cliente',
        'proveedor__nombre': 'Proveedor'
    }, inplace=True)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="facturas.xlsx"'

    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Facturas')

    return response

@api_view(['GET'])
def obtener_notificaciones(request):
    hoy = date.today()

    # Obtener facturas vencidas
    facturas_vencidas = Factura.objects.filter(fecha_vencimiento__lt=hoy)

    # Obtener facturas por vencer en los próximos 3 días
    proximas_a_vencer = Factura.objects.filter(
        fecha_vencimiento__gte=hoy,
        fecha_vencimiento__lte=hoy + timedelta(days=3)
    )

    # Generar notificaciones
    notificaciones = []

    for factura in facturas_vencidas:
        notificaciones.append({
            "mensaje": f"La factura {factura.numero} está vencida.",
            "tipo": "vencida",
            "fecha_vencimiento": str(factura.fecha_vencimiento),
        })

    for factura in proximas_a_vencer:
        notificaciones.append({
            "mensaje": f"La factura {factura.numero} está por vencer.",
            "tipo": "proxima",
            "fecha_vencimiento": str(factura.fecha_vencimiento),
        })

    return Response(notificaciones)


@csrf_exempt
@login_required
def marcar_notificacion_leida(request, id):
    notificacion = get_object_or_404(Notificacion, id=id, usuario=request.user)
    notificacion.leida = True
    notificacion.save()
    return JsonResponse({"mensaje": "Notificación marcada como leída"})

def verificar_facturas_vencidas():
    facturas = Factura.objects.filter(estado="PENDIENTE", fecha_vencimiento__lte=now() + timedelta(days=3))
    for factura in facturas:
        mensaje = f"La factura {factura.numero} está próxima a vencer."
        Notificacion.objects.create(usuario=factura.cliente.usuario, mensaje=mensaje)