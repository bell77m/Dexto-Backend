from sqlalchemy.orm import joinedload
from sqlalchemy.sql import func
from graphql_app.database import SessionLocal
from graphql_app.model import ChatMessage, User, Friend
from typing import List, Optional

class ChatGateway:
    @staticmethod
    def send_message(sender_id: int, receiver_id: int, message: Optional[str] = None, image_url: Optional[str] = None):
        """ ส่งข้อความหรือรูปภาพ """
        with SessionLocal() as db:
            new_message = ChatMessage(
                sender_id=sender_id,
                receiver_id=receiver_id,
                message=message,
                image_url=image_url,
                is_read=False
            )
            db.add(new_message)
            db.commit()
            return new_message

    @staticmethod
    def get_messages(user_id: int, friend_id: int):
        """ ดึงข้อความแชทระหว่าง user_id และ friend_id """
        with SessionLocal() as db:
            messages = db.query(ChatMessage).filter(
                ((ChatMessage.sender_id == user_id) & (ChatMessage.receiver_id == friend_id)) |
                ((ChatMessage.sender_id == friend_id) & (ChatMessage.receiver_id == user_id))
            ).order_by(ChatMessage.sent_at.asc()).all()
        
            print(f"🔍 DEBUG: get_messages({user_id}, {friend_id}) ->", messages)  # ✅ ดูว่ามีข้อมูลหรือไม่
        
            return messages

    @staticmethod
    def mark_messages_as_read(user_id: int, friend_id: int):
        """ เปลี่ยนสถานะ is_read เป็น True """
        with SessionLocal() as db:
            db.query(ChatMessage).filter(
                (ChatMessage.sender_id == friend_id) &
                (ChatMessage.receiver_id == user_id) &
                (ChatMessage.is_read == False)
            ).update({"is_read": True})
            db.commit()

    @staticmethod
    def get_friends_with_last_message(user_id: int) -> List[dict]:
        """ ดึงรายชื่อเพื่อนทั้งหมดของ user และข้อความล่าสุด """
        with SessionLocal() as db:
            # ดึงเพื่อนทั้งหมด
            friends = db.query(User).join(Friend, ((Friend.user_id == user_id) & (Friend.friend_id == User.id)) |
                                          ((Friend.friend_id == user_id) & (Friend.user_id == User.id))).distinct().all()

            friend_list = []
            for friend in friends:
                last_msg = db.query(ChatMessage).filter(
                    ((ChatMessage.sender_id == user_id) & (ChatMessage.receiver_id == friend.id)) |
                    ((ChatMessage.sender_id == friend.id) & (ChatMessage.receiver_id == user_id))
                ).order_by(ChatMessage.sent_at.desc()).first()

                friend_list.append({
                    "id": friend.id,
                    "displayName": friend.display_name,
                    "profilePictureUrl": friend.profile_picture_url,
                    "lastMessage": last_msg.message if last_msg else None,
                    "lastImage": last_msg.image_url if last_msg else None,
                    "lastMessageTime": last_msg.sent_at.timestamp() if last_msg else None,
                    "lastIsRead": last_msg.is_read if last_msg else None
                })

            return sorted(friend_list, key=lambda f: f["lastMessageTime"] or 0, reverse=True)
