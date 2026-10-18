import shutil
import tempfile
from io import BytesIO

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .models import Post

MEDIA_TEMP = tempfile.mkdtemp()


def imagen_fake(nombre="foto.png"):
    buffer = BytesIO()
    Image.new("RGB", (4, 4), color=(10, 61, 98)).save(buffer, format="PNG")
    return SimpleUploadedFile(nombre, buffer.getvalue(), content_type="image/png")


class PostModelTests(TestCase):
    def test_el_str_devuelve_el_titulo(self):
        post = Post.objects.create(titulo="Mi post", contenido="...", autor="Nico")
        self.assertEqual(str(post), "Mi post")

    def test_el_slug_se_genera_solo_a_partir_del_titulo(self):
        post = Post.objects.create(titulo="Como ahorrar plata", contenido="...", autor="Nico")
        self.assertEqual(post.slug, "como-ahorrar-plata")

    def test_titulos_repetidos_generan_slugs_distintos(self):
        post1 = Post.objects.create(titulo="Mismo titulo", contenido="...", autor="Nico")
        post2 = Post.objects.create(titulo="Mismo titulo", contenido="...", autor="Nico")
        self.assertNotEqual(post1.slug, post2.slug)

    def test_el_estado_por_defecto_es_borrador(self):
        post = Post.objects.create(titulo="Sin estado", contenido="...", autor="Nico")
        self.assertEqual(post.estado, Post.Estado.BORRADOR)


class ListaYDetalleTests(TestCase):
    def setUp(self):
        self.publicado = Post.objects.create(
            titulo="Nota publicada",
            contenido="Contenido de la nota publicada.",
            autor="Nico",
            estado=Post.Estado.PUBLICADO,
        )
        self.borrador = Post.objects.create(
            titulo="Nota en borrador",
            contenido="Contenido de la nota en borrador.",
            autor="Nico",
            estado=Post.Estado.BORRADOR,
        )

    def test_el_listado_publico_solo_muestra_posts_publicados(self):
        response = self.client.get(reverse("lista_posts"))
        self.assertContains(response, self.publicado.titulo)
        self.assertNotContains(response, self.borrador.titulo)

    def test_el_detalle_de_un_post_publicado_carga(self):
        response = self.client.get(reverse("detalle_post", args=[self.publicado.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.publicado.contenido)

    def test_el_detalle_de_un_borrador_da_404(self):
        response = self.client.get(reverse("detalle_post", args=[self.borrador.slug]))
        self.assertEqual(response.status_code, 404)

    def test_un_post_sin_imagen_muestra_el_icono_sin_romper(self):
        response = self.client.get(reverse("detalle_post", args=[self.publicado.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "tarjeta-post-icono")


@override_settings(MEDIA_ROOT=MEDIA_TEMP)
class CrudProtegidoTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.usuario = User.objects.create_user(username="autor", password="ContraseñaSegura123")

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_TEMP, ignore_errors=True)

    def test_crear_post_sin_login_redirige_al_login_del_blog(self):
        response = self.client.get(reverse("crear_post"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_gestionar_posts_sin_login_redirige_al_login(self):
        response = self.client.get(reverse("gestionar_posts"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_crear_post_logueado_funciona_y_procesa_la_imagen(self):
        self.client.login(username="autor", password="ContraseñaSegura123")
        response = self.client.post(reverse("crear_post"), {
            "titulo": "Post con imagen",
            "resumen": "",
            "contenido": "contenido de prueba",
            "autor": "Nico",
            "estado": "publicado",
            "icono": "🧪",
            "imagen": imagen_fake(),
        })
        self.assertRedirects(response, reverse("gestionar_posts"))
        post = Post.objects.get(titulo="Post con imagen")
        self.assertTrue(post.imagen)

    def test_crear_post_sin_imagen_tambien_funciona(self):
        self.client.login(username="autor", password="ContraseñaSegura123")
        self.client.post(reverse("crear_post"), {
            "titulo": "Post sin imagen",
            "resumen": "",
            "contenido": "contenido de prueba",
            "autor": "Nico",
            "estado": "publicado",
            "icono": "📝",
        })
        post = Post.objects.get(titulo="Post sin imagen")
        self.assertFalse(post.imagen)

    def test_editar_y_borrar_sin_login_redirigen_y_no_modifican_nada(self):
        post = Post.objects.create(
            titulo="Protegido", contenido="...", autor="Nico", estado=Post.Estado.PUBLICADO,
        )
        respuesta_editar = self.client.get(reverse("editar_post", args=[post.slug]))
        self.assertEqual(respuesta_editar.status_code, 302)

        respuesta_borrar = self.client.post(reverse("eliminar_post", args=[post.slug]))
        self.assertEqual(respuesta_borrar.status_code, 302)
        self.assertTrue(Post.objects.filter(pk=post.pk).exists())

    def test_borrar_logueado_pide_confirmacion_y_borra_recien_con_el_post(self):
        self.client.login(username="autor", password="ContraseñaSegura123")
        post = Post.objects.create(
            titulo="A borrar", contenido="...", autor="Nico", estado=Post.Estado.PUBLICADO,
        )
        respuesta_confirmacion = self.client.get(reverse("eliminar_post", args=[post.slug]))
        self.assertEqual(respuesta_confirmacion.status_code, 200)
        self.assertTrue(Post.objects.filter(pk=post.pk).exists())

        respuesta_borrado = self.client.post(reverse("eliminar_post", args=[post.slug]))
        self.assertRedirects(respuesta_borrado, reverse("gestionar_posts"))
        self.assertFalse(Post.objects.filter(pk=post.pk).exists())

    def test_editar_sin_subir_imagen_nueva_conserva_la_anterior(self):
        self.client.login(username="autor", password="ContraseñaSegura123")
        post = Post.objects.create(
            titulo="Con imagen", contenido="...", autor="Nico",
            estado=Post.Estado.PUBLICADO, imagen=imagen_fake(),
        )
        nombre_original = post.imagen.name

        self.client.post(reverse("editar_post", args=[post.slug]), {
            "titulo": post.titulo,
            "resumen": "",
            "contenido": "contenido editado",
            "autor": "Nico",
            "estado": "publicado",
            "icono": "📝",
        })
        post.refresh_from_db()
        self.assertEqual(post.imagen.name, nombre_original)
        self.assertEqual(post.contenido, "contenido editado")
