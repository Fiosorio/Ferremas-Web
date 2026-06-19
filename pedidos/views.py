from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Pedido
from carrito.models import Carrito

@login_required
def lista_pedidos(request):
    """Vista para mostrar la lista de pedidos del usuario"""
    pedidos = Pedido.objects.filter(usuario=request.user).order_by('-fecha_creacion')
    
    return render(request, 'pedidos/lista.html', {
        'pedidos': pedidos
    })

@login_required
def detalle_pedido(request, numero_pedido):
    """Vista para mostrar el detalle de un pedido"""
    pedido = get_object_or_404(Pedido, numero_pedido=numero_pedido, usuario=request.user)
    
    return render(request, 'pedidos/detalle.html', {
        'pedido': pedido
    })

@login_required
def crear_pedido(request):
    """Vista para crear un nuevo pedido a partir del carrito"""
    carrito = Carrito.objects.filter(usuario=request.user, completado=False).first()
    
    if not carrito or carrito.items.count() == 0:
        messages.warning(request, 'Tu carrito está vacío.')
        return redirect('ver_carrito')
    
    # Aquí iría la lógica para crear el pedido a partir del carrito
    # Por ahora, simplemente redirigimos al carrito
    
    return redirect('checkout')
