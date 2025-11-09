# 🛠️ ERP Cell - Developer Guide

> **Complete technical documentation for development, implementation, and deployment**

> For developers, contributors, and final year project reference

---

## 📋 Table of Contents

1. [Development Setup](#-development-setup)
2. [Database Guide](#️-database-guide)
3. [API Reference](#-api-reference)
4. [Code Architecture](#️-code-architecture)
5. [Authentication & Security](#-authentication--security)
6. [Frontend Architecture](#-frontend-architecture)
7. [Testing Guide](#-testing-guide)
8. [Deployment](#-deployment)
9. [Troubleshooting](#-troubleshooting)
10. [Best Practices](#-best-practices)

---

## 🚀 Development Setup

### Prerequisites

```bash
# Check Python version (3.8+ required)
python --version

# Check MySQL version (8.0+ required)
mysql --version

# Check pip
pip --version
```

### Step 1: Clone Repository

```bash
git clone https://github.com/neverbeatenrc/ERP-cell.git
cd ERP-cell
```

### Step 2: Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Environment Variables

Create `.env` file:

```env
# Database Configuration
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=erp_database

# Flask Configuration
FLASK_SECRET_KEY=your-secret-key-change-in-production
FLASK_ENV=development
DEBUG=True

# Security
BCRYPT_LOG_ROUNDS=12
```

### Step 4: Setup MySQL

**Windows:**
```bash
# Start MySQL service
net start MySQL80
```

**macOS/Linux:**
```bash
sudo systemctl start mysql
```

### Step 5: Run Application

```bash
python app.py
```

**First run output:**
```
Tables not found. Initializing...
Executing database.sql...
Executing seed.sql...
Hashing placeholder passwords...
Found 9 users with placeholder passwords. Hashing...
  ✓ Hashed password for Aarsee (Student)
  ✓ Hashed password for Vedika (Student)
  ...
Successfully hashed 9 passwords.
Database initialized and seeded successfully.
 * Running on http://127.0.0.1:5000
```

---

## 🗄️ Database Guide

### Schema Overview

#### Tables (10)

1. **User_Credentials** - Authentication
2. **Student_Info** - Student details
3. **Faculty_Info** - Faculty details
4. **Departments** - Department management
5. **Subjects** - Course catalog
6. **Student_Results** - Marks & grades
7. **Student_Fees** - Fee records
8. **Student_Attendance** - Attendance tracking
9. **Class_Timetable** - Class schedules
10. **Library_Transaction** - Library books

### Entity-Relationship Diagram

```
Student_Info ──┬──▶ Student_Results
               ├──▶ Student_Fees
               ├──▶ Student_Attendance
               └──▶ Library_Transaction

Faculty_Info ──▶ Class_Timetable ◀── Subjects ◀── Departments

User_Credentials ──┬──▶ Student_Info (student_ref_id)
                   └──▶ Faculty_Info (faculty_ref_id)
```

### Key Table Schemas

#### 1. User_Credentials (Authentication)

```sql
CREATE TABLE User_Credentials (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,      -- Bcrypt hash
    user_role ENUM('Student','Faculty') NOT NULL,
    student_ref_id INT,                       -- FK to Student_Info
    faculty_ref_id INT,                       -- FK to Faculty_Info
    FOREIGN KEY (student_ref_id) REFERENCES Student_Info(student_id),
    FOREIGN KEY (faculty_ref_id) REFERENCES Faculty_Info(faculty_id)
);
```

#### 2. Student_Info

```sql
CREATE TABLE Student_Info (
    student_id INT PRIMARY KEY AUTO_INCREMENT,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE,
    email VARCHAR(150) UNIQUE NOT NULL,
    phone_number VARCHAR(20),
    enrollment_date DATE NOT NULL,
    gender ENUM('Male','Female','Other')
);
```

#### 3. Student_Results

```sql
CREATE TABLE Student_Results (
    result_id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    subject_id INT NOT NULL,
    exam_date DATE NOT NULL,
    theory_marks INT,                         -- 0-100
    practical_marks INT,                      -- 0-100
    credits DECIMAL(3,1) NOT NULL,
    grade ENUM('A+','A','B+','B','C+','C','D','F') NOT NULL,
    status_exam ENUM('PASS','FAIL') NOT NULL,
    FOREIGN KEY (student_id) REFERENCES Student_Info(student_id),
    FOREIGN KEY (subject_id) REFERENCES Subjects(subject_id),
    UNIQUE KEY unique_student_subject (student_id, subject_id)
);
```

### Database Conventions

#### Naming

- **Tables**: `PascalCase` (e.g., `Student_Info`)
- **Columns**: `snake_case` (e.g., `student_id`)
- **Foreign Keys**: `table_id` (e.g., `student_id`, `faculty_id`)

#### Data Types

```sql
-- IDs
student_id INT AUTO_INCREMENT PRIMARY KEY

-- Names
first_name VARCHAR(50) NOT NULL
email VARCHAR(100) UNIQUE

-- Marks
theory_marks DECIMAL(5,2)  -- e.g., 85.50

-- Dates
enrollment_date DATE
attendance_date DATE

-- Money
tuition_fee DECIMAL(10,2)  -- e.g., 60000.00

-- Status
status ENUM('Present', 'Absent')
```

### Sample Queries

**Get student with attendance:**

```sql
SELECT 
    si.student_id,
    si.first_name,
    si.last_name,
    COUNT(sa.attendance_id) as total_classes,
    SUM(CASE WHEN sa.status = 'Present' THEN 1 ELSE 0 END) as present_count
FROM Student_Info si
LEFT JOIN Student_Attendance sa ON si.student_id = sa.student_id
GROUP BY si.student_id;
```

**Get marks with grades:**

```sql
SELECT 
    s.subject_name,
    sr.theory_marks,
    sr.practical_marks,
    (sr.theory_marks + sr.practical_marks) as total,
    sr.grade
FROM Student_Results sr
JOIN Subjects s ON sr.subject_id = s.subject_id
WHERE sr.student_id = 1;
```

### Database Initialization

The application automatically:
- Creates database if missing
- Creates all tables
- Seeds sample data
- Hashes passwords

**Manual initialization:**

```bash
# Start MySQL
net start MySQL80

# Connect to MySQL
mysql -u root -p

# Run schema
mysql -u root -p < database/database.sql

# Seed data
mysql -u root -p erp_database < database/seed.sql
```

---

## 📡 API Reference

### Response Format

All APIs return JSON:

```json
{
  "success": true,
  "data": [...],
  "message": "Operation successful"
}
```

**Error Response:**

```json
{
  "success": false,
  "message": "Error description"
}
```

### Authentication Endpoints

#### POST /login

**Description:** Authenticates user and creates session

**Request:**
```json
{
  "username": "Aarsee",
  "password": "student123"
}
```

**Response (Success):**
```json
{
  "success": true,
  "user": {
    "user_role": "Student",
    "id": 1,
    "username": "Aarsee",
    "redirect_url": "/student-dashboard"
  }
}
```

#### POST /logout

**Description:** Ends user session

**Response:**
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

### Student APIs (9 endpoints)

#### GET /api/student/subjects/\<student_id\>

**Description:** Get all enrolled subjects

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "subject_id": 1,
      "subject_name": "Data Structures",
      "subject_code": "CSE201",
      "credits": 4.0,
      "faculty_name": "Dr. Emily Usher"
    }
  ]
}
```

#### GET /api/student/marks/\<student_id\>

**Description:** Get marks for all subjects

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "result_id": 1,
      "subject_name": "Data Structures",
      "exam_date": "2024-05-15",
      "theory_marks": 85,
      "practical_marks": 90,
      "credits": "4.0",
      "grade": "A+",
      "status_exam": "PASS",
      "department": "Computer Science"
    }
  ]
}
```

#### GET /api/student/attendance-detailed/\<student_id\>

**Description:** Subject-wise attendance summary

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "subject_id": 1,
      "subject_name": "Data Structures",
      "total_classes": 40,
      "classes_attended": 36,
      "attendance_percentage": 90.00
    }
  ]
}
```

#### GET /api/student/attendance-breakdown/\<student_id\>/\<subject_id\>

**Description:** Day-by-day attendance for specific subject

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "subject_name": "Data Structures",
      "attendance_date": "2024-11-09",
      "status": "Present",
      "day_name": "Saturday"
    }
  ]
}
```

### Faculty APIs (8 endpoints)

#### GET /api/faculty/dashboard/stats/\<faculty_id\>

**Description:** Dashboard statistics

**Response:**
```json
{
  "success": true,
  "total_subjects": 3,
  "total_students": 45,
  "classes_today": 2,
  "avg_attendance": 85,
  "today_classes": [
    {
      "subject_name": "Data Structures",
      "time_slot": "09:00:00 - 10:00:00",
      "location": "Room 301"
    }
  ]
}
```

#### POST /api/faculty/attendance

**Description:** Mark attendance (bulk operation)

**Request:**
```json
{
  "subject_id": 1,
  "date": "2024-11-09",
  "attendance": [
    {"student_id": 1, "present": true},
    {"student_id": 2, "present": false}
  ]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Attendance saved successfully"
}
```

#### POST /api/faculty/marks

**Description:** Enter/update marks with auto-grading

**Request:**
```json
{
  "subject_id": 1,
  "marks": [
    {
      "student_id": 1,
      "theory_marks": 85,
      "practical_marks": 90
    }
  ]
}
```

**Grading Logic:**
```python
total = theory + practical
if total >= 90:   grade = 'A+'
elif total >= 80: grade = 'A'
elif total >= 70: grade = 'B+'
elif total >= 60: grade = 'B'
elif total >= 50: grade = 'C'
else:             grade = 'F'
```

### Admin APIs (20 endpoints)

All admin endpoints require Faculty role (`@admin_required` decorator).

#### GET /api/admin/dashboard/stats

**Description:** System-wide statistics

**Response:**
```json
{
  "success": true,
  "stats": {
    "total_students": 150,
    "total_faculty": 25,
    "total_departments": 5,
    "pending_fees": 12
  }
}
```

#### POST /api/admin/students

**Description:** Add new student

**Request:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "phone_number": "1234567890",
  "enrollment_date": "2024-09-01",
  "date_of_birth": "2005-05-15",
  "gender": "Male",
  "username": "johndoe"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Student added successfully",
  "student_id": 6
}
```

**Default password:** `student123` (auto-hashed with bcrypt)

#### Complete API List

```http
# Authentication (2)
POST /login
POST /logout

# Student APIs (9)
GET  /api/student/subjects/<id>
GET  /api/student/marks/<id>
GET  /api/student/attendance-detailed/<id>
GET  /api/student/attendance-breakdown/<student_id>/<subject_id>
GET  /api/fees/<id>
GET  /api/library/<id>
GET  /api/profile/<id>/Student
GET  /api/timetable/<id>/Student
POST /api/student/change-password

# Faculty APIs (8)
GET  /api/faculty/dashboard/stats/<id>
GET  /api/faculty/classes/<id>
GET  /api/faculty/students/<subject_id>
GET  /api/faculty/all-students/<id>
POST /api/faculty/attendance
GET  /api/faculty/marks/<subject_id>
POST /api/faculty/marks
GET  /api/timetable/<id>/Faculty

# Admin APIs (20)
GET    /api/admin/dashboard/stats
GET    /api/admin/students
POST   /api/admin/students
PUT    /api/admin/students/<id>
DELETE /api/admin/students/<id>
GET    /api/admin/faculty
POST   /api/admin/faculty
PUT    /api/admin/faculty/<id>
DELETE /api/admin/faculty/<id>
GET    /api/admin/departments
POST   /api/admin/departments
PUT    /api/admin/departments/<id>
DELETE /api/admin/departments/<id>
GET    /api/admin/subjects
POST   /api/admin/subjects
PUT    /api/admin/subjects/<id>
DELETE /api/admin/subjects/<id>
GET    /api/admin/fees
```

**Total: 45 endpoints**

---

## 🏗️ Code Architecture

### Project Structure

```
ERP-cell/
├── app.py                      # Main Flask application
│   ├── Configuration
│   ├── Database initialization
│   ├── 45 API routes
│   ├── Authentication handlers
│   └── Error handlers
│
├── auth.py                     # Authentication utilities
│   ├── User class (Flask-Login)
│   ├── hash_password()
│   ├── verify_password()
│   └── create_user_from_db()
│
├── validators.py               # Input validation
│   ├── validate_username()
│   ├── validate_password()
│   ├── validate_email_address()
│   ├── validate_name()
│   └── sanitize_input()
│
├── hash_passwords.py           # Password migration script
│
├── database/
│   ├── database.sql           # Database schema (10 tables)
│   └── seed.sql              # Sample data
│
└── template/
    ├── index.html            # Login page
    ├── style.css             # Login styles
    ├── student_dashboard.html/.css/.js
    ├── faculty_dashboard.html/.css/.js
    └── admin.html/.css/.js
```

### Application Flow

```
Client (Browser)
    ↓
Flask Application (app.py)
    ↓
Authentication Layer (auth.py)
    ↓
Validation Layer (validators.py)
    ↓
Database Layer (MySQL)
    ↓
Response (JSON)
```

### Key Functions

#### Database Connection

```python
def get_db():
    """Get database connection from g object or create new."""
    if 'db' not in g:
        g.db = mysql.connector.connect(
            host=os.environ.get('DB_HOST'),
            user=os.environ.get('DB_USER'),
            password=os.environ.get('DB_PASSWORD'),
            database=os.environ.get('DB_NAME')
        )
    return g.db

@app.teardown_appcontext
def close_db(error):
    """Close database connection."""
    db = g.pop('db', None)
    if db is not None:
        db.close()
```

#### Password Hashing

```python
from auth import hash_password, verify_password

# Hash password
hashed = hash_password('student123')

# Verify password
is_valid = verify_password('student123', hashed)
```

#### Input Validation

```python
from validators import (
    validate_username,
    validate_password,
    validate_email_address,
    sanitize_input
)

# Validate
is_valid, msg = validate_username(username)
is_valid, msg = validate_password(password)

# Sanitize
clean_input = sanitize_input(user_input)
```

---

## 🔐 Authentication & Security

### Password Hashing

**Using Flask-Bcrypt:**

```python
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt(app)

# Hash password
def hash_password(password):
    return bcrypt.generate_password_hash(password).decode('utf-8')

# Verify password
def verify_password(password_hash, password):
    return bcrypt.check_password_hash(password_hash, password)
```

**Why bcrypt?**
- Salt randomization (different hash each time)
- Adaptive hashing (slow to prevent brute force)
- Industry standard

### Session Management

**Using Flask-Login:**

```python
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

login_manager = LoginManager()
login_manager.init_app(app)

# User class
class User(UserMixin):
    def __init__(self, user_id, username, user_role, ref_id):
        self.id = user_id
        self.username = username
        self.user_role = user_role
        self.ref_id = ref_id

# Login user
@app.route('/login', methods=['POST'])
def login():
    user = create_user_from_db(user_data)
    login_user(user)
    return jsonify({'success': True})

# Protected route
@app.route('/api/protected')
@login_required
def protected():
    # Only logged-in users can access
    return jsonify({'user': current_user.username})
```

### Authorization Decorators

#### `@login_required`

```python
from flask_login import login_required

@app.route('/api/profile/<int:id>')
@login_required
def get_profile(id):
    # Only logged-in users
    pass
```

#### `@admin_required`

```python
def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.user_role != 'Faculty':
            return jsonify({'success': False, 'message': 'Admin access only'}), 403
        return f(*args, **kwargs)
    return decorated_function
```

### Input Validation

**Always validate user input:**

```python
from validators import validate_username, validate_email_address, sanitize_input

# Validate
is_valid, error = validate_username(username)
if not is_valid:
    return jsonify({'success': False, 'message': error}), 400

# Sanitize
clean_input = sanitize_input(user_input)
```

**Validation functions:**
- `validate_username()` - 3-50 chars, alphanumeric + underscore/dash
- `validate_password()` - Min 6 chars
- `validate_email_address()` - Valid email format
- `validate_name()` - 2-100 chars, letters only
- `validate_marks()` - 0-100 range

### SQL Injection Prevention

**Always use parameterized queries:**

```python
# ✅ CORRECT (parameterized)
cursor.execute(
    "SELECT * FROM Student_Info WHERE student_id = %s",
    (student_id,)
)

# ❌ WRONG (string concatenation)
cursor.execute(f"SELECT * FROM Student_Info WHERE student_id = {student_id}")
```

---

## 🎨 Frontend Architecture

### File Structure

Each dashboard has 3 files:
- **HTML** - Structure
- **CSS** - Styling
- **JS** - Interactivity

```
template/
├── index.html              # Login page
├── style.css              # Login styles
│
├── student_dashboard.html
├── student_dashboard.css
├── student_dashboard.js
│
├── faculty_dashboard.html
├── faculty_dashboard.css
├── faculty_dashboard.js
│
├── admin.html
├── admin.css
└── admin.js
```

### JavaScript Patterns

#### API Call Pattern

```javascript
async function loadData(endpoint) {
    try {
        const response = await fetch(endpoint);
        const data = await response.json();
        
        if (data.success) {
            renderData(data.data);
        } else {
            showError(data.message);
        }
    } catch (error) {
        console.error('Error:', error);
        showError('Failed to load data');
    }
}
```

#### Form Submission

```javascript
form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = {
        field1: document.getElementById('field1').value,
        field2: document.getElementById('field2').value
    };
    
    const response = await fetch('/api/endpoint', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(formData)
    });
    
    const data = await response.json();
    if (data.success) {
        showSuccess(data.message);
    } else {
        showError(data.message);
    }
});
```

#### Dynamic Table Rendering

```javascript
function renderTable(data) {
    const tbody = document.getElementById('tableBody');
    tbody.innerHTML = '';
    
    data.forEach(row => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${row.id}</td>
            <td>${row.name}</td>
            <td>${row.email}</td>
            <td>
                <button onclick="editRow(${row.id})">Edit</button>
                <button onclick="deleteRow(${row.id})">Delete</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}
```

### CSS Styling

**Modern gradient design:**

```css
.card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    transition: transform 0.3s ease;
}

