import io
import random
from decimal import Decimal

import qrcode
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (
    ContactoForm,
    LoginForm,
    MontoForm,
    PagoServicioForm,
    PerfilForm,
    RecargaForm,
    RegistroForm,
    RetiroForm,
    SolicitudForm,
    TransferenciaForm,
    VerificacionForm,
    EMPRESAS_SERVICIO,
    OPERADORAS_RECARGA,
)
from .models import (
    Contacto,
    Cuenta,
    Movimiento,
    SolicitudDinero,
    generar_alias,
    generar_cbu,
    generar_numero_cuenta,
    generar_tarjeta,
)


def inicio(request):
    return render(request, "banca/inicio.html")


def seguridad(request):
    return render(request, "banca/seguridad.html")


def registro(request):
    if request.user.is_authenticated:
        return redirect("banca:panel")

    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            numero_tarjeta, vencimiento = generar_tarjeta()
            Cuenta.objects.create(
                usuario=usuario,
                numero_cuenta=generar_numero_cuenta(),
                numero_tarjeta=numero_tarjeta,
                vencimiento_tarjeta=vencimiento,
                alias=generar_alias(),
                cbu=generar_cbu(),
            )
            messages.success(request, "Cuenta creada. Ahora ingresa con tu usuario y contrasena.")
            return redirect("banca:ingresar")
    else:
        form = RegistroForm()

    return render(request, "banca/registro.html", {"form": form})


def ingresar(request):
    if request.user.is_authenticated:
        return redirect("banca:panel")

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            usuario = authenticate(
                request,
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"],
            )
            if usuario is not None:
                request.session["pre_auth_user_id"] = usuario.id
                request.session["pre_auth_codigo"] = f"{random.randint(0, 999999):06d}"
                return redirect("banca:verificar")
            form.add_error(None, "Usuario o contrasena incorrectos.")
    else:
        form = LoginForm()

    return render(request, "banca/login.html", {"form": form})


def verificar(request):
    """
    Segundo paso del login. En un banco real este codigo llegaria por
    SMS o email; aca lo mostramos en pantalla porque es una demo.
    """
    user_id = request.session.get("pre_auth_user_id")
    codigo_esperado = request.session.get("pre_auth_codigo")

    if not user_id or not codigo_esperado:
        return redirect("banca:ingresar")

    if request.method == "POST":
        form = VerificacionForm(request.POST)
        if form.is_valid():
            if form.cleaned_data["codigo"] == codigo_esperado:
                usuario = get_object_or_404(get_user_model(), id=user_id)
                login(request, usuario)
                del request.session["pre_auth_user_id"]
                del request.session["pre_auth_codigo"]
                messages.success(request, f"Bienvenido, {usuario.first_name or usuario.username}.")
                return redirect("banca:panel")
            form.add_error("codigo", "El codigo no coincide.")
    else:
        form = VerificacionForm()

    return render(request, "banca/verificar.html", {"form": form, "codigo_demo": codigo_esperado})


@require_POST
@login_required
def cerrar_sesion(request):
    logout(request)
    messages.info(request, "Cerraste sesion. Hasta la proxima!")
    return redirect("banca:inicio")


@login_required
def panel(request):
    cuenta = get_object_or_404(Cuenta, usuario=request.user)
    cuenta.acreditar_rendimiento()
    return render(request, "banca/panel.html", {
        "cuenta": cuenta,
        "movimientos": cuenta.movimientos.all()[:5],
        "solicitudes_pendientes": cuenta.solicitudes_recibidas.filter(estado=SolicitudDinero.PENDIENTE).count(),
    })


@login_required
def depositar(request):
    cuenta = get_object_or_404(Cuenta, usuario=request.user)

    if request.method == "POST":
        form = MontoForm(request.POST)
        if form.is_valid():
            monto = form.cleaned_data["monto"]
            cuenta.saldo += monto
            cuenta.save()
            mov = Movimiento.objects.create(
                cuenta=cuenta,
                tipo=Movimiento.DEPOSITO,
                monto=monto,
                saldo_posterior=cuenta.saldo,
                descripcion=form.cleaned_data["descripcion"],
            )
            messages.success(request, f"Depositaste ${monto}. Nuevo saldo: ${cuenta.saldo}.")
            return redirect("banca:comprobante", pk=mov.pk)
    else:
        form = MontoForm()

    return render(request, "banca/depositar.html", {"form": form, "cuenta": cuenta})


