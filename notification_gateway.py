from graphql_app.model import Notification, User, Friend
from graphql_app.database import SessionLocal
from typing import List, Dict

class NotificationGateway:

    @classmethod
    def search_users(cls, query: str, user_id: int) -> List[Dict]:
        """ค้นหาผู้ใช้ โดยค้นหาจากชื่อ (display_name) เท่านั้น และตรวจสอบสถานะความเป็นเพื่อน และคำขอที่ส่งมา"""

        with SessionLocal() as db:
            # ค้นหาผู้ใช้จากชื่อ (display_name) เท่านั้น
            users = db.query(User).filter(
                User.display_name.ilike(f"%{query}%"),  # ค้นหาจากชื่อผู้ใช้
                User.id != user_id  # ยกเว้นตัวเอง
            ).all()

            friends = db.query(Friend).filter(
                (Friend.user_id == user_id) | (Friend.friend_id == user_id)
            ).all()

            friend_status = {}
            for friend in friends:
                key = (friend.user_id, friend.friend_id)
                reverse_key = (friend.friend_id, friend.user_id)

                if friend.status == "accepted":
                    friend_status[key] = "friend"
                    friend_status[reverse_key] = "friend"
                elif friend.status == "pending":
                    friend_status[key] = "sent"
                    friend_status[reverse_key] = "received"

            results = []
            for user in users:
                user_status = friend_status.get((user_id, user.id), None)
                request_sent = user_status == "sent"
                request_received = user_status == "received"
                is_friend = user_status == "friend"

                results.append({
                    "id": user.id,
                    "displayName": user.display_name,
                    "email": user.email,
                    "profilePictureUrl": user.profile_picture_url,
                    "requestSent": request_sent,
                    "requestReceived": request_received,
                    "isFriend": is_friend
                })

            return results
        
    @classmethod
    def get_notifications(cls, user_id: int) -> List[Dict]:
        """ ดึง Notification พร้อมข้อมูลของผู้ส่ง """
        with SessionLocal() as db:
            notifications = db.query(Notification, User).join(User, Notification.sender_id == User.id).filter(
                Notification.user_id == user_id
            ).order_by(Notification.sent_at.desc()).all()

            return [
                {
                    "id": noti.id,
                    "user_id": noti.user_id,
                    "sender_id": noti.sender_id,
                    "sender_name": sender.display_name,
                    "sender_email": sender.email,
                    "type": noti.type,
                    "sent_at": str(noti.sent_at),
                    "is_read": noti.is_read
                }
                for noti, sender in notifications
            ]


    @classmethod
    def mark_as_read(cls, notification_id: int) -> bool:
        """ ทำเครื่องหมายว่าอ่านแล้ว """
        with SessionLocal() as db:
            notification = db.query(Notification).filter(Notification.id == notification_id).first()
            if not notification:
                return False
            notification.is_read = True
            db.commit()
            return True
