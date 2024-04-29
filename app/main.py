import asyncio
import json
import logging
from concurrent.futures import TimeoutError as ConnectionTimeoutError

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from retell import Retell

from app.constants import CHECK_EVERY, DEBUG, MAX_WAIT, RETELL_API_KEY
from app.llm import LlmClient
from app.schema import CustomLlmRequest, CustomLlmResponse

app = FastAPI()
retell = Retell(api_key=RETELL_API_KEY)
callbacks = {}


@app.post("/zapier-callback/{callback_id}")
async def zapier_callback(body: dict, callback_id: str):
    callbacks[callback_id] = body
    return {"status": "success"}


@app.get("/zapier-callback-result/{callback_id}")
async def zapier_callback_result(callback_id: str):
    wait = 0.0
    print("zapier_callback_result", callbacks)
    while callbacks.get(callback_id) is None:
        await asyncio.sleep(CHECK_EVERY)
        wait += CHECK_EVERY
        if wait > MAX_WAIT:
            print("max wait")
            break
    else:
        callback_value = callbacks[callback_id]
        del callbacks[callback_id]
        return {"callback_value": callback_value}
    return JSONResponse(status_code=500, content={"message": "Internal Server Error"})


# Only used for web frontend to register call so that frontend don't need api key
@app.post("/register-call-on-your-server")
async def handle_register_call(request: Request):
    try:
        post_data = await request.json()
        call_response = retell.call.register(
            agent_id=post_data["agent_id"],
            audio_websocket_protocol="web",
            audio_encoding="s16le",
            sample_rate=post_data["sample_rate"],  # Sample rate has to be 8000 for Twilio
        )
        if DEBUG:
            print(f"Call response: {call_response}")
    except Exception as err:
        if DEBUG:
            print(f"Error in register call: {err}")
        return JSONResponse(status_code=500, content={"message": "Internal Server Error"})


# Custom LLM Websocket handler, receive audio transcription and send back text response
@app.websocket("/llm-websocket/{call_id}")
async def websocket_handler(websocket: WebSocket, call_id: str):
    if DEBUG:
        logger = logging.getLogger("uvicorn")
    await websocket.accept()
    llm_client = LlmClient()

    # Send optional config to Retell server
    config = CustomLlmResponse(
        response_type="config",
        config={
            "auto_reconnect": True,
            "call_details": True,
        },
        response_id=1,
    )
    await websocket.send_text(json.dumps(config.__dict__))

    # Send first message to signal ready of server
    response_id = 0
    first_event = llm_client.greetings()
    await websocket.send_text(json.dumps(first_event.__dict__))

    async def stream_response(request: CustomLlmRequest):
        nonlocal response_id
        for event in llm_client.stream_response(request):
            await websocket.send_text(json.dumps(event.__dict__))
            if request.response_id < response_id:
                return  # new response needed, abandon this one

    try:
        while True:
            message = await asyncio.wait_for(websocket.receive_text(), timeout=100 * 6000)  # 100 minutes
            request_json = json.loads(message)
            request: CustomLlmRequest = CustomLlmRequest(**request_json)
            if DEBUG:
                logger.info("LLM Request received")

            # There are 5 types of interaction_type: call_details, pingpong, update_only, response_required,
            # and reminder_required.
            # Not all of them need to be handled, only response_required and reminder_required.
            if request.interaction_type == "call_details":
                continue
            if request.interaction_type == "ping_pong":
                await websocket.send_text(json.dumps({"response_type": "ping_pong", "timestamp": request.timestamp}))
                continue
            if request.interaction_type == "update_only":
                continue
            if request.interaction_type == "response_required" or request.interaction_type == "reminder_required":
                asyncio.create_task(stream_response(request))
    except WebSocketDisconnect:
        print(f"LLM WebSocket disconnected for {call_id}")
    except ConnectionTimeoutError as e:
        print(f"Connection timeout error: {e}")
    except Exception as e:
        print(f"Error in LLM WebSocket: {e}")
    finally:
        print(f"LLM WebSocket connection closed for {call_id}")
