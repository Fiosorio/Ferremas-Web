from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from productos.models import Producto, Categoria

# IMPORTACIONES PARA TRANSBANK
import random
from transbank.webpay.webpay_plus.transaction import Transaction
from transbank.common.options import WebpayOptions
from transbank.common.integration_type import IntegrationType

def home(request):
    productos_destacados = Producto.objects.filter(destacado=True)[:3]
    categorias = Categoria.objects.all()
    return render(request, 'home.html', {
        'productos_destacados': productos_destacados,
        'categorias': categorias
    })

def catalogo(request):
    productos = Producto.objects.all()
    categorias = Categoria.objects.all()
    return render(request, 'tienda/catalogo.html', {
        'productos': productos,
        'categorias': categorias
    })

def detalle_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    return render(request, 'tienda/detalle_producto.html', {'producto': producto})

def ofertas(request):
    ofertas = []  
    return render(request, 'tienda/ofertas.html', {'ofertas': ofertas})

def contacto(request):
    if request.method == 'POST':
        messages.success(request, "Tu mensaje ha sido enviado correctamente.")
        return redirect('contacto')
    return render(request, 'tienda/contacto.html')

def nosotros(request):
    return render(request, 'tienda/nosotros.html')

def terminos(request):
    return render(request, 'tienda/terminos.html')

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Bienvenido, {username}!")
                return redirect('home')
            else:
                messages.error(request, "Usuario o contraseña incorrectos.")
        else:
            messages.error(request, "Usuario o contraseña incorrectos.")
    else:
        form = AuthenticationForm()
    return render(request, 'tienda/login.html', {'form': form})

def registro(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "¡Registro exitoso!")
            return redirect('home')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = UserCreationForm()
    return render(request, 'tienda/registro.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, "Has cerrado sesión correctamente.")
    return redirect('home')

@login_required
def perfil(request):
    return render(request, 'tienda/perfil.html')

@login_required
def pedidos(request):
    pedidos = []  
    return render(request, 'tienda/pedidos.html', {'pedidos': pedidos})

def carrito(request):
    carrito_sesion = request.session.get('carrito', {})
    productos_para_template = []
    total_acumulado = 0

    for p_id, item in carrito_sesion.items():
        producto = get_object_or_404(Producto, pk=p_id)
        subtotal = producto.precio * item['cantidad']
        total_acumulado += subtotal
        productos_para_template.append({
            'producto': producto,
            'cantidad': item['cantidad'],
            'subtotal': subtotal,
        })

    return render(request, 'tienda/ver_carrito.html', {
        'productos': productos_para_template,
        'total': total_acumulado
    })

def eliminar_del_carrito(request, producto_id):
    carrito = request.session.get('carrito', {})
    p_id = str(producto_id)
    if p_id in carrito:
        del carrito[p_id]
        request.session['carrito'] = carrito
        request.session.modified = True
        messages.success(request, "Producto eliminado.")
    return redirect('carrito')

def actualizar_carrito(request, producto_id):
    if request.method == 'POST':
        cantidad = int(request.POST.get('cantidad', 1))
        carrito = request.session.get('carrito', {})
        p_id = str(producto_id)
        if p_id in carrito and cantidad > 0:
            carrito[p_id]['cantidad'] = cantidad
            request.session['carrito'] = carrito
            request.session.modified = True
    return redirect('carrito')

def agregar_al_carrito(request, producto_id):
    carrito_sesion = request.session.get('carrito', {})
    p_id = str(producto_id)
    if p_id not in carrito_sesion:
        carrito_sesion[p_id] = {'cantidad': 1}
    else:
        carrito_sesion[p_id]['cantidad'] += 1
    request.session['carrito'] = carrito_sesion
    request.session.modified = True 
    messages.success(request, "Producto añadido.")
    return redirect('catalogo')

def limpiar_carrito(request):
    request.session['carrito'] = {}
    return redirect('carrito')

# VISTAS DE PAGO CORREGIDAS PARA EVITAR DECIMALES
def iniciar_pago(request):
    carrito_sesion = request.session.get('carrito', {})
    total_acumulado = 0

    for p_id, item in carrito_sesion.items():
        producto = get_object_or_404(Producto, pk=p_id)
        total_acumulado += (producto.precio * item['cantidad'])

    if total_acumulado <= 0:
        messages.error(request, "El carrito está vacío.")
        return redirect('carrito')

    # CORRECCIÓN CLAVE: Forzamos el monto a entero para Webpay
    monto_final = int(total_acumulado)

    buy_order = str(random.randint(100000, 999999))
    session_id = str(request.user.id) if request.user.is_authenticated else "anonimo"
    return_url = request.build_absolute_uri('/pago-confirmacion/')

    tx = Transaction(WebpayOptions("597055555532", "579B532A7440BB0C9079DED94D31EA1615BACEB56610332264630D42D0A36B1C", IntegrationType.TEST))
    
    try:
        response = tx.create(buy_order, session_id, monto_final, return_url)
        return render(request, 'tienda/ir_a_pagar.html', {
            'url': response['url'],
            'token': response['token']
        })
    except Exception as e:
        messages.error(request, f"Error al conectar con Webpay: {e}")
        return redirect('carrito')

def pago_confirmacion(request):
    token = request.GET.get("token_ws")
    
    if not token:
        messages.error(request, "Transacción cancelada.")
        return redirect('carrito')

    tx = Transaction(WebpayOptions("597055555532", "579B532A7440BB0C9079DED94D31EA1615BACEB56610332264630D42D0A36B1C", IntegrationType.TEST))
    
    try:
        response = tx.commit(token)
        if response['status'] == 'AUTHORIZED':
            request.session['carrito'] = {}
            request.session.modified = True
            return render(request, 'tienda/pago_exitoso.html', {'res': response})
        else:
            return render(request, 'tienda/pago_fallido.html', {'res': response})
    except Exception as e:
        messages.error(request, f"Error al confirmar el pago: {e}")
        return redirect('carrito')