.card:hover {
    transform: translateY(-5px);
}
```

---

## 🧪 Testing Guide

### Manual Testing Checklist

#### Authentication
- [ ] Login with valid student credentials
- [ ] Login with valid faculty credentials
- [ ] Login with invalid credentials (should fail)
- [ ] Logout (should redirect to login)
- [ ] Access protected route without login (should redirect)

#### Student Portal
- [ ] View profile
- [ ] View subjects
- [ ] View marks
- [ ] View attendance summary
- [ ] Click subject to see attendance breakdown
- [ ] View fees (check totals display correctly)
- [ ] View library books
- [ ] View timetable

#### Faculty Dashboard
- [ ] Mark attendance (single student)
- [ ] Mark attendance (bulk - all present)
- [ ] Enter marks with auto-grading
- [ ] View student list
- [ ] View timetable
- [ ] Click view button on subject card

#### Admin Dashboard
- [ ] View dashboard statistics
- [ ] Add new student
- [ ] Edit existing student
- [ ] Delete student
- [ ] Add new faculty
- [ ] Edit faculty
- [ ] Manage departments
- [ ] Manage subjects

### Test Data

**Student IDs:** 1-5  
**Faculty IDs:** 1-4  
**Subject IDs:** 1-6  
**Department IDs:** 1-4  

### API Testing with cURL

**Login:**
```bash
curl -X POST http://127.0.0.1:5000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"Aarsee","password":"student123"}'
```

**Get Marks:**
```bash
curl http://127.0.0.1:5000/api/student/marks/1
```

**Mark Attendance:**
```bash
curl -X POST http://127.0.0.1:5000/api/faculty/attendance \
  -H "Content-Type: application/json" \
  -d '{
    "subject_id": 1,
    "date": "2024-11-09",
    "attendance": [
      {"student_id": 1, "present": true},
      {"student_id": 2, "present": false}
    ]
  }'
