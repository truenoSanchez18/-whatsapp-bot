import json
import re
from pathlib import Path
from datetime import datetime, timedelta

from openai import OpenAI

from config import OPENAI_API_KEY, OPENAI_MODEL, PAYMENT_LINK
from database import get_conversation, save_conversation, schedule_followup
import notion_client as notion

# Cargar configuración del agente
_config_path = Path(__file__).parent / "skills" / "agent_config.json"
with open(_config_path, encoding="utf-8") as f:
    AGENT_CONFIG = json.load(f)

# Cargar catálogo de productos (para system prompt)
_catalog_path = Path(__file__).parent / "skills" / "catalog.json"
with open(_catalog_path, encoding="utf-8") as f:
    CATALOG = json.load(f)

# Cargar catálogo con imágenes (para envío de fotos de productos)
_images_path = Path(__file__).parent / "skills" / "catalogo_con_imagenes.json"
with open(_images_path, encoding="utf-8") as f:
    _CATALOG_IMAGES = json.load(f)

# Índice de imágenes: codigo -> url y nombre normalizado -> url
_IMAGE_BY_CODE: dict[str, str] = {}
_IMAGE_BY_NAME: dict[str, str] = {}

for _p in _CATALOG_IMAGES.get("productos", []):
    _url = _p.get("imagen_url", "")
    if not _url:
        continue
    _codes = _p.get("codigo", "")
    if isinstance(_codes, list):
        for _c in _codes:
            if _c:
                _IMAGE_BY_CODE[_c.upper()] = _url
    elif _codes:
        _IMAGE_BY_CODE[_codes.upper()] = _url
    _name_key = re.sub(r"\s+", " ", _p.get("nombre", "")).strip().upper()
    if _name_key:
        _IMAGE_BY_NAME[_name_key] = _url

client = OpenAI(api_key=OPENAI_API_KEY)


def get_product_image(product_code_or_name: str) -> str | None:
    """Busca la imagen de un producto por código o nombre."""
    key = product_code_or_name.strip().upper()
    if key in _IMAGE_BY_CODE:
        return _IMAGE_BY_CODE[key]
    # Búsqueda parcial por nombre
    for name_key, url in _IMAGE_BY_NAME.items():
        if key in name_key or name_key in key:
            return url
    return None


def _build_catalog_text() -> str:
    """Construye el texto del catálogo para incluir en el system prompt."""
    lines = ["=== CATÁLOGO COMPLETO DE PRODUCTOS ==="]
    lines.append("Cuando el cliente pregunte por precio, producto o necesidad, usa ESTE catálogo exacto.\n")
    for cat_key, cat_data in CATALOG["categories"].items():
        lines.append(f"▸ {cat_data['description'].upper()}")
        lines.append(f"  Palabras clave: {', '.join(cat_data['keywords'])}")
        for p in cat_data["products"]:
            lines.append(f"  • {p['name']} — Precio público: ${p['precio_publico']} MXN | Precio socio: ${p['precio_socio']} MXN")
            lines.append(f"    Beneficio: {p['benefit']}")
        lines.append("")
    lines.append("INSTRUCCIÓN: Cuando el usuario mencione una necesidad, busca en las palabras clave la categoría correcta y recomienda 1-2 productos de esa categoría con su precio.")
    return "\n".join(lines)


