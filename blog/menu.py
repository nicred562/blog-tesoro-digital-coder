"""
Menu e input(). Este modulo solo pregunta cosas y devuelve lo que
escribe el usuario, no busca ni valida nada por su cuenta.
"""


def mostrar_menu():
    """Muestra el menu, pide una opcion y la devuelve tal cual."""
    print("\n--- MENU DEL BLOG ---")
    print("1. Ver todos los posts")
    print("2. Buscar por titulo")
    print("3. Filtrar por tag")
    print("4. Crear nuevo post")
    print("5. Validar posts")
    print("6. Guardar posts en JSON")
    print("7. Salir")

    opcion = input("Elegi una opcion (1-7): ").strip()
    return opcion


def pedir_termino_busqueda():
    """Pide el termino a buscar en los titulos."""
    return input("Ingresa el termino a buscar en el titulo: ").strip()


def pedir_tag():
    """Pide el tag por el que filtrar."""
    return input("Ingresa el tag a filtrar: ").strip()


def pedir_datos_nuevo_post():
    """Pide los datos de un post nuevo y los devuelve en un diccionario."""
    print("\n== NUEVO POST ==")
    titulo = input("Titulo: ").strip()
    contenido = input("Contenido: ").strip()
    nombre_autor = input("Nombre del autor: ").strip()
    bio_autor = input("Bio del autor (opcional): ").strip()
    tags_texto = input("Tags separados por coma: ").strip()
    tags = [tag.strip() for tag in tags_texto.split(",") if tag.strip()]
    estado = input("Estado (publicado/borrador/archivado): ").strip().lower()

    return {
        "titulo": titulo,
        "contenido": contenido,
        "nombre_autor": nombre_autor,
        "bio_autor": bio_autor,
        "tags": tags,
        "estado": estado,
    }
