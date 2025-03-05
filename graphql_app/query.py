import strawberry
from typing import List, Optional
from user_gateway import UserGateway
from .types import UserType

@strawberry.type
class Query:
    @strawberry.field
    def get_users(self) -> List[UserType]:
        users = UserGateway.get_users()
        return [UserType(id=user.id, display_name=user.display_name, email=user.email) for user in users]

    @strawberry.field
    def get_user_by_id(self, id: int) -> Optional[UserType]:
        user = UserGateway.get_user_by_id(id)
        if user:
            return UserType(id=user.id, display_name=user.display_name, email=user.email)
        return None
