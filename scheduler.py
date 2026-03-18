"""
Scheduler: revisa cada minuto si hay follow-ups pendientes y los envía.
"""
import asyncio
import logging
from datetime import datetime

from database import get_pending_followups, mark_followup_sent, get_conversation, save_conversation
from agent import build_followup_message
from whapi_client import send_text

logger = logging.getLogger(__name__)


async def process_pending_followups():
    """Revisa y envía todos los follow-ups que ya vencieron su tiempo programado."""
    now = datetime.utcnow()
    pending = get_pending_followups(now)

    for followup in pending:
        phone = followup["phone"]
        followup_type = followup["followup_type"]
        followup_id = followup["id"]

        try:
            state = get_conversation(phone)

            # No enviar si ya compró o fue transferido a humano
            if state.get("conversation_status") in ("sold", "human_handoff"):
                mark_followup_sent(followup_id)
                continue

            # No enviar si ya superó el máximo de follow-ups normales
            if followup_type.startswith("follow_up") and state.get("follow_up_count", 0) >= 2:
                mark_followup_sent(followup_id)
                continue

            message = build_followup_message(phone, followup_type)
            if not message:
                mark_followup_sent(followup_id)
                continue

            await send_text(phone, message)
            logger.info(f"Follow-up '{followup_type}' enviado a {phone}")

            # Actualizar contador de follow-ups
            if followup_type.startswith("follow_up"):
                state["follow_up_count"] = state.get("follow_up_count", 0) + 1

                # Si ya enviamos el follow_up_2, cerrar conversación
                if state["follow_up_count"] >= 2:
                    close_msg = "Perfecto 😊 Dejamos esta conversación pausada por ahora. Si más adelante quieres retomar el tema, aquí estaré para ayudarte 🙌"
                    await send_text(phone, close_msg)
                    state["conversation_status"] = "closed"

            elif followup_type == "reactivation":
                # Si no hubo respuesta al reactivation, cerrar
                # (esto se maneja si el usuario no responde en 24h)
                pass

            save_conversation(phone, state)
            mark_followup_sent(followup_id)

        except Exception as e:
            logger.error(f"Error enviando follow-up {followup_id} a {phone}: {e}")


async def run_scheduler():
    """Loop infinito que revisa follow-ups cada 60 segundos."""
    logger.info("Scheduler iniciado - revisando follow-ups cada 60 segundos")
    while True:
        try:
            await process_pending_followups()
        except Exception as e:
            logger.error(f"Error en el scheduler: {e}")
        await asyncio.sleep(60)
