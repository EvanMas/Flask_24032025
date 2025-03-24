from flask import Flask, request
from random import choice
from pathlib import Path

BASE_DIR = Path(__file__).parent
path_to_db = BASE_DIR / "store.db"  # <- тут путь к БД# Используем так:
connection = sqlite3.connect(path_to_db)


app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

about_me = {
    "name" : "Ivan",
    "surname" : "Maslov",
    "email" : "mas15van@gmail.com"
}

quotes = [
    {
        "id": 3,
        "author": "Rick Cook",
        "text": """Программирование сегодня — это гонка
разработчиков программ, стремящихся писать программы с
большей и лучшей идиотоустойчивостью, и вселенной, которая
пытается создать больше отборных идиотов. Пока вселенная
побеждает."""
    },
    {
        "id": 5,
        "author": "Waldi Ravens",
        "text": """Программирование на С похоже на быстрые танцы
на только что отполированном полу людей с острыми бритвами в
руках."""
    },
    {
        "id": 6,
        "author": "Mosher’s Law of Software Engineering",
        "text": """Не волнуйтесь, если что-то не работает. Если
бы всё работало, вас бы уволили."""
    },
    {
        "id": 8,
        "author": "Yoggi Berra",
        "text": """В теории, теория и практика неразделимы. На
практике это не так."""
    },
    {
        "id": 10,
        "author": "IM",
        "text": """И это работает? удивительно"""
    },
]

def get_next_id():
    last_quote = quotes[-1]
    return last_quote['id'] + 1

@app.route("/")
def hello_world():
    return "Hello, World!"

@app.route("/about")
def about():
    return about_me
    
@app.route("/quotes")
def get_quotes():
    return quotes

@app.route("/quotes/<int:quote_id>")
def get_quote(quote_id):
    quote = next((q for q in quotes if q['id'] == quote_id), None)
    if quote:
        return quote
    return ({"error": "Quote not found"}), 404

@app.route("/quotes/count")
def get_quotes_count():
    return {"count" : len(quotes)}

@app.route("/quotes/random")
def random_quote():
    random_quote = choice(quotes)
    return random_quote


@app.route("/quotes", methods=['POST'])
def create_quote():
    data = request.json
    if not data or 'author' not in data or 'text' not in data:
        return {"error": "Missing required fields (author and text)"}, 400
    
    new_quote = {
        "id": get_next_id(),
        "author": data['author'],
        "text": data['text']
    }
    quotes.append(new_quote)
    return new_quote, 201

@app.route("/quotes/<int:quote_id>", methods=['PUT'])
def edit_quote(quote_id):
    quote = next((q for q in quotes if q['id'] == quote_id), None)
    
    if not quote:
        return {"error": "Quote not found"}, 404
    
    new_data = request.json
    
    if 'author' in new_data:
        quote['author'] = new_data['author']
    if 'text' in new_data:
        quote['text'] = new_data['text']
    
    return quote, 200

@app.route("/quotes/<int:quote_id>", methods=['DELETE'])
def delete_quote(quote_id):
    global quotes
    quote = next((q for q in quotes if q['id'] == quote_id), None)
    
    if not quote:
        return {"error": "Quote not found"}, 404
    
    quotes = [q for q in quotes if q['id'] != quote_id]
    
    return {"message": f"Quote with id {quote_id} was deleted."}, 200

if __name__ == "__main__":
    app.run(debug=True)