import strawberry
from typing import Optional
from graphql_app.database import SessionLocal
from user_gateway import UserGateway
from friend_gateway import FriendGateway
from chat_gateway import ChatGateway
from forum_gateway import ForumGateway
from graphql_app.Types import UserType, LoginResponse, FriendType, FriendRequestResponse
from graphql_app.Types import ChatMessageType, FriendChatSummary
from graphql_app.Types import ForumPostType, ForumCommentType


@strawberry.type
class ChatMutation:
    
    @strawberry.mutation
    def send_message(self, user_id: int, friend_id: int, message: Optional[str] = None, image_url: Optional[str] = None) -> bool:
        """ ส่งข้อความหรือรูปภาพ """
        ChatGateway.send_message(user_id, friend_id, message, image_url)
        return True

    @strawberry.mutation
    def mark_messages_as_read(self, user_id: int, friend_id: int) -> bool:
        """ อัปเดต is_read เป็น True """
        ChatGateway.mark_messages_as_read(user_id, friend_id)
        return True