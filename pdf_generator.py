"""
Genera los PDFs de lead magnets para Guerreros de Fuego ISME.
Se ejecuta al iniciar el servidor y guarda los PDFs en lead_magnets/
"""
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, white
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT

OUTPUT_DIR = Path(__file__).parent / "lead_magnets"
OUTPUT_DIR.mkdir(exist_ok=True)

FIRE_RED = HexColor("#E63946")
DARK = HexColor("#1D1D2C")
GOLD = HexColor("#F4A261")
LIGHT_GRAY = HexColor("#F8F8F8")

def _base_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("GFTitle", fontSize=26, textColor=white,
        fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=6))
    styles.add(ParagraphStyle("GFSubtitle", fontSize=13, textColor=GOLD,
        fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=20))
    styles.add(ParagraphStyle("GFHeading", fontSize=14, textColor=FIRE_RED,
        fontName="Helvetica-Bold", spaceBefore=16, spaceAfter=6))
    styles.add(ParagraphStyle("GFBody", fontSize=11, textColor=DARK,
        fontName="Helvetica", spaceAfter=8, leading=16))
    styles.add(ParagraphStyle("GFBullet", fontSize=11, textColor=DARK,
        fontName="Helvetica", spaceAfter=6, leftIndent=20, leading=15))
    styles.add(ParagraphStyle("GFFooter", fontSize=9, textColor=HexColor("#888888"),
        fontName="Helvetica", alignment=TA_CENTER))
    return styles


def _header_block(title: str, subtitle: str, styles) -> list:
    header_data = [[Paragraph(f"<b>{title}</b>", styles["GFTitle"]),
                    Paragraph(subtitle, styles["GFSubtitle"])]]
    t = Table(header_data, colWidths=[6.5 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), DARK),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 24),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 24),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
        ("ROUNDEDCORNERS", (0, 0), (-1, -1), 8),
    ]))
    return [t, Spacer(1, 0.3 * inch)]


def _footer(styles) -> list:
    return [
        Spacer(1, 0.3 * inch),
        Paragraph("🔥 Guerreros de Fuego ISME  |  @guerrerosdfisme  |  youtube.com/@guerrerosdfisme", styles["GFFooter"]),
    ]


