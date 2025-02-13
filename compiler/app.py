from Demos.security.lsastore import retrieveddata
from flask import Flask, request, jsonify
import subprocess
import os

app = Flask(__name__)

LANGUAGE_COMMANDS = {
    "python": ["python3", "temp_code.py"],
    "javascript": ["node", "temp_code.js"],
    "c": ["gcc", "-o", "temp_code", "temp_code.c", "&&", "./temp_code"],
    "cpp": ["g++", "-o", "temp_code", "temp_code.cpp", "&&", "./temp_code"]
}
@app.route
def show():
    return "helo"


@app.route('/api/compile', methods=['POST'])
def compile_code():
    data = request.json
    code = data.get('code', '')
    language = data.get('language', 'python')

    if not code:
        return jsonify({"output": "No code provided."})

    try:
        file_extension = {
            "python": "py",
            "javascript": "js",
            "c": "c",
            "cpp": "cpp"
        }.get(language, "txt")

        file_name = f"temp_code.{file_extension}"

        # Write the code to a temporary file
        with open(file_name, "w") as code_file:
            code_file.write(code)

        # Execute the code
        command = LANGUAGE_COMMANDS.get(language)
        if not command:
            return jsonify({"output": "Unsupported language."})

        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            text=True
        )

        # Remove the temporary file after execution
        os.remove(file_name)

        output = result.stdout + result.stderr
        return jsonify({"output": output})
    except Exception as e:
        return jsonify({"output": f"Error executing code: {str(e)}"})


if __name__ == '__main__':
    app.run(port=5000, debug=True)
