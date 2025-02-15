# pip install strawberry-graphql fastapi uvicorn sqlalchemy mysql-connector-python

import ipconfig
import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host=ipconfig.ip,
        user="root",
        password="123456",
        database="dexto_demo7"
    )