# ─── PDF 1: 5 Errores ────────────────────────────────────────────────────────
def generate_pdf_errores():
    path = OUTPUT_DIR / "5_errores_ismerely.pdf"
    doc = SimpleDocTemplate(str(path), pagesize=letter,
                            leftMargin=inch, rightMargin=inch,
                            topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    styles = _base_styles()
    story = []

    story += _header_block(
        "🔥 LOS 5 ERRORES QUE MATAN TU NEGOCIO ISMERELY",
        "Guerreros de Fuego ISME — Guía Gratuita"
    , styles)

    story.append(Paragraph("Introducción", styles["GFHeading"]))
    story.append(Paragraph(
        "La mayoría de las personas que entran a Ismerely cometen los mismos errores una y otra vez. "
        "No porque sean malos, sino porque nadie les enseñó la forma correcta. "
        "Este documento te muestra los 5 errores más comunes y cómo evitarlos desde hoy.",
        styles["GFBody"]))

    errores = [
        ("❌ Error #1: Hablarle a todo el mundo",
         "Muchos piensan que mientras más personas contacten, más venderán. Error. "
         "Hablarle a personas sin perfil definido solo genera rechazos y desgaste. "
         "Solución: define tu prospecto ideal — edad, problema que tiene, qué busca — y habla solo con esas personas."),
        ("❌ Error #2: Empezar por el producto, no por el dolor",
         "Decir 'tengo un producto increíble' antes de entender qué le duele al prospecto es vender en el vacío. "
         "Solución: siempre pregunta primero. ¿Qué problema tienes? ¿Qué has intentado? Luego presenta el producto como la solución."),
        ("❌ Error #3: No hacer seguimiento",
         "El 80% de las ventas ocurren después del 5to contacto. La mayoría se rinde en el primero. "
         "Solución: usa un sistema de seguimiento con fechas y notas. Un 'no' hoy puede ser un 'sí' en 3 semanas."),
        ("❌ Error #4: Copiar y pegar mensajes genéricos",
         "Los mensajes masivos se ven a kilómetros. La gente los ignora o bloquea. "
         "Solución: personaliza cada mensaje con el nombre y algo específico de la persona. Tarda 30 segundos más y duplica la respuesta."),
        ("❌ Error #5: No invertir en tu propio desarrollo",
         "Tu negocio crece hasta donde tú creciste. Si no aprendes nuevas habilidades, tu ingreso se estanca. "
         "Solución: dedica mínimo 20 minutos al día a aprender — videos, libros, comunidades como Guerreros de Fuego."),
    ]

    for titulo, desc in errores:
        story.append(Paragraph(titulo, styles["GFHeading"]))
        story.append(Paragraph(desc, styles["GFBody"]))

    story.append(Paragraph("Próximo Paso", styles["GFHeading"]))
    story.append(Paragraph(
        "Únete a nuestra comunidad en YouTube @guerrerosdfisme donde publicamos estrategias semanales, "
        "casos de éxito y entrenamiento en vivo para llevar tu negocio al siguiente nivel.",
        styles["GFBody"]))

    story += _footer(styles)
    doc.build(story)
    return path


# ─── PDF 2: Guía 7 Días ──────────────────────────────────────────────────────
def generate_pdf_7dias():
    path = OUTPUT_DIR / "guia_7dias_primera_venta.pdf"
    doc = SimpleDocTemplate(str(path), pagesize=letter,
                            leftMargin=inch, rightMargin=inch,
                            topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    styles = _base_styles()
    story = []

    story += _header_block(
        "🗓 GUÍA DE 7 DÍAS PARA TU PRIMERA VENTA",
        "El Plan Exacto — Guerreros de Fuego ISME"
    , styles)

    dias = [
        ("DÍA 1 — Define tu prospecto ideal",
         "Escribe en papel: ¿A quién le vas a vender? Edad, situación económica, problema principal. "
         "Haz una lista de 20 personas de tu contactos que encajen con ese perfil."),
        ("DÍA 2 — Prepara tu mensaje de apertura",
         "Escribe un mensaje de 3 líneas: saludo personalizado + pregunta sobre su situación + propuesta de valor. "
         "NO menciones el producto todavía. Ejemplo: 'Hola Ana, ¿cómo estás? Vi que buscas formas de mejorar tu salud, ¿tienes 5 minutos?'"),
        ("DÍA 3 — Contacta a 10 personas",
         "Manda el mensaje a las primeras 10 personas de tu lista. "
         "No copies y pegues — personaliza cada uno con el nombre. Registra quién respondió."),
        ("DÍA 4 — Haz las preguntas correctas",
         "A los que respondieron, haz 3 preguntas: ¿Qué problema tienes? ¿Qué has intentado? ¿Qué tan urgente es para ti resolverlo? "
         "Escucha más de lo que hablas."),
        ("DÍA 5 — Presenta la solución",
         "Basándote en lo que dijeron, presenta el producto como LA solución a SU problema específico. "
         "Usa sus propias palabras: 'Mencionaste que tienes X problema, este producto ayuda exactamente con eso porque...'"),
        ("DÍA 6 — Maneja la objeción más común",
         "La objeción más frecuente es el precio. Respuesta: '¿Cuánto te cuesta NO resolver este problema cada mes?' "
         "Luego compara ese costo con el del producto. Generalmente el producto es más barato."),
        ("DÍA 7 — Cierra y contacta a los otros 10",
         "Pide el cierre directo: '¿Empezamos hoy?' o '¿Te envío el link de pago?' "
         "Luego contacta a las otras 10 personas de tu lista. La primera venta siempre es la más difícil — después viene sola."),
    ]

    for titulo, desc in dias:
        story.append(Paragraph(titulo, styles["GFHeading"]))
        story.append(Paragraph(desc, styles["GFBody"]))

    story.append(Paragraph("Recuerda", styles["GFHeading"]))
    story.append(Paragraph(
        "La consistencia gana a la perfección. No necesitas el mensaje perfecto ni el producto perfecto. "
        "Necesitas acción diaria. Únete a @guerrerosdfisme para recibir entrenamiento semanal y apoyo de la comunidad.",
        styles["GFBody"]))

    story += _footer(styles)
    doc.build(story)
    return path


# ─── PDF 3: Script de WhatsApp ────────────────────────────────────────────────
def generate_pdf_script():
    path = OUTPUT_DIR / "script_whatsapp_cierre.pdf"
    doc = SimpleDocTemplate(str(path), pagesize=letter,
                            leftMargin=inch, rightMargin=inch,
                            topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    styles = _base_styles()
    story = []

    story += _header_block(
        "💬 SCRIPT DE WHATSAPP QUE CIERRA EN 3 MENSAJES",
        "Conversaciones que Convierten — Guerreros de Fuego ISME"
    , styles)

    story.append(Paragraph(
        "Este script fue probado en cientos de conversaciones reales. "
        "Funciona porque no vende — conecta primero, luego cierra.",
        styles["GFBody"]))

    scripts = [
        ("MENSAJE 1 — La Apertura (Día 0)",
         "Hola [Nombre] 👋 ¿Cómo estás? Te escribo porque sé que [menciona algo específico de su situación]. "
         "¿Tienes 5 minutos? Tengo algo que creo que te puede interesar mucho.",
         "Objetivo: lograr que respondan. No vendas nada todavía."),
        ("MENSAJE 2 — El Diagnóstico (Si responden)",
         "Qué bueno que me respondiste 😊 Cuéntame, ¿cuál es tu mayor reto ahorita con [tema: salud/negocio/etc]? "
         "Porque dependiendo de lo que me digas, tengo algo específico para ti.",
         "Objetivo: que te cuenten su dolor. Escucha y guarda esa información."),
        ("MENSAJE 3 — La Solución y el Cierre",
         "Entiendo perfectamente, [repite su problema con sus palabras]. Justo por eso quiero presentarte [producto]. "
         "Ha ayudado a [número] personas con exactamente lo mismo. El precio es $[X] y puedes empezar hoy mismo. "
         "¿Te envío el link para que lo veas? 🔥",
         "Objetivo: cierre directo. Si dicen que necesitan pensarlo, programa seguimiento en 48h."),
    ]

    for titulo, script, objetivo in scripts:
        story.append(Paragraph(titulo, styles["GFHeading"]))
        data = [[Paragraph(f'"{script}"', styles["GFBody"])]]
        t = Table(data, colWidths=[6 * inch])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GRAY),
            ("TOPPADDING", (0, 0), (-1, -1), 12),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ("LEFTPADDING", (0, 0), (-1, -1), 16),
            ("RIGHTPADDING", (0, 0), (-1, -1), 16),
            ("LINEABOVE", (0, 0), (-1, 0), 2, FIRE_RED),
        ]))
        story.append(t)
        story.append(Paragraph(f"✅ {objetivo}", styles["GFBullet"]))
        story.append(Spacer(1, 0.1 * inch))

    story.append(Paragraph("Manejo de Objeciones Rápido", styles["GFHeading"]))
    objeciones = [
        ("'Está muy caro'", "¿Cuánto gastas en [problema] al mes? Este producto cuesta menos que eso."),
        ("'Voy a pensarlo'", "Claro, ¿qué es lo que más dudas tienes? Lo resolvemos ahorita."),
        ("'No tengo tiempo'", "Es justo por eso que te recomiendo esto — te ahorra tiempo a largo plazo."),
        ("'No me interesa'", "Sin problema 😊 ¿Hay algo más que te pueda ayudar?"),
    ]
    for obj, resp in objeciones:
        story.append(Paragraph(f"<b>{obj}</b> → {resp}", styles["GFBullet"]))

    story += _footer(styles)
    doc.build(story)
    return path


LEAD_MAGNETS = {
    "errores": {
        "file": "5_errores_ismerely.pdf",
        "generator": generate_pdf_errores,
        "title": "Los 5 Errores que Matan tu Negocio Ismerely",
        "emoji": "❌",
    },
    "7dias": {
        "file": "guia_7dias_primera_venta.pdf",
        "generator": generate_pdf_7dias,
        "title": "Guía de 7 Días para tu Primera Venta",
        "emoji": "🗓",
    },
    "script": {
        "file": "script_whatsapp_cierre.pdf",
        "generator": generate_pdf_script,
        "title": "Script de WhatsApp que Cierra en 3 Mensajes",
        "emoji": "💬",
    },
}


def generate_all():
    """Genera todos los PDFs si no existen ya."""
    for key, meta in LEAD_MAGNETS.items():
        path = OUTPUT_DIR / meta["file"]
        if not path.exists():
            print(f"Generando PDF: {meta['title']}...")
            meta["generator"]()
            print(f"  → {path}")
        else:
            print(f"PDF ya existe: {meta['file']}")


if __name__ == "__main__":
    generate_all()
