from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Perfil


class RegistroForm(UserCreationForm):
    email = forms.EmailField(required=False, label="Email")

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].help_text = "Sin espacios. Lo vas a usar para ingresar."
        self.fields["password1"].help_text = "Mínimo 8 caracteres, que no sea algo obvio."
        self.fields["password2"].help_text = ""


class PerfilForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ["biografia", "link_web", "avatar"]
        labels = {
            "biografia": "Biografía",
            "link_web": "Sitio web (opcional)",
            "avatar": "Avatar",
        }


class DatosUsuarioForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]
        labels = {
            "first_name": "Nombre",
            "last_name": "Apellido",
            "email": "Email",
        }
