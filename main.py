import socket
import psutil
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from graphql_app.schema import schema
from strawberry.fastapi import GraphQLRouter
from config.config import Config
import uvicorn
import requests

# No-IP Credentials
NOIP_USERNAME = "domdypol@gmail.com"
NOIP_PASSWORD = "Dompol19#"
NOIP_HOSTNAME = "sedexto.ddns.net"

def get_local_ip() -> str:
    """หาหมายเลข IP ของ VPN Interface โดยใช้ psutil"""
    try:
        for interface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == socket.AF_INET and addr.address.startswith("10.6.38."):
                    return addr.address
        return "127.0.0.1"  # ถ้าไม่พบ VPN IP
    except Exception as e:
        print(f"Error getting local IP: {str(e)}")
        return "127.0.0.1"

def update_noip(ip: str):
    """อัปเดต IP บน No-IP ผ่าน HTTP Basic Auth"""
    try:
        url = f"https://dynupdate.no-ip.com/nic/update?hostname={NOIP_HOSTNAME}&myip={ip}"
        response = requests.get(url, auth=(NOIP_USERNAME, NOIP_PASSWORD))
        print(f"[No-IP] Response: {response.text}")

    except Exception as e:
        print(f"[No-IP] Error updating: {str(e)}")

# สร้าง FastAPI App
app = FastAPI()

# ตั้งค่า CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"], 
)

# GraphQL API
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")

def run():
    """เริ่มรันเซิร์ฟเวอร์"""
    conf = Config("config/config.ini")
    
    db_config = conf.load_db_config()
    server_config = conf.load_server_config()

    local_ip = get_local_ip()
    db_config["host"] = local_ip
    server_config["host"] = local_ip

    # แสดงค่าที่จะใช้รันเซิร์ฟเวอร์
    print(f"🌍 Running FastAPI on: http://{local_ip}:{server_config['port']}/graphql")

    # อัปเดต No-IP ทุกครั้งที่รันเซิร์ฟเวอร์
    update_noip(local_ip)

    # รันเซิร์ฟเวอร์
    uvicorn.run("main:app", host="0.0.0.0", port=int(server_config["port"]), reload=True)

if __name__ == "__main__":
    run()
