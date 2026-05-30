from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session
)

import os

from models.database import get_db_connection

app = Flask(__name__)

app.secret_key = "lifelink_secret"


# Home

@app.route('/')
def home():

    return redirect(url_for('login'))


# Register

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        db = get_db_connection()

        cursor = db.cursor()

        sql = """
        INSERT INTO users
        (username, email, password)

        VALUES (%s, %s, %s)
        """

        cursor.execute(
            sql,
            (username, email, password)
        )

        db.commit()

        cursor.close()
        db.close()

        return redirect(url_for('login'))

    return render_template('register.html')


# Login

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        db = get_db_connection()

        cursor = db.cursor()

        sql = """
        SELECT * FROM users
        WHERE email=%s AND password=%s
        """

        cursor.execute(sql, (email, password))

        user = cursor.fetchone()

        cursor.close()
        db.close()

        if user:

            session['user'] = user[1]
            session['user_id'] = user[0]
            session['role'] = user[4]

            if user[4] == 'admin':

                return redirect(
                    url_for('admin_dashboard')
                )

            return redirect(
                url_for('user_dashboard')
            )

        return "Invalid Email or Password"

    return render_template('login.html')


# Dashboard Redirect

@app.route('/dashboard')
def dashboard():

    if session.get('role') == 'admin':

        return redirect(
            url_for('admin_dashboard')
        )

    return redirect(
        url_for('user_dashboard')
    )


# User Dashboard

@app.route('/user-dashboard')
def user_dashboard():

    if 'user' not in session:

        return redirect(url_for('login'))

    db = get_db_connection()

    cursor = db.cursor()

    cursor.execute(
        """
        SELECT *
        FROM blood_requests
        WHERE status != 'Completed'
        ORDER BY id DESC
        LIMIT 5
        """
    )

    emergency_requests = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(

        'user_dashboard.html',

        username=session['user'],

        emergency_requests=emergency_requests
    )


# Admin Dashboard

@app.route('/admin-dashboard')
def admin_dashboard():

    if 'user' not in session:

        return redirect(url_for('login'))

    if session.get('role') != 'admin':

        return redirect(url_for('user_dashboard'))

    return render_template(

        'admin_dashboard.html',

        username=session['user']
    )


# Add Donor

@app.route('/add-donor', methods=['GET', 'POST'])
def add_donor():

    if 'user' not in session:

        return redirect(url_for('login'))

    if request.method == 'POST':

        fullname = request.form['fullname']
        blood_group = request.form['blood_group']
        city = request.form['city']
        contact = request.form['contact']
        availability = request.form['availability']

        db = get_db_connection()

        cursor = db.cursor()

        sql = """
        INSERT INTO donors
        (fullname, blood_group, city, contact, availability)

        VALUES (%s, %s, %s, %s, %s)
        """

        cursor.execute(
            sql,
            (
                fullname,
                blood_group,
                city,
                contact,
                availability
            )
        )

        db.commit()

        cursor.close()
        db.close()

        return redirect(url_for('donor_list'))

    return render_template('donor_form.html')


# Donor List

@app.route('/donors')
def donor_list():

    if 'user' not in session:

        return redirect(url_for('login'))

    blood_group = request.args.get('blood_group')
    city = request.args.get('city')

    sql = "SELECT * FROM donors WHERE 1=1"

    values = []

    if blood_group and blood_group != "":

        sql += " AND blood_group=%s"

        values.append(blood_group)

    if city and city != "":

        sql += " AND city LIKE %s"

        values.append(f"%{city}%")

    db = get_db_connection()

    cursor = db.cursor()

    cursor.execute(sql, tuple(values))

    donors = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        'donor_list.html',
        donors=donors
    )


# Request Blood

