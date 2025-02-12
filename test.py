import strawberry
import mysql.connector
import bcrypt
import jwt
import datetime
from typing import Optional
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter


#ประกาศ secret key
SECRET_KEY = "12345"

# Database connection function
def get_db_connection():
    return mysql.connector.connect(
        host="158.108.237.9",
        port=3306,
        user="bell77m",
        password="12345678",
        database="chat_db"
    )

# Define User type
@strawberry.type
class User:
    id: int
    name: str
    email: str

@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "Hello, GraphQL"
    
    @strawberry.field
    def get_users(self) -> list[User]:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id, name, email FROM users")
        result = cursor.fetchall()

        users = [User(id=row[0], name=row[1], email=row[2]) for row in result]

        cursor.close()
        conn.close()

        return users

# Mutation to add a user
@strawberry.type
class Mutation:
    @strawberry.mutation
    def signup(self, name: str, email: str, password: str) -> Optional[User]:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Hash the password before storing it
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Insert user into the database with hashed password
        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
            (name, email, hashed_password)
        )
        conn.commit()
        
        # Get the inserted user's ID
        user_id = cursor.lastrowid

        # Generate JWT token for the user
        token = jwt.encode(
            {"user_id": user_id, "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)},  # Token expires in 1 hour
            SECRET_KEY,
            algorithm="HS256"
        )

        # Close connection
        cursor.close()
        conn.close()

        return User(id=user_id, name=name, email=email),token

# Create the schema
schema = strawberry.Schema(query=Query, mutation=Mutation)

# FastAPI setup
app = FastAPI()
app.include_router(GraphQLRouter(schema), prefix="/graphql")
