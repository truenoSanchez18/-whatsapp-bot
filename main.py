import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from config import PORT
from database import init_db, get_all_subscribers
from whapi_client import extract_message_data, send_text, send_image, send_document, transcribe_audio
from agent import process_message
from scheduler import run_scheduler
from pdf_generator import generate_all, OUTPUT_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Iniciando Guerreros de Fuego WhatsApp Bot...")
    init_db()
    logger.info("Base de datos inicializada")
    generate_all()
    logger.info("Lead magnets PDFs listos")

    # Iniciar scheduler en background
    scheduler_task = asyncio.create_task(run_scheduler())
    logger.info("Scheduler de follow-ups iniciado")

    yield

    # Shutdown
    scheduler_task.cancel()
    logger.info("Agente detenido")


app = FastAPI(title="Guerreros de Fuego WhatsApp Bot", lifespan=lifespan)


@app.get("/")
async def health_check():
    return {"status": "ok", "agent": "Guerreros de Fuego Bot v2.0"}


@app.get("/lead-magnets/{filename}")
async def serve_lead_magnet(filename: str):
    """Sirve los PDFs de lead magnets."""
    path = OUTPUT_DIR / filename
    if not path.exists() or not filename.endswith(".pdf"):
        raise HTTPException(status_code=404, detail="PDF no encontrado")
    return FileResponse(str(path), media_type="application/pdf", filename=filename)


@app.post("/broadcast")
async def broadcast(request: Request):
    """
    Endpoint para enviar un mensaje masivo a todos los suscriptores.
    Body: {"message": "texto del mensaje", "secret": "gdf2026"}
    """
    body = await request.json()
    if body.get("secret") != "gdf2026":
        raise HTTPException(status_code=403, detail="No autorizado")

    message = body.get("message", "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="Mensaje vacío")

    subscribers = get_all_subscribers()
    asyncio.create_task(_send_broadcast(subscribers, message))
    return {"status": "ok", "recipients": len(subscribers)}


async def _send_broadcast(subscribers: list, message: str):
    for sub in subscribers:
        try:
            await send_text(sub["phone"], message)
            await asyncio.sleep(1)  # evitar rate limit
        except Exception as e:
            logger.error(f"Broadcast error a {sub['phone']}: {e}")


@app.get("/webhook")
async def webhook_verify():
    return JSONResponse({"status": "ok", "message": "webhook active"})


@app.post("/webhook")
async def webhook(request: Request):
    """
    Endpoint que recibe todos los eventos de Whapi.
    Siempre retorna 200 para que Whapi no reintente.
    """
    try:
        body = await request.json()
    except Exception:
        print("WEBHOOK: body vacío o no JSON")
        return JSONResponse({"status": "ok"})

    print(f"WEBHOOK RECIBIDO: {body}")
    logger.info(f"Webhook recibido: {body}")

    try:
        msg_data = extract_message_data(body)
    except Exception as e:
        logger.error(f"Error extrayendo mensaje: {e}")
        return JSONResponse({"status": "ok"})

    if msg_data is None:
        return JSONResponse({"status": "ok"})

    phone = msg_data["phone"]
    user_message = msg_data["body"]
    msg_type = msg_data["type"]
    media_url = msg_data.get("media_url")

    logger.info(f"Mensaje de {phone} [{msg_type}]: {user_message[:80]}")

    if not user_message:
        user_message = f"[el usuario envió un {msg_type}]"

    # Procesar en background para responder 200 rápido a Whapi
    asyncio.create_task(_process_and_reply(phone, user_message, msg_type, media_url))

    return JSONResponse({"status": "ok"})


async def _process_and_reply(phone: str, user_message: str, msg_type: str = "text", media_url: str = None):
    # Transcribir audio con Whisper si aplica
    if msg_type in ("audio", "voice", "ptt") and media_url:
        logger.info(f"Transcribiendo audio de {phone}...")
        transcribed = await transcribe_audio(media_url)
        if transcribed:
            user_message = transcribed
            logger.info(f"Audio transcrito: {transcribed[:80]}")
        else:
            user_message = "[audio no pudo transcribirse]"

    try:
        responses = await process_message(phone, user_message)
    except Exception as e:
        logger.error(f"Error procesando mensaje de {phone}: {e}", exc_info=True)
        return

    for i, item in enumerate(responses):
        if i > 0:
            await asyncio.sleep(1.5)
        try:
            if isinstance(item, dict) and item.get("type") == "image":
                await send_image(phone, item["url"], item.get("caption", ""))
            else:
                await send_text(phone, item)
        except Exception as e:
            logger.error(f"Error enviando mensaje a {phone}: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=False)
