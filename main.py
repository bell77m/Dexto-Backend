import uvicorn
from fastapi import FastAPI
from graphql_app.schema import schema
from strawberry.fastapi import GraphQLRouter
from config.config import Config

# สร้างแอพ FastAPI
app = FastAPI()

# สร้าง router สำหรับ GraphQL
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")

# ฟังก์ชั่นที่ใช้รันแอพ FastAPI
def run():
    conf = Config("config/config.ini")
    server_config = conf.load_server_config()
    uvicorn.run("main:app", host=server_config["host"], port=int(server_config["port"]), reload=True)

# รันเซิร์ฟเวอร์
if __name__ == "__main__":
    run()



#  python main.py

    # cursor = mydb.cursor()
    # cursor.execute("SHOW DATABASES")
    # for db in cursor.fetchall():
    #     print(db)
    
# python -m uvicorn main:app --host 10.6.38.146 --port 3000 --reload 
# python -m uvicorn main:app --reload
    
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
#   createUser(displayName: "John Doe", email: "john@example.com", password: "123456") {
#     id
#     displayName
#     email
#   }
# }

# mutation {
#   updateUser(id: 1, displayName: "Updated Name", email: "updated@example.com") {
#     id
#     displayName
#     email
#   }
# }

# mutation {
#   deleteUser(id: 3)
# }