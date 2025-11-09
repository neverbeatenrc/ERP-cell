"""
Authentication utilities for ERP Cell system.
Handles password hashing, verification, and user authentication.
"""

from flask_bcrypt import Bcrypt
from flask_login import UserMixin

bcrypt = Bcrypt()


class User(UserMixin):
    """User class for Flask-Login."""
    
    def __init__(self, user_id, username, user_role, ref_id):
        self.id = user_id
        self.username = username
        self.user_role = user_role
        self.ref_id = ref_id  # student_ref_id or faculty_ref_id
    
    def get_id(self):
        """Return user ID as string for Flask-Login."""
        return str(self.id)
    
    def is_student(self):
        """Check if user is a student."""
        return self.user_role == 'Student'
    
    def is_faculty(self):
        """Check if user is faculty."""
        return self.user_role == 'Faculty'


def hash_password(password):
    """
    Hash a password using bcrypt.
    
    Args:
        password (str): Plain text password
        
    Returns:
        str: Hashed password
    """
    return bcrypt.generate_password_hash(password).decode('utf-8')


def verify_password(password_hash, password):
    """
    Verify a password against its hash.
    
    Args:
        password_hash (str): Stored password hash
        password (str): Plain text password to verify
        
    Returns:
        bool: True if password matches, False otherwise
    """
    return bcrypt.check_password_hash(password_hash, password)


def create_user_from_db(user_data):
    """
    Create a User object from database row.
    
    Args:
        user_data (dict): User data from database
        
    Returns:
        User: User object for Flask-Login
    """
    ref_id = user_data.get('student_ref_id') or user_data.get('faculty_ref_id')
    
    return User(
        user_id=user_data['user_id'],
        username=user_data['username'],
        user_role=user_data['user_role'],
        ref_id=ref_id
    )
