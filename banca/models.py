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
    TIPO_CHOICES = [
        (DEPOSITO, "Depósito"),
        (EXTRACCION, "Extracción"),
        (TRANSFERENCIA_ENVIADA, "Transferencia enviada"),
        (TRANSFERENCIA_RECIBIDA, "Transferencia recibida"),
        (PAGO_SERVICIO, "Pago de servicio"),
        (RECARGA_CELULAR, "Recarga de celular"),
        (RENDIMIENTO, "Rendimiento"),
    ]
    TIPOS_INGRESO = (DEPOSITO, TRANSFERENCIA_RECIBIDA, RENDIMIENTO)

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
