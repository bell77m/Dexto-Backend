# pip install strawberry-graphql fastapi uvicorn sqlalchemy mysql-connector-python


import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="10.6.38.139",
        user="root",
        password="123456",
        database="dexto_demo7"
    )