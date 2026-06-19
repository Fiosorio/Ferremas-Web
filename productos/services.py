import requests
from django.conf import settings
from .models import Producto, Categoria

class ProductoService:
    """
    Servicio para interactuar con la API de productos o base de datos local.
    """
    
    @staticmethod
    def get_productos(filtros=None, pagina=1, items_por_pagina=12):
        # 1. CORRECCIÓN: Usamos .all() en lugar de .filter(activo=True)
        queryset = Producto.objects.all()
        
        if filtros:
            if 'categoria' in filtros:
                # 2. CORRECCIÓN: Buscamos por el ID de la categoría, no por slug
                queryset = queryset.filter(categoria__id=filtros['categoria'])
            if 'busqueda' in filtros:
                queryset = queryset.filter(nombre__icontains=filtros['busqueda'])
            if 'destacados' in filtros and filtros['destacados']:
                queryset = queryset.filter(destacado=True)
        
        # Ordenar productos
        queryset = queryset.order_by('-destacado', 'nombre')
        
        # Paginación
        total = queryset.count()
        inicio = (pagina - 1) * items_por_pagina
        fin = inicio + items_por_pagina
        productos = queryset[inicio:fin]
        
        return {
            'productos': productos,
            'total': total,
            'pagina_actual': pagina,
            'total_paginas': (total + items_por_pagina - 1) // items_por_pagina
        }
    
    @staticmethod
    def get_producto_por_slug(identificador):
        """
        Obtiene un producto específico (usamos ID porque no hay campo slug).
        """
        try:
            # 3. CORRECCIÓN: Buscamos por 'id' y quitamos 'activo=True'
            return Producto.objects.get(id=identificador)
        except Producto.DoesNotExist:
            return None
    
    @staticmethod
    def get_categorias():
        return Categoria.objects.all()
    
    @staticmethod
    def get_productos_relacionados(producto, limite=4):
        # 4. CORRECCIÓN: Quitamos 'activo=True'
        return Producto.objects.filter(
            categoria=producto.categoria
        ).exclude(id=producto.id)[:limite]
    
    @staticmethod
    def actualizar_catalogo_desde_api():
        """
        Método para actualizar el catálogo local desde la API externa.
        Este método se puede llamar manualmente o programar con Celery/cron.
        """
        # Aquí iría el código para consumir la API externa y actualizar la base de datos local
        # Por ejemplo:
        try:
            # URL de ejemplo, reemplaza con la URL real de tu API
            api_url = getattr(settings, 'API_PRODUCTOS_URL', 'https://api.example.com/productos')
            response = requests.get(api_url)
            
            if response.status_code == 200:
                productos_data = response.json()
                
                # Procesar cada producto de la API
                for producto_data in productos_data:
                    # Buscar o crear la categoría
                    categoria, _ = Categoria.objects.get_or_create(
                        nombre=producto_data['categoria'],
                        defaults={'slug': producto_data['categoria'].lower().replace(' ', '-')}
                    )
                    
                    # Buscar o crear el producto
                    Producto.objects.update_or_create(
                        codigo=producto_data['codigo'],
                        defaults={
                            'nombre': producto_data['nombre'],
                            'slug': producto_data.get('slug', producto_data['nombre'].lower().replace(' ', '-')),
                            'descripcion': producto_data.get('descripcion', ''),
                            'precio': producto_data['precio'],
                            'stock': producto_data.get('stock', 0),
                            'categoria': categoria,
                            'imagen': producto_data.get('imagen', ''),
                            'destacado': producto_data.get('destacado', False),
                            'activo': producto_data.get('activo', True)
                        }
                    )
                
                return True, f"Se actualizaron {len(productos_data)} productos"
            else:
                return False, f"Error al obtener datos de la API: {response.status_code}"
                
        except Exception as e:
            return False, f"Error al actualizar el catálogo: {str(e)}"
