import shutil
import tempfile
from io import BytesIO

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .models import Perfil

MEDIA_TEMP = tempfile.mkdtemp()


def avatar_fake():
    buffer = BytesIO()
    Image.new("RGB", (4, 4), color=(26, 188, 156)).save(buffer, format="PNG")
    return SimpleUploadedFile("avatar.png", buffer.getvalue(), content_type="image/png")


class RegistroTests(TestCase):
    def test_registrarse_crea_el_usuario_y_el_perfil_sin_signals(self):
        self.client.post(reverse("registro"), {
            "username": "nuevo",
            "email": "nuevo@tesorodigital.com",
            "password1": "ContraseñaSegura123",
            "password2": "ContraseñaSegura123",
        })
        usuario = User.objects.get(username="nuevo")
        self.assertTrue(Perfil.objects.filter(user=usuario).exists())

    def test_registrarse_redirige_al_perfil(self):
        response = self.client.post(reverse("registro"), {
            "username": "otro",
            "email": "",
            "password1": "ContraseñaSegura123",
            "password2": "ContraseñaSegura123",
        })
        self.assertRedirects(response, reverse("perfil"))

    def test_registrarse_loguea_automaticamente(self):
        self.client.post(reverse("registro"), {
            "username": "tercero",
            "email": "",
            "password1": "ContraseñaSegura123",
            "password2": "ContraseñaSegura123",
        })
        response = self.client.get(reverse("perfil"))
        self.assertEqual(response.status_code, 200)


class LoginLogoutTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(username="autor", password="ContraseñaSegura123")
        Perfil.objects.create(user=self.usuario)

    def test_login_con_credenciales_correctas(self):
        logueado = self.client.login(username="autor", password="ContraseñaSegura123")
        self.assertTrue(logueado)

    def test_perfil_sin_login_redirige_al_login_del_blog(self):
        response = self.client.get(reverse("perfil"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_logout_cierra_la_sesion(self):
        self.client.login(username="autor", password="ContraseñaSegura123")
        self.client.post(reverse("logout"))
        response = self.client.get(reverse("perfil"))
        self.assertEqual(response.status_code, 302)


@override_settings(MEDIA_ROOT=MEDIA_TEMP)
class EditarPerfilTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_TEMP, ignore_errors=True)

    def setUp(self):
        self.usuario = User.objects.create_user(username="autor", password="ContraseñaSegura123")
        Perfil.objects.create(user=self.usuario)
        self.client.login(username="autor", password="ContraseñaSegura123")

    def test_editar_perfil_guarda_biografia_sitio_web_y_avatar(self):
        self.client.post(reverse("editar_perfil"), {
            "first_name": "Nico",
            "last_name": "Autor",
            "email": "autor@tesorodigital.com",
            "biografia": "Escribo sobre finanzas personales.",
            "link_web": "https://ejemplo.com",
            "avatar": avatar_fake(),
        })
        perfil = Perfil.objects.get(user=self.usuario)
        self.assertEqual(perfil.biografia, "Escribo sobre finanzas personales.")
        self.assertTrue(perfil.avatar)

    def test_editar_perfil_tambien_actualiza_datos_del_user(self):
        self.client.post(reverse("editar_perfil"), {
            "first_name": "Nico",
            "last_name": "Autor",
            "email": "autor@tesorodigital.com",
            "biografia": "",
            "link_web": "",
        })
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.first_name, "Nico")
        self.assertEqual(self.usuario.email, "autor@tesorodigital.com")

    def test_un_usuario_sin_perfil_previo_no_rompe_la_vista(self):
        # Simula un superusuario creado con createsuperuser, que nunca paso
        # por la vista de registro y por lo tanto no tiene Perfil todavia.
        huerfano = User.objects.create_user(username="sin_perfil", password="ContraseñaSegura123")
        self.client.login(username="sin_perfil", password="ContraseñaSegura123")

        response = self.client.get(reverse("perfil"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Perfil.objects.filter(user=huerfano).exists())
