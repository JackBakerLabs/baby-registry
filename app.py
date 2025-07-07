import os
import pandas as pd
from flask import Flask, render_template, redirect, url_for, flash, request, session
from flask_sqlalchemy import SQLAlchemy

# --- load your CSV seed data ---
gifts_df = pd.read_csv('gifts.csv')
if 'persons' in gifts_df.columns:
    gifts_df['persons'] = gifts_df['persons'].fillna('')
gifts = gifts_df.values.tolist()

# --- Flask + SQLAlchemy setup ---
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'supersecretkey')


app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://registry_ni9u_user:IshazfFwVkQ2pIOUWDCv2q42z0jy0zQ1@dpg-d1m4cdvdiees738oms8g-a.oregon-postgres.render.com/registry_ni9u"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class Gift(db.Model):
    __tablename__ = 'gifts'
    id                 = db.Column(db.Integer, primary_key=True)
    name               = db.Column(db.String, nullable=False)
    description        = db.Column(db.String)
    remaining_quantity = db.Column(db.Integer, nullable=False)
    max_quantity       = db.Column(db.Integer, nullable=False)
    persons            = db.Column(db.Text, default='')

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
    db.create_all()
    if Gift.query.count() == 0:
        for name, desc, rem, mx, persons in gifts:
            g = Gift(
                name=name,
                description=desc,
                remaining_quantity=int(rem),
                max_quantity=int(mx),
                persons='X'
            )
            db.session.add(g)
        db.session.commit()


# --- your routes (unchanged) ---
@app.route('/')
def index():
    gifts = Gift.query.all()
    return render_template('index.html', gifts=gifts)

@app.route('/set_name', methods=['POST'])
def set_name():
    session['name'] = request.form['name']
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

    user = session['name']
    gift = Gift.query.get(gift_id)
    if not gift:
        flash("Gift not found.", "warning")
    else:
        attendees = gift.persons.split(',') if gift.persons else []
        if user in attendees:
            flash(f"You have already registered for '{gift.name}'.", "info")
        elif gift.remaining_quantity > 0:
            gift.remaining_quantity -= 1
            attendees.append(user)
            gift.persons = ','.join(attendees)
            db.session.commit()
            flash(message_map.get(gift.name, "Registered successfully!"), "success")
        else:
            flash(f"'{gift.name}' is no longer available.", "danger")

    return redirect(url_for('index'))

@app.route('/unregister/<int:gift_id>')
def unregister(gift_id):
    if 'name' not in session:
        flash("You must be logged in to unregister.", "warning")
        return redirect(url_for('index'))

    user = session['name']
    gift = Gift.query.get(gift_id)
    if not gift:
        flash("Gift not found.", "warning")
    else:
        attendees = gift.persons.split(',') if gift.persons else []
        if user in attendees:
            attendees.remove(user)
            gift.persons = ','.join(attendees)
            if gift.remaining_quantity < gift.max_quantity:
                gift.remaining_quantity += 1
            db.session.commit()
            flash(f"You have unregistered from '{gift.name}'.", "success")
        else:
            flash(f"You weren't registered for '{gift.name}'.", "info")

    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        init_db()

    app.run(debug=True)
