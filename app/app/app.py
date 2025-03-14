import asyncio  # Added this import here to ensure it's at the top of the file
import json
import os
import platform
import subprocess
import tempfile
from datetime import datetime, timedelta
from typing import Dict, Optional, Set, Any, List

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



# Git-related models
class GitAddRequest(BaseModel):
    files: List[str]


class GitRestoreRequest(BaseModel):
    files: List[str]


class GitCommitRequest(BaseModel):
    message: str
    author: Optional[str] = None
    email: Optional[str] = None


class GitRemoteRequest(BaseModel):
    name: str
    url: str


class GitCredentials(BaseModel):
    username: str
    password: str


class GitPushRequest(BaseModel):
    remote: str
    branch: str
    credentials: Optional[GitCredentials] = None


class GitBranchRequest(BaseModel):
    name: str


class GitCheckoutRequest(BaseModel):
    branch: str

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





# Git utilities
def run_git_command(command, cwd=UPLOADS_DIR, timeout=30, env=None):
    """Run a git command and return the output"""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout,
            cwd=cwd,
            env=env
        )
        return {"success": True, "output": result.stdout.strip()}
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": e.stderr.strip() or e.stdout.strip() or str(e)}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# Git endpoints
@app.post("/git/init")
def init_git_repo():
    """Initialize git repository"""
    result = run_git_command(["git", "init"])
    if result["success"]:
        return {"success": True, "message": "Git repository initialized successfully"}
    return {"success": False, "error": result["error"]}


@app.get("/git/status")
def get_git_status():
    """Get git repository status"""
    # Check if it's a git repository
    is_repo = run_git_command(["git", "rev-parse", "--is-inside-work-tree"])
    if not is_repo["success"]:
        return {"isRepo": False, "modified": [], "staged": [], "untracked": []}

    # Get current branch
    branch_result = run_git_command(["git", "branch", "--show-current"])
    branch = branch_result["output"] if branch_result["success"] else None

    # Get status in porcelain format for easy parsing
    status_result = run_git_command(["git", "status", "--porcelain"])

    if not status_result["success"]:
        return {"isRepo": True, "branch": branch, "modified": [], "staged": [], "untracked": []}

    status_output = status_result["output"]

    # Parse porcelain output
    modified = []
    staged = []
    untracked = []

    for line in status_output.split("\n"):
        if not line.strip():
            continue

        status_code = line[:2]
        filename = line[3:].strip()  # Ensure we strip any extra whitespace

        # Skip .git directory entries if they appear
        if filename.startswith(".git/"):
            continue

        if status_code == "??":
            untracked.append(filename)
        elif status_code[0] == "M":
            staged.append(filename)
        elif status_code[1] == "M":
            modified.append(filename)
        elif status_code[0] in ["A", "D", "R", "C"]:
            staged.append(filename)
        elif status_code[1] in ["A", "D", "R", "C", "M"]:
            modified.append(filename)

    return {
        "isRepo": True,
        "branch": branch,
        "modified": modified,
        "staged": staged,
        "untracked": untracked
    }


@app.post("/git/add")
def add_files(request: GitAddRequest):
    """Stage files for commit"""
    if not request.files:
        return {"success": False, "error": "No files specified"}

    command = ["git", "add"]
    command.extend(request.files)

    result = run_git_command(command)
    if result["success"]:
        return {"success": True, "message": f"Added {len(request.files)} files"}
    return {"success": False, "error": result["error"]}


@app.post("/git/restore")
def restore_files(request: GitRestoreRequest):
    """Unstage files"""
    if not request.files:
        return {"success": False, "error": "No files specified"}

    command = ["git", "restore", "--staged"]
    command.extend(request.files)

    result = run_git_command(command)
    if result["success"]:
        return {"success": True, "message": f"Unstaged {len(request.files)} files"}
    return {"success": False, "error": result["error"]}


@app.post("/git/commit")
def commit_changes(request: GitCommitRequest):
    """Commit staged changes"""
    command = ["git", "commit", "-m", request.message]

    # Set author if provided
    env = os.environ.copy()
    if request.author and request.email:
        env["GIT_COMMITTER_NAME"] = request.author
        env["GIT_COMMITTER_EMAIL"] = request.email
        env["GIT_AUTHOR_NAME"] = request.author
        env["GIT_AUTHOR_EMAIL"] = request.email

    result = run_git_command(command, env=env)
    if result["success"]:
        return {"success": True, "message": "Changes committed successfully"}
    return {"success": False, "error": result["error"]}


