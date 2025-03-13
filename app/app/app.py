import asyncio  # Added this import here to ensure it's at the top of the file
import json
import os
import platform
import subprocess
import tempfile
from datetime import datetime, timedelta
from typing import Dict, Optional, Set, Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Use SelectorEventLoop on Windows to avoid Proactor issues
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

app = FastAPI()

CODE_STORAGE = "code_storage"
UPLOADS_DIR = "uploaded_files"
os.makedirs(CODE_STORAGE, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)


# Model definitions
class CodeRequest(BaseModel):
    files: dict
    language: str
    main_file: str


class SessionCreate(BaseModel):
    session_id: Optional[str] = None
    user_name: str


class SessionJoin(BaseModel):
    session_id: str
    user_name: str


class EditorUpdate(BaseModel):
    session_id: str
    file_path: str
    content: str
    cursor_position: Optional[dict] = None
    user_id: str


class VoiceData(BaseModel):
    session_id: str
    user_id: str
    chunk_data: str  # Base64 encoded audio


# Session management
active_sessions: Dict[str, Dict[str, Any]] = {}
connected_clients: Dict[str, Set[WebSocket]] = {}
voice_clients: Dict[str, Dict[str, WebSocket]] = {}

SUPPORTED_LANGUAGES = {
    "python": "python",
    "javascript": "node",
    "go": "go"
}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Session cleanup background task
async def cleanup_inactive_sessions():
    while True:
        now = datetime.now()
        sessions_to_remove = []

        for session_id, session_data in active_sessions.items():
            last_activity = session_data.get("last_activity", now)
            # Remove sessions inactive for more than 24 hours
            if now - last_activity > timedelta(hours=24):
                sessions_to_remove.append(session_id)

        for session_id in sessions_to_remove:
            del active_sessions[session_id]
            if session_id in connected_clients:
                del connected_clients[session_id]
            if session_id in voice_clients:
                del voice_clients[session_id]

        await asyncio.sleep(3600)  # Check once per hour


def execute_command(command, timeout=10, cwd=None):
    """Execute command with directory context"""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd  # Added working directory parameter
        )
        output = result.stdout.strip()
        error = result.stderr.strip()

        if result.returncode != 0:
            return (result.returncode, f"{error}\n{output}" if error else output)
        return (0, output)
    except subprocess.TimeoutExpired:
        return (-1, "Error: Execution timed out")
    except Exception as e:
        return (-1, f"Error: {str(e)}")


@app.post("/run")
def run_code(request: CodeRequest):
    """Run code with multiple files and imports"""
    if request.language not in SUPPORTED_LANGUAGES:
        raise HTTPException(400, "Unsupported language")

    if not request.files or request.main_file not in request.files:
        raise HTTPException(400, "Invalid files")

    with tempfile.TemporaryDirectory() as temp_dir:
        # For Go files, we need to create the correct directory structure
        # based on the imports before writing the files
        if request.language == "go":
            # First, identify if any file is importing from temp_module/utils
            utils_files = {}
            main_files = {}

            for filename, content in request.files.items():
                if "/utils/" in filename or filename.startswith("utils/"):
                    utils_files[filename] = content
                else:
                    main_files[filename] = content

            # Use a fixed module name
            module_name = "temp_module"

            # Create the module directory structure
            utils_dir = os.path.join(temp_dir, "utils")
            os.makedirs(utils_dir, exist_ok=True)

            # Write utils files to utils directory
            for filename, content in utils_files.items():
                # Extract the base filename without any path components
                base_filename = os.path.basename(filename)
                file_path = os.path.join(utils_dir, base_filename)
                with open(file_path, "w") as f:
                    f.write(content)

            # Write main files to root directory
            for filename, content in main_files.items():
                file_path = os.path.join(temp_dir, os.path.basename(filename))
                with open(file_path, "w") as f:
                    f.write(content)
        else:
            # For non-Go languages, write files normally
            for filename, content in request.files.items():
                file_path = os.path.join(temp_dir, filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, "w") as f:
                    f.write(content)

        # Handle JavaScript ES modules
        if request.language == "javascript":
            # Check if any file has import/export statements
            has_es_modules = False
            for content in request.files.values():
                if "import " in content or "export " in content:
                    has_es_modules = True
                    break

            # Create package.json for ES modules support if needed
            if has_es_modules:
                package_json = {
                    "name": "temp-js-project",
                    "version": "1.0.0",
                    "type": "module"
                }

                package_path = os.path.join(temp_dir, "package.json")
                with open(package_path, "w") as f:
                    json.dump(package_json, f, indent=2)

        if request.language == "go":
            # Create go.mod with fixed module name
            go_mod_content = f"module {module_name}\ngo 1.21\n"
            go_mod_path = os.path.join(temp_dir, "go.mod")

            with open(go_mod_path, "w") as f:
                f.write(go_mod_content)

            # Configure binary name
            binary_name = "main.exe" if platform.system() == "Windows" else "main"
            binary_path = os.path.join(temp_dir, binary_name)

            # Build command with temp_dir as working directory
            build_command = ["go", "build", "-o", binary_path, "."]
            returncode, build_output = execute_command(
                build_command,
                timeout=15,
                cwd=temp_dir  # Crucial: Execute in temp directory
            )

            if returncode != 0:
                return {"output": f"Build failed:\n{build_output}"}

            if not os.path.exists(binary_path):
                return {"output": f"Error: Binary not found at {binary_path}"}

            run_command = [binary_path]
        else:
            main_path = os.path.join(temp_dir, request.main_file)
            run_command = [SUPPORTED_LANGUAGES[request.language], main_path]

        # Execute the command in temp directory context
        returncode, output = execute_command(run_command, cwd=temp_dir)
        return {"output": output}


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


# Uncomment the following if you want to activate the cleanup task
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(cleanup_inactive_sessions())

