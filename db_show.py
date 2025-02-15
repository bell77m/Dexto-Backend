import mysql.connector
import ipconfig

# Connect to MySQL database
conn = mysql.connector.connect(
    host=ipconfig.ip,
    # host="127.0.0.1",
    port = 3306,
    user="root",
    password="123456",
    database="dexto_demo7"
)

# Create a cursor object
cursor = conn.cursor()

cursor.execute("SELECT * FROM users")

# Fetch all results
users = cursor.fetchall()

# Print results
for user in users:
    print(user)

# Close the connection
conn.close()