@login_required
def retirar(request):
    cuenta = get_object_or_404(Cuenta, usuario=request.user)

    if request.method == "POST":
        form = RetiroForm(request.POST, saldo_disponible=cuenta.saldo)
        if form.is_valid():
            monto = form.cleaned_data["monto"]
            cuenta.saldo -= monto
            cuenta.save()
            mov = Movimiento.objects.create(
                cuenta=cuenta,
                tipo=Movimiento.EXTRACCION,
                monto=monto,
                saldo_posterior=cuenta.saldo,
                descripcion=form.cleaned_data["descripcion"],
            )
            messages.success(request, f"Retiraste ${monto}. Nuevo saldo: ${cuenta.saldo}.")
            return redirect("banca:comprobante", pk=mov.pk)
    else:
        form = RetiroForm(saldo_disponible=cuenta.saldo)

    return render(request, "banca/retirar.html", {"form": form, "cuenta": cuenta})


@login_required
def transferir(request):
    cuenta = get_object_or_404(Cuenta, usuario=request.user)

    if request.method == "POST":
        form = TransferenciaForm(request.POST, cuenta_origen=cuenta)
        if form.is_valid():
            monto = form.cleaned_data["monto"]
            descripcion = form.cleaned_data["descripcion"]
            cuenta_destino = form.cleaned_data["destino"]

            with transaction.atomic():
                cuenta.saldo -= monto
                cuenta.save()
                cuenta_destino.saldo += monto
                cuenta_destino.save()
                mov = Movimiento.objects.create(
                    cuenta=cuenta,
                    tipo=Movimiento.TRANSFERENCIA_ENVIADA,
                    monto=monto,
                    saldo_posterior=cuenta.saldo,
                    descripcion=descripcion,
                    contraparte=cuenta_destino.numero_cuenta,
                )
                Movimiento.objects.create(
                    cuenta=cuenta_destino,
                    tipo=Movimiento.TRANSFERENCIA_RECIBIDA,
                    monto=monto,
                    saldo_posterior=cuenta_destino.saldo,
                    descripcion=descripcion,
                    contraparte=cuenta.numero_cuenta,
                )

            messages.success(request, f"Transferiste ${monto} a la cuenta {cuenta_destino.numero_cuenta}.")
            return redirect("banca:comprobante", pk=mov.pk)
    else:
        inicial = {}
        if request.GET.get("destino"):
            inicial["destino"] = request.GET["destino"]
        form = TransferenciaForm(cuenta_origen=cuenta, initial=inicial)

    return render(request, "banca/transferir.html", {"form": form, "cuenta": cuenta})


@login_required
def pagar_servicio(request):
    cuenta = get_object_or_404(Cuenta, usuario=request.user)

    if request.method == "POST":
        form = PagoServicioForm(request.POST, saldo_disponible=cuenta.saldo)
        if form.is_valid():
            monto = form.cleaned_data["monto"]
            empresa = dict(EMPRESAS_SERVICIO)[form.cleaned_data["empresa"]]
            nota = form.cleaned_data["numero_factura"] or form.cleaned_data["descripcion"]
            cuenta.saldo -= monto
            cuenta.save()
            mov = Movimiento.objects.create(
                cuenta=cuenta,
                tipo=Movimiento.PAGO_SERVICIO,
                monto=monto,
                saldo_posterior=cuenta.saldo,
                contraparte=empresa,
                descripcion=nota,
            )
            messages.success(request, f"Pagaste ${monto} a {empresa}.")
            return redirect("banca:comprobante", pk=mov.pk)
    else:
        form = PagoServicioForm(saldo_disponible=cuenta.saldo)

    return render(request, "banca/pagar_servicio.html", {"form": form, "cuenta": cuenta})


@login_required
def recargar_celular(request):
    cuenta = get_object_or_404(Cuenta, usuario=request.user)

    if request.method == "POST":
        form = RecargaForm(request.POST, saldo_disponible=cuenta.saldo)
        if form.is_valid():
            monto = form.cleaned_data["monto"]
            operadora = dict(OPERADORAS_RECARGA)[form.cleaned_data["operadora"]]
            numero = form.cleaned_data["numero_telefono"]
            cuenta.saldo -= monto
            cuenta.save()
            mov = Movimiento.objects.create(
                cuenta=cuenta,
                tipo=Movimiento.RECARGA_CELULAR,
                monto=monto,
                saldo_posterior=cuenta.saldo,
                contraparte=operadora,
                descripcion=f"Recarga a {numero}",
            )
            messages.success(request, f"Recargaste ${monto} en {operadora}.")
            return redirect("banca:comprobante", pk=mov.pk)
    else:
        form = RecargaForm(saldo_disponible=cuenta.saldo)

    return render(request, "banca/recargar.html", {"form": form, "cuenta": cuenta})


