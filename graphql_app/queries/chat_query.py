import strawberry
from typing import List, Optional
from user_gateway import UserGateway
from friend_gateway import FriendGateway
from chat_gateway import ChatGateway
from notification_gateway import NotificationGateway
from forum_gateway import ForumGateway
from graphql_app.Types import  UserType, NotificationType, FriendRequestType
from graphql_app.Types import ChatMessageType, FriendChatSummary
from graphql_app.Types import ForumPostType, ForumCommentType, ForumPostDetailType
from graphql_app.database import SessionLocal
from graphql_app.model import User, Friend

@strawberry.type
class ChatQuery:
    
    @strawberry.field
    def get_chat_messages(self, user_id: int, friend_id: int) -> List[ChatMessageType]:
        """ ดึงข้อความแชทระหว่าง user_id และ friend_id """
    
        print(f"📢 DEBUG: get_chat_messages called with user_id={user_id}, friend_id={friend_id}")  # ✅ เช็คว่า Query ทำงาน
    
        messages = ChatGateway.get_messages(user_id, friend_id)
    
        print("🔍 DEBUG: Retrieved Messages ->", messages)  # ✅ ดูว่ามีข้อมูลหรือไม่
    
        return [ChatMessageType(
            id=m.id, sender_id=m.sender_id, message=m.message, image_url=m.image_url,
            is_read=m.is_read, sent_at=str(m.sent_at)
        ) for m in messages]


    @strawberry.field
    def get_friend_chat(self, user_id: int) -> List[FriendChatSummary]:
        friends = ChatGateway.get_friends_with_last_message(user_id)
        return [FriendChatSummary(**friend) for friend in friends]
    
   