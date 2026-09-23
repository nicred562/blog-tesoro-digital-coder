"""
Posts del blog, escritos a mano en una lista de diccionarios (sin base de
datos ni modelos, como pide todavia el checkpoint). El dia que el proyecto
sume modelos, esta lista es la que se va a migrar a la base de datos.
"""

from datetime import date

POSTS = [
    {
        "slug": "abrir-cuenta-en-minutos",
        "titulo": "Cómo abrir tu cuenta en Tesoro Digital en 5 minutos",
        "resumen": "El paso a paso para crear tu cuenta desde la app: validación de identidad, alta de usuario y primer ingreso.",
        "contenido": (
            "Abrir una cuenta en Tesoro Digital lleva menos de lo que tarda un café. "
            "Solo necesitás tu nombre, un usuario y una contraseña. Una vez creada la cuenta, "
            "te generamos automáticamente un número de cuenta, un CBU y un alias para que puedas "
            "recibir transferencias desde el primer minuto.\n\n"
            "No hace falta que subas ningún documento ni que esperes aprobación: la cuenta queda "
            "lista al toque para que empieces a moverte."
        ),
        "autor": {"nombre": "Nicolás Sosa", "rol": "Equipo de Producto"},
        "tags": ["cuentas", "tutorial"],
        "fecha": date(2026, 1, 12),
        "icono": "🏦",
    },
    {
        "slug": "ahorro-para-principiantes",
        "titulo": "Ahorro para principiantes: cómo armar tu fondo de emergencia",
        "resumen": "Cuánto guardar, dónde tenerlo y cómo automatizarlo para no tener que pensarlo todos los meses.",
        "contenido": (
            "La regla más simple para empezar a ahorrar es separar la plata apenas la cobrás, "
            "no al final del mes cuando ya no queda nada. Un objetivo razonable para arrancar "
            "es guardar entre el 10% y el 20% de tus ingresos.\n\n"
            "En Tesoro Digital, cualquier saldo que dejes en la cuenta va generando un rendimiento "
            "diario, así que tu fondo de emergencia no se queda parado: crece solo mientras lo tenés guardado."
        ),
        "autor": {"nombre": "Ana López", "rol": "Educación Financiera"},
        "tags": ["ahorro", "finanzas personales"],
        "fecha": date(2026, 1, 20),
        "icono": "💡",
    },
    {
        "slug": "transferencias-instantaneas",
        "titulo": "Transferencias instantáneas: alias, CBU o número de cuenta",
        "resumen": "Repasamos las tres formas de mandar plata en Tesoro Digital y cuándo conviene usar cada una.",
        "contenido": (
            "Podés transferirle a otra cuenta de Tesoro Digital de tres formas: con su alias "
            "(algo fácil de recordar, tipo rio.sol.tesoro), con su CBU completo, o con su número "
            "de cuenta interno. Las tres llegan igual de rápido, así que usá la que tengas más a mano.\n\n"
            "Un consejo: si transferís seguido a la misma persona, guardala como contacto para no "
            "tener que volver a escribir el alias cada vez."
        ),
        "autor": {"nombre": "Nicolás Sosa", "rol": "Equipo de Producto"},
        "tags": ["transferencias", "tutorial"],
        "fecha": date(2026, 2, 2),
        "icono": "🔁",
    },
    {
        "slug": "seguridad-de-tu-cuenta",
        "titulo": "Seguridad: cómo protegemos tu cuenta de fraudes y phishing",
        "resumen": "Verificación en dos pasos, contraseñas encriptadas y qué hacer si sospechás de un mensaje falso.",
        "contenido": (
            "Nunca te vamos a pedir tu contraseña ni el código de verificación por WhatsApp, "
            "teléfono o redes sociales. Si alguien te lo pide diciendo que es de Tesoro Digital, es un fraude.\n\n"
            "Tu contraseña nunca se guarda en texto plano: la encriptamos apenas la creás. Y cada vez "
            "que iniciás sesión, te pedimos un código extra antes de mostrarte tu cuenta. Podés leer más "
            "detalles en la sección de Seguridad del sitio."
        ),
        "autor": {"nombre": "Carlos Fernández", "rol": "Seguridad"},
        "tags": ["seguridad"],
        "fecha": date(2026, 2, 10),
        "icono": "🛡️",
    },
    {
        "slug": "tarjetas-2026",
        "titulo": "Tarjetas 2026: qué debés saber antes de elegir una",
        "resumen": "Débito, crédito y prepagas: costos, beneficios y límites a tener en cuenta este año.",
        "contenido": (
            "Tu cuenta de Tesoro Digital ya incluye una tarjeta virtual, lista para usar apenas te registrás. "
            "Podés verla completa (número, vencimiento) desde tu perfil, y bloquearla al instante desde el "
            "panel si alguna vez la necesitás desactivar por un rato.\n\n"
            "Como es una tarjeta de ejemplo, no tiene costo de mantenimiento ni límites de gasto: es solo "
            "para que veas cómo se integraría una tarjeta real en la experiencia de la app."
        ),
        "autor": {"nombre": "Ana López", "rol": "Educación Financiera"},
        "tags": ["tarjetas"],
        "fecha": date(2026, 2, 18),
        "icono": "💳",
    },
]


def obtener_posts():
    """Devuelve todos los posts, mas nuevos primero."""
    return sorted(POSTS, key=lambda post: post["fecha"], reverse=True)


def obtener_post(slug):
    """Busca un post por su slug. Devuelve None si no existe."""
    for post in POSTS:
        if post["slug"] == slug:
            return post
    return None
