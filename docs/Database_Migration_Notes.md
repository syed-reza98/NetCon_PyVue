# Database Migration Notes: SQLite Integration for Python Project

## Overview
This document summarizes the changes made to migrate user authentication and log data storage from file-based (JSON) to SQLite database using SQLAlchemy in the `src` directory.

---

## 1. Dependencies
- **Added to `requirements.txt`:**
  - `Flask-SQLAlchemy` (for ORM/database integration)
  - `Werkzeug` (for password hashing)

---

## 2. New/Modified Files

### `src/models.py`
- Created new file to define SQLAlchemy models:
  - `User`: Stores user credentials (email, username, hashed password).
  - `Transaction`: Stores extracted log transaction data (timestamp, card_number, transaction_type, amount).
- Initializes the `db` object for use throughout the app.

### `src/app.py`
- Configured Flask to use SQLite via SQLAlchemy.
- Calls `db.create_all()` on startup to ensure tables are created.

### `src/controllers/auth_controller.py`
- Replaced file-based user management with database queries using the `User` model.
- Passwords are now hashed using Werkzeug.
- Registration and login endpoints now interact with the database.
- Removed all references to `users.json`.

### `src/controllers/ej_controller.py`
- After extracting transactions, each transaction is saved to the `Transaction` table in the database.
- Imports and uses the `Transaction` model and `db` session.

### `src/controllers/users.json`
- **Deleted**: User data is now stored in the database, not in a JSON file.

---

## 3. How It Works
- On first run, `app.db` (SQLite database) is created in the `src` directory.
- User registration and login are handled via the `User` table.
- Extracted log transactions are stored in the `Transaction` table.

---

## 4. Next Steps
- Consider adding database migrations (e.g., Flask-Migrate) for future schema changes.
- Add endpoints to query transactions from the database if needed.
- Add tests to verify database integration.

---

**Migration completed: All user and log data is now stored in SQLite via SQLAlchemy.** 