import asyncio

from dotenv import load_dotenv
from starlette.websockets import WebSocket, WebSocketState, WebSocketDisconnect

load_dotenv()

def handle_websocket_disconnect(func):
    async def wrapper(manager, user_id, *args, **kwargs):
        try:
            return await func(manager, user_id, *args, **kwargs)
        except WebSocketDisconnect:
            await manager.disconnect(user_id)
            print(f"Disconnected and removed WebSocket for user: {user_id}")
    return wrapper

# class MockWebSocket:
#     async def send_json(self, data):
#         print(data)

class WebSocketManager:
    def __init__(self):
        self.clients: dict[str, WebSocket] = {}

        # self.clients: dict[str, WebSocket] = {
        #     'clulqsgkw00048gontjpleai8': MockWebSocket(),
        # }

    # Connect
    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.clients[user_id] = websocket

    def get_client(self, user_id: str):
        return self.clients.get(user_id)

    def get_clients(self):
        return self.clients

    async def disconnect(self, user_id: str):
        if user_id not in self.clients:
            return
        if self.clients[user_id].client_state == WebSocketState.CONNECTED:
            await self.clients[user_id].close()
        del self.clients[user_id]

    async def disconnect_all(self):
        await asyncio.gather(self.disconnect(user_id) for user_id in self.clients)

    def is_client_connected(self, user_id: str):
        if user_id not in self.clients:
            return False

        match self.clients[user_id].client_state:
            case WebSocketState.CONNECTED:
                return True
            case WebSocketState.DISCONNECTED:
                self.disconnect(user_id)

        return False

    def is_any_client_connected(self):
        return bool(self.clients)

    def get_client_ids(self):
        return list(self.clients.keys())

    # Send
    async def broadcast(self, command, data):
        return await asyncio.gather(
            command(user_id, data)
            if self.is_client_connected(user_id)
            else self.disconnect(user_id)
            for user_id in self.clients
        )

    @handle_websocket_disconnect
    async def send_text(self, user_id, message: str):
        await self.clients[user_id].send_text(message)

    async def broadcast_text(self, message: str):
        return await self.broadcast(self.send_text, message)

    @handle_websocket_disconnect
    async def send_json(self, user_id, data: dict):
        await self.clients[user_id].send_json(data)

    async def broadcast_json(self, data: dict):
        return await self.broadcast(self.send_json, data)

    # Receive
    @handle_websocket_disconnect
    async def receive_text(self, user_id: str):
        return await self.clients[user_id].receive_text()

    @handle_websocket_disconnect
    async def receive_json(self, user_id: str):
        return await self.clients[user_id].receive_json()

    @handle_websocket_disconnect
    async def receive_bytes(self, user_id: str):
        return await self.clients[user_id].receive_bytes()
