from graphql_app.model import Notification, User
from graphql_app.database import SessionLocal
from typing import List, Dict

class NotificationGateway:
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
