#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import init_db, get_db
from app.auth import hash_password, get_user_by_email

def create_admin():
    init_db()
    db = get_db()
    
    admin_email = "admin@astrovakta.com"
    admin_name = "Admin"
    admin_password = "admin123"
    
    existing = get_user_by_email(admin_email)
    if existing:
        print(f"Admin user already exists: {admin_email}")
        if not existing.get("is_admin"):
            db.execute("UPDATE users SET is_admin = 1 WHERE id = ?", (existing["id"],))
            db.commit()
            print("Promoted existing user to admin.")
        return
    
    cur = db.execute(
        "INSERT INTO users (email, name, password_hash, plan, is_admin) VALUES (?, ?, ?, ?, ?)",
        (admin_email, admin_name, hash_password(admin_password), "enterprise", 1),
    )
    db.commit()
    
    print(f"Admin user created successfully!")
    print(f"Email:    {admin_email}")
    print(f"Password: {admin_password}")
    print(f"Plan:     enterprise")
    print(f"Admin:    Yes")

if __name__ == "__main__":
    create_admin()
