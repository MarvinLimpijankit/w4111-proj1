#code credit: https://flask.palletsprojects.com/en/2.0.x/tutorial/views/

import functools
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

        #can add if email exists or user name exists (both of these are candidate keys)
        #then we redirect straight to login

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

        error = None
        user = g.conn.execute(
            "SELECT * FROM users WHERE email = %s", (email+" "*(256-len(email))),
        ).fetchone()

        if user is not None:
            print("password_input:" + password)
            print("password:" + user['password'])
            print("pass_length", len(user['password']))

        if user is None:
            error = 'Incorrect email.'
        
        #removes trailing spaces
        elif not user['password'].strip() == password:
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user['u_id'].strip()

            #go to the logged-in home page
            return redirect(url_for('apl.home'))

        flash(error)

    return render_template('login.html')

#will run before any view
#determines which user is loggen in (if there is none, then g.user will be None)
@bp.before_app_request
def login_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = g.conn.execute(
            "SELECT * FROM users WHERE u_id = %s", (user_id),
        ).fetchone()

#logouts of the session
@bp.route('/logout')
def logout():

    session.clear()

    #return to homepage
    return redirect(url_for('index'))

#allows for some URL to require login
#will be helpful when seeing profile
#and using our webstie in general
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view