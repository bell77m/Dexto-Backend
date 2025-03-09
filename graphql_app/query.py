import strawberry
from typing import List, Optional
from user_gateway import UserGateway
from friend_gateway import FriendGateway
from notification_gateway import NotificationGateway
from .Types import  UserType, NotificationType, FriendRequestType
from graphql_app.database import SessionLocal
from graphql_app.model import User, Friend

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
        """ ดึง Notification พร้อมชื่อและอีเมลของผู้ส่ง """
        notifications = NotificationGateway.get_notifications(user_id)
        return [
            NotificationType(
                id=noti["id"],
                user_id=noti["user_id"],
                sender_id=noti["sender_id"],
                sender_name=noti["sender_name"],
                sender_email=noti["sender_email"],
                type=noti["type"],
                sent_at=noti["sent_at"],
                is_read=noti["is_read"]
            ) for noti in notifications
        ]

    @strawberry.field
    def search_users(self, query: str, user_id: int) -> List[UserType]:
        """ ค้นหาผู้ใช้จาก display_name หรือ email และไม่แสดงตัวเอง """
        users = NotificationGateway.search_users(query, user_id)
        return [
            UserType(
                id=user["id"],
                display_name=user["displayName"],
                email=user["email"],
                profile_picture_url=user["profilePictureUrl"],
                request_sent=user["requestSent"],
                request_received=user["requestReceived"],  # ✅ ดึงค่า requestReceived
                is_friend=user["isFriend"],  # ✅ ดึงค่า isFriend
            ) 
            for user in users
        ]
    
    @strawberry.field
    def get_friend_requests(self, user_id: int) -> List[FriendRequestType]:
        """ดึงรายการคำขอที่ส่งถึงปลายทาง"""
        requests = FriendGateway.get_friend_requests(user_id)
        return [
            FriendRequestType(
                id=req.id,
                sender=UserType(
                    id=req.user.id,
                    display_name=req.user.display_name,
                    email=req.user.email,
                    profile_picture_url=req.user.profile_picture_url
                )
            ) for req in requests
        ]


