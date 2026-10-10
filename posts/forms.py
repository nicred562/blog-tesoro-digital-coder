from django import forms

from .models import Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["titulo", "resumen", "contenido", "autor", "estado", "icono", "imagen"]
        labels = {
            "titulo": "Título",
            "resumen": "Resumen (opcional)",
            "contenido": "Contenido",
            "autor": "Autor",
            "estado": "Estado",
            "icono": "Ícono (un emoji, opcional)",
            "imagen": "Imagen (opcional)",
        }
