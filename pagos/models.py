from django.db import models
from usuarios.models import Usuario
from carrito.models import Carrito

class Orden(models.Model):
    ESTADO_CHOICES = (
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
        ('enviado', 'Enviado'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
    )
    
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    carrito = models.OneToOneField(Carrito, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    direccion_envio = models.TextField()
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"Orden #{self.id} - {self.usuario.username}"

class Transaccion(models.Model):
    orden = models.ForeignKey(Orden, on_delete=models.CASCADE)
    token = models.CharField(max_length=100)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=50)
    codigo_autorizacion = models.CharField(max_length=50, blank=True, null=True)
    
    def __str__(self):
        return f"Transacción {self.id} - Orden #{self.orden.id}"
