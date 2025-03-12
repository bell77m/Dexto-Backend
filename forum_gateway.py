from graphql_app.database import SessionLocal
from graphql_app.model import ForumPost, ForumComment, ForumLike
from sqlalchemy.orm import joinedload
from sqlalchemy.sql import func  
from typing import Optional, List


class ForumGateway:
    
    @staticmethod
    def create_post(user_id: int, title: str, content: str, tags: str, image_url: Optional[str] = None):
        """ เพิ่มโพสต์ใหม่ พร้อมรองรับรูปภาพ """
        with SessionLocal() as db:
            new_post = ForumPost(
                user_id=user_id,
                title=title,
                content=content,
                tags=tags,
                image_url=image_url,  # ✅ รองรับ `image_url`
                created_at=func.now()
            )
            db.add(new_post)
            db.commit()
            db.refresh(new_post)
            
            post_with_user = db.query(ForumPost).options(joinedload(ForumPost.user)).filter(ForumPost.id == new_post.id).first()
            return post_with_user

    @staticmethod
    def get_comments(post_id: int):
        """ ดึงคอมเมนต์ของโพสต์ พร้อมข้อมูลผู้ใช้ """
        with SessionLocal() as db:
            comments = db.query(ForumComment).options(joinedload(ForumComment.user)).filter(ForumComment.post_id == post_id).all()
            return comments

    @staticmethod
    def delete_post(user_id: int, post_id: int):
        """ ลบโพสต์ (เฉพาะเจ้าของโพสต์เท่านั้น) """
        with SessionLocal() as db:
            post = db.query(ForumPost).filter(ForumPost.id == post_id, ForumPost.user_id == user_id).first()
            if post:
                db.delete(post)
                db.commit()
                return True
        return False

    @staticmethod
    def search_posts(query: str):
        """ ค้นหาโพสต์จากชื่อหรือแท็ก """
        with SessionLocal() as db:
            posts = db.query(ForumPost).options(joinedload(ForumPost.user)).filter(
                (ForumPost.title.ilike(f"%{query}%")) | (ForumPost.tags.ilike(f"%{query}%"))
            ).all()
            return posts

    @staticmethod
    def like_post(user_id: int, post_id: int):
        """ กดไลค์โพสต์ (1 คนไลค์ได้แค่ 1 ครั้ง และเจ้าของโพสต์ไลค์โพสตัวเองไม่ได้) """
        with SessionLocal() as db:
            post = db.query(ForumPost).filter(ForumPost.id == post_id).first()
            if not post or post.user_id == user_id:
                return False  # ✅ ห้ามเจ้าของโพสต์ไลค์โพสต์ตัวเอง

            existing_like = db.query(ForumLike).filter(
                ForumLike.user_id == user_id, ForumLike.post_id == post_id
            ).first()
            if existing_like:
                return False  # ✅ ป้องกันการไลค์ซ้ำ

            db.add(ForumLike(user_id=user_id, post_id=post_id))
            post.likes += 1  # ✅ อัปเดตจำนวนไลค์ใน `forum_posts`
            db.commit()
            return True

    @staticmethod
    def add_comment(user_id: int, post_id: int, content: str, parent_comment_id: Optional[int] = None):
        """ เพิ่มคอมเมนต์หรือคอมเมนต์ตอบกลับ """
        with SessionLocal() as db:
            new_comment = ForumComment(
                user_id=user_id,
                post_id=post_id,
                parent_comment_id=parent_comment_id,
                content=content,
                created_at=func.now()
            )
            db.add(new_comment)
            db.commit()
            db.refresh(new_comment)
            
            comment_with_user = db.query(ForumComment).options(joinedload(ForumComment.user)).filter(ForumComment.id == new_comment.id).first()
            return comment_with_user
        
    @staticmethod
    def get_post_by_id(post_id: int):
        """ ดึงโพสต์ตาม ID พร้อมข้อมูลผู้ใช้ """
        with SessionLocal() as db:
            post = db.query(ForumPost).options(joinedload(ForumPost.user)).filter(ForumPost.id == post_id).first()
            return post
