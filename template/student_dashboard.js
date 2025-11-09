// Student Dashboard JavaScript
let currentStudent = null;
let studentId = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', async function() {
  // Get current user from session
  await getCurrentUser();
  
  // Load dashboard data
  if (currentStudent) {
    loadDashboardData();
  }
  
  // Setup navigation
  setupNavigation();
  
  // Setup change password form
  setupChangePasswordForm();
  
  // Close modals when clicking outside
  setupModalCloseOnOutsideClick();
});

// Get current logged-in student
async function getCurrentUser() {
  try {
    // You might need to adjust this endpoint based on your session management
    const response = await fetch('/api/current-user');
    const data = await response.json();
    
    if (data.success) {
      currentStudent = data.user;
      studentId = data.user.ref_id;
      document.getElementById('user-name').textContent = `${data.user.first_name || 'Student'}`;
    }
  } catch (error) {
    console.error('Error getting current user:', error);
    // If session check fails, redirect to login
    window.location.href = '/';
  }
}

// Setup navigation between sections
function setupNavigation() {
  const navItems = document.querySelectorAll('.nav-item');
  const sections = document.querySelectorAll('.content-section');
  
  navItems.forEach(item => {
    item.addEventListener('click', function(e) {
      e.preventDefault();
      
      // Remove active class from all nav items and sections
      navItems.forEach(nav => nav.classList.remove('active'));
      sections.forEach(section => section.classList.remove('active'));
      
      // Add active class to clicked item
      this.classList.add('active');
      
      // Show corresponding section
      const sectionId = this.dataset.section + '-section';
      const targetSection = document.getElementById(sectionId);
      if (targetSection) {
        targetSection.classList.add('active');
        
        // Update page title
        const title = this.querySelector('span').textContent;
        document.getElementById('page-title').textContent = title;
        
        // Load section data
        loadSectionData(this.dataset.section);
      }
    });
  });
}

// Load section-specific data
async function loadSectionData(section) {
  if (!studentId) return;
  
  switch(section) {
    case 'dashboard':
      loadDashboardData();
      break;
    case 'profile':
      loadProfile();
      break;
    case 'subjects':
      loadSubjects();
      break;
    case 'marks':
      loadMarks();
      break;
    case 'attendance':
      loadAttendance();
      break;
    case 'fees':
      loadFees();
      break;
    case 'library':
      loadLibrary();
      break;
  }
}

// Load dashboard data
async function loadDashboardData() {
  if (!studentId) return;
  
  try {
    // Load stats
    const statsResponse = await fetch(`/api/student/quick-stats/${studentId}`);
    const statsData = await statsResponse.json();
    
    if (statsData.success) {
      const stats = statsData.data;
      document.getElementById('total-subjects').textContent = stats.total_subjects || '0';
      document.getElementById('attendance-percentage').textContent = `${stats.attendance_percentage || '0'}%`;
      document.getElementById('pending-fees').textContent = `₹${stats.pending_fees || '0'}`;
      document.getElementById('library-books').textContent = stats.library_books || '0';
    }
    
    // Load academic overview
    const profileResponse = await fetch(`/api/profile/${studentId}/Student`);
    const profileData = await profileResponse.json();
    
    if (profileData.success) {
      const profile = profileData.data;
      // Try to get department from first subject
      const subjectsResponse = await fetch(`/api/student/subjects/${studentId}`);
      const subjectsData = await subjectsResponse.json();
      
      let department = 'Technology';
      if (subjectsData.success && subjectsData.data && subjectsData.data.length > 0) {
        // Get department from Student_Results
        const resultsResponse = await fetch(`/api/results/${studentId}`);
        const resultsData = await resultsResponse.json();
        if (resultsData.success && resultsData.data && resultsData.data.length > 0) {
          department = resultsData.data[0].department || 'Technology';
        }
      }
      
      document.getElementById('dept-name').textContent = department;
      document.getElementById('semester').textContent = '6'; // Default semester
      document.getElementById('year').textContent = '2024-25';
      document.getElementById('roll-no').textContent = `STU${String(studentId).padStart(4, '0')}`;
    }
    
    // Load recent activities
    loadRecentActivities();
    
  } catch (error) {
    console.error('Error loading dashboard:', error);
    showError('Failed to load dashboard data');
  }
}

