from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

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
    path("dolares/", views.dolares, name="dolares"),
    path("dolares/comprar/", views.comprar_dolares, name="comprar_dolares"),
    path("dolares/vender/", views.vender_dolares, name="vender_dolares"),
    path("prestamos/", views.prestamos, name="prestamos"),
    path("prestamos/<int:pk>/pagar-cuota/", views.pagar_cuota, name="pagar_cuota"),
    path("plazos-fijos/", views.plazos_fijos, name="plazos_fijos"),
    path("plazos-fijos/<int:pk>/rescatar/", views.rescatar_plazo_fijo, name="rescatar_plazo_fijo"),
    path("seguros/", views.seguros, name="seguros"),
    path("seguros/<str:tipo>/contratar/", views.contratar_seguro, name="contratar_seguro"),
    path("seguros/<int:pk>/cancelar/", views.cancelar_seguro, name="cancelar_seguro"),
    path("contrasena/cambiar/", views.cambiar_contrasena, name="cambiar_contrasena"),

    # Recuperar contraseña (usuario deslogueado). Usamos las vistas que ya
    # trae Django porque manejan los tokens de forma segura: no tiene
    # sentido reinventar esa parte.
    path(
        "contrasena/recuperar/",
        auth_views.PasswordResetView.as_view(
            template_name="banca/contrasena_recuperar.html",
            email_template_name="banca/email_recuperar_contrasena.txt",
            subject_template_name="banca/email_recuperar_contrasena_asunto.txt",
            success_url=reverse_lazy("banca:contrasena_recuperar_enviado"),
        ),
        name="contrasena_recuperar",
    ),
    path(
        "contrasena/recuperar/enviado/",
        auth_views.PasswordResetDoneView.as_view(template_name="banca/contrasena_recuperar_enviado.html"),
        name="contrasena_recuperar_enviado",
    ),
    path(
        "contrasena/recuperar/confirmar/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="banca/contrasena_recuperar_confirmar.html",
            success_url=reverse_lazy("banca:contrasena_recuperar_listo"),
        ),
        name="contrasena_recuperar_confirmar",
    ),
    path(
        "contrasena/recuperar/listo/",
        auth_views.PasswordResetCompleteView.as_view(template_name="banca/contrasena_recuperar_listo.html"),
        name="contrasena_recuperar_listo",
    ),
]