def _build_system_prompt(state: dict) -> str:
    name = state.get("name", "")
    intent = state.get("intent_route", "")
    temperature = state.get("lead_temperature", "")
    need = state.get("need_or_motivation", "")
    status = state.get("conversation_status", "new")
    follow_up_count = state.get("follow_up_count", 0)
    payment_sent = state.get("payment_link_sent", False)
    handoff = state.get("human_handoff_requested", False)

    return f"""Eres un agente de ventas profesional por WhatsApp. Tu nombre es Valeria y trabajas para un negocio que vende productos físicos de bienestar y tiene una oportunidad de afiliación MLM.

=== REGLAS ESENCIALES ===
- Responde SIEMPRE en español (o en el idioma que use el usuario)
- Usa un tono humano, cálido, claro y persuasivo sin presionar
- Mensajes cortos (máximo 3-4 líneas por mensaje)
- Usa 1-3 emojis por mensaje cuando sea natural: 😊 🙌 ✨ 🔥 🌿 💬 💡 🛒 📦 📲 🚀 🤝
- Haz UNA sola pregunta por mensaje
- Usa palabras conectoras: "claro", "perfecto", "entiendo", "con gusto", "te acompaño"
- NUNCA inventes beneficios médicos ni prometas curas
- NUNCA mandes párrafos enormes
- NUNCA presiones al prospecto

=== FLUJO DE VENTAS (sigue este orden) ===
1. BIENVENIDA: Si es contacto nuevo, preguntar el nombre
2. NOMBRE: Guardar nombre y hacer 3 preguntas estratégicas
3. PREGUNTA 1 (intención): ¿Busca producto, negocio MLM, o ambos?
4. PREGUNTA 2: Según la ruta - necesidad del producto O motivación del negocio
5. PREGUNTA 3: Nivel de urgencia/disposición
6. CLASIFICACIÓN: Asignar temperatura (hot/warm/cold/risk)
7. RECOMENDACIÓN: Ofrecer solución concreta según la necesidad
8. CIERRE: Según temperatura - cierre directo, consultivo o de opciones
9. PAGO: Si acepta, compartir link de Mercado Pago
10. SEGUIMIENTO: Si no cierra, agendar follow-up

=== ESTADO ACTUAL DEL PROSPECTO ===
- Nombre: {name if name else "no capturado aún"}
- Ruta de interés: {intent if intent else "no detectada aún"}
- Temperatura: {temperature if temperature else "no clasificada"}
- Necesidad/motivación: {need if need else "no capturada"}
- Estado conversación: {status}
- Follow-ups enviados: {follow_up_count}
- Link de pago enviado: {"sí" if payment_sent else "no"}
- Transferencia a humano solicitada: {"sí" if handoff else "no"}

=== LINK DE PAGO ===
Cuando el prospecto confirme que quiere comprar, usa este link:
{PAYMENT_LINK}

=== CUÁNDO ESCALAR A HUMANO ===
- El usuario pide hablar con una persona
- Hay molestia, fricción o desconfianza fuerte
- Preguntas médicas delicadas
- Objeciones que no puedes resolver
- Tono confrontativo

=== CUÁNDO CERRAR CONVERSACIÓN ===
- Después de 2 follow-ups sin respuesta
- El usuario dice que no le interesa
- Después de completar la venta

=== RECOMENDACIÓN DE COMBOS (MUY IMPORTANTE) ===
Cuando el cliente mencione una necesidad específica, recomienda 2-3 productos complementarios que trabajen juntos:
- Bajar de peso + digestión: FT-ELYM CAPS + DG BRAN + MY BELLY CAPS
- Bajar de peso + energía: FT-ELYM PRO CAPS + ORIGEN CAFÉ + MY REVENUE
- Articulaciones + inflamación: FTX + OMG 369 + MY GS-TREL
- Estrés + sueño: MY MAHAL + S-MN + MY ST-MORY
- Diabéticos / azúcar: MY SUKER + SUKER JUICE + FT-ELYM DTOX
- Detox completo: FT-ELYM DTOX + MY LIVE-T + BE GREEN
- Piel + colágeno: SERUM VITAMINA C + ADN VEGETAL + COLÁGENO + ELASTINA
- Energía + rendimiento: ORIGEN CAFÉ + VYBES PRANA + INTENS-MN
- Inmunidad: AG COLOIDAL + X-PRO + REVEN-VIT
Presenta el combo como "protocolo" o "kit" — siempre con precio y beneficio claro de cada uno.

=== CLASIFICACIÓN DE INTENCIÓN ===
Al final de tu respuesta incluye AMBAS líneas (NO las muestre al usuario):
[STATE: intent_route=product|business|both, lead_temperature=hot|warm|cold|risk, name=NombreDelProspecto, need=ResumenNecesidad, status=active|closed|human_handoff|follow_up_scheduled]
[RECOMMEND: CODIGO1,CODIGO2] ← solo cuando recomiendes productos concretos, usa los códigos PT7XX. Si no hay recomendación esta línea no va.

Solo incluye los campos que tengas información para actualizar.

Responde SOLAMENTE con el mensaje para el prospecto (más las líneas STATE/RECOMMEND). Sin explicaciones extras.

{_build_catalog_text()}"""


def _parse_state_update(response_text: str) -> tuple[str, dict, list[str]]:
    """Retorna (mensaje_limpio, state_updates, lista_de_codigos_recomendados)."""
    state_updates = {}
    recommended_codes = []
    clean_message = response_text

    # Extraer [RECOMMEND: ...] primero
    recommend_match = re.search(r"\[RECOMMEND:\s*([^\]]+)\]", response_text)
    if recommend_match:
        codes_raw = recommend_match.group(1)
        recommended_codes = [c.strip() for c in codes_raw.split(",") if c.strip()]
        response_text = response_text.replace(recommend_match.group(0), "").strip()

    if "[STATE:" in response_text:
        parts = response_text.split("[STATE:")
        clean_message = parts[0].strip()
        state_raw = parts[1].rstrip("]").strip()

        for item in state_raw.split(","):
            item = item.strip()
            if "=" in item:
                key, value = item.split("=", 1)
                state_updates[key.strip()] = value.strip()
    else:
        clean_message = response_text.strip()

    return clean_message, state_updates, recommended_codes


def _should_send_payment_link(message: str, state: dict) -> bool:
    closing_triggers = AGENT_CONFIG["trigger_system"]["closing_triggers"]
    msg_lower = message.lower()
    return (
        state.get("lead_temperature") == "hot"
        and not state.get("payment_link_sent")
        and any(trigger in msg_lower for trigger in closing_triggers)
    )


