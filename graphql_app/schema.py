"""
fast api + strawberry + uvicorn
"""
import strawberry
from .resolver import Query, Mutation
schema = strawberry.Schema(query=Query)