import bcrypt
import mysql.connector
from config.config import Config  
from typing import List, Optional
from .Types import UserType

class UserGateway:
    @staticmethod
    def get_db_connection():
        """สร้างและคืนค่าการเชื่อมต่อฐานข้อมูล"""
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
            print(f"Database connection error: {e}")
            return None

    @classmethod
    def get_users(cls) -> List[UserType]:
        """ดึงข้อมูลผู้ใช้ทั้งหมด"""
        conn = cls.get_db_connection()
        if not conn:
            return []

        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT id, display_name, email FROM users')
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return [UserType(id=row['id'], display_name=row['display_name'], email=row['email']) for row in rows]

    @classmethod
    def get_user_by_id(cls, id: int) -> Optional[UserType]:
        """ดึงข้อมูลผู้ใช้โดย ID"""
        conn = cls.get_db_connection()
        if not conn:
            return None

        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT id, display_name, email FROM users WHERE id = %s', (id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if row:
            return UserType(id=row['id'], display_name=row['display_name'], email=row['email'])
        return None

    @classmethod
    def add_user(cls, display_name: str, email: str, password: str) -> Optional[UserType]:
        """เพิ่มผู้ใช้ใหม่"""
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
        """ตรวจสอบการเข้าสู่ระบบของผู้ใช้"""
        email = email.strip().lower()
        conn = cls.get_db_connection()
        if not conn:
            raise ValueError("Database connection failed")

        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, display_name, email, password FROM users WHERE email = %s", (email,))
        row = cursor.fetchone()

        if not row:
            cursor.close()
            conn.close()
            raise ValueError("Invalid email")

        if bcrypt.checkpw(password.encode('utf-8'), row['password'].encode('utf-8')):
            cursor.close()
            conn.close()
            return UserType(id=row['id'], display_name=row['display_name'], email=row['email'])

        cursor.close()
        conn.close()
        raise ValueError("Wrong password")
