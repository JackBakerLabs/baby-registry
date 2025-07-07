from flask import Flask, render_template, redirect, url_for, flash, request, session
import sqlite3
import os
import pandas as pd

# Load the Excel file
csv_file = 'gifts.csv'
gifts_df = pd.read_csv(csv_file)


# Convert the DataFrame to a list of tuples
gifts = gifts_df.values.tolist()


app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Needed for flash messages

DB_NAME = 'gifts.db'

message_map = {
    gifts[0][0]: "Maybe he's born with it... Maybe it's baby cream.",
    gifts[1][0]: "Push it to the Muslin-it!",
    gifts[2][0]: "Baby Disarmed!",
    gifts[3][0]: "Clothes maketh' the man",
    gifts[4][0]: "Sleep tight baby!",
    gifts[5][0]: "First nappies, of thousands!",
    gifts[6][0]: "For the busy baby on the go",
    gifts[7][0]: "Suda-creme de la creme",
    gifts[8][0]: "Making the floor 20% more fun",
    gifts[9][0]: "The best a baby can get."
}



def init_db():
    if not os.path.exists(DB_NAME):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
    CREATE TABLE gifts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        remaining_quantity INTEGER NOT NULL,
        max_quantity INTEGER NOT NULL,
        persons TEXT DEFAULT ''
    )
    ''')
        cursor.executemany('''
            INSERT INTO gifts (name, description, remaining_quantity, max_quantity, persons)
            VALUES (?, ?, ?, ?, ?)
        ''', gifts)
        conn.commit()
        conn.close()
init_db()

@app.route('/')
def index():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description, remaining_quantity, max_quantity, persons FROM gifts")
    gifts = cursor.fetchall()
    conn.close()
    return render_template('index.html', gifts=gifts)

@app.route('/set_name', methods=['POST'])
def set_name():
    session['name'] = request.form.get('name')
    flash(f"Hello, {session['name']}! You are now registered.", "info")
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('name', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('index'))
@app.route('/register/<int:gift_id>')
def register(gift_id):
    if 'name' not in session:
        flash("Please enter your name before registering.", "warning")
        return redirect(url_for('index'))

    user_name = session['name']
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT name, remaining_quantity, persons FROM gifts WHERE id = ?", (gift_id,))
    gift = cursor.fetchone()

    if gift:
        name, quantity, persons = gift
        registered_names = persons.split(",") if persons else []

        if user_name in registered_names:
            flash(f"You have already registered for '{name}'.", "info")
        elif quantity > 0 or quantity < 0:
            if quantity >= 0:
                cursor.execute("UPDATE gifts SET remaining_quantity = remaining_quantity - 1 WHERE id = ?", (gift_id,))
            registered_names.append(user_name)
            updated_persons = ",".join(registered_names)
            cursor.execute("UPDATE gifts SET persons = ? WHERE id = ?", (updated_persons, gift_id))
            conn.commit()
            flash(f"{message_map.get(name, 'Registered successfully!')}", "success")
        else:
            flash(f"'{name}' is no longer available.", "danger")
    else:
        flash("Gift not found.", "warning")

    conn.close()
    return redirect(url_for('index'))


@app.route('/unregister/<int:gift_id>')
def unregister(gift_id):
    if 'name' not in session:
        flash("You must be logged in to unregister.", "warning")
        return redirect(url_for('index'))

    user_name = session['name']
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT name, remaining_quantity, persons FROM gifts WHERE id = ?", (gift_id,))
    gift = cursor.fetchone()

    if gift:
        name, quantity, persons = gift
        registered_names = persons.split(",") if persons else []

        if user_name in registered_names:
            registered_names.remove(user_name)
            updated_persons = ",".join(registered_names)
            if quantity >= 0:
                cursor.execute("UPDATE gifts SET remaining_quantity = remaining_quantity + 1, persons = ? WHERE id = ?", (updated_persons, gift_id))
            else:
                cursor.execute("UPDATE gifts SET persons = ? WHERE id = ?", (updated_persons, gift_id))
            conn.commit()
            flash(f"You have unregistered from '{name}'.", "success")
        else:
            flash(f"You weren't registered for '{name}'.", "info")
    else:
        flash("Gift not found.", "warning")

    conn.close()
    return redirect(url_for('index'))


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
