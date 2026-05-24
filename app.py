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

            session['user_id'] = user[0]

            session['role'] = user[4]

            if user[4] == 'admin':

             return redirect(
              url_for('admin_dashboard')
            )
            else:

             return redirect(
                url_for('user_dashboard')
             )

        return "Invalid Email or Password"

    return render_template('login.html')


# User Dashboard

@app.route('/user-dashboard')
def user_dashboard():

    if 'user' not in session:

        return redirect(url_for('login'))

    return render_template(

        'user_dashboard.html',

        username=session['user']
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
# Assign Donor

@app.route('/assign-donor/<int:request_id>/<donor_name>')
def assign_donor(request_id, donor_name):

    if session.get('role') != 'admin':

        return redirect(
            url_for('user_dashboard')
        )

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

    return redirect(
        url_for('request_list')
    )

 
# Blood Request

@app.route('/request-blood', methods=['GET', 'POST'])
def request_blood():

    if 'user' not in session:

        return redirect(url_for('login'))

    if request.method == 'POST':
        user_id = session['user_id']        
        patient_name = request.form['patient_name']
        blood_group = request.form['blood_group']
        city = request.form['city']
        hospital = request.form['hospital']
        contact = request.form['contact']
        urgency = request.form['urgency']

        sql = """
        INSERT INTO blood_requests
        (patient_name, blood_group, city, hospital, contact, urgency, user_id)

        VALUES (%s,%s,%s,%s,%s,%s,%s)
        """

        values = (
            
            patient_name,
            blood_group,
            city,
            hospital,
            contact,
            urgency,
            user_id
        )

        cursor.execute(sql, values)

        db.commit()

        # Find Matching Donors

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




        return render_template(

    'matching_donors.html',

    donors=matching_donors
)

    return render_template('request_blood.html')
#  Requests

@app.route('/requests')
def my_requests():

    if 'user' not in session:

        return redirect(url_for('login'))
    if session.get('role') != 'admin':
        return redirect(url_for('user_dashboard'))

    sql = """

    SELECT *

    FROM blood_requests

    WHERE user_id=%s

    ORDER BY id DESC

    """

    cursor.execute(

        sql,

        (session['user_id'],)
    )

    requests = cursor.fetchall()

    return render_template(

        'my_requests.html',

        requests=requests
    )
# Delete Request

@app.route('/delete-request/<int:id>')
def delete_request(id):

    if 'user' not in session:

        return redirect(url_for('login'))

    sql = """

    DELETE FROM blood_requests

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

    return redirect(
        url_for('my_requests')
    )

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

    return redirect(url_for('request_list')
    )

# Blood Stock

@app.route('/blood-stock')
def blood_stock():

    if 'user' not in session:

        return redirect(url_for('login'))

    cursor.execute(

        """

        SELECT *

        FROM blood_stock

        ORDER BY blood_group

        """
    )

    stock = cursor.fetchall()

    return render_template(

        'blood_stock.html',

        stock=stock
    )

# Add Blood Stock

@app.route('/add-stock', methods=['GET', 'POST'])
def add_stock():

    if session.get('role') != 'admin':

        return redirect(
            url_for('user_dashboard')
        )

    if request.method == 'POST':

        blood_group = request.form['blood_group']

        units = request.form['units']

        hospital = request.form['hospital']

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

        return redirect(
            url_for('blood_stock')
        )

    return render_template('add_stock.html')

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

    session.clear()

    return redirect(url_for('login'))


if __name__ == '__main__':

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host='0.0.0.0',
        port=port,
        debug=True
    )