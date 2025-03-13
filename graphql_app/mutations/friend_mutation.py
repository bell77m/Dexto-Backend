import strawberry
from typing import Optional
from graphql_app.database import SessionLocal
from user_gateway import UserGateway
from friend_gateway import FriendGateway
from chat_gateway import ChatGateway
from forum_gateway import ForumGateway
from graphql_app.Types import UserType, LoginResponse, FriendType, FriendRequestResponse
from graphql_app.Types import ChatMessageType, FriendChatSummary
from graphql_app.Types import ForumPostType, ForumCommentType


@strawberry.type
class FriendMutation:
    @strawberry.mutation
    def send_friend_request(self, user_id: int, friend_id: int) -> FriendRequestResponse:
        try:
            FriendGateway.send_friend_request(user_id, friend_id)
            return FriendRequestResponse(success=True, message="Friend request sent successfully")
        except ValueError as e:
            return FriendRequestResponse(success=False, message=str(e))

    @strawberry.mutation
    def accept_friend_request(self, user_id: int, friend_id: int) -> FriendRequestResponse:
        if FriendGateway.accept_friend_request(user_id, friend_id):
            return FriendRequestResponse(success=True, message="Friend request accepted")
        return FriendRequestResponse(success=False, message="Friend request not found or already accepted")

    @strawberry.mutation
    def reject_friend_request(self, user_id: int, friend_id: int) -> FriendRequestResponse:
        if FriendGateway.reject_friend_request(user_id, friend_id):
            return FriendRequestResponse(success=True, message="Friend request rejected")
        return FriendRequestResponse(success=False, message="Friend request not found or already rejected")

    @strawberry.mutation
    def cancel_friend_request(self, user_id: int, friend_id: int) -> FriendRequestResponse:
        if FriendGateway.cancel_friend_request(user_id, friend_id):
            return FriendRequestResponse(success=True, message="Friend request canceled")
        return FriendRequestResponse(success=False, message="Friend request not found or already canceled")