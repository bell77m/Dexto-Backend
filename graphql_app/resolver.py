import strawberry
import bcrypt
from typing import List, Optional
import mysql.connector
from .Types import UserType, UsersType


class UserGateway:
    @staticmethod
    def get_db_connection():
        try:
            return mysql.connector.connect(
                host="10.6.38.144",
                user="root",
                password="123456",
                database="dexto_demo7"
            )
        except mysql.connector.Error as e:
            print(f"Database connection error: {e}")
            return None

    @classmethod
    def get_users(cls) -> List[UserType]:
        conn = cls.get_db_connection()
        if not conn:
            return []

        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT id, display_name, email FROM users')
        rows = cursor.fetchall()
        conn.close()

        return [UserType(id=row['id'], display_name=row['display_name'], email=row['email']) for row in rows]

    @classmethod
    def get_user_by_id(cls, id: int) -> Optional[UserType]:
        conn = cls.get_db_connection()
        if not conn:
            return None

        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT id, display_name, email FROM users WHERE id = %s', (id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return UserType(id=row['id'], display_name=row['display_name'], email=row['email'])
        return None

    @classmethod
    def add_user(cls, display_name: str, email: str, password: str) -> Optional[UserType]:
        try:
            hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
            conn = cls.get_db_connection()
            cursor = conn.cursor()

            # Check if the email already exists
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                conn.close()
                raise ValueError("Email already in use")

            cursor.execute(
                'INSERT INTO users (display_name, email, password) VALUES (%s, %s, %s)',
                (display_name, email, hashed_pw)
            )
            conn.commit()
            new_id = cursor.lastrowid
            conn.close()

            return UserType(id=new_id, display_name=display_name, email=email)

        except mysql.connector.Error as e:
            print("Database Error:", e)
            return None

    @classmethod
    def update_user(cls, id: int, display_name: Optional[str] = None, email: Optional[str] = None,
                    password: Optional[str] = None) -> Optional[UserType]:
        conn = cls.get_db_connection()
        if not conn:
            return None

        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT id FROM users WHERE id = %s', (id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None

        updates = []
        values = []
        if display_name:
            updates.append("display_name = %s")
            values.append(display_name)
        if email:
            updates.append("email = %s")
            values.append(email)
        if password:
            hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
            updates.append("password = %s")
            values.append(hashed_pw)

        if not updates:
            return None

        values.append(id)
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = %s"
        cursor.execute(query, values)
        conn.commit()
        conn.close()
        return cls.get_user_by_id(id)

    @classmethod
    def delete_user(cls, id: int) -> bool:
        conn = cls.get_db_connection()
        if not conn:
            return False

        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE id = %s', (id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False

        cursor.execute('DELETE FROM users WHERE id = %s', (id,))
        conn.commit()
        conn.close()
        return True


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "Hello World"

    @strawberry.field
    def users(self) -> UsersType:
        return UsersType(users=UserGateway.get_users())

    @strawberry.field
    def user(self, id: int) -> Optional[UserType]:
        return UserGateway.get_user_by_id(id)


@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_user(self, display_name: str, email: str, password: str) -> Optional[UserType]:
        return UserGateway.add_user(display_name, email, password)

    @strawberry.mutation
    def update_user(self, id: int, display_name: Optional[str] = None, email: Optional[str] = None,
                    password: Optional[str] = None) -> Optional[UserType]:
        return UserGateway.update_user(id, display_name, email, password)

    @strawberry.mutation
    def delete_user(self, id: int) -> bool:
        return UserGateway.delete_user(id)

    # testDom
