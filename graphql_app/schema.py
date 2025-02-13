"""
fast api + strawberry + uvicorn
"""
import strawberry
from .resolver import Query
schema = strawberry.Schema(query=Query)