from flask import Flask, request, jsonify, g, abort
from pathlib import Path
import sqlite3
from werkzeug.exceptions import HTTPException

BASE_DIR = Path(__file__).parent
path_to_db = BASE_DIR / "store.db"  # <- тут путь к БД# Используем так:

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(path_to_db)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.errorhandler(HTTPException)
def handle_exeption(e):
    return jsonify({"message": e.description}), e.code

# URL: quotes
@app.route("/quotes")
def get_quotes() -> list[dict[str, any]]: 

    select_quotes = "SELECT * from quotes"

    cursor = get_db().cursor()
    cursor.execute(select_quotes)
    quotes_db = cursor.fetchall() # list[tuple]

    # Необходимо преобразовать данные
    keys = ("id", "author", "text")
    quotes = []
    for quote_db in quotes_db:
        quote = dict(zip(keys, quote_db))
        quotes.append(quote)
    return jsonify(quotes), 200

# URL: quotes/<int:quote_id>
@app.route("/quotes/<int:quote_id>")
def get_quote(quote_id):
    sel_quote = "select * from quotes where id = ?"
    cursor = get_db().cursor()
    quote_db = cursor.execute(sel_quote, (quote_id,)).fetchone()
    if quote_db:
        keys = ("id", "author", "text")
        quote = dict(zip(keys, quote_db))
        return jsonify(quote), 200
    return ({"error": "Quote not found"}), 404

# URL: quotes/count
@app.route("/quotes/count")
def get_quotes_count():
    sel_count = "select count(*) cnt from quotes"
    cursor = get_db().cursor()
    cursor.execute(sel_count)
    count = cursor.fetchone()
    if count:
        return jsonify(count=count[0]), 200
    abort(503)

# URL: quotes POST
@app.route("/quotes", methods=['POST'])
def create_quote():
    data = request.json
    if not data or 'author' not in data or 'text' not in data:
        return {"error": "Missing required fields (author and text)"}, 400
    
    ins_sql = "insert into quotes (author, text) values (?,?)"
    connection = get_db()
    cursor = connection.cursor()
    cursor.execute(ins_sql, (data['author'], data['text']))
    answer = cursor.lastrowid
    connection.commit()
    data['id'] = answer
    return jsonify(data), 201

# URL: quotes PUT
@app.route("/quotes/<int:quote_id>", methods=['PUT'])
def edit_quote(quote_id):
    new_data = request.json
    att: set = set(new_data.keys()) & set(('author', 'text'))
    
    udt_sql = f"Update quotes set {', '.join(i + '= ? 'for i in att)} where id = ?"
    params = tuple(new_data.get(i) for i in att) + (quote_id,)
    connection = get_db()
    cursor = connection.cursor()
    cursor.execute(udt_sql, params)
    rows = cursor.rowcount
    if rows:
        connection.commit()
        cursor.close()
        responce, status_code = get_quote(quote_id)
        if status_code == 200:
            return responce
    connection.rollback()
    abort(404, "Quote not found")

# URL: quotes DELETE
@app.route("/quotes/<int:quote_id>", methods=['DELETE'])
def delete_quote(quote_id: int):
    del_sql = f"delete from quotes where id = ?"
    params = (quote_id,)
    connection = get_db()
    cursor = connection.cursor()
    cursor.execute(del_sql, params)
    rows = cursor.rowcount
    global quotes
    if rows:
        connection.commit()
        cursor.close()
        return jsonify({"message": f"Quote with id {quote_id} has deleted."}), 200
    abort(404, f"Quote with id {quote_id} not found")

if __name__ == "__main__":
    app.run(debug=True)