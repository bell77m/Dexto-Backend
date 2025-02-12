import strawberry
import mysql.connector
from typing import Optional
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter

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

# Mutation to add a user
@strawberry.type
class Mutation:
    @strawberry.mutation
    def signup(self, name: str, email: str, password: str) -> Optional[User]:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert user into the database
        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
            (name, email, password)
        )
        conn.commit()
        
        # Get the inserted user's ID
        user_id = cursor.lastrowid

        # Close connection
        cursor.close()
        conn.close()

        return User(id=user_id, name=name, email=email)

# Create the schema
schema = strawberry.Schema(mutation=Mutation)

# FastAPI setup
app = FastAPI()
app.include_router(GraphQLRouter(schema), prefix="/graphql")
