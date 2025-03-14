import tempfile
import uvicorn
import platform
import shutil
import mimetypes
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
import subprocess
import os
from fastapi.middleware.cors import CORSMiddleware
import asyncio  # Added this import here to ensure it's at the top of the file
app = FastAPI()

if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

active_connections = {}
@app.websocket("/ws/vc/{client_id}")
async def VC_websocket_endpoint(websocket: WebSocket, client_id: str):
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

