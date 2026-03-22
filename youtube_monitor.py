"""
Monitorea el canal de YouTube de Guerreros de Fuego
y detecta cuando hay un stream en vivo.
"""
import httpx
import logging

logger = logging.getLogger(__name__)

CHANNEL_ID = "UCqyv78XprOJ3TZcZHMym6Lg"
YOUTUBE_API_KEY = "AIzaSyC80WkUDqV4-2C6FgeYEvV78sYfJ198oG4"

_was_live = False  # estado anterior para detectar cambio


async def check_live() -> dict | None:
    """
    Verifica si el canal está en vivo ahora mismo.
    Retorna dict con {title, url} si está en vivo, None si no.
    """
    global _was_live
    try:
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "channelId": CHANNEL_ID,
            "eventType": "live",
            "type": "video",
            "key": YOUTUBE_API_KEY,
        }
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params)
            data = resp.json()

        items = data.get("items", [])
        if items:
            video_id = items[0]["id"]["videoId"]
            title = items[0]["snippet"]["title"]
            live_url = f"https://youtube.com/watch?v={video_id}"

            if not _was_live:
                # Acaba de empezar el live — notificar
                _was_live = True
                logger.info(f"LIVE DETECTADO: {title} — {live_url}")
                return {"title": title, "url": live_url, "is_new": True}
            else:
                # Ya estaba en vivo, no re-notificar
                return {"title": title, "url": live_url, "is_new": False}
        else:
            _was_live = False
            return None

    except Exception as e:
        logger.error(f"Error chequeando YouTube live: {e}")
        return None
