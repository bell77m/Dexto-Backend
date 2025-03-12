from graphql_app.database import SessionLocal
from graphql_app.model import ForumPost, ForumComment, ForumLike
from sqlalchemy.orm import joinedload

class ForumGateway:
    @staticmethod
    def create_post(user_id: int, title: str, content: str, tags: str, image_data=None, image_url=None):
        """ เพิ่มโพสต์ใหม่ """
        with SessionLocal() as db:
            new_post = ForumPost(user_id=user_id, title=title, content=content, tags=tags, image_data=image_data, image_url=image_url)
            db.add(new_post)
            db.commit()
            db.refresh(new_post)
            return new_post

    @staticmethod
    def get_comments(post_id: int):
        """ ดึงคอมเมนต์ของโพสต์ พร้อมแสดงโปรไฟล์ผู้ใช้ """
        with SessionLocal() as db:
            comments = db.query(ForumComment).options(
                joinedload(ForumComment.user)  # ✅ โหลดข้อมูลผู้ใช้
            ).filter(ForumComment.post_id == post_id).all()
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
        """ ค้นหาโพสต์จากหัวข้อหรือแท็ก """
        with SessionLocal() as db:
            posts = db.query(ForumPost).filter(
                (ForumPost.title.ilike(f"%{query}%")) | (ForumPost.tags.ilike(f"%{query}%"))
            ).all()
            return posts

    @staticmethod
    def like_post(user_id: int, post_id: int):
        """ ไลค์โพสต์ (1 คนไลค์ได้แค่ 1 ครั้ง และเจ้าของโพสไลค์โพสตัวเองไม่ได้) """
        with SessionLocal() as db:
            post = db.query(ForumPost).filter(ForumPost.id == post_id).first()
            if not post or post.user_id == user_id:
                return False

            existing_like = db.query(ForumLike).filter(ForumLike.user_id == user_id, ForumLike.post_id == post_id).first()
            if not existing_like:
                db.add(ForumLike(user_id=user_id, post_id=post_id))
                post.likes += 1
                db.commit()
                return True
        return False

    @staticmethod
    def add_comment(user_id: int, post_id: int, content: str, parent_comment_id=None):
        """ เพิ่มคอมเมนต์หรือคอมเมนต์ตอบกลับ """
        with SessionLocal() as db:
            new_comment = ForumComment(user_id=user_id, post_id=post_id, content=content, parent_comment_id=parent_comment_id)
            db.add(new_comment)
            db.commit()
            db.refresh(new_comment)
            return new_comment
