from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session
)
import os

from models.database import db, cursor

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

        sql = """
        INSERT INTO users
        (username, email, password)

        VALUES (%s, %s, %s)
        """

        values = (
            username,
            email,
            password
        )

        cursor.execute(sql, values)

        db.commit()

        return redirect(url_for('login'))

    return render_template('register.html')


# Login

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        sql = """
        SELECT * FROM users
        WHERE email=%s AND password=%s
        """

        values = (
            email,
            password
        )

        cursor.execute(sql, values)

        user = cursor.fetchone()

        if user:
            session['user'] = user[1]

            session['role'] = user[4]

            return redirect(url_for('dashboard'))

        return "Invalid Email or Password"

    return render_template('login.html')


# Dashboard

@app.route('/dashboard')
def dashboard():

    if 'user' not in session:

        return redirect(url_for('login'))

    return render_template(
        'dashboard.html',
        username=session['user']
    )

# Donor Registration

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

        sql = """
        INSERT INTO donors
        (fullname, blood_group, city, contact, availability)

        VALUES (%s, %s, %s, %s, %s)
        """

        values = (
            fullname,
            blood_group,
            city,
            contact,
            availability
        )

        cursor.execute(sql, values)

        db.commit()

        return redirect(url_for('donor_list'))

    return render_template('donor_form.html')

# Donor List + Search

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

    cursor.execute(sql, tuple(values))

    donors = cursor.fetchall()

    return render_template(
        'donor_list.html',
        donors=donors
    )

 
# Blood Request

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

        sql = """
        INSERT INTO blood_requests
        (patient_name, blood_group, city, hospital, contact, urgency)

        VALUES (%s, %s, %s, %s, %s, %s)
        """

        values = (
            patient_name,
            blood_group,
            city,
            hospital,
            contact,
            urgency
        )

        cursor.execute(sql, values)

        db.commit()
        # Create Emergency Notification

        notification = f"""

        Emergency blood request created
        for {blood_group} blood group
        in {city}.

        Hospital: {hospital}

        Urgency Level: {urgency}

        """

        cursor.execute(

           """
            INSERT INTO notifications (message)

            VALUES (%s)
            """,

             (notification,)

        )

        db.commit()




        return redirect(url_for('request_list'))

    return render_template('request_blood.html')


# Emergency Requests

@app.route('/requests')
def request_list():

    if 'user' not in session:

        return redirect(url_for('login'))

    cursor.execute(

        """
        SELECT *
        FROM blood_requests

        ORDER BY id DESC
        """
    )

    requests = cursor.fetchall()

    return render_template(

        'request_list.html',

        requests=requests
    )

# Update Request Status

@app.route('/update-status/<int:id>/<status>')
def update_status(id, status):

    if 'user' not in session:

        return redirect(url_for('login'))

    sql = """

    UPDATE blood_requests

    SET status=%s

    WHERE id=%s

    """

    cursor.execute(sql, (status, id))

    db.commit()

    return redirect(url_for('request_list'))


# Analytics Dashboard

@app.route('/admin')
def admin():

    if 'user' not in session:

        return redirect(url_for('login'))

    # Total Donors

    cursor.execute(
        "SELECT COUNT(*) FROM donors"
    )

    total_donors = cursor.fetchone()[0]

    # Available Donors

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM donors
        WHERE availability='Available'
        """
    )

    available_donors = cursor.fetchone()[0]

    # Total Blood Requests

    cursor.execute(
        "SELECT COUNT(*) FROM blood_requests"
    )

    total_requests = cursor.fetchone()[0]

    return render_template(

        'admin.html',

        total_donors=total_donors,

        available_donors=available_donors,

        total_requests=total_requests

    )

# City Analytics

@app.route('/city-analytics')
def city_analytics():

    if 'user' not in session:

        return redirect(url_for('login'))

    sql = """

    SELECT city, COUNT(*)

    FROM donors

    GROUP BY city

    ORDER BY COUNT(*) DESC

    """

    cursor.execute(sql)

    cities = cursor.fetchall()

    return render_template(

        'city_analytics.html',

        cities=cities

    )

# Notifications

@app.route('/notifications')
def notifications():

    if 'user' not in session:

        return redirect(url_for('login'))

    cursor.execute(

        """
        SELECT *
        FROM notifications

        ORDER BY created_at DESC
        """
    )

    notifications = cursor.fetchall()

    return render_template(

        'notifications.html',

        notifications=notifications
    )

# Awareness Module

@app.route('/awareness')
def awareness():

    if 'user' not in session:

        return redirect(url_for('login'))

    return render_template('awareness.html')

# Mobile App Center

@app.route('/mobile-app')
def mobile_app():

    if 'user' not in session:

        return redirect(url_for('login'))

    return render_template('mobile_app.html')

# Logout

@app.route('/logout')
def logout():

    session.pop('user', None)

    return redirect(url_for('login'))


if __name__ == '__main__':

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host='0.0.0.0',
        port=port,
        debug=True
    )