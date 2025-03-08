import strawberry
from typing import List, Optional
from user_gateway import UserGateway
from friend_gateway import FriendGateway
from notification_gateway import NotificationGateway
from .Types import UserType, NotificationType

@strawberry.type
class Query:
    @strawberry.field
    def get_users(self) -> List[UserType]:
        users = UserGateway.get_users()
        return [
            UserType(
                id=user.id, 
                display_name=user.display_name, 
                email=user.email, 
                profile_picture_url=user.profile_picture_url  # ✅ เพิ่มฟิลด์นี้
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
                profile_picture_url=user.profile_picture_url  # ✅ เพิ่มฟิลด์นี้
            )
        return None
    

    @strawberry.field
    def get_friends(self, user_id: int) -> List[UserType]:
        friends = FriendGateway.get_friends(user_id)
        return [
            UserType(
                id=friend.id,
                display_name=friend.display_name,
                email=friend.email,
                profile_picture_url=friend.profile_picture_url
            ) for friend in friends
        ]
        
    @strawberry.field
    def get_notifications(self, user_id: int) -> List[NotificationType]:
        """ ดึง Notification เฉพาะของผู้ใช้ """
        notifications = NotificationGateway.get_notifications(user_id)
        return [
            NotificationType(
                id=noti.id,
                user_id=noti.user_id,
                sender_id=noti.sender_id,
                type=noti.type,
                sent_at=str(noti.sent_at),
                is_read=noti.is_read
            ) for noti in notifications
        ]