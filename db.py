from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

engine = create_engine('sqlite:///data/library.sqlite')

Session = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass