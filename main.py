import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

from config import PORT
from database import init_db
from whapi_client import extract_message_data, send_text
from agent import process_message
from scheduler import run_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Iniciando agente de ventas WhatsApp...")
    init_db()
    logger.info("Base de datos inicializada")

    # Iniciar scheduler en background
    scheduler_task = asyncio.create_task(run_scheduler())
    logger.info("Scheduler de follow-ups iniciado")

    yield

    # Shutdown
    scheduler_task.cancel()
    logger.info("Agente detenido")


app = FastAPI(title="Agente de Ventas WhatsApp", lifespan=lifespan)


@app.get("/")
async def health_check():
    return {"status": "ok", "agent": "Agente de Ventas WhatsApp v1.0"}


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

    logger.info(f"Mensaje de {phone} [{msg_type}]: {user_message[:80]}")

    if not user_message:
        user_message = f"[el usuario envió un {msg_type}]"

    # Procesar en background para responder 200 rápido a Whapi
    asyncio.create_task(_process_and_reply(phone, user_message))

    return JSONResponse({"status": "ok"})


async def _process_and_reply(phone: str, user_message: str):
    try:
        responses = await process_message(phone, user_message)
    except Exception as e:
        logger.error(f"Error procesando mensaje de {phone}: {e}", exc_info=True)
        return

    for i, response in enumerate(responses):
        if i > 0:
            await asyncio.sleep(1.5)
        try:
            await send_text(phone, response)
        except Exception as e:
            logger.error(f"Error enviando mensaje a {phone}: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=False)
