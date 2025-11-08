import mysql.connector
from mysql.connector import errorcode
import json
import os
from flask import Flask, request, jsonify, g, render_template, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import pathlib

load_dotenv()

# Initialize Flask app with correct template and static folders
template_dir = pathlib.Path(__file__).parent / 'template'
static_dir = pathlib.Path(__file__).parent / 'template'  # Since style.css is in template folder
app = Flask(__name__, 
            template_folder=str(template_dir),
            static_folder=str(static_dir),
            static_url_path='')

# Enable CORS for all routes
CORS(app)

# --- MySQL Database Configuration ---
# BEST PRACTICE: Use environment variables for credentials
DB_NAME = 'erp_database'
DB_CONFIG = {
    'user': os.environ.get('DB_USER', 'root'),       # Your MySQL username
    'password': os.environ.get('DB_PASSWORD', ''),   # Your MySQL password
    'host': os.environ.get('DB_HOST', 'localhost'),  # e.g., '127.0.0.1'
    'raise_on_warnings': True
}

BASE_DIR = os.path.dirname(__file__)

# --- Database Initialization Functions ---

def get_db():
    """Connects to the MySQL database."""
    db = getattr(g, '_database', None)
    if db is None:
        try:
            # Try connecting to the specific database
            db = g._database = mysql.connector.connect(database=DB_NAME, **DB_CONFIG)
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_BAD_DB_ERROR:
                # Database doesn't exist. Connect to server, create DB, then reconnect.
                print(f"Database '{DB_NAME}' does not exist. Attempting to create it.")
                server_config = DB_CONFIG.copy()
                # remove database key if present
                server_config.pop('database', None)

                try:
                    db_server = mysql.connector.connect(**server_config)
                    cursor = db_server.cursor()
                    cursor.execute(f"CREATE DATABASE {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                    print(f"Database '{DB_NAME}' created successfully.")
                    cursor.close()
                    db_server.close()

                    # Reconnect to the newly created database
                    db = g._database = mysql.connector.connect(database=DB_NAME, **DB_CONFIG)
                except mysql.connector.Error as err_create:
                    print(f"Failed to create database: {err_create}")
                    raise  # Re-raise exception to stop the app
            else:
                print(f"Error connecting to database: {err}")
                raise  # Re-raise other connection errors
    return db

@app.teardown_appcontext
def close_connection(exception):
    """Closes the database connection at the end of the request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def execute_sql_file(db, filename):
    """Executes SQL commands from a file located in the database/ folder."""
    cursor = db.cursor()
    try:
        path = os.path.join(BASE_DIR, 'database', filename)
        with open(path, 'r', encoding='utf-8') as f:
            sql_script = f.read()

        # Split script into individual statements and execute safely
        statements = [s.strip() for s in sql_script.split(';') if s.strip()]
        for statement in statements:
            try:
                cursor.execute(statement)
            except mysql.connector.Error as err:
                # Log and continue — some scripts may include statements that fail on repeat runs
                print(f"Error executing statement: {statement[:200]}...\n{err}")

        print(f"Successfully executed {filename}.")
    except Exception as e:
        print(f"Error executing SQL file {filename}: {e}")
        raise
    finally:
        cursor.close()

def init_db():
    """Initializes the database schema and seeds it if tables don't exist."""
    try:
        db = get_db()  # This will connect or create the DB

        # Check if tables are already created
        cursor = db.cursor()
        cursor.execute("SHOW TABLES LIKE 'Student_Info'")
        table_exists = cursor.fetchone()
        cursor.close()

        if table_exists:
            print("Tables already exist. Skipping initialization.")
            return

        print("Tables not found. Initializing...")

        # 1. Create Tables
        print("Executing database.sql...")
        execute_sql_file(db, 'database.sql')

        # 2. Seed Data
        print("Executing seed.sql...")
        execute_sql_file(db, 'seed.sql')

        db.commit()
        print("Database initialized and seeded successfully.")
    except Exception as e:
        print(f"Error in init_db: {e}")
        raise

# --- API Routes ---

@app.route('/', methods=['GET'])
def index():
    """Route to serve the main HTML file."""
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    """Handles user login authentication."""
    data = request.get_json()
    username = data.get('username')

    db = get_db()
    cursor = db.cursor(dictionary=True)  # Use dictionary=True for dict results

    cursor.execute(
        "SELECT user_role, student_ref_id, faculty_ref_id FROM User_Credentials WHERE username = %s",
        (username,)  # Use %s for placeholders
    )
    user = cursor.fetchone()
    cursor.close()

    if user:
        user_info = dict(user)
        if user_info['user_role'] == 'Student':
            user_info['id'] = user_info.pop('student_ref_id')
        else:
            user_info['id'] = user_info.pop('faculty_ref_id')

        if 'student_ref_id' in user_info:
            del user_info['student_ref_id']
        if 'faculty_ref_id' in user_info:
            del user_info['faculty_ref_id']

        return jsonify({'success': True, 'user': user_info}), 200
    else:
        return jsonify({'success': False, 'message': 'Invalid username or password.'}), 401


@app.route('/api/profile/<int:user_id>/<string:role>', methods=['GET'])
def get_profile(user_id, role):
    """Fetches user profile data (Student or Faculty)."""
    db = get_db()
    cursor = db.cursor(dictionary=True)

    if role == 'Student':
        cursor.execute(
            """
            SELECT s.*,
                   (SELECT department FROM Student_Fees WHERE student_id = s.student_id LIMIT 1) as department_name
            FROM Student_Info s
            WHERE s.student_id = %s
            """,
            (user_id,)
        )
    elif role == 'Faculty':
        cursor.execute(
            "SELECT * FROM Faculty_Info WHERE faculty_id = %s",
            (user_id,)
        )
    else:
        cursor.close()
        return jsonify({'message': 'Invalid role.'}), 400

    profile = cursor.fetchone()
    cursor.close()

    if profile:
        profile_dict = dict(profile)
        # Convert date/decimal objects to strings for JSON
        for key, value in profile_dict.items():
            if hasattr(value, 'isoformat'):  # Handles date/time
                profile_dict[key] = value.isoformat()
            elif isinstance(value, bytes):  # Handles other types
                profile_dict[key] = str(value)

        return jsonify({'success': True, 'data': profile_dict})
    return jsonify({'message': 'Profile not found.'}), 404


@app.route('/api/timetable/<int:user_id>/<string:role>', methods=['GET'])
def get_timetable(user_id, role):
    """Fetches class timetable based on user role."""
    db = get_db()
    cursor = db.cursor(dictionary=True)

    if role == 'Student':
        query = """
            SELECT t.day_of_week, t.start_time, t.end_time, t.location,
                   s.subject_name,
                   CONCAT(f.first_name, ' ', f.last_name) AS faculty_name
            FROM Class_Timetable t
            JOIN Subjects s ON t.subject_id = s.subject_id
            JOIN Faculty_Info f ON t.faculty_id = f.faculty_id
            WHERE t.subject_id IN (SELECT subject_id FROM Student_Results WHERE student_id = %s)
            ORDER BY FIELD(t.day_of_week, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'), t.start_time
        """
        params = (user_id,)
    elif role == 'Faculty':
        query = """
            SELECT t.day_of_week, t.start_time, t.end_time, t.location,
                   s.subject_name,
                   CONCAT(f.first_name, ' ', f.last_name) AS faculty_name
            FROM Class_Timetable t
            JOIN Subjects s ON t.subject_id = s.subject_id
            JOIN Faculty_Info f ON t.faculty_id = f.faculty_id
            WHERE t.faculty_id = %s
            ORDER BY FIELD(t.day_of_week, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'), t.start_time
        """
        params = (user_id,)
    else:
        cursor.close()
        return jsonify({'message': 'Invalid role.'}), 400

    cursor.execute(query, params)
    timetable = cursor.fetchall()  # Already a list of dicts
    cursor.close()

    # Convert time objects to strings
    for row in timetable:
        row['start_time'] = str(row['start_time'])
        row['end_time'] = str(row['end_time'])

    return jsonify({'success': True, 'data': timetable})


@app.route('/api/results/<int:student_id>', methods=['GET'])
def get_results(student_id):
    """Fetches student results."""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT result_id, subject_name, exam_date, theory_marks, practical_marks, 
               credits, grade, status_exam, department
        FROM Student_Results
        WHERE student_id = %s
        ORDER BY exam_date DESC
        """,
        (student_id,)
    )
    results = cursor.fetchall()
    cursor.close()

    # Convert dates/decimals
    for row in results:
        if row.get('exam_date'):
            row['exam_date'] = str(row['exam_date'])
        if row.get('credits') is not None:
            row['credits'] = str(row['credits'])

    return jsonify({'success': True, 'data': results})


@app.route('/api/attendance/<int:student_id>', methods=['GET'])
def get_attendance(student_id):
    """Calculates and fetches student attendance summary."""
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT T1.subject_name,
               COUNT(T2.status) AS total_classes,
               SUM(CASE WHEN T2.status = 'Present' THEN 1 ELSE 0 END) AS classes_present
        FROM Subjects T1
        JOIN Student_Attendance T2 ON T1.subject_id = T2.subject_id
        WHERE T2.student_id = %s
        GROUP BY T1.subject_name
        """,
        (student_id,)
    )

    attendance_summary = []
    for row in cursor.fetchall():
        row_dict = dict(row)
        total = row_dict['total_classes']
        present = row_dict.get('classes_present') or 0

        percentage = (present / total) * 100 if total > 0 else 0

        attendance_summary.append({
            'subject_name': row_dict['subject_name'],
            'total_classes': total,
            'classes_present': int(present),  # Ensure it's an int
            'percentage': round(percentage, 2)
        })
    cursor.close()
    return jsonify({'success': True, 'data': attendance_summary})