@login_required
def movimientos(request):
    cuenta = get_object_or_404(Cuenta, usuario=request.user)
    return render(request, "banca/movimientos.html", {
        "cuenta": cuenta,
        "movimientos": cuenta.movimientos.all(),
    })


@login_required
def comprobante(request, pk):
    cuenta = get_object_or_404(Cuenta, usuario=request.user)
    mov = get_object_or_404(Movimiento, pk=pk, cuenta=cuenta)
    return render(request, "banca/comprobante.html", {"cuenta": cuenta, "mov": mov})


@login_required
def resumen(request):
    cuenta = get_object_or_404(Cuenta, usuario=request.user)
    cuenta.acreditar_rendimiento()

    etiquetas = dict(Movimiento.TIPO_CHOICES)
    totales = cuenta.movimientos.values("tipo").annotate(total=Sum("monto"))
    totales_por_tipo = {fila["tipo"]: fila["total"] for fila in totales}

    barras_data = sorted(
        ((etiquetas[tipo], monto) for tipo, monto in totales_por_tipo.items() if monto),
        key=lambda item: item[1],
        reverse=True,
    )
    maximo = barras_data[0][1] if barras_data else 1
    barras = [
        {"etiqueta": etiqueta, "monto": monto, "porcentaje": int((monto / maximo) * 100)}
        for etiqueta, monto in barras_data
    ]

    total_ingresos = sum(
        (monto for tipo, monto in totales_por_tipo.items() if tipo in Movimiento.TIPOS_INGRESO),
        start=Decimal("0"),
    )
    total_egresos = sum(
        (monto for tipo, monto in totales_por_tipo.items() if tipo not in Movimiento.TIPOS_INGRESO),
        start=Decimal("0"),
    )

    return render(request, "banca/resumen.html", {
        "cuenta": cuenta,
        "barras": barras,
        "total_ingresos": total_ingresos,
        "total_egresos": total_egresos,
    })


@login_required
def qr_cobrar(request):
    cuenta = get_object_or_404(Cuenta, usuario=request.user)
    monto = request.GET.get("monto", "").strip()
    return render(request, "banca/qr.html", {"cuenta": cuenta, "monto": monto})


@login_required
def qr_imagen(request):
    cuenta = get_object_or_404(Cuenta, usuario=request.user)
    monto = request.GET.get("monto", "").strip()

    contenido = f"tesorodigital://pagar?alias={cuenta.alias}"
    if monto:
        contenido += f"&monto={monto}"

    imagen = qrcode.make(contenido)
    buffer = io.BytesIO()
    imagen.save(buffer, format="PNG")
    return HttpResponse(buffer.getvalue(), content_type="image/png")


@login_required
def contactos(request):
    cuenta = get_object_or_404(Cuenta, usuario=request.user)

    if request.method == "POST":
        form = ContactoForm(request.POST, cuenta_propia=cuenta)
        if form.is_valid():
            cuenta_destino = form.cleaned_data["destino"]
            _, creado = Contacto.objects.get_or_create(
                usuario=request.user,
                cuenta_guardada=cuenta_destino,
                defaults={"apodo": form.cleaned_data["apodo"]},
            )
            messages.success(request, "Contacto agregado." if creado else "Ese contacto ya estaba guardado.")
            return redirect("banca:contactos")
    else:
        form = ContactoForm(cuenta_propia=cuenta)

    return render(request, "banca/contactos.html", {
        "form": form,
        "contactos": request.user.contactos.select_related("cuenta_guardada"),
    })


@login_required
@require_POST
def eliminar_contacto(request, pk):
    contacto = get_object_or_404(Contacto, pk=pk, usuario=request.user)
    contacto.delete()
    messages.info(request, "Contacto eliminado.")
    return redirect("banca:contactos")


