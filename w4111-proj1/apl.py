from sqlalchemy import *
from sqlalchemy import exc
from sqlalchemy.pool import NullPool
from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from auth import login_required

bp = Blueprint('apl', __name__, url_prefix='/apl')

DATABASEURI = "postgresql://mmo2134:3889@34.74.246.148/proj1part2"
engine = create_engine(DATABASEURI)

@bp.route('/home')
@login_required
def home():
#list of restaurants
#user can add reservation (w/ time and date)
#user can label a restaurant as visited or wishlisted
    g.conn = engine.connect()
    restaurants = g.conn.execute(
        "SELECT * FROM restaurants r\
        LEFT JOIN addresses a ON r.a_id = a.a_id",
    ).fetchall()

    #what has the user already visited
    user_visited = g.conn.execute(
        "SELECT v.r_id FROM users u LEFT JOIN visited v ON u.u_id = v.u_id WHERE u.u_id = %s", (g.user['u_id'])
    ).fetchall()
    r_visited = []
    for uv in user_visited:
        r_visited.append(uv['r_id'])

    #what has the user already wishlisted
    user_wishlist = g.conn.execute(
        "SELECT w.r_id FROM users u LEFT JOIN wants_to_eat w ON u.u_id = w.u_id WHERE u.u_id = %s",(g.user['u_id'])
    ).fetchall()
    r_wish = []
    for uw in user_wishlist:
        r_wish.append(uw['r_id'])

    #what has the user already reviewed
    user_rev = g.conn.execute(
        "SELECT rev.r_id FROM users u LEFT JOIN reviews rev ON u.u_id = rev.u_id WHERE u.u_id = %s",(g.user['u_id'])
    ).fetchall()
    r_rev = []
    for urev in user_rev:
        r_rev.append(urev['r_id'])

    #bug fix
    print(r_visited)
    print(r_wish)
    print(r_rev)

    return render_template('home.html', user=g.user, restaurants = restaurants, r_visited = r_visited, r_wish = r_wish, r_rev = r_rev)

@bp.route('/profile')
def profile():
#show user current reservations
#show users visited list
#show user wishlist
#show list of followed users
    return render_template('index')


#add routing reviewing, reservations, visited, wishlist
