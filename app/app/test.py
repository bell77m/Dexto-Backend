import requests

# Define the URL of the FastAPI server
url = "http://127.0.0.1:12345/run"

# Define the payload (code files, language, and main file)
payload = {
  "files": {
    "main.go": ""
  },
  "language": "go",
  "main_file": "main.go"
}

# Send a POST request to the /run endpoint
response = requests.post(url, json=payload)

# Print the response from the server
print(response.json())