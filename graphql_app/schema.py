"""
fast api + strawberry + uvicorn
"""
import strawberry
from .resolver import Query, Mutation  # นำเข้า Query และ Mutation

# สร้าง schema โดยกำหนดทั้ง query และ mutation
schema = strawberry.Schema(query=Query, mutation=Mutation)