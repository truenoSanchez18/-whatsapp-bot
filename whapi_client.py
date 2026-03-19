import io
import httpx
from openai import OpenAI
from config import WHAPI_API_KEY, WHAPI_BASE_URL, OPENAI_API_KEY


HEADERS = {
    "Authorization": f"Bearer {WHAPI_API_KEY}",
    "Content-Type": "application/json",
}

_openai = OpenAI(api_key=OPENAI_API_KEY)


async def transcribe_audio(media_url: str) -> str:
    """
    Descarga un audio de Whapi y lo transcribe con Whisper.
    Retorna el texto transcrito o un mensaje de error descriptivo.
    """
    try:
        # Descargar el audio desde Whapi
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                media_url,
                headers={"Authorization": f"Bearer {WHAPI_API_KEY}"},
            )
            resp.raise_for_status()
            audio_bytes = resp.content

        # Transcribir con Whisper
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "audio.ogg"
        result = _openai.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="es",
        )
        return result.text.strip()

    except Exception as e:
        print(f"Error transcribiendo audio: {e}")
        return ""


async def send_text(phone: str, message: str):
    """Envía un mensaje de texto a un número de WhatsApp."""
    url = f"{WHAPI_BASE_URL}/messages/text"
    payload = {
        "to": phone,
        "body": message,
    }
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(url, json=payload, headers=HEADERS)
        response.raise_for_status()
        return response.json()


async def send_image(phone: str, image_url: str, caption: str = ""):
    """Envía una imagen con caption opcional."""
    url = f"{WHAPI_BASE_URL}/messages/image"
    payload = {
        "to": phone,
        "media": image_url,
        "caption": caption,
    }
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(url, json=payload, headers=HEADERS)
        response.raise_for_status()
        return response.json()


async def send_video(phone: str, video_url: str, caption: str = ""):
    """Envía un video con caption opcional."""
    url = f"{WHAPI_BASE_URL}/messages/video"
    payload = {
        "to": phone,
        "media": video_url,
        "caption": caption,
    }
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(url, json=payload, headers=HEADERS)
        response.raise_for_status()
        return response.json()


async def send_document(phone: str, doc_url: str, filename: str = "documento.pdf", caption: str = ""):
    """Envía un documento (PDF, etc.)."""
    url = f"{WHAPI_BASE_URL}/messages/document"
    payload = {
        "to": phone,
        "media": doc_url,
        "filename": filename,
        "caption": caption,
    }
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(url, json=payload, headers=HEADERS)
        response.raise_for_status()
        return response.json()


def extract_message_data(webhook_body: dict) -> dict | None:
    """
    Extrae los datos relevantes del webhook de Whapi.
    Retorna dict con phone, body, type o None si no es un mensaje entrante.
    """
    messages = webhook_body.get("messages", [])
    if not messages:
        return None

    msg = messages[0]

    # Ignorar mensajes enviados por nosotros (fromMe)
    if msg.get("from_me") or msg.get("fromMe"):
        return None

    msg_type = msg.get("type", "text")
    phone = msg.get("from", "")

    # Limpiar el número (quitar @s.whatsapp.net si viene así)
    if "@" in phone:
        phone = phone.split("@")[0]

    body = ""
    media_url = None
    if msg_type == "text":
        body = msg.get("text", {}).get("body", "") if isinstance(msg.get("text"), dict) else msg.get("body", "")
    elif msg_type == "image":
        body = "[imagen]"
        media_url = msg.get("image", {}).get("link") or msg.get("media_url")
    elif msg_type == "video":
        body = "[video]"
    elif msg_type in ("audio", "voice", "ptt"):
        body = "[audio]"
        audio_data = msg.get("audio") or msg.get("voice") or {}
        media_url = audio_data.get("link") or msg.get("media_url")
    elif msg_type == "document":
        body = "[documento]"
    else:
        body = msg.get("body", "")

    if not phone:
        return None

    return {
        "phone": phone,
        "body": body.strip(),
        "type": msg_type,
        "message_id": msg.get("id", ""),
        "media_url": media_url,
    }
