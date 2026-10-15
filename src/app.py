import os
import requests as http_requests
from flask import Flask, render_template, request, jsonify, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector

app = Flask(__name__)
app.secret_key = 'sekret'

# ==== Настройки AI ====
AI_API_URL = os.environ.get('AI_API_URL', 'https://api.openai.com/v1/chat/completions')
AI_API_KEY = os.environ.get('AI_API_KEY', '')
AI_MODEL   = os.environ.get('AI_MODEL', 'gpt-4o-mini')


def db():
    return mysql.connector.connect(
        host="185.114.247.43",
        port=3306,
        database="sch688_vvedenie",
        user="sch688_vvedenie",
        password="Qwerty123")


# ===================== РЕГИСТРАЦИЯ / ЛОГИН =====================

@app.route('/user_register', methods=['POST'])
def user_register():
    req = request.get_json()
    cnx = db()
    name = req['name']
    login = req['email']
    password = generate_password_hash(req['password'])
    cur = cnx.cursor()
    try:
        cur.execute(
            'INSERT INTO `users`(`username`, `email`, `password_hash`) VALUES (%s, %s, %s)',
            (name, login, password)
        )
    except mysql.connector.IntegrityError:
        cnx.close()
        return 'takoy email uzhe est', 400
    cnx.commit()
    session['user_id'] = cur.lastrowid
    cnx.close()
    return 'vse ok'


@app.route('/user_login', methods=['POST'])
def user_login():
    req = request.get_json()
    cnx = db()
    cur = cnx.cursor()
    cur.execute('SELECT `id`, `password_hash` FROM `users` WHERE `email` = %s', (req['email'],))
    row = cur.fetchone()
    cnx.close()

    if row is None or not check_password_hash(row[1], req['password']):
        return 'nevernyi login ili parol', 401
    session['user_id'] = row[0]
    return 'vse ok'


# ===================== ПОПОЛНЕНИЕ =====================

@app.route('/topup', methods=['POST'])
def topup():
    if 'user_id' not in session:
        return jsonify(error='ne avtorizovan'), 401
    req = request.get_json()
    try:
        amount = float(req['amount'])
    except (ValueError, TypeError):
        return jsonify(error='ne chislo'), 400
    if amount <= 0:
        return jsonify(error='summa dolzhna byt bolshe 0'), 400

    cnx = db()
    cur = cnx.cursor()
    cur.execute('UPDATE `users` SET `balance` = `balance` + %s WHERE `id` = %s',
                (amount, session['user_id']))
    cnx.commit()
    cur.execute('SELECT `balance` FROM `users` WHERE `id` = %s', (session['user_id'],))
    balance = cur.fetchone()[0]
    cnx.close()
    return jsonify(balance=float(balance))


# ===================== AI-ПОМОЩНИК =====================

@app.route('/ai_chat')
def ai_chat_page():
    if 'user_id' not in session:
        return redirect('/login')
    cnx = db()
    cur = cnx.cursor()
    cur.execute('SELECT `username`, `balance` FROM `users` WHERE `id` = %s', (session['user_id'],))
    row = cur.fetchone()
    cnx.close()
    return render_template('ai_chat.html', name=row[0], balance=row[1])


@app.route('/ai_suggest', methods=['POST'])
def ai_suggest():
    if 'user_id' not in session:
        return jsonify(error='ne avtorizovan'), 401

    req = request.get_json() or {}
    prompt = (req.get('prompt') or '').strip()
    if not prompt:
        return jsonify(error='pustoy zapros'), 400

    history = req.get('history') or []

    cnx = db()
    cur = cnx.cursor()
    cur.execute('SELECT `username`, `balance` FROM `users` WHERE `id` = %s', (session['user_id'],))
    row = cur.fetchone()
    cnx.close()

    name, balance = row[0], float(row[1])
    system_prompt = (
        "Ты помощник в приложении пополнения баланса. "
        f"Пользователь: {name}, текущий баланс: {balance}. "
        "Отвечай кратко (1–3 предложения), по-русски. "
        "Если спрашивают про сумму пополнения — предложи разумную сумму."
    )

    messages = [{"role": "system", "content": system_prompt}]
    for m in history:
        if m.get('role') in ('user', 'assistant') and m.get('content'):
            messages.append({"role": m['role'], "content": m['content']})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": AI_MODEL,
        "messages": messages,
        "temperature": 0.6,
    }
    headers = {
        "Authorization": f"Bearer {AI_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        r = http_requests.post(AI_API_URL, json=payload, headers=headers, timeout=30)
        r.raise_for_status()
        data = r.json()
        answer = data['choices'][0]['message']['content']
    except Exception as e:
        return jsonify(error=f'oshibka AI: {e}'), 502

    return jsonify(answer=answer)


# ===================== ЗМЕЙКА =====================

@app.route('/snake')
def snake_page():
    if 'user_id' not in session:
        return redirect('/login')
    cnx = db()
    cur = cnx.cursor()
    cur.execute('SELECT `username` FROM `users` WHERE `id` = %s', (session['user_id'],))
    row = cur.fetchone()
    cnx.close()
    return render_template('snake.html', name=row[0])


# ===================== СТРАНИЦЫ =====================

@app.route("/")
def registration():
    return render_template('registration.html')


@app.route("/login")
def login():
    return render_template('login.html')


@app.route("/balance")
def balance():
    if 'user_id' not in session:
        return redirect('/login')
    cnx = db()
    cur = cnx.cursor()
    cur.execute('SELECT `username`, `balance` FROM `users` WHERE `id` = %s', (session['user_id'],))
    row = cur.fetchone()
    cnx.close()
    return render_template('balance.html', name=row[0], balance=row[1])


@app.route("/logout")
def logout():
    session.clear()
    return redirect('/login')


if __name__ == '__main__':
    app.run(port=5001, debug=True)