@app.post("/git/remote/add")
def add_remote(request: GitRemoteRequest):
    """Add a remote repository"""
    command = ["git", "remote", "add", request.name, request.url]

    result = run_git_command(command)
    if result["success"]:
        return {"success": True, "message": f"Remote '{request.name}' added successfully"}
    return {"success": False, "error": result["error"]}


@app.post("/git/push")
def push_changes(request: GitPushRequest):
    """Push changes to remote repository"""
    command = ["git", "push", request.remote, request.branch]

    # Set credentials if provided
    env = os.environ.copy()
    if request.credentials:
        git_credential = f"https://{request.credentials.username}:{request.credentials.password}@github.com"
        env["GIT_ASKPASS"] = "echo"
        env["GIT_TERMINAL_PROMPT"] = "0"
        env["GCM_INTERACTIVE"] = "never"

        # Create a temporary credential helper script
        helper_script = os.path.join(UPLOADS_DIR, ".git-credentials-helper.sh")
        with open(helper_script, "w") as f:
            f.write(f"#!/bin/sh\necho {git_credential}")
        os.chmod(helper_script, 0o755)

        command = ["git", "-c", f"credential.helper={helper_script}", "push", request.remote, request.branch]

    result = run_git_command(command, env=env, timeout=60)

    # Clean up helper script if it exists
    if request.credentials and os.path.exists(helper_script):
        os.remove(helper_script)

    if result["success"]:
        return {"success": True, "message": f"Changes pushed to {request.remote}/{request.branch} successfully"}
    return {"success": False, "error": result["error"]}


@app.post("/git/pull")
def pull_changes(request: GitPushRequest):
    """Pull changes from remote repository"""
    command = ["git", "pull", request.remote, request.branch]

    # Set credentials if provided
    env = os.environ.copy()
    if request.credentials:
        git_credential = f"https://{request.credentials.username}:{request.credentials.password}@github.com"
        env["GIT_ASKPASS"] = "echo"
        env["GIT_TERMINAL_PROMPT"] = "0"
        env["GCM_INTERACTIVE"] = "never"

        # Create a temporary credential helper script
        helper_script = os.path.join(UPLOADS_DIR, ".git-credentials-helper.sh")
        with open(helper_script, "w") as f:
            f.write(f"#!/bin/sh\necho {git_credential}")
        os.chmod(helper_script, 0o755)

        command = ["git", "-c", f"credential.helper={helper_script}", "pull", request.remote, request.branch]

    result = run_git_command(command, env=env, timeout=60)

    # Clean up helper script if it exists
    if request.credentials and os.path.exists(helper_script):
        os.remove(helper_script)

    if result["success"]:
        return {"success": True, "message": f"Changes pulled from {request.remote}/{request.branch} successfully"}
    return {"success": False, "error": result["error"]}


@app.get("/git/log")
def get_commit_logs(limit: int = 10):
    """Get commit history"""
    command = ["git", "log", f"-{limit}", "--pretty=format:%H|%an|%ae|%ad|%s"]

    result = run_git_command(command)
    if not result["success"]:
        return []

    logs = []
    for line in result["output"].split("\n"):
        if not line.strip():
            continue

        parts = line.split("|")
        if len(parts) >= 5:
            logs.append({
                "hash": parts[0],
                "author": parts[1],
                "email": parts[2],
                "date": parts[3],
                "message": parts[4]
            })

    return logs


@app.post("/git/branch")
def create_branch(request: GitBranchRequest):
    """Create a new branch"""
    command = ["git", "branch", request.name]

    result = run_git_command(command)
    if result["success"]:
        return {"success": True, "message": f"Branch '{request.name}' created successfully"}
    return {"success": False, "error": result["error"]}


@app.post("/git/checkout")
def checkout_branch(request: GitCheckoutRequest):
    """Switch to a branch"""
    command = ["git", "checkout", request.branch]

    result = run_git_command(command)
    if result["success"]:
        return {"success": True, "message": f"Switched to branch '{request.branch}'"}
    return {"success": False, "error": result["error"]}


@app.get("/git/branches")
def list_branches():
    """List all branches"""
    command = ["git", "branch", "--format=%(refname:short)"]

    result = run_git_command(command)
    if not result["success"]:
        return []

    branches = [branch for branch in result["output"].split("\n") if branch.strip()]
    return branches

# Uncomment the following if you want to activate the cleanup task
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(cleanup_inactive_sessions())