// Load recent activities
async function loadRecentActivities() {
  try {
    const response = await fetch(`/api/student/recent-activity/${studentId}`);
    const data = await response.json();
    
    const activitiesList = document.getElementById('recent-activities');
    
    if (data.success && data.data && data.data.length > 0) {
      activitiesList.innerHTML = data.data.map(activity => `
        <div class="activity-item">
          <i class="fas fa-${activity.icon || 'circle'}"></i> ${activity.message}
        </div>
      `).join('');
    } else {
      activitiesList.innerHTML = `
        <div class="empty-state">
          <i class="fas fa-inbox"></i>
          <p>No recent activities</p>
        </div>
      `;
    }
  } catch (error) {
    console.error('Error loading activities:', error);
  }
}

// Load profile
async function loadProfile() {
  if (!studentId) return;
  
  try {
    const response = await fetch(`/api/profile/${studentId}/Student`);
    const data = await response.json();
    
    if (data.success) {
      const profile = data.data;
      
      // Update header
      document.getElementById('profile-name').textContent = `${profile.first_name} ${profile.last_name}`;
      document.getElementById('profile-email').textContent = profile.email || 'N/A';
      
      // Personal information
      const personalInfo = document.getElementById('personal-info');
      personalInfo.innerHTML = `
        <div class="info-item">
          <span class="label">First Name</span>
          <span class="value">${profile.first_name || 'N/A'}</span>
        </div>
        <div class="info-item">
          <span class="label">Last Name</span>
          <span class="value">${profile.last_name || 'N/A'}</span>
        </div>
        <div class="info-item">
          <span class="label">Email</span>
          <span class="value">${profile.email || 'N/A'}</span>
        </div>
        <div class="info-item">
          <span class="label">Phone</span>
          <span class="value">${profile.phone_number || 'N/A'}</span>
        </div>
        <div class="info-item">
          <span class="label">Date of Birth</span>
          <span class="value">${profile.date_of_birth || 'N/A'}</span>
        </div>
        <div class="info-item">
          <span class="label">Gender</span>
          <span class="value">${profile.gender || 'N/A'}</span>
        </div>
      `;
      
      // Get department from results
      const resultsResponse = await fetch(`/api/results/${studentId}`);
      const resultsData = await resultsResponse.json();
      
      let department = 'Technology';
      if (resultsData.success && resultsData.data && resultsData.data.length > 0) {
        department = resultsData.data[0].department || 'Technology';
      }
      
      // Academic information
      const academicInfo = document.getElementById('academic-info');
      academicInfo.innerHTML = `
        <div class="info-item">
          <span class="label">Roll Number</span>
          <span class="value">STU${String(studentId).padStart(4, '0')}</span>
        </div>
        <div class="info-item">
          <span class="label">Department</span>
          <span class="value">${department}</span>
        </div>
        <div class="info-item">
          <span class="label">Semester</span>
          <span class="value">6</span>
        </div>
        <div class="info-item">
          <span class="label">Year</span>
          <span class="value">2024-25</span>
        </div>
        <div class="info-item">
          <span class="label">Admission Date</span>
          <span class="value">${profile.enrollment_date || 'N/A'}</span>
        </div>
      `;
    }
  } catch (error) {
    console.error('Error loading profile:', error);
    showError('Failed to load profile data');
  }
}

