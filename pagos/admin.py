from django.contrib import admin
from .models import Orden, Transaccion

admin.site.register(Orden)
admin.site.register(Transaccion)