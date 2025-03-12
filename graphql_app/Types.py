import strawberry
from typing import List, Optional

@strawberry.type
class UserType:
    id: int
    display_name: str
    email: str
    profile_picture_url: str
    request_sent: bool = False
    request_received: bool = False
    is_friend: bool = False

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
class FriendRequestType:
    id: int
    sender: UserType

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
    
@strawberry.type
class ChatMessageType:
    id: int
    sender_id: int
    message: Optional[str]
    image_url: Optional[str]
    is_read: bool
    sent_at: str
    
@strawberry.type
class FriendChatSummary:
    id: int
    displayName: str
    profilePictureUrl: str
    lastMessage: Optional[str]
    lastImage: Optional[str]
    lastMessageTime: Optional[float]
    lastIsRead: Optional[bool]
    
@strawberry.type
class ForumPostType:
    """ GraphQL Type สำหรับ Forum Post """
    id: int
    user_id: int  # ✅ เพิ่ม `user_id` ให้รองรับใน `searchPosts`
    title: str
    content: str
    image_url: Optional[str] = None  # ✅ ป้องกัน `None` error
    tags: Optional[str] = None
    likes: int
    created_at: str

@strawberry.type
class ForumLikeType:
    """ GraphQL Type สำหรับ Forum Like """
    id: int
    user_id: int
    post_id: int

@strawberry.type
class ForumCommentType:
    """ GraphQL Type สำหรับ Forum Comment """
    id: int
    post_id: int
    user_id: int
    parent_comment_id: Optional[int] = None  # ✅ รองรับค่า `None`
    content: str
    created_at: str
    user_profile: Optional[str] = None

@strawberry.type
class ForumPostDetailType:
    """ GraphQL Type ที่รวม Post และ Comments """
    post: ForumPostType
    comments: List[ForumCommentType]
