from django.urls import path

from . import views

app_name = "banca"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("seguridad/", views.seguridad, name="seguridad"),
    path("registro/", views.registro, name="registro"),
    path("ingresar/", views.ingresar, name="ingresar"),
    path("verificar/", views.verificar, name="verificar"),
    path("salir/", views.cerrar_sesion, name="salir"),
    path("panel/", views.panel, name="panel"),
    path("perfil/", views.perfil, name="perfil"),
    path("depositar/", views.depositar, name="depositar"),
    path("retirar/", views.retirar, name="retirar"),
    path("transferir/", views.transferir, name="transferir"),
    path("pagar-servicio/", views.pagar_servicio, name="pagar_servicio"),
    path("recargar/", views.recargar_celular, name="recargar_celular"),
    path("movimientos/", views.movimientos, name="movimientos"),
    path("movimientos/<int:pk>/", views.comprobante, name="comprobante"),
    path("resumen/", views.resumen, name="resumen"),
    path("qr/", views.qr_cobrar, name="qr_cobrar"),
    path("qr/imagen/", views.qr_imagen, name="qr_imagen"),
    path("contactos/", views.contactos, name="contactos"),
    path("contactos/<int:pk>/eliminar/", views.eliminar_contacto, name="eliminar_contacto"),
    path("solicitar/", views.solicitar_dinero, name="solicitar_dinero"),
    path("solicitudes/", views.solicitudes, name="solicitudes"),
    path("solicitudes/<int:pk>/pagar/", views.pagar_solicitud, name="pagar_solicitud"),
    path("solicitudes/<int:pk>/cancelar/", views.cancelar_solicitud, name="cancelar_solicitud"),
    path("tarjeta/bloqueo/", views.alternar_bloqueo_tarjeta, name="alternar_bloqueo_tarjeta"),
]