```

---

## 🚀 Deployment

### Local Development

```bash
# Activate virtual environment
venv\Scripts\activate

# Set environment
set FLASK_ENV=development

# Run app
python app.py
```

### Production Checklist

**Security:**
- [ ] Set `DEBUG=False`
- [ ] Change `FLASK_SECRET_KEY` to strong random value
- [ ] Update all default passwords
- [ ] Enable HTTPS
- [ ] Configure CORS properly
- [ ] Set secure cookie flags

**Database:**
- [ ] Use production database (not localhost)
- [ ] Create separate DB user (not root)
- [ ] Enable backups
- [ ] Configure connection pooling

**Performance:**
- [ ] Enable gzip compression
- [ ] Minify CSS/JS
- [ ] Use CDN for static files
- [ ] Add database indexes
- [ ] Enable caching

### Deployment Options

#### Option 1: PythonAnywhere

1. **Upload code** to PythonAnywhere
2. **Create virtual environment**
3. **Install dependencies**: `pip install -r requirements.txt`
4. **Configure MySQL** database
5. **Set environment variables**
6. **Configure WSGI** file
7. **Reload web app**

#### Option 2: Heroku

```bash
# Install Heroku CLI
heroku login

# Create app
heroku create erp-cell

# Add MySQL addon
heroku addons:create cleardb:ignite