// Load subjects
async function loadSubjects() {
  if (!studentId) return;
  
  try {
    const response = await fetch(`/api/student/subjects/${studentId}`);
    const data = await response.json();
    
    const subjectsList = document.getElementById('subjects-list');
    
    if (data.success && data.data && data.data.length > 0) {
      subjectsList.innerHTML = data.data.map(subject => `
        <div class="subject-card">
          <h3>${subject.subject_name}</h3>
          <div class="subject-code">${subject.subject_code || 'N/A'}</div>
          <div class="subject-info">
            <div class="subject-info-item">
              <span class="label">Credits:</span>
              <span class="value">${subject.credits || 'N/A'}</span>
            </div>
            <div class="subject-info-item">
              <span class="label">Type:</span>
              <span class="value">${subject.subject_type || 'N/A'}</span>
            </div>
            <div class="subject-info-item">
              <span class="label">Faculty:</span>
              <span class="value">${subject.faculty_name || 'N/A'}</span>
            </div>
          </div>
        </div>
      `).join('');
    } else {
      subjectsList.innerHTML = `
        <div class="empty-state">
          <i class="fas fa-book"></i>
          <p>No subjects enrolled</p>
        </div>
      `;
    }
  } catch (error) {
    console.error('Error loading subjects:', error);
    showError('Failed to load subjects');
  }
}

// Load marks
async function loadMarks() {
  if (!studentId) return;
  
  try {
    const response = await fetch(`/api/results/${studentId}`);
    const data = await response.json();
    
    const marksTable = document.getElementById('marks-table').querySelector('tbody');
    
    if (data.success && data.data && data.data.length > 0) {
      marksTable.innerHTML = data.data.map(mark => {
        const theory = mark.theory_marks || 0;
        const practical = mark.practical_marks || 0;
        const total = theory + practical;
        return `
          <tr>
            <td>${mark.subject_name}</td>
            <td>${mark.theory_marks !== null ? mark.theory_marks : 'N/A'}</td>
            <td>${mark.practical_marks !== null ? mark.practical_marks : 'N/A'}</td>
            <td><strong>${total}</strong></td>
            <td><span class="grade-badge grade-${mark.grade}">${mark.grade || 'N/A'}</span></td>
          </tr>
        `;
      }).join('');
    } else {
      marksTable.innerHTML = `
        <tr>
          <td colspan="5" style="text-align: center; padding: 40px; color: #6c757d;">
            <i class="fas fa-chart-line" style="font-size: 48px; margin-bottom: 16px; display: block; opacity: 0.3;"></i>
            No marks available
          </td>
        </tr>
      `;
    }
  } catch (error) {
    console.error('Error loading marks:', error);
    showError('Failed to load marks');
  }
}

// Load attendance
async function loadAttendance() {
  if (!studentId) return;
  
  try {
    const response = await fetch(`/api/student/attendance-detailed/${studentId}`);
    const data = await response.json();
    
    const attendanceList = document.getElementById('attendance-list');
    
    if (data.success && data.data && data.data.length > 0) {
      attendanceList.innerHTML = data.data.map(att => {
        const percentage = parseFloat(att.attendance_percentage) || 0;
        let statusClass = 'low';
        if (percentage >= 75) statusClass = 'high';
        else if (percentage >= 65) statusClass = 'medium';
        
        return `
          <div class="attendance-card" onclick="viewAttendanceBreakdown(${att.subject_id}, '${att.subject_name}')">
            <h3>${att.subject_name}</h3>
            <div class="attendance-progress">
              <div class="attendance-progress-bar ${statusClass}" style="width: ${percentage}%"></div>
            </div>
            <div class="attendance-stats">
              <span>${att.classes_attended || 0} / ${att.total_classes || 0} classes</span>
              <span class="percentage ${statusClass}">${percentage.toFixed(1)}%</span>
            </div>
            <div class="view-details-hint">
              <i class="fas fa-eye"></i> Click to view details
            </div>
          </div>
        `;
      }).join('');
    } else {
      attendanceList.innerHTML = `
        <div class="empty-state">
          <i class="fas fa-calendar-check"></i>
          <p>No attendance records</p>
        </div>
      `;
    }
  } catch (error) {
    console.error('Error loading attendance:', error);
    showError('Failed to load attendance');
  }
}

