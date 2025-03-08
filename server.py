import uvicorn, socket, json, asyncio, platform
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse


# Use SelectorEventLoop on Windows to avoid Proactor issues
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


app = FastAPI()
app.mount("/static", StaticFiles(directory="static", html=True), name="static")


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.get("/")
async def get():
    return HTMLResponse(content=read_html("text_chat.html"))


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


# For fetching IP
@app.get("/server-ip")
async def get_server_ip_endpoint():
    return {"ip": get_server_ip()}


# Redirect root route to index.html
@app.get("/vc")
async def root():
    return HTMLResponse(content=read_html("voice_chat.html"))


# Store active WebSocket connections
active_connections = {}
@app.websocket("/ws/vc/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    try:
        await websocket.accept()
        active_connections[client_id] = websocket
        print(f"Connection established with client: {client_id}")
        # Notify other clients about the new connection
        for cid, conn in active_connections.items():
            if cid != client_id:
                try:
                    await conn.send_text(json.dumps({
                        "join": True,
                        "sender": client_id
                    }))
                except Exception as e:
                    print(f"Error notifying client {cid}: {e}")
        # Main message loop
        while True:
            try:
                message = await websocket.receive_text()
                data = json.loads(message)
                print(f"Received message from {client_id}: {data}")

                if "target" in data and data["target"] in active_connections:
                    await active_connections[data["target"]].send_text(json.dumps(data))
                    print(f"Message forwarded to {data['target']}")
            except WebSocketDisconnect:
                print(f"Client {client_id} disconnected normally")
                break
            except Exception as e:
                print(f"Error processing message from {client_id}: {e}")
                break
    except Exception as e:
        print(f"Error during WebSocket communication with {client_id}: {e}")
    finally:
        if client_id in active_connections:
            try:
                del active_connections[client_id]
                print(f"Connection closed for client: {client_id}")
            except Exception as e:
                print(f"Error removing client {client_id} from active connections: {e}")
        # Notify other clients about the disconnection
        for cid, conn in active_connections.items():
            try:
                await conn.send_text(json.dumps({
                    "leave": True,
                    "sender": client_id
                }))
            except Exception as e:
                print(f"Error notifying client {cid} about disconnection: {e}")


if __name__ == "__main__":
    config = uvicorn.Config("__main__:app", host=get_server_ip(), port=8000, ssl_keyfile="key.pem", ssl_certfile="cert.pem")
    uvicorn.run(config)

