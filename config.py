from dotenv import load_dotenv
import os

load_dotenv()

WHAPI_API_KEY = os.getenv("WHAPI_API_KEY")
WHAPI_BASE_URL = os.getenv("WHAPI_BASE_URL", "https://gate.whapi.cloud")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

HUMAN_AGENT_PHONE = os.getenv("HUMAN_AGENT_PHONE")
PAYMENT_LINK = os.getenv("PAYMENT_LINK")
PORT = int(os.getenv("PORT", 8000))
