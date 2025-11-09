"""
Input validation utilities for ERP Cell system.
Validates user inputs before processing to prevent invalid data and SQL injection.
"""

import re
from datetime import datetime
from email_validator import validate_email, EmailNotValidError


def validate_username(username):
    """
    Validate username format.
    
    Args:
        username (str): Username to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not username or len(username.strip()) == 0:
        return False, "Username is required"
    
    if len(username) < 3:
        return False, "Username must be at least 3 characters long"
    
    if len(username) > 50:
        return False, "Username must be less than 50 characters"
    
    # Allow alphanumeric, underscore, dash
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return False, "Username can only contain letters, numbers, underscores, and dashes"
    
    return True, None


def validate_email_address(email):
    """
    Validate email format.
    
    Args:
        email (str): Email to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not email or len(email.strip()) == 0:
        return False, "Email is required"
    
    try:
        validate_email(email)
        return True, None
    except EmailNotValidError as e:
        return False, str(e)


def validate_password(password):
    """
    Validate password strength.
    
    Args:
        password (str): Password to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not password:
        return False, "Password is required"
    
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    
    if len(password) > 100:
        return False, "Password must be less than 100 characters"
    
    return True, None


def validate_name(name, field_name="Name"):
    """
    Validate name fields (first name, last name).
    
    Args:
        name (str): Name to validate
        field_name (str): Field name for error messages
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not name or len(name.strip()) == 0:
        return False, f"{field_name} is required"
    
    if len(name) < 2:
        return False, f"{field_name} must be at least 2 characters long"
    
    if len(name) > 100:
        return False, f"{field_name} must be less than 100 characters"
    
    # Allow letters, spaces, hyphens, apostrophes
    if not re.match(r"^[a-zA-Z\s\-'\.]+$", name):
        return False, f"{field_name} can only contain letters, spaces, hyphens, and apostrophes"
    
    return True, None


def validate_phone(phone):
    """
    Validate phone number format.
    
    Args:
        phone (str): Phone number to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not phone:
        return True, None  # Phone is optional
    
    # Remove common separators
    cleaned = re.sub(r'[\s\-\(\)\+]', '', phone)
    
    # Check if only digits remain
    if not cleaned.isdigit():
        return False, "Phone number can only contain digits and separators"
    
    if len(cleaned) < 10 or len(cleaned) > 15:
        return False, "Phone number must be between 10 and 15 digits"
    
    return True, None


def validate_date(date_string, field_name="Date"):
    """
    Validate date format (YYYY-MM-DD).
    
    Args:
        date_string (str): Date string to validate
        field_name (str): Field name for error messages
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not date_string:
        return False, f"{field_name} is required"
    
    try:
        datetime.strptime(date_string, '%Y-%m-%d')
        return True, None
    except ValueError:
        return False, f"{field_name} must be in YYYY-MM-DD format"


def validate_marks(marks, field_name="Marks"):
    """
    Validate marks (0-100).
    
    Args:
        marks: Marks value to validate
        field_name (str): Field name for error messages
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if marks is None:
        return True, None  # Marks can be optional for some fields
    
    try:
        marks_int = int(marks)
        if marks_int < 0 or marks_int > 100:
            return False, f"{field_name} must be between 0 and 100"
        return True, None
    except (ValueError, TypeError):
        return False, f"{field_name} must be a valid number"


def validate_amount(amount, field_name="Amount"):
    """
    Validate monetary amount.
    
    Args:
        amount: Amount to validate
        field_name (str): Field name for error messages
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if amount is None:
        return False, f"{field_name} is required"
    
    try:
        amount_float = float(amount)
        if amount_float < 0:
            return False, f"{field_name} cannot be negative"
        if amount_float > 9999999.99:
            return False, f"{field_name} is too large"
        return True, None
    except (ValueError, TypeError):
        return False, f"{field_name} must be a valid number"


def validate_id(id_value, field_name="ID"):
    """
    Validate numeric ID.
    
    Args:
        id_value: ID to validate
        field_name (str): Field name for error messages
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if id_value is None:
        return False, f"{field_name} is required"
    
    try:
        id_int = int(id_value)
        if id_int <= 0:
            return False, f"{field_name} must be a positive number"
        return True, None
    except (ValueError, TypeError):
        return False, f"{field_name} must be a valid number"


def sanitize_input(text):
    """
    Sanitize text input by stripping whitespace.
    
    Args:
        text (str): Text to sanitize
        
    Returns:
        str: Sanitized text
    """
    if text is None:
        return None
    return text.strip()
