import strawberry
from typing import List, Optional

@strawberry.type
class UserType:
    id: int
    display_name: str
    email: str
    profile_picture_url: str
    request_sent: bool = False

@strawberry.type
class LoginResponse:
    success: bool
    message: str
    user: Optional[UserType]

@strawberry.type
class FriendType:
    id: int
    user_id: int
    friend_id: int
    status: str
    created_at: str
    accepted_at: Optional[str] = None

@strawberry.type
class FriendRequestResponse:
    success: bool
    message: str

@strawberry.type
class NotificationType:
    id: int
    user_id: int
    sender_id: int
    sender_name: str
    sender_email: str
    type: str
    sent_at: str
    is_read: bool
