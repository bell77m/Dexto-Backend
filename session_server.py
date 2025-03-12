from server import *
from fastapi.responses import FileResponse


# Store active sessions: session_id -> list of connected WebSocket clients
sessions: Dict[str, List[WebSocket]] = {}

# Create a new session with a unique ID
@app.get("/session-id")
async def get_session():
    session_id = str(uuid.uuid4())
    sessions[session_id] = []
    return {"session_id": session_id}


@app.get("/session")
@app.get("/session/{session_id}")
async def session(session_id: str = None):
    if session_id is None:
        # If no session ID is provided, generate one and redirect
        session_id = str(uuid.uuid4())
    
    return HTMLResponse(content=read_html("session.html"))


@app.websocket("/ws/session/{session_id}")
async def session_websocket_endpoint(websocket: WebSocket, session_id: str):
    # Handle WebSocket connections for a given session
    await websocket.accept()

    if session_id not in sessions:
        sessions[session_id] = []

    # Add the user to the session
    sessions[session_id].append(websocket)
    
    try:
        while True:
            # Receive code updates from a user
            data = await websocket.receive_text()

            # Broadcast the update to all other users in the session
            for connection in sessions[session_id]:
                if connection != websocket:  # Avoid sending back to the sender
                    await connection.send_text(data)
    except WebSocketDisconnect:
        # Remove the user from the session when they disconnect
        sessions[session_id].remove(websocket)
        if not sessions[session_id]:  # If no users left, delete the session
            del sessions[session_id]


if __name__ == "__main__":
    uvicorn.run("__main__:app", host=get_server_ip(), port=8000, ssl_keyfile="key.pem", ssl_certfile="cert.pem", reload=True)

