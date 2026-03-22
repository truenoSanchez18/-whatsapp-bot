"""
30 mensajes Duolingo-style para notificaciones diarias de Guerreros de Fuego.
Cada mensaje es único, motivacional, y dirige a acción concreta.
"""

YOUTUBE_URL = "https://youtube.com/@guerrerosdfisme"

# 30 mensajes únicos — rotan en ciclo
DAILY_MESSAGES = [
    "🔥 *¡Buenos días, Guerrero!*\nCada día que no prospectas, alguien más se queda con tu cliente. Hoy manda 5 mensajes. Solo 5. ¿Lo harás?",
    "⚡ *Un paso al día mueve montañas.*\nLa diferencia entre quien triunfa en Ismerely y quien no: consistencia. ¿Qué vas a hacer hoy por tu negocio?",
    "🎯 *Dato rápido:*\nEl 80% de las ventas ocurren después del 5to seguimiento. ¿A cuántas personas les has dado seguimiento esta semana?",
    "💡 *Tip del día:*\nNo hables del producto en el primer mensaje. Habla del PROBLEMA del prospecto. El producto es la solución, no la introducción.",
    "🚀 *¿Sabías esto?*\nLas personas no compran productos, compran transformaciones. ¿Cómo describes la transformación que ofreces?",
    "🔥 *Modo Guerrero: ACTIVADO*\nHoy es un buen día para hacer una venta. Ve tu canal de YouTube para la estrategia de la semana 👉 " + YOUTUBE_URL,
    "💪 *Recuerda por qué empezaste.*\nNo es por el dinero. Es por la libertad, la familia, el tiempo. Ese 'por qué' es tu combustible hoy.",
    "📱 *Ejercicio de hoy:*\nAbre tus conversaciones de WhatsApp. Encuentra a alguien que no ha respondido en 3+ días. Mándale un mensaje de seguimiento ahora.",
    "🌟 *Tu posición en el ranking depende de HOY.*\nCada acción cuenta. Cada mensaje enviado. Cada llamada hecha. ¿Qué nivel quieres alcanzar?",
    "⚡ *La verdad que nadie dice:*\nLos primeros 90 días son los más difíciles. Pero si los superas con consistencia, el negocio se vuelve exponencial.",
    "🎯 *Script de apertura que funciona:*\n'Hola [Nombre], ¿cómo estás? Vi que [algo de ellos]. ¿Tienes 5 minutos? Tengo algo para ti.' Pruébalo hoy.",
    "🔥 *Nuevo video en el canal:*\nEstamos subiendo contenido fresco para que aprendas las mejores estrategias. Dale amor 👉 " + YOUTUBE_URL,
    "💡 *La objeción más común: 'Está caro'*\nRespuesta: '¿Cuánto te cuesta NO resolver esto cada mes?' Luego espera. El silencio vende.",
    "🚀 *Guerrero, escucha esto:*\nTu red no crece sola. Necesita tu energía, tu visión, tu liderazgo. ¿Qué hiciste hoy por tu equipo?",
    "⭐ *Mindset del día:*\nNo estás vendiendo. Estás AYUDANDO a alguien a resolver un problema. Cambia ese enfoque y cambia tus resultados.",
    "💪 *Reto de 24 horas:*\nContacta a 3 personas nuevas hoy. No para vender. Solo para conocerlas y entender qué necesitan. Los mejores leads nacen de conversaciones reales.",
    "🔥 *El secreto de los top sellers:*\nDocumentan todo. Nombres, fechas, qué dijo el prospecto, cuándo hacer seguimiento. ¿Tienes tu sistema de seguimiento?",
    "🎯 *¿Cuántos prospectos tienes activos ahora mismo?*\nSi son menos de 20, hoy es el día para cambiar eso. Empieza con 5 mensajes nuevos.",
    "💡 *Tip de cierre:*\nEn lugar de preguntar '¿Qué piensas?', pregunta '¿Cuándo quieres empezar?' La segunda pregunta asume el cierre.",
    "⚡ *Contenido nuevo para ti:*\nAprendizaje constante = crecimiento constante. Mira el último video y aplica UNA cosa hoy 👉 " + YOUTUBE_URL,
    "🌟 *El mejor momento para actuar fue ayer.*\nEl segundo mejor momento es AHORA. No esperes el momento perfecto. Empieza con lo que tienes.",
    "💪 *Para los que dicen 'no tengo tiempo':*\nSon solo 30 minutos al día. 30 minutos de prospectar activamente puede cambiar tu realidad en 90 días.",
    "🔥 *Guerrero de la semana:*\nLos que más crecen en nuestra comunidad tienen algo en común: no se rinden en el primer 'no'. El 'no' los acerca al 'sí'.",
    "🎯 *Pregunta poderosa para hoy:*\n'¿Qué haría si supiera que no voy a fallar?' Respóndela honestamente y actúa como si esa respuesta fuera tu realidad.",
    "🚀 *Sistema de 3 pasos:*\n1) Prospecta a diario. 2) Da seguimiento sin rendirte. 3) Cierra con confianza. Simple, pero pocos lo aplican todos los días.",
    "💡 *La diferencia entre el éxito y el fracaso en Ismerely:*\nNo es el producto. No es el mercado. Eres TÚ y tu disposición a aprender y actuar.",
    "⭐ *Hoy es un buen día para una venta.*\nAbre el chat, elige un prospecto tibio, y manda un mensaje de seguimiento genuino. Así de simple.",
    "⚡ *Tu negocio es un reflejo de tu energía.*\nSi estás estancado, pregúntate: ¿Estoy haciendo lo suficiente? ¿Estoy aprendiendo lo suficiente? ¿Estoy rodeado de las personas correctas?",
    "🔥 *Únete a los Guerreros en vivo:*\nSeguimos el canal para que no te pierdas ningún entrenamiento. Activa la campanita 👉 " + YOUTUBE_URL,
    "💪 *Último mensaje de la serie:*\nLlevamos 30 días juntos. Lo que empieza como hábito se vuelve carácter. Sigue adelante, Guerrero. 🔥 El fuego no se apaga.",
]


LIVE_NOTIFICATION = """🔴 *¡ESTAMOS EN VIVO AHORA!* 🔴

Trueno Sánchez está transmitiendo en este momento en YouTube.

No te lo pierdas 👇
{url}

¡Únete ahora! 🔥"""


def get_daily_message(day: int) -> str:
    """Retorna el mensaje del día (cicla cada 30 días)."""
    return DAILY_MESSAGES[day % len(DAILY_MESSAGES)]


def get_live_message(live_url: str) -> str:
    return LIVE_NOTIFICATION.format(url=live_url)
