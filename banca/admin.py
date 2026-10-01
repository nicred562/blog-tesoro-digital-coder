from django.contrib import admin

from .models import Contacto, Cuenta, Movimiento, PlazoFijo, Prestamo, Seguro, SolicitudDinero

admin.site.register(Cuenta)
admin.site.register(Movimiento)
admin.site.register(Contacto)
admin.site.register(SolicitudDinero)
admin.site.register(Prestamo)
admin.site.register(PlazoFijo)
admin.site.register(Seguro)
