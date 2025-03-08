from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Enum, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    display_name = Column(String(255), nullable=True)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    password_updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    reset_token = Column(String(100), nullable=True, default=None)
    created_at = Column(DateTime, nullable=False, default=func.now())
    reset_token_expiry = Column(DateTime, nullable=True)
    login_attempts = Column(Integer, nullable=False, default=0)
    account_locked = Column(Boolean, nullable=False, default=False)
    lock_time = Column(DateTime, nullable=True)

    profile_picture_url = Column(
        String(500), 
        nullable=False, 
        default="https://static.vecteezy.com/system/resources/thumbnails/006/911/398/small_2x/rainbow-waves-background-free-vector.jpg"
    )

    friends = relationship("Friend", back_populates="user", foreign_keys="Friend.user_id")

    def __repr__(self):
        return f"<User(id={self.id}, display_name={self.display_name}, email={self.email})>"
    
class Friend(Base):
    __tablename__ = "friends"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    friend_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(Enum("pending", "accepted", "rejected"), nullable=False, default="pending")
    created_at = Column(DateTime, default=func.now())
    accepted_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="friends", foreign_keys=[user_id])
    friend = relationship("User", foreign_keys=[friend_id])

    __table_args__ = (
        UniqueConstraint('user_id', 'friend_id', name='unique_friendship'),
        CheckConstraint('user_id <> friend_id', name='check_no_self_friendship')
    )

    def __repr__(self):
        return f"<Friend(user_id={self.user_id}, friend_id={self.friend_id}, status={self.status})>"
