-- Student_Info: 

INSERT INTO Student_Info (student_id, first_name, last_name, date_of_birth, email, phone_number, enrollment_date, gender)
VALUES
('1','Aarsee', 'Vadya', '2004-09-24', 'rcmiawmiaw@foxwin.edu', '555-1001', '2023-09-01', 'Female'),
('2', 'Vedika', 'Agarwal', '2005-03-20', 'vediyay@foxwin.edu', '555-1002', '2023-09-01', 'Female'),
('3', 'Awantika', 'Swati', '2005-06-06', 'avpingu@foxwin.edu', '555-1003', '2023-09-01', 'Female'),
('4', 'Naina', 'Barnawal', '2005-11-19', 'nainunu@foxwin.edu', '555-1004', '2023-09-01', 'Female'),
('5', 'Aditi', 'Kumari', '2003-07-10', 'aditiiyippee@foxwin.edu', '555-1005', '2023-09-01', 'Female');

-- Faculty_Info: 
INSERT INTO Faculty_Info (faculty_id, faculty_code, first_name, last_name, gender, department, email, phone_number, hire_date)
VALUES
('1', 'FCS001', 'Dr. Emily', 'Usher', 'Female', 'Technology', 'emily.d@foxwin.edu', '555-2010', '2010-08-15'),
('2', 'FEE002', 'Mr. Frank', 'Miller', 'Male', 'Technology', 'frank.m@foxwin.edu', '555-2011', '2018-01-20'),
('3', 'FME003', 'Prof. Grace', 'Lee', 'Female', 'Finance', 'grace.l@foxwin.edu', '555-2012', '2015-05-10'),
('4', 'FCS004', 'Dr. Henry', 'Scott', 'Male', 'Arts', 'henry.s@foxwin.edu', '555-2013', '2020-03-01'),
('5', 'FCS005', 'Dr. Lewis', 'Brown', 'Male', 'Arts', 'lewis.b@foxwin.edu', '555-2014', '2013-08-31');


-- User_Credentials: Students 
INSERT INTO User_Credentials (username, password_hash, user_role, student_ref_id, faculty_ref_id)
VALUES
('Aarsee', 'hashed_pass_s1', 'Student', '1', NULL),
('Vedika', 'hashed_pass_s2', 'Student', '2', NULL),
('Awantika', 'hashed_pass_s3', 'Student','3' , NULL),
('Naina', 'hashed_pass_s4', 'Student', '4', NULL),
('Aditi', 'hashed_pass_s5', 'Student', '5', NULL);

-- User_Credentials: Faculty 
INSERT INTO User_Credentials (username, password_hash, user_role, student_ref_id, faculty_ref_id)
VALUES
('emilyd', 'hashed_pass_f1', 'Faculty', NULL, 1),
('frankm', 'hashed_pass_f2', 'Faculty', NULL, 2),
('gracel', 'hashed_pass_f3', 'Faculty', NULL, 3),
('henrys', 'hashed_pass_f4', 'Faculty', NULL, 4);

-- Departments Table
INSERT INTO Departments (dept_id, dept_name)
VALUES
('1', 'Arts'),        -- dept_id 1
('2','Finance'),     -- dept_id 2
('3','Technology');  -- dept_id 3

-- Subjects Table 
INSERT INTO Subjects (subject_code, subject_name, credits, dept_id)
VALUES
('ART101', 'Animation', 3.5, 1),
('ART102', 'Architecture', 4.0, 1),
('FIN201', 'Corporate Finance', 3.0, 2),
('TEC301', 'Computer Science', 4.0, 3),
('TEC302', 'Electronics', 3.5, 3);