// Load fees
async function loadFees() {
  if (!studentId) return;
  
  try {
    const response = await fetch(`/api/fees/${studentId}`);
    const data = await response.json();
    
    if (data.success && data.data && data.data.length > 0) {
      const fees = data.data[0]; // Assuming first record has the breakdown
      
      // Calculate totals - ensure numbers are parsed correctly
      const totalFees = parseFloat(fees.tuition_fee || 0) + 
                       parseFloat(fees.library_fee || 0) + 
                       parseFloat(fees.lab_fee || 0) + 
                       parseFloat(fees.exam_fee || 0) + 
                       parseFloat(fees.hostel_fee || 0) + 
                       parseFloat(fees.other_charges || 0);
      
      const paidAmount = fees.status === 'Paid' ? totalFees : 0;
      const pendingAmount = fees.status === 'Pending' ? totalFees : 0;
      
      // Update summary with single total values
      document.getElementById('total-fees').textContent = `₹${totalFees.toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
      document.getElementById('paid-amount').textContent = `₹${paidAmount.toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
      document.getElementById('pending-amount').textContent = `₹${pendingAmount.toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
      
      // Update fee details breakdown
      const feeDetails = document.getElementById('fee-details');
      feeDetails.innerHTML = `
        <div class="fee-card">
          <h4>Tuition Fee</h4>
          <div class="amount">₹${parseFloat(fees.tuition_fee || 0).toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
        </div>
        <div class="fee-card">
          <h4>Library Fee</h4>
          <div class="amount">₹${parseFloat(fees.library_fee || 0).toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
        </div>
        <div class="fee-card">
          <h4>Lab Fee</h4>
          <div class="amount">₹${parseFloat(fees.lab_fee || 0).toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
        </div>
        <div class="fee-card">
          <h4>Exam Fee</h4>
          <div class="amount">₹${parseFloat(fees.exam_fee || 0).toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
        </div>
        <div class="fee-card">
          <h4>Hostel Fee</h4>
          <div class="amount">₹${parseFloat(fees.hostel_fee || 0).toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
        </div>
        <div class="fee-card">
          <h4>Other Charges</h4>
          <div class="amount">₹${parseFloat(fees.other_charges || 0).toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
        </div>
      `;
    }
  } catch (error) {
    console.error('Error loading fees:', error);
    showError('Failed to load fee details');
  }
}

// Load library books
async function loadLibrary() {
  if (!studentId) return;
  
  try {
    const response = await fetch(`/api/library/${studentId}`);
    const data = await response.json();
    
    const libraryTable = document.getElementById('library-table').querySelector('tbody');
    
    if (data.success && data.data && data.data.length > 0) {
      libraryTable.innerHTML = data.data.map(book => {
        const isOverdue = new Date(book.due_date) < new Date() && book.status === 'Issued';
        const statusClass = isOverdue ? 'danger' : (book.status === 'Returned' ? 'success' : 'info');
        
        return `
          <tr>
            <td>${book.book_title}</td>
            <td>${book.book_author || 'N/A'}</td>
            <td>${book.issue_date || 'N/A'}</td>
            <td>${book.due_date || 'N/A'}</td>
            <td>
              <span class="grade-badge ${statusClass}">
                ${isOverdue ? 'Overdue' : book.status}
              </span>
            </td>
          </tr>
        `;
      }).join('');
    } else {
      libraryTable.innerHTML = `
        <tr>
          <td colspan="5" style="text-align: center; padding: 40px; color: #6c757d;">
            <i class="fas fa-book-reader" style="font-size: 48px; margin-bottom: 16px; display: block; opacity: 0.3;"></i>
            No books issued
          </td>
        </tr>
      `;
    }
  } catch (error) {
    console.error('Error loading library data:', error);
    showError('Failed to load library records');
  }
}

// Change Password Modal
function showChangePasswordModal() {
  document.getElementById('change-password-modal').classList.add('active');
}

function closeChangePasswordModal() {
  document.getElementById('change-password-modal').classList.remove('active');
  document.getElementById('change-password-form').reset();
}

function setupChangePasswordForm() {
  const form = document.getElementById('change-password-form');
  form.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = new FormData(form);
    const currentPassword = formData.get('current_password');
    const newPassword = formData.get('new_password');
    const confirmPassword = formData.get('confirm_password');
    
    if (newPassword !== confirmPassword) {
      showError('New passwords do not match!');
      return;
    }
    
    try {
      const response = await fetch('/api/student/change-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          student_id: studentId,
          current_password: currentPassword,
          new_password: newPassword
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        showSuccess('Password changed successfully!');
        closeChangePasswordModal();
      } else {
        showError(data.message || 'Failed to change password');
      }
    } catch (error) {
      console.error('Error changing password:', error);
      showError('Failed to change password');
    }
  });
}

// Edit Profile (placeholder)
function toggleEditMode() {
  showInfo('Profile editing feature coming soon!');
}

// View Attendance Breakdown
async function viewAttendanceBreakdown(subjectId, subjectName) {
  if (!studentId) return;
  
  try {
    const response = await fetch(`/api/student/attendance-breakdown/${studentId}/${subjectId}`);
    const data = await response.json();
    
    if (data.success && data.data) {
      showAttendanceModal(subjectName, data.data);
    } else {
      showError('Failed to load attendance details');
    }
  } catch (error) {
    console.error('Error loading attendance breakdown:', error);
    showError('Failed to load attendance details');
  }
}

function showAttendanceModal(subjectName, breakdown) {
  const modal = document.getElementById('attendance-modal');
  const modalTitle = document.getElementById('modal-subject-name');
  const modalBody = document.getElementById('attendance-breakdown-list');
  
  modalTitle.textContent = subjectName;
  
  if (breakdown && breakdown.length > 0) {
    modalBody.innerHTML = breakdown.map(record => {
      const date = new Date(record.attendance_date);
      const formattedDate = date.toLocaleDateString('en-IN', { 
        day: '2-digit', 
        month: 'short', 
        year: 'numeric' 
      });
      const statusClass = record.status === 'Present' ? 'present' : 'absent';
      const statusIcon = record.status === 'Present' ? 'fa-check-circle' : 'fa-times-circle';
      
      return `
        <div class="breakdown-item ${statusClass}">
          <div class="breakdown-date">
            <span class="day-name">${record.day_name}</span>
            <span class="date">${formattedDate}</span>
          </div>
          <div class="breakdown-status">
            <i class="fas ${statusIcon}"></i>
            <span>${record.status}</span>
          </div>
        </div>
      `;
    }).join('');
  } else {
    modalBody.innerHTML = `
      <div class="empty-state">
        <i class="fas fa-calendar-times"></i>
        <p>No attendance records found</p>
      </div>
    `;
  }
  
  modal.style.display = 'flex';
}

function closeAttendanceModal() {
  const modal = document.getElementById('attendance-modal');
  modal.style.display = 'none';
}

// Setup modal close on outside click
function setupModalCloseOnOutsideClick() {
  const modals = document.querySelectorAll('.modal');
  modals.forEach(modal => {
    modal.addEventListener('click', function(e) {
      if (e.target === modal) {
        modal.style.display = 'none';
      }
    });
  });
}

// Logout Modal Functions
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
  window.location.href = '/logout';
}

// Close logout modal when clicking outside
window.addEventListener('click', function(event) {
  const logoutModal = document.getElementById('logout-modal');
  if (event.target === logoutModal) {
    closeLogoutModal();
  }
});

// Utility functions
function showError(message) {
  alert('Error: ' + message);
}

function showSuccess(message) {
  alert('Success: ' + message);
}

function showInfo(message) {
  alert('Info: ' + message);
}
