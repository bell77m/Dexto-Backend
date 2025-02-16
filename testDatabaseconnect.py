import mysql.connector

# Connect to MySQL database
conn = mysql.connector.connect(
    host="10.6.38.146",
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

# run อย่าลืม cd เข้า file
# c

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
