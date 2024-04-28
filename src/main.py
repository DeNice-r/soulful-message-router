import json
import logging
from os import environ
from random import choice as random_choice

from sqlalchemy import select
from sqlalchemy import text
from starlette.websockets import WebSocketDisconnect
from fastapi import FastAPI, HTTPException, Query, Request, WebSocket

from src.api import send_message
from src.db.engine import Session
from src.db.models.chat import Chat
from src.db.models.message import Message
from src.db.models.user import User
from src.db.queries import get_personnel
from src.event import EventFactory
from src.webhooks import init as webhooks_init
from src.websocket_manager import WebSocketManager
from src.util import no_personnel_error

# Warning: This import is import'ant, even though it is not used
from src import platforms


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
app = FastAPI()

webhook_path = environ["WEBHOOK_PATH"]


ws_manager = WebSocketManager()


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
    try:
        event = await EventFactory.create_event(request)
    except ValueError as e:
        logging.warning(f"Error: {e}")
        return HTTPException(status_code=400, detail=str(e))

    personnel_ids = ws_manager.get_client_ids()
    user_id = event.user_unique_id
    with Session() as session:
        user: User = session.get(User, user_id)
        if not user:
            user = User(
                id=user_id,
            )
            session.add(user)
            session.commit()

        if user.suspended:
            event.send_message("Ви були заблоковані. Якщо вважаєте, що це помилка - зверніться на пошту unban@soulful.pp.ua для розблокування.")
            return

        chat = session.execute(select(Chat).where(Chat.user_id == user_id)).scalar_one_or_none()
        if not chat:
            # The following could be used to continuously verify user access to chat, probably unnecessary
            # personnel = get_personnel(session, personnel_ids)

            if not personnel_ids:
                no_personnel_error(event, user_id)

            chat = Chat(
                user_id=user_id,
                personnel_id=random_choice(personnel_ids) if personnel_ids else None,  # TODO: Some complicated logic to choose the personnel
            )
            session.add(chat)
            session.commit()

            event.send_message("Привіт! Як ми можемо вам допомогти? Оператор незабаром відповість вам.")

        message = Message(
            text=event.text,
            is_from_user=True,
            chat_id=chat.id,
        )
        session.add(message)
        session.commit()

        if chat.personnel_id not in personnel_ids:
            if chat.personnel_id:
                no_personnel_error(event, user_id, is_assigned=True)
            return

        try:
            await ws_manager.send_json(chat.personnel_id, {
                'id': message.id,
                'text': message.text,
                'createdAt': message.created_at.timestamp(),
                'chatId': chat.id,
                'isFromUser': message.is_from_user,
            })
        except Exception as e:
            if e == WebSocketDisconnect:
                await ws_manager.disconnect(chat.personnel_id)

            logging.error(f"Unable to reach an operator who was previously connected: {e}")

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


@app.websocket("/ws/{personnel_token}")
async def websocket_endpoint(websocket: WebSocket, personnel_token: str):
    with Session() as session:
        personnel_id = session.execute(text("SELECT user_id FROM \"Session\" WHERE session_token = :token"), {'token': personnel_token}).scalars().one_or_none()

        user = get_personnel(session, [personnel_id])

    if not personnel_id or not user:
        return HTTPException(status_code=401, detail="Unauthorized")

    await ws_manager.connect(personnel_id, websocket)

    while ws_manager.get_client(personnel_id):
        data = await ws_manager.receive_text(personnel_id)

        if not data:
            continue

        data = json.loads(data)

        with Session() as session:
            message = Message(
                text=data['text'],
                chat_id=data['chatId'],
                is_from_user=data['isFromUser'],
            )
            session.add(message)
            session.commit()

            send_message(data['userId'], data['text'])

            await ws_manager.send_json(personnel_id, {
                'id': message.id,
                'text': message.text,
                'createdAt': message.created_at.timestamp(),
                'chatId': message.chat_id,
                'isFromUser': message.is_from_user,
            })
