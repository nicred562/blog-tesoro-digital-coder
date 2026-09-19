"""
Clases del sistema: Autor, Post y Blog. Reemplazan la parte central del
programa, que antes eran diccionarios sueltos.
"""


class Autor:
    """Representa a la persona que escribe un post."""

    def __init__(self, nombre, usuario="", email="", bio=""):
        self.nombre = nombre
        self.usuario = usuario
        self.email = email
        self.bio = bio

    def to_dict(self):
        return {
            "nombre": self.nombre,
            "usuario": self.usuario,
            "email": self.email,
            "bio": self.bio,
        }

    @staticmethod
    def from_dict(data):
        if not isinstance(data, dict) or not data.get("nombre"):
            return Autor(nombre="Autor desconocido")
        return Autor(
            nombre=data.get("nombre", "Autor desconocido"),
            usuario=data.get("usuario", ""),
            email=data.get("email", ""),
            bio=data.get("bio", ""),
        )


class Post:
    """Representa una publicacion del blog. El autor es un objeto Autor."""

    def __init__(self, titulo, contenido, autor, tags=None, estado="borrador"):
        self.titulo = titulo
        self.contenido = contenido
        self.autor = autor
        self.tags = tags if tags is not None else []
        self.estado = estado

    def to_dict(self):
        return {
            "titulo": self.titulo,
            "contenido": self.contenido,
            "autor": self.autor.to_dict() if isinstance(self.autor, Autor) else {},
            "tags": self.tags,
            "estado": self.estado,
        }

    @staticmethod
    def from_dict(data):
        if not isinstance(data, dict):
            raise ValueError("el post cargado no es un diccionario valido")
        autor = Autor.from_dict(data.get("autor", {}))
        tags = data.get("tags", [])
        return Post(
            titulo=data.get("titulo", "Sin titulo"),
            contenido=data.get("contenido", ""),
            autor=autor,
            tags=tags if isinstance(tags, list) else [],
            estado=data.get("estado", "borrador"),
        )


class Blog:
    """Centraliza la coleccion de posts y las operaciones sobre ella."""

    def __init__(self, posts=None):
        self.posts = posts if posts is not None else []

    def obtener_posts(self):
        return self.posts

    def agregar_post(self, post):
        self.posts.append(post)

    def crear_post(self, titulo, contenido, autor, tags=None, estado="borrador"):
        post = Post(titulo, contenido, autor, tags, estado)
        self.agregar_post(post)
        return post

    def listar_posts(self, lista=None):
        lista = self.posts if lista is None else lista
        if not lista:
            print("No hay posts para mostrar.")
            return
        for post in lista:
            nombre_autor = post.autor.nombre if isinstance(post.autor, Autor) else "Autor desconocido"
            print(f"- {post.titulo}  |  Autor: {nombre_autor}  |  Estado: {post.estado}")

    def buscar_por_titulo(self, termino):
        termino = (termino or "").lower()
        return [post for post in self.posts if termino in post.titulo.lower()]

    def filtrar_por_tag(self, tag):
        tag = (tag or "").lower()
        return [post for post in self.posts if tag in [str(t).lower() for t in post.tags]]

    def validar_posts(self):
        from blog.validaciones import validar_posts as _validar_posts
        return _validar_posts(self.posts)

    def a_diccionarios(self):
        return [post.to_dict() for post in self.posts]
