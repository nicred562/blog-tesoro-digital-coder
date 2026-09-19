"""
Archivo principal. Solo arma el flujo: carga los posts, crea el
objeto Blog, muestra el menu y llama al metodo que corresponda segun
lo que elija el usuario. La logica de verdad esta en blog/modelos.py.
"""

from blog.datos import cargar_posts, guardar_posts
from blog.menu import mostrar_menu, pedir_termino_busqueda, pedir_tag, pedir_datos_nuevo_post
from blog.modelos import Autor, Blog

ESTADOS_VALIDOS = ("publicado", "borrador", "archivado")


def opcion_ver_posts(blog):
    print("\n== TODOS LOS POSTS ==")
    blog.listar_posts()


def opcion_buscar_por_titulo(blog):
    termino = pedir_termino_busqueda()
    resultados = blog.buscar_por_titulo(termino)
    print(f"\n== RESULTADOS PARA '{termino}' ==")
    blog.listar_posts(resultados)


def opcion_filtrar_por_tag(blog):
    tag = pedir_tag()
    resultados = blog.filtrar_por_tag(tag)
    print(f"\n== POSTS CON TAG '{tag}' ==")
    blog.listar_posts(resultados)


def opcion_crear_post(blog):
    datos = pedir_datos_nuevo_post()

    if not datos["titulo"] or not datos["contenido"] or not datos["nombre_autor"]:
        print("\nFaltan datos obligatorios (titulo, contenido o autor). No se creo el post.")
        return

    autor = Autor(nombre=datos["nombre_autor"], bio=datos["bio_autor"])
    estado = datos["estado"] if datos["estado"] in ESTADOS_VALIDOS else "borrador"

    post = blog.crear_post(datos["titulo"], datos["contenido"], autor, datos["tags"], estado)
    print(f"\nPost '{post.titulo}' creado y agregado al blog.")


def opcion_validar_posts(blog):
    print("\n== VALIDACION DE POSTS ==")
    resultados = blog.validar_posts()
    for post, es_valido, errores in resultados:
        titulo = post.titulo if hasattr(post, "titulo") else "Post invalido"
        if es_valido:
            print(f"[OK]    '{titulo}' es valido.")
        else:
            print(f"[ERROR] '{titulo}' tiene {len(errores)} error(es):")
            for error in errores:
                print(f"        - {error}")


def opcion_guardar_posts(blog):
    guardar_posts(blog.obtener_posts())


def ejecutar_opcion(opcion, blog):
    """Ejecuta la opcion elegida. Devuelve False si hay que salir."""
    if opcion == "1":
        opcion_ver_posts(blog)
    elif opcion == "2":
        opcion_buscar_por_titulo(blog)
    elif opcion == "3":
        opcion_filtrar_por_tag(blog)
    elif opcion == "4":
        opcion_crear_post(blog)
    elif opcion == "5":
        opcion_validar_posts(blog)
    elif opcion == "6":
        opcion_guardar_posts(blog)
    elif opcion == "7":
        guardar_posts(blog.obtener_posts())
        print("\nGracias por visitar el blog. Hasta la proxima!")
        return False
    else:
        print("\nOpcion invalida. Elegi un numero del 1 al 7.")

    return True


def main():
    print("Bienvenido al blog por consola.")
    blog = Blog(cargar_posts())

    continuar = True
    while continuar:
        opcion = mostrar_menu()
        continuar = ejecutar_opcion(opcion, blog)


if __name__ == "__main__":
    main()
