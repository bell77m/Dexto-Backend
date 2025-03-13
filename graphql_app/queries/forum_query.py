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
class ForumQuery:
    
    @strawberry.field
    def search_posts(self, query: str) -> List[ForumPostType]:
        """ ค้นหาโพสต์พร้อมคอมเมนต์ทั้งหมด """
        posts = ForumGateway.search_posts(query)
        return [
            ForumPostType(
                id=post["id"],
                user_id=post["userId"],
                user_name=post["userName"],
                user_profile=post["userProfile"],
                title=post["title"],
                content=post["content"],
                image_url=post["imageUrl"],
                tags=post["tags"],
                likes=post["likes"],
                created_at=str(post["createdAt"]),
                comments=[
                    ForumCommentType(
                        id=comment["id"],
                        post_id=post["id"],
                        user_id=comment["userId"],
                        user_name=comment["userName"],
                        user_profile=comment["userProfile"],
                        content=comment["content"],
                        created_at=str(comment["createdAt"]),
                    )
                    for comment in post["comments"]
                ],
            )
            for post in posts
        ]
    
    @strawberry.field
    def get_comments(self, post_id: int) -> List[ForumCommentType]:
        """ ดึงคอมเมนต์ของโพสต์ """
        comments = ForumGateway.get_comments(post_id)
        return [
            ForumCommentType(
                id=c.id,
                user_id=c.user_id,
                post_id=c.post_id,
                user_name=c.user.display_name,  # ✅ เพิ่มชื่อของเจ้าของคอมเมนต์
                user_profile=c.user.profile_picture_url, 
                parent_comment_id=c.parent_comment_id,
                content=c.content,
                created_at=str(c.created_at)  # ✅ แปลง `datetime` เป็น `str`
            ) 
            for c in comments
        ]
 
    @strawberry.field
    def get_post_with_comments(self, post_id: int) -> ForumPostDetailType:
        """ ดึงโพสต์และคอมเมนต์ของโพสต์ """
        post = ForumGateway.get_post_by_id(post_id)  # ✅ เรียกฟังก์ชันใหม่
        if not post:
            return None

        comments = ForumGateway.get_comments(post_id)
        return ForumPostDetailType(
            post=ForumPostType(
                id=post.id,
                user_id=post.user_id,
                user_name=post.user.display_name,  # ✅ ดึงชื่อของเจ้าของโพสต์
                user_profile=post.user.profile_picture_url,
                title=post.title,
                content=post.content,
                image_url=post.image_url,
                tags=post.tags,
                likes=post.likes,
                created_at=str(post.created_at)
            ),
            comments=[
                ForumCommentType(
                    id=c.id, 
                    user_id=c.user_id, 
                    post_id=c.post_id, 
                    user_name=c.user.display_name,  # ✅ ดึงชื่อของเจ้าของคอมเมนต์
                    user_profile=c.user.profile_picture_url,
                    parent_comment_id=c.parent_comment_id,
                    content=c.content, 
                    created_at=str(c.created_at)
                ) 
                for c in comments
            ]
        )
    

   