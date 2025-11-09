// Faculty Dashboard JavaScript

let currentFacultyId = null;
let currentSubjects = [];
let attendanceData = [];
let marksData = [];

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Get faculty ID from session/URL (you'll need to pass this from Flask)
    currentFacultyId = getFacultyIdFromSession();
    
    // Set today's date in attendance picker
    document.getElementById('attendance-date').valueAsDate = new Date();
    
    // Load initial data
    loadFacultyProfile();
    loadDashboardStats();
    
    // Setup navigation
    setupNavigation();
    
    // Setup event listeners
    setupEventListeners();
});

function getFacultyIdFromSession() {
    // This should be set by your Flask template
    // For now, return a default value
    return 1; // You'll replace this with actual session data
}

function setupNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    
    navItems.forEach(item => {
        item.addEventListener('click', function(e) {
            if (this.getAttribute('href') === '#') {
                e.preventDefault();
                
                // Remove active class from all items
                navItems.forEach(nav => nav.classList.remove('active'));
                
                // Add active class to clicked item
                this.classList.add('active');
                
                // Get section to show
                const section = this.dataset.section;
                showSection(section);
            }
        });
    });
}

function showSection(sectionName) {
    // Hide all sections
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });
    
    // Show selected section
    const section = document.getElementById(`${sectionName}-section`);
    if (section) {
        section.classList.add('active');
    }
    
    // Update page title
    const titles = {
        'dashboard': 'Dashboard',
        'classes': 'My Classes',
        'attendance': 'Mark Attendance',
        'marks': 'Enter Marks',
        'timetable': 'My Timetable',
        'students': 'Student List'
    };
    
    if (titles[sectionName]) {
        document.getElementById('section-title').textContent = titles[sectionName];
    }
    
    // Load section-specific data
    switch(sectionName) {
        case 'dashboard':
            loadDashboardStats();
            break;
        case 'classes':
            loadMyClasses();
            break;
        case 'attendance':
            loadSubjectsForAttendance();
            break;
        case 'marks':
            loadSubjectsForMarks();
            break;
        case 'timetable':
            loadTimetable();
            break;
        case 'students':
            loadStudentsList();
            break;
    }
}

function setupEventListeners() {
    // Attendance listeners
    document.getElementById('load-students-btn').addEventListener('click', loadStudentsForAttendance);
    document.getElementById('mark-all-present-btn').addEventListener('click', markAllPresent);
    document.getElementById('save-attendance-btn').addEventListener('click', saveAttendance);
    
    // Marks listeners
    document.getElementById('load-marks-students-btn').addEventListener('click', loadStudentsForMarks);
    document.getElementById('save-marks-btn').addEventListener('click', saveMarks);
    
    // Search listener
    document.getElementById('student-search').addEventListener('input', filterStudents);
}

// API Calls

async function loadFacultyProfile() {
    try {
        const response = await fetch(`/api/profile/${currentFacultyId}/Faculty`);
        const data = await response.json();
        
        if (data.first_name && data.last_name) {
            document.getElementById('faculty-name').textContent = 
                `${data.first_name} ${data.last_name}`;
        }
    } catch (error) {
        console.error('Error loading faculty profile:', error);
    }
}

async function loadDashboardStats() {
    try {
        const response = await fetch(`/api/faculty/dashboard/stats/${currentFacultyId}`);
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('total-subjects').textContent = data.total_subjects || 0;
            document.getElementById('total-students-taught').textContent = data.total_students || 0;
            document.getElementById('classes-today').textContent = data.classes_today || 0;
            document.getElementById('avg-attendance').textContent = 
                (data.avg_attendance || 0) + '%';
            
            // Load today's classes
            loadTodayClasses(data.today_classes || []);
            
            // Load recent activities
            loadRecentActivities(data.recent_activities || []);
        }
    } catch (error) {
        console.error('Error loading dashboard stats:', error);
        showNotification('Error loading dashboard data', 'error');
    }
}

