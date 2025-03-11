from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config.config import Config

conf = Config("config/config.ini")
db_config = conf.load_db_config()

DATABASE_URL = f"mysql+mysqlconnector://{db_config['user']}:{db_config['password']}@{db_config['host']}/{db_config['database']}"

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False)
Base = declarative_base()

print("✅ Database Connected Successfully!")
