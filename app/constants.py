import os

# Global config
DEBUG = False
USE_ZAPIER = False

# API keys
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY")
RETELL_API_KEY = os.environ.get("RETELL_API_KEY")

# Mistral parameters
MODEL = "mistral-large-latest"
LLM_KWARGS = {
    "temperature": 0.2,
    "max_tokens": 500,
}

# RAG parameters
TOP_K = 2

# Zapier parameters
HOST_NAME = os.environ.get("HOST_NAME")
GET_AVAILABILITY_WEBHOOK = os.environ.get("GET_AVAILABILITY_WEBHOOK")
BOOK_SLOT_WEBHOOK = os.environ.get("BOOK_SLOT_WEBHOOK")
SEND_MAIL_WEBHOOK = os.environ.get("SEND_MAIL_WEBHOOK")
MAX_WAIT = 15
CHECK_EVERY = 0.1

# Prompting
SYSTEM_PROMPT = (
    "You are engaging voice conversation with a patient.\n"
    "You have the following capabilities:\n"
    "1. Ask about the reason for the consultation.\n"
    "2. Ask about the patient's name.\n"
    "3. Ask about the date of the appointment.\n"
    "4. Use a function to get the availability of the doctor.\n"
    "5. Use a function to book a slot with the doctor.\n"
    "6. Use a function to get additional information.\n"
)
REMINDER_PROMPT = "(Now the user has not responded in a while, you would say:)"
ERROR_PROMPT = "An error occured"
DOCUMENT_PROMPT = """## Documents
{document_stack}\n
"""

# Hardcoded answers
GREETINGS = "Hey there, I'm Ema and I work at the Dental Office, how can I help you?"
