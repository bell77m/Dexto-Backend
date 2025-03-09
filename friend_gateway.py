from graphql_app.model import User, Friend, Notification
from graphql_app.database import SessionLocal
from sqlalchemy.sql import func
from sqlalchemy.orm import joinedload
from typing import Optional, List

class FriendGateway:
    @classmethod
    def send_friend_request(cls, user_id: int, friend_id: int) -> Optional[Friend]:
        """ ส่งคำขอเป็นเพื่อน และสร้าง Notification """
        with SessionLocal() as db:
            if user_id == friend_id:
                raise ValueError("You cannot send a friend request to yourself.")

            existing_request = db.query(Friend).filter(
                ((Friend.user_id == user_id) & (Friend.friend_id == friend_id)) |
                ((Friend.user_id == friend_id) & (Friend.friend_id == user_id))
            ).first()

            if existing_request:
                raise ValueError("Friend request already exists.")

            # บันทึกคำขอเป็นเพื่อน
            new_request = Friend(user_id=user_id, friend_id=friend_id, status="pending")
            db.add(new_request)

            # บันทึกการแจ้งเตือน
            new_notification = Notification(
                user_id=friend_id,
                sender_id=user_id,
                type="friend_request"
            )
            db.add(new_notification)

            db.commit()
            db.refresh(new_request)
            return new_request

    @classmethod
    def accept_friend_request(cls, user_id: int, friend_id: int) -> bool:
        """ ยอมรับคำขอเป็นเพื่อน และสร้าง Notification """
        with SessionLocal() as db:
            request = db.query(Friend).filter(
                (Friend.user_id == friend_id) & (Friend.friend_id == user_id) & (Friend.status == "pending")
            ).first()

            if not request:
                return False

            request.status = "accepted"
            request.accepted_at = func.now()

            # บันทึกการแจ้งเตือน
            new_notification = Notification(
                user_id=friend_id,
                sender_id=user_id,
                type="friend_accept"
            )
            db.add(new_notification)

            db.commit()
            return True

    @classmethod
    def reject_friend_request(cls, user_id: int, friend_id: int) -> bool:
        """ ปฏิเสธคำขอเป็นเพื่อน (และลบออกจากฐานข้อมูล) """
        with SessionLocal() as db:
            request = db.query(Friend).filter(
                (Friend.user_id == friend_id) & (Friend.friend_id == user_id) & (Friend.status == "pending")
            ).first()

            if not request:
                return False

            # ลบคำขอเป็นเพื่อนออกจากฐานข้อมูล
            db.delete(request)
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
    
    @classmethod
    def get_friend_requests(cls, user_id: int):
        """ดึงรายการคำขอเป็นเพื่อนที่ส่งถึงปลายทาง (ผู้ใช้)"""
        with SessionLocal() as db:
            requests = db.query(Friend).options(
                joinedload(Friend.user) 
            ).filter(
                Friend.friend_id == user_id,  
                Friend.status == "pending"
            ).all()

            return requests
