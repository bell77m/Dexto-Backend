import strawberry
from typing import List

@strawberry.type
class UserType:
    id: int
    display_name: str
    email: str

@strawberry.type
class UsersType:
    users: List[UserType]  # Use `List[UserType]` for Python <3.9
