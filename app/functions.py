import pickle
import uuid

import requests
from langchain_community.vectorstores import FAISS

from app.constants import (
    BOOK_SLOT_WEBHOOK,
    DEBUG,
    DOCUMENT_PROMPT,
    ERROR_PROMPT,
    GET_AVAILABILITY_WEBHOOK,
    HOST_NAME,
    SEND_MAIL_WEBHOOK,
    TOP_K,
    USE_ZAPIER,
)

with open("rag.pkl", "rb") as f:
    rag: FAISS = pickle.load(f)


def get_informartion(query):
    print(f"[CALL] call_clinic_rag: {query}")
    docs = rag.similarity_search(query, k=TOP_K)
    document_stack = "\n###\n".join([doc.page_content for doc in docs])
    return DOCUMENT_PROMPT.format(document_stack=document_stack)


def get_availability(**kwargs):
    print("[CALL] get_availability", kwargs)
    if not USE_ZAPIER:
        return "available [you should ask for confirmation and book the slot]"

    hour = kwargs["hour"] - 2
    start_at = f"2024-04-27T{hour:02d}:00:00.000Z"
    end_at = f"2024-04-27T{hour:02d}:30:00.000Z"

    callback_id = str(uuid.uuid4())
    callback_url = f"{HOST_NAME}/zapier-callback/{callback_id}"
    response = requests.post(
        url=GET_AVAILABILITY_WEBHOOK,
        data={
            "start_at": start_at,
            "end_at": end_at,
            "callback_url": callback_url,
        },
    )

    if response.status_code != 200:
        return ERROR_PROMPT

    response = requests.get(f"{HOST_NAME}/zapier-callback-result/{callback_id}")
    if response.status_code != 200:
        return ERROR_PROMPT
    callback_value = response.json()["callback_value"]

    if callback_value.get("event") is None:
        return "available [you should ask for confirmation and book the slot]"
    else:
        return "busy"


def send_email(**kwargs):
    response = requests.post(
        url=SEND_MAIL_WEBHOOK,
        data=kwargs,
    )

    if response.status_code != 200 and DEBUG:
        print("Error")


def book_slot(**kwargs):
    print("[CALL] get_availability", kwargs)
    if not USE_ZAPIER:
        return "available [you should ask for confirmation and book the slot]"

    hour = kwargs["hour"] - 2
    start_at = f"2024-04-27T{hour:02d}:00:00.000Z"
    end_at = f"2024-04-27T{hour:02d}:30:00.000Z"

    content = kwargs["conversation_summary"]
    subject = "Appointment booked for " + kwargs["patient_name"]
    response = requests.post(
        url=BOOK_SLOT_WEBHOOK,
        data={
            "start_at": start_at,
            "end_at": end_at,
            "title": subject,
            "description": content,
        },
    )

    if response.status_code != 200:
        return ERROR_PROMPT

    send_email(subject=subject, content=content)

    return "booked"


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_informartion",
            "description": "Get information about the clinic.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The query necessitating additionnal information.",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_availability",
            "description": "Get the availability of the doctor.",
            "parameters": {
                "type": "object",
                "properties": {
                    "hour": {
                        "type": "integer",
                        "description": "The hour of the appointment.",
                    },
                    "patient_name": {
                        "type": "string",
                        "description": "The name of the patient.",
                    },
                    "reason_for_consultation": {
                        "type": "string",
                        "description": "The reason for the consultation.",
                    },
                },
                "required": ["hour", "patient_name", "reason_for_consultation"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "book_slot",
            "description": "Book a slot with the doctor when a slot has been found.",
            "parameters": {
                "type": "object",
                "properties": {
                    "hour": {
                        "type": "integer",
                        "description": "The hour of the appointment.",
                    },
                    "conversation_summary": {
                        "type": "string",
                        "description": "The summary of the conversation.",
                    },
                    "patient_name": {
                        "type": "string",
                        "description": "The name of the patient.",
                    },
                    "reason_for_consultation": {
                        "type": "string",
                        "description": "The reason for the consultation.",
                    },
                },
                "required": [
                    "hour",
                    "conversation_summary",
                    "patient_name",
                    "reason_for_consultation",
                ],
            },
        },
    },
]

NAME_TO_FUNCTIONS = {
    "get_informartion": get_informartion,
    "get_availability": get_availability,
    "book_slot": book_slot,
}

NAME_TO_FILLER = {
    "get_informartion": "I will get the information for you.\n",
    "get_availability": "Well... Let me check if the doctor is available at that time.\n",
    "book_slot": "I will book the slot for you.\n",
}
