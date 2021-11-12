from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for

bp = Blueprint('auth', __name__, url_prefix='/auth')

DATABASEURI = "postgresql://mmo2134:3889@34.74.246.148/proj1part2"
engine = create_engine(DATABASEURI)


@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        g.conn = engine.connect()
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'

        #number of users
        user_id = g.conn.execute("SELECT COUNT(*) FROM users")

        if error is None:
            try:
                g.conn.execute(
                    "INSERT INTO users (user_id, username, email, password) VALUES (?, ?)",
                    (username, password),
                )
                g.conn.commit()
            except g.conn.IntegrityError:
                error = f"User {username} is already registered."
            else:
                return redirect(url_for("auth.login"))

        flash(error)
    return render_template('auth/register.html')