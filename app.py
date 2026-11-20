from datetime import date
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from flask import Flask, render_template, request
from pathlib import Path
from data_models import Authors, Books
from db import Session

app = Flask(__name__)

basedir = Path(__file__).resolve().parent
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{basedir / 'data' / 'library.sqlite'}"

def get_post_book(this_request):
    """Extract (title, isbn, publication_year, author_id) from book form data."""
    publication_year = this_request.form.get("publication_year")
    author_id = this_request.form.get("author_id")

    return (
        this_request.form.get("title") or "",
        this_request.form.get("isbn") or None,
        int(publication_year) if publication_year else None,
        int(author_id) if author_id else None
    )

def normalize_isbn(raw_isbn: Optional[str]) -> Optional[str]:
    if not raw_isbn:
        return None
    cleaned = raw_isbn.strip()
    return cleaned or None

@app.route('/add_author', methods=['GET', 'POST'])
def add_author():
    message = ''
    if request.method == 'POST':
        name = (request.form.get("name") or "").strip()
        birth_date = date.fromisoformat(d) if (d := request.form.get("birth_date")) else None
        date_of_death = date.fromisoformat(d) if (d := request.form.get("date_of_death")) else None

        if not name:
            message = "Bitte einen Namen für den Autor angeben."
        else:
            with Session() as session:
                existing = session.scalar(select(Authors).where(Authors.name == name))
                if existing:
                    message = f"Der Autor '{name}' existiert bereits."
                else:
                    author = Authors(
                        name=name,
                        birth_date=birth_date,
                        date_of_death=date_of_death
                    )
                    session.add(author)
                    try:
                        session.commit()
                        message = f"Autor: {name} wurde erfolgreich angelegt."
                    except IntegrityError:
                        session.rollback()
                        message = f"Der Autor '{name}' existiert bereits."

    return render_template('add_author.html', message=message)

@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    message = ''

    if request.method == 'POST':
        title, raw_isbn, publication_year, author_id = get_post_book(request)
        isbn = normalize_isbn(raw_isbn)

        with Session() as session:
            existing_book = None
            if isbn:
                existing_book = session.scalar(select(Books).where(Books.isbn == isbn))

            if existing_book:
                message = f"Fehler: Ein Buch mit der ISBN '{isbn}' existiert bereits im Katalog ('{existing_book.title}')."
            else:
                book = Books(
                    title=title,
                    isbn=isbn,
                    publication_year=publication_year,
                    author_id=author_id
                )
                session.add(book)
                try:
                    session.commit()
                    message = f"Das Buch: {title} wurde erfolgreich in die Bibliothek aufgenommen."
                except IntegrityError:
                    session.rollback()
                    message = f"Fehler: Ein Buch mit der ISBN '{isbn}' existiert bereits im Katalog."

    with Session() as session:
        authors = session.scalars(select(Authors)).all()

    return render_template('add_book.html', authors=authors, message=message)

@app.route('/list_authors')
def list_authors():
    with Session()  as session:
        authors = session.scalars(select(Authors)).all()
    return render_template('list_authors.html', authors=authors)

@app.route('/')
@app.route('/list_books')
def list_books():
    with Session()  as session:
        stmt = select(Books, Authors).outerjoin(Authors, Books.author_id == Authors.id)
        books = session.execute(stmt).all()

    return render_template('list_books.html', books=books)

@app.route('/edit_book/<int:book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    message = ''
    if request.method == 'POST':
        with Session.begin () as session:

            title, isbn, publication_year, author_id = get_post_book(request)

            stmt = select(Books).where(Books.id == book_id)
            book_to_update = session.execute(stmt).scalar_one()
            book_to_update.title = title
            book_to_update.isbn = isbn
            book_to_update.publication_year = publication_year
            book_to_update.author_id = author_id

        message = f"Das Buch mit dem Titel: {title} wurde erfolgreich aktualisiert."

    with Session()  as session:
        book = session.get(Books, book_id)
        authors = session.scalars(select(Authors)).all()

    return render_template('edit_book.html', book=book, authors=authors, message=message)

@app.route('/edit_author/<int:author_id>', methods=['GET', 'POST'])
def edit_author(author_id):
    message = ''
    with Session() as session:
        author = session.get(Authors, author_id)
        if not author:
            return "Autor nicht gefunden", 404

        if request.method == 'POST':
            name = (request.form.get("name") or "").strip()
            birth_date = date.fromisoformat(d) if (d := request.form.get("birth_date")) else None
            date_of_death = date.fromisoformat(d) if (d := request.form.get("date_of_death")) else None

            if not name:
                message = "Bitte einen Namen für den Autor angeben."
            else:
                duplicate = session.scalar(
                    select(Authors).where(Authors.name == name, Authors.id != author_id)
                )
                if duplicate:
                    message = f"Ein anderer Autor mit dem Namen '{name}' existiert bereits."
                else:
                    author.name = name
                    author.birth_date = birth_date
                    author.date_of_death = date_of_death
                    try:
                        session.commit()
                        message = f"Der Autor '{name}' wurde erfolgreich aktualisiert."
                    except IntegrityError:
                        session.rollback()
                        message = f"Ein anderer Autor mit dem Namen '{name}' existiert bereits."

    return render_template('edit_author.html', author=author, message=message)

@app.route('/search_book', methods=['POST'])
def search_book():
    message = ''
    query_param = request.form.get("query_param") or ""
    with Session().begin () as session:
        stmt = select(Books, Authors).outerjoin(
            Authors,
            Books.author_id == Authors.id
        ).where(
            Books.title.like(f"%{query_param}%")
        )
        books = session.execute(stmt).all()
        if not books:
            message = f"Zu ihrer Suche '{query_param}' konnte kein Buch gefunden werden."

    return render_template('list_books.html', books=books, query_param=query_param, message=message)

@app.route('/book/<int:book_id>')
def view_book(book_id):

    with Session()  as session:
        book = session.get(Books, book_id)
        author = session.get(Authors, book.author_id) if book.author_id else None

    return render_template('view_book.html', book=book, author=author)

@app.route('/delete/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    message = ''
    with Session()  as session:

        book = session.get(Books, book_id)
        if book:
            session.delete(book)
            session.commit()

        stmt = select(Books, Authors).outerjoin(Authors, Books.author_id == Authors.id)
        books = session.execute(stmt).all()
        message = f"Das Buch ist aus dem Katalog entfernt worden."

    return render_template('list_books.html', books=books, message=message)

@app.route('/delete_author/<int:author_id>', methods=['POST'])
def delete_author(author_id):
    message = ''
    with Session.begin() as session:
        result = session.execute(delete(Authors).where(Authors.id == author_id))
        if result.rowcount:
            message = "Der Autor und seine zugehörigen Bücher wurden aus dem Katalog entfernt."
        else:
            message = "Der Autor wurde nicht gefunden."

    with Session() as session:
        authors = session.scalars(select(Authors)).all()

    return render_template('list_authors.html', authors=authors, message=message)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
