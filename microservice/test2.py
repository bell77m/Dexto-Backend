import mysql.connector

try:
    conn = mysql.connector.connect(
        host="10.6.38.144",
        user="root",
        password="123456",
        database="dexto_demo7"
    )
    print("Connected successfully!")
except mysql.connector.Error as err:
    print(f"Error: {err}")