# 🎓 ERP Cell - College Management System

> **Final Year Project | CN312 Mini Project | Foxwin University**

A comprehensive web-based ERP system for colleges that enables admins, faculty, and students to manage academic, administrative, and financial activities efficiently.

[![Python 3.13](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![Flask 3.0](https://img.shields.io/badge/Flask-3.0-green.svg)](https://flask.palletsprojects.com/)
[![MySQL 8.0](https://img.shields.io/badge/MySQL-8.0-orange.svg)](https://www.mysql.com/)
[![License: MIT](https://img.shields.io/badge/License-Educational-yellow.svg)](LICENSE)

## 📋 Project Information

- **Project**: CN312 Mini Project (MO 2025)
- **Title**: ERP Cell - College Management System

---

## 🎯 Overview

ERP Cell is a modern, secure, and user-friendly college management system that streamlines academic and administrative operations. Built with Python Flask and MySQL, it provides role-based dashboards for students, faculty, and administrators.

### Key Features

- 🔐 **Secure Authentication** - Bcrypt password hashing with Flask-Login sessions
- 👥 **Role-Based Access Control** - Faculty (Admin), Student portals
- 📊 **Real-time Analytics** - Dashboard statistics and performance tracking
- 📱 **Responsive Design** - Works seamlessly on all devices
- ⚡ **Fast & Efficient** - Optimized queries and modern architecture
- 🎨 **Beautiful UI** - Modern gradient design with smooth animations

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Technology Stack](#️-technology-stack)
- [Installation](#-installation)
- [Login Credentials](#-login-credentials)
- [Database Schema](#️-database-schema)
- [API Documentation](#-api-documentation)
- [Project Status](#-project-status)
- [Troubleshooting](#-troubleshooting)
- [Support](#-support)

---

## ✨ Features

### 👨‍🎓 Student Portal

- ✅ **Personal Dashboard** - Academic overview, attendance %, fee status
- ✅ **Profile Management** - View and edit personal information
- ✅ **Marks & Grades** - Subject-wise marks with grade calculation
- ✅ **Attendance Tracking** - View attendance with **day-by-day breakdown** 🆕
- ✅ **Fee Management** - Detailed fee breakdown and payment history
- ✅ **Library Access** - Current books, transaction history
- ✅ **Timetable** - Class schedules and timings
- ✅ **Change Password** - Secure password update functionality

### 👨‍🏫 Faculty Portal

- ✅ **Faculty Dashboard** - Today's classes, student statistics
- ✅ **Attendance Marking** - Bulk attendance with date selection
- ✅ **Marks Entry** - Enter theory/practical marks with auto-grading
- ✅ **Student Management** - View all students taught
- ✅ **Timetable View** - Personal class schedule
- ✅ **Profile Access** - View personal information

### 👨‍💼 Admin Dashboard (Faculty Only)

- ✅ **System Analytics** - Total students, faculty, departments
- ✅ **Student Management** - Complete CRUD operations
- ✅ **Faculty Management** - Add, edit, delete faculty members
- ✅ **Department Management** - Manage departments and courses
- ✅ **Subject Management** - Course catalog administration
- ✅ **Fee Monitoring** - View all fee records and payment status
- ✅ **Reports** - Generate system-wide reports

### Upcoming Features 🚧

- ⏳ Notification System (Week 4)
- ⏳ Performance Reports (Week 4)
- ⏳ Analytics Dashboard (Week 4)
- ⏳ Email Notifications (Week 4)


---

## 🛠️ Technology Stack

### Backend

- **Python 3.13** - Core programming language
- **Flask 3.0** - Web framework
- **MySQL 8.0** - Relational database
- **Flask-Login 0.6.3** - Session management
- **Flask-Bcrypt 1.0.1** - Password hashing
- **Flask-CORS 4.0.0** - Cross-origin requests
- **Flask-WTF 1.2.2** - Form validation

### Frontend

- **HTML5** - Structure
- **CSS3** - Styling with modern gradients
- **JavaScript ES6+** - Interactivity
- **Font Awesome 6.5.0** - Icons

### Database

- **10 Tables**: Students, Faculty, Users, Departments, Subjects, Results, Fees, Attendance, Timetable, Library
- **Normalized Design**: 3NF compliance
- **Foreign Keys**: Relational integrity

---

## 📥 Installation

### Prerequisites

- Python 3.8 or higher
- MySQL Server 8.0 or higher
- pip (Python package manager)

### Step 1: Clone Repository

```bash
git clone https://github.com/neverbeatenrc/ERP-cell.git
cd ERP-cell
```

### Step 2: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Set Up MySQL

1. Install MySQL Server (see `MYSQL_SETUP.md` for detailed instructions)
2. Start MySQL service:

   ```bash
   # Windows
   net start MySQL80
   
   # Or use Services app (services.msc)
   ```

### Step 4: Configure Environment

1. Copy `.env.example` to `.env`:

   ```bash
   copy .env.example .env
   ```

2. Edit `.env` and set your MySQL password:

   ```
   DB_USER=root
   DB_PASSWORD=your_mysql_password_here
   DB_HOST=localhost
   DB_NAME=erp_database
   FLASK_SECRET_KEY=your-secret-key-here
   ```

### Step 5: Run Application (Auto-setup!)

```bash
python app.py
```

**That's it!** 🎉 The app automatically:
- ✅ Creates database `erp_database`
- ✅ Creates all 10 tables
- ✅ Seeds sample data (5 students, 4 faculty)
- ✅ **Hashes all passwords with bcrypt** 🔐
- ✅ Starts the Flask server

**Expected output on first run:**
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

**On subsequent runs:**
```
Tables already exist. Skipping initialization.
 * Running on http://127.0.0.1:5000
```

---

## 🚀 Running the Application

The app will be available at:
- **Local**: http://127.0.0.1:5000
- **Network**: http://your-ip:5000

---

## 🔐 Login Credentials

See `CREDENTIALS.md` for all test accounts.

### Quick Test Login

**Student (Portal Access Only):**
- Username: `Aarsee`
- Password: `student123`

**Faculty (Admin Access):**
- Username: `emilyd`
- Password: `faculty123`

**Note**: All faculty members have admin privileges AND access to faculty dashboard for attendance/marks entry.

> ⚠️ **Change these passwords in production!**

---

## 📁 Project Structure

```
ERP-cell/
├── app.py                  # Main Flask application
├── auth.py                 # Authentication utilities
├── validators.py           # Input validation functions
├── hash_passwords.py       # Password hashing script
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (not in git)
├── .env.example           # Environment template
│
├── database/
│   ├── database.sql       # Database schema
│   ├── seed.sql          # Sample data
│   └── seed.sql.backup   # Backup of original
│
└── template/
    ├── index.html        # Main HTML file
    └── style.css         # Stylesheet
```

---

## 🗄️ Database Schema

### Tables (10)

1. **Student_Info** - Student personal details
2. **Faculty_Info** - Faculty information
3. **User_Credentials** - Login & authentication
4. **Departments** - Department management
5. **Subjects** - Course catalog
6. **Student_Results** - Marks & grades
7. **Student_Fees** - Fee tracking
8. **Student_Attendance** - Attendance records
9. **Class_Timetable** - Class schedules
10. **Library_Transaction** - Library books

---

## 📡 API Documentation

### Total Endpoints: 45

**Authentication (2)**
```
POST /login
POST /logout
```

**Student APIs (9)**
```
GET  /api/student/subjects/<id>
GET  /api/student/marks/<id>
GET  /api/student/attendance-detailed/<id>
GET  /api/student/attendance-breakdown/<student_id>/<subject_id>
GET  /api/fees/<id>
GET  /api/library/<id>
POST /api/student/change-password
GET  /api/profile/<id>/Student
GET  /api/timetable/<id>/Student
```

**Faculty APIs (8)**
```
GET  /api/faculty/dashboard/stats/<id>
GET  /api/faculty/classes/<id>
POST /api/faculty/attendance
POST /api/faculty/marks
GET  /api/faculty/marks/<subject_id>
GET  /api/faculty/students/<subject_id>
GET  /api/faculty/all-students/<faculty_id>
GET  /api/profile/<id>/Faculty
GET  /api/timetable/<id>/Faculty
```

**Admin APIs (20)**
```
GET/POST/PUT/DELETE /api/admin/students
GET/POST/PUT/DELETE /api/admin/faculty
GET/POST/PUT/DELETE /api/admin/departments
GET/POST/PUT/DELETE /api/admin/subjects
GET /api/admin/dashboard/stats
GET /api/admin/fees
```

See `DEV_GUIDE.md` for complete API reference.

---

## 📊 Project Status

### 🆕 Latest Features

- ✅ Attendance breakdown - Click any subject to see day-by-day present/absent records
- ✅ Fee display optimization - Clean totals with proper breakdown
- ✅ Profile management enhancements
- ✅ Modern UI polish with gradients

### 🚧 Upcoming

- [ ] Profile editing functionality
- [ ] Advanced testing
- [ ] Production deployment

---

## 🧪 Testing

### Manual Testing

1. Start the application
2. Open browser to http://127.0.0.1:5000
3. Login with test credentials
4. Navigate through different sections
5. Verify data displays correctly

### Test Scenarios

- ✅ Login with valid credentials
- ✅ Login with invalid credentials
- ✅ View student profile
- ✅ View timetable
- ✅ View results
- ✅ View attendance
- ✅ View fees
- ✅ View library transactions
- ✅ Logout

---

## 🐛 Troubleshooting

### Database Connection Error

**Error**: `Can't connect to MySQL server`

**Solution**:
1. Check if MySQL service is running
2. Verify credentials in `.env` file
3. Test connection: `mysql -u root -p`

### Import Errors

**Error**: `ModuleNotFoundError`

**Solution**:
```bash
pip install -r requirements.txt
```

### Port already in use

**Solution:** Kill process or change port in `app.py`

### More help?

See **[DEV_GUIDE.md](DEV_GUIDE.md)** for detailed troubleshooting

---

## 📞 Support

### Documentation

- **README.md** - Installation and usage (this file)
- **DEV_GUIDE.md** - Developer documentation
- **Database Schema** - `database/database.sql`

### Contact

- **GitHub**: [@neverbeatenrc](https://github.com/neverbeatenrc)
- **Repository**: [ERP-cell](https://github.com/neverbeatenrc/ERP-cell)
- **Issues**: [Report a bug](https://github.com/neverbeatenrc/ERP-cell/issues)

For technical details, see **[DEV_GUIDE.md](DEV_GUIDE.md)**

---

## 🤝 Contributing

This is a final year college project. For suggestions or issues:

1. Open an issue on GitHub
2. Submit a pull request

---

## 📄 License

**Educational Use Only** - CN312 Mini Project

Not licensed for commercial use.

---

## 🎯 Project Goals

As per synopsis, this system enables:
- ✅ Student registration & management
- ✅ Attendance tracking & marking
- ✅ Marks management & entry
- ✅ Fee processing
- ✅ Course management
- ✅ Library management
- ⏳ Automated notifications (Week 4)
- ⏳ Performance reports (Week 4)
- ✅ Role-based access control

---

<div align="center">

**Made with ❤️ by neverbeatenrc**

**⭐ Star this repo if you found it helpful!**

[![GitHub](https://img.shields.io/github/stars/neverbeatenrc/ERP-cell?style=social)](https://github.com/neverbeatenrc/ERP-cell)

</div>

