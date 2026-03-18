import httpx
from datetime import date

from config import NOTION_API_KEY
NOTION_DB_ID = "1b14b647-b1bb-80f9-9341-cef181ed6234"
NOTION_VERSION = "2022-06-28"


def _headers():
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


async def upsert_prospect(state: dict):
    """
    Crea o actualiza un prospecto en Notion.
    Busca por número de WhatsApp — si existe lo actualiza, si no lo crea.
    """
    phone = state.get("phone", "")
    name = state.get("name", "") or "Sin nombre"
    status = _map_status(state.get("conversation_status", "new"))
    notes = _build_notes(state)
    today = date.today().isoformat()

    existing_id = await _find_prospect_by_phone(phone)

    if existing_id:
        await _update_prospect(existing_id, name, status, notes, today)
    else:
        await _create_prospect(phone, name, status, notes, today)


def _map_status(conversation_status: str) -> str:
    mapping = {
        "new": "Nuevo",
        "active": "Interesado",
        "follow_up_scheduled": "En Seguimiento",
        "human_handoff": "En Seguimiento",
        "closed": "No Interesado",
        "sold": "Cerrado",
    }
    return mapping.get(conversation_status, "Nuevo")


def _build_notes(state: dict) -> str:
    parts = []
    if state.get("intent_route"):
        route_map = {"product": "Productos", "business": "Negocio MLM", "both": "Ambos"}
        parts.append(f"Interés: {route_map.get(state['intent_route'], state['intent_route'])}")
    if state.get("need_or_motivation"):
        parts.append(f"Necesidad: {state['need_or_motivation']}")
    if state.get("lead_temperature"):
        temp_map = {"hot": "🔥 Caliente", "warm": "🌡 Tibio", "cold": "❄ Frío", "risk": "⚠ Riesgo"}
        parts.append(f"Temperatura: {temp_map.get(state['lead_temperature'], state['lead_temperature'])}")
    if state.get("recommended_offer"):
        parts.append(f"Recomendación dada: {state['recommended_offer']}")
    if state.get("payment_link_sent"):
        parts.append("✅ Link de pago enviado")
    if state.get("human_handoff_requested"):
        parts.append("🤝 Escalado a humano")
    if state.get("last_message_summary"):
        parts.append(f"Último mensaje: {state['last_message_summary']}")
    return " | ".join(parts) if parts else "Sin notas"


async def _find_prospect_by_phone(phone: str) -> str | None:
    url = f"https://api.notion.com/v1/databases/{NOTION_DB_ID}/query"
    payload = {
        "filter": {
            "property": "Numero de WhatsApp",
            "phone_number": {"equals": f"+{phone}"}
        }
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(url, json=payload, headers=_headers())
        if resp.status_code == 200:
            results = resp.json().get("results", [])
            if results:
                return results[0]["id"]
    return None


async def _create_prospect(phone: str, name: str, status: str, notes: str, today: str):
    url = "https://api.notion.com/v1/pages"
    payload = {
        "parent": {"database_id": NOTION_DB_ID},
        "properties": {
            "Nombre": {"title": [{"text": {"content": name}}]},
            "Estado": {"status": {"name": status}},
            "Numero de WhatsApp": {"phone_number": f"+{phone}"},
            "Enlace de WhatsApp": {"url": f"https://wa.me/{phone}"},
            "Fecha de Contacto": {"date": {"start": today}},
            "Ultimo Seguimiento": {"date": {"start": today}},
            "Notas": {"rich_text": [{"text": {"content": notes}}]},
        }
    }
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(url, json=payload, headers=_headers())


async def _update_prospect(page_id: str, name: str, status: str, notes: str, today: str):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    payload = {
        "properties": {
            "Estado": {"status": {"name": status}},
            "Ultimo Seguimiento": {"date": {"start": today}},
            "Notas": {"rich_text": [{"text": {"content": notes}}]},
        }
    }
    # Actualizar nombre solo si ya se capturó
    if name and name != "Sin nombre":
        payload["properties"]["Nombre"] = {"title": [{"text": {"content": name}}]}

    async with httpx.AsyncClient(timeout=10) as client:
        await client.patch(url, json=payload, headers=_headers())
