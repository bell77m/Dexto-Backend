import strawberry
from typing import Optional
from user_gateway import UserGateway
from .types import UserType, LoginResponse

@strawberry.type
class Mutation:
    @strawberry.mutation
    def add_user(self, display_name: str, email: str, password: str, profile_picture_url: Optional[str] = None) -> Optional[UserType]:
        # ถ้าไม่ส่ง `profile_picture_url` ให้ใช้ค่า Default

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
    def update_user(self, id: int, display_name: Optional[str] = None, email: Optional[str] = None, password: Optional[str] = None) -> Optional[UserType]:
        user = UserGateway.update_user(id, display_name, email, password)
        if user:
            return UserType(id=user.id, display_name=user.display_name, email=user.email)
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
                profile_picture_url=user.profile_picture_url 
            )
        )

        except ValueError as e:
            # กรณีเกิดข้อผิดพลาดอื่นๆ
            return LoginResponse(success=False, message=str(e), user=None)
