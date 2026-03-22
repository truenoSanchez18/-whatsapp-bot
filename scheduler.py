"""
Scheduler: maneja follow-ups, notificaciones diarias Duolingo y detección YouTube Live.
"""
import asyncio
import logging
from datetime import datetime, date

import pytz

from database import (get_pending_followups, mark_followup_sent,
                      get_conversation, save_conversation, get_all_subscribers)
from agent import build_followup_message
from whapi_client import send_text, send_document
from notifications import get_daily_message, get_live_message
from youtube_monitor import check_live
from pdf_generator import LEAD_MAGNETS, OUTPUT_DIR, generate_all

logger = logging.getLogger(__name__)

MEXICO_TZ = pytz.timezone("America/Mexico_City")
NOTIFICATION_HOUR = 9   # 9am hora México
LEAD_MAGNET_INTERVAL = 3  # cada 3 días

# IDs de lead magnets en orden de rotación
LEAD_MAGNET_ROTATION = ["errores", "7dias", "script"]


def _mexico_now() -> datetime:
    return datetime.now(MEXICO_TZ)


async def process_pending_followups():
    now = datetime.utcnow()
    pending = get_pending_followups(now)

    for followup in pending:
        phone = followup["phone"]
        followup_type = followup["followup_type"]
        followup_id = followup["id"]
        try:
            state = get_conversation(phone)
            if state.get("conversation_status") in ("sold", "human_handoff"):
                mark_followup_sent(followup_id)
                continue
            if followup_type.startswith("follow_up") and state.get("follow_up_count", 0) >= 2:
                mark_followup_sent(followup_id)
                continue

            message = build_followup_message(phone, followup_type)
            if not message:
                mark_followup_sent(followup_id)
                continue

            await send_text(phone, message)
            logger.info(f"Follow-up '{followup_type}' enviado a {phone}")

            if followup_type.startswith("follow_up"):
                state["follow_up_count"] = state.get("follow_up_count", 0) + 1
                if state["follow_up_count"] >= 2:
                    await send_text(phone, "😊 Hasta pronto, Guerrero. Aquí estaré cuando me necesites 🔥")
                    state["conversation_status"] = "closed"

            save_conversation(phone, state)
            mark_followup_sent(followup_id)
        except Exception as e:
            logger.error(f"Error enviando follow-up {followup_id} a {phone}: {e}")


async def send_daily_notifications():
    """Envía notificación diaria Duolingo a todos los suscriptores activos."""
    now_mx = _mexico_now()
    today_str = now_mx.strftime("%Y-%m-%d")

    subscribers = get_all_subscribers()
    count = 0

    generate_all()  # asegura que existan PDFs

    for sub in subscribers:
        # Saltar si ya recibió notificación hoy
        if sub.get("last_notification_date") == today_str:
            continue

        phone = sub["phone"]
        notification_day = sub.get("notification_day", 0)
        lead_magnets_sent = sub.get("lead_magnets_sent", [])

        try:
            # Mensaje diario Duolingo
            message = get_daily_message(notification_day)
            await send_text(phone, message)
            await asyncio.sleep(0.5)

            # Cada 3 días → enviar lead magnet
            if notification_day > 0 and notification_day % LEAD_MAGNET_INTERVAL == 0:
                # Elegir el siguiente lead magnet no enviado
                next_pdf = None
                for key in LEAD_MAGNET_ROTATION:
                    if key not in lead_magnets_sent:
                        next_pdf = key
                        break
                # Si ya se enviaron todos, rotar desde el principio
                if not next_pdf and LEAD_MAGNET_ROTATION:
                    next_pdf = LEAD_MAGNET_ROTATION[
                        (len(lead_magnets_sent)) % len(LEAD_MAGNET_ROTATION)
                    ]

                if next_pdf:
                    meta = LEAD_MAGNETS[next_pdf]
                    pdf_url = f"https://whatsapp-bot-7sv8.onrender.com/lead-magnets/{meta['file']}"
                    intro = f"🎁 *Recurso gratuito para ti, Guerrero:*\n_{meta['title']}_"
                    await send_text(phone, intro)
                    await asyncio.sleep(1)
                    await send_document(phone, pdf_url, meta["file"],
                                        caption=f"🔥 {meta['title']}")
                    if next_pdf not in lead_magnets_sent:
                        lead_magnets_sent.append(next_pdf)
                    logger.info(f"Lead magnet '{next_pdf}' enviado a {phone}")

            # Actualizar estado
            sub["notification_day"] = notification_day + 1
            sub["last_notification_date"] = today_str
            sub["lead_magnets_sent"] = lead_magnets_sent
            save_conversation(phone, sub)

            count += 1
            await asyncio.sleep(1)  # evitar rate limit de Whapi

        except Exception as e:
            logger.error(f"Error enviando notificación a {phone}: {e}")

    if count > 0:
        logger.info(f"Notificaciones diarias enviadas a {count} suscriptores")


async def check_youtube_live():
    """Verifica si el canal está en vivo y notifica a todos si acaba de empezar."""
    live = await check_live()
    if live and live.get("is_new"):
        logger.info(f"¡LIVE NUEVO! Notificando a todos los suscriptores...")
        message = get_live_message(live["url"])
        subscribers = get_all_subscribers()
        for sub in subscribers:
            try:
                await send_text(sub["phone"], message)
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Error notificando live a {sub['phone']}: {e}")
        logger.info(f"Notificación de live enviada a {len(subscribers)} personas")


async def run_scheduler():
    """Loop infinito: follow-ups cada minuto, YouTube cada 5 min, notificaciones diarias a las 9am México."""
    logger.info("Scheduler iniciado")
    last_notification_check = ""
    tick = 0

    while True:
        try:
            # Follow-ups siempre
            await process_pending_followups()

            # YouTube Live cada 5 minutos (tick 0, 5, 10...)
            if tick % 5 == 0:
                await check_youtube_live()

            # Notificaciones diarias — solo una vez al día a las 9am México
            now_mx = _mexico_now()
            today_str = now_mx.strftime("%Y-%m-%d")
            if now_mx.hour == NOTIFICATION_HOUR and last_notification_check != today_str:
                last_notification_check = today_str
                logger.info("Enviando notificaciones diarias...")
                await send_daily_notifications()

        except Exception as e:
            logger.error(f"Error en el scheduler: {e}")

        tick += 1
        await asyncio.sleep(60)
