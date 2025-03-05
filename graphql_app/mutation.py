import strawberry
from typing import Optional
from user_gateway import UserGateway
from .types import UserType, LoginResponse

@strawberry.type
class Mutation:
    @strawberry.mutation
    def add_user(self, display_name: str, email: str, password: str) -> Optional[UserType]:
        user = UserGateway.add_user(display_name, email, password)
        if user:
            return UserType(id=user.id, display_name=user.display_name, email=user.email)
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
        try:
            user = UserGateway.login_user(email, password)
            if user:
                return LoginResponse(success=True, message="Login successful", user=UserType(id=user.id, display_name=user.display_name, email=user.email))
            return LoginResponse(success=False, message="Invalid email or password", user=None)
        except ValueError as e:
            return LoginResponse(success=False, message=str(e), user=None)
