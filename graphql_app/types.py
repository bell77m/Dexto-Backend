import strawberry

@strawberry.type
class UserType:
    id: int
    email: str
