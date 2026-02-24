#!/usr/bin/env python3
"""
Generate a bcrypt password hash for use as the SpoolSense owner password.

Usage:
    python scripts/generate-password-hash.py

Then update your AppSettings row:
    UPDATE app_settings SET password_hash = '<output>' WHERE id = 1;

Or set it via the Change Password form in the UI after first login.
"""
import getpass
import bcrypt


def main():
    password = getpass.getpass("Enter password: ")
    confirm = getpass.getpass("Confirm password: ")

    if password != confirm:
        print("Passwords do not match.")
        raise SystemExit(1)

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()
    print(f"\nPassword hash:\n{hashed}")


if __name__ == "__main__":
    main()
