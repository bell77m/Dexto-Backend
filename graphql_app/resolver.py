from typing import List

import strawberry
from sqlalchemy.orm import Session

from app.database import SessionLocal
from graphql_app.models import User
from graphql_app.types import UserType


# Query Resolvers
@strawberry.type
class Query:
    @strawberry.field
    def users(self) -> List[UserType]:
        db:Session = SessionLocal()
        users = db.query(User).all()
        db.close()
        return [UserType(id=user.id, email=user.email) for user in users]



# Mutation Resolvers
# @strawberry.type
# class Mutation:
    # @strawberry.mutation
    # def create_user(self, name: str, email: str, db: Session = Depends(get_db)) -> UserType:
    #     new_user = User(name=name, email=email)
    #     db.add(new_user)
    #     db.commit()
    #     db.refresh(new_user)
    #     return new_user
    #
    # @strawberry.mutation
    # def delete_user(self, id: int, db: Session = Depends(get_db)) -> str:
    #     user = db.query(User).filter(User.id == id).first()
    #     if user:
    #         db.delete(user)
    #         db.commit()
    #         return "User deleted"
    #     return "User not found"
