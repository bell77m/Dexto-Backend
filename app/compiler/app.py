from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn



app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/")
def hello():
    return {"message": "Hello World!!!!"}

if __name__ == "__main__":
    uvicorn.run("__main__:app", host="0.0.0.0", port=8002, reload=True, log_level="debug", workers=1)


