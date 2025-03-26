from flask import Flask, request, jsonify, abort
from pathlib import Path
from werkzeug.exceptions import HTTPException
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, select, Integer, ForeignKey, DateTime
from sqlalchemy.sql import func
from flask_migrate import Migrate
import datetime

class Base(DeclarativeBase):
    pass

BASE_DIR = Path(__file__).parent

app = Flask(__name__)
app.json.ensure_ascii = False
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{BASE_DIR / 'quotes.db'}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(model_class=Base)
db.init_app(app)
migrate = Migrate(app, db)

class AuthorModel(db.Model):
    __tablename__ = 'authors'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(32), index=True, unique=True)
    surname: Mapped[str] = mapped_column(String(32), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(default=False, server_default='0')
    quotes: Mapped[list['QuoteModel']] = relationship(back_populates='author', lazy='dynamic', cascade='all, delete-orphan')

    def __init__(self, name, surname=None):
        self.name = name
        self.surname = surname

    def to_dict(self):
        return {
            'id': self.id,
            "name": self.name,
            "surname": self.surname,
            "is_deleted": self.is_deleted
        }

class QuoteModel(db.Model):
    __tablename__ = 'quotes'
    id: Mapped[int] = mapped_column(primary_key=True)
    author_id: Mapped[int] = mapped_column(ForeignKey('authors.id'))
    author: Mapped['AuthorModel'] = relationship(back_populates='quotes')
    text: Mapped[str] = mapped_column(String(255))
    rating: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default='1')
    created: Mapped[datetime.datetime] = mapped_column(DateTime(), server_default=func.now())

    def __init__(self, author, text, rating=1):
        self.author = author
        self.text = text
        self.rating = max(1, min(5, rating))  # гарантия что будет между 1-5

    def to_dict(self):
        return {
            "id": self.id,
            "author_id": self.author_id,
            "text": self.text,
            "author_name": self.author.name,
            "rating": self.rating,
            "created": self.created.strftime("%d.%m.%Y")
        }

@app.errorhandler(HTTPException)
def handle_exception(e):
    return jsonify({"message": e.description}), e.code

# Authors CRUD
@app.route("/authors", methods=['GET'])
def get_authors():
    # добавляем аргументы для сортировки (?sort_by=)
    sort_by = request.args.get('sort_by', 'name')
    sort_order = request.args.get('sort_order', 'asc')
    
    query = AuthorModel.query.filter_by(is_deleted=False)
    # условия сортировки, для фамилии наллы в конец
    if sort_by == 'name':
        if sort_order == 'desc':
            query = query.order_by(AuthorModel.name.desc())
        else:
            query = query.order_by(AuthorModel.name.asc())
    elif sort_by == 'surname':
        if sort_order == 'desc':
            query = query.order_by(AuthorModel.surname.desc().nulls_last())
        else:
            query = query.order_by(AuthorModel.surname.asc().nulls_last())
    
    authors = query.all()
    return jsonify([author.to_dict() for author in authors]), 200

@app.route("/authors/<int:author_id>", methods=['GET'])
def get_author(author_id):
    author = db.session.get(AuthorModel, author_id)
    if not author or author.is_deleted:
        abort(404, "Author not found")
    return jsonify(author.to_dict()), 200

@app.route("/authors", methods=['POST'])
def create_author():
    data = request.json
    if not data or 'name' not in data:
        return {"error": "Missing required field 'name'"}, 400
    
    author = AuthorModel(
        name=data['name'],
        surname=data.get('surname') # для необязательных полей метод get
        )
    db.session.add(author)
    db.session.commit()
    return jsonify(author.to_dict()), 201

@app.route("/authors/<int:author_id>", methods=['PUT'])
def update_author(author_id):
    author = db.session.get(AuthorModel, author_id)
    if not author or author.is_deleted:
        abort(404, "Author not found")
    
    data = request.json
    if 'name' in data:
        author.name = data['name']

    if 'surname' in data:
        author.surname = data['surname']
    
    db.session.commit()
    return jsonify(author.to_dict()), 200

@app.route("/authors/<int:author_id>", methods=['DELETE'])
def delete_author(author_id):
    author = db.session.get(AuthorModel, author_id)
    if not author or author.is_deleted:
        abort(404, f"Author with id {author_id} not found")
    
    author.is_deleted = True
    db.session.commit()
    return jsonify({"message": f"Author with id {author_id} has been marked as deleted."}), 200

