import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone

validador_alias = RegexValidator(
    regex=r"^[a-z0-9]+(\.[a-z0-9]+){2}$",
    message="El alias va en minusculas y con el formato palabra.palabra.palabra.",
)

# Rendimiento diario ficticio que gana la plata parada en la cuenta.
TASA_RENDIMIENTO_DIARIA = Decimal("0.0008")

# Cotizacion de ejemplo del dolar (fija, no representa un valor de mercado real).
TASA_DOLAR = Decimal("1000.00")

# Interes fijo que se le suma a cualquier prestamo, sea cual sea el plazo.
TASA_INTERES_PRESTAMO = Decimal("0.15")

# Tasas anuales de ejemplo para los plazos fijos, segun los dias elegidos.
TASAS_PLAZO_FIJO = {
    30: Decimal("0.30"),
    60: Decimal("0.33"),
    90: Decimal("0.36"),
    180: Decimal("0.40"),
    365: Decimal("0.45"),
}

CATALOGO_SEGUROS = {
    "celular": {"nombre": "Seguro de celular", "costo_mensual": Decimal("1500.00"), "icono": "📱"},
    "hogar": {"nombre": "Seguro de hogar", "costo_mensual": Decimal("3500.00"), "icono": "🏠"},
    "vida": {"nombre": "Seguro de vida", "costo_mensual": Decimal("2200.00"), "icono": "❤️"},
}


class Cuenta(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name="cuenta")
    numero_cuenta = models.CharField(max_length=20, unique=True)
    cbu = models.CharField(max_length=22, unique=True, blank=True)
    alias = models.CharField(max_length=40, unique=True, blank=True, validators=[validador_alias])
    saldo = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    numero_tarjeta = models.CharField(max_length=16, blank=True)
    vencimiento_tarjeta = models.CharField(max_length=5, blank=True)
    tarjeta_bloqueada = models.BooleanField(default=False)
    foto = models.ImageField(upload_to="perfiles/", blank=True, null=True)
    ultimo_rendimiento = models.DateField(null=True, blank=True)
    saldo_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    es_comercio = models.BooleanField(default=False)
    nombre_comercio = models.CharField(max_length=100, blank=True)
    creada = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        nombre = self.usuario.get_full_name() or self.usuario.username
        return f"Cuenta {self.numero_cuenta} de {nombre}"

    @property
    def tarjeta_enmascarada(self):
        if not self.numero_tarjeta:
            return ""
        return f"•••• •••• •••• {self.numero_tarjeta[-4:]}"

    @property
    def numero_tarjeta_formateado(self):
        if not self.numero_tarjeta:
            return ""
        return " ".join(self.numero_tarjeta[i:i + 4] for i in range(0, 16, 4))

    def acreditar_rendimiento(self):
        """
        Calcula el rendimiento diario sobre el saldo y lo acredita, como si
        fuera "tu dinero rinde" de una billetera real. Se llama cada vez que
        se abre el panel: no hace falta un cron, se pone al dia solo.
        """
        hoy = timezone.localdate()
        ultimo = self.ultimo_rendimiento or self.creada.date()
        dias = (hoy - ultimo).days

        if dias <= 0:
            return

        ganancia = (self.saldo * TASA_RENDIMIENTO_DIARIA * dias).quantize(Decimal("0.01"))
        self.ultimo_rendimiento = hoy

        if ganancia <= 0:
            self.save(update_fields=["ultimo_rendimiento"])
            return

        self.saldo += ganancia
        self.save()
        Movimiento.objects.create(
            cuenta=self,
            tipo=Movimiento.RENDIMIENTO,
            monto=ganancia,
            saldo_posterior=self.saldo,
            descripcion="Rendimiento diario",
        )


