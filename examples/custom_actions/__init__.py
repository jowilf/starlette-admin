from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base

from .config import ENGINE_URI

engine = create_engine(ENGINE_URI, connect_args={"check_same_thread": False}, echo=True)
Base = declarative_base()