# Set environment variables
heroku config:set FLASK_SECRET_KEY=xxx

# Deploy
git push heroku main
```

#### Option 3: VPS (AWS, DigitalOcean)

1. SSH into server
2. Install Python, MySQL, Nginx
3. Clone repository
4. Install dependencies
5. Configure Nginx as reverse proxy
6. Use gunicorn as WSGI server
7. Set up systemd service

---

## 🐛 Troubleshooting

### Common Errors

#### 1. Database Connection Error

```
mysql.connector.errors.DatabaseError: 2003: Can't connect to MySQL server
```

**Solutions:**
- Check MySQL service is running: `net start MySQL80`
- Verify credentials in `.env`
- Check port (default: 3306)
- Test connection: `mysql -u root -p`

#### 2. Import Error

```
ModuleNotFoundError: No module named 'flask'
```

**Solution:**
```bash
pip install -r requirements.txt
```

#### 3. Port Already in Use

```
OSError: [Errno 98] Address already in use
```

**Solutions:**
- Kill process: `taskkill /F /IM python.exe`
- Change port in `app.py`: `app.run(port=5001)`

#### 4. Password Hash Error

```
ValueError: Invalid salt
```

**Solution:**
- Run `python hash_passwords.py`
- Clear browser cache
- Check bcrypt installation

#### 5. Session Error

```
RuntimeError: The session is unavailable because no secret key was set
```

**Solution:**
- Check `FLASK_SECRET_KEY` in `.env`
- Restart application

### Debug Mode

Enable detailed error messages:

```python
# app.py
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
```

### Logging

Add logging for debugging:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# In routes
logger.debug(f"Received data: {data}")
logger.error(f"Error occurred: {e}")
```