def _should_handoff(message: str) -> bool:
    handoff_triggers = AGENT_CONFIG["trigger_system"]["human_handoff_triggers"]
    friction_triggers = AGENT_CONFIG["trigger_system"]["friction_triggers"]
    msg_lower = message.lower()
    return any(t in msg_lower for t in handoff_triggers + friction_triggers)


async def process_message(phone: str, user_message: str) -> list[str]:
    state = get_conversation(phone)
    responses = []

    if state.get("human_handoff_requested"):
        return []

    if state.get("conversation_status") == "closed":
        state["conversation_status"] = "active"

    if _should_handoff(user_message):
        state["human_handoff_requested"] = True
        state["conversation_status"] = "human_handoff"
        save_conversation(phone, state)
        name = state.get("name", "")
        return [AGENT_CONFIG["sales_flow"]["step_9_human_handoff"]["handoff_message_template"].replace("{name}", name)]

    history = state.get("history", [])
    history.append({"role": "user", "content": user_message, "ts": datetime.utcnow().isoformat()})

    if len(history) > 20:
        history = history[-20:]
    state["history"] = history

    system_prompt = _build_system_prompt(state)

    # Construir mensajes para OpenAI
    messages = [{"role": "system", "content": system_prompt}]
    for msg in history[:-1]:
        role = "user" if msg["role"] == "user" else "assistant"
        messages.append({"role": role, "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    # Llamar a OpenAI
    print(f"Llamando a OpenAI con modelo {OPENAI_MODEL}...")
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        temperature=0.7,
        max_tokens=500,
    )
    raw_response = response.choices[0].message.content
    print(f"Respuesta OpenAI: {raw_response[:100]}")

    clean_message, state_updates, recommended_codes = _parse_state_update(raw_response)

    if "intent_route" in state_updates:
        state["intent_route"] = state_updates["intent_route"]
    if "lead_temperature" in state_updates:
        state["lead_temperature"] = state_updates["lead_temperature"]
    if "name" in state_updates and state_updates["name"] and not state.get("name"):
        state["name"] = state_updates["name"]
    if "need" in state_updates:
        state["need_or_motivation"] = state_updates["need"]
    if "status" in state_updates:
        state["conversation_status"] = state_updates["status"]
    if recommended_codes:
        state["recommended_offer"] = ", ".join(recommended_codes)

    history.append({"role": "assistant", "content": clean_message, "ts": datetime.utcnow().isoformat()})
    state["history"] = history
    state["last_message_summary"] = user_message[:100]

    responses.append(clean_message)

    # Enviar imagen(es) del/los producto(s) recomendado(s)
    sent_urls = set()
    for code in recommended_codes[:2]:  # máximo 2 imágenes
        img_url = get_product_image(code)
        if img_url and img_url not in sent_urls:
            responses.append({"type": "image", "url": img_url, "caption": ""})
            sent_urls.add(img_url)

    if _should_send_payment_link(user_message, state):
        name = state.get("name", "")
        payment_msg = (
            AGENT_CONFIG["sales_flow"]["step_7_payment"]["payment_message_template"]
            .replace("{name}", name)
            .replace("{payment_link}", PAYMENT_LINK or "[link pendiente]")
        )
        responses.append(payment_msg)
        state["payment_link_sent"] = True

    if state.get("conversation_status") in ("follow_up_scheduled", "closed"):
        follow_up_count = state.get("follow_up_count", 0)
        if follow_up_count < 2:
            scheduled = datetime.utcnow() + timedelta(days=3)
            schedule_followup(phone, f"follow_up_{follow_up_count + 1}", scheduled)
        reactivation_time = datetime.utcnow() + timedelta(hours=24)
        schedule_followup(phone, "reactivation", reactivation_time)

    save_conversation(phone, state)

    # Sincronizar con Notion CRM (sin bloquear si falla)
    try:
        await notion.upsert_prospect({"phone": phone, **state})
    except Exception as e:
        print(f"Notion sync error: {e}")

    return responses


def build_followup_message(phone: str, followup_type: str) -> str | None:
    state = get_conversation(phone)
    name = state.get("name", "")
    interest = state.get("need_or_motivation", "") or state.get("intent_route", "nuestros productos")

    templates = AGENT_CONFIG["sales_flow"]["step_8_follow_up"]

    if followup_type == "reactivation":
        return templates["reactivation_followup"]["message"].replace("{name}", name)
    elif followup_type == "follow_up_1":
        return templates["follow_up_templates"]["follow_up_1"].replace("{name}", name).replace("{interest_summary}", interest)
    elif followup_type == "follow_up_2":
        return templates["follow_up_templates"]["follow_up_2"].replace("{name}", name).replace("{interest_summary}", interest)

    return None
