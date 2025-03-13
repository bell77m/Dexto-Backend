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
class UserQuery:
    
    @strawberry.field
    def get_users(self) -> List[UserType]:
        users = UserGateway.get_users()
        print("🔍 DEBUG: Messages Retrieved ->")
        return [
            UserType(
                id=user.id, 
                display_name=user.display_name, 
                email=user.email, 
                profile_picture_url=user.profile_picture_url  
            ) 
            for user in users
        ]

    @strawberry.field
    def get_user_by_id(self, id: int) -> Optional[UserType]:
        user = UserGateway.get_user_by_id(id)
        if user:
            return UserType(
                id=user.id, 
                display_name=user.display_name, 
                email=user.email, 
                profile_picture_url=user.profile_picture_url 
            )
        return None