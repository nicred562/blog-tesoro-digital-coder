from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import (
    Cuenta,
    PlazoFijo,
    Prestamo,
    Seguro,
    TASA_INTERES_PRESTAMO,
    generar_alias,
    generar_cbu,
    generar_numero_cuenta,
    generar_tarjeta,
    obtener_o_crear_cuenta,
)


def _dv_independiente(digitos, pesos):
    # Reimplementado aca aparte (no reutiliza banca.models) para que la
    # verificacion sea independiente de como esta escrito el generador.
    total = sum(int(digito) * peso for digito, peso in zip(digitos, pesos))
    resto = total % 10
    return 0 if resto == 0 else 10 - resto


def cbu_es_valido(cbu):
    bloque1, bloque2 = cbu[:8], cbu[8:]
    dv1_ok = _dv_independiente(bloque1[:7], [7, 1, 3, 9, 7, 1, 3]) == int(bloque1[7])
    dv2_ok = _dv_independiente(bloque2[:13], [3, 9, 7, 1, 3, 9, 7, 1, 3, 9, 7, 1, 3]) == int(bloque2[13])
    return len(cbu) == 22 and dv1_ok and dv2_ok


def crear_cuenta(username, saldo=Decimal("0")):
    usuario = User.objects.create_user(username=username, password="ContraseñaSegura123")
    numero_tarjeta, vencimiento = generar_tarjeta()
    return Cuenta.objects.create(
        usuario=usuario,
        numero_cuenta=generar_numero_cuenta(),
        numero_tarjeta=numero_tarjeta,
        vencimiento_tarjeta=vencimiento,
        alias=generar_alias(),
        cbu=generar_cbu(),
        saldo=saldo,
    )


class GeneradorCBUTests(TestCase):
    def test_el_cbu_generado_pasa_su_propio_digito_verificador(self):
        for _ in range(20):
            self.assertTrue(cbu_es_valido(generar_cbu()))


class RegistroYLoginTests(TestCase):
    def test_registro_crea_cuenta_con_alias_y_cbu(self):
        self.client.post(reverse("banca:registro"), {
            "first_name": "Nico", "username": "nuevo", "email": "nuevo@tesorodigital.com",
            "password1": "ContraseñaSegura123", "password2": "ContraseñaSegura123",
        })
        usuario = User.objects.get(username="nuevo")
        cuenta = Cuenta.objects.get(usuario=usuario)
        self.assertEqual(cuenta.alias.count("."), 2)
        self.assertTrue(cbu_es_valido(cuenta.cbu))

    def test_login_pide_verificacion_en_dos_pasos(self):
        crear_cuenta("autor")
        response = self.client.post(reverse("banca:ingresar"), {
            "username": "autor", "password": "ContraseñaSegura123",
        })
        self.assertRedirects(response, reverse("banca:verificar"))
        self.assertIn("pre_auth_codigo", self.client.session)

    def test_codigo_incorrecto_no_autentica(self):
        crear_cuenta("autor")
        self.client.post(reverse("banca:ingresar"), {"username": "autor", "password": "ContraseñaSegura123"})
        self.client.post(reverse("banca:verificar"), {"codigo": "000000"})
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_codigo_correcto_autentica(self):
        crear_cuenta("autor")
        self.client.post(reverse("banca:ingresar"), {"username": "autor", "password": "ContraseñaSegura123"})
        codigo = self.client.session.get("pre_auth_codigo")
        self.client.post(reverse("banca:verificar"), {"codigo": codigo})
        self.assertIn("_auth_user_id", self.client.session)


