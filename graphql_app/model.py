from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    display_name = Column(String(255), nullable=True)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    password_updated_at = Column(DateTime, nullable=False, default=func.now())
    reset_token = Column(String(100), nullable=True, default=None)
    created_at = Column(DateTime, nullable=False, default=func.now())
    reset_token_expiry = Column(DateTime, nullable=True)
    login_attempts = Column(Integer, nullable=False, default=0)
    account_locked = Column(Boolean, nullable=False, default=False)
    lock_time = Column(DateTime, nullable=True)
    
    profile_picture_url = Column(
        String(500), 
        nullable=False, 
        default="https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_640.png"
    )

    def __repr__(self):
        return f"<User(id={self.id}, display_name={self.display_name}, email={self.email})>"
