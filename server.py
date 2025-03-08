from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn, json, socket

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Get server's local IP address
def get_server_ip():
    try:
        hostname = socket.gethostname()
        server_ip = socket.gethostbyname(hostname)
        return str(server_ip)
    except:
        return "127.0.0.1"  # Fallback to localhost

def read_html(html):
    with open(f"templates/{html}", "r", encoding="utf-8") as file:
        return file.read()


# ConnectionManager to handle WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, websocket: WebSocket, message: str):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


@app.get("/")
async def get():
    return HTMLResponse(content=read_html("text_chat.html"))


@app.get("/server-ip")
async def get_server_ip_endpoint():
    return {"ip": get_server_ip()}


# Text chat endpoint
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(websocket, f"You wrote: {data}")
            await manager.broadcast(f"Client #{user_id} says: {data}")
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
        await manager.broadcast(f"Client #{user_id} has left the chat")


@app.get("/vc")
async def get():
    return HTMLResponse(content=read_html("voice_chat.html"))


# vc endpoint
connected_users = {}
@app.websocket("/ws/vc/{user_id}")
async def call_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket)
    try:
        while True:
            message = await websocket.receive_text()
            message_data = json.loads(message)
            target_peer = message_data.get("target")
            if target_peer == "all":
                await manager.broadcast(json.dumps(message_data), sender_id=user_id)
            elif target_peer in manager.active_connections:
                await manager.send_personal_message(json.dumps(message_data), target_peer)
    except WebSocketDisconnect:
        manager.disconnect(user_id)
        await manager.broadcast(json.dumps({"type": "peer-disconnect", "peer_id": user_id}))


if __name__ == "__main__":
    config = uvicorn.Config("server:app", host=get_server_ip(), port=8000)
    server = uvicorn.Server(config)
    server.run()

