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
class UserMutation:
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