class Movimiento(models.Model):
    DEPOSITO = "deposito"
    EXTRACCION = "extraccion"
    TRANSFERENCIA_ENVIADA = "transferencia_enviada"
    TRANSFERENCIA_RECIBIDA = "transferencia_recibida"
    PAGO_SERVICIO = "pago_servicio"
    RECARGA_CELULAR = "recarga_celular"
    RENDIMIENTO = "rendimiento"
    COMPRA_USD = "compra_usd"
    VENTA_USD = "venta_usd"
    PRESTAMO_ACREDITADO = "prestamo_acreditado"
    PAGO_CUOTA_PRESTAMO = "pago_cuota_prestamo"
    PLAZO_FIJO_CREADO = "plazo_fijo_creado"
    PLAZO_FIJO_RESCATADO = "plazo_fijo_rescatado"
    SEGURO_CONTRATADO = "seguro_contratado"
    TIPO_CHOICES = [
        (DEPOSITO, "Depósito"),
        (EXTRACCION, "Extracción"),
        (TRANSFERENCIA_ENVIADA, "Transferencia enviada"),
        (TRANSFERENCIA_RECIBIDA, "Transferencia recibida"),
        (PAGO_SERVICIO, "Pago de servicio"),
        (RECARGA_CELULAR, "Recarga de celular"),
        (RENDIMIENTO, "Rendimiento"),
        (COMPRA_USD, "Compra de dólares"),
        (VENTA_USD, "Venta de dólares"),
        (PRESTAMO_ACREDITADO, "Préstamo acreditado"),
        (PAGO_CUOTA_PRESTAMO, "Pago de cuota de préstamo"),
        (PLAZO_FIJO_CREADO, "Plazo fijo"),
        (PLAZO_FIJO_RESCATADO, "Rescate de plazo fijo"),
        (SEGURO_CONTRATADO, "Seguro contratado"),
    ]
    TIPOS_INGRESO = (DEPOSITO, TRANSFERENCIA_RECIBIDA, RENDIMIENTO, VENTA_USD, PRESTAMO_ACREDITADO, PLAZO_FIJO_RESCATADO)

    cuenta = models.ForeignKey(Cuenta, on_delete=models.CASCADE, related_name="movimientos")
    tipo = models.CharField(max_length=24, choices=TIPO_CHOICES)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    saldo_posterior = models.DecimalField(max_digits=12, decimal_places=2)
    descripcion = models.CharField(max_length=140, blank=True)
    contraparte = models.CharField(max_length=40, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.get_tipo_display()} de ${self.monto} en {self.cuenta.numero_cuenta}"

    @property
    def es_ingreso(self):
        return self.tipo in self.TIPOS_INGRESO

    @property
    def detalle_contraparte(self):
        if not self.contraparte:
            return ""
        if self.tipo == self.TRANSFERENCIA_ENVIADA:
            return f"a {self.contraparte}"
        if self.tipo == self.TRANSFERENCIA_RECIBIDA:
            return f"de {self.contraparte}"
        return self.contraparte


class Contacto(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name="contactos")
    cuenta_guardada = models.ForeignKey(Cuenta, on_delete=models.CASCADE, related_name="guardado_por")
    apodo = models.CharField(max_length=40, blank=True)
    agregado = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("usuario", "cuenta_guardada")
        ordering = ["apodo", "id"]

    def __str__(self):
        return self.apodo or self.cuenta_guardada.alias

    @property
    def nombre_mostrado(self):
        return self.apodo or self.cuenta_guardada.alias


class SolicitudDinero(models.Model):
    PENDIENTE = "pendiente"
    PAGADA = "pagada"
    CANCELADA = "cancelada"
    ESTADO_CHOICES = [
        (PENDIENTE, "Pendiente"),
        (PAGADA, "Pagada"),
        (CANCELADA, "Cancelada"),
    ]

    solicitante = models.ForeignKey(Cuenta, on_delete=models.CASCADE, related_name="solicitudes_hechas")
    destinatario = models.ForeignKey(Cuenta, on_delete=models.CASCADE, related_name="solicitudes_recibidas")
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    descripcion = models.CharField(max_length=140, blank=True)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default=PENDIENTE)
    creada = models.DateTimeField(auto_now_add=True)
    resuelta = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-creada"]

    def __str__(self):
        return f"{self.solicitante.alias} le pide ${self.monto} a {self.destinatario.alias}"


class Prestamo(models.Model):
    ACTIVO = "activo"
    PAGADO = "pagado"
    ESTADO_CHOICES = [
        (ACTIVO, "Activo"),
        (PAGADO, "Pagado"),
    ]

    cuenta = models.ForeignKey(Cuenta, on_delete=models.CASCADE, related_name="prestamos")
    monto_solicitado = models.DecimalField(max_digits=12, decimal_places=2)
    tasa_interes = models.DecimalField(max_digits=4, decimal_places=2, default=TASA_INTERES_PRESTAMO)
    cantidad_cuotas = models.PositiveSmallIntegerField()
    monto_cuota = models.DecimalField(max_digits=12, decimal_places=2)
    cuotas_pagadas = models.PositiveSmallIntegerField(default=0)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default=ACTIVO)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado"]

    def __str__(self):
        return f"Préstamo de ${self.monto_solicitado} para {self.cuenta.numero_cuenta}"

    @property
    def monto_total_a_pagar(self):
        return self.monto_cuota * self.cantidad_cuotas

    @property
    def cuotas_restantes(self):
        return self.cantidad_cuotas - self.cuotas_pagadas

    @property
    def saldo_pendiente(self):
        return self.monto_cuota * self.cuotas_restantes


