import strawberry
from typing import Optional
from .user_gateway import UserGateway
from .Types import UserType, UsersType, LoginResponse

@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "Hello World"

    @strawberry.field
    def users(self) -> UsersType:
        return UsersType(users=UserGateway.get_users())

    @strawberry.field
    def user(self, id: int) -> Optional[UserType]:
        return UserGateway.get_user_by_id(id)

@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_user(self, display_name: str, email: str, password: str) -> Optional[UserType]:
        return UserGateway.add_user(display_name, email, password)
    
    @strawberry.mutation
    def update_user(self, id: int, display_name: Optional[str] = None, email: Optional[str] = None,
                    password: Optional[str] = None) -> Optional[UserType]:
        return UserGateway.update_user(id, display_name, email, password)
    
    @strawberry.mutation
    def delete_user(self, id: int) -> bool:
        return UserGateway.delete_user(id)
    
    @strawberry.mutation
    def login_user(self, email: str, password: str) -> LoginResponse:
        try:
            user = UserGateway.login_user(email, password)
            if user:
                return LoginResponse(success=True, message="Login successful!", user=user)
            else:
                return LoginResponse(success=False, message="Invalid email or password", user=None)
        except ValueError as e:
            return LoginResponse(success=False, message=str(e), user=None)
