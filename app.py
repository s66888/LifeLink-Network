from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session
)

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

# Donor List

@app.route('/donors')
def donor_list():

    if 'user' not in session:

        return redirect(url_for('login'))

    sql = """
    SELECT * FROM donors
    """

    cursor.execute(sql)

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

        return redirect(url_for('request_list'))

    return render_template('request_blood.html')


# Blood Request List

@app.route('/requests')
def request_list():

    if 'user' not in session:

        return redirect(url_for('login'))

    sql = """
    SELECT * FROM blood_requests
    """

    cursor.execute(sql)

    requests = cursor.fetchall()

    return render_template(
        'request_list.html',
        requests=requests
    )
# Logout

@app.route('/logout')
def logout():

    session.pop('user', None)

    return redirect(url_for('login'))


if __name__ == '__main__':

    app.run(
    host='0.0.0.0',
    port=5000
)