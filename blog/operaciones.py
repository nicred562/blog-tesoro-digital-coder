"""
Operaciones del blog: listar, buscar y filtrar. Reciben la lista de
posts por parametro, no dependen de variables globales.
"""


def listar_posts(lista):
    """Muestra titulo, autor y estado de cada post de la lista."""
    if not lista:
        print("No hay posts para mostrar.")
        return

    for post in lista:
        titulo = post.get("titulo", "Sin titulo")
        autor = post.get("autor", {})
        nombre_autor = (
            autor.get("nombre", "Autor desconocido")
            if isinstance(autor, dict)
            else "Autor desconocido"
        )
        estado = post.get("estado", "sin estado")
        print(f"- {titulo}  |  Autor: {nombre_autor}  |  Estado: {estado}")


def buscar_por_titulo(lista, termino):
    """Devuelve los posts cuyo titulo contiene el termino (sin mayus/minus)."""
    termino = (termino or "").lower()
    return [
        post
        for post in lista
        if termino in post.get("titulo", "").lower()
    ]


def filtrar_por_tag(lista, tag):
    """Devuelve los posts que tengan ese tag (sin mayus/minus)."""
    tag = (tag or "").lower()
    resultados = []
    for post in lista:
        tags = post.get("tags", [])
        if isinstance(tags, list) and tag in [str(t).lower() for t in tags]:
            resultados.append(post)
    return resultados
