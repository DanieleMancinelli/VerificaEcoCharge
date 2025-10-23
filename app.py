from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db_config = {
    'host': 'mysql-54fee60-correzione-verifica21-10.j.aivencloud.com',
    'user': 'avnadmin',
    'password': 'AVNS_iY9T-ZLq2IPFDEue9p6',
    'database': 'EcoCharge',
    'port': 19384
}

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# ================================
# LOGIN
# ================================
@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM amministratori WHERE email=%s", (email,))
        admin = cursor.fetchone()
        if admin and check_password_hash(admin['password_hash'], password):
            session['user_id'] = admin['id_admin']
            session['is_admin'] = True
            cursor.close()
            conn.close()
            return redirect(url_for('admin_dashboard'))

        cursor.execute("SELECT * FROM utenti WHERE email=%s", (email,))
        user = cursor.fetchone()
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id_utente']
            session['is_admin'] = False
            cursor.close()
            conn.close()
            return redirect(url_for('map_view'))

        flash("Credenziali errate.", "error")
        cursor.close()
        conn.close()
    return render_template('login.html')


# ================================
# REGISTRAZIONE
# ================================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nome = request.form['nome']
        cognome = request.form['cognome']
        email = request.form['email']
        password = request.form['password']
        password_hash = generate_password_hash(password)

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM utenti WHERE email=%s", (email,))
        if cursor.fetchone():
            flash("Email già registrata.", "error")
            cursor.close()
            conn.close()
            return redirect(url_for('register'))

        cursor.execute("""
            INSERT INTO utenti (nome, cognome, email, password_hash)
            VALUES (%s, %s, %s, %s)
        """, (nome, cognome, email, password_hash))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Registrazione avvenuta con successo!", "success")
        return redirect(url_for('login'))
    return render_template('register.html')


# ================================
# LOGOUT
# ================================
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ================================
# MAPPA UTENTE
# ================================
@app.route('/map')
def map_view():
    if 'user_id' not in session or session.get('is_admin'):
        return redirect(url_for('login'))

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM colonnine")
    colonnine = cursor.fetchall()

    cursor.execute("SELECT id_colonnina FROM ricariche WHERE CURRENT_TIMESTAMP BETWEEN data_inizio AND data_fine")
    occupate = [row['id_colonnina'] for row in cursor.fetchall()]

    cursor.close()
    conn.close()
    return render_template('map.html', colonnine=colonnine, occupate=occupate)


# ================================
# DASHBOARD ADMIN
# ================================
@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    # Tutti gli utenti
    cursor.execute("SELECT * FROM utenti")
    utenti = cursor.fetchall()

    # Tutte le colonnine
    cursor.execute("SELECT * FROM colonnine")
    colonnine = cursor.fetchall()

    # Ricariche giornaliere per grafico
    cursor.execute("""
        SELECT DATE(data_inizio) AS giorno, COUNT(*) AS totale
        FROM ricariche
        GROUP BY giorno
        ORDER BY giorno
    """)
    ricariche_giornaliere = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('admin_dashboard.html', utenti=utenti, colonnine=colonnine, ricariche=ricariche_giornaliere)


# ================================
# CRUD colonnine (Admin)
# ================================
@app.route('/admin/colonnina/add', methods=['POST'])
def add_colonnina():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    indirizzo = request.form['indirizzo']
    lat = float(request.form['latitudine'])
    lon = float(request.form['longitudine'])
    potenza = int(request.form['potenza_kw'])
    NIL = request.form['NIL']

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO colonnine (indirizzo, latitudine, longitudine, potenza_kw, NIL)
        VALUES (%s, %s, %s, %s, %s)
    """, (indirizzo, lat, lon, potenza, NIL))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/colonnina/delete/<int:id>', methods=['POST'])
def delete_colonnina(id):
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM colonnine WHERE id_colonnina=%s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('admin_dashboard'))


# ================================
# CRUD utenti (Admin)
# ================================
@app.route('/admin/utente/delete/<int:id>', methods=['POST'])
def delete_utente(id):
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM utenti WHERE id_utente=%s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('admin_dashboard'))


if __name__ == "__main__":
    app.run(debug=True)
