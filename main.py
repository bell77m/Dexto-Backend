import socket
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from graphql_app.schema import schema
from strawberry.fastapi import GraphQLRouter
from config.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from graphql_app.model import Base
from user_gateway import UserGateway

# ฟังก์ชันสำหรับดึง Local IP
def get_local_ip() -> str:
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        return local_ip
    except Exception as e:
        print(f"Error getting local IP: {str(e)}")
        return "127.0.0.1"

# ฟังก์ชันสำหรับดึง Domain Name
def get_domain_name() -> str:
    return "dexto.com"

# การตั้งค่า FastAPI
app = FastAPI()

# การตั้งค่า CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all domains for now (ปรับได้)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# GraphQL Router
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")

# ฟังก์ชันสำหรับเชื่อมต่อกับฐานข้อมูล
def get_db():
    conf = Config("config/config.ini")
    db_config = conf.load_db_config()

    # กำหนดค่าการเชื่อมต่อฐานข้อมูล (ใช้ IP 127.0.0.1)
    engine = create_engine(f"mysql+mysqlconnector://{db_config['user']}:{db_config['password']}@127.0.0.1/{db_config['database']}")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ฟังก์ชันสำหรับการเรียกใช้งาน GraphQL
def run():
    conf = Config("config/config.ini")
    db_config = conf.load_db_config()
    server_config = conf.load_server_config()

    # กำหนดที่อยู่ของ IP และ Domain สำหรับ FastAPI Server
    local_ip = get_local_ip()
    domain_name = get_domain_name()

    # ตั้งค่าการเชื่อมต่อฐานข้อมูลและ server
    db_config["host"] = "127.0.0.1"  # ตั้ง IP ของฐานข้อมูลเป็น 127.0.0.1
    server_config["host"] = local_ip  # ตั้ง IP ของ FastAPI server เป็น IP ที่ได้จากฟังก์ชัน

    print(f"Running server on http://{domain_name}:{server_config['port']}")

    # เรียกใช้งาน Uvicorn
    uvicorn.run("main:app", host=server_config["host"], port=int(server_config["port"]), reload=True)


# เรียกใช้งานฟังก์ชันในการรันแอปพลิเคชัน
if __name__ == "__main__":
    run()
