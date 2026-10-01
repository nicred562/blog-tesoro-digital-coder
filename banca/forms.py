from decimal import Decimal

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Cuenta, resolver_cuenta

EMPRESAS_SERVICIO = [
    ("luzclara", "Luz Clara (electricidad)"),
    ("aquavida", "AquaVida (agua)"),
    ("gashogar", "GasHogar (gas)"),
    ("conectatel", "ConectaTel (telefonía e internet)"),
]

OPERADORAS_RECARGA = [
    ("moviclaro", "Moviclaro"),
    ("teleandes", "TeleAndes"),
    ("rapifon", "Rapifon"),
]


class RegistroForm(UserCreationForm):
    first_name = forms.CharField(label="Nombre", max_length=150)
    email = forms.EmailField(label="Correo electronico")

    class Meta:
        model = User
        fields = ("first_name", "username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Usuario"
        self.fields["username"].help_text = "Sin espacios. Lo vas a usar para ingresar."
        self.fields["password1"].label = "Contrasena"
        self.fields["password1"].help_text = "Minimo 8 caracteres, que no sea algo obvio."
        self.fields["password2"].label = "Repetir contrasena"
        self.fields["password2"].help_text = ""

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Ya hay una cuenta con ese email.")
        return email


class LoginForm(forms.Form):
    username = forms.CharField(label="Usuario")
    password = forms.CharField(label="Contrasena", widget=forms.PasswordInput)


class VerificacionForm(forms.Form):
    codigo = forms.CharField(label="Codigo de verificacion", max_length=6)


class MontoForm(forms.Form):
    monto = forms.DecimalField(
        label="Monto",
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.01"),
    )
    descripcion = forms.CharField(label="Nota (opcional)", max_length=140, required=False)


class MontoConSaldoForm(MontoForm):
    """Base para operaciones que descuentan saldo: retirar, pagar servicios, recargar."""

    def __init__(self, *args, saldo_disponible=None, **kwargs):
        self.saldo_disponible = saldo_disponible
        super().__init__(*args, **kwargs)

    def clean_monto(self):
        monto = self.cleaned_data["monto"]
        if self.saldo_disponible is not None and monto > self.saldo_disponible:
            raise forms.ValidationError("No tenes saldo suficiente para esa operacion.")
        return monto


class RetiroForm(MontoConSaldoForm):
    pass


class PagoServicioForm(MontoConSaldoForm):
    empresa = forms.ChoiceField(label="Empresa", choices=EMPRESAS_SERVICIO)
    numero_factura = forms.CharField(label="Numero de factura (opcional)", max_length=30, required=False)

    field_order = ["empresa", "numero_factura", "monto", "descripcion"]


class RecargaForm(MontoConSaldoForm):
    operadora = forms.ChoiceField(label="Operadora", choices=OPERADORAS_RECARGA)
    numero_telefono = forms.CharField(label="Numero de telefono", max_length=20)

    field_order = ["operadora", "numero_telefono", "monto", "descripcion"]


class DestinoFormBase(forms.Form):
    """Base para formularios que resuelven un destino por alias, CBU o numero de cuenta."""

    destino = forms.CharField(
        label="Alias, CBU o numero de cuenta",
        max_length=40,
        help_text="Por ejemplo: rio.sol.tesoro, TD-12345678 o el CBU completo.",
    )

    def __init__(self, *args, cuenta_propia=None, **kwargs):
        self.cuenta_propia = cuenta_propia
        super().__init__(*args, **kwargs)

    def clean_destino(self):
        valor = self.cleaned_data["destino"].strip()
        cuenta = resolver_cuenta(valor)

        if cuenta is None:
            raise forms.ValidationError("No existe ninguna cuenta con ese alias, CBU o numero.")
        if self.cuenta_propia and cuenta.pk == self.cuenta_propia.pk:
            raise forms.ValidationError("No podes usar tu propia cuenta aca.")
        return cuenta


class TransferenciaForm(DestinoFormBase, MontoForm):
    field_order = ["destino", "monto", "descripcion"]

    def __init__(self, *args, cuenta_origen=None, **kwargs):
        super().__init__(*args, cuenta_propia=cuenta_origen, **kwargs)

    def clean(self):
        cleaned = super().clean()
        monto = cleaned.get("monto")
        if monto is not None and self.cuenta_propia and monto > self.cuenta_propia.saldo:
            self.add_error("monto", "No tenes saldo suficiente para esa transferencia.")
        return cleaned


class SolicitudForm(DestinoFormBase, MontoForm):
    field_order = ["destino", "monto", "descripcion"]


class ContactoForm(DestinoFormBase):
    apodo = forms.CharField(label="Apodo (opcional)", max_length=40, required=False)

    field_order = ["destino", "apodo"]


class PerfilForm(forms.ModelForm):
    class Meta:
        model = Cuenta
        fields = ["foto", "alias", "es_comercio", "nombre_comercio"]
        labels = {
            "foto": "Foto de perfil",
            "alias": "Alias para recibir transferencias",
            "es_comercio": "Es una cuenta de comercio",
            "nombre_comercio": "Nombre del comercio",
        }
        help_texts = {
            "alias": "Formato palabra.palabra.palabra, todo en minusculas.",
            "es_comercio": "Mostrá tu negocio en el QR para cobrar.",
        }

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("es_comercio") and not cleaned.get("nombre_comercio"):
            self.add_error("nombre_comercio", "Si activás cuenta de comercio, necesitás ponerle un nombre.")
        return cleaned


class DolarForm(forms.Form):
    monto_usd = forms.DecimalField(
        label="Cantidad de dólares",
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.01"),
    )

    def __init__(self, *args, saldo_disponible_usd=None, **kwargs):
        self.saldo_disponible_usd = saldo_disponible_usd
        super().__init__(*args, **kwargs)

    def clean_monto_usd(self):
        monto = self.cleaned_data["monto_usd"]
        if self.saldo_disponible_usd is not None and monto > self.saldo_disponible_usd:
            raise forms.ValidationError("No tenes esa cantidad de dólares para vender.")
        return monto


class PrestamoForm(forms.Form):
    OPCIONES_CUOTAS = [(3, "3 cuotas"), (6, "6 cuotas"), (12, "12 cuotas"), (24, "24 cuotas")]

    monto_solicitado = forms.DecimalField(
        label="Monto a solicitar",
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("1000.00"),
        max_value=Decimal("10000000.00"),
    )
    cantidad_cuotas = forms.TypedChoiceField(label="Cuotas", choices=OPCIONES_CUOTAS, coerce=int)


class PlazoFijoForm(forms.Form):
    OPCIONES_DIAS = [(30, "30 días"), (60, "60 días"), (90, "90 días"), (180, "180 días"), (365, "365 días")]

    monto = forms.DecimalField(
        label="Monto a invertir",
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("100.00"),
    )
    dias = forms.TypedChoiceField(label="Plazo", choices=OPCIONES_DIAS, coerce=int)

    def __init__(self, *args, saldo_disponible=None, **kwargs):
        self.saldo_disponible = saldo_disponible
        super().__init__(*args, **kwargs)

    def clean_monto(self):
        monto = self.cleaned_data["monto"]
        if self.saldo_disponible is not None and monto > self.saldo_disponible:
            raise forms.ValidationError("No tenes saldo suficiente para ese plazo fijo.")
        return monto