---

## 📝 Best Practices

### Code Style

**Python (PEP 8):**

```python
# Function names: lowercase with underscores
def get_student_marks(student_id):
    pass

# Constants: UPPERCASE
MAX_MARKS = 100
DEFAULT_GRADE = 'F'

# Classes: PascalCase
class User:
    pass
```

**JavaScript:**

```javascript
// Variables: camelCase
const studentId = 1;

// Functions: camelCase
function loadStudentData() {}

// Constants: UPPER_CASE
const API_BASE_URL = '/api';
```

### Security

✅ **DO:**
- Hash all passwords with bcrypt
- Validate all user inputs
- Sanitize data before database queries
- Use parameterized queries
- Implement CSRF protection
- Use HTTPS in production

❌ **DON'T:**
- Store plain text passwords
- Trust user input
- Use string concatenation for SQL
- Expose database errors to users
- Hardcode credentials

### Database

✅ **DO:**
- Use prepared statements
- Close database connections
- Index frequently queried columns
- Normalize data (3NF)
- Use transactions for multi-step operations

❌ **DON'T:**
- Expose raw SQL errors
- Store duplicate data
- Use SELECT *
- Forget to close cursors

### Git Workflow

```bash
# Feature branch
git checkout -b feature/attendance-breakdown

# Commit with meaningful message
git commit -m "feat: Add day-by-day attendance breakdown"

# Push to remote
git push origin feature/attendance-breakdown

# Create pull request
```

