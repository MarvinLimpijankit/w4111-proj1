from sqlalchemy import *
from sqlalchemy import exc
from sqlalchemy.pool import NullPool
from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from sqlalchemy.sql.functions import user
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
        "SELECT r.*, a.*, cui.cuisine FROM restaurants r\
        LEFT JOIN addresses a ON r.a_id = a.a_id\
        LEFT JOIN ( SELECT re.r_id, STRING_AGG(c.cuisine_name, \', \') as cuisine\
        FROM restaurants re\
        LEFT JOIN is_cuisine ic ON ic.r_id = re.r_id\
        LEFT JOIN cuisines c ON ic.c_id = c.c_id\
        GROUP BY re.r_id) as cui\
        ON r.r_id = cui.r_id",
    ).fetchall()

    for r in restaurants:
        print(r['trendy_flag'])

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

    return render_template('home.html', user=g.user, restaurants = restaurants, r_visited = r_visited, r_wish = r_wish, r_rev = r_rev)

@bp.route('/profile')
@login_required
def profile():
    g.conn = engine.connect()

#show user current reservations
    reserve = g.conn.execute(
        "SELECT res.*, r.name FROM users u\
        LEFT JOIN reservations res ON u.u_id = res.u_id\
        LEFT JOIN restaurants r ON res.r_id = r.r_id\
        WHERE u.u_id = %s", (g.user['u_id'])
    ).fetchall()

#show users visited / reviews list
    visited = g.conn.execute(
        "SELECT r.r_id, r.name, v.date_visited, rev.* FROM users u\
        LEFT JOIN visited v ON u.u_id = v.u_id\
        LEFT JOIN restaurants r ON v.r_id = r.r_id\
        LEFT JOIN reviews rev ON u.u_id = rev.u_id and rev.r_id = r.r_id\
        WHERE u.u_id = %s", (g.user['u_id'])
    ).fetchall()

#show user wishlist
    wishlist = g.conn.execute(
        "SELECT r.r_id, r.name, w.date_added FROM users u\
        LEFT JOIN wants_to_eat w ON u.u_id = w.u_id\
        LEFT JOIN restaurants r ON w.r_id = r.r_id\
        WHERE u.u_id = %s", (g.user['u_id'])
    ).fetchall()

#show list of followed users
    user_followed = g.conn.execute(
        "SELECT u.user_name, f.follows_since,\
        CASE\
            WHEN f2.u_id IS NULL THEN 'false'\
            ELSE 'true' END AS u_id\
        FROM follows f\
        LEFT JOIN users u ON f.follows_id = u.u_id\
        LEFT JOIN follows f2 ON f.follows_id = f2.u_id AND f2.follows_id = f.u_id\
        WHERE f.u_id = %s", (g.user['u_id'])
    ).fetchall()

    return render_template('profile.html', user=g.user, res = reserve, visited = visited, wishlist = wishlist, user_followed = user_followed)

@bp.route('/users')
@login_required
def users():
    g.conn = engine.connect()

    users_followed = g.conn.execute(
        "SELECT u.u_id, u.user_name,\
        CASE\
            WHEN f.follows_since IS NULL THEN 'false'\
            ELSE 'true' END AS follow_flag\
        FROM users u\
        LEFT JOIN follows f\
        ON f.follows_id = u.u_id\
        AND f.u_id = %s\
        WHERE u.u_id != %s", (g.user['u_id'],g.user['u_id'])
    ).fetchall()

    return render_template('users.html', user=g.user, user_followed = users_followed)

#add routing reviewing, reservations, visited, wishlist

