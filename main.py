import socket
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from graphql_app.schema import schema
from strawberry.fastapi import GraphQLRouter
from config.config import Config

def get_local_ip() -> str:
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        return local_ip
    except Exception as e:
        print(f" Error getting local IP: {str(e)}")
        return "127.0.0.1"  

def get_domain_name() -> str:
    
    return "graphql.example.com" 


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://graphql.example.com"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"], 
)


graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")


def run():
    conf = Config("config/config.ini")
    
    db_config = conf.load_db_config()
    server_config = conf.load_server_config()

    local_ip = get_local_ip()
    domain_name = get_domain_name()

    db_config["host"] = local_ip
    server_config["host"] = domain_name
    
    print(f"🚀 Running server on http://{domain_name}:{server_config['port']}")
    
    uvicorn.run("main:app", host=server_config["host"], port=int(server_config["port"]), reload=True)


if __name__ == "__main__":
    run()



