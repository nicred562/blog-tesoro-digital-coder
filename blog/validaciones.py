"""
Validaciones: revisan que un post (objeto Post) este bien formado.
"""

from blog.datos import estados_post
from blog.modelos import Autor, Post


def validar_post(post):
    """
    Chequea que sea una instancia de Post, con titulo y contenido no
    vacios, autor valido con nombre, tags como lista y estado valido.

    Devuelve (es_valido, errores).
    """
    if not isinstance(post, Post):
        return False, ["El post no es una instancia valida de Post."]

    errores = []

    if not isinstance(post.titulo, str) or not post.titulo.strip():
        errores.append("El titulo no puede estar vacio.")

    if not isinstance(post.contenido, str) or not post.contenido.strip():
        errores.append("El contenido no puede estar vacio.")

    if not isinstance(post.autor, Autor):
        errores.append("El autor debe ser una instancia de Autor.")
    elif not post.autor.nombre:
        errores.append("El autor debe tener un nombre.")

    if not isinstance(post.tags, list):
        errores.append("Los tags deben estar guardados como una lista.")

    if post.estado not in estados_post:
        errores.append(
            f"El estado '{post.estado}' no es valido "
            f"(validos: {', '.join(estados_post)})."
        )

    return (len(errores) == 0, errores)


def validar_posts(lista):
    """Valida cada post de la lista. Devuelve (post, es_valido, errores) por post."""
    resultados = []
    for post in lista:
        es_valido, errores = validar_post(post)
        resultados.append((post, es_valido, errores))
    return resultados
