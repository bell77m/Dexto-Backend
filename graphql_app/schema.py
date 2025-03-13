import strawberry
from .mutations.user_mutation import UserMutation
from .mutations.friend_mutation import FriendMutation
from .mutations.chat_mutation import ChatMutation
from .mutations.forum_mutation import ForumMutation
from .queries.user_query import UserQuery
from .queries.friend_query import FriendQuery
from .queries.chat_query import ChatQuery
from .queries.forum_query import ForumQuery



@strawberry.type
class Mutation(
    UserMutation,
    FriendMutation,
    ChatMutation,
    ForumMutation
):
    pass

@strawberry.type
class Query(
    UserQuery,
    FriendQuery,
    ChatQuery,
    ForumQuery
):
    pass

schema = strawberry.Schema(query=Query, mutation=Mutation)