from config.config import Config
from graphql_app.schema import schema
from fastapi import FastAPI, File, UploadFile
from strawberry.fastapi import GraphQLRouter
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/excute")
async def excute():
    pass

# GraphQL endpoint
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")

# load server config
server_conf = Config("../config/config.ini")