@app.route("/authors/deleted", methods=['GET'])
def get_deleted_authors():
    authors = AuthorModel.query.filter_by(is_deleted=True).all()
    return jsonify([author.to_dict() for author in authors]), 200

@app.route("/authors/<int:author_id>/restore", methods=['POST'])
def restore_author(author_id):
    author = db.session.get(AuthorModel, author_id)
    if not author or not author.is_deleted:
        abort(404, f"Author with id {author_id} not found in deleted authors")
    
    author.is_deleted = False
    db.session.commit()
    return jsonify({"message": f"Author with id {author_id} has been restored."}), 200

# Quotes CRUD
@app.route("/quotes", methods=['GET'])
def get_quotes():
    quotes = QuoteModel.query.join(AuthorModel).filter(AuthorModel.is_deleted == False).all()
    return jsonify([quote.to_dict() for quote in quotes]), 200

@app.route("/quotes/<int:quote_id>", methods=['GET'])
def get_quote(quote_id):
    quote = db.session.get(QuoteModel, quote_id)
    if not quote or quote.author.is_deleted:
        abort(404, "Quote not found")
    return jsonify(quote.to_dict()), 200

@app.route("/authors/<int:author_id>/quotes", methods=['POST'])
def create_author_quote(author_id):
    author = db.session.get(AuthorModel, author_id)
    if not author or author.is_deleted:
        abort(404, "Author not found")
    
    data = request.json
    if not data or 'text' not in data:
        return {"error": "Missing required field 'text'"}, 400
    
    rating = data.get('rating', 1) 
    quote = QuoteModel(author=author, text=data['text'], rating=rating)
    db.session.add(quote)
    db.session.commit()
    
    return jsonify({
        "quote": quote.to_dict(),
        "message": f"Quote successfully created for author {author.name}"
    }), 201

@app.route("/quotes/<int:quote_id>/increase_rating", methods=['PATCH'])
def increase_quote_rating(quote_id):
    quote = db.session.get(QuoteModel, quote_id)
    if not quote or quote.author.is_deleted:
        abort(404, "Quote not found")
    
    if quote.rating < 5:
        quote.rating += 1
        db.session.commit()
    
    return jsonify(quote.to_dict()), 200

@app.route("/quotes/<int:quote_id>/decrease_rating", methods=['PATCH'])
def decrease_quote_rating(quote_id):
    quote = db.session.get(QuoteModel, quote_id)
    if not quote or quote.author.is_deleted:
        abort(404, "Quote not found")
    
    if quote.rating > 1:
        quote.rating -= 1
        db.session.commit()
    
    return jsonify(quote.to_dict()), 200

@app.route("/quotes/<int:quote_id>", methods=['PUT'])
def update_quote(quote_id):
    quote = db.session.get(QuoteModel, quote_id)
    if not quote or quote.author.is_deleted:
        abort(404, "Quote not found")
    
    data = request.json
    if 'text' in data:
        quote.text = data['text']
    if 'author_id' in data:
        author = db.session.get(AuthorModel, data['author_id'])
        if not author or author.is_deleted:
            return {"error": "Author not found"}, 404
        quote.author = author
    if 'rating' in data:
        quote.rating = max(1, min(5, data['rating']))
    
    db.session.commit()
    return jsonify(quote.to_dict()), 200

@app.route("/quotes/<int:quote_id>", methods=['DELETE'])
def delete_quote(quote_id):
    quote = db.session.get(QuoteModel, quote_id)
    if not quote or quote.author.is_deleted:
        abort(404, f"Quote with id {quote_id} not found")
    
    db.session.delete(quote)
    db.session.commit()
    return jsonify({"message": f"Quote with id {quote_id} has been deleted."}), 200

# Author's quotes
@app.route("/authors/<int:author_id>/quotes")
def get_author_quotes(author_id):
    author = db.session.get(AuthorModel, author_id)
    if not author or author.is_deleted:
        abort(404, "Author not found")
        
    quotes = [quote.to_dict() for quote in author.quotes]
    return jsonify(author=author.to_dict(), quotes=quotes), 200

if __name__ == "__main__":
    app.run(debug=True)