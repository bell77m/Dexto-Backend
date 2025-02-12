# pip install strawberry-graphql fastapi uvicorn sqlalchemy mysql-connector-python

import strawberry
from fastapi import FastAPI
from strawberry.asgi import GraphQL
from schema2 import schema
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

graphql_app = GraphQL(schema)

app.add_route("/graphql", graphql_app)
app.add_websocket_route("/graphql", graphql_app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # อนุญาตทุกโดเมน ถ้าจะจำกัดให้ใส่ ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],  # อนุญาตทุก Method เช่น GET, POST, OPTIONS
    allow_headers=["*"],  # อนุญาตทุก Header
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="10.6.38.139", port=3000)

# run อย่าลืม cd เข้า file 
# python -m uvicorn main:app --host 10.6.38.139 --port 3000 --reload

#  mutation {
#   createUser(email: "john.doe@example.com", displayName: "John Doe", password: "securepassword") {
#     displayName 
#     email
#   }
# }


# mutation {
#   updateUser(id: 1, name: "John Smith", status: true) {
#     id
#     name
#     status
#   }
# }

# mutation {
#   deleteUser(id: 1)
# }


# query {
#     getUsers {
#     id
#     displayName
#     email
#     password
#   }
# }

# mutation {
#   loginUser(email: "dom@gmail.com", password: "123456") {
#     success
#     message
#     user {
#       id
#       displayName
#       email
#     }
#   }
# }

