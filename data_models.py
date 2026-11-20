from datetime import date
from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, Mapped
from db import Base, engine


class Authors(Base):
    __tablename__ = 'authors'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    birth_date: Mapped[date | None] = mapped_column(nullable=True)
    date_of_death: Mapped[date | None] = mapped_column(nullable=True)

    def __repr__(self):
        return f"Autorenname: {self.name} Geburtstag: {self.birth_date} - falls verstorben, dann am: {self.date_of_death}"


class Books(Base):
    __tablename__ = 'books'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str]
    isbn: Mapped[str | None] = mapped_column(unique=True, nullable=True)
    publication_year: Mapped[int | None] = mapped_column(nullable=True)
    author_id: Mapped[int | None] = mapped_column(
        ForeignKey('authors.id', ondelete="CASCADE"),
        nullable=True
    )

    @property
    def cover_url(self) -> str | None:
        if self.isbn:
            clean_isbn = self.isbn.replace("-", "").strip()
            return f"https://covers.openlibrary.org/b/isbn/{clean_isbn}-M.jpg"
        return None

    def __repr__(self):
        return f"Buchtitel: {self.title} Veröffentlichungsjahr: {self.publication_year}"


#Base.metadata.create_all(engine)
