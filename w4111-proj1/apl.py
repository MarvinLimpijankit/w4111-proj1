from sqlalchemy import *
from sqlalchemy import exc
from sqlalchemy.pool import NullPool
from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from sqlalchemy.sql.functions import user
from auth import login_required
from datetime import datetime 
from sqlalchemy.sql import text


bp = Blueprint('apl', __name__, url_prefix='/apl')

DATABASEURI = "postgresql://mmo2134:3889@34.74.246.148/proj1part2"
engine = create_engine(DATABASEURI)

@bp.route('/home')
@login_required
def home():
#list of restaurants
#user can add reservation (w/ time and date)
#user can label a restaurant as visited or wishlisted
    restaurants = g.conn.execute(
        "SELECT r.*, a.*, cui.cuisine,\
        CASE\
            WHEN ic.r_id IS NULL THEN 'FALSE'\
            ELSE 'TRUE' END AS chain_flag\
        FROM restaurants r\
        LEFT JOIN addresses a ON r.a_id = a.a_id\
        LEFT JOIN ( SELECT re.r_id, STRING_AGG(c.cuisine_name, \', \') as cuisine\
        FROM restaurants re\
        LEFT JOIN is_cuisine ic ON ic.r_id = re.r_id\
        LEFT JOIN cuisines c ON ic.c_id = c.c_id\
        GROUP BY re.r_id) as cui\
        ON r.r_id = cui.r_id\
        LEFT JOIN is_chain ic\
        ON ic.r_id = r.r_id"
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

    return render_template('home.html', user=g.user, restaurants = restaurants, r_visited = r_visited, r_wish = r_wish, r_rev = r_rev)

@bp.route('/search', methods=('GET', 'POST'))
@login_required
def search(): 
    
    if request.method == 'POST': 
        
        query = request.form['body'].lower()
    
        print(query)
    
        s = text("SELECT r.*, a.*, cui.cuisine FROM restaurants r\
        LEFT JOIN addresses a ON r.a_id = a.a_id\
        LEFT JOIN ( SELECT re.r_id, STRING_AGG(c.cuisine_name, \', \') as cuisine\
        FROM restaurants re\
        LEFT JOIN is_cuisine ic ON ic.r_id = re.r_id\
        LEFT JOIN cuisines c ON ic.c_id = c.c_id\
        GROUP BY re.r_id) as cui\
        ON r.r_id = cui.r_id\
        WHERE LOWER(r.name) LIKE :e1 OR\
        LOWER(r.restaurant_type) LIKE :e1 OR\
        LOWER(cui.cuisine) LIKE :e1")
    
        restaurants = g.conn.execute(s, e1 = '%' + query + '%').fetchall()
    
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
            
        return render_template('search.html', user=g.user, restaurants = restaurants, r_visited = r_visited, r_wish = r_wish, r_rev = r_rev)
    
    return render_template('search.html', user=g.user, restaurants = [], r_visited = [], r_wish = [], r_rev = [])

@bp.route('/profile')
@login_required
def profile():

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


#most common cuisine
    most_common = g.conn.execute(
        "SELECT cuisine_name\
        FROM visited v\
        LEFT JOIN is_cuisine ic ON ic.r_id = v.r_id\
        LEFT JOIN cuisines c ON ic.c_id = c.c_id\
        WHERE v.u_id = (%s)\
        GROUP BY c.cuisine_name\
        ORDER BY COUNT(*) DESC", (g.user['u_id'])
    ).fetchone()

    if most_common is not None:
        most_common = most_common['cuisine_name']

    return render_template('profile.html', user=g.user, res = reserve, visited = visited, wishlist = wishlist, user_followed = user_followed, fav_cuisine = most_common)

@bp.route('/users')
@login_required
def users():

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

#Visited: same as wishlist, but for visited
@bp.route('/visited')
@login_required
def visited(): 
    
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

        g.conn.execute(
            "INSERT INTO follows (u_id, follows_id, follows_since) VALUES(%s,%s,NOW())",(g.user['u_id'], u_id))
    
    return redirect(url_for('apl.users'))

#  <a href="{{ url_for('apl.unfollow', u_id = u['u_id']) }}">Unfollow</a>
@bp.route('/<int:u_id>/unfollow')
@login_required
def unfollow(u_id):
    if request.method == 'GET':

        g.conn.execute(
            "DELETE FROM follows f WHERE f.u_id = %s AND f.follows_id = %s",(g.user['u_id'], str(u_id)))
    
    return redirect(url_for('apl.users'))

# <a href="{{ url_for('apl.wish', r_id = r['r_id']) }}">Add to Wishlist!</a>
@bp.route('/<int:r_id>/wish')
@login_required
def wish(r_id):
    if request.method == 'GET':

        g.conn.execute(
            "INSERT INTO wants_to_eat (u_id, r_id, date_added) VALUES(%s,%s,NOW())",(g.user['u_id'], r_id))
    
    return redirect(url_for('apl.wishlist'))

# <a href="{{ url_for('apl.unwish', r_id = r['r_id']) }}">Remove from Wishlist!</a>
@bp.route('/<int:r_id>/unwish')
@login_required
def unwish(r_id):
    if request.method == 'GET':

        g.conn.execute(
            "DELETE FROM wants_to_eat w WHERE w.u_id = %s AND w.r_id = %s",(g.user['u_id'], str(r_id)))
    
    return redirect(url_for('apl.wishlist'))

# <a href="{{ url_for('apl.visit', r_id = r['r_id']) }}">Mark as Visisted!</a>
@bp.route('/<int:r_id>/visit')
@login_required
def visit(r_id):
    
    if request.method == 'GET': 
        
        g.conn.execute(
            "INSERT INTO visited (u_id, r_id, date_visited) VALUES(%s,%s,NOW())",(g.user['u_id'], r_id))
        
        return redirect(url_for('apl.visited'))

# <a href="{{ url_for('apl.unvisit', r_id = r['r_id']) }}">Remove from Visited</a>
@bp.route('/<int:r_id>/unvisit')
@login_required
def unvisit(r_id):
    
    if request.method == 'GET': 
        
        g.conn.execute(
            "DELETE FROM visited WHERE u_id = %s AND r_id = %s", (g.user['u_id'], str(r_id)))
        
        #ADD ALTERNATIVE: DELETE REVIEWS ASSOCIATED WITH u_id, r_id WHEN MARKING AS UNVISITED
        #g.conn.execute(
        #    "DELETE FROM revuews WHERE u_id = %s AND r_id = %s", (g.user['u_id'], str(r_id)))
        
        return redirect(url_for('apl.visited'))

# <a href="{{ url_for('apl.review', r_id = r['r_id']) }}">Add a Review.</a>
@bp.route('/<int:r_id>/review', methods=('GET', 'POST'))
@login_required
def review(r_id):
    r_id = str(r_id)
    res = g.conn.execute("SELECT * FROM restaurants r WHERE r_id = %s", (str(r_id))).fetchone()
    res_name = res['name']

    if request.method == 'POST':
        print("POST")
        #check if review already exists
        exists_flag = ""
        exists = g.conn.execute("SELECT * FROM reviews r WHERE r_id = %s AND u_id = %s", (r_id, g.user['u_id'])).fetchone()
        if exists is not None:
            exists_flag = True
        else:
            exists_flag = False

        #parse html data
        stars = request.form['s_rating']
        text_body = request.form['body']

        #checks if there is written text
        is_written = True
        if len(text_body.strip()) < 1:
            is_written = False
            text_body = None


        #if review already exists then set rev_id then update star_Rating, is_written, textbody
        if exists_flag:
            rev_id = exists['rev_id']

            g.conn.execute("UPDATE reviews SET star_rating = %s, is_written = %s, text = %s\
                WHERE rev_id = %s", (int(stars), is_written, text_body, rev_id))

            return redirect(url_for('apl.home'))

        #if not insert a new review in database
        else:
            #count number of reviews to use for rev_id
            rev_count = 0
            reviews = g.conn.execute("SELECT COUNT(*) as c FROM reviews")
            for u in reviews:
                rev_count = u['c']

            g.conn.execute(
                "INSERT INTO reviews (rev_id, star_rating, is_written, text, created_date, u_id, r_id)\
                VALUES(%s,%s,%s,%s,NOW(),%s,%s)",(rev_count+1, int(stars), is_written, text_body, g.user['u_id'], r_id ))

            return redirect(url_for('apl.visited'))

    return render_template('review.html', user = g.user, r_id = r_id, res_name = res_name)

# <a href="{{ url_for('apl.reserve', r_id = r['r_id']) }}">Reserve a Slot!.</a>
@bp.route('/<int:r_id>/reserve', methods=('GET', 'POST'))
@login_required
def reserve(r_id):
    
    r_id = str(r_id)
    res = g.conn.execute("SELECT * FROM restaurants r WHERE r_id = %s", (str(r_id))).fetchone()
    res_name = res['name']
    
    if request.method == 'POST': 
        num_of_party = request.form['party_size']
        notes = request.form['body']
        reservation_date = request.form['date']
        reservation_time = request.form['time']

        reservation_datetime = datetime.fromisoformat(reservation_date + " " + reservation_time)
        
        if(reservation_datetime < datetime.now()): 
            return render_template('reserve.html', user = g.user, r_id = r_id, res_name = res_name, error = True)

        reservations = g.conn.execute("SELECT COUNT(*) as c FROM reservations")
        for u in reservations:
            res_count = u['c']
        
        g.conn.execute(
            "INSERT INTO reservations (res_id, booking_datetime, reservation_datetime, is_cancelled, cancelled_datetime, party_size, special_occassion, u_id, r_id)\
                VALUES(%s, NOW(), (TO_TIMESTAMP(%s, 'YYYY-MM-DD HH24:MI:SS')), NULL, NULL, %s, %s, %s, %s)", (res_count+1, reservation_date + " " + reservation_time, num_of_party, notes, g.user['u_id'], r_id))
    
        return redirect(url_for('apl.home'))
    
    return render_template('reserve.html', user = g.user, r_id = r_id, res_name = res_name, error = False)

#Reservations: similar to home
@bp.route('/reservations')
@login_required
def reservations(): 
    reservations = g.conn.execute(
        'SELECT res.res_id, r.name, r.phone_number, res.reservation_datetime, res.is_cancelled, res.party_size, res.special_occassion\
         FROM reservations res\
         LEFT JOIN restaurants r ON res.r_id = r.r_id\
         WHERE res.u_id = %s\
         ORDER BY res.reservation_datetime ASC', g.user['u_id'])

    return render_template('reservations.html', user=g.user, reservations = reservations)

#cancel reservation
@bp.route('/<int:res_id>/cancel_reservation')
@login_required
def cancel_reservation(res_id):
    
    if request.method == 'GET': 
        g.conn.execute(
            "UPDATE reservations SET cancelled_datetime = NOW(), is_cancelled = TRUE WHERE res_id = %s", str(res_id))
        
        return redirect(url_for('apl.reservations'))

@bp.route('/recommendation')
@login_required
def recommendation():
#list of restaurants
#user can add reservation (w/ time and date)
#user can label a restaurant as visited or wishlisted

    #all restaurants that user has reviewed above 3 stars
    rev_3 = g.conn.execute(
        "SELECT *\
        FROM users u\
        LEFT JOIN reviews rev ON rev.u_id = u.u_id\
        LEFT JOIN (SELECT r.*, cui.cuisine\
        FROM restaurants r\
        LEFT JOIN ( SELECT re.r_id, STRING_AGG(c.cuisine_name, \', \') as cuisine\
        FROM restaurants re\
        LEFT JOIN is_cuisine ic ON ic.r_id = re.r_id\
        LEFT JOIN cuisines c ON ic.c_id = c.c_id\
        GROUP BY re.r_id) as cui ON r.r_id = cui.r_id) as r_info ON r_info.r_id = rev.r_id\
        WHERE u.u_id = %s AND rev.star_rating >= 3", (g.user['u_id'])
    ).fetchall()

    #check if there is actually 1 restaurants rated postively to build recommendations
    recc_flag = 'FALSE'
    if len(rev_3) >= 1:
        recc_flag = 'TRUE'
    
    #recommendation checking
    price_range = {}
    res_type = {}
    cuisine = {}

    for rev in rev_3:
        #pricerange
        price_range[rev['price_range']] = price_range.get(rev['price_range'], 0)+1

        #restaurant type
        res_type[rev['restaurant_type']] = res_type.get(rev['restaurant_type'], 0)+1

        #cuisine
        for c in rev['cuisine'].split(","):
            cuisine[c] = cuisine.get(c, 0)+1

    print(price_range)
    print(res_type)
    print(cuisine)

    #restaurant query
    restaurants = g.conn.execute(
        "SELECT r.*, a.*, cui.cuisine,\
        CASE\
            WHEN ic.r_id IS NULL THEN 'FALSE'\
            ELSE 'TRUE' END AS chain_flag\
        FROM restaurants r\
        LEFT JOIN addresses a ON r.a_id = a.a_id\
        LEFT JOIN ( SELECT re.r_id, STRING_AGG(c.cuisine_name, \', \') as cuisine\
        FROM restaurants re\
        LEFT JOIN is_cuisine ic ON ic.r_id = re.r_id\
        LEFT JOIN cuisines c ON ic.c_id = c.c_id\
        GROUP BY re.r_id) as cui\
        ON r.r_id = cui.r_id\
        LEFT JOIN is_chain ic\
        ON ic.r_id = r.r_id"
    ).fetchall()

    resto_list = []

    for r in restaurants:
        curr_score = 0
        
        #recomendation score
        curr_score += cuisine.get(r['cuisine'], 0)
        curr_score += price_range.get(r['price_range'], 0)
        curr_score += res_type.get(r['restaurant_type'], 0)

        resto_list.append((curr_score, r['name'].strip()))

    #sort the list based on recommendation score
    resto_list.sort(key = lambda x: x[0], reverse=True)

    print(resto_list)

    return render_template('recommendation.html', user=g.user, resto=resto_list, recc_flag = recc_flag)