@app.route('/request-blood', methods=['GET', 'POST'])
def request_blood():

    if 'user' not in session:

        return redirect(url_for('login'))

    if request.method == 'POST':

        patient_name = request.form['patient_name']
        blood_group = request.form['blood_group']
        city = request.form['city']
        hospital = request.form['hospital']
        contact = request.form['contact']
        urgency = request.form['urgency']

        user_id = session['user_id']

        db = get_db_connection()

        cursor = db.cursor()

        sql = """
        INSERT INTO blood_requests
        (
            patient_name,
            blood_group,
            city,
            hospital,
            contact,
            urgency,
            user_id
        )

        VALUES (%s,%s,%s,%s,%s,%s,%s)
        """

        cursor.execute(

            sql,

            (
                patient_name,
                blood_group,
                city,
                hospital,
                contact,
                urgency,
                user_id
            )
        )

        db.commit()

        # Matching Donors

        cursor.execute(

            """
            SELECT *
            FROM donors
            WHERE blood_group=%s
            AND city=%s
            """,

            (
                blood_group,
                city
            )
        )

        matching_donors = cursor.fetchall()

        # Notifications

        notification = f"""
        Emergency blood request created
        for {blood_group} blood group in {city}.
        """

        cursor.execute(

            """
            INSERT INTO notifications (message)

            VALUES (%s)
            """,

            (notification,)
        )

        db.commit()

        cursor.close()
        db.close()

        return render_template(

            'matching_donors.html',

            donors=matching_donors
        )

    return render_template('request_blood.html')


# My Requests

@app.route('/my-requests')
def my_requests():

    if 'user' not in session:

        return redirect(url_for('login'))

    db = get_db_connection()

    cursor = db.cursor()

    sql = """
    SELECT *
    FROM blood_requests
    WHERE user_id=%s
    AND is_deleted=FALSE
    ORDER BY id DESC
    """

    cursor.execute(
        sql,
        (session['user_id'],)
    )

    requests = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(

        'my_requests.html',

        requests=requests
    )


# Delete Request

@app.route('/delete-request/<int:id>')
def delete_request(id):

    if 'user' not in session:

        return redirect(url_for('login'))

    db = get_db_connection()

    cursor = db.cursor()

    sql = """

    UPDATE blood_requests

    SET is_deleted=TRUE

    WHERE id=%s

    AND user_id=%s

    """

    cursor.execute(

        sql,

        (

            id,

            session['user_id']

        )
    )

    db.commit()

    cursor.close()
    db.close()

    return redirect(
        url_for('my_requests')
    )

# Public Emergency Requests

@app.route('/emergency-requests')
def emergency_requests():

    if 'user' not in session:

        return redirect(url_for('login'))

    db = get_db_connection()

    cursor = db.cursor()

    cursor.execute(
        """
        SELECT *
        FROM blood_requests
        ORDER BY id DESC
        LIMIT 20
        """
    )

    requests = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(

        'emergency_requests.html',

        requests=requests
    )


# Emergency Workflow

@app.route('/requests')
def request_list():

    if 'user' not in session:

        return redirect(url_for('login'))

    if session.get('role') != 'admin':

        return redirect(url_for('user_dashboard'))

    db = get_db_connection()

    cursor = db.cursor()

    cursor.execute(
        """
        SELECT *
        FROM blood_requests
        ORDER BY id DESC
        """
    )

    requests = cursor.fetchall()

    cursor.execute(
        "SELECT * FROM donors"
    )

    donors = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(

        'request_list.html',

        requests=requests,

        donors=donors
    )


# Assign Donor

@app.route('/assign-donor/<int:request_id>/<donor_name>')
def assign_donor(request_id, donor_name):

    if session.get('role') != 'admin':

        return redirect(url_for('user_dashboard'))

    db = get_db_connection()

    cursor = db.cursor()

    sql = """
    UPDATE blood_requests
    SET assigned_donor=%s,
        status='Accepted'
    WHERE id=%s
    """

    cursor.execute(
        sql,
        (
            donor_name,
            request_id
        )
    )

    db.commit()

    cursor.close()
    db.close()

    return redirect(url_for('request_list'))


# Update Status

@app.route('/update-status/<int:id>/<status>')
def update_status(id, status):

    if session.get('role') != 'admin':

        return redirect(url_for('user_dashboard'))

    db = get_db_connection()

    cursor = db.cursor()

    sql = """
    UPDATE blood_requests
    SET status=%s
    WHERE id=%s
    """

    cursor.execute(
        sql,
        (status, id)
    )

    db.commit()

    cursor.close()
    db.close()

    return redirect(url_for('request_list'))

