from flask import Flask, render_template, request, redirect, session, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
from functools import wraps


app = Flask(__name__)
app.secret_key = 'secretsecret'  # Replace with a secure random key
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

# Database connection
def get_db_connection():
    try:
        return mysql.connector.connect(
            host="b8vhejmhepchuaqha9qy-mysql.services.clever-cloud.com",
            user="uea8xq30wkuhcj2a",
            password="hItigiUj7AKbUpgo9HDE",
            database="b8vhejmhepchuaqha9qy",
            port=3306  # Explicitly specify the port
        )
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
        return None

# Decorator to restrict access to admin-only routes
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect('/admin/login')
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    # Redirect to the appropriate dashboard if logged in
    if 'admin_logged_in' in session and session['admin_logged_in']:
        return redirect('/admin/dashboard')
    elif 'user_id' in session:
        return redirect('/user/dashboard')
    return render_template('home.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    # Redirect logged-in admin to their dashboard
    if 'admin_logged_in' in session:
        flash("You are already logged in as Admin.", "info")
        return redirect('/admin/dashboard')

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Input validation
        if not username or not password:
            flash("Both username and password are required.", "error")
            return render_template('admin_login.html')

        # Hardcoded admin credentials
        hardcoded_username = 'admin'
        hardcoded_password = 'password123'

        if username == hardcoded_username and password == hardcoded_password:
            # Successful login
            session['admin_logged_in'] = True
            session.permanent = True  # Ensure session timeout
            flash("Welcome, Admin!", "success")
            return redirect('/admin/dashboard')
        else:
            # Invalid credentials
            flash("Invalid username or password.", "error")

    return render_template('admin_login.html')




@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/admin/events', methods=['GET', 'POST'])
@admin_required
def admin_events():
    conn = get_db_connection()
    if not conn:
        flash("Database connection error.", "error")
        return redirect('/admin/dashboard')

    cursor = conn.cursor()
    if request.method == 'POST':
        name = request.form['name']
        date = request.form['date']
        location = request.form['location']
        capacity = request.form.get('capacity', type=int)

        cursor.execute(
            "INSERT INTO events (name, date, location, capacity) VALUES (%s, %s, %s, %s)",
            (name, date, location, capacity)
        )
        conn.commit()

    cursor.execute("SELECT * FROM events")
    events = cursor.fetchall()
    conn.close()
    return render_template('admin_events.html', events=events)

@app.route('/admin/events/edit/<int:event_id>', methods=['GET', 'POST'])
@admin_required
def edit_event(event_id):
    conn = get_db_connection()
    if not conn:
        flash("Database connection error.", "error")
        return redirect('/admin/events')

    cursor = conn.cursor()
    if request.method == 'POST':
        name = request.form['name']
        date = request.form['date']
        location = request.form['location']
        capacity = request.form.get('capacity', type=int)

        cursor.execute("""
            UPDATE events
            SET name = %s, date = %s, location = %s, capacity = %s
            WHERE id = %s
        """, (name, date, location, capacity, event_id))
        conn.commit()
        flash("Event updated successfully.", "success")
        conn.close()
        return redirect('/admin/events')

    cursor.execute("SELECT id, name, date, location, capacity FROM events WHERE id = %s", (event_id,))
    event = cursor.fetchone()
    conn.close()

    if not event:
        return "Event not found.", 404

    return render_template('edit_event.html', event=event)

@app.route('/admin/events/delete/<int:event_id>', methods=['POST'])
@admin_required
def delete_event(event_id):
    conn = get_db_connection()
    if not conn:
        flash("Database connection error.", "error")
        return redirect('/admin/events')

    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM registrations WHERE event_id = %s", (event_id,))
        cursor.execute("DELETE FROM events WHERE id = %s", (event_id,))
        conn.commit()
        flash("Event deleted successfully.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error deleting event: {e}", "error")
    finally:
        conn.close()

    return redirect('/admin/events')

@app.route('/register', methods=['GET', 'POST'])
def register():
    # Redirect logged-in users to their dashboard
    if 'user_id' in session:
        flash("You are already logged in.", "info")
        return redirect('/user/dashboard')

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Validate inputs
        if not username or not password:
            flash("Both username and password are required.", "error")
            return redirect('/register')

        hashed_password = generate_password_hash(password)

        # Database connection
        conn = get_db_connection()
        if not conn:
            flash("Database connection error.", "error")
            return redirect('/register')

        cursor = conn.cursor()

        # Check if the username already exists
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            conn.close()
            flash("Username already exists. Please choose another.", "error")
            return redirect('/register')

        # Insert new user into the database
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
            conn.commit()
            flash("Registration successful! Please log in.", "success")
        except Exception as e:
            conn.rollback()
            flash(f"Error during registration: {e}", "error")
        finally:
            conn.close()

        return redirect('/login')

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    # Redirect logged-in users to their dashboard
    if 'user_id' in session:
        flash("You are already logged in.", "info")
        return redirect('/user/dashboard')

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Validate inputs
        if not username or not password:
            flash("Both username and password are required.", "error")
            return render_template('login.html')

        # Database connection
        conn = get_db_connection()
        if not conn:
            flash("Database connection error.", "error")
            return render_template('login.html')

        cursor = conn.cursor()

        try:
            # Fetch user details
            cursor.execute("SELECT id, password FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()

            if user and check_password_hash(user[1], password):
                # Successful login
                session['user_id'] = user[0]
                session.permanent = True  # Ensures session timeout
                flash("Login successful!", "success")
                return redirect('/user/dashboard')
            else:
                # Invalid credentials
                flash("Invalid username or password.", "error")
        except Exception as e:
            flash(f"Error during login: {e}", "error")
        finally:
            conn.close()

    return render_template('login.html')


@app.route('/user/dashboard')
def user_dashboard():
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/login')  # Redirect to login if the user is not logged in

    return render_template('user_dashboard.html')  # Render the user dashboard




@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect('/')

@app.route('/events')
def list_events():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events")
    events = cursor.fetchall()
    conn.close()

    return render_template('events.html', events=events)

@app.route('/register_event/<int:event_id>')
def register_event(event_id):
    # Check if the user is logged in
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/login')  # Redirect to login if user is not logged in

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        conn.start_transaction()

        # Check event capacity
        cursor.execute("SELECT capacity FROM events WHERE id = %s FOR UPDATE", (event_id,))
        event = cursor.fetchone()

        if not event:
            conn.rollback()
            return render_template('404.html'), 404

        if event[0] <= 0:
            conn.rollback()
            flash("Event is fully booked.", "error")
            return redirect('/events')

        # Check if the user is already registered
        cursor.execute("SELECT * FROM registrations WHERE user_id = %s AND event_id = %s", (user_id, event_id))
        if cursor.fetchone():
            conn.rollback()
            flash("You are already registered for this event.", "error")
            return redirect('/events')

        # Register the user for the event
        cursor.execute("UPDATE events SET capacity = capacity - 1 WHERE id = %s", (event_id,))
        cursor.execute("INSERT INTO registrations (user_id, event_id) VALUES (%s, %s)", (user_id, event_id))
        conn.commit()

        flash("Successfully registered for the event!", "success")
        return redirect('/user/my_events')
    except Exception as e:
        conn.rollback()
        flash(f"An error occurred: {e}", "error")
        return redirect('/events')
    finally:
        conn.close()
    
@app.route('/user/my_events')
def my_events():
    user_id = session.get('user_id')  # Ensure the user is logged in
    if not user_id:
        return redirect('/login')

    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch events the user is registered for
    cursor.execute("""
        SELECT e.id, e.name, e.date, e.location, e.capacity
        FROM events e
        INNER JOIN registrations r ON e.id = r.event_id
        WHERE r.user_id = %s
    """, (user_id,))
    events = cursor.fetchall()
    conn.close()

    return render_template('my_events.html', events=events)

@app.route('/user/cancel_registration/<int:event_id>', methods=['POST'])
def cancel_registration(event_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/login')  # Redirect to login if the user is not logged in

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        conn.start_transaction()  # Start a transaction

        # Delete the user's registration for the event
        cursor.execute("DELETE FROM registrations WHERE event_id = %s AND user_id = %s", (event_id, user_id))
        
        # Increase the event's capacity
        cursor.execute("UPDATE events SET capacity = capacity + 1 WHERE id = %s", (event_id,))

        conn.commit()  # Commit the transaction
        flash("Registration cancelled successfully.", "success")
    except Exception as e:
        conn.rollback()  # Roll back the transaction in case of an error
        flash(f"Error cancelling registration: {e}", "error")
    finally:
        conn.close()

    return redirect('/user/my_events')

@app.route('/admin/users')
def manage_users():
    if not session.get('admin_logged_in'):
        return redirect('/admin/login')  # Redirect if admin is not logged in

    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch all users
    cursor.execute("SELECT id, username FROM users")
    users = cursor.fetchall()
    conn.close()

    return render_template('manage_users.html', users=users)

@app.route('/admin/registrations')
def manage_registrations():
    if not session.get('admin_logged_in'):
        return redirect('/admin/login')  # Redirect if admin is not logged in

    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch all registrations with event and user details
    cursor.execute("""
        SELECT r.id, u.username, e.name
        FROM registrations r
        INNER JOIN users u ON r.user_id = u.id
        INNER JOIN events e ON r.event_id = e.id
    """)
    registrations = cursor.fetchall()
    conn.close()

    return render_template('manage_registrations.html', registrations=registrations)

@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if not session.get('admin_logged_in'):
        return redirect('/admin/login')

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Get all event IDs for the user's registrations
        cursor.execute("SELECT event_id FROM registrations WHERE user_id = %s", (user_id,))
        user_registrations = cursor.fetchall()

        # Increment capacity for each event the user was registered for
        for registration in user_registrations:
            event_id = registration[0]
            cursor.execute("UPDATE events SET capacity = capacity + 1 WHERE id = %s", (event_id,))

        # Delete the user's registrations
        cursor.execute("DELETE FROM registrations WHERE user_id = %s", (user_id,))
        
        # Delete the user
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))

        conn.commit()
        flash("User and associated registrations deleted successfully.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error deleting user: {e}", "error")
    finally:
        conn.close()

    return redirect('/admin/users')

@app.route('/admin/registrations/delete/<int:registration_id>', methods=['POST'])
def delete_registration(registration_id):
    if not session.get('admin_logged_in'):
        return redirect('/admin/login')

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Get the event ID for the registration
        cursor.execute("SELECT event_id FROM registrations WHERE id = %s", (registration_id,))
        registration = cursor.fetchone()

        if not registration:
            flash("Registration not found.", "error")
            return redirect('/admin/registrations')

        event_id = registration[0]

        # Delete the registration
        cursor.execute("DELETE FROM registrations WHERE id = %s", (registration_id,))
        
        # Increment the event's capacity
        cursor.execute("UPDATE events SET capacity = capacity + 1 WHERE id = %s", (event_id,))
        
        conn.commit()
        flash("Registration deleted successfully.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error deleting registration: {e}", "error")
    finally:
        conn.close()

    return redirect('/admin/registrations')




@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template('500.html'), 500


if __name__ == '__main__':
    app.run(debug=False)