function loadTodayClasses(classes) {
    const container = document.getElementById('today-classes');
    
    if (classes.length === 0) {
        container.innerHTML = '<p class="placeholder">No classes scheduled for today</p>';
        return;
    }
    
    container.innerHTML = classes.map(cls => `
        <div class="class-item">
            <h4>${cls.subject_name} (${cls.subject_code})</h4>
            <p><i class="fas fa-clock"></i> ${cls.time_slot}</p>
        </div>
    `).join('');
}

function loadRecentActivities(activities) {
    const container = document.getElementById('recent-activities');
    
    if (activities.length === 0) {
        container.innerHTML = '<p class="placeholder">No recent activities</p>';
        return;
    }
    
    container.innerHTML = activities.map(activity => `
        <div class="activity-item">
            <h4>${activity.title}</h4>
            <p>${activity.description} - ${activity.time}</p>
        </div>
    `).join('');
}

async function loadMyClasses() {
    try {
        const response = await fetch(`/api/faculty/classes/${currentFacultyId}`);
        const data = await response.json();
        
        if (data.success) {
            currentSubjects = data.subjects || [];
            displayClasses(currentSubjects);
        }
    } catch (error) {
        console.error('Error loading classes:', error);
        showNotification('Error loading classes', 'error');
    }
}

function displayClasses(subjects) {
    const tbody = document.getElementById('classes-table-body');
    
    if (subjects.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="placeholder">No classes assigned</td></tr>';
        return;
    }
    
    tbody.innerHTML = subjects.map(subject => `
        <tr>
            <td>${subject.subject_code}</td>
            <td>${subject.subject_name}</td>
            <td>${subject.dept_name}</td>
            <td>${subject.credits}</td>
            <td>${subject.student_count || 0}</td>
            <td>
                <button class="btn btn-view" onclick="viewSubjectDetails(${subject.subject_id}, '${subject.subject_name}')">
                    <i class="fas fa-eye"></i> View
                </button>
            </td>
        </tr>
    `).join('');
}

