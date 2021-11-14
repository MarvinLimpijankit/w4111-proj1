from sqlalchemy import *
from sqlalchemy import exc
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
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        password = request.form['password']
        g.conn = engine.connect()
        error = None

        #check none of the fields is null
        if not username:
            error = 'Username is required.'
        elif not email:
            error = 'Email is required.'
        elif not first_name:
            error = 'First Name is required.'
        elif not last_name:
            error = 'Last Name is required.'
        elif not password:
            error = 'Password is required.'

        #counts number of users
        user_id = g.conn.execute("SELECT COUNT(*) as c FROM users")
        for u in user_id:
            user_count = u['c']

        #if neither is null
        if error is None:
            try:
                g.conn.execute(
                    "INSERT INTO users (u_id, user_name, email, first_name, last_name, join_date, is_elite, password) VALUES (%s,%s,%s,%s,%s, NOW(), FALSE, %s)",
                    (user_count+1, username, email, first_name, last_name, password),
                )
            #didnt match a constraint
            except exc.IntegrityError:
                error = "Invalid Input."
            
            #if it already exists
            else:
                return redirect(url_for("auth.login"))

        flash(error)
    return render_template('register.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        g.conn = engine.connect()

        error = None
        user = g.conn.execute(
            "SELECT * FROM users WHERE email = ?", (email)
        ).fetchone()

        if user is None:
            error = 'Incorrect email.'
        elif user['password'] != password:
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user['u_id']
            return redirect(url_for('index'))

        flash(error)

    return render_template('login.html')