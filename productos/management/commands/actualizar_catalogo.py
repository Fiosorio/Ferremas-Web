from django.core.management.base import BaseCommand
from productos.models import Producto, Categoria
from productos.services import ProductoService
import json

class Command(BaseCommand):
    help = 'Actualiza el catálogo desde API o desde un archivo JSON local'

    def add_arguments(self, parser):
        parser.add_argument('--archivo', type=str, help='Ruta a un archivo JSON local')

    def handle(self, *args, **options):
        archivo = options['archivo']
        
        if archivo:
            self.stdout.write(f"Leyendo datos desde: {archivo}")
            with open(archivo, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for item in data:
                # 1. Buscamos o creamos la categoría
                cat, _ = Categoria.objects.get_or_create(nombre=item['categoria'])
                
                # 2. Creamos o actualizamos el producto usando 'nombre' como identificador
                # Nota: 'descripcion' es obligatorio en tu modelo, así que lo incluimos
                producto, created = Producto.objects.update_or_create(
                    nombre=item['nombre'],
                    defaults={
                        'descripcion': item.get('descripcion', 'Sin descripción'),
                        'precio': item['precio'],
                        'stock': item.get('stock', 0),
                        'categoria': cat,
                        'imagen': item.get('imagen', ''),
                        'destacado': item.get('destacado', False)
                    }
                )
                self.stdout.write(f"Procesado: {item['nombre']} - {'Creado' if created else 'Actualizado'}")
            
            self.stdout.write(self.style.SUCCESS('Carga local finalizada y guardada en base de datos'))
            
        else:
            # --- MODO API (Tu lógica original) ---
            self.stdout.write('Iniciando actualización desde API externa...')
            exito, mensaje = ProductoService.actualizar_catalogo_desde_api()
            if exito:
                self.stdout.write(self.style.SUCCESS(f'Éxito: {mensaje}'))
            else:
                self.stdout.write(self.style.ERROR(f'Error: {mensaje}'))