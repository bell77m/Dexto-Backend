
from typing import List
from typing import Optional
import strawberry
from sqlalchemy.orm import Session

from app.database import SessionLocal
from graphql_app.models import User
from graphql_app.types import UserType
from graphql_app.auth import hash_password, verify_password, create_access_token

# Query Resolvers
@strawberry.type
class Query:
    @strawberry.field
    async def users(self) -> List[UserType]:
        db:Session = SessionLocal()
        users = db.query(User).all()
        db.close()
        return [UserType(id=user.id, email=user.email) for user in users]

    @strawberry.field
    async def get_user(self, id:int)->UserType:
        db:Session = SessionLocal()
        user = db.query(User).filter(User.id == id).first()
        if user is None:
            return None
        db.close()
        return UserType(id=user.id, email=user.email)



@strawberry.type
class Mutation:
    @strawberry.mutation
    async def register_user(self, email: str, username: str, password: str) -> UserType:
        db: Session = SessionLocal()

        hashed_password = hash_password(password)

        new_user = User(email=email, username=username, password_hash=hashed_password)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        db.close()
        return UserType(id=new_user.id, email=new_user.email)

    @strawberry.mutation
    async def login_user(self, email: str, password: str) -> Optional[str]:
        db: Session = SessionLocal()
        user = db.query(User).filter(User.email == email).first()
        db.close()

        if user and verify_password(password, user.password_hash):
            return create_access_token({"sub": user.email})
        return None

    @strawberry.mutation
    async def update_email(self, id: int, new_email: str) -> UserType:
        db: Session = SessionLocal()
        user = db.query(User).filter(User.id == id).first()
        if user:
            user.email = new_email
            db.commit()
            db.refresh(user)
        db.close()
        return UserType(id=user.id, email=user.email)