"""
Secure Admin Account Setup CLI
Usage:
    python backend/create_admin.py --email <admin_email> --password <secure_password> --name <optional_name>
Or run interactively:
    python backend/create_admin.py
"""

import sys
import os
import argparse
import getpass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from database.db import query_db, execute_db, init_db
from utils.security import hash_password, validate_password_strength

def setup_admin(email, password, full_name="System Administrator"):
    init_db()
    email = email.strip().lower()
    full_name = full_name.strip()

    ok_pwd, err_msg = validate_password_strength(password)
    if not ok_pwd:
        print(f"[Error] Insecure password: {err_msg}")
        return False

    pwd_hash = hash_password(password)
    avatar = None

    existing = query_db("SELECT id, role FROM users WHERE email = ?", (email,), one=True)
    if existing:
        execute_db("""
            UPDATE users
            SET password_hash = ?, role = 'admin', full_name = ?, is_verified = 1, locked_until = NULL, failed_login_attempts = 0
            WHERE id = ?
        """, (pwd_hash, full_name, existing['id']))
        print(f"[Success] Existing user '{email}' was promoted/updated to Administrator role.")
    else:
        execute_db("""
            INSERT INTO users (email, password_hash, role, full_name, is_verified, avatar_url)
            VALUES (?, ?, 'admin', ?, 1, ?)
        """, (email, pwd_hash, full_name, avatar))
        print(f"[Success] Created new Administrator account for '{email}'.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Create or update an Administrator account securely.")
    parser.add_argument("--email", help="Administrator email address")
    parser.add_argument("--password", help="Administrator password (min 8 chars, letter + number)")
    parser.add_argument("--name", default="System Administrator", help="Administrator full name")

    args = parser.parse_args()

    email = args.email
    password = args.password
    name = args.name

    if not email:
        email = input("Enter Admin Email (default: vinaybandi651@gmail.com): ").strip() or "vinaybandi651@gmail.com"

    if not password:
        password = getpass.getpass("Enter Secure Admin Password (hidden): ").strip()
        confirm = getpass.getpass("Confirm Admin Password (hidden): ").strip()
        if password != confirm:
            print("[Error] Passwords do not match.")
            sys.exit(1)

    success = setup_admin(email, password, name)
    if not success:
        sys.exit(1)

if __name__ == '__main__':
    main()
