from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Enum, UniqueConstraint, CheckConstraint, Text
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
        default="https://t4.ftcdn.net/jpg/00/64/67/63/360_F_64676383_LdbmhiNM6Ypzb3FM4PPuFP9rHe7ri8Ju.webp"
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

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type = Column(Enum("friend_request", "friend_accept", "project_invite"), nullable=False)
    sent_at = Column(DateTime, default=func.now())
    is_read = Column(Boolean, default=False)

    user = relationship("User", foreign_keys=[user_id])
    sender = relationship("User", foreign_keys=[sender_id])

    def __repr__(self):
        return f"<Notification(user_id={self.user_id}, sender_id={self.sender_id}, type={self.type})>"

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    message = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)
    is_read = Column(Boolean, default=False, nullable=False)
    sent_at = Column(DateTime, default=func.now(), nullable=False)

    sender = relationship("User", foreign_keys=[sender_id])
    receiver = relationship("User", foreign_keys=[receiver_id])