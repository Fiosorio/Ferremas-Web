from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_productos, name='lista_productos'),
    path('buscar/', views.buscar_productos, name='buscar_productos'),
    path('categoria/<slug:slug>/', views.productos_por_categoria, name='productos_por_categoria'),
    path('actualizar-catalogo/', views.actualizar_catalogo, name='actualizar_catalogo'),
    path('<slug:slug>/', views.detalle_producto, name='detalle_producto'),
    path('admin/lista/', views.admin_productos, name='admin_productos'),
    path('admin/crear/', views.producto_crear, name='producto_crear'),
    path('admin/editar/<int:id>/', views.producto_editar, name='producto_editar'),
    path('admin/eliminar/<int:id>/', views.producto_eliminar, name='producto_eliminar'),
    path('admin/categorias/crear/', views.categoria_crear, name='categoria_crear'),
    path('admin/categorias/editar/<int:id>/', views.categoria_editar, name='categoria_editar'),
    path('admin/categorias/eliminar/<int:id>/', views.categoria_eliminar, name='categoria_eliminar'),
]

