from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn, json, socket


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


def get_server_ip():
    try:
        hostname = socket.gethostname()
        server_ip = socket.gethostbyname(hostname)
        return server_ip
    except:
        return "127.0.0.1"  # Fallback to localhost


def read_html(html):
    with open(f"templates/{html}", "r", encoding="utf-8") as file:
        return file.read()


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

    
manager = ConnectionManager()


@app.get("/")
async def get():
    return HTMLResponse(content=read_html("websocket.html"))


@app.get("/server-ip")
async def get_server_ip_endpoint():
    return {"ip": get_server_ip()}


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    try: 
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"You wrote: {data}", websocket)
            await manager.broadcast(f"Client #{client_id} says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} has left the chat")


@app.get("/vc")
async def get():
    return HTMLResponse(content=read_html("webrtc.html"))


peers = {}
@app.websocket("vc/ws/{peer_id}")
async def websocket_endpoint(websocket: WebSocket, peer_id: str):
    await websocket.accept()
    
    peers[peer_id] = websocket
    try:
        while True:
            message = await websocket.receive_text()
            message_data = json.loads(message)
            
            target_peer = message_data.get("target")
            if target_peer in peers:
                await peers[target_peer].send_text(message)
    except WebSocketDisconnect:
        peers.pop(peer_id, None)
        print(f"Peer {peer_id} disconnected.")


if __name__ == "__main__":
    config = uvicorn.Config("websocket:app", host = '0.0.0.0', port=8000)
    server = uvicorn.Server(config)
    server.run()

