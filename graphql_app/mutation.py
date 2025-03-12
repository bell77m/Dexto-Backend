import strawberry
from typing import Optional
from user_gateway import UserGateway
from friend_gateway import FriendGateway
from chat_gateway import ChatGateway
from forum_gateway import ForumGateway
from .Types import UserType, LoginResponse, FriendType, FriendRequestResponse
from .Types import ChatMessageType, FriendChatSummary
from .Types import ForumPostType, ForumCommentType

@strawberry.type
class Mutation:
    @strawberry.mutation
    def add_user(self, display_name: str, email: str, password: str, profile_picture_url: Optional[str] = None) -> Optional[UserType]:
        user = UserGateway.add_user(display_name, email, password, profile_picture_url)
        if user:
            return UserType(
                id=user.id, 
                display_name=user.display_name, 
                email=user.email, 
                profile_picture_url=user.profile_picture_url
            )
        return None


    @strawberry.mutation
    def update_user(self, id: int, display_name: Optional[str] = None, email: Optional[str] = None, password: Optional[str] = None, profile_picture_url: Optional[str] = None) -> Optional[UserType]:
        """อัปเดตข้อมูลผู้ใช้"""
        user = UserGateway.update_user(id, display_name, email, password, profile_picture_url)
        if user:
            return UserType(id=user.id, display_name=user.display_name, email=user.email, profile_picture_url=user.profile_picture_url)
        return None
    
    @strawberry.mutation
    def update_user_avatar(self, id: int, profile_picture_url: str) -> Optional[UserType]:
        """อัปเดตรูปโปรไฟล์ของผู้ใช้"""
        
        # ตรวจสอบว่าค่า URL มีการส่งเข้ามาจริง
        if not profile_picture_url or not isinstance(profile_picture_url, str):
            raise ValueError("Invalid profile picture URL")
        
        user = UserGateway.update_user_avatar(id, profile_picture_url.strip()) # Trim ช่องว่างก่อนบันทึก
        if user:
            return UserType(
                id=user.id,
                display_name=user.display_name,
                email=user.email,
                profile_picture_url=user.profile_picture_url
            )
        return None

    @strawberry.mutation
    def delete_user(self, id: int) -> bool:
        return UserGateway.delete_user(id)

    @strawberry.mutation
    def login_user(self, email: str, password: str) -> LoginResponse:
        # เช็คว่า email หรือ password ไม่มีค่าหรือไม่
        if not email or not password:
            return LoginResponse(success=False, message="Email and password are required", user=None)

        try:
            # เช็คว่า email มีอยู่ในฐานข้อมูลหรือไม่
            user = UserGateway.get_user_by_email(email)

            # ถ้าไม่พบ email ในฐานข้อมูล
            if not user:
                return LoginResponse(success=False, message="Invalid email", user=None)

            # ถ้ามี email แต่รหัสผ่านไม่ถูกต้อง
            if not UserGateway.verify_password(user, password):
                return LoginResponse(success=False, message="Incorrect password", user=None)

            # ถ้ารหัสผ่านถูกต้อง
            return LoginResponse(
            success=True, 
            message="Login successful", 
            user=UserType(
                id=user.id, 
                display_name=user.display_name, 
                email=user.email,
                profile_picture_url=user.profile_picture_url, 
                request_sent=False
            )
        )

        except ValueError as e:
            # กรณีเกิดข้อผิดพลาดอื่นๆ
            return LoginResponse(success=False, message=str(e), user=None)
     
    @strawberry.mutation    
    def logout_user(self) -> bool:
        """ ออกจากระบบ (Logout) """
        # ถ้ามีระบบ Session ต้องทำการลบ Session ที่นี่ (เช่น Redis หรือ Database)
        # ถ้ามีระบบ JWT ให้ลบ Token หรือทำให้ Token ใช้ไม่ได้ (เช่น Blacklist)
        return True  # ✅ คืนค่า success = True
 
    @strawberry.mutation
    def send_friend_request(self, user_id: int, friend_id: int) -> FriendRequestResponse:
        try:
            FriendGateway.send_friend_request(user_id, friend_id)
            return FriendRequestResponse(success=True, message="Friend request sent successfully")
        except ValueError as e:
            return FriendRequestResponse(success=False, message=str(e))

    @strawberry.mutation
    def accept_friend_request(self, user_id: int, friend_id: int) -> FriendRequestResponse:
        if FriendGateway.accept_friend_request(user_id, friend_id):
            return FriendRequestResponse(success=True, message="Friend request accepted")
        return FriendRequestResponse(success=False, message="Friend request not found or already accepted")

    @strawberry.mutation
    def reject_friend_request(self, user_id: int, friend_id: int) -> FriendRequestResponse:
        if FriendGateway.reject_friend_request(user_id, friend_id):
            return FriendRequestResponse(success=True, message="Friend request rejected")
        return FriendRequestResponse(success=False, message="Friend request not found or already rejected")

    @strawberry.mutation
    def cancel_friend_request(self, user_id: int, friend_id: int) -> FriendRequestResponse:
        if FriendGateway.cancel_friend_request(user_id, friend_id):
            return FriendRequestResponse(success=True, message="Friend request canceled")
        return FriendRequestResponse(success=False, message="Friend request not found or already canceled")
    
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
                created_at=str(post.created_at)  # ✅ แปลงเป็น `str`
            )
        return None

    @strawberry.mutation
    def delete_post(self, user_id: int, post_id: int) -> bool:
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
    