-- Library_Transaction: 
INSERT INTO Library_Transaction (student_id, book_title, book_author, book_isbn, issue_date, due_date, return_date, status)
VALUES
(1, 'SQL Database Design', 'J. Smith', '978-1234567890', '2025-10-25', '2025-11-25', NULL, 'Issued'),
(2, 'SQL Database Design', 'J. Smith', '978-1234567890', '2025-10-25', '2025-11-25', '2025-11-22', 'Returned'),
(2, 'Learning Python', 'M. Lutz', '978-0987654321', '2025-09-15', '2025-10-15', '2025-10-10', 'Returned'),
(4, 'Data Structures', 'A. Tanenbaum', '978-1122334455', '2025-11-01', '2025-12-01', NULL, 'Issued'),
(5, 'Operating Systems', 'W. Stallings', '978-6677889900', '2025-10-20', '2025-11-20', NULL, 'Overdue'),
(3, 'Computer Networks', 'A. S. Tanenbaum', '978-5544332211', '2025-09-10', '2025-10-10', '2025-10-05', 'Returned'),
(1, 'Database Systems', 'R. Elmasri', '978-9988776655', '2025-11-05', '2025-12-05', NULL, 'Issued'),
(4, 'Artificial Intelligence', 'S. Russell', '978-4433221100', '2025-10-15', '2025-11-15', NULL, 'Issued'),
(5, 'Machine Learning', 'T. Mitchell', '978-2211003344', '2025-09-20', '2025-10-20', '2025-10-18', 'Returned');

-- Student_Results 
INSERT INTO Student_Results (result_id, student_id, subject_id, department, exam_date, subject_name, theory_marks, practical_marks, credits, grade, status_exam)
VALUES
-- Aarsee Vadya (1): Animation (1, Arts) & Computer Science (4, Tech)
(1, 1, 1, 1, '2025-12-10', 'Animation', 78, 92, 3.5, 'A', 'PASS'),
(2, 1, 4, 3, '2025-12-15', 'Computer Science', 88, 75, 4.0, 'A', 'PASS'),

-- Vedika Agarwal (2): Architecture (2, Arts) & Computer Science (4, Tech)
(3, 2, 2, 1, '2025-12-11', 'Architecture', 70, 85, 4.0, 'B+', 'PASS'),
(4, 2, 4, 3, '2025-12-16', 'Computer Science', 65, 70, 4.0, 'B', 'PASS'),

-- Awantika Swati (3): Finance (3, Finance) & Electronics (5, Tech)
(5, 3, 3, 2, '2025-12-12', 'Corporate Finance', 95, NULL, 3.0, 'A+', 'PASS'),
(6, 3, 5, 3, '2025-12-17', 'Electronics', 40, 60, 3.5, 'F', 'FAIL'), -- Example of a FAIL

-- Naina Barnawal (4): Computer Science (4, Tech) & Electronics (5, Tech)
(7, 4, 4, 3, '2025-12-18', 'Computer Science', 55, 65, 4.0, 'C+', 'PASS'),
(8, 4, 5, 3, '2025-12-13', 'Electronics', 78, 80, 3.5, 'A', 'PASS'),

-- Aditi Kumari (5): Finance (3, Finance) & Architecture (2, Arts)
(9, 5, 3, 2, '2025-12-14', 'Corporate Finance', 82, NULL, 3.0, 'A', 'PASS'),
(10, 5, 2, 1, '2025-12-19', 'Architecture', 90, 90, 4.0, 'A+', 'PASS');

-- Student_Fees 
INSERT INTO Student_Fees (student_id, department, tuition_fee, library_fee, lab_fee, exam_fee, hostel_fee, other_charges, total_fee, paid_date, status)
VALUES
-- Aarsee Vadya (ID 1) - Technology: Fully Paid
(1, 'Technology', 60000.00, 2000.00, 3000.00, 500.00, 0.00, 500.00, 66000.00, '2024-08-15', 'Paid'),

-- Vedika Agarwal (ID 2) - Arts: Pending
(2, 'Arts', 55000.00, 1500.00, 1000.00, 1000.00, 10000.00, 1000.00, 69500.00, NULL, 'Pending'),