@login_required
def solicitar_dinero(request):
    cuenta = get_object_or_404(Cuenta, usuario=request.user)

    if request.method == "POST":
        form = SolicitudForm(request.POST, cuenta_propia=cuenta)
        if form.is_valid():
            SolicitudDinero.objects.create(
                solicitante=cuenta,
                destinatario=form.cleaned_data["destino"],
                monto=form.cleaned_data["monto"],
                descripcion=form.cleaned_data["descripcion"],
            )
            messages.success(request, "Solicitud enviada.")
            return redirect("banca:solicitudes")
    else:
        form = SolicitudForm(cuenta_propia=cuenta)

    return render(request, "banca/solicitar.html", {"form": form, "cuenta": cuenta})


@login_required
def solicitudes(request):
    cuenta = get_object_or_404(Cuenta, usuario=request.user)
    return render(request, "banca/solicitudes.html", {
        "cuenta": cuenta,
        "recibidas": cuenta.solicitudes_recibidas.filter(estado=SolicitudDinero.PENDIENTE),
        "enviadas": cuenta.solicitudes_hechas.all(),
    })


@login_required
@require_POST
def pagar_solicitud(request, pk):
    cuenta = get_object_or_404(Cuenta, usuario=request.user)
    solicitud = get_object_or_404(
        SolicitudDinero, pk=pk, destinatario=cuenta, estado=SolicitudDinero.PENDIENTE
    )

    if solicitud.monto > cuenta.saldo:
        messages.error(request, "No tenes saldo suficiente para pagar esta solicitud.")
        return redirect("banca:solicitudes")

    cuenta_solicitante = solicitud.solicitante

    with transaction.atomic():
        cuenta.saldo -= solicitud.monto
        cuenta.save()
        cuenta_solicitante.saldo += solicitud.monto
        cuenta_solicitante.save()
        mov = Movimiento.objects.create(
            cuenta=cuenta,
            tipo=Movimiento.TRANSFERENCIA_ENVIADA,
            monto=solicitud.monto,
            saldo_posterior=cuenta.saldo,
            descripcion=solicitud.descripcion or "Pago de solicitud",
            contraparte=cuenta_solicitante.numero_cuenta,
        )
        Movimiento.objects.create(
            cuenta=cuenta_solicitante,
            tipo=Movimiento.TRANSFERENCIA_RECIBIDA,
            monto=solicitud.monto,
            saldo_posterior=cuenta_solicitante.saldo,
            descripcion=solicitud.descripcion or "Pago de solicitud",
            contraparte=cuenta.numero_cuenta,
        )
        solicitud.estado = SolicitudDinero.PAGADA
        solicitud.resuelta = timezone.now()
        solicitud.save()

    messages.success(request, f"Pagaste ${solicitud.monto} a {cuenta_solicitante.alias}.")
    return redirect("banca:comprobante", pk=mov.pk)


@login_required
@require_POST
def cancelar_solicitud(request, pk):
    cuenta = get_object_or_404(Cuenta, usuario=request.user)
    solicitud = get_object_or_404(SolicitudDinero, pk=pk, estado=SolicitudDinero.PENDIENTE)

    if cuenta.pk not in (solicitud.solicitante_id, solicitud.destinatario_id):
        messages.error(request, "No podes modificar esa solicitud.")
        return redirect("banca:solicitudes")

    solicitud.estado = SolicitudDinero.CANCELADA
    solicitud.resuelta = timezone.now()
    solicitud.save()
    messages.info(request, "Solicitud cancelada.")
    return redirect("banca:solicitudes")


@login_required
@require_POST
def alternar_bloqueo_tarjeta(request):
    cuenta = get_object_or_404(Cuenta, usuario=request.user)
    cuenta.tarjeta_bloqueada = not cuenta.tarjeta_bloqueada
    cuenta.save()
    if cuenta.tarjeta_bloqueada:
        messages.info(request, "Bloqueaste tu tarjeta. La podes reactivar cuando quieras.")
    else:
        messages.success(request, "Reactivaste tu tarjeta.")
    return redirect("banca:panel")


@login_required
def perfil(request):
    cuenta = get_object_or_404(Cuenta, usuario=request.user)

    if request.method == "POST":
        form = PerfilForm(request.POST, request.FILES, instance=cuenta)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil actualizado.")
            return redirect("banca:perfil")
    else:
        form = PerfilForm(instance=cuenta)

    return render(request, "banca/perfil.html", {"form": form, "cuenta": cuenta})
