# config_sys/context_processors.py

def cart_count_processor(request):
    total_items = 0
    if request.user.is_authenticated: # Opcional: si quieres lógica por usuario
        carrito = request.session.get('carrito', {})
        for item in carrito.values():
            total_items += item.get('cantidad', 0)
    else:
        # Lógica para usuarios anónimos
        carrito = request.session.get('carrito', {})
        for item in carrito.values():
            total_items += item.get('cantidad', 0)
            
    return {'cart_count': total_items}