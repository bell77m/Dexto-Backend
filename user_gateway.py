import bcrypt
from sqlalchemy.orm import Session
from graphql_app.database import SessionLocal
from graphql_app.model import User
from typing import Optional, List

class UserGateway:
    @staticmethod
    def get_db():
        """สร้างและคืนค่า Session ของฐานข้อมูล"""
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    @classmethod
    def get_users(cls) -> List[User]:
        """ดึงข้อมูลผู้ใช้ทั้งหมด"""
        with SessionLocal() as db:
            return db.query(User).all()

    @classmethod
    def get_user_by_id(cls, id: int) -> Optional[User]:
        """ดึงข้อมูลผู้ใช้โดย ID"""
        with SessionLocal() as db:
            return db.query(User).filter(User.id == id).first()

    @classmethod
    def add_user(cls, display_name: str, email: str, password: str) -> Optional[User]:
        """เพิ่มผู้ใช้ใหม่"""
        hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode('utf-8')

        with SessionLocal() as db:
            if db.query(User).filter(User.email == email).first():
                raise ValueError("Email already in use")

            new_user = User(display_name=display_name, email=email, password=hashed_pw)
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            return new_user

    @classmethod
    def update_user(cls, id: int, display_name: Optional[str] = None, email: Optional[str] = None,
                    password: Optional[str] = None) -> Optional[User]:
        """อัปเดตข้อมูลผู้ใช้"""
        with SessionLocal() as db:
            user = db.query(User).filter(User.id == id).first()
            if not user:
                return None

            if display_name:
                user.display_name = display_name
            if email:
                user.email = email
            if password:
                user.password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode('utf-8')

            db.commit()
            db.refresh(user)
            return user

    @classmethod
    def delete_user(cls, id: int) -> bool:
        """ลบผู้ใช้"""
        with SessionLocal() as db:
            user = db.query(User).filter(User.id == id).first()
            if not user:
                return False

            db.delete(user)
            db.commit()
            return True

    @classmethod
    def login_user(cls, email: str, password: str) -> Optional[User]:
        """ตรวจสอบการเข้าสู่ระบบ"""
        with SessionLocal() as db:
            user = db.query(User).filter(User.email == email).first()
            if not user or not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
                raise ValueError("Invalid email or password")
            return user