class PlazoFijo(models.Model):
    ACTIVO = "activo"
    RESCATADO = "rescatado"
    ESTADO_CHOICES = [
        (ACTIVO, "Activo"),
        (RESCATADO, "Rescatado"),
    ]

    cuenta = models.ForeignKey(Cuenta, on_delete=models.CASCADE, related_name="plazos_fijos")
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    tasa_anual = models.DecimalField(max_digits=4, decimal_places=2)
    dias = models.PositiveSmallIntegerField()
    monto_final = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default=ACTIVO)
    fecha_inicio = models.DateField(auto_now_add=True)
    fecha_vencimiento = models.DateField()

    class Meta:
        ordering = ["-fecha_inicio"]

    def __str__(self):
        return f"Plazo fijo de ${self.monto} a {self.dias} días"

    @property
    def esta_vencido(self):
        return timezone.localdate() >= self.fecha_vencimiento

    @property
    def ganancia(self):
        return self.monto_final - self.monto

    def save(self, *args, **kwargs):
        if not self.fecha_vencimiento:
            self.fecha_vencimiento = timezone.localdate() + timedelta(days=self.dias)
        super().save(*args, **kwargs)


class Seguro(models.Model):
    cuenta = models.ForeignKey(Cuenta, on_delete=models.CASCADE, related_name="seguros")
    tipo = models.CharField(max_length=20)
    nombre = models.CharField(max_length=100)
    costo_mensual = models.DecimalField(max_digits=10, decimal_places=2)
    activo = models.BooleanField(default=True)
    fecha_contratacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha_contratacion"]

    def __str__(self):
        return f"{self.nombre} de {self.cuenta.numero_cuenta}"


def resolver_cuenta(valor):
    """Busca una cuenta por alias, CBU o numero de cuenta (usado en transferencias, contactos y solicitudes)."""
    valor = (valor or "").strip()
    if not valor:
        return None
    return Cuenta.objects.filter(
        Q(numero_cuenta__iexact=valor) | Q(alias__iexact=valor) | Q(cbu=valor)
    ).first()


def generar_numero_cuenta():
    """Genera un numero de cuenta random tipo TD-12345678, sin repetirse."""
    while True:
        numero = "TD-" + "".join(str(random.randint(0, 9)) for _ in range(8))
        if not Cuenta.objects.filter(numero_cuenta=numero).exists():
            return numero


def generar_tarjeta():
    """Genera un numero de tarjeta y vencimiento de mentira para el panel."""
    numero = "4" + "".join(str(random.randint(0, 9)) for _ in range(15))
    vencimiento = (timezone.now() + timedelta(days=365 * 4)).strftime("%m/%y")
    return numero, vencimiento


ADJETIVOS_ALIAS = ["rapido", "claro", "fuerte", "sereno", "dorado", "veloz", "noble", "astuto", "gentil", "firme"]
SUSTANTIVOS_ALIAS = ["rio", "sol", "luna", "monte", "valle", "bosque", "cielo", "mar", "viento", "roble"]


def generar_alias():
    """Genera un alias tipo 'palabra.palabra.tesoro', como el de cualquier billetera."""
    while True:
        alias = f"{random.choice(ADJETIVOS_ALIAS)}.{random.choice(SUSTANTIVOS_ALIAS)}.tesoro"
        if not Cuenta.objects.filter(alias=alias).exists():
            return alias


def _digito_verificador(digitos, pesos):
    """Digito verificador modulo 10, el mismo calculo que usa el CBU real."""
    total = sum(int(digito) * peso for digito, peso in zip(digitos, pesos))
    resto = total % 10
    return 0 if resto == 0 else 10 - resto


def generar_cbu():
    """
    Genera un CBU de 22 digitos con el algoritmo real (BCRA), pero con un
    codigo de entidad ficticio (999) porque Tesoro Digital no es un banco
    real ni esta registrado en ningun lado.
    """
    while True:
        entidad = "999"
        sucursal = f"{random.randint(0, 9999):04d}"
        base_bloque1 = entidad + sucursal
        dv1 = _digito_verificador(base_bloque1, [7, 1, 3, 9, 7, 1, 3])
        bloque1 = base_bloque1 + str(dv1)

        base_bloque2 = f"{random.randint(0, 10 ** 13 - 1):013d}"
        dv2 = _digito_verificador(base_bloque2, [3, 9, 7, 1, 3, 9, 7, 1, 3, 9, 7, 1, 3])
        bloque2 = base_bloque2 + str(dv2)

        cbu = bloque1 + bloque2
        if not Cuenta.objects.filter(cbu=cbu).exists():
            return cbu


def obtener_o_crear_cuenta(usuario):
    """
    Devuelve la Cuenta del usuario. Si todavia no tiene una (por ejemplo,
    un superusuario creado con createsuperuser, que nunca paso por el
    formulario de registro), le crea una cuenta nueva en el momento en
    vez de romper con un 404.
    """
    try:
        return Cuenta.objects.get(usuario=usuario)
    except Cuenta.DoesNotExist:
        numero_tarjeta, vencimiento = generar_tarjeta()
        return Cuenta.objects.create(
            usuario=usuario,
            numero_cuenta=generar_numero_cuenta(),
            numero_tarjeta=numero_tarjeta,
            vencimiento_tarjeta=vencimiento,
            alias=generar_alias(),
            cbu=generar_cbu(),
        )
