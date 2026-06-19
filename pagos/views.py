import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response

from .models import Orden, Transaccion
from carrito.models import Carrito
from .serializers import OrdenSerializer, TransaccionSerializer

# Importamos la librería de Transbank
from transbank.webpay.webpay_plus.transaction import Transaction
from transbank.error.transbank_error import TransbankError
from transbank.webpay.webpay_plus.transaction import IntegrationCommerceCodes, IntegrationApiKeys, Environment

# Configuración de Transbank (Ambiente de integración)
def get_transbank_config():
    return {
        'commerce_code': IntegrationCommerceCodes.WEBPAY_PLUS,
        'api_key': IntegrationApiKeys.WEBPAY_PLUS,
        'environment': Environment.INTEGRATION
    }

# API Views
class OrdenViewSet(viewsets.ModelViewSet):
    serializer_class = OrdenSerializer
    
    def get_queryset(self):
        return Orden.objects.filter(usuario=self.request.user)
    
    @action(detail=False, methods=['post'])
    def crear_orden(self, request):
        try:
            carrito = Carrito.objects.get(usuario=request.user)
            if not carrito.items.exists():
                return Response({"error": "El carrito está vacío"}, status=status.HTTP_400_BAD_REQUEST)
        except Carrito.DoesNotExist:
            return Response({"error": "No se encontró un carrito para este usuario"}, status=status.HTTP_404_NOT_FOUND)
        
        direccion = request.data.get('direccion', '')
        if not direccion:
            return Response({"error": "Se requiere una dirección de envío"}, status=status.HTTP_400_BAD_REQUEST)
        
        orden = Orden.objects.create(
            usuario=request.user,
            carrito=carrito,
            direccion_envio=direccion,
            total=carrito.total
        )
        
        serializer = OrdenSerializer(orden)
        return Response(serializer.data)

# Template Views
@login_required
def checkout(request):
    try:
        carrito = Carrito.objects.get(usuario=request.user)
        if not carrito.items.exists():
            return redirect('ver_carrito')
    except Carrito.DoesNotExist:
        return redirect('ver_carrito')
    
    if request.method == 'POST':
        direccion = request.POST.get('direccion', '')
        if not direccion:
            return render(request, 'pagos/checkout.html', {
                'carrito': carrito,
                'error': 'Se requiere una dirección de envío'
            })
        
        orden = Orden.objects.create(
            usuario=request.user,
            carrito=carrito,
            direccion_envio=direccion,
            total=carrito.total,
            estado='pendiente'
        )
        
        try:
            tx = Transaction(**get_transbank_config())
            
            buy_order = str(orden.id)
            session_id = str(request.user.id)
            amount = int(orden.total)
            
            # AJUSTE: Usamos 'pago_retorno' porque así está en tu urls.py
            return_url = request.build_absolute_uri(reverse('pago_retorno'))
            
            response = tx.create(buy_order, session_id, amount, return_url)
            
            Transaccion.objects.create(
                orden=orden,
                token=response.token,
                monto=orden.total,
                estado='INICIADA'
            )
            
            # Redirigimos al template intermedio que hace el POST automático
            return render(request, 'pagos/checkout.html', {
                'url': response.url,
                'token': response.token,
                'paso_pago': True # Flag para saber que ya vamos a pagar
            })
            
        except TransbankError as e:
            orden.estado = 'cancelado'
            orden.save()
            return render(request, 'pagos/error.html', {'error': str(e)})
    
    return render(request, 'pagos/checkout.html', {'carrito': carrito})

@csrf_exempt
def pago_retorno(request):
    # Transbank puede enviar el token por POST o GET dependiendo del caso
    token = request.POST.get('token_ws') or request.GET.get('token_ws')
    
    if not token:
        return render(request, 'pagos/error.html', {'error': 'Transacción cancelada o sin token.'})
    
    try:
        transaccion = get_object_or_404(Transaccion, token=token)
        orden = transaccion.orden
        
        tx = Transaction(**get_transbank_config())
        response = tx.commit(token)
        
        transaccion.estado = response.status
        
        if response.status == 'AUTHORIZED':
            transaccion.codigo_autorizacion = response.authorization_code
            transaccion.save()
            
            orden.estado = 'pagado'
            orden.save()
            
            # Limpiar carrito
            carrito_actual = Carrito.objects.get(usuario=orden.usuario)
            carrito_actual.items.all().delete() 
            
            return render(request, 'pagos/confirmacion.html', {
                'orden': orden,
                'exito': True,
                'response': response
            })
        else:
            transaccion.save()
            return render(request, 'pagos/confirmacion.html', {'exito': False})
            
    except Exception as e:
        return render(request, 'pagos/error.html', {'error': str(e)})

@login_required
def historial_ordenes(request):
    ordenes = Orden.objects.filter(usuario=request.user).order_by('-fecha_creacion')
    return render(request, 'pagos/historial_ordenes.html', {'ordenes': ordenes})

@login_required
def detalle_orden(request, orden_id):
    orden = get_object_or_404(Orden, id=orden_id, usuario=request.user)
    return render(request, 'pagos/detalle_orden.html', {'orden': orden})