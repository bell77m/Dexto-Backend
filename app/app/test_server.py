import asyncio
import json
import socket
from typing import Dict, Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uuid

import uvicorn

app = FastAPI()

# Configure CORS to allow WebSocket connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session management for collaborative coding and voice chat
class CollaborationManager:
    def __init__(self):
        # Track active sessions, clients, and their states
        self.sessions: Dict[str, Dict[str, WebSocket]] = {}
        self.code_states: Dict[str, Dict[str, str]] = {}
        self.voice_streams: Dict[str, Set[str]] = {}

    async def connect(self, session_id: str, client_id: str, websocket: WebSocket):
        """Establish a connection for a client in a specific session"""
        if session_id not in self.sessions:
            self.sessions[session_id] = {}
            self.code_states[session_id] = {}
            self.voice_streams[session_id] = set()
        
        self.sessions[session_id][client_id] = websocket
        await websocket.accept()

    def disconnect(self, session_id: str, client_id: str):
        """Remove a client from a session"""
        if session_id in self.sessions:
            del self.sessions[session_id][client_id]
            # Clean up empty sessions
            if not self.sessions[session_id]:
                del self.sessions[session_id]
                del self.code_states[session_id]
                del self.voice_streams[session_id]

    async def broadcast(self, session_id: str, message: dict, sender_id: str = None):
        """Broadcast a message to all clients in a session except the sender"""
        if session_id in self.sessions:
            for client_id, websocket in self.sessions[session_id].items():
                if sender_id is None or client_id != sender_id:
                    try:
                        await websocket.send_json(message)
                    except Exception:
                        # Handle potential send errors
                        pass

# Global collaboration manager
manager = CollaborationManager()

@app.websocket("/ws/{session_id}/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    session_id: str, 
    client_id: str = str(uuid.uuid4())
):
    """Main WebSocket endpoint for collaborative sessions"""
    await manager.connect(session_id, client_id, websocket)
    
    try:
        while True:
            # Receive and process incoming messages
            data = await websocket.receive_json()
            
            # Handle different message types
            message_type = data.get('type')
            
            if message_type == 'code_update':
                # Update code state and broadcast to other clients
                manager.code_states[session_id][data['file']] = data['content']
                await manager.broadcast(
                    session_id, 
                    {
                        'type': 'code_update', 
                        'file': data['file'], 
                        'content': data['content'],
                        'sender': client_id
                    }, 
                    sender_id=client_id
                )
            
            elif message_type == 'voice_data':
                # Forward voice data to other clients
                await manager.broadcast(
                    session_id, 
                    {
                        'type': 'voice_data', 
                        'data': data['data'],
                        'sender': client_id
                    }, 
                    sender_id=client_id
                )
            
            elif message_type == 'cursor_update':
                # Broadcast cursor position updates
                await manager.broadcast(
                    session_id, 
                    {
                        'type': 'cursor_update', 
                        'file': data['file'],
                        'position': data['position'],
                        'sender': client_id
                    }, 
                    sender_id=client_id
                )
    
    except WebSocketDisconnect:
        # Handle client disconnection
        manager.disconnect(session_id, client_id)
        # Optionally broadcast disconnection to other clients
        await manager.broadcast(
            session_id, 
            {
                'type': 'user_left', 
                'client_id': client_id
            }
        )

# Optional: Endpoint to create a new session
@app.get("/create_session")
async def create_session():
    """Generate a new unique session ID"""
    return {"session_id": str(uuid.uuid4())}

# Get server's local IP address
def get_server_ip():
    try:
        hostname = socket.gethostname()
        server_ip = socket.gethostbyname(hostname)
        return str(server_ip)
    except:
        return "127.0.0.1"  # Fallback to localhost
    

# For fetching IP via front end
@app.get("/server-ip")
async def get_server_ip_endpoint():
    return {"ip": get_server_ip()}

if __name__ == "__main__":
    uvicorn.run("__main__:app", host=get_server_ip(), port=12347, ssl_keyfile="key.pem", ssl_certfile="cert.pem", reload=True)
    