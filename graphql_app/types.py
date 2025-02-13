import strawberry

@strawberry.type
class UserType:
    id: int
    name: str
    email: str
