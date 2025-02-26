# __init__.py
from fastapi import FastAPI
from .config import SECRET_KEY

app = FastAPI()

# You can define some routes or configurations here if needed
@app.get("/")
def read_root():
    return {"message": "Hello from the FastAPI microservice"}

# Any other setup code for the microservice can go here
