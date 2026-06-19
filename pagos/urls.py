from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'ordenes', views.OrdenViewSet, basename='orden')

urlpatterns = [
    path('api/', include(router.urls)),
    path('checkout/', views.checkout, name='checkout'),
    path('retorno/', views.pago_retorno, name='pago_retorno'),
    path('historial/', views.historial_ordenes, name='historial_ordenes'),
    path('orden/<int:orden_id>/', views.detalle_orden, name='detalle_orden'),
]

