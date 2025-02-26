import strawberry
from typing import List, Optional
from .Types import UserType, UsersType, LoginResponse
import bcrypt
import mysql.connector
from config.config import Config  

class UserGateway:
    @staticmethod
    def get_db_connection():
        try:
            conf = Config("config/config.ini")
            db_config = conf.load_db_config()

            conn = mysql.connector.connect(
                host=db_config['host'],
                user=db_config['user'],
                password=db_config['password'],
                database=db_config['database']
            )
            conn.autocommit = True
            return conn
        except mysql.connector.Error as e:
            raise Exception(f"Database connection error: {e}")

    @classmethod
    def get_users(cls) -> List[UserType]:
        conn = cls.get_db_connection()
        if not conn:
            return []

        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT id, display_name, email FROM users')
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [UserType(**row) for row in rows]

    @classmethod
    def get_user_by_id(cls, id: int) -> Optional[UserType]:
        conn = cls.get_db_connection()
        if not conn:
            return None

        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT id, display_name, email FROM users WHERE id = %s', (id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return UserType(**row) if row else None

    @classmethod
    def add_user(cls, display_name: str, email: str, password: str) -> Optional[UserType]:
        try:
            email = email.strip().lower()
            display_name = display_name.strip()
            hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode('utf-8')
            conn = cls.get_db_connection()
            if not conn:
                return None

            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                cursor.close()
                conn.close()
                raise ValueError("Email already in use")

            cursor.execute(
                'INSERT INTO users (display_name, email, password) VALUES (%s, %s, %s)',
                (display_name, email, hashed_pw)
            )
            new_id = cursor.lastrowid
            cursor.close()
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

        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE id = %s', (id,))
        row = cursor.fetchone()
        if not row:
            cursor.close()
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
            hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode('utf-8')
            updates.append("password = %s")
            values.append(hashed_pw)

        if not updates:
            cursor.close()
            conn.close()
            return None

        values.append(id)
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = %s"
        cursor.execute(query, values)
        cursor.close()
        conn.close()
        return cls.get_user_by_id(id)

    @classmethod
    def delete_user(cls, id: int) -> bool:
        conn = cls.get_db_connection()
        if not conn:
            return False

        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE id = %s', (id,))
        deleted = cursor.rowcount > 0
        cursor.close()
        conn.close()
        return deleted
    
    @classmethod
    def login_user(cls, email: str, password: str) -> Optional[UserType]:
        email = email.strip().lower()
        print(f"Attempting login for email: {email}")
        conn = cls.get_db_connection()
        if not conn:
            raise ValueError("Database connection failed")

        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT id, display_name, email, password FROM users WHERE email = %s", (email,))
            row = cursor.fetchone()
            if not row:
                raise ValueError("Invalid email")

            if bcrypt.checkpw(password.encode('utf-8'), row['password'].encode('utf-8')):
                return UserType(**{k: v for k, v in row.items() if k != 'password'})
            raise ValueError("Wrong password")
        finally:
            cursor.close()
            conn.close()

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
    
    @strawberry.mutation
    def login_user(self, email: str, password: str) -> LoginResponse:
        try:
            user = UserGateway.login_user(email, password)
            return LoginResponse(success=True, message="Login successful!", user=user) if user else LoginResponse(success=False, message="Invalid email or password", user=None)
        except ValueError as e:
            return LoginResponse(success=False, message=str(e), user=None)