**Commit Conventions:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `style:` Code formatting
- `refactor:` Code refactoring
- `test:` Testing
- `chore:` Maintenance

---

## 📚 Additional Resources

### Documentation
- [Flask Documentation](https://flask.palletsprojects.com/)
- [MySQL Reference](https://dev.mysql.com/doc/)
- [Flask-Login](https://flask-login.readthedocs.io/)
- [Flask-Bcrypt](https://flask-bcrypt.readthedocs.io/)

### Tools
- **MySQL Workbench** - Database management
- **Postman** - API testing
- **VS Code** - Code editor
- **Git** - Version control

### Learning
- [Python Tutorial](https://docs.python.org/3/tutorial/)
- [JavaScript MDN](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
- [SQL Tutorial](https://www.w3schools.com/sql/)

---

## 📊 Project Metrics

**Current Status:**
- **Lines of Code:** ~5,000+
- **API Endpoints:** 45
- **Database Tables:** 10
- **Test Accounts:** 9 (5 students, 4 faculty)
- **Completion:** 90%

**Features:**
- ✅ Authentication & Authorization
- ✅ Student Portal
- ✅ Faculty Dashboard
- ✅ Admin Dashboard
- ✅ Attendance System
- ✅ Marks Management
- ✅ Fee Tracking
- ✅ Library Management

---

## 📄 License

Educational Use Only - Final Year Project

---

<div align="center">

**Last Updated:** November 9, 2025 | **Version:** 0.90.0 | **Status:** In Development - Week 4 🚀

For general information, see **[README.md](README.md)**

</div>
