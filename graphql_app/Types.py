import strawberry
from typing import Optional, List

@strawberry.type
class UserType:
    id: int
    display_name: str
    email: str

@strawberry.type
class UsersType:
    users: List[UserType]

@strawberry.type
class LoginResponse:
    success: bool
    message: str
    user: Optional[UserType]