@app.route('/api/fees/<int:student_id>', methods=['GET'])
def get_fees(student_id):
    """Fetches student fee information."""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT *
        FROM Student_Fees
        WHERE student_id = %s
        ORDER BY status, paid_date DESC
        """,
        (student_id,)
    )
    fees = cursor.fetchall()
    cursor.close()

    # Convert decimals/dates
    for row in fees:
        for key, value in list(row.items()):
            if isinstance(value, (bytes, bytearray)):  # Handle decimals
                row[key] = value.decode('utf-8', errors='ignore')
            elif hasattr(value, 'isoformat'):  # Handle dates
                row[key] = value.isoformat()

    return jsonify({'success': True, 'data': fees})


@app.route('/api/library/<int:student_id>', methods=['GET'])
def get_library(student_id):
    """Fetches student library transactions."""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT book_title, book_author, issue_date, due_date, return_date, status
        FROM Library_Transaction
        WHERE student_id = %s
        ORDER BY issue_date DESC
        """,
        (student_id,)
    )
    transactions = cursor.fetchall()
    cursor.close()

    # Convert dates
    for row in transactions:
        if row.get('issue_date'):
            row['issue_date'] = str(row['issue_date'])
        if row.get('due_date'):
            row['due_date'] = str(row['due_date'])
        if row.get('return_date'):
            row['return_date'] = str(row['return_date'])

    return jsonify({'success': True, 'data': transactions})


@app.after_request
def add_header(response):
    """Add headers to prevent caching in development."""
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'no-store'
    return response

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    return jsonify(error=str(e)), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors."""
    return jsonify(error=str(e)), 500

if __name__ == '__main__':
    # Initialize the database within the app context
    with app.app_context():
        init_db()

    # Run the app with host specified to allow external access if needed
    app.run(debug=True, host='0.0.0.0', port=5000)