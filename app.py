from flask import Flask, request, jsonify, abort
from pathlib import Path
from werkzeug.exceptions import HTTPException
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, select, Integer, ForeignKey
from flask_migrate import Migrate

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
    quotes: Mapped[list['QuoteModel']] = relationship(back_populates='author', lazy='dynamic', cascade='all, delete-orphan')

    def __init__(self, name):
        self.name = name

    def to_dict(self):
        return {
            'id' : self.id,
            "name": self.name
        }

class QuoteModel(db.Model):
    __tablename__ = 'quotes'
    id: Mapped[int] = mapped_column(primary_key=True)
    author_id: Mapped[int] = mapped_column(ForeignKey('authors.id'))
    author: Mapped['AuthorModel'] = relationship(back_populates='quotes')
    text: Mapped[str] = mapped_column(String(255))

    def __init__(self, author, text):
        self.author = author
        self.text = text

    def to_dict(self):
        return {
            "id": self.id,
            "author_id": self.author_id,
            "text": self.text,
            "author_name": self.author.name if self.author else None
        }

@app.errorhandler(HTTPException)
def handle_exception(e):
    return jsonify({"message": e.description}), e.code

# Authors CRUD
@app.route("/authors", methods=['GET'])
def get_authors():
    authors = AuthorModel.query.all()
    return jsonify([author.to_dict() for author in authors]), 200

@app.route("/authors/<int:author_id>", methods=['GET'])
def get_author(author_id):
    author = db.session.get(AuthorModel, author_id)
    if not author:
        abort(404, "Author not found")
    return jsonify(author.to_dict()), 200

@app.route("/authors", methods=['POST'])
def create_author():
    data = request.json
    if not data or 'name' not in data:
        return {"error": "Missing required field 'name'"}, 400
    
    author = AuthorModel(name=data['name'])
    db.session.add(author)
    db.session.commit()
    return jsonify(author.to_dict()), 201

@app.route("/authors/<int:author_id>", methods=['PUT'])
def update_author(author_id):
    author = db.session.get(AuthorModel, author_id)
    if not author:
        abort(404, "Author not found")
    
    data = request.json
    if 'name' in data:
        author.name = data['name']
    
    db.session.commit()
    return jsonify(author.to_dict()), 200

@app.route("/authors/<int:author_id>", methods=['DELETE'])
def delete_author(author_id):
    author = db.session.get(AuthorModel, author_id)
    if not author:
        abort(404, f"Author with id {author_id} not found")
    
    db.session.delete(author)
    db.session.commit()
    return jsonify({"message": f"Author with id {author_id} has been deleted."}), 200

# Quotes CRUD
@app.route("/quotes", methods=['GET'])
def get_quotes():
    quotes = QuoteModel.query.all()
    return jsonify([quote.to_dict() for quote in quotes]), 200

@app.route("/quotes/<int:quote_id>", methods=['GET'])
def get_quote(quote_id):
    quote = db.session.get(QuoteModel, quote_id)
    if not quote:
        abort(404, "Quote not found")
    return jsonify(quote.to_dict()), 200

@app.route("/authors/<int:author_id>/quotes", methods=['POST'])
def create_author_quote(author_id):
    author = db.session.get(AuthorModel, author_id)
    if not author:
        abort(404, "Author not found")
    
    data = request.json
    if not data or 'text' not in data:
        return {"error": "Missing required field 'text'"}, 400
    
    quote = QuoteModel(author=author, text=data['text'])
    db.session.add(quote)
    db.session.commit()
    
    return jsonify({
        "quote": quote.to_dict(),
        "message": f"Quote successfully created for author {author.name}"
    }), 201

@app.route("/quotes/<int:quote_id>", methods=['PUT'])
def update_quote(quote_id):
    quote = db.session.get(QuoteModel, quote_id)
    if not quote:
        abort(404, "Quote not found")
    
    data = request.json
    if 'text' in data:
        quote.text = data['text']
    if 'author_id' in data:
        author = db.session.get(AuthorModel, data['author_id'])
        if not author:
            return {"error": "Author not found"}, 404
        quote.author = author
    
    db.session.commit()
    return jsonify(quote.to_dict()), 200

@app.route("/quotes/<int:quote_id>", methods=['DELETE'])
def delete_quote(quote_id):
    quote = db.session.get(QuoteModel, quote_id)
    if not quote:
        abort(404, f"Quote with id {quote_id} not found")
    
    db.session.delete(quote)
    db.session.commit()
    return jsonify({"message": f"Quote with id {quote_id} has been deleted."}), 200

# Author's quotes
@app.route("/authors/<int:author_id>/quotes")
def get_author_quotes(author_id):
    author = db.session.get(AuthorModel, author_id)
    if not author:
        abort(404, "Author not found")
        
    quotes = [quote.to_dict() for quote in author.quotes]
    return jsonify(author=author.to_dict(), quotes=quotes), 200

if __name__ == "__main__":
    app.run(debug=True)