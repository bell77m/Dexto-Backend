import strawberry
from typing import List, Optional

@strawberry.type
class UserType:
    id: int
    display_name: str
    email: str
    profile_picture_url: str

@strawberry.type
class LoginResponse:
    success: bool
    message: str
    user: Optional[UserType]
