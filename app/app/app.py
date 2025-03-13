import tempfile
import time
import platform
import shutil
import mimetypes
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
import subprocess
import os
from typing import Dict, List, Optional
import json
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

CODE_STORAGE = "code_storage"
UPLOADS_DIR = "uploaded_files"
os.makedirs(CODE_STORAGE, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)


class CodeRequest(BaseModel):
    files: dict
    language: str
    main_file: str


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


@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...), folder: Optional[str] = Form(None)):
    """Upload one or more files to the server. Optionally specify a folder path."""
    result = {}

    for file in files:
        # Create safe filename
        filename = file.filename
        if not filename:
            continue

        # Create folder path if specified
        if folder:
            # Sanitize folder path
            folder_path = os.path.normpath(folder).lstrip('/')
            save_path = os.path.join(UPLOADS_DIR, folder_path)
            os.makedirs(save_path, exist_ok=True)
        else:
            save_path = UPLOADS_DIR

        # Full path to save the file
        file_path = os.path.join(save_path, filename)

        # Save the file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Add file info to result
        result[os.path.join(folder, filename) if folder else filename] = {
            "size": os.path.getsize(file_path),
            "type": mimetypes.guess_type(filename)[0] or "application/octet-stream"
        }

    return {"uploaded": result}


@app.get("/files")
def list_files():
    """List all files in the uploads directory"""
    files = []

    for root, dirs, filenames in os.walk(UPLOADS_DIR):
        rel_path = os.path.relpath(root, UPLOADS_DIR)

        for filename in filenames:
            if rel_path == ".":
                # File is in root
                files.append(filename)
            else:
                # File is in subdirectory
                files.append(os.path.join(rel_path, filename))

    return {"files": files}


@app.get("/files/{file_path:path}")
def get_file(file_path: str):
    """Retrieve a file from the uploads directory"""
    # Normalize and secure the path
    norm_path = os.path.normpath(file_path).lstrip('/')
    full_path = os.path.join(UPLOADS_DIR, norm_path)

    if not os.path.exists(full_path) or not os.path.isfile(full_path):
        raise HTTPException(404, "File not found")

    return FileResponse(
        full_path,
        headers={"Content-Disposition": f"attachment; filename={os.path.basename(file_path)}"}
    )


@app.delete("/files/{file_path:path}")
def delete_file(file_path: str):
    """Delete a file from the uploads directory"""
    # Normalize and secure the path
    norm_path = os.path.normpath(file_path).lstrip('/')
    full_path = os.path.join(UPLOADS_DIR, norm_path)

    if not os.path.exists(full_path):
        raise HTTPException(404, "File not found")

    if os.path.isfile(full_path):
        os.remove(full_path)
        return {"deleted": file_path}
    elif os.path.isdir(full_path):
        shutil.rmtree(full_path)
        return {"deleted": file_path, "type": "directory"}

    raise HTTPException(400, "Path is neither a file nor directory")


@app.post("/move")
def move_file(source: str, destination: str):
    """Move a file from one location to another"""
    # Normalize and secure the paths
    source_path = os.path.normpath(source).lstrip('/')
    dest_path = os.path.normpath(destination).lstrip('/')

    full_source = os.path.join(UPLOADS_DIR, source_path)
    full_dest = os.path.join(UPLOADS_DIR, dest_path)

    # Check if source exists
    if not os.path.exists(full_source):
        raise HTTPException(404, "Source file or folder not found")

    # Create destination directory if needed
    os.makedirs(os.path.dirname(full_dest), exist_ok=True)

    # Check if destination already exists
    if os.path.exists(full_dest):
        raise HTTPException(400, "Destination already exists")

    try:
        # Move the file or directory
        shutil.move(full_source, full_dest)
        return {"moved": {"from": source, "to": destination}}
    except Exception as e:
        raise HTTPException(500, f"Error moving file: {str(e)}")