#Wishlist: similar to home, but only for restaurants in corresponding wants to eat
@bp.route('/wishlist')
@login_required
def wishlist(): 
    g.conn = engine.connect()

    #querying restaurant info for all rsetaurant in users wants to eat
    restaurants = g.conn.execute(
        "WITH t1 AS(\
            SELECT r.*, a.*, cui.cuisine FROM restaurants r\
            LEFT JOIN addresses a ON r.a_id = a.a_id\
            LEFT JOIN ( SELECT re.r_id, STRING_AGG(c.cuisine_name, \', \') as cuisine\
            FROM restaurants re\
            LEFT JOIN is_cuisine ic ON ic.r_id = re.r_id\
            LEFT JOIN cuisines c ON ic.c_id = c.c_id\
            GROUP BY re.r_id) as cui\
            ON r.r_id = cui.r_id)\
        SELECT DISTINCT t1.*\
        FROM t1\
        LEFT JOIN wants_to_eat w ON t1.r_id = w.r_id\
        WHERE w.u_id = %s", (g.user['u_id']))

    #what has the user already visited
    user_visited = g.conn.execute(
        "SELECT v.r_id FROM users u LEFT JOIN visited v ON u.u_id = v.u_id WHERE u.u_id = %s", (g.user['u_id'])
    ).fetchall()
    r_visited = []
    for uv in user_visited:
        r_visited.append(uv['r_id'])
        
    #what has the user already reviewed
    user_rev = g.conn.execute(
        "SELECT rev.r_id FROM users u LEFT JOIN reviews rev ON u.u_id = rev.u_id WHERE u.u_id = %s",(g.user['u_id'])
    ).fetchall()
    r_rev = []
    for urev in user_rev:
        r_rev.append(urev['r_id'])

    return render_template('wishlist.html', user=g.user, restaurants = restaurants, r_visited = r_visited, r_rev = r_rev)

#Visited: same as wishlist, but for wants to eat
@bp.route('/visited')
@login_required
def visited(): 
    g.conn = engine.connect()
    
    restaurants = g.conn.execute(
        "WITH t1 AS(\
            SELECT r.*, a.*, cui.cuisine FROM restaurants r\
            LEFT JOIN addresses a ON r.a_id = a.a_id\
            LEFT JOIN ( SELECT re.r_id, STRING_AGG(c.cuisine_name, \', \') as cuisine\
            FROM restaurants re\
            LEFT JOIN is_cuisine ic ON ic.r_id = re.r_id\
            LEFT JOIN cuisines c ON ic.c_id = c.c_id\
            GROUP BY re.r_id) as cui\
            ON r.r_id = cui.r_id)\
        SELECT DISTINCT t1.*\
        FROM t1\
        LEFT JOIN visited v ON t1.r_id = v.r_id\
        WHERE v.u_id = %s", (g.user['u_id']))

    #what has the user already visited
    user_visited = g.conn.execute(
        "SELECT v.r_id FROM users u LEFT JOIN visited v ON u.u_id = v.u_id WHERE u.u_id = %s", (g.user['u_id'])
    ).fetchall()
    r_visited = []
    for uv in user_visited:
        r_visited.append(uv['r_id'])
        
    #what has the user already reviewed
    user_rev = g.conn.execute(
        "SELECT rev.r_id FROM users u LEFT JOIN reviews rev ON u.u_id = rev.u_id WHERE u.u_id = %s",(g.user['u_id'])
    ).fetchall()
    r_rev = []
    for urev in user_rev:
        r_rev.append(urev['r_id'])

    return render_template('visited.html', user=g.user, restaurants = restaurants, r_rev = r_rev, r_visited = r_visited)

# <a href="{{ url_for('apl.follow', u_id = u['u_id']) }}">Click here to Follow!</a>
@bp.route('/<int:u_id>/follow')
@login_required
def follow(u_id):
    if request.method == 'GET':
        g.conn = engine.connect()
        user_id = u_id

        g.conn.execute(
            "INSERT INTO follows (u_id, follows_id, follows_since) VALUES(%s,%s,NOW())",(g.user['u_id'], user_id))
    
    return redirect(url_for('apl.users'))

#  <a href="{{ url_for('apl.unfollow', u_id = u['u_id']) }}">Unfollow</a>
@bp.route('/<int:u_id>/unfollow')
@login_required
def unfollow(u_id):
    if request.method == 'GET':
        g.conn = engine.connect()
        user_id = u_id

        g.conn.execute(
            "DELETE FROM follows f WHERE f.u_id = %s AND f.follows_id = %s",(g.user['u_id'], str(user_id)))
    
    return redirect(url_for('apl.users'))


