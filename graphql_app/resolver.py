import typing
import strawberry

@strawberry.type
class Query():
    @strawberry.field
    def hello(self) -> str:
        return "Hello World"

# @strawberry.type
# class Mutation():
#     pass