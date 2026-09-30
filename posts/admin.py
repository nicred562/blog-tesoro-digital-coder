from django.contrib import admin

from .models import Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("titulo", "autor", "estado", "fecha_creacion")
    list_filter = ("estado",)
    search_fields = ("titulo", "contenido", "autor")
    prepopulated_fields = {"slug": ("titulo",)}
