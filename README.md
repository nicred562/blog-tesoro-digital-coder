# Blog Django - Tesoro Digital

Proyecto base del blog web de **Tesoro Digital**, un banco digital. El blog va a publicar contenido para clientes: guías de uso de la app, ahorro, tarjetas, transferencias, seguridad y novedades. Este repositorio también conserva el blog por consola que se construyó en los módulos anteriores (ver más abajo).

## Descripción

Contiene la estructura inicial de un proyecto Django (`blog_project`) y una aplicación llamada `posts`, con idioma `es-ar` y zona horaria `America/Argentina/Buenos_Aires`. Todavía no tiene modelos, vistas ni templates.

## Instalación

Clonar el repositorio:

```bash
git clone https://github.com/nicred562/blog-tesoro-digital-coder.git
```

Entrar a la carpeta del proyecto:

```bash
cd blog-tesoro-digital-coder
```

Crear el entorno virtual:

```bash
python -m venv venv
```

Activarlo (Windows PowerShell):

```powershell
.\venv\Scripts\Activate.ps1
```

Activarlo (Linux o macOS):

```bash
source venv/bin/activate
```

Instalar las dependencias:

```bash
pip install -r requirements.txt
```

Levantar el servidor de desarrollo:

```bash
python manage.py runserver
```

Abrir en el navegador: http://127.0.0.1:8000/

## Aplicaciones

- `posts`: aplicación inicial para manejar las publicaciones del blog.

## Estructura del proyecto Django

```
blog_consola/
├── manage.py
├── requirements.txt
├── .gitignore
├── blog_project/     (configuración del proyecto Django)
└── posts/            (app del blog)
```

---

# Blog por Consola (Tesoro Digital)

Blog por consola de Tesoro Digital en Python, organizado en módulos y con las entidades modeladas como clases (POO). Permite ver posts, buscar por título, filtrar por tag, crear posts nuevos, validarlos y guardarlos en un archivo JSON para que persistan entre ejecuciones.

## Cómo correrlo

```bash
python main.py
```

Desde la carpeta raíz (`blog_consola/`), donde están `main.py` y `posts.json`.

## Estructura

```
blog_consola/
├── main.py
├── posts.json
├── README.md
└── blog/
    ├── __init__.py
    ├── datos.py
    ├── menu.py
    ├── modelos.py
    └── validaciones.py
```

- `main.py` → arranca el programa, crea el `Blog` y conecta el menú con sus métodos.
- `blog/modelos.py` → clases `Autor`, `Post` y `Blog`.
- `blog/datos.py` → carga y guarda `posts.json`, y guarda constantes de referencia (estados válidos, tags).
- `blog/menu.py` → menú e `input()`.
- `blog/validaciones.py` → valida que un `Post` tenga los datos correctos.

## Clases principales

- **Autor**: representa a quien escribe un post (`nombre`, `usuario`, `email`, `bio`).
- **Post**: representa una publicación (`titulo`, `contenido`, `autor`, `tags`, `estado`). El `autor` es siempre una instancia de `Autor`, no un texto ni un diccionario suelto.
- **Blog**: centraliza la colección de posts (lista de objetos `Post`) y toda la lógica: listar, buscar por título, filtrar por tag, crear posts, validarlos y convertirlos a diccionarios.

## Persistencia con JSON

- Al arrancar, `main.py` llama a `cargar_posts()` (en `blog/datos.py`), que lee `posts.json` y reconstruye cada diccionario como un objeto `Post` (con su `Autor` adentro), usando `Post.from_dict()` / `Autor.from_dict()`.
- Si `posts.json` no existe, está vacío o tiene contenido inválido, `cargar_posts()` avisa por consola y devuelve una lista vacía en vez de romper el programa.
- Al guardar (opción 6 del menú, o automáticamente al salir), `guardar_posts()` convierte cada `Post` a diccionario con `post.to_dict()` y escribe la lista completa en `posts.json` con el módulo `json`.
- Un post creado desde la opción "Crear nuevo post" es una instancia real de `Post`/`Autor`, se agrega al `Blog` y queda disponible para guardarse igual que los demás.

## Menú

```
--- MENU DEL BLOG ---
1. Ver todos los posts
2. Buscar por titulo
3. Filtrar por tag
4. Crear nuevo post
5. Validar posts
6. Guardar posts en JSON
7. Salir
```

## Qué cambió respecto al checkpoint anterior

- Se agregó `blog/modelos.py` con las clases `Autor`, `Post` y `Blog`.
- Los posts dejaron de ser diccionarios sueltos en `blog/datos.py`: ahora son objetos `Post`, y su autor es un objeto `Autor` (composición).
- `blog/operaciones.py` se eliminó: su lógica (listar, buscar, filtrar) pasó a ser métodos de la clase `Blog`.
- `blog/datos.py` ahora se encarga de leer y escribir `posts.json`, en vez de tener los posts hardcodeados en el código.
- `blog/validaciones.py` se adaptó para validar instancias de `Post` en vez de diccionarios.
- El menú sumó las opciones "Crear nuevo post" y "Guardar posts en JSON".
- `main.py` instancia un `Blog` y todas las opciones del menú llaman a métodos de esa instancia.
