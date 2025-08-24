#!/usr/bin/env python3
"""
Check if user exists in database and verify authentication.
"""

import sys
from pathlib import Path

current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.user import User


def check_user():
    email = "heyeqiu1210@gmail.com"
    
    db = SessionLocal()
    
    try:
        print(f"Checking user: {email}")
        
        # Check if user exists
        user = db.query(User).filter(User.email == email).first()
        
        if user:
            print(f"User FOUND:")
            print(f"  ID: {user.id}")
            print(f"  Email: {user.email}")
            print(f"  Role: {user.role}")
            print(f"  Created: {user.created_at}")
            print(f"  Password Hash: {user.password_hash[:20]}...")
        else:
            print("User NOT FOUND in database")
            
            # Show all users for debugging
            all_users = db.query(User).all()
            print(f"\nAll users in database ({len(all_users)}):")
            for u in all_users:
                print(f"  - {u.email} - Role: {u.role}")
    
    finally:
        db.close()


if __name__ == "__main__":
    check_user()