from flask import Flask, render_template, request, redirect, url_for, flash,jsonify,session,get_flashed_messages
import pymysql.cursors
from datetime import datetime, timedelta
import uuid
from math import radians, sin, cos, sqrt, atan2
app = Flask(__name__)
app.secret_key = 'rohithattoli'
@app.route('/')
def index():
    if 'email' in session:
        email = session['email']
        messages = get_flashed_messages(with_categories=True)
        return render_template('index.html', email=email, messages=messages)
    return render_template('index.html')

@app.route('/check')
def check():
    connection = pymysql.connect(host='localhost',
                                 user='root',
                                 password='chinthaprabha2',
                                 db='parking',
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)
    try:
        with connection.cursor() as cursor:
            # Read all records from the parking table
            sql = "SELECT * FROM parking"
            cursor.execute(sql)
            result = cursor.fetchall()
            for row in result:
                if row['slotstatus'] == 'empty':
                    row['image_url'] = 'https://thumbs.dreamstime.com/b/grey-passenger-car-top-view-white-background-isolated-c-118573471.jpg'  # URL for empty slot image
                else:
                    row['image_url'] = 'https://thumbs.dreamstime.com/b/green-cartoon-car-top-view-vector-illustration-eps-green-cartoon-car-top-view-vector-illustration-121136719.jpg'   # URL for full slot image
    finally:
        connection.close()


    return render_template('check.html', data=result)

@app.route('/nearby_slots')
def nearby_slots():
    user_lat = request.args.get('lat', type=float)
    user_lon = request.args.get('lon', type=float)

    connection = pymysql.connect(host='localhost',
                                 user='root',
                                 password='chinthaprabha2',
                                 db='parking',
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)

    try:
        with connection.cursor() as cursor:
            sql = "SELECT `slotnumber`, `latitude`, `longitude`,`slotstatus` FROM `parking`"
            cursor.execute(sql)
            parking_slots = cursor.fetchall()

            R = 6371.0
            nearby_slots = []
            for slot in parking_slots:
                lat = slot['latitude']
                lon = slot['longitude']
                status=slot['slotstatus']

                lat1 = radians(user_lat)
                lon1 = radians(user_lon)
                lat2 = radians(lat)
                lon2 = radians(lon)

                dlat = lat2 - lat1
                dlon = lon2 - lon1

                a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
                c = 2 * atan2(sqrt(a), sqrt(1 - a))

                distance = R * c * 1000  # in meters
                print(distance)
                if distance <= 15000 and (status == "empty"):  # Change the distance threshold as needed
                    nearby_slots.append({'slotnumber': slot['slotnumber'], 'latitude': lat, 'longitude': lon})
                    print(nearby_slots)
            return jsonify({'slots': nearby_slots})
            
        

    finally:
        connection.close()
    return render_template('check.html')


@app.route('/reserve', methods=['GET', 'POST'])
def reserve():
    if request.method == 'POST':
        if 'email' in session:
            email = session['email']
            name = request.form['name']
            date = request.form['date']
            start_time = request.form['time']
            duration=request.form['duration']
            if start_time:
                try:
                    # Assuming the time format is '%H:%M'
                    time_obj = datetime.strptime(start_time, '%H:%M')
                    # Adding ':00' for seconds to match MySQL's time format
                    start_time = time_obj.strftime('%H.%M')
                except ValueError:
                    # Handle invalid time format
                    pass
            else:
                # Handle empty time string
                pass
            end_time = float(start_time) + float(duration)
            integer_part = int(end_time)
            decimal_part = end_time - integer_part

            if decimal_part >= 0.6:
                integer_part += 1
                decimal_part -= 0.6

            end_time = integer_part + decimal_part

            # Save the reservation details to the database
            connection = pymysql.connect(host='localhost',
                                         user='root',
                                         password='chinthaprabha2',
                                         db='reserve',
                                         charset='utf8mb4',
                                         cursorclass=pymysql.cursors.DictCursor)
            # Initialize a list to store available slots
            available_slots = []

            # Loop through each slot table (slot1 to slot5)
            for i in range(1, 6):
                with connection.cursor() as cursor:
                    # Fetch logs that overlap with the requested time slot
                    sql = f"SELECT * FROM slot{i} WHERE NOT(date = %s AND (end_time <= %s OR start_time >= %s))"
                    cursor.execute(sql, (date, start_time, end_time))
                    logs = cursor.fetchall()

                    if not logs:
                        available_slots.append(i)
            connection.close()
            session['available_slots'] = available_slots
            # Redirect to the available_slots route
            return redirect(url_for('available_slots', name=name, time=start_time, date=date, duration=duration))
        return redirect(url_for('login'))
    return render_template('reserve.html')
        
    

            
