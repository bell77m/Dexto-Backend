import tempfile
import time
import platform
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess
import os
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

CODE_STORAGE = "code_storage"
os.makedirs(CODE_STORAGE, exist_ok=True)


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