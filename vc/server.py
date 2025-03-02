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


connected_users = {}
# vc endpoint
@app.websocket("/ws/vc/{user_id}")
async def vc_websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()
    connected_users[user_id] = websocket

    # Send the list of existing peers when a new user connects
    await websocket.send_json({"type": "peer-list", "peers": list(connected_users.keys())})

    # Notify all peers about the new user
    await notify_peers()

    try:
        while True:
            # Receive messages from the client
            message = await websocket.receive_text()
            data = json.loads(message)
            
            if data["type"] == "peer-connect":
                target_peer_id = data["peer_id"]
                # Send peer connect message to all other peers
                for peer_id, peer_ws in connected_users.items():
                    if peer_id != user_id:
                        await peer_ws.send_text(json.dumps({
                            "type": "peer-connect",
                            "peer_id": user_id
                        }))
            
            elif data["type"] == "peer-disconnect":
                # Handle peer disconnect
                if user_id in connected_users:
                    del connected_users[user_id]
                await notify_peers()

    except WebSocketDisconnect:
        # Handle WebSocket disconnect
        del connected_users[user_id]
        print(f"{user_id} disconnected.")
        await notify_peers()

# Notify all peers of the updated peer list
async def notify_peers():
    # Send the updated peer list to all connected peers
    for peer_id, peer_ws in connected_users.items():
        await peer_ws.send_text(json.dumps({
            "type": "peer-list",
            "peers": list(connected_users.keys())
        }))


if __name__ == "__main__":
    config = uvicorn.Config("server:app", host=get_server_ip(), port=8000)
    server = uvicorn.Server(config)
    server.run()

