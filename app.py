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

# 
class AuthorModel(db.Model):
    __tablename__ = 'authors'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[int] = mapped_column(String(32), index= True, unique=True)
    quotes: Mapped[list['QuoteModel']] = relationship( back_populates='author', lazy='dynamic')

    def __init__(self, name):
      self.name = name

    def to_dict(self):
        return {
            'id' : self.id,
            "name": self.name
        }   
    
# 
class QuoteModel(db.Model):
    __tablename__ = 'quotes'

    id: Mapped[int] = mapped_column(primary_key=True)
    author_id: Mapped[str] = mapped_column(ForeignKey('authors.id'))
    author: Mapped['AuthorModel'] = relationship(back_populates='quotes')
    text: Mapped[str] = mapped_column(String(255))

    def __init__(self, author, text):
        self.author = author
        self.text  = text


    def to_dict(self):
        return {
            "id": self.id,
            "text": self.text,
        }    

@app.errorhandler(HTTPException)
def handle_exeption(e):
    return jsonify({"message": e.description}), e.code

# URL: /authors/1/quotes
@app.route("/authors/<int:author_id>/quotes")
def get_author_quotes(author_id): 
    author = db.session.get(AuthorModel, author_id)
    quotes = []
    for quote in author.quotes:
        quotes.append(quote.to_dict())

    return jsonify(author=author.to_dict(), quotes=quotes), 200

# URL: quotes/<int:quote_id>
@app.route("/quotes/<int:quote_id>")
def get_quote(quote_id):
    quote = db.session.get(QuoteModel, quote_id)
    if quote:
        return jsonify(quote.to_dict()), 200
    return {"error": "Quote not found"}, 404

# URL: quotes/count
@app.route("/quotes/count")
def get_quotes_count():
    count = db.session.query(QuoteModel).count()
    return jsonify(count), 200 # count=count чтобы получить пару ключ:значение

# URL: quotes POST
@app.route("/quotes", methods=['POST'])
def create_quote():
    data = request.json
    if not data or 'author' not in data or 'text' not in data:
        return {"error": "Missing required fields (author and text)"}, 400
    
    quote = QuoteModel(author=data['author'], text=data['text'], rating=data['rating'])
    db.session.add(quote)
    db.session.commit()
    
    return jsonify(quote.to_dict()), 201

# URL: quotes PUT
@app.route("/quotes/<int:quote_id>", methods=['PUT'])
def edit_quote(quote_id):
    quote = db.session.get(QuoteModel, quote_id)
    if not quote:
        abort(404, "Quote not found")
    
    data = request.json
    if 'author' in data:
        quote.author = data['author']
    if 'text' in data:
        quote.text = data['text']
    if 'rating' in data:
        quote.rating = data['rating']    
    
    db.session.commit()
    return jsonify(quote.to_dict())

# URL: quotes DELETE
@app.route("/quotes/<int:quote_id>", methods=['DELETE'])
def delete_quote(quote_id: int):
    quote = db.session.get(QuoteModel, quote_id)
    if not quote:
        abort(404, f"Quote with id {quote_id} not found")
    
    db.session.delete(quote)
    db.session.commit()
    return jsonify({"message": f"Quote with id {quote_id} has been deleted."}), 200

# URL: quotes/filter
@app.route("/quotes/filter", methods=['GET'])
def search():
    author = request.args.get('author', '').strip() # получаем то что после ? в адресной строке + убираем пробелы

    quotes = QuoteModel.query.filter(QuoteModel.author.ilike(author)).all()
    
    if not quotes:
        return {'error': f"Quotes with such {author} were not found"}, 404
    
    return jsonify([quote.to_dict() for quote in quotes])
        
if __name__ == "__main__":
    app.run(debug=True)