from flask import Flask, render_template, request, redirect
import mysql.connector

app = Flask(__name__)

# Database connection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",       
        password="kalql@12345",  
        database="event_management"
    )

@app.route('/')
def home():
    return "Welcome to the Event Management System!"

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Hardcoded admin credentials for simplicity
        if username == 'admin' and password == 'password123':
            return redirect('/admin/dashboard')
        else:
            return "Invalid username or password"

    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    return "Welcome to the Admin Dashboard!"

@app.route('/admin/events', methods=['GET', 'POST'])
def admin_events():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        # Capture form data for new event creation
        name = request.form['name']
        date = request.form['date']
        location = request.form['location']
        capacity = request.form['capacity']

        # Insert the new event into the database
        cursor.execute(
            "INSERT INTO events (name, date, location, capacity) VALUES (%s, %s, %s, %s)",
            (name, date, location, capacity)
        )
        conn.commit()
        conn.close()
        return "Event created successfully!"

    # Retrieve all events to display in the table
    cursor.execute("SELECT * FROM events")
    events = cursor.fetchall()
    conn.close()

    return render_template('admin_events.html', events=events)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if username already exists
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            conn.close()
            return "Username already exists. Please choose another."

        # Insert the new user into the database
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
        conn.commit()
        conn.close()

        return "Registration successful! You can now log in."

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if user exists and password matches
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            return f"Welcome, {username}!"
        else:
            return "Invalid username or password."

    return render_template('login.html')

@app.route('/events')
def list_events():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Retrieve all available events
    cursor.execute("SELECT * FROM events")
    events = cursor.fetchall()
    conn.close()

    return render_template('events.html', events=events)

@app.route('/register_event/<int:event_id>')
def register_event(event_id):
    # Simulate a logged-in user (for simplicity)
    user_id = 1  # Replace with actual user ID from session in real applications

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if the user has already registered for the event
    cursor.execute("SELECT * FROM registrations WHERE user_id = %s AND event_id = %s", (user_id, event_id))
    existing_registration = cursor.fetchone()

    if existing_registration:
        conn.close()
        return "You are already registered for this event."

    # Insert the registration into the database
    cursor.execute("INSERT INTO registrations (user_id, event_id) VALUES (%s, %s)", (user_id, event_id))
    conn.commit()
    conn.close()

    return "Event registration successful!"

@app.route('/my_events')
def my_events():
    # Simulate a logged-in user
    user_id = 1  # Replace with actual user ID from session in real applications

    conn = get_db_connection()
    cursor = conn.cursor()

    # Retrieve events the user has registered for
    cursor.execute("""
        SELECT e.id, e.name, e.date, e.location, e.capacity
        FROM events e
        INNER JOIN registrations r ON e.id = r.event_id
        WHERE r.user_id = %s
    """, (user_id,))
    events = cursor.fetchall()
    conn.close()

    return render_template('my_events.html', events=events)

if __name__ == '__main__':
    app.run(debug=True)
