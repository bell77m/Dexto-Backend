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
class ForumMutation:
    
    @strawberry.mutation
    def create_post(self, user_id: int, title: str, content: str, tags: str, image_data: Optional[str] = None, image_url: Optional[str] = None) -> Optional[ForumPostType]:
        post = ForumGateway.create_post(user_id, title, content, tags, image_url)
        if post:
            return ForumPostType(
                id=post.id,
                user_id=post.user_id,
                user_name=post.user.display_name,  # ✅ เพิ่มชื่อของเจ้าของโพสต์
                user_profile=post.user.profile_picture_url,
                title=post.title,
                content=post.content,
                tags=post.tags,
                likes=post.likes,
                image_url=post.image_url,
                created_at=str(post.created_at),
                comments=[] # ✅ แปลงเป็น `str`
            )
        return None
    
    @strawberry.mutation
    def delete_post(self, user_id: int, post_id: int) -> bool:
        """ ลบโพสต์เฉพาะเจ้าของโพสต์เท่านั้น """
        return ForumGateway.delete_post(user_id, post_id)

    @strawberry.mutation
    def like_post(self, user_id: int, post_id: int) -> bool:
        return ForumGateway.like_post(user_id, post_id)

    @strawberry.mutation
    def add_comment(self, user_id: int, post_id: int, content: str, parent_comment_id: Optional[int] = None) -> Optional[ForumCommentType]:
        """ เพิ่มคอมเมนต์หรือคอมเมนต์ตอบกลับ """
        comment = ForumGateway.add_comment(user_id, post_id, content, parent_comment_id)
        if comment:
            return ForumCommentType(
                id=comment.id,
                user_id=comment.user_id,
                post_id=comment.post_id,
                user_name=comment.user.display_name,  # ✅ เพิ่มชื่อของเจ้าของคอมเมนต์
                user_profile=comment.user.profile_picture_url,
                parent_comment_id=comment.parent_comment_id,  # ✅ ส่งค่า `parent_comment_id`
                content=comment.content,
                created_at=str(comment.created_at)  # ✅ ส่งค่า `created_at`
            )
        return None