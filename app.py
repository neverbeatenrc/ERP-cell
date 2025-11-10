import mysql.connector
from mysql.connector import errorcode
import json
import os
from decimal import Decimal
from flask import Flask, request, jsonify, g, render_template, send_from_directory, session, redirect
from flask_cors import CORS
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from dotenv import load_dotenv
import pathlib
from auth import bcrypt, User, hash_password, verify_password, create_user_from_db
from validators import (
    validate_username, validate_password, validate_email_address,
    validate_name, sanitize_input
)

load_dotenv()

# Initialize Flask app with correct template and static folders
template_dir = pathlib.Path(__file__).parent / 'template'
static_dir = pathlib.Path(__file__).parent / 'template'  # Since style.css is in template folder
app = Flask(__name__, 
            template_folder=str(template_dir),
            static_folder=str(static_dir),
            static_url_path='')

# Set secret key for sessions (IMPORTANT: Change this in production!)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# Enable CORS for all routes
CORS(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'index'  # Redirect to login page if not authenticated

# Initialize Bcrypt
bcrypt.init_app(app)

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

# --- Flask-Login User Loader ---

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login."""
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT user_id, username, user_role, student_ref_id, faculty_ref_id FROM User_Credentials WHERE user_id = %s",
            (user_id,)
        )
        user_data = cursor.fetchone()
        cursor.close()
        
        if user_data:
            return create_user_from_db(user_data)
        return None
    except Exception as e:
        print(f"Error loading user: {e}")
        return None

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

        # 3. Hash Placeholder Passwords
        print("Hashing placeholder passwords...")
        hash_all_passwords(db)

        db.commit()
        print("Database initialized and seeded successfully.")
    except Exception as e:
        print(f"Error in init_db: {e}")
        raise


def hash_all_passwords(db):
    """
    Replaces placeholder passwords in User_Credentials with actual bcrypt hashes.
    This is necessary because bcrypt generates different hashes each time due to salt randomization,
    so we can't pre-store hashed passwords in seed.sql.
    """
    cursor = db.cursor(dictionary=True)
    
    # Default passwords
    default_passwords = {
        'student': 'student123',
        'faculty': 'faculty123'
    }
    
    try:
        # Get all users with placeholder passwords (passwords starting with 'hashed_pass_')
        cursor.execute("""
            SELECT user_id, username, password_hash, user_role 
            FROM User_Credentials 
            WHERE password_hash LIKE 'hashed_pass_%'
        """)
        users_to_hash = cursor.fetchall()
        
        if not users_to_hash:
            print("No placeholder passwords found. Skipping password hashing.")
            cursor.close()
            return
        
        print(f"Found {len(users_to_hash)} users with placeholder passwords. Hashing...")
        
        # Hash passwords for each user
        for user in users_to_hash:
            user_role = user['user_role'].lower()
            default_password = default_passwords.get(user_role)
            
            if not default_password:
                print(f"Warning: Unknown role '{user['user_role']}' for user {user['username']}. Skipping.")
                continue
            
            # Generate bcrypt hash
            hashed = hash_password(default_password)
            
            # Update the user's password
            cursor.execute("""
                UPDATE User_Credentials 
                SET password_hash = %s 
                WHERE user_id = %s
            """, (hashed, user['user_id']))
            
            print(f"  ✓ Hashed password for {user['username']} ({user['user_role']})")
        
        db.commit()
        print(f"Successfully hashed {len(users_to_hash)} passwords.")
        
    except Exception as e:
        print(f"Error hashing passwords: {e}")
        raise
    finally:
        cursor.close()

# --- Helper Functions ---

def is_admin():
    """Check if current user is admin (Faculty only)."""
    return current_user.is_authenticated and current_user.user_role == 'Faculty'


def admin_required(f):
    """Decorator to require admin (Faculty) access."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'message': 'Login required'}), 401
        if current_user.user_role != 'Faculty':
            return jsonify({'success': False, 'message': 'Admin privileges required. Only faculty can access this.'}), 403
        return f(*args, **kwargs)
    return decorated_function


# --- API Routes ---

@app.route('/', methods=['GET'])
def index():
    """Route to serve the main HTML file."""
    return render_template('index.html')


@app.route('/admin', methods=['GET'])
@login_required
def admin_dashboard():
    """Serves the admin dashboard page. Only accessible to Faculty (admins)."""
    if not is_admin():
        return jsonify({'success': False, 'message': 'Access denied. Admin privileges required.'}), 403
    return render_template('admin.html')


@app.route('/login', methods=['POST'])
def login():
    """Handles user login authentication with password verification."""
    data = request.get_json()
    username = sanitize_input(data.get('username'))
    password = data.get('password')
    
    # Validate inputs
    is_valid, error = validate_username(username)
    if not is_valid:
        return jsonify({'success': False, 'message': error}), 400
    
    is_valid, error = validate_password(password)
    if not is_valid:
        return jsonify({'success': False, 'message': error}), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        "SELECT user_id, username, password_hash, user_role, student_ref_id, faculty_ref_id FROM User_Credentials WHERE username = %s",
        (username,)
    )
    user_data = cursor.fetchone()
    cursor.close()

    if user_data and verify_password(user_data['password_hash'], password):
        # Create user object and log them in
        user = create_user_from_db(user_data)
        login_user(user)
        
        # Determine redirect URL based on role
        if user.user_role == 'Student':
            redirect_url = '/student-dashboard'
        elif user.user_role == 'Faculty':
            redirect_url = '/faculty-dashboard'
        else:
            redirect_url = '/'
        
        # Prepare response data
        user_info = {
            'user_role': user.user_role,
            'id': user.ref_id,
            'username': user.username,
            'redirect_url': redirect_url
        }
        
        return jsonify({'success': True, 'user': user_info}), 200
    else:
        return jsonify({'success': False, 'message': 'Invalid username or password.'}), 401


