import strawberry
from typing import List
from database import get_db_connection

@strawberry.type
class User:
    id: int
    display_name: str
    email: str

@strawberry.type
class LoginResponse:
    success: bool
    message: str
    user: User | None = None

@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_user(self, display_name: str, email: str, password: str) -> User:
        connection = get_db_connection()
        cursor = connection.cursor()

        query = "INSERT INTO users (display_name, email, password) VALUES (%s, %s, %s)"
        cursor.execute(query, (display_name, email, password))
        connection.commit()

        user_id = cursor.lastrowid
        cursor.close()
        connection.close()

        return User(id=user_id, display_name=display_name, email=email)

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

schema_users = strawberry.Schema(query=Query, mutation=Mutation)