@app.route('/available_slots', methods=['GET'])
def available_slots():
    # Assuming available_slots is a list of slot numbers
    available_slots = session.get('available_slots', [])
    name = request.args.get('name')
    time = request.args.get('time')
    date = request.args.get('date')
    duration = request.args.get('duration')
    email=session['email']
    return render_template('layout.html', available_slots=available_slots, name=name, time=time, date=date, duration=duration,email=email)

@app.route('/book_slot', methods=['POST'])
def book_slot():
    if 'email' in session:
        email = session['email']
        slot_number = request.form['slot_number']
        name = request.form['name']
        date = request.form['date']
        time = request.form['time']
        duration = request.form['duration']
        print(time)
        print(duration)
        end_time = float(time) + float(duration)
        print(end_time)
        integer_part = int(end_time)
        decimal_part = end_time - integer_part
        if decimal_part >= 0.6:
            integer_part += 1
            decimal_part -= 0.6
        end_time = integer_part + decimal_part
        print(end_time)
        #generate unique reservation_id
        reservation_uuid = str(uuid.uuid4())
    
        # Get the current timestamp
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
    
        # Concatenate UUID and timestamp to create the reservation ID
        reservation_id = f"{reservation_uuid}-{timestamp}"
        # Save the reservation details to the database
        connection = pymysql.connect(host='localhost',
                                     user='root',
                                     password='chinthaprabha2',
                                     db='reserve',
                                     charset='utf8mb4',
                                     cursorclass=pymysql.cursors.DictCursor)
        try:
            with connection.cursor() as cursor:
                sql = "INSERT INTO slot{} (email, name, date, start_time,end_time,slotno,reservation_id) VALUES (%s, %s, %s, %s,%s,%s,%s)".format(slot_number)
                cursor.execute(sql, (email, name, date, time,str(end_time),slot_number,reservation_id))
            connection.commit()
        finally:
            connection.close()

        flash('Slot booked successfully', 'success')
        return redirect(url_for('index'))
    else:
        return jsonify({'error': 'User not logged in'}), 401


@app.route('/pay')
def pay():
    return render_template('pay.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'email' in session:
        # User is already logged in, redirect to index with alert message
        flash('You are already logged in.', 'info')
        return redirect(url_for('index'))
    
    connection = pymysql.connect(host='localhost',
                             user='root',
                             password='chinthaprabha2',
                             db='user',
                             cursorclass=pymysql.cursors.DictCursor)
    if request.method == 'POST':
        name = request.form['name']
        mobile_number = request.form['mobile_number']
        email = request.form['email']
        password = request.form['password']
        branch = request.form['branch']

        # if not email.endswith('@nitdelhi.ac.in'):
        #     return render_template('signup.html', error='Please enter a valid email from nitdelhi.ac.in domain.')

        try:
            with connection.cursor() as cursor:
                # Check if email already exists in the database
                sql = "SELECT * FROM `login` WHERE `email`=%s"
                cursor.execute(sql, (email,))
                existing_user = cursor.fetchone()

                if existing_user:
                    return render_template('signup.html', error='Email already exists. Please use another email.')

                # Check if mobile number already exists in the database
                sql = "SELECT * FROM `login` WHERE `mobile_number`=%s"
                cursor.execute(sql, (mobile_number,))
                existing_mobile = cursor.fetchone()

                if existing_mobile:
                    return render_template('signup.html', error='Mobile number already exists. Please use another mobile number.')

                # Insert new user into the database
                sql = "INSERT INTO `login` (`name`, `mobile_number`, `email`, `password`,`branch`) VALUES (%s, %s, %s, %s, %s)"
                cursor.execute(sql, (name, mobile_number, email, password, branch))
                connection.commit()

                flash('You have signed up successfully! Please login.', 'success')
                return redirect(url_for('login'))

        except pymysql.Error as e:
            print("Error: %s" % e)
            return render_template('signup.html', error='An error occurred. Please try again.')

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'email' in session:
        # User is already logged in, show alert and redirect to index
        flash('You are already logged in.', 'info')
        return redirect(url_for('index'))

    connection = pymysql.connect(host='localhost',
                             user='root',
                             password='chinthaprabha2',
                             db='user',
                             cursorclass=pymysql.cursors.DictCursor)
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # if not email.endswith('@nitdelhi.ac.in'):
        #     return render_template('login.html', error='Please enter a valid email from nitdelhi.ac.in domain.')

        try:
            with connection.cursor() as cursor:
                # Check if the email and password match
                sql = "SELECT * FROM `login` WHERE `email`=%s AND `password`=%s"
                cursor.execute(sql, (email, password))
                user = cursor.fetchone()

                if user:
                    # Store the user's email in the session
                    session['email'] = email
                    flash('You have logged in successfully!', 'success')
                    return redirect(url_for('profile'))
                else:
                    return render_template('login.html', error='Incorrect email or password.')

        except pymysql.Error as e:
            print("Error: %s" % e)
            return render_template('login.html', error='An error occurred. Please try again.')

    return render_template('login.html', alert='')

@app.route('/logout')
def logout():
    if 'email' in session:
        # Remove the email from the session
        session.pop('email')
        flash('You have logged out successfully', 'success')
    else:
        flash('No user found', 'warning')

    return redirect(url_for('index'))  # Redirect to the index route


def get_user_by_email(email):
    connection = pymysql.connect(host='localhost',
                                 user='root',
                                 password='chinthaprabha2',
                                 db='user',
                                 cursorclass=pymysql.cursors.DictCursor)

    try:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM `login` WHERE `email`=%s"
            cursor.execute(sql, (email,))
            user = cursor.fetchone()
            return user
    finally:
        connection.close()

@app.route('/profile')
def profile():
    if 'email' not in session:
        return redirect(url_for('login'))

    email = session['email']
    user = get_user_by_email(email)
    reservations = get_reservations_by_email(email)

    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('login'))

    return render_template('profile.html', user=user, reservations=reservations)