@app.route('/logout', methods=['POST', 'GET'])
@login_required
def logout():
    """Handles user logout."""
    logout_user()
    if request.method == 'GET':
        return redirect('/')
    return jsonify({'success': True, 'message': 'Logged out successfully'}), 200


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
            "SELECT *, department as department_name FROM Faculty_Info WHERE faculty_id = %s",
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
                   s.subject_name, s.subject_code,
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

    # Convert decimals/dates to proper types
    for row in fees:
        for key, value in list(row.items()):
            if isinstance(value, Decimal):  # Handle Decimal objects
                row[key] = float(value)
            elif isinstance(value, (bytes, bytearray)):
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


# ============================================
# ADMIN API ENDPOINTS (Week 2)
# ============================================

@app.route('/api/admin/dashboard/stats', methods=['GET'])
@admin_required
def get_admin_stats():
    """Get dashboard statistics for admin panel. Faculty only."""
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        # Total students
        cursor.execute("SELECT COUNT(*) as count FROM Student_Info")
        total_students = cursor.fetchone()['count']
        
        # Total faculty
        cursor.execute("SELECT COUNT(*) as count FROM Faculty_Info")
        total_faculty = cursor.fetchone()['count']
        
        # Total departments
        cursor.execute("SELECT COUNT(*) as count FROM Departments")
        total_departments = cursor.fetchone()['count']
        
        # Pending fees (students with balance)
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM Student_Fees 
            WHERE status = 'Pending'
        """)
        pending_fees = cursor.fetchone()['count']
        
        cursor.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_students': total_students,
                'total_faculty': total_faculty,
                'total_departments': total_departments,
                'pending_fees': pending_fees
            }
        })
    except Exception as e:
        print(f"Error getting admin stats: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/admin/students', methods=['GET'])
@admin_required
def get_all_students():
    """Get all students for admin panel. Faculty only."""
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT s.student_id, s.first_name, s.last_name, s.email, 
                   s.phone_number, s.enrollment_date, s.date_of_birth, s.gender,
                   u.username
            FROM Student_Info s
            LEFT JOIN User_Credentials u ON s.student_id = u.student_ref_id
            ORDER BY s.student_id DESC
        """)
        
        students = cursor.fetchall()
        cursor.close()
        
        # Convert dates to strings
        for student in students:
            if student.get('enrollment_date'):
                student['enrollment_date'] = str(student['enrollment_date'])
            if student.get('date_of_birth'):
                student['date_of_birth'] = str(student['date_of_birth'])
        
        return jsonify({'success': True, 'students': students})
    except Exception as e:
        print(f"Error getting students: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/admin/students', methods=['POST'])
@admin_required
def add_student():
    """Add a new student. Faculty only."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['first_name', 'last_name', 'email', 'phone_number', 
                          'enrollment_date', 'date_of_birth', 'gender', 'username']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'{field} is required'}), 400
        
        # Validate inputs
        is_valid, error = validate_name(data['first_name'], 'First name')
        if not is_valid:
            return jsonify({'success': False, 'message': error}), 400
        
        is_valid, error = validate_name(data['last_name'], 'Last name')
        if not is_valid:
            return jsonify({'success': False, 'message': error}), 400
        
        is_valid, error = validate_email_address(data['email'])
        if not is_valid:
            return jsonify({'success': False, 'message': error}), 400
        
        is_valid, error = validate_username(data['username'])
        if not is_valid:
            return jsonify({'success': False, 'message': error}), 400
        
        db = get_db()
        cursor = db.cursor()
        
        # Insert student
        cursor.execute("""
            INSERT INTO Student_Info 
            (first_name, last_name, date_of_birth, email, phone_number, enrollment_date, gender)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            sanitize_input(data['first_name']),
            sanitize_input(data['last_name']),
            data['date_of_birth'],
            sanitize_input(data['email']),
            sanitize_input(data['phone_number']),
            data['enrollment_date'],
            data['gender']
        ))
        
        student_id = cursor.lastrowid
        
        # Create user credentials with default password
        default_password = hash_password('student123')
        cursor.execute("""
            INSERT INTO User_Credentials (username, password_hash, user_role, student_ref_id, faculty_ref_id)
            VALUES (%s, %s, 'Student', %s, NULL)
        """, (sanitize_input(data['username']), default_password, student_id))
        
        db.commit()
        cursor.close()
        
        return jsonify({
            'success': True, 
            'message': 'Student added successfully',
            'student_id': student_id
        })
    except mysql.connector.IntegrityError as e:
        db.rollback()
        return jsonify({'success': False, 'message': 'Username or email already exists'}), 400
    except Exception as e:
        db.rollback()
        print(f"Error adding student: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/admin/students/<int:student_id>', methods=['PUT'])
@admin_required
def update_student(student_id):
    """Update student information. Faculty only."""
    try:
        data = request.get_json()
        
        db = get_db()
        cursor = db.cursor()
        
        # Update student info
        cursor.execute("""
            UPDATE Student_Info 
            SET first_name = %s, last_name = %s, date_of_birth = %s, 
                email = %s, phone_number = %s, enrollment_date = %s, gender = %s
            WHERE student_id = %s
        """, (
            sanitize_input(data['first_name']),
            sanitize_input(data['last_name']),
            data['date_of_birth'],
            sanitize_input(data['email']),
            sanitize_input(data['phone_number']),
            data['enrollment_date'],
            data['gender'],
            student_id
        ))
        
        # Update username if provided
        if data.get('username'):
            cursor.execute("""
                UPDATE User_Credentials 
                SET username = %s 
                WHERE student_ref_id = %s
            """, (sanitize_input(data['username']), student_id))
        
        db.commit()
        cursor.close()
        
        return jsonify({'success': True, 'message': 'Student updated successfully'})
    except mysql.connector.IntegrityError:
        db.rollback()
        return jsonify({'success': False, 'message': 'Username or email already exists'}), 400
    except Exception as e:
        db.rollback()
        print(f"Error updating student: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/admin/students/<int:student_id>', methods=['DELETE'])
@admin_required
def delete_student(student_id):
    """Delete a student and all related records. Faculty only."""
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Delete all related records first (foreign key constraints)
        # 1. Library transactions
        cursor.execute("DELETE FROM Library_Transaction WHERE student_id = %s", (student_id,))
        
        # 2. Student fees
        cursor.execute("DELETE FROM Student_Fees WHERE student_id = %s", (student_id,))
        
        # 3. Student attendance
        cursor.execute("DELETE FROM Student_Attendance WHERE student_id = %s", (student_id,))
        
        # 4. Student results
        cursor.execute("DELETE FROM Student_Results WHERE student_id = %s", (student_id,))
        
        # 5. User credentials
        cursor.execute("DELETE FROM User_Credentials WHERE student_ref_id = %s", (student_id,))
        
        # 6. Finally delete student
        cursor.execute("DELETE FROM Student_Info WHERE student_id = %s", (student_id,))
        
        db.commit()
        cursor.close()
        
        return jsonify({'success': True, 'message': 'Student and all related records deleted successfully'})
    except Exception as e:
        db.rollback()
        print(f"Error deleting student: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/admin/faculty', methods=['GET'])
@admin_required
def get_all_faculty():
    """Get all faculty for admin panel."""
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT f.faculty_id, f.faculty_code, f.first_name, f.last_name, 
                   f.gender, f.department, f.email, f.phone_number, f.hire_date,
                   u.username
            FROM Faculty_Info f
            LEFT JOIN User_Credentials u ON f.faculty_id = u.faculty_ref_id
            ORDER BY f.faculty_id DESC
        """)
        
        faculty = cursor.fetchall()
        cursor.close()
        
        # Convert dates to strings
        for f in faculty:
            if f.get('hire_date'):
                f['hire_date'] = str(f['hire_date'])
        
        return jsonify({'success': True, 'faculty': faculty})
    except Exception as e:
        print(f"Error getting faculty: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/admin/faculty', methods=['POST'])
@admin_required
def add_faculty():
    """Add a new faculty member."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['faculty_code', 'first_name', 'last_name', 'gender', 
                          'department', 'email', 'phone_number', 'hire_date', 'username']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'{field} is required'}), 400
        
        db = get_db()
        cursor = db.cursor()
        
        # Insert faculty
        cursor.execute("""
            INSERT INTO Faculty_Info 
            (faculty_code, first_name, last_name, gender, department, email, phone_number, hire_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            sanitize_input(data['faculty_code']),
            sanitize_input(data['first_name']),
            sanitize_input(data['last_name']),
            data['gender'],
            sanitize_input(data['department']),
            sanitize_input(data['email']),
            sanitize_input(data['phone_number']),
            data['hire_date']
        ))
        
        faculty_id = cursor.lastrowid
        
        # Create user credentials with default password
        default_password = hash_password('faculty123')
        cursor.execute("""
            INSERT INTO User_Credentials (username, password_hash, user_role, student_ref_id, faculty_ref_id)
            VALUES (%s, %s, 'Faculty', NULL, %s)
        """, (sanitize_input(data['username']), default_password, faculty_id))
        
        db.commit()
        cursor.close()
        
        return jsonify({
            'success': True, 
            'message': 'Faculty added successfully',
            'faculty_id': faculty_id
        })
    except mysql.connector.IntegrityError:
        db.rollback()
        return jsonify({'success': False, 'message': 'Faculty code or username already exists'}), 400
    except Exception as e:
        db.rollback()
        print(f"Error adding faculty: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/admin/faculty/<int:faculty_id>', methods=['PUT'])
@admin_required
def update_faculty(faculty_id):
    """Update faculty information."""
    try:
        data = request.get_json()
        
        db = get_db()
        cursor = db.cursor()
        
        # Update faculty info
        cursor.execute("""
            UPDATE Faculty_Info 
            SET faculty_code = %s, first_name = %s, last_name = %s, 
                gender = %s, department = %s, email = %s, 
                phone_number = %s, hire_date = %s
            WHERE faculty_id = %s
        """, (
            sanitize_input(data['faculty_code']),
            sanitize_input(data['first_name']),
            sanitize_input(data['last_name']),
            data['gender'],
            sanitize_input(data['department']),
            sanitize_input(data['email']),
            sanitize_input(data['phone_number']),
            data['hire_date'],
            faculty_id
        ))
        
        # Update username if provided
        if data.get('username'):
            cursor.execute("""
                UPDATE User_Credentials 
                SET username = %s 
                WHERE faculty_ref_id = %s
            """, (sanitize_input(data['username']), faculty_id))
        
        db.commit()
        cursor.close()
        
        return jsonify({'success': True, 'message': 'Faculty updated successfully'})
    except mysql.connector.IntegrityError:
        db.rollback()
        return jsonify({'success': False, 'message': 'Faculty code or username already exists'}), 400
    except Exception as e:
        db.rollback()
        print(f"Error updating faculty: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/admin/faculty/<int:faculty_id>', methods=['DELETE'])
@admin_required
def delete_faculty(faculty_id):
    """Delete a faculty member."""
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Delete user credentials first
        cursor.execute("DELETE FROM User_Credentials WHERE faculty_ref_id = %s", (faculty_id,))
        
        # Delete faculty
        cursor.execute("DELETE FROM Faculty_Info WHERE faculty_id = %s", (faculty_id,))
        
        db.commit()
        cursor.close()
        
        return jsonify({'success': True, 'message': 'Faculty deleted successfully'})
    except Exception as e:
        db.rollback()
        print(f"Error deleting faculty: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/admin/departments', methods=['GET'])
@admin_required
def get_all_departments():
    """Get all departments with student/faculty counts."""
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT d.dept_id, d.dept_name,
                   (SELECT COUNT(*) FROM Student_Results sr 
                    WHERE sr.department = d.dept_id) as student_count,
                   (SELECT COUNT(*) FROM Faculty_Info f 
                    WHERE f.department = d.dept_name) as faculty_count
            FROM Departments d
            ORDER BY d.dept_id
        """)
        
        departments = cursor.fetchall()
        cursor.close()
        
        return jsonify({'success': True, 'departments': departments})
    except Exception as e:
        print(f"Error getting departments: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/admin/departments', methods=['POST'])
@admin_required
def add_department():
    """Add a new department."""
    try:
        data = request.get_json()
        
        if not data.get('dept_name'):
            return jsonify({'success': False, 'message': 'Department name is required'}), 400
        
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("""
            INSERT INTO Departments (dept_name)
            VALUES (%s)
        """, (sanitize_input(data['dept_name']),))
        
        dept_id = cursor.lastrowid
        db.commit()
        cursor.close()
        
        return jsonify({
            'success': True, 
            'message': 'Department added successfully',
            'dept_id': dept_id
        })
    except mysql.connector.IntegrityError:
        db.rollback()
        return jsonify({'success': False, 'message': 'Department already exists'}), 400
    except Exception as e:
        db.rollback()
        print(f"Error adding department: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/admin/departments/<int:dept_id>', methods=['PUT'])
@admin_required
def update_department(dept_id):
    """Update department information."""
    try:
        data = request.get_json()
        
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("""
            UPDATE Departments 
            SET dept_name = %s
            WHERE dept_id = %s
        """, (sanitize_input(data['dept_name']), dept_id))
        
        db.commit()
        cursor.close()
        
        return jsonify({'success': True, 'message': 'Department updated successfully'})
    except Exception as e:
        db.rollback()
        print(f"Error updating department: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/admin/departments/<int:dept_id>', methods=['DELETE'])
@admin_required
def delete_department(dept_id):
    """Delete a department."""
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("DELETE FROM Departments WHERE dept_id = %s", (dept_id,))
        
        db.commit()
        cursor.close()
        
        return jsonify({'success': True, 'message': 'Department deleted successfully'})
    except Exception as e:
        db.rollback()
        print(f"Error deleting department: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/admin/subjects', methods=['GET'])
@admin_required
def get_all_subjects():
    """Get all subjects/courses."""
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT s.subject_id, s.subject_code, s.subject_name, s.credits, 
                   s.dept_id, d.dept_name
            FROM Subjects s
            LEFT JOIN Departments d ON s.dept_id = d.dept_id
            ORDER BY s.subject_code
        """)
        
        subjects = cursor.fetchall()
        cursor.close()
        
        return jsonify({'success': True, 'subjects': subjects})
    except Exception as e:
        print(f"Error getting subjects: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/admin/subjects', methods=['POST'])
@admin_required
def add_subject():
    """Add a new subject/course."""
    try:
        data = request.get_json()
        
        required_fields = ['subject_code', 'subject_name', 'credits', 'dept_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'{field} is required'}), 400
        
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("""
            INSERT INTO Subjects (subject_code, subject_name, credits, dept_id)
            VALUES (%s, %s, %s, %s)
        """, (
            sanitize_input(data['subject_code']),
            sanitize_input(data['subject_name']),
            data['credits'],
            data['dept_id']
        ))
        
        subject_id = cursor.lastrowid
        db.commit()
        cursor.close()
        
        return jsonify({
            'success': True, 
            'message': 'Subject added successfully',
            'subject_id': subject_id
        })
    except mysql.connector.IntegrityError:
        db.rollback()
        return jsonify({'success': False, 'message': 'Subject code already exists'}), 400
    except Exception as e:
        db.rollback()
        print(f"Error adding subject: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/admin/subjects/<int:subject_id>', methods=['PUT'])
@admin_required
def update_subject(subject_id):
    """Update subject information."""
    try:
        data = request.get_json()
        
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("""
            UPDATE Subjects 
            SET subject_code = %s, subject_name = %s, credits = %s, dept_id = %s
            WHERE subject_id = %s
        """, (
            sanitize_input(data['subject_code']),
            sanitize_input(data['subject_name']),
            data['credits'],
            data['dept_id'],
            subject_id
        ))
        
        db.commit()
        cursor.close()
        
        return jsonify({'success': True, 'message': 'Subject updated successfully'})
    except Exception as e:
        db.rollback()
        print(f"Error updating subject: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/admin/subjects/<int:subject_id>', methods=['DELETE'])
@admin_required
def delete_subject(subject_id):
    """Delete a subject."""
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("DELETE FROM Subjects WHERE subject_id = %s", (subject_id,))
        
        db.commit()
        cursor.close()
        
        return jsonify({'success': True, 'message': 'Subject deleted successfully'})
    except Exception as e:
        db.rollback()
        print(f"Error deleting subject: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/admin/fees', methods=['GET'])
@admin_required
def get_all_fees():
    """Get all fee records with student names."""
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT f.fee_id, f.student_id, f.department,
                   f.tuition_fee, f.library_fee, f.lab_fee, f.exam_fee, 
                   f.hostel_fee, f.other_charges, f.total_fee, f.status,
                   CONCAT(s.first_name, ' ', s.last_name) as student_name
            FROM Student_Fees f
            JOIN Student_Info s ON f.student_id = s.student_id
            ORDER BY f.student_id
        """)
        
        fees = cursor.fetchall()
        cursor.close()
        
        # Convert Decimal to float for JSON serialization
        for fee in fees:
            fee['tuition_fee'] = float(fee['tuition_fee'])
            fee['library_fee'] = float(fee['library_fee'])
            fee['lab_fee'] = float(fee['lab_fee'])
            fee['exam_fee'] = float(fee['exam_fee'])
            fee['hostel_fee'] = float(fee['hostel_fee'])
            fee['other_charges'] = float(fee['other_charges'])
            fee['total_fee'] = float(fee['total_fee'])
        
        return jsonify({'success': True, 'fees': fees})
    except Exception as e:
        print(f"Error getting fees: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================================================
# FACULTY DASHBOARD ENDPOINTS (Week 3)
# ============================================================================

@app.route('/faculty-dashboard')
@login_required
def faculty_dashboard_page():
    """Faculty dashboard page - Faculty only."""
    if current_user.user_role != 'Faculty':
        return jsonify({
            'success': False,
            'message': 'Faculty access required.'
        }), 403
    return render_template('faculty_dashboard.html', faculty_id=current_user.ref_id)


@app.route('/api/faculty/dashboard/stats/<int:faculty_id>', methods=['GET'])
@login_required
def get_faculty_dashboard_stats(faculty_id):
    """Get faculty dashboard statistics."""
    # Security check: ensure faculty can only access their own stats
    if current_user.user_role != 'Faculty' or current_user.ref_id != faculty_id:
        return jsonify({'success': False, 'message': 'Unauthorized access'}), 403
    
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        # Get total subjects taught by faculty
        cursor.execute("""
            SELECT COUNT(DISTINCT subject_id) as total_subjects
            FROM Class_Timetable
            WHERE faculty_id = %s
        """, (faculty_id,))
        subjects_result = cursor.fetchone()
        total_subjects = subjects_result['total_subjects'] if subjects_result else 0
        
        # Get total students taught (unique students in all classes)
        cursor.execute("""
            SELECT COUNT(DISTINCT sr.student_id) as total_students
            FROM Student_Results sr
            JOIN Class_Timetable ct ON sr.subject_id = ct.subject_id
            WHERE ct.faculty_id = %s
        """, (faculty_id,))
        students_result = cursor.fetchone()
        total_students = students_result['total_students'] if students_result else 0
        
        # Get classes today
        cursor.execute("""
            SELECT COUNT(*) as classes_today
            FROM Class_Timetable
            WHERE faculty_id = %s 
            AND day_of_week = DAYNAME(CURDATE())
        """, (faculty_id,))
        today_result = cursor.fetchone()
        classes_today = today_result['classes_today'] if today_result else 0
        
        # Get today's class schedule
        cursor.execute("""
            SELECT ct.*, s.subject_name, s.subject_code
            FROM Class_Timetable ct
            JOIN Subjects s ON ct.subject_id = s.subject_id
            WHERE ct.faculty_id = %s 
            AND ct.day_of_week = DAYNAME(CURDATE())
            ORDER BY ct.start_time
        """, (faculty_id,))
        today_classes = cursor.fetchall()
        
        # Format time slots
        for cls in today_classes:
            cls['time_slot'] = f"{cls['start_time']} - {cls['end_time']}"
            cls['start_time'] = str(cls['start_time'])
            cls['end_time'] = str(cls['end_time'])
        
        # Calculate average attendance (placeholder - will implement fully)
        avg_attendance = 85  # Default placeholder
        
        # Recent activities (placeholder)
        recent_activities = [
            {'title': 'Attendance Marked', 'description': 'CSE101 - 25 students', 'time': '2 hours ago'},
            {'title': 'Marks Entered', 'description': 'CSE102 - Mid-term exam', 'time': '1 day ago'}
        ]
        
        cursor.close()
        
        return jsonify({
            'success': True,
            'total_subjects': total_subjects,
            'total_students': total_students,
            'classes_today': classes_today,
            'avg_attendance': avg_attendance,
            'today_classes': today_classes,
            'recent_activities': recent_activities
        })
    except Exception as e:
        print(f"Error getting faculty stats: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/faculty/classes/<int:faculty_id>', methods=['GET'])
@login_required
def get_faculty_classes(faculty_id):
    """Get all classes/subjects taught by a faculty member."""
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT DISTINCT s.subject_id, s.subject_code, s.subject_name, 
                   s.credits, d.dept_name,
                   (SELECT COUNT(DISTINCT sr.student_id) 
                    FROM Student_Results sr 
                    WHERE sr.subject_id = s.subject_id) as student_count
            FROM Subjects s
            JOIN Class_Timetable ct ON s.subject_id = ct.subject_id
            LEFT JOIN Departments d ON s.dept_id = d.dept_id
            WHERE ct.faculty_id = %s
            ORDER BY s.subject_code
        """, (faculty_id,))
        
        subjects = cursor.fetchall()
        cursor.close()
        
        return jsonify({'success': True, 'subjects': subjects})
    except Exception as e:
        print(f"Error getting faculty classes: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/faculty/students/<int:subject_id>', methods=['GET'])
@login_required
def get_students_in_class(subject_id):
    """Get all students enrolled in a specific subject."""
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT DISTINCT si.student_id, 
                   si.first_name, si.last_name, si.email
            FROM Student_Info si
            JOIN Student_Results sr ON si.student_id = sr.student_id
            WHERE sr.subject_id = %s
            ORDER BY si.last_name, si.first_name
        """, (subject_id,))
        
        students = cursor.fetchall()
        cursor.close()
        
        return jsonify({'success': True, 'students': students})
    except Exception as e:
        print(f"Error getting students: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/faculty/attendance', methods=['POST'])
@login_required
def mark_attendance():
    """Mark attendance for students (bulk operation)."""
    try:
        data = request.get_json()
        subject_id = data.get('subject_id')
        date = data.get('date')
        attendance_list = data.get('attendance', [])
        
        if not subject_id or not date or not attendance_list:
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        db = get_db()
        cursor = db.cursor()
        
        # Check if attendance already exists for this date
        cursor.execute("""
            SELECT COUNT(*) as count FROM Student_Attendance
            WHERE subject_id = %s AND attendance_date = %s
        """, (subject_id, date))
        result = cursor.fetchone()
        
        if result[0] > 0:
            # Update existing attendance
            for student in attendance_list:
                cursor.execute("""
                    UPDATE Student_Attendance
                    SET status = %s
                    WHERE student_id = %s AND subject_id = %s AND attendance_date = %s
                """, (
                    'Present' if student['present'] else 'Absent',
                    student['student_id'],
                    subject_id,
                    date
                ))
        else:
            # Insert new attendance records
            for student in attendance_list:
                cursor.execute("""
                    INSERT INTO Student_Attendance 
                    (student_id, subject_id, attendance_date, status)
                    VALUES (%s, %s, %s, %s)
                """, (
                    student['student_id'],
                    subject_id,
                    date,
                    'Present' if student['present'] else 'Absent'
                ))
        
        db.commit()
        cursor.close()
        
        return jsonify({'success': True, 'message': 'Attendance saved successfully'})
    except Exception as e:
        db.rollback()
        print(f"Error marking attendance: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/faculty/marks/<int:subject_id>', methods=['GET'])
@login_required
def get_marks_for_subject(subject_id):
    """Get marks for all students in a subject."""
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT si.student_id, si.first_name, si.last_name,
                   sr.theory_marks, sr.practical_marks, sr.grade
            FROM Student_Info si
            JOIN Student_Results sr ON si.student_id = sr.student_id
            WHERE sr.subject_id = %s
            ORDER BY si.last_name, si.first_name
        """, (subject_id,))
        
        students = cursor.fetchall()
        cursor.close()
        
        return jsonify({'success': True, 'students': students})
    except Exception as e:
        print(f"Error getting marks: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/faculty/marks', methods=['POST'])
@login_required
def save_marks():
    """Save/update marks for students."""
    try:
        data = request.get_json()
        subject_id = data.get('subject_id')
        marks_list = data.get('marks', [])
        
        if not subject_id or not marks_list:
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        db = get_db()
        cursor = db.cursor()
        
        for student_marks in marks_list:
            theory = int(student_marks.get('theory_marks', 0))
            practical = int(student_marks.get('practical_marks', 0))
            total = theory + practical
            
            # Calculate grade
            if total >= 90:
                grade = 'A+'
            elif total >= 80:
                grade = 'A'
            elif total >= 70:
                grade = 'B+'
            elif total >= 60:
                grade = 'B'
            elif total >= 50:
                grade = 'C'
            else:
                grade = 'F'
            
            # Update marks in Student_Results
            cursor.execute("""
                UPDATE Student_Results
                SET theory_marks = %s, practical_marks = %s, grade = %s
                WHERE student_id = %s AND subject_id = %s
            """, (
                theory,
                practical,
                grade,
                student_marks['student_id'],
                subject_id
            ))
        
        db.commit()
        cursor.close()
        
        return jsonify({'success': True, 'message': 'Marks saved successfully'})
    except Exception as e:
        db.rollback()
        print(f"Error saving marks: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/faculty/all-students/<int:faculty_id>', methods=['GET'])
@login_required
def get_all_faculty_students(faculty_id):
    """Get all students taught by a faculty member across all subjects."""
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT DISTINCT si.student_id, 
                   si.first_name, si.last_name, si.email,
                   sr.department
            FROM Student_Info si
            JOIN Student_Results sr ON si.student_id = sr.student_id
            JOIN Class_Timetable ct ON sr.subject_id = ct.subject_id
            WHERE ct.faculty_id = %s
            ORDER BY si.last_name, si.first_name
        """, (faculty_id,))
        
        students = cursor.fetchall()
        
        # Get attendance percentage for each student (placeholder)
        for student in students:
            student['attendance_percentage'] = 85  # Placeholder
        
        cursor.close()
        
        return jsonify({'success': True, 'students': students})
    except Exception as e:
        print(f"Error getting students: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ==========================================
# STUDENT DASHBOARD APIS (WEEK 4)
# ==========================================

@app.route('/student-dashboard')
@login_required
def student_dashboard_page():
    """Serve student dashboard page."""
    if current_user.user_role != 'Student':
        return jsonify({'error': 'Access denied'}), 403
    return send_from_directory('template', 'student_dashboard.html')

@app.route('/api/current-user', methods=['GET'])
@login_required
def get_current_user():
    """Get currently logged-in user info."""
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        # Get user details based on role
        if current_user.user_role == 'Student':
            cursor.execute("""
                SELECT student_id, first_name, last_name, email
                FROM Student_Info
                WHERE student_id = %s
            """, (current_user.ref_id,))
        elif current_user.user_role == 'Faculty':
            cursor.execute("""
                SELECT faculty_id, first_name, last_name, email
                FROM Faculty_Info
                WHERE faculty_id = %s
            """, (current_user.ref_id,))
        
        user_info = cursor.fetchone()
        cursor.close()
        
        if user_info:
            return jsonify({
                'success': True,
                'user': {
                    'id': current_user.id,
                    'ref_id': current_user.ref_id,
                    'username': current_user.username,
                    'user_role': current_user.user_role,
                    'first_name': user_info.get('first_name'),
                    'last_name': user_info.get('last_name'),
                    'email': user_info.get('email')
                }
            })
        else:
            return jsonify({'success': False, 'message': 'User info not found'}), 404
            
    except Exception as e:
        print(f"Error getting current user: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/student/quick-stats/<int:student_id>', methods=['GET'])
@login_required
def get_student_quick_stats(student_id):
    """Get quick stats for student dashboard."""
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        # Total subjects
        cursor.execute("""
            SELECT COUNT(DISTINCT subject_id) as total_subjects
            FROM Student_Results
            WHERE student_id = %s
        """, (student_id,))
        subjects_count = cursor.fetchone()['total_subjects'] or 0
        
        # Overall attendance percentage
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN status = 'Present' THEN 1 END) as present,
                COUNT(*) as total
            FROM Student_Attendance
            WHERE student_id = %s
        """, (student_id,))
        attendance_data = cursor.fetchone()
        attendance_percentage = round((attendance_data['present'] / attendance_data['total'] * 100), 2) if attendance_data['total'] > 0 else 0
        
        # Pending fees
        cursor.execute("""
            SELECT 
                COALESCE(SUM(tuition_fee + library_fee + lab_fee + exam_fee + hostel_fee + other_charges), 0) as pending_fees
            FROM Student_Fees
            WHERE student_id = %s AND status = 'Pending'
        """, (student_id,))
        pending_fees = cursor.fetchone()['pending_fees'] or 0
        
        # Library books issued
        cursor.execute("""
            SELECT COUNT(*) as books_issued
            FROM Library_Transaction
            WHERE student_id = %s AND status = 'Issued'
        """, (student_id,))
        books_issued = cursor.fetchone()['books_issued'] or 0
        
        cursor.close()
        
        return jsonify({
            'success': True,
            'data': {
                'total_subjects': subjects_count,
                'attendance_percentage': attendance_percentage,
                'pending_fees': pending_fees,
                'library_books': books_issued
            }
        })
        
    except Exception as e:
        print(f"Error getting quick stats: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/student/recent-activity/<int:student_id>', methods=['GET'])
@login_required
def get_student_recent_activity(student_id):
    """Get recent activities for student."""
    try:
        activities = []
        
        # This is a simplified version - you can expand with real activity tracking
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        # Recent marks added
        cursor.execute("""
            SELECT s.subject_name, sr.theory_marks, sr.practical_marks
            FROM Student_Results sr
            JOIN Subjects s ON sr.subject_id = s.subject_id
            WHERE sr.student_id = %s AND (sr.theory_marks IS NOT NULL OR sr.practical_marks IS NOT NULL)
            ORDER BY sr.exam_date DESC
            LIMIT 3
        """, (student_id,))
        recent_marks = cursor.fetchall()
        
        for mark in recent_marks:
            theory = mark['theory_marks'] or 0
            practical = mark['practical_marks'] or 0
            total = theory + practical
            activities.append({
                'icon': 'chart-line',
                'message': f"Marks updated for {mark['subject_name']}: {total}/200"
            })
        
        # Recent attendance
        cursor.execute("""
            SELECT sa.attendance_date, sa.status
            FROM Student_Attendance sa
            WHERE sa.student_id = %s
            ORDER BY sa.attendance_date DESC
            LIMIT 2
        """, (student_id,))
        recent_attendance = cursor.fetchall()
        
        for att in recent_attendance:
            activities.append({
                'icon': 'calendar-check',
                'message': f"Attendance marked {att['status']} on {att['attendance_date']}"
            })
        
        cursor.close()
        
        return jsonify({'success': True, 'data': activities})
        
    except Exception as e:
        print(f"Error getting recent activity: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/student/subjects/<int:student_id>', methods=['GET'])
@login_required
def get_student_subjects(student_id):
    """Get all subjects enrolled by student with faculty info."""
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                s.subject_id,
                s.subject_name,
                s.subject_code,
                s.credits,
                GROUP_CONCAT(DISTINCT CONCAT(f.first_name, ' ', f.last_name) SEPARATOR ', ') as faculty_name
            FROM Subjects s
            JOIN Student_Results sr ON s.subject_id = sr.subject_id
            LEFT JOIN Class_Timetable ct ON s.subject_id = ct.subject_id
            LEFT JOIN Faculty_Info f ON ct.faculty_id = f.faculty_id
            WHERE sr.student_id = %s
            GROUP BY s.subject_id, s.subject_name, s.subject_code, s.credits
            ORDER BY s.subject_name
        """, (student_id,))
        
        subjects = cursor.fetchall()
        cursor.close()
        
        return jsonify({'success': True, 'data': subjects})
        
    except Exception as e:
        print(f"Error getting subjects: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/student/attendance-detailed/<int:student_id>', methods=['GET'])
@login_required
def get_student_attendance_detailed(student_id):
    """Get subject-wise detailed attendance for student."""
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                s.subject_id,
                s.subject_name,
                COUNT(*) as total_classes,
                SUM(CASE WHEN sa.status = 'Present' THEN 1 ELSE 0 END) as classes_attended,
                ROUND((SUM(CASE WHEN sa.status = 'Present' THEN 1 ELSE 0 END) / COUNT(*)) * 100, 2) as attendance_percentage
            FROM Student_Attendance sa
            JOIN Subjects s ON sa.subject_id = s.subject_id
            WHERE sa.student_id = %s
            GROUP BY sa.subject_id, s.subject_name
            ORDER BY s.subject_name
        """, (student_id,))
        
        attendance = cursor.fetchall()
        cursor.close()
        
        return jsonify({'success': True, 'data': attendance})
        
    except Exception as e:
        print(f"Error getting detailed attendance: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/student/attendance-breakdown/<int:student_id>/<int:subject_id>', methods=['GET'])
@login_required
def get_student_attendance_breakdown(student_id, subject_id):
    """Get day-by-day attendance breakdown for a specific subject."""
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                s.subject_name,
                sa.attendance_date,
                sa.status,
                DAYNAME(sa.attendance_date) as day_name
            FROM Student_Attendance sa
            JOIN Subjects s ON sa.subject_id = s.subject_id
            WHERE sa.student_id = %s AND sa.subject_id = %s
            ORDER BY sa.attendance_date DESC
        """, (student_id, subject_id))
        
        breakdown = cursor.fetchall()
        cursor.close()
        
        return jsonify({'success': True, 'data': breakdown})
        
    except Exception as e:
        print(f"Error getting attendance breakdown: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/student/change-password', methods=['POST'])
@login_required
def change_student_password():
    """Change student password."""
    try:
        data = request.get_json()
        student_id = data.get('student_id')
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not all([student_id, current_password, new_password]):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        # Validate new password
        is_valid, msg = validate_password(new_password)
        if not is_valid:
            return jsonify({'success': False, 'message': msg}), 400
        
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        # Get current password hash
        cursor.execute("""
            SELECT password_hash
            FROM User_Credentials
            WHERE user_id = %s
        """, (current_user.id,))
        
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        # Verify current password
        if not verify_password(current_password, user['password_hash']):
            cursor.close()
            return jsonify({'success': False, 'message': 'Current password is incorrect'}), 401
        
        # Hash new password and update
        new_password_hash = hash_password(new_password)
        cursor.execute("""
            UPDATE User_Credentials
            SET password_hash = %s
            WHERE user_id = %s
        """, (new_password_hash, current_user.id))
        
        db.commit()
        cursor.close()
        
        return jsonify({'success': True, 'message': 'Password changed successfully'})
        
    except Exception as e:
        print(f"Error changing password: {e}")
        if db:
            db.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

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