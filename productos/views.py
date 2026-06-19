from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib import messages
from .services import ProductoService
from django.contrib.auth.decorators import user_passes_test
from .models import Producto
from .forms import ProductoForm
from .forms import CategoriaForm
from .models import Producto, Categoria

def lista_productos(request):
    """Vista para mostrar el catálogo de productos"""
    pagina = int(request.GET.get('page', 1))
    
    # Usar el servicio para obtener los productos
    resultado = ProductoService.get_productos(pagina=pagina)
    
    # Obtener categorías para el menú lateral
    categorias = ProductoService.get_categorias()
    
    return render(request, 'productos/lista.html', {
        'productos': resultado['productos'],
        'total': resultado['total'],
        'pagina_actual': resultado['pagina_actual'],
        'total_paginas': resultado['total_paginas'],
        'categorias': categorias
    })

def detalle_producto(request, slug):
    """Vista para mostrar el detalle de un producto"""
    # Usar el servicio para obtener el producto
    producto = ProductoService.get_producto_por_slug(slug)
    
    if not producto:
        messages.error(request, 'El producto solicitado no existe o no está disponible.')
        return redirect('lista_productos')
    
    # Obtener productos relacionados
    productos_relacionados = ProductoService.get_productos_relacionados(producto)
    
    return render(request, 'tienda/detalle_producto.html', {
        'producto': producto,
        'productos_relacionados': productos_relacionados
    })

def productos_por_categoria(request, slug):
    """Vista para mostrar productos por categoría"""
    pagina = int(request.GET.get('page', 1))
    
    # Usar el servicio para obtener los productos filtrados por categoría
    resultado = ProductoService.get_productos(
        filtros={'categoria': slug},
        pagina=pagina
    )
    
    # Obtener categorías para el menú lateral
    categorias = ProductoService.get_categorias()
    
    # Obtener la categoría actual
    categoria_actual = next((c for c in categorias if c.slug == slug), None)
    
    return render(request, 'productos/categoria.html', {
        'categoria': categoria_actual,
        'productos': resultado['productos'],
        'total': resultado['total'],
        'pagina_actual': resultado['pagina_actual'],
        'total_paginas': resultado['total_paginas'],
        'categorias': categorias
    })

def buscar_productos(request):
    """Vista para buscar productos"""
    query = request.GET.get('q', '')
    pagina = int(request.GET.get('page', 1))
    
    if query:
        # Usar el servicio para buscar productos
        resultado = ProductoService.get_productos(
            filtros={'busqueda': query},
            pagina=pagina
        )
    else:
        resultado = {
            'productos': [],
            'total': 0,
            'pagina_actual': 1,
            'total_paginas': 0
        }
    
    # Obtener categorías para el menú lateral
    categorias = ProductoService.get_categorias()
    
    return render(request, 'productos/busqueda.html', {
        'query': query,
        'productos': resultado['productos'],
        'total': resultado['total'],
        'pagina_actual': resultado['pagina_actual'],
        'total_paginas': resultado['total_paginas'],
        'categorias': categorias
    })

def actualizar_catalogo(request):
    """
    Vista para actualizar manualmente el catálogo desde la API.
    Solo accesible para administradores.
    """
    if not request.user.is_staff:
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('home')
    
    exito, mensaje = ProductoService.actualizar_catalogo_desde_api()
    
    if exito:
        messages.success(request, mensaje)
    else:
        messages.error(request, mensaje)
    
    return redirect('lista_productos')

def is_admin(user):
    return user.is_superuser

# --- DASHBOARD PRINCIPAL (Aquí vive todo ahora) ---
@user_passes_test(is_admin)
def admin_productos(request):
    productos = Producto.objects.all().order_by('-fecha_creacion')
    categorias = Categoria.objects.all() # Necesario para listar categorías si quieres
    
    # Enviamos ambos formularios vacíos para los Modales del Dashboard
    form_producto = ProductoForm()
    form_categoria = CategoriaForm()
    
    return render(request, 'admin_custom/admin_dashboard.html', {
        'productos': productos,
        'categorias': categorias,
        'form_producto': form_producto,
        'form_categoria': form_categoria
    })

# --- CRUD PRODUCTOS ---
@user_passes_test(is_admin)
def producto_crear(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto creado exitosamente.')
    return redirect('admin_productos') # Siempre vuelve al Dashboard

@user_passes_test(is_admin)
def producto_editar(request, id):
    producto = get_object_or_404(Producto, id=id)
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto actualizado exitosamente.')
            return redirect('admin_productos')
    else:
        form = ProductoForm(instance=producto)
    return render(request, 'admin_custom/Crear_Editar_prod.html', {'form': form, 'titulo': 'Editar Producto'})

@user_passes_test(is_admin)
def producto_eliminar(request, id):
    producto = get_object_or_404(Producto, id=id)
    if request.method == 'POST':
        producto.delete()
        messages.success(request, 'Producto eliminado exitosamente.')
        return redirect('admin_productos')
    return render(request, 'admin_custom/Eliminar_prod.html', {'producto': producto})

# --- CRUD CATEGORÍAS ---
@user_passes_test(is_admin)
def categoria_crear(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría creada exitosamente.')
    return redirect('admin_productos') # Vuelve al Dashboard para ver el cambio

@user_passes_test(is_admin)
def categoria_editar(request, id):
    categoria = get_object_or_404(Categoria, id=id)
    if request.method == 'POST':
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría actualizada correctamente.')
            return redirect('admin_productos')
    else:
        form = CategoriaForm(instance=categoria)
    
    # CORRECCIÓN AQUÍ: Cambia Crear_Editar_cat.html por Crear_Editar_prod.html
    return render(request, 'admin_custom/Crear_Editar_prod.html', {
        'form': form, 
        'titulo': 'Editar Categoría'
    })
@user_passes_test(is_admin)
def categoria_eliminar(request, id):
    categoria = get_object_or_404(Categoria, id=id)
    if request.method == 'POST':
        categoria.delete()
        messages.success(request, 'Categoría borrada.')
        return redirect('admin_productos')
    return render(request, 'admin_custom/Eliminar_prod.html', {'categoria': categoria})