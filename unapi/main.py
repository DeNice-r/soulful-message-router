import logging
from typing import List

from fastapi import FastAPI, HTTPException, Query, Request, WebSocket

from unapi.event import EventFactory
from unapi import platforms

from unapi.webhooks import init as webhooks_init

from os import environ

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
app = FastAPI()

webhook_path = environ["WEBHOOK_PATH"]

ws_clients: List[WebSocket] = []
last_event = None

@app.get("/")
async def index():
    return "I'm ok"


@app.get("/init")
async def webhook_init():
    try:
        await webhooks_init()
        return f"I'm ok"
    except Exception as e:
        return HTTPException(500, f"Error: {e}")


@app.post(webhook_path)
async def webhook_callback(request: Request):
    event = None
    try:
        event = await EventFactory.create_event(request)
    except ValueError as e:
        logging.warning(f"Error: {e}")
        return HTTPException(status_code=400, detail=str(e))

    global last_event
    last_event = event
    # event.send_message(event.text)

    for client in ws_clients:
        await client.send_text(event.text)

    return "OK"


# Following code must be moved or removed
facebook_verification_token = environ["FACEBOOK_VERIFICATION_TOKEN"]


@app.get(webhook_path)
async def facebook_subscribe(mode: str = Query(None, alias="hub.mode"),
                             verify_token: str = Query(None, alias="hub.verify_token"),
                             challenge: int = Query(None, alias="hub.challenge")):
    if verify_token == facebook_verification_token and mode == "subscribe":
        return challenge
    raise HTTPException(status_code=403, detail="Invalid key")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    ws_clients.append(websocket)

    try:
        while True:
            data = await websocket.receive_text()

            if last_event:
                last_event.send_message(data)
    except Exception as e:
        ws_clients.remove(websocket)