-- Awantika Swati (ID 3) - Finance: Fully Paid
(3, 'Finance', 58000.00, 1000.00, 0.00, 500.00, 0.00, 3500.00, 63000.00, '2024-09-01', 'Paid'),

-- Naina Barnawal (ID 4) - Technology: Pending
(4, 'Technology', 60000.00, 2000.00, 3000.00, 1000.00, 10000.00, 0.00, 76000.00, NULL, 'Pending'),

-- Aditi Kumari (ID 5) - Arts: Fully Paid
(5, 'Arts', 55000.00, 1500.00, 1000.00, 500.00, 0.00, 1000.00, 59000.00, '2024-08-25', 'Paid');


-- Student_Attendance (Aarsee, Vedika, Awantika, Naina, Aditi):
INSERT INTO Student_Attendance (student_id, subject_id, attendance_date, status)
VALUES  
(1, 1, '2025-09-01', 'Present'),
(1, 1, '2025-09-02', 'Absent'),
(1, 4, '2025-09-01', 'Present'),
(1, 4, '2025-09-02', 'Present'),
(2, 2, '2025-09-01', 'Present'),
(2, 2, '2025-09-02', 'Present'),
(2, 4, '2025-09-01', 'Absent'),
(2, 4, '2025-09-02', 'Present'),
(2, 2, '2025-09-03', 'Present'),
(2, 4, '2025-09-04', 'Absent'),
(2, 2, '2025-09-05', 'Present'),
(3, 3, '2025-09-01', 'Present'),
(3, 3, '2025-09-02', 'Present'),
(3, 5, '2025-09-01', 'Absent'),
(3, 5, '2025-09-02', 'Absent'),
(3, 3, '2025-09-03', 'Present'),
(3, 5, '2025-09-03', 'Present'),
(3, 3, '2025-09-04', 'Present'),
(3, 5, '2025-09-04', 'Present'),
(4, 4, '2025-09-01', 'Present'),
(4, 4, '2025-09-02', 'Present'),
(4, 5, '2025-09-01', 'Present'),
(4, 5, '2025-09-02', 'Absent'),
(4, 4, '2025-09-03', 'Absent'),
(4, 5, '2025-09-03', 'Present'),
(4, 4, '2025-09-04', 'Present'),
(4, 5, '2025-09-04', 'Present'),
(5, 3, '2025-09-01', 'Absent'),
(5, 3, '2025-09-02', 'Present'),
(5, 2, '2025-09-01', 'Present'),
(5, 2, '2025-09-02', 'Present'),
(5, 3, '2025-09-03', 'Present'),
(5, 2, '2025-09-03', 'Absent'),
(5, 3, '2025-09-04', 'Present'),
(5, 2, '2025-09-04', 'Present');

-- Class Timetable: Computer Science, Animation, Electronics, Architecture, Corporate Finance
INSERT INTO Class_Timetable (department, subject_id, faculty_id, day_of_week, start_time, end_time, location)
VALUES
(3, 4, 1, 'Monday', '09:00:00', '10:30:00', 'Tech Room T101'),
(3, 4, 1, 'Wednesday', '13:30:00', '15:00:00', 'Tech Room T101'),
(1, 1, 4, 'Monday', '14:00:00', '15:30:00', 'Arts Studio A2'),
(1, 1, 4, 'Thursday', '09:00:00', '10:30:00', 'Arts Studio A2'),
(3, 5, 2, 'Tuesday', '10:00:00', '11:30:00', 'Tech Lab L304'),
(3, 5, 2, 'Thursday', '14:00:00', '15:30:00', 'Tech Lab L304'),
(1, 2, 5, 'Tuesday', '15:00:00', '16:30:00', 'Arts Workshop W1'),
(1, 2, 5, 'Friday', '10:00:00', '11:30:00', 'Arts Workshop W1'),
(2, 3, 3, 'Wednesday', '09:30:00', '11:00:00', 'Finance Lecture F12'),
(2, 3, 3, 'Friday', '14:30:00', '16:00:00', 'Finance Lecture F12');
