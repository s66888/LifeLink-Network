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

        cursor = db.cursor(buffered=True)

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

        cursor = db.cursor(buffered=True)
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




# User Dashboard

@app.route('/user-dashboard')
def user_dashboard():

    if 'user' not in session:

        return redirect(url_for('login'))

    db = get_db_connection()

    cursor = db.cursor()

    # Emergency Requests

    cursor.execute(
        """
        SELECT *
        FROM blood_requests
        WHERE status != 'Completed'
        AND is_deleted = FALSE
        AND user_id != %s
        ORDER BY id DESC
        LIMIT 5
        """,
        (session['user_id'],)
    )

    emergency_requests = cursor.fetchall()

    # Donor Availability

    cursor.execute(
        """
        SELECT availability
        FROM donors
        WHERE user_id=%s
        """,
        (session['user_id'],)
    )

    donor = cursor.fetchone()

    availability = "Not Registered"

    if donor:

        availability = donor[0]

    cursor.close()
    db.close()

    return render_template(

        'user_dashboard.html',

        username=session['user'],

        emergency_requests=emergency_requests,

        availability=availability
    )

@app.route('/request-details/<int:id>')
def request_details(id):

    if 'user' not in session:
        return redirect(url_for('login'))

    db = get_db_connection()

    cursor = db.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT *
        FROM blood_requests
        WHERE id=%s
        """,
        (id,)
    )

    request = cursor.fetchone()

    cursor.close()
    db.close()

    return render_template(
        'request_details.html',
        request=request
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




@app.route('/add-donor', methods=['GET', 'POST'])
def add_donor():
    

    if 'user' not in session:
    
     return redirect(url_for('login'))
    
    if request.method == 'POST':
    
        fullname = request.form['fullname'].strip()
        blood_group = request.form['blood_group']
        city = request.form['city'].strip()
        contact = request.form['contact'].strip()
        availability = request.form['availability']
    
        if not contact.isdigit():
    
            return "Contact number must contain digits only."
    
        if len(contact) < 10:
    
            return "Contact number must be at least 10 digits."
    
        if len(fullname) < 3:
    
            return "Enter a valid donor name."
    
        db = get_db_connection()
    
        cursor = db.cursor(dictionary=True)
    
        # Check if user already registered as donor
    
        cursor.execute(
            """
            SELECT id
            FROM donors
            WHERE user_id = %s
            """,
            (session['user_id'],)
        )
    
        existing_donor = cursor.fetchone()
    
        if existing_donor:
    
            cursor.close()
            db.close()
    
            return "You are already registered as a donor."
    
        sql = """
        INSERT INTO donors
        (
            user_id,
            fullname,
            blood_group,
            city,
            contact,
            availability
        )
        VALUES (%s,%s,%s,%s,%s,%s)
        """
    
        cursor.execute(
            sql,
            (
                session['user_id'],
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

    cursor = db.cursor(buffered=True)

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
    
        patient_name = request.form['patient_name'].strip()
        blood_group = request.form['blood_group'].strip()
        city = request.form['city'].strip()
        hospital = request.form['hospital'].strip()
        contact = request.form['contact'].strip()
        urgency = request.form['urgency'].strip()
    
        user_id = session['user_id']
    
        # Required field validation
    
        if not all([
            patient_name,
            blood_group,
            city,
            hospital,
            contact,
            urgency
        ]):
    
            return "All fields are required."
    
        # Contact validation
    
        if not contact.isdigit():
    
            return "Contact number must contain digits only."
    
        if len(contact) < 10:
    
            return "Contact number must be at least 10 digits."
    
        # Blood group validation
    
        valid_groups = [
            'A+','A-',
            'B+','B-',
            'AB+','AB-',
            'O+','O-'
        ]
    
        if blood_group not in valid_groups:
    
            return "Invalid blood group."

        db = get_db_connection()

        cursor = db.cursor(buffered=True)

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
            AND availability='Available'
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
 
 cursor = db.cursor(dictionary=True)
 
 cursor.execute(
     """
     SELECT *
     FROM blood_requests
     WHERE user_id=%s
     AND is_deleted=FALSE
     ORDER BY id DESC
     """,
     (session['user_id'],)
 )
 
 requests = cursor.fetchall()
 
 # Get interested donors for every request
 
 for request in requests:
 
     cursor.execute(
         """
         SELECT
             d.fullname,
             d.blood_group,
             d.city,
             d.contact
         FROM accepted_requests ar
         JOIN donors d
         ON ar.donor_id = d.id
         WHERE ar.request_id=%s
         """,
         (request['id'],)
     )
 
     request['interested_donors'] = cursor.fetchall()
 
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

    cursor = db.cursor(buffered=True)

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

    cursor = db.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT *
        FROM blood_requests
        WHERE status != 'Completed'
        AND is_deleted = FALSE
        AND user_id != %s
        ORDER BY id DESC
        LIMIT 20
        """,
        (session['user_id'],)
    )

    requests = cursor.fetchall()

    # Check if current user already responded

    for request in requests:

        cursor.execute(
            """
            SELECT ar.id
            FROM accepted_requests ar
            JOIN donors d
            ON ar.donor_id = d.id
            WHERE ar.request_id=%s
            AND d.user_id=%s
            """,
            (
                request['id'],
                session['user_id']
            )
        )

        request['already_responded'] = (
            cursor.fetchone() is not None
        )

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

    cursor = db.cursor(buffered=True)

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

    cursor = db.cursor(buffered=True)

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

    cursor = db.cursor(buffered=True)

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

    cursor = db.cursor(buffered=True)

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

    cursor = db.cursor(buffered=True)

    # Get request

    cursor.execute(
        """
        SELECT user_id,status
        FROM blood_requests
        WHERE id=%s
        """,
        (id,)
    )

    request_data = cursor.fetchone()

    if not request_data:

        cursor.close()
        db.close()

        return "Request not found"

    request_owner = request_data[0]
    status = request_data[1]

    # Cannot accept own request

    if request_owner == session['user_id']:

        cursor.close()
        db.close()

        return "You cannot accept your own request"

    # Completed request check

    if status == 'Completed':

        cursor.close()
        db.close()

        return "Request already completed"

# Check donor registration and availability

    cursor.execute(
        """
        SELECT id, availability
        FROM donors
        WHERE user_id=%s
        """,
        (session['user_id'],)
    )
    
    donor = cursor.fetchone()
    
    if not donor:
    
        cursor.close()
        db.close()
    
        return redirect(url_for('add_donor'))
    
    donor_id = donor[0]
    
    availability = donor[1]
    
    if availability != "Available":
    
        cursor.close()
        db.close()
    
        return """
        You are currently marked as Not Available.
        Please update your availability first.
        """

    # Prevent duplicate acceptance

    cursor.execute(
        """
        SELECT id
        FROM accepted_requests
        WHERE request_id=%s
        AND donor_id=%s
        """,
        (
            id,
            donor_id
        )
    )

    already_exists = cursor.fetchone()

    if already_exists:

        cursor.close()
        db.close()

        return "You already responded"

    # Save response

    cursor.execute(
        """
        INSERT INTO accepted_requests
        (
            request_id,
            donor_id
        )
        VALUES
        (
            %s,
            %s
        )
        """,
        (
            id,
            donor_id
        )
    )

    db.commit()

    cursor.close()
    db.close()

    return redirect(
        url_for('emergency_requests')
    )

@app.route('/toggle-availability')
def toggle_availability():

    if 'user' not in session:

        return redirect(url_for('login'))

    db = get_db_connection()

    cursor = db.cursor()

    cursor.execute(
        """
        SELECT availability
        FROM donors
        WHERE user_id=%s
        """,
        (session['user_id'],)
    )

    donor = cursor.fetchone()

    if donor:

        new_status = (
            'Not Available'
            if donor[0] == 'Available'
            else 'Available'
        )

        cursor.execute(
            """
            UPDATE donors
            SET availability=%s
            WHERE user_id=%s
            """,
            (
                new_status,
                session['user_id']
            )
        )

        db.commit()

    cursor.close()
    db.close()

    return redirect(url_for('user_dashboard'))

@app.route('/blood-stock')
def blood_stock():

    if session.get('role') != 'admin':

        return "Access Denied"

    db = get_db_connection()

    cursor = db.cursor()

    cursor.execute(
        """
        SELECT *
        FROM blood_stock
        """
    )

    stocks = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(

        'blood_stock.html',

        stocks=stocks
    )

@app.route(
    '/edit-stock/<int:id>',
    methods=['GET','POST']
)
def edit_stock(id):

    if session.get('role') != 'admin':

        return "Access Denied"

    db = get_db_connection()

    cursor = db.cursor()

    if request.method == 'POST':

        units = request.form['units']

        cursor.execute(
            """
            UPDATE blood_stock
            SET units=%s
            WHERE id=%s
            """,
            (
                units,
                id
            )
        )

        db.commit()

        cursor.close()
        db.close()

        return redirect(
            url_for('blood_stock')
        )

    cursor.execute(
        """
        SELECT *
        FROM blood_stock
        WHERE id=%s
        """,
        (id,)
    )

    stock = cursor.fetchone()

    cursor.close()
    db.close()

    return render_template(

        'edit_stock.html',

        stock=stock
    )

# Analytics

@app.route('/analytics')
def analytics():

    if session.get('role') != 'admin':

        return "Access Denied"

    db = get_db_connection()

    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM donors")
    total_donors = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM blood_requests")
    total_requests = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM blood_requests
        WHERE status='Completed'
        """
    )
    completed_requests = cursor.fetchone()[0]

    cursor.close()
    db.close()

    return render_template(
        'analytics.html',
        total_users=total_users,
        total_donors=total_donors,
        total_requests=total_requests,
        completed_requests=completed_requests
    )


# Notifications

@app.route('/notifications')
def notifications():

    if 'user' not in session:

        return redirect(url_for('login'))

    db = get_db_connection()

    cursor = db.cursor(buffered=True)

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