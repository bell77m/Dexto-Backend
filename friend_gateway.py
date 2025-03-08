from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from graphql_app.database import SessionLocal
from graphql_app.model import User, Friend
from typing import Optional, List

class FriendGateway:
    @staticmethod
    def get_db():
        """จัดการ Session ของ Database"""
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    @classmethod
    def send_friend_request(cls, user_id: int, friend_id: int) -> Optional[Friend]:
        """ ส่งคำขอเป็นเพื่อน """
        with SessionLocal() as db:
            if user_id == friend_id:
                raise ValueError("You cannot send a friend request to yourself.")
            
            existing_request = db.query(Friend).filter(
                ((Friend.user_id == user_id) & (Friend.friend_id == friend_id)) |
                ((Friend.user_id == friend_id) & (Friend.friend_id == user_id))
            ).first()

            if existing_request:
                raise ValueError("Friend request already exists.")

            new_request = Friend(user_id=user_id, friend_id=friend_id, status="pending")
            db.add(new_request)
            db.commit()
            db.refresh(new_request)
            return new_request

    @classmethod
    def accept_friend_request(cls, user_id: int, friend_id: int) -> bool:
        """ ยอมรับคำขอเป็นเพื่อน """
        with SessionLocal() as db:
            request = db.query(Friend).filter(
                (Friend.user_id == friend_id) & (Friend.friend_id == user_id) & (Friend.status == "pending")
            ).first()

            if not request:
                return False

            request.status = "accepted"
            request.accepted_at = func.now()
            db.commit()
            return True

    @classmethod
    def reject_friend_request(cls, user_id: int, friend_id: int) -> bool:
        """ ปฏิเสธคำขอเป็นเพื่อน """
        with SessionLocal() as db:
            request = db.query(Friend).filter(
                (Friend.user_id == friend_id) & (Friend.friend_id == user_id) & (Friend.status == "pending")
            ).first()

            if not request:
                return False

            request.status = "rejected"
            db.commit()
            return True

    @classmethod
    def cancel_friend_request(cls, user_id: int, friend_id: int) -> bool:
        """ ยกเลิกคำขอเป็นเพื่อน (กรณียังอยู่ใน pending) """
        with SessionLocal() as db:
            request = db.query(Friend).filter(
                (Friend.user_id == user_id) & (Friend.friend_id == friend_id) & (Friend.status == "pending")
            ).first()

            if not request:
                return False

            db.delete(request)
            db.commit()
            return True

    @classmethod
    def get_friends(cls, user_id: int) -> List[User]:
        """ ดึงรายชื่อเพื่อนทั้งหมดที่เป็น 'accepted' """
        with SessionLocal() as db:
            friends = db.query(Friend).filter(
                ((Friend.user_id == user_id) | (Friend.friend_id == user_id)) & (Friend.status == "accepted")
            ).all()

            friend_list = []
            for f in friends:
                friend_user = db.query(User).filter(User.id == (f.friend_id if f.user_id == user_id else f.user_id)).first()
                friend_list.append(friend_user)

            return friend_list

    @classmethod
    def unfriend(cls, user_id: int, friend_id: int) -> bool:
        """ ลบเพื่อนออกจากระบบ """
        with SessionLocal() as db:
            friendship = db.query(Friend).filter(
                ((Friend.user_id == user_id) & (Friend.friend_id == friend_id)) |
                ((Friend.user_id == friend_id) & (Friend.friend_id == user_id))
            ).first()

            if not friendship:
                return False

            db.delete(friendship)
            db.commit()
            return True
