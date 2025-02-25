import socket
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from graphql_app.schema import schema
from strawberry.fastapi import GraphQLRouter
from config.config import Config

def get_local_ip() -> str:
    """ฟังก์ชันเพื่อดึง IP ของเครื่องในเครือข่าย"""
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        return local_ip
    except Exception as e:
        print(f" Error getting local IP: {str(e)}")
        return "127.0.0.1"  # fallback to localhost if there's an error

# สร้างแอพ FastAPI
app = FastAPI()

# ตั้งค่า CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # หรือระบุเป็น URL ของ frontend ที่จะให้สามารถเข้าถึงได้
    allow_credentials=True,
    allow_methods=["*"],  # อนุญาตให้ใช้ทุก method (GET, POST, PUT, DELETE, ฯลฯ)
    allow_headers=["*"],  # อนุญาตให้ใช้ header ทั้งหมด
)


# สร้าง router สำหรับ GraphQL
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")


# ฟังก์ชั่นที่ใช้รันแอพ FastAPI
def run():
    conf = Config("config/config.ini")
    
    # โหลดการตั้งค่าจาก config.ini แต่กำหนด IP อัตโนมัติ
    db_config = conf.load_db_config()
    server_config = conf.load_server_config()

    # ดึง IP ที่ใช้งานจริงจากฟังก์ชัน
    local_ip = get_local_ip()

    # ตั้งค่า host ให้เป็น IP ที่ได้จากฟังก์ชัน get_local_ip()
    db_config["host"] = local_ip
    server_config["host"] = local_ip

    # ใช้ 'main:app' แทนการส่ง app โดยตรง
    uvicorn.run("main:app", host=server_config["host"], port=int(server_config["port"]), reload=True)


# รันเซิร์ฟเวอร์เมื่อเรียกไฟล์นี้
if __name__ == "__main__":
    run()



#  python main.py

    # cursor = mydb.cursor()
    # cursor.execute("SHOW DATABASES")
    # for db in cursor.fetchall():
    #     print(db)
    
# python -m uvicorn main:app --host 10.6.38.146 --port 3000 --reload 
# python -m uvicorn main:app --reload

# GRANT ALL PRIVILEGES ON *.* TO 'root'@'10.6.38.160' IDENTIFIED BY '123456';
# FLUSH PRIVILEGES;

    

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
