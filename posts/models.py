from django.db import models
from django.utils.text import slugify


class Post(models.Model):
    class Estado(models.TextChoices):
        BORRADOR = "borrador", "Borrador"
        PUBLICADO = "publicado", "Publicado"
        ARCHIVADO = "archivado", "Archivado"

    titulo = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    resumen = models.CharField(max_length=300, blank=True)
    contenido = models.TextField()
    autor = models.CharField(max_length=150)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.BORRADOR)
    icono = models.CharField(max_length=10, blank=True, default="📝")

    class Meta:
        ordering = ["-fecha_creacion"]

    def __str__(self):
        return self.titulo

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.titulo)
            slug = base
            contador = 1
            while Post.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                contador += 1
                slug = f"{base}-{contador}"
            self.slug = slug
        super().save(*args, **kwargs)
