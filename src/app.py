from flask import Flask, render_template, request, jsonify, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector

app = Flask(__name__)
app.secret_key = 'sekret'

def db():
    return mysql.connector.connect(
        host="185.114.247.43",
        port=3306,
        database="sch688_vvedenie",
        user="sch688_vvedenie",
        password="Qwerty123")

@app.route('/user_register', methods=['POST'])
def user_register():
    req = request.get_json()
    cnx = db()

    name = req['name']
    login = req['email']
    password = generate_password_hash(req['password'])
    date = (name, login, password)
    cur = cnx.cursor()
    try:
        cur.execute('INSERT INTO `users`(`username`, `email`, `password_hash`) VALUES (%s, %s, %s)', date)
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

@app.route('/topup', methods=['POST'])
def topup():
    if 'user_id' not in session:
        return 'ne avtorizovan', 401
    req = request.get_json()
    try:
        amount = float(req['amount'])
    except (ValueError, TypeError):
        return 'ne chislo', 400
    if amount <= 0:
        return 'summa dolzhna byt bolshe 0', 400

    cnx = db()
    cur = cnx.cursor()
    cur.execute('UPDATE `users` SET `balance` = `balance` + %s WHERE `id` = %s', (amount, session['user_id']))
    cnx.commit()
    cur.execute('SELECT `balance` FROM `users` WHERE `id` = %s', (session['user_id'],))
    balance = cur.fetchone()[0]
    cnx.close()

    return jsonify(balance=float(balance))

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

app.run(port=5001)
