"""
Script to hash existing passwords in the database.
Run this once to update all plain text passwords to hashed versions.
"""

import mysql.connector
import os
from dotenv import load_dotenv
from auth import hash_password

load_dotenv()

# Database configuration
DB_CONFIG = {
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'host': os.environ.get('DB_HOST', 'localhost'),
    'database': 'erp_database'
}

# Default password mapping (what's currently in seed.sql)
PASSWORD_MAPPING = {
    'Aarsee': 'student123',
    'Vedika': 'student123',
    'Awantika': 'student123',
    'Naina': 'student123',
    'Aditi': 'student123',
    'emilyd': 'faculty123',
    'frankm': 'faculty123',
    'gracel': 'faculty123',
    'henrys': 'faculty123'
}

def update_passwords():
    """Update all passwords in the database to hashed versions."""
    try:
        # Connect to database
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("Updating passwords to hashed versions...")
        
        for username, plain_password in PASSWORD_MAPPING.items():
            hashed = hash_password(plain_password)
            
            cursor.execute(
                "UPDATE User_Credentials SET password_hash = %s WHERE username = %s",
                (hashed, username)
            )
            print(f"✓ Updated password for: {username}")
        
        conn.commit()
        print(f"\n✅ Successfully updated {len(PASSWORD_MAPPING)} passwords!")
        print("\n📝 Default passwords:")
        print("   Students: student123")
        print("   Faculty:  faculty123")
        
        cursor.close()
        conn.close()
        
    except mysql.connector.Error as err:
        print(f"❌ Database error: {err}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    print("=" * 60)
    print("ERP Cell - Password Hashing Script")
    print("=" * 60)
    print("\nThis will update all passwords in the database to bcrypt hashes.")
    
    response = input("\nContinue? (yes/no): ").strip().lower()
    
    if response == 'yes':
        update_passwords()
    else:
        print("Operation cancelled.")
