import strawberry
from typing import List
from database import get_db_connection

@strawberry.type
class Chatlog:
    id: int
    sender_id: int
    receiver_id: int
    message: str
    

# @strawberry.type
# class LoginResponse:
#     success: bool
#     message: str
#     user: User | None = None

@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_chatlog(self, sender_id: int, receiver_id: int, message: str) -> Chatlog:
        connection = get_db_connection()
        cursor = connection.cursor()

        query = "INSERT INTO chat_logs (sender_id, receiver_id, message) VALUES (%s, %s, %s)"
        cursor.execute(query, (id, sender_id, receiver_id, message))
        connection.commit()

        chatlog_id = cursor.lastrowid
        cursor.close()
        connection.close()

        return Chatlog(id=chatlog_id, sender_id=sender_id, receiver_id=receiver_id, message=message )

    @strawberry.mutation
    def update_user(self, id: int, display_name: str = None, password: str = None) -> User:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT id, display_name, email FROM users WHERE id = %s", (id,))
                user = cursor.fetchone()
                if not user:
                    raise Exception("User not found")

                updated_display_name = display_name if display_name is not None else user[1]
                updated_password = password if password is not None else user[3]

                cursor.execute(
                    "UPDATE users SET display_name = %s, password = %s WHERE id = %s",
                    (updated_display_name, updated_password, id)
                )
                connection.commit()

        return User(id=id, display_name=updated_display_name, email=user[2])

    @strawberry.mutation
    def login_user(self, email: str, password: str) -> LoginResponse:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT id, display_name, email FROM users WHERE email = %s AND password = %s", (email, password))
        user = cursor.fetchone()

        cursor.close()
        connection.close()

        if user:
            return LoginResponse(success=True, message="Login successful", user=User(id=user[0], display_name=user[1], email=user[2]))
        return LoginResponse(success=False, message="Invalid email or password")

@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "Hello, GraphQL!"

    @strawberry.field
    def get_users(self) -> List[User]:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT id, display_name, email FROM users")
        users = cursor.fetchall()
        cursor.close()
        connection.close()
        return [User(id=user[0], display_name=user[1], email=user[2]) for user in users]

schema_chatlogs = strawberry.Schema(query=Query, mutation=Mutation)