def get_reservations_by_email(email):
    connection = pymysql.connect(host='localhost',
                                 user='root',
                                 password='chinthaprabha2',
                                 db='reserve',
                                 cursorclass=pymysql.cursors.DictCursor)
    try:
        with connection.cursor() as cursor:
            sql = """
            SELECT `name`, `email`, `date`, `start_time`, `end_time`, `slotno`,`reservation_id`
            FROM `slot1`
            WHERE `email`=%s
            UNION ALL
            SELECT `name`, `email`, `date`, `start_time`, `end_time`, `slotno`,`reservation_id`
            FROM `slot2`
            WHERE `email`=%s
            UNION ALL
            SELECT `name`, `email`, `date`, `start_time`, `end_time`, `slotno`,`reservation_id`
            FROM `slot3`
            WHERE `email`=%s
            UNION ALL
            SELECT `name`, `email`, `date`, `start_time`, `end_time`, `slotno`,`reservation_id`
            FROM `slot4`
            WHERE `email`=%s
            UNION ALL
            SELECT `name`, `email`, `date`, `start_time`, `end_time`, `slotno`,`reservation_id`
            FROM `slot5`
            WHERE `email`=%s
            """
            cursor.execute(sql, (email, email, email, email, email))
            reservations = cursor.fetchall()
            return reservations
    finally:
        connection.close()



@app.route('/update_profile', methods=['POST'])
def update_profile():
    connection = pymysql.connect(host='localhost',
                             user='root',
                             password='chinthaprabha2',
                             db='user',
                             cursorclass=pymysql.cursors.DictCursor)
    if 'email' not in session:
        return redirect(url_for('login'))

    email = session['email']
    user = get_user_by_email(email)

    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('login'))

    new_name = request.form['name']
    new_email = request.form['email']
    new_mobile_number = request.form['mobile_number']
    new_branch = request.form['branch']

    try:
        with connection.cursor() as cursor:
            sql = "UPDATE `login` SET `name`=%s, `email`=%s, `mobile_number`=%s, `branch`=%s WHERE `email`=%s"
            cursor.execute(sql, (new_name, new_email, new_mobile_number, new_branch, email))
            connection.commit()

            if new_email != email:
                session['email'] = new_email

            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))

    except pymysql.Error as e:
        print("Error: %s" % e)
        flash('An error occurred. Please try again.', 'error')
        return redirect(url_for('profile'))

@app.route('/cancel_reservation', methods=['POST'])
def cancel_reservation():
    if 'email' not in session:
        return redirect(url_for('login'))

    # Get reservation details from the form
    email=session['email']
    reservation_id = request.form['reservation_id']

    # Delete the reservation record from the database
    connection = pymysql.connect(host='localhost',
                                 user='root',
                                 password='chinthaprabha2',
                                 db='reserve',
                                 cursorclass=pymysql.cursors.DictCursor)

    try:
        for i in range(1,6):
            with connection.cursor() as cursor:
                sql = f"DELETE FROM `slot{i}` WHERE `reservation_id` =%s "
                cursor.execute(sql, (reservation_id))
                connection.commit()
        flash('Reservation cancelled successfully!', 'success')
    except pymysql.Error as e:
        print("Error: %s" % e)
        flash('Failed to cancel reservation.', 'error')
    finally:
        connection.close()

    return redirect(url_for('profile'))
if __name__ == '__main__':
    app.run(debug=True)