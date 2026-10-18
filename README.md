# Blog Django - Tesoro Digital

Proyecto base del blog web de **Tesoro Digital**, un banco digital. El blog va a publicar contenido para clientes: guías de uso de la app, ahorro, tarjetas, transferencias, seguridad y novedades. Este repositorio también conserva el blog por consola que se construyó en los módulos anteriores (ver más abajo).

## Descripción

Proyecto Django (`blog_project`) con tres apps:

- `posts`: el blog en sí (notas, ayuda, términos). Los posts son un modelo (`Post`) con CRUD completo desde el sitio y desde `/admin/`, con base de datos SQLite.
- `accounts`: registro, login, logout y perfil de usuario (biografía + avatar) para quienes escriben en el blog. Protege crear/editar/borrar posts.
- `banca`: una demo de banca online (cuentas, depósitos, retiros, transferencias, tarjeta virtual, etc.), también con modelos y base de datos SQLite. Es un agregado aparte, no forma parte de lo que piden los checkpoints de `posts`/`accounts`, y tiene su **propio** sistema de login independiente (no te confundas: `/login/` es para escribir en el blog, `/banca/ingresar/` es para la cuenta bancaria ficticia).

Idioma `es-ar`, zona horaria `America/Argentina/Buenos_Aires`.

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

Crear la base de datos:

```bash
python manage.py migrate
```

Crear un usuario administrador (para poder entrar a `/admin/` y cargar posts):

```bash
python manage.py createsuperuser
```

Va a pedir un nombre de usuario, un email y una contraseña. Con eso ya se puede entrar al panel.

Levantar el servidor de desarrollo:

```bash
python manage.py runserver
```

Abrir en el navegador:

- http://127.0.0.1:8000/ → página de inicio del blog
- http://127.0.0.1:8000/notas/ → listado de notas publicadas (público)
- http://127.0.0.1:8000/registro/ → crear una cuenta de autor
- http://127.0.0.1:8000/login/ → iniciar sesión en el blog
- http://127.0.0.1:8000/perfil/ → tu perfil (requiere login)
- http://127.0.0.1:8000/notas/crear/ → crear una nota nueva, con imagen opcional (requiere login)
- http://127.0.0.1:8000/notas/gestionar/ → listado con **todos** los posts, cualquier estado (requiere login)
- http://127.0.0.1:8000/acerca/ → página "Acerca de"
- http://127.0.0.1:8000/ayuda/, http://127.0.0.1:8000/terminos/ y http://127.0.0.1:8000/contacto/
- http://127.0.0.1:8000/admin/ → panel de administración (usá el usuario que creaste con `createsuperuser`)
- http://127.0.0.1:8000/banca/ → landing de la banca online (login propio, independiente del de arriba)

## Aplicaciones

- `posts`: el blog, con CRUD completo de publicaciones. El modelo `Post` tiene título, contenido, autor, fecha de creación, estado (borrador/publicado/archivado) e **imagen opcional**. El listado público (`/notas/`) solo muestra los posts con estado "publicado" (`Post.objects.filter(estado="publicado")`); crear, editar y borrar requieren estar logueado (ver `accounts` abajo).
- `accounts`: registro, login, logout, cambio de contraseña y perfil (biografía + avatar) para quienes escriben en el blog.
- `banca`: demo de banca online (agregado extra, fuera de lo que piden los checkpoints de `posts`/`accounts`). Usa modelos y base de datos: cuentas con alias/CBU/tarjeta virtual, login propio en dos pasos, depósitos, retiros, transferencias, pago de servicios, recarga de celular, contactos, solicitudes de dinero, QR para cobrar y resumen de gastos.

## Autenticación, usuarios y perfiles (Preentrega 11)

- **Registro** (`/registro/`): formulario propio (`RegistroForm`, basado en `UserCreationForm`) con usuario, email y contraseña. Al guardar el `User`, la vista crea el `Perfil` explícitamente con `Perfil.objects.create(user=usuario)` — **no se usan signals**, tal como permite la consigna — y loguea a la persona automáticamente.
- **Login** (`/login/`) y **logout** (`/logout/`, por POST): usan las vistas nativas de Django (`LoginView`/`LogoutView`), con templates propios que mantienen el diseño del sitio.
- **Modelo `Perfil`** (`accounts/models.py`): `user` (`OneToOneField` a `User`), `biografia` (`TextField`), `link_web` (`URLField`, opcional) y `avatar` (`ImageField`, sube a `avatares/` dentro de `media/`).
- **Ver perfil** (`/perfil/`, protegida): muestra usuario, nombre, email, biografía y avatar (o un círculo con la inicial si todavía no subiste uno).
- **Editar perfil** (`/perfil/editar/`, protegida): un formulario para los datos del `User` (nombre, apellido, email) y otro para el `Perfil` (biografía, sitio web, avatar), en la misma página. Usa `Perfil.objects.get_or_create(user=request.user)` por si alguna vez accede un usuario sin perfil todavía (por ejemplo, un superusuario creado por `createsuperuser`). Procesa la imagen con `request.FILES`.
- **Rutas protegidas**: crear, editar, eliminar y gestionar posts (`/notas/crear/`, `/notas/<slug>/editar/`, `/notas/<slug>/eliminar/`, `/notas/gestionar/`) usan `@login_required(login_url='login')`. El listado (`/notas/`) y el detalle (`/notas/<slug>/`) siguen siendo públicos. Si entrás a una de esas URLs sin sesión iniciada, te redirige a `/login/?next=...` y, después de loguearte, te manda de vuelta a donde querías ir.
- **Navegación condicional**: el menú muestra "Iniciar sesión"/"Registrarse" si no estás logueado, o "Mi perfil"/"Crear post"/tu nombre de usuario/"Cerrar sesión" si lo estás.
- **Ojo:** este login (`/login/`) es el del **blog** (para escribir posts). La banca tiene su **propio** login en `/banca/ingresar/`, con verificación en dos pasos — son dos sistemas separados, aunque comparten el mismo modelo `User` de Django por debajo.

## CRUD de posts (Preentrega 10)

Las operaciones disponibles:

| Operación | Ruta | Descripción |
|---|---|---|
| Crear | `/notas/crear/` | Formulario (`PostForm`, un `ModelForm`) con título, resumen, contenido, autor, estado, ícono e imagen. |
| Leer (listado público) | `/notas/` | Solo posts publicados. |
| Leer (listado completo) | `/notas/gestionar/` | Todos los posts, cualquier estado. |
| Leer (detalle) | `/notas/<slug>/` | Muestra título, contenido, autor, estado e imagen (si tiene). Solo posts publicados. |
| Actualizar | `/notas/<slug>/editar/` | Mismo formulario que crear, precargado. Si no subís una imagen nueva, se conserva la que ya tenía. |
| Borrar | `/notas/<slug>/eliminar/` | Pide confirmación antes de borrar (GET muestra la confirmación, el borrado real es por POST). |

### Cómo se maneja la imagen

- El modelo tiene `imagen = models.ImageField(upload_to='posts/', null=True, blank=True)` — es opcional.
- Se necesita **Pillow** para que `ImageField` funcione (`pip install Pillow`, ya en `requirements.txt`).
- `MEDIA_URL` y `MEDIA_ROOT` están definidos en `settings.py`, y `blog_project/urls.py` sirve la carpeta `media/` mientras `DEBUG=True`.
- El formulario (`post_form.html`) tiene `enctype="multipart/form-data"`, imprescindible para que el archivo viaje al servidor.
- Las vistas de crear/editar instancian el formulario con `PostForm(request.POST, request.FILES)` (o `request.FILES, instance=post` al editar), para procesar tanto los campos de texto como el archivo.
- Si un post no tiene imagen, el template muestra su ícono (emoji) en vez de romper.

**Para probarlo:** registrate en `/registro/` (o logueate si ya tenés cuenta), entrá a `/notas/crear/`, completá el formulario y subí una imagen (cualquier `.jpg`/`.png`). Guardá como "Publicado" y mirá cómo aparece en `/notas/` y en el detalle del post. Las imágenes quedan en `media/posts/` (esa carpeta no se sube a GitHub, está en `.gitignore`).

## Estructura del proyecto Django

```
blog_consola/
├── manage.py
├── requirements.txt
├── .gitignore
├── blog_project/          (configuración del proyecto Django)
├── posts/                 (app del blog)
│   ├── models.py          (modelo Post, con imagen)
│   ├── forms.py           (PostForm, un ModelForm)
│   ├── admin.py           (PostAdmin: columnas de titulo, autor, estado y fecha)
│   ├── urls.py
│   ├── views.py           (listar, detalle, crear, editar, eliminar, gestionar)
│   ├── migrations/
│   ├── templates/posts/   (base.html, inicio.html, acerca.html, lista_posts.html,
│   │                        detalle_post.html, post_form.html, post_confirm_delete.html,
│   │                        gestionar_posts.html, ayuda.html, terminos.html, contacto.html)
│   └── static/posts/css/  (estilos.css)
├── accounts/               (registro, login, logout y perfil)
│   ├── models.py           (modelo Perfil)
│   ├── forms.py            (RegistroForm, PerfilForm, DatosUsuarioForm)
│   ├── admin.py
│   ├── urls.py
│   ├── views.py            (registro, perfil, editar_perfil)
│   └── templates/accounts/ (login.html, registro.html, perfil.html, editar_perfil.html,
│                             password_change.html, password_change_done.html)
└── banca/                 (app de banca online, con modelos y base de datos)
    ├── models.py, forms.py, views.py, urls.py
    ├── templates/banca/
    └── static/banca/css/
```

## Páginas y navegación

El sitio tiene un template base (`posts/templates/posts/base.html`) compartido por las tres apps, con el menú de navegación y el pie de página. De ahí heredan todos los templates usando `{% extends %}`.

## Tests automatizados

Cada app (`posts`, `accounts`, `banca`) tiene su `tests.py` con tests reales (`django.test.TestCase`), no scripts sueltos. Para correrlos todos:

```bash
python manage.py test
```

Usan una base de datos de prueba separada (se crea y se borra sola en cada corrida, no toca `db.sqlite3`) y los que suben imágenes usan un `MEDIA_ROOT` temporal, así que tampoco ensucian la carpeta `media/` real. Cubren, entre otras cosas: que el slug de un post se genere solo, que un borrador no sea visible por URL directa, que crear/editar/borrar posts sin estar logueado redirija al login, que el registro cree el `Perfil` sin signals, y varios de los flujos de la banca (transferencias, dólares, préstamos, plazo fijo, seguros).

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