# Mark Blood Arranged

@app.route('/blood-arranged/<int:id>')
def blood_arranged(id):

    if 'user' not in session:

        return redirect(url_for('login'))

    db = get_db_connection()

    cursor = db.cursor()

    cursor.execute(

        """

        UPDATE blood_requests

        SET status='Completed'

        WHERE id=%s

        AND user_id=%s

        """,

        (

            id,

            session['user_id']

        )
    )

    db.commit()

    cursor.close()
    db.close()

    return redirect(
        url_for('my_requests')
    )

# Accept Emergency Request

@app.route('/accept-request/<int:id>')
def accept_request(id):

    if 'user' not in session:

        return redirect(url_for('login'))

    db = get_db_connection()

    cursor = db.cursor()

    # Check request owner

    cursor.execute(

        """

        SELECT user_id

        FROM blood_requests

        WHERE id=%s

        """,

        (id,)
    )

    request_owner = cursor.fetchone()

    # Prevent accepting own request

    if request_owner[0] == session['user_id']:

        cursor.close()
        db.close()

        return "You cannot accept your own request"

    # Accept request

    cursor.execute(

        """

        UPDATE blood_requests

        SET accepted_by=%s,
            status='Pending Donor'

        WHERE id=%s

        """,

        (

            session['user'],

            id

        )
    )

    db.commit()

    cursor.close()
    db.close()

    return redirect(
        url_for('emergency_requests')
    )
# Blood Stock

@app.route('/blood-stock')
def blood_stock():

    if 'user' not in session:

        return redirect(url_for('login'))

    db = get_db_connection()

    cursor = db.cursor()

    cursor.execute(
        """
        SELECT *
        FROM blood_stock
        ORDER BY blood_group
        """
    )

    stock = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(

        'blood_stock.html',

        stock=stock
    )


# Add Blood Stock

@app.route('/add-stock', methods=['GET', 'POST'])
def add_stock():

    if session.get('role') != 'admin':

        return redirect(url_for('user_dashboard'))

    if request.method == 'POST':

        blood_group = request.form['blood_group']
        units = request.form['units']
        hospital = request.form['hospital']

        db = get_db_connection()

        cursor = db.cursor()

        sql = """
        INSERT INTO blood_stock
        (
            blood_group,
            units_available,
            hospital_name
        )

        VALUES (%s,%s,%s)
        """

        cursor.execute(
            sql,
            (
                blood_group,
                units,
                hospital
            )
        )

        db.commit()

        cursor.close()
        db.close()

        return redirect(url_for('blood_stock'))

    return render_template('add_stock.html')


# Analytics

@app.route('/admin')
def admin():

    if session.get('role') != 'admin':

        return redirect(url_for('user_dashboard'))

    db = get_db_connection()

    cursor = db.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM donors"
    )

    total_donors = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM donors
        WHERE availability='Available'
        """
    )

    available_donors = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM blood_requests"
    )

    total_requests = cursor.fetchone()[0]

    cursor.close()
    db.close()

    return render_template(

        'admin.html',

        total_donors=total_donors,

        available_donors=available_donors,

        total_requests=total_requests
    )


# Notifications

@app.route('/notifications')
def notifications():

    if 'user' not in session:

        return redirect(url_for('login'))

    db = get_db_connection()

    cursor = db.cursor()

    cursor.execute(
        """
        SELECT *
        FROM notifications
        ORDER BY created_at DESC
        """
    )

    notifications = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(

        'notifications.html',

        notifications=notifications
    )


# Awareness

@app.route('/awareness')
def awareness():

    if 'user' not in session:

        return redirect(url_for('login'))

    return render_template('awareness.html')


# Mobile App

@app.route('/mobile-app')
def mobile_app():

    if 'user' not in session:

        return redirect(url_for('login'))

    return render_template('mobile_app.html')


# Logout

@app.route('/logout')
def logout():

    session.clear()

    return redirect(url_for('login'))


if __name__ == '__main__':

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host='0.0.0.0',
        port=port,
        debug=False
    )