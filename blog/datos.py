"""
Carga y guardado de posts en posts.json. Ademas guarda algunas
constantes de referencia (estados y tags posibles).
"""

import json
import os

from blog.modelos import Post

RUTA_JSON = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "posts.json"
)

# Estados que puede tener un post
estados_post = ["publicado", "borrador", "archivado"]

# Tags disponibles en el blog (solo de referencia)
etiquetas_blog = {"python", "fivem", "gaming", "tutorial", "noticias", "programacion"}


def cargar_posts(ruta=RUTA_JSON):
    """
    Lee posts.json y devuelve una lista de objetos Post.
    Si el archivo no existe, esta vacio o el contenido es invalido,
    devuelve una lista vacia en vez de romper el programa.
    """
    if not os.path.exists(ruta):
        print(f"No se encontro '{ruta}'. Se arranca con el blog vacio.")
        return []

    try:
        with open(ruta, "r", encoding="utf-8") as archivo:
            contenido = archivo.read().strip()
    except OSError as error:
        print(f"No se pudo abrir '{ruta}' ({error}). Se arranca con el blog vacio.")
        return []

    if not contenido:
        print(f"El archivo '{ruta}' esta vacio. Se arranca con el blog vacio.")
        return []

    try:
        datos = json.loads(contenido)
    except json.JSONDecodeError as error:
        print(f"El archivo '{ruta}' tiene contenido invalido ({error}). Se arranca con el blog vacio.")
        return []

    if not isinstance(datos, list):
        print(f"El contenido de '{ruta}' no es una lista de posts. Se arranca con el blog vacio.")
        return []

    posts = []
    for item in datos:
        try:
            posts.append(Post.from_dict(item))
        except ValueError as error:
            print(f"Se salteo un post invalido dentro de '{ruta}': {error}")
    return posts


def guardar_posts(posts, ruta=RUTA_JSON):
    """Convierte los posts a diccionarios y los guarda en posts.json."""
    try:
        datos = [post.to_dict() for post in posts]
    except AttributeError:
        print("Error: hay elementos que no son posts validos, no se guardo nada.")
        return False

    try:
        with open(ruta, "w", encoding="utf-8") as archivo:
            json.dump(datos, archivo, indent=2, ensure_ascii=False)
    except OSError as error:
        print(f"No se pudo guardar en '{ruta}': {error}")
        return False

    print(f"Posts guardados en '{ruta}'.")
    return True