class CuentaSinRegistroTests(TestCase):
    """Reproduce el bug de un User sin Cuenta (ej. un superusuario) y confirma el arreglo."""

    def test_un_usuario_sin_cuenta_no_rompe_el_panel(self):
        admin = User.objects.create_superuser(username="admin", password="ContraseñaSegura123", email="a@a.com")
        self.assertFalse(Cuenta.objects.filter(usuario=admin).exists())

        self.client.force_login(admin)
        response = self.client.get(reverse("banca:panel"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Cuenta.objects.filter(usuario=admin).exists())

    def test_obtener_o_crear_cuenta_es_idempotente(self):
        usuario = User.objects.create_user(username="sin_cuenta", password="x")
        cuenta1 = obtener_o_crear_cuenta(usuario)
        cuenta2 = obtener_o_crear_cuenta(usuario)
        self.assertEqual(cuenta1.pk, cuenta2.pk)


class OperacionesBasicasTests(TestCase):
    def setUp(self):
        self.cuenta = crear_cuenta("operador", saldo=Decimal("1000.00"))
        self.client.force_login(self.cuenta.usuario)

    def test_depositar_acredita_saldo(self):
        self.client.post(reverse("banca:depositar"), {"monto": "500.00", "descripcion": ""})
        self.cuenta.refresh_from_db()
        self.assertEqual(self.cuenta.saldo, Decimal("1500.00"))

    def test_no_se_puede_retirar_mas_del_saldo_disponible(self):
        response = self.client.post(reverse("banca:retirar"), {"monto": "999999", "descripcion": ""})
        self.assertContains(response, "No tenes saldo suficiente")
        self.cuenta.refresh_from_db()
        self.assertEqual(self.cuenta.saldo, Decimal("1000.00"))

    def test_transferir_por_alias_mueve_la_plata_entre_cuentas(self):
        destino = crear_cuenta("destino")
        self.client.post(reverse("banca:transferir"), {
            "destino": destino.alias, "monto": "200.00", "descripcion": "",
        })
        self.cuenta.refresh_from_db()
        destino.refresh_from_db()
        self.assertEqual(self.cuenta.saldo, Decimal("800.00"))
        self.assertEqual(destino.saldo, Decimal("200.00"))

    def test_no_se_puede_transferir_a_la_propia_cuenta(self):
        response = self.client.post(reverse("banca:transferir"), {
            "destino": self.cuenta.numero_cuenta, "monto": "10", "descripcion": "",
        })
        self.assertContains(response, "No podes usar tu propia cuenta")


class DolaresTests(TestCase):
    def setUp(self):
        self.cuenta = crear_cuenta("cambista", saldo=Decimal("500000.00"))
        self.client.force_login(self.cuenta.usuario)

    def test_comprar_y_vender_dolares(self):
        self.client.post(reverse("banca:comprar_dolares"), {"monto_usd": "100"})
        self.cuenta.refresh_from_db()
        self.assertEqual(self.cuenta.saldo_usd, Decimal("100.00"))

        self.client.post(reverse("banca:vender_dolares"), {"monto_usd": "40"})
        self.cuenta.refresh_from_db()
        self.assertEqual(self.cuenta.saldo_usd, Decimal("60.00"))

    def test_no_se_puede_vender_mas_dolares_de_los_que_hay(self):
        response = self.client.post(reverse("banca:vender_dolares"), {"monto_usd": "999"})
        self.assertContains(response, "No tenes esa cantidad")


class PrestamosTests(TestCase):
    def setUp(self):
        # Saldo inicial con margen extra: el prestamo acredita el monto
        # pedido, pero las cuotas incluyen interes, asi que hace falta
        # algo mas que lo prestado para poder pagarlo todo.
        self.cuenta = crear_cuenta("deudor", saldo=Decimal("20000.00"))
        self.client.force_login(self.cuenta.usuario)

    def test_el_prestamo_acredita_el_monto_y_calcula_la_cuota_con_interes(self):
        saldo_antes = self.cuenta.saldo
        self.client.post(reverse("banca:prestamos"), {"monto_solicitado": "100000", "cantidad_cuotas": "3"})
        self.cuenta.refresh_from_db()
        self.assertEqual(self.cuenta.saldo, saldo_antes + Decimal("100000.00"))

        prestamo = Prestamo.objects.get(cuenta=self.cuenta)
        esperado = (Decimal("100000.00") * (1 + TASA_INTERES_PRESTAMO) / 3).quantize(Decimal("0.01"))
        self.assertEqual(prestamo.monto_cuota, esperado)

    def test_pagar_todas_las_cuotas_marca_el_prestamo_como_pagado(self):
        self.client.post(reverse("banca:prestamos"), {"monto_solicitado": "90000", "cantidad_cuotas": "3"})
        prestamo = Prestamo.objects.get(cuenta=self.cuenta)

        for _ in range(3):
            self.client.post(reverse("banca:pagar_cuota", args=[prestamo.pk]))

        prestamo.refresh_from_db()
        self.assertEqual(prestamo.estado, Prestamo.PAGADO)


class PlazoFijoTests(TestCase):
    def setUp(self):
        self.cuenta = crear_cuenta("ahorrista", saldo=Decimal("100000.00"))
        self.client.force_login(self.cuenta.usuario)

    def test_no_se_puede_rescatar_antes_del_vencimiento(self):
        self.client.post(reverse("banca:plazos_fijos"), {"monto": "50000", "dias": "30"})
        plazo = PlazoFijo.objects.get(cuenta=self.cuenta)

        self.client.post(reverse("banca:rescatar_plazo_fijo", args=[plazo.pk]))
        plazo.refresh_from_db()
        self.assertEqual(plazo.estado, PlazoFijo.ACTIVO)

    def test_rescatar_un_plazo_vencido_acredita_con_ganancia(self):
        self.client.post(reverse("banca:plazos_fijos"), {"monto": "50000", "dias": "30"})
        plazo = PlazoFijo.objects.get(cuenta=self.cuenta)
        plazo.fecha_vencimiento = timezone.localdate() - timedelta(days=1)
        plazo.save()

        saldo_antes = Cuenta.objects.get(pk=self.cuenta.pk).saldo
        self.client.post(reverse("banca:rescatar_plazo_fijo", args=[plazo.pk]))

        self.cuenta.refresh_from_db()
        plazo.refresh_from_db()
        self.assertEqual(plazo.estado, PlazoFijo.RESCATADO)
        self.assertEqual(self.cuenta.saldo, saldo_antes + plazo.monto_final)
        self.assertGreater(plazo.monto_final, plazo.monto)


class SegurosTests(TestCase):
    def setUp(self):
        self.cuenta = crear_cuenta("asegurado", saldo=Decimal("10000.00"))
        self.client.force_login(self.cuenta.usuario)

    def test_contratar_un_seguro_descuenta_el_primer_mes(self):
        self.client.post(reverse("banca:contratar_seguro", args=["celular"]))
        seguro = Seguro.objects.get(cuenta=self.cuenta, tipo="celular")
        self.cuenta.refresh_from_db()
        self.assertEqual(self.cuenta.saldo, Decimal("10000.00") - seguro.costo_mensual)

    def test_no_se_puede_contratar_el_mismo_seguro_dos_veces(self):
        self.client.post(reverse("banca:contratar_seguro", args=["celular"]))
        self.client.post(reverse("banca:contratar_seguro", args=["celular"]))
        self.assertEqual(
            Seguro.objects.filter(cuenta=self.cuenta, tipo="celular", activo=True).count(), 1
        )


class TarjetaTests(TestCase):
    def setUp(self):
        self.cuenta = crear_cuenta("titular")
        self.client.force_login(self.cuenta.usuario)

    def test_bloquear_y_reactivar_la_tarjeta(self):
        self.client.post(reverse("banca:alternar_bloqueo_tarjeta"))
        self.cuenta.refresh_from_db()
        self.assertTrue(self.cuenta.tarjeta_bloqueada)

        self.client.post(reverse("banca:alternar_bloqueo_tarjeta"))
        self.cuenta.refresh_from_db()
        self.assertFalse(self.cuenta.tarjeta_bloqueada)

    def test_bloquear_la_tarjeta_con_get_no_esta_permitido(self):
        response = self.client.get(reverse("banca:alternar_bloqueo_tarjeta"))
        self.assertEqual(response.status_code, 405)
