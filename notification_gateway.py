from graphql_app.model import Notification
from graphql_app.database import SessionLocal
from typing import List

class NotificationGateway:
    @classmethod
    def get_notifications(cls, user_id: int) -> List[Notification]:
        """ ดึง Notification เฉพาะของผู้ใช้ปลายทาง """
        with SessionLocal() as db:
            return db.query(Notification).filter(Notification.user_id == user_id).order_by(Notification.sent_at.desc()).all()

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
