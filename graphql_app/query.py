import strawberry
from typing import List, Optional
from user_gateway import UserGateway
from friend_gateway import FriendGateway
from .Types import UserType

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
