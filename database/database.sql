-- Fixed and consistent schema

CREATE DATABASE IF NOT EXISTS erp_database CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE erp_database;

CREATE TABLE IF NOT EXISTS Student_Info (
    student_id INT PRIMARY KEY AUTO_INCREMENT,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE,
    email VARCHAR(150) UNIQUE NOT NULL,
    phone_number VARCHAR(20),
    enrollment_date DATE NOT NULL,
    gender ENUM('Male','Female','Other')
);

CREATE TABLE IF NOT EXISTS Faculty_Info (
    faculty_id INT PRIMARY KEY AUTO_INCREMENT,
    faculty_code VARCHAR(50) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    gender ENUM('Male','Female','Other'),
    department VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    phone_number VARCHAR(20),
    hire_date DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS User_Credentials (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    user_role ENUM('Student','Faculty') NOT NULL,
    student_ref_id INT,
    faculty_ref_id INT,
    FOREIGN KEY (student_ref_id) REFERENCES Student_Info(student_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (faculty_ref_id) REFERENCES Faculty_Info(faculty_id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS Departments (
    dept_id INT PRIMARY KEY AUTO_INCREMENT,
    dept_name VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS Subjects (
    subject_id INT PRIMARY KEY AUTO_INCREMENT,
    subject_code VARCHAR(15) UNIQUE NOT NULL,
    subject_name VARCHAR(150) NOT NULL,
    credits DECIMAL(3,1) NOT NULL,
    dept_id INT NOT NULL,
    FOREIGN KEY (dept_id) REFERENCES Departments(dept_id) ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS Library_Transaction (
    library_id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    book_title VARCHAR(255) NOT NULL,
    book_author VARCHAR(255),
    book_isbn VARCHAR(20),
    issue_date DATE NOT NULL,
    due_date DATE NOT NULL,
    return_date DATE,
    status ENUM('Issued','Returned','Overdue') NOT NULL,
    FOREIGN KEY (student_id) REFERENCES Student_Info(student_id) ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS Student_Results (
    result_id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    subject_id INT NOT NULL,
    department VARCHAR(100) NOT NULL,
    exam_date DATE NOT NULL,
    subject_name VARCHAR(150) NOT NULL,
    theory_marks INT,
    practical_marks INT,
    credits DECIMAL(3,1) NOT NULL,
    grade ENUM('A+','A','B+','B','C+','C','D','F') NOT NULL,
    status_exam ENUM('PASS','FAIL') NOT NULL,
    FOREIGN KEY (student_id) REFERENCES Student_Info(student_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES Subjects(subject_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    UNIQUE KEY unique_student_subject (student_id, subject_id)
);

CREATE TABLE IF NOT EXISTS Student_Fees (
    fee_id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    department VARCHAR(100) NOT NULL,
    tuition_fee DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    library_fee DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    lab_fee DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    exam_fee DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    hostel_fee DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    other_charges DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    total_fee DECIMAL(10,2) NOT NULL,
    paid_date DATE,
    status ENUM('Paid','Pending') NOT NULL DEFAULT 'Pending',
    FOREIGN KEY (student_id) REFERENCES Student_Info(student_id) ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS Student_Attendance (
    attendance_id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    subject_id INT NOT NULL,
    attendance_date DATE NOT NULL,
    status ENUM('Present','Absent') NOT NULL,
    FOREIGN KEY (student_id) REFERENCES Student_Info(student_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES Subjects(subject_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    UNIQUE KEY unique_student_date (student_id, attendance_date, subject_id)
);

CREATE TABLE IF NOT EXISTS Class_Timetable (
    timetable_id INT PRIMARY KEY AUTO_INCREMENT,
    department VARCHAR(100) NOT NULL,
    faculty_id INT NOT NULL,
    subject_id INT NOT NULL,
    day_of_week ENUM('Monday','Tuesday','Wednesday','Thursday','Friday','Saturday') NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    location VARCHAR(100),
    FOREIGN KEY (faculty_id) REFERENCES Faculty_Info(faculty_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES Subjects(subject_id) ON DELETE RESTRICT ON UPDATE CASCADE
);