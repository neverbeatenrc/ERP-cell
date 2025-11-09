// Admin Dashboard JavaScript

// ============================================
// GLOBAL STATE
// ============================================
let currentUser = null;
let students = [];
let faculty = [];
let departments = [];
let courses = [];

// ============================================
// INITIALIZATION
// ============================================
document.addEventListener('DOMContentLoaded', function() {
    // Check if user is logged in
    checkAuth();
    
    // Initialize navigation
    initNavigation();
    
    // Load initial dashboard data
    loadDashboardData();
    
    // Set up search and filter listeners
    setupEventListeners();
});

function checkAuth() {
    // In a real app, check session/token
    // For now, assume logged in as admin
    currentUser = {
        username: 'admin',
        role: 'Admin'
    };
    
    document.getElementById('admin-name').textContent = currentUser.username;
}

function initNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active class from all links
            navLinks.forEach(l => l.classList.remove('active'));
            
            // Add active class to clicked link
            this.classList.add('active');
            
            // Show corresponding section
            const section = this.dataset.section;
            showSection(section);
        });
    });
}

function showSection(sectionName) {
    // Hide all sections
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });
    
    // Show selected section
    const selectedSection = document.getElementById(sectionName);
    if (selectedSection) {
        selectedSection.classList.add('active');
        
        // Update page title
        const titles = {
            'dashboard': 'Dashboard',
            'students': 'Student Management',
            'faculty': 'Faculty Management',
            'courses': 'Course Management',
            'departments': 'Department Management',
            'fees': 'Fee Management',
            'reports': 'Reports & Analytics'
        };
        
        document.getElementById('page-title').textContent = titles[sectionName] || 'Admin Panel';
        
        // Load data for specific sections
        if (sectionName === 'students') loadStudents();
        if (sectionName === 'faculty') loadFaculty();
        if (sectionName === 'departments') loadDepartments();
        if (sectionName === 'courses') loadCourses();
        if (sectionName === 'fees') loadFees();
    }
}

// ============================================
// DASHBOARD DATA
// ============================================
async function loadDashboardData() {
    try {
        // Load statistics
        await loadStatistics();
        
        // Load recent activities
        loadRecentActivities();
    } catch (error) {
        console.error('Error loading dashboard:', error);
        showNotification('Failed to load dashboard data', 'error');
    }
}

async function loadStatistics() {
    try {
        const response = await fetch('/api/admin/dashboard/stats');
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('total-students').textContent = data.stats.total_students || 0;
            document.getElementById('total-faculty').textContent = data.stats.total_faculty || 0;
            document.getElementById('total-departments').textContent = data.stats.total_departments || 0;
            document.getElementById('pending-fees').textContent = data.stats.pending_fees || 0;
        }
    } catch (error) {
        console.error('Error loading statistics:', error);
        // Set default values
        document.getElementById('total-students').textContent = '0';
        document.getElementById('total-faculty').textContent = '0';
        document.getElementById('total-departments').textContent = '0';
        document.getElementById('pending-fees').textContent = '0';
    }
}

function loadRecentActivities() {
    const activitiesList = document.getElementById('activities-list');
    
    // Placeholder activities
    const activities = [
        { message: 'New student enrolled: Aarsee Vadya', time: '2 hours ago' },
        { message: 'Faculty updated: Dr. Emily Usher', time: '5 hours ago' },
        { message: 'Fee payment received from Student ID: 3', time: '1 day ago' },
        { message: 'New course added: Machine Learning', time: '2 days ago' }
    ];
    
    activitiesList.innerHTML = activities.map(activity => `
        <div class="activity-item">
            <p>${activity.message}</p>
            <span class="activity-time">${activity.time}</span>
        </div>
    `).join('');
}

// ============================================
// STUDENTS MANAGEMENT
// ============================================
async function loadStudents() {
    try {
        const response = await fetch('/api/admin/students');
        const data = await response.json();
        
        if (data.success) {
            students = data.students;
            renderStudentsTable(students);
        } else {
            showNotification('Failed to load students', 'error');
        }
    } catch (error) {
        console.error('Error loading students:', error);
        showNotification('Error loading students', 'error');
    }
}

function renderStudentsTable(studentsData) {
    const tbody = document.getElementById('students-tbody');
    
    if (!studentsData || studentsData.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center;">No students found</td></tr>';
        return;
    }
    
    tbody.innerHTML = studentsData.map(student => `
        <tr>
            <td>${student.student_id}</td>
            <td>${student.first_name} ${student.last_name}</td>
            <td>${student.email}</td>
            <td>${student.phone_number}</td>
            <td>${formatDate(student.enrollment_date)}</td>
            <td class="table-actions">
                <button class="btn-view" onclick="viewStudent(${student.student_id})">
                    <i class="fas fa-eye"></i> View
                </button>
                <button class="btn-edit" onclick="editStudent(${student.student_id})">
                    <i class="fas fa-edit"></i> Edit
                </button>
                <button class="btn-delete" onclick="deleteStudent(${student.student_id})">
                    <i class="fas fa-trash"></i> Delete
                </button>
            </td>
        </tr>
    `).join('');
}

function openAddStudentModal() {
    document.getElementById('student-modal-title').textContent = 'Add Student';
    document.getElementById('student-form').reset();
    document.getElementById('edit-student-id').value = '';
    document.getElementById('student-modal').classList.add('active');
}

function closeStudentModal() {
    document.getElementById('student-modal').classList.remove('active');
}

async function saveStudent(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    const studentId = formData.get('student_id');
    
    const studentData = {
        first_name: formData.get('first_name'),
        last_name: formData.get('last_name'),
        date_of_birth: formData.get('date_of_birth'),
        gender: formData.get('gender'),
        email: formData.get('email'),
        phone_number: formData.get('phone_number'),
        enrollment_date: formData.get('enrollment_date'),
        username: formData.get('username')
    };
    
    try {
        const url = studentId ? `/api/admin/students/${studentId}` : '/api/admin/students';
        const method = studentId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(studentData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(studentId ? 'Student updated successfully' : 'Student added successfully', 'success');
            closeStudentModal();
            loadStudents();
            loadStatistics();
        } else {
            showNotification(data.message || 'Failed to save student', 'error');
        }
    } catch (error) {
        console.error('Error saving student:', error);
        showNotification('Error saving student', 'error');
    }
}

function editStudent(studentId) {
    const student = students.find(s => s.student_id === studentId);
    if (!student) return;
    
    document.getElementById('student-modal-title').textContent = 'Edit Student';
    document.getElementById('edit-student-id').value = studentId;
    
    const form = document.getElementById('student-form');
    form.first_name.value = student.first_name;
    form.last_name.value = student.last_name;
    form.date_of_birth.value = student.date_of_birth;
    form.gender.value = student.gender;
    form.email.value = student.email;
    form.phone_number.value = student.phone_number;
    form.enrollment_date.value = student.enrollment_date;
    form.username.value = student.username || '';
    
    document.getElementById('student-modal').classList.add('active');
}

async function deleteStudent(studentId) {
    if (!confirm('Are you sure you want to delete this student? This action cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/admin/students/${studentId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Student deleted successfully', 'success');
            loadStudents();
            loadStatistics();
        } else {
            showNotification(data.message || 'Failed to delete student', 'error');
        }
    } catch (error) {
        console.error('Error deleting student:', error);
        showNotification('Error deleting student', 'error');
    }
}

function viewStudent(studentId) {
    // Redirect to student profile or show details modal
    window.location.href = `/api/profile/${studentId}/Student`;
}

// ============================================
// FACULTY MANAGEMENT
// ============================================
async function loadFaculty() {
    try {
        const response = await fetch('/api/admin/faculty');
        const data = await response.json();
        
        if (data.success) {
            faculty = data.faculty;
            renderFacultyTable(faculty);
        } else {
            showNotification('Failed to load faculty', 'error');
        }
    } catch (error) {
        console.error('Error loading faculty:', error);
        showNotification('Error loading faculty', 'error');
    }
}

function renderFacultyTable(facultyData) {
    const tbody = document.getElementById('faculty-tbody');
    
    if (!facultyData || facultyData.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center;">No faculty found</td></tr>';
        return;
    }
    
    tbody.innerHTML = facultyData.map(f => `
        <tr>
            <td>${f.faculty_id}</td>
            <td>${f.faculty_code}</td>
            <td>${f.first_name} ${f.last_name}</td>
            <td>${f.department}</td>
            <td>${f.email}</td>
            <td>${f.phone_number}</td>
            <td class="table-actions">
                <button class="btn-edit" onclick="editFaculty(${f.faculty_id})">
                    <i class="fas fa-edit"></i> Edit
                </button>
                <button class="btn-delete" onclick="deleteFaculty(${f.faculty_id})">
                    <i class="fas fa-trash"></i> Delete
                </button>
            </td>
        </tr>
    `).join('');
}

function openAddFacultyModal() {
    document.getElementById('faculty-modal-title').textContent = 'Add Faculty';
    document.getElementById('faculty-form').reset();
    document.getElementById('edit-faculty-id').value = '';
    loadDepartmentOptions('faculty-department');
    document.getElementById('faculty-modal').classList.add('active');
}

function closeFacultyModal() {
    document.getElementById('faculty-modal').classList.remove('active');
}

async function saveFaculty(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    const facultyId = formData.get('faculty_id');
    
    const facultyData = {
        faculty_code: formData.get('faculty_code'),
        first_name: formData.get('first_name'),
        last_name: formData.get('last_name'),
        gender: formData.get('gender'),
        department: formData.get('department'),
        email: formData.get('email'),
        phone_number: formData.get('phone_number'),
        hire_date: formData.get('hire_date'),
        username: formData.get('username')
    };
    
    try {
        const url = facultyId ? `/api/admin/faculty/${facultyId}` : '/api/admin/faculty';
        const method = facultyId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(facultyData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(facultyId ? 'Faculty updated successfully' : 'Faculty added successfully', 'success');
            closeFacultyModal();
            loadFaculty();
            loadStatistics();
        } else {
            showNotification(data.message || 'Failed to save faculty', 'error');
        }
    } catch (error) {
        console.error('Error saving faculty:', error);
        showNotification('Error saving faculty', 'error');
    }
}

function editFaculty(facultyId) {
    const f = faculty.find(fac => fac.faculty_id === facultyId);
    if (!f) return;
    
    document.getElementById('faculty-modal-title').textContent = 'Edit Faculty';
    document.getElementById('edit-faculty-id').value = facultyId;
    loadDepartmentOptions('faculty-department');
    
    const form = document.getElementById('faculty-form');
    form.faculty_code.value = f.faculty_code;
    form.first_name.value = f.first_name;
    form.last_name.value = f.last_name;
    form.gender.value = f.gender;
    form.department.value = f.department;
    form.email.value = f.email;
    form.phone_number.value = f.phone_number;
    form.hire_date.value = f.hire_date;
    form.username.value = f.username || '';
    
    document.getElementById('faculty-modal').classList.add('active');
}

async function deleteFaculty(facultyId) {
    if (!confirm('Are you sure you want to delete this faculty member?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/admin/faculty/${facultyId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Faculty deleted successfully', 'success');
            loadFaculty();
            loadStatistics();
        } else {
            showNotification(data.message || 'Failed to delete faculty', 'error');
        }
    } catch (error) {
        console.error('Error deleting faculty:', error);
        showNotification('Error deleting faculty', 'error');
    }
}

// ============================================
// DEPARTMENTS MANAGEMENT
// ============================================
async function loadDepartments() {
    try {
        const response = await fetch('/api/admin/departments');
        const data = await response.json();
        
        if (data.success) {
            departments = data.departments;
            renderDepartmentsTable(departments);
        } else {
            showNotification('Failed to load departments', 'error');
        }
    } catch (error) {
        console.error('Error loading departments:', error);
        showNotification('Error loading departments', 'error');
    }
}

function renderDepartmentsTable(deptData) {
    const tbody = document.getElementById('departments-tbody');
    
    if (!deptData || deptData.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center;">No departments found</td></tr>';
        return;
    }
    
    tbody.innerHTML = deptData.map(dept => `
        <tr>
            <td>${dept.dept_id}</td>
            <td>${dept.dept_name}</td>
            <td>${dept.student_count || 0}</td>
            <td>${dept.faculty_count || 0}</td>
            <td class="table-actions">
                <button class="btn-edit" onclick="editDepartment(${dept.dept_id})">
                    <i class="fas fa-edit"></i> Edit
                </button>
                <button class="btn-delete" onclick="deleteDepartment(${dept.dept_id})">
                    <i class="fas fa-trash"></i> Delete
                </button>
            </td>
        </tr>
    `).join('');
}

function openAddDepartmentModal() {
    document.getElementById('department-modal-title').textContent = 'Add Department';
    document.getElementById('department-form').reset();
    document.getElementById('edit-dept-id').value = '';
    document.getElementById('department-modal').classList.add('active');
}

function closeDepartmentModal() {
    document.getElementById('department-modal').classList.remove('active');
}

async function saveDepartment(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    const deptId = formData.get('dept_id');
    
    const deptData = {
        dept_name: formData.get('dept_name')
    };
    
    try {
        const url = deptId ? `/api/admin/departments/${deptId}` : '/api/admin/departments';
        const method = deptId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(deptData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(deptId ? 'Department updated successfully' : 'Department added successfully', 'success');
            closeDepartmentModal();
            loadDepartments();
            loadStatistics();
        } else {
            showNotification(data.message || 'Failed to save department', 'error');
        }
    } catch (error) {
        console.error('Error saving department:', error);
        showNotification('Error saving department', 'error');
    }
}

function editDepartment(deptId) {
    const dept = departments.find(d => d.dept_id === deptId);
    if (!dept) return;
    
    document.getElementById('department-modal-title').textContent = 'Edit Department';
    document.getElementById('edit-dept-id').value = deptId;
    
    const form = document.getElementById('department-form');
    form.dept_name.value = dept.dept_name;
    
    document.getElementById('department-modal').classList.add('active');
}

async function deleteDepartment(deptId) {
    if (!confirm('Are you sure you want to delete this department?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/admin/departments/${deptId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Department deleted successfully', 'success');
            loadDepartments();
            loadStatistics();
        } else {
            showNotification(data.message || 'Failed to delete department', 'error');
        }
    } catch (error) {
        console.error('Error deleting department:', error);
        showNotification('Error deleting department', 'error');
    }
}

// ============================================
// COURSES MANAGEMENT
// ============================================
async function loadCourses() {
    try {
        const response = await fetch('/api/admin/subjects');
        const data = await response.json();
        
        if (data.success) {
            courses = data.subjects;
            renderCoursesTable(courses);
        } else {
            showNotification('Failed to load courses', 'error');
        }
    } catch (error) {
        console.error('Error loading courses:', error);
        showNotification('Error loading courses', 'error');
    }
}

function renderCoursesTable(coursesData) {
    const tbody = document.getElementById('courses-tbody');
    
    if (!coursesData || coursesData.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center;">No courses found</td></tr>';
        return;
    }
    
    tbody.innerHTML = coursesData.map(course => `
        <tr>
            <td>${course.subject_code}</td>
            <td>${course.subject_name}</td>
            <td>${course.credits}</td>
            <td>${course.dept_name || course.dept_id}</td>
            <td class="table-actions">
                <button class="btn-edit" onclick="editCourse(${course.subject_id})">
                    <i class="fas fa-edit"></i> Edit
                </button>
                <button class="btn-delete" onclick="deleteCourse(${course.subject_id})">
                    <i class="fas fa-trash"></i> Delete
                </button>
            </td>
        </tr>
    `).join('');
}

function openAddCourseModal() {
    document.getElementById('course-modal-title').textContent = 'Add Course';
    document.getElementById('course-form').reset();
    document.getElementById('edit-subject-id').value = '';
    loadDepartmentOptions('course-department');
    document.getElementById('course-modal').classList.add('active');
}

function closeCourseModal() {
    document.getElementById('course-modal').classList.remove('active');
}

async function saveCourse(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    const subjectId = formData.get('subject_id');
    
    const courseData = {
        subject_code: formData.get('subject_code'),
        subject_name: formData.get('subject_name'),
        credits: parseFloat(formData.get('credits')),
        dept_id: parseInt(formData.get('dept_id'))
    };
    
    try {
        const url = subjectId ? `/api/admin/subjects/${subjectId}` : '/api/admin/subjects';
        const method = subjectId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(courseData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(subjectId ? 'Course updated successfully' : 'Course added successfully', 'success');
            closeCourseModal();
            loadCourses();
        } else {
            showNotification(data.message || 'Failed to save course', 'error');
        }
    } catch (error) {
        console.error('Error saving course:', error);
        showNotification('Error saving course', 'error');
    }
}

function editCourse(subjectId) {
    const course = courses.find(c => c.subject_id === subjectId);
    if (!course) return;
    
    document.getElementById('course-modal-title').textContent = 'Edit Course';
    document.getElementById('edit-subject-id').value = subjectId;
    loadDepartmentOptions('course-department');
    
    const form = document.getElementById('course-form');
    form.subject_code.value = course.subject_code;
    form.subject_name.value = course.subject_name;
    form.credits.value = course.credits;
    form.dept_id.value = course.dept_id;
    
    document.getElementById('course-modal').classList.add('active');
}

async function deleteCourse(subjectId) {
    if (!confirm('Are you sure you want to delete this course?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/admin/subjects/${subjectId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Course deleted successfully', 'success');
            loadCourses();
        } else {
            showNotification(data.message || 'Failed to delete course', 'error');
        }
    } catch (error) {
        console.error('Error deleting course:', error);
        showNotification('Error deleting course', 'error');
    }
}

// ============================================
// FEES MANAGEMENT
// ============================================
async function loadFees() {
    try {
        const response = await fetch('/api/admin/fees');
        const data = await response.json();
        
        if (data.success) {
            renderFeesTable(data.fees);
        } else {
            showNotification('Failed to load fees', 'error');
        }
    } catch (error) {
        console.error('Error loading fees:', error);
        showNotification('Error loading fees', 'error');
    }
}

function renderFeesTable(feesData) {
    const tbody = document.getElementById('fees-tbody');
    
    if (!feesData || feesData.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center;">No fee records found</td></tr>';
        return;
    }
    
    tbody.innerHTML = feesData.map(fee => {
        // Calculate breakdown
        const breakdown = `
            Tuition: ₹${fee.tuition_fee.toFixed(2)}<br>
            Library: ₹${fee.library_fee.toFixed(2)}<br>
            Lab: ₹${fee.lab_fee.toFixed(2)}<br>
            Exam: ₹${fee.exam_fee.toFixed(2)}<br>
            Hostel: ₹${fee.hostel_fee.toFixed(2)}<br>
            Other: ₹${fee.other_charges.toFixed(2)}
        `;
        
        return `
        <tr>
            <td>${fee.student_id}</td>
            <td>${fee.student_name || 'N/A'}</td>
            <td>${fee.department || 'N/A'}</td>
            <td>₹${fee.total_fee.toFixed(2)}</td>
            <td><span class="status-badge ${fee.status.toLowerCase()}">${fee.status}</span></td>
            <td class="table-actions">
                <button class="btn-view" onclick="viewFeeBreakdown(${fee.student_id}, \`${breakdown}\`)">
                    <i class="fas fa-eye"></i> View
                </button>
            </td>
        </tr>
        `;
    }).join('');
}

function viewFeeBreakdown(studentId, breakdown) {
    alert(`Fee Breakdown for Student ${studentId}:\n\n${breakdown.replace(/<br>/g, '\n')}`);
}

// ============================================
// UTILITY FUNCTIONS
// ============================================
async function loadDepartmentOptions(selectId) {
    try {
        const response = await fetch('/api/admin/departments');
        const data = await response.json();
        
        if (data.success) {
            const select = document.getElementById(selectId);
            select.innerHTML = '<option value="">Select Department</option>' +
                data.departments.map(dept => 
                    `<option value="${dept.dept_name}">${dept.dept_name}</option>`
                ).join('');
        }
    } catch (error) {
        console.error('Error loading departments:', error);
    }
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

function showNotification(message, type = 'info') {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification ${type}`;
    notification.classList.add('show');
    
    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

function logout() {
    showLogoutModal();
}

function showLogoutModal() {
    const modal = document.getElementById('logout-modal');
    modal.classList.add('active');
}

function closeLogoutModal() {
    const modal = document.getElementById('logout-modal');
    modal.classList.remove('active');
}

function confirmLogout() {
    fetch('/logout', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        window.location.href = '/';
    })
    .catch(error => {
        console.error('Logout error:', error);
        window.location.href = '/';
    });
}

// Close logout modal when clicking outside
window.addEventListener('click', function(event) {
    const logoutModal = document.getElementById('logout-modal');
    if (event.target === logoutModal) {
        closeLogoutModal();
    }
});


// ============================================
// SEARCH AND FILTER
// ============================================
function setupEventListeners() {
    // Student search
    const studentSearch = document.getElementById('student-search');
    if (studentSearch) {
        studentSearch.addEventListener('input', function() {
            const query = this.value.toLowerCase();
            const filtered = students.filter(s => 
                s.first_name.toLowerCase().includes(query) ||
                s.last_name.toLowerCase().includes(query) ||
                s.student_id.toString().includes(query)
            );
            renderStudentsTable(filtered);
        });
    }
    
    // Faculty search
    const facultySearch = document.getElementById('faculty-search');
    if (facultySearch) {
        facultySearch.addEventListener('input', function() {
            const query = this.value.toLowerCase();
            const filtered = faculty.filter(f => 
                f.first_name.toLowerCase().includes(query) ||
                f.last_name.toLowerCase().includes(query) ||
                f.faculty_code.toLowerCase().includes(query)
            );
            renderFacultyTable(filtered);
        });
    }
}

// Close modals when clicking outside
window.addEventListener('click', function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.classList.remove('active');
    }
});
