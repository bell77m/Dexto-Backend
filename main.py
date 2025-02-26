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

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
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

    db_config["host"] = local_ip
    server_config["host"] = local_ip
    
    uvicorn.run("main:app", host=server_config["host"], port=int(server_config["port"]), reload=True)


if __name__ == "__main__":
    run()



#  python main.py

    # cursor = mydb.cursor()
    # cursor.execute("SHOW DATABASES")
    # for db in cursor.fetchall():
    #     print(db)
    
# python -m uvicorn main:app --host 10.6.38.146 --port 3000 --reload 
# python -m uvicorn main:app --reload

# GRANT ALL PRIVILEGES ON *.* TO 'root'@'10.6.38.%' IDENTIFIED BY '123456';
# FLUSH PRIVILEGES;

# REVOKE ALL PRIVILEGES ON *.* FROM 'root'@'10.6.38.%';
# FLUSH PRIVILEGES;

# CHECK TABLE mysql.db, mysql.user, mysql.tables_priv, mysql.columns_priv;
# REPAIR TABLE mysql.db, mysql.user, mysql.tables_priv, mysql.columns_priv;

    

# query {
#   users {
#     users {
#       id
#       displayName
#       email
#     }
#   }
# }

# mutation {
#   createUser(displayName: "John Doe", email: "johndoe@example.com", password: "password123") {
#     id
#     displayName
#     email
#   }
# }

# mutation {
#   updateUser(id: 1, displayName: "U", email: "updated@example.com") {
#     id
#     displayName
#     email
#   }
# }

# mutation {
#   deleteUser(id: 1)
# }

# mutation {
#   loginUser(email: "dom2@gmail.com", password: "123") {
#     id
#     displayName
#     email
#   }
# }
