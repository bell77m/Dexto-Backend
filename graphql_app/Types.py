import strawberry
from typing import List
from typing import Optional

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
    

