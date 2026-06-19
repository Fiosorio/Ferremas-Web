from rest_framework import serializers
from .models import Orden, Transaccion
from carrito.serializers import CarritoSerializer

class TransaccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaccion
        fields = ['id', 'token', 'monto', 'fecha', 'estado', 'codigo_autorizacion']

class OrdenSerializer(serializers.ModelSerializer):
    carrito_detalle = CarritoSerializer(source='carrito', read_only=True)
    transacciones = TransaccionSerializer(many=True, read_only=True, source='transaccion_set')
    
    class Meta:
        model = Orden
        fields = ['id', 'usuario', 'carrito', 'carrito_detalle', 'fecha_creacion', 
                  'estado', 'direccion_envio', 'total', 'transacciones']
