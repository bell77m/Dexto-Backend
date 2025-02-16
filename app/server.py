from config.config import Config
from graphql_app.schema import schema
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from watchgod import run_process


app = FastAPI()
origins = [
    "http://localhost",
    "http://localhost:8080",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GraphQL endpoint
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")

# load server config
server_conf = Config("../config/config.ini")
def run():
    uvicorn.run(app, host=server_conf.load_server_config()["host"], port=int(server_conf.load_server_config()["port"]))

if __name__ == "__main__":
    #run sever
    run_process(".", run)