async function loadSubjectsForAttendance() {
    try {
        const response = await fetch(`/api/faculty/classes/${currentFacultyId}`);
        const data = await response.json();
        
        if (data.success) {
            const select = document.getElementById('attendance-subject');
            select.innerHTML = '<option value="">Choose a subject...</option>';
            
            data.subjects.forEach(subject => {
                const option = document.createElement('option');
                option.value = subject.subject_id;
                option.textContent = `${subject.subject_code} - ${subject.subject_name}`;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading subjects:', error);
    }
}

async function loadStudentsForAttendance() {
    const subjectId = document.getElementById('attendance-subject').value;
    const date = document.getElementById('attendance-date').value;
    
    if (!subjectId) {
        showNotification('Please select a subject first', 'error');
        return;
    }
    
    if (!date) {
        showNotification('Please select a date', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/api/faculty/students/${subjectId}`);
        const data = await response.json();
        
        if (data.success) {
            attendanceData = data.students.map(student => ({
                student_id: student.student_id,
                name: `${student.first_name} ${student.last_name}`,
                roll_no: `STU${String(student.student_id).padStart(4, '0')}`,
                present: false
            }));
            
            displayAttendanceTable();
        }
    } catch (error) {
        console.error('Error loading students:', error);
        showNotification('Error loading students', 'error');
    }
}

function displayAttendanceTable() {
    const tbody = document.getElementById('attendance-table-body');
    
    tbody.innerHTML = attendanceData.map((student, index) => `
        <tr>
            <td>${student.roll_no}</td>
            <td>${student.name}</td>
            <td>
                <div class="attendance-checkbox">
                    <input type="checkbox" 
                           id="attendance-${index}" 
                           ${student.present ? 'checked' : ''}
                           onchange="toggleAttendance(${index})">
                    <label for="attendance-${index}">
                        ${student.present ? 'Present' : 'Absent'}
                    </label>
                </div>
            </td>
        </tr>
    `).join('');
}

function toggleAttendance(index) {
    attendanceData[index].present = !attendanceData[index].present;
    displayAttendanceTable();
}

function markAllPresent() {
    attendanceData.forEach(student => student.present = true);
    displayAttendanceTable();
    showNotification('All students marked present', 'success');
}

async function saveAttendance() {
    const subjectId = document.getElementById('attendance-subject').value;
    const date = document.getElementById('attendance-date').value;
    
    if (!subjectId || !date) {
        showNotification('Please select subject and date', 'error');
        return;
    }
    
    if (attendanceData.length === 0) {
        showNotification('No students loaded', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/faculty/attendance', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                subject_id: subjectId,
                date: date,
                attendance: attendanceData
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Attendance saved successfully', 'success');
        } else {
            showNotification(data.message || 'Failed to save attendance', 'error');
        }
    } catch (error) {
        console.error('Error saving attendance:', error);
        showNotification('Error saving attendance', 'error');
    }
}

async function loadSubjectsForMarks() {
    try {
        const response = await fetch(`/api/faculty/classes/${currentFacultyId}`);
        const data = await response.json();
        
        if (data.success) {
            const select = document.getElementById('marks-subject');
            select.innerHTML = '<option value="">Choose a subject...</option>';
            
            data.subjects.forEach(subject => {
                const option = document.createElement('option');
                option.value = subject.subject_id;
                option.textContent = `${subject.subject_code} - ${subject.subject_name}`;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading subjects:', error);
    }
}

async function loadStudentsForMarks() {
    const subjectId = document.getElementById('marks-subject').value;
    
    if (!subjectId) {
        showNotification('Please select a subject first', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/api/faculty/marks/${subjectId}`);
        const data = await response.json();
        
        if (data.success) {
            marksData = data.students.map(student => ({
                student_id: student.student_id,
                name: `${student.first_name} ${student.last_name}`,
                roll_no: `STU${String(student.student_id).padStart(4, '0')}`,
                theory_marks: student.theory_marks || 0,
                practical_marks: student.practical_marks || 0
            }));
            
            displayMarksTable();
        }
    } catch (error) {
        console.error('Error loading students:', error);
        showNotification('Error loading students', 'error');
    }
}

function displayMarksTable() {
    const tbody = document.getElementById('marks-table-body');
    
    tbody.innerHTML = marksData.map((student, index) => {
        const total = parseInt(student.theory_marks) + parseInt(student.practical_marks);
        const grade = calculateGrade(total);
        
        return `
            <tr>
                <td>${student.roll_no}</td>
                <td>${student.name}</td>
                <td>
                    <input type="number" 
                           class="marks-input" 
                           min="0" max="100" 
                           value="${student.theory_marks}"
                           onchange="updateMarks(${index}, 'theory', this.value)">
                </td>
                <td>
                    <input type="number" 
                           class="marks-input" 
                           min="0" max="100" 
                           value="${student.practical_marks}"
                           onchange="updateMarks(${index}, 'practical', this.value)">
                </td>
                <td><strong>${total}</strong></td>
                <td><span class="grade-badge ${grade.class}">${grade.grade}</span></td>
            </tr>
        `;
    }).join('');
}

function updateMarks(index, type, value) {
    if (type === 'theory') {
        marksData[index].theory_marks = parseInt(value) || 0;
    } else {
        marksData[index].practical_marks = parseInt(value) || 0;
    }
    displayMarksTable();
}

function calculateGrade(total) {
    if (total >= 90) return { grade: 'A+', class: 'a-plus' };
    if (total >= 80) return { grade: 'A', class: 'a' };
    if (total >= 70) return { grade: 'B+', class: 'b-plus' };
    if (total >= 60) return { grade: 'B', class: 'b' };
    if (total >= 50) return { grade: 'C', class: 'c' };
    return { grade: 'F', class: 'fail' };
}

async function saveMarks() {
    const subjectId = document.getElementById('marks-subject').value;
    const examType = document.getElementById('exam-type').value;
    
    if (!subjectId) {
        showNotification('Please select a subject', 'error');
        return;
    }
    
    if (marksData.length === 0) {
        showNotification('No students loaded', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/faculty/marks', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                subject_id: subjectId,
                exam_type: examType,
                marks: marksData
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Marks saved successfully', 'success');
        } else {
            showNotification(data.message || 'Failed to save marks', 'error');
        }
    } catch (error) {
        console.error('Error saving marks:', error);
        showNotification('Error saving marks', 'error');
    }
}

async function loadTimetable() {
    try {
        const response = await fetch(`/api/timetable/${currentFacultyId}/Faculty`);
        const result = await response.json();
        
        if (result.success && result.data && result.data.length > 0) {
            displayTimetable(result.data);
        } else {
            document.getElementById('timetable-body').innerHTML = 
                '<tr><td colspan="6" class="placeholder">No timetable available</td></tr>';
        }
    } catch (error) {
        console.error('Error loading timetable:', error);
        document.getElementById('timetable-body').innerHTML = 
            '<tr><td colspan="6" class="placeholder">Error loading timetable</td></tr>';
    }
}

function displayTimetable(timetableData) {
    // Group by time slots
    const slots = {};
    timetableData.forEach(entry => {
        const timeSlot = `${entry.start_time} - ${entry.end_time}`;
        if (!slots[timeSlot]) {
            slots[timeSlot] = {};
        }
        slots[timeSlot][entry.day_of_week] = entry;
    });
    
    const tbody = document.getElementById('timetable-body');
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];
    
    tbody.innerHTML = Object.keys(slots).map(timeSlot => `
        <tr>
            <td><strong>${timeSlot}</strong></td>
            ${days.map(day => {
                const entry = slots[timeSlot][day];
                if (entry) {
                    return `
                        <td>
                            <div class="timetable-slot">
                                <h4>${entry.subject_name}</h4>
                                <p>${entry.subject_code}</p>
                            </div>
                        </td>
                    `;
                }
                return '<td></td>';
            }).join('')}
        </tr>
    `).join('');
}

async function loadStudentsList() {
    try {
        const response = await fetch(`/api/faculty/all-students/${currentFacultyId}`);
        const data = await response.json();
        
        if (data.success) {
            displayStudentsList(data.students || []);
        }
    } catch (error) {
        console.error('Error loading students:', error);
        showNotification('Error loading students', 'error');
    }
}

function displayStudentsList(students) {
    const tbody = document.getElementById('students-table-body');
    
    if (students.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="placeholder">No students found</td></tr>';
        return;
    }
    
    tbody.innerHTML = students.map(student => `
        <tr>
            <td>STU${String(student.student_id).padStart(4, '0')}</td>
            <td>${student.first_name} ${student.last_name}</td>
            <td>${student.email}</td>
            <td>${student.department}</td>
            <td>${student.attendance_percentage || 0}%</td>
            <td>
                <button class="btn btn-view" onclick="viewStudentDetails(${student.student_id}, '${student.first_name} ${student.last_name}')">
                    <i class="fas fa-eye"></i> View
                </button>
            </td>
        </tr>
    `).join('');
}

function filterStudents() {
    const searchTerm = document.getElementById('student-search').value.toLowerCase();
    const rows = document.querySelectorAll('#students-table-body tr');
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(searchTerm) ? '' : 'none';
    });
}

function viewSubjectDetails(subjectId, subjectName) {
    // Switch to marks section and pre-select this subject
    const marksSubjectSelect = document.getElementById('marks-subject');
    if (marksSubjectSelect) {
        marksSubjectSelect.value = subjectId;
    }
    
    // Navigate to marks section
    document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
    document.querySelector('[data-section="marks"]').classList.add('active');
    showSection('marks');
    
    showNotification(`Switched to marks entry for ${subjectName}`, 'success');
}

function viewStudentDetails(studentId, studentName) {
    showNotification(`Student profile view coming soon for ${studentName}`, 'info');
    // TODO: Implement student profile modal or redirect
}

// Notification System
function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification ${type} show`;
    
    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

// Logout Modal Functions
function showLogoutModal() {
    const modal = document.getElementById('logout-modal');
    modal.classList.add('active');
}

function closeLogoutModal() {
    const modal = document.getElementById('logout-modal');
    modal.classList.remove('active');
}

function confirmLogout() {
    window.location.href = '/logout';
}

// Close modal when clicking outside
window.addEventListener('click', function(event) {
    const modal = document.getElementById('logout-modal');
    if (event.target === modal) {
        closeLogoutModal();
    }
});

