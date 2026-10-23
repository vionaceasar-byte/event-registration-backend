"""
database.py - Database Connection and SQL Query Handlers

WHY THIS FILE EXISTS:
Separating database logic from API routes (Separation of Concerns) keeps our codebase clean.
Route handlers in main.py focus on HTTP requests and responses, while database.py focuses
strictly on storing, fetching, and updating data in SQLite.

WHY SQLITE:
Python comes with a built-in 'sqlite3' module. It requires zero external database installation,
stores everything in a single local file (event.db), and uses plain SQL queries that are
easy to understand and explain in an interview.
"""

import sqlite3
from contextlib import contextmanager
from typing import Optional, List, Dict, Any, Generator

# Constant for the database file name so it's defined in one place
DB_FILE = "event.db"


@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager that opens and automatically closes an SQLite database connection.
    
    WHY THIS PATTERN:
    In Python's sqlite3, `with sqlite3.connect(...)` only manages transaction commits/rollbacks,
    it does NOT close the connection. Using @contextmanager with `finally: conn.close()` ensures
    every database connection is properly closed when the query finishes, preventing memory
    leaks and file locks on the operating system.
    
    WHY conn.row_factory = sqlite3.Row:
    By default, SQLite returns query results as plain tuples (e.g. (1, 'Alice', 'alice@test.com')).
    Setting row_factory to sqlite3.Row allows accessing columns by name (e.g. row['email']),
    and makes it effortless to convert rows into Python dictionaries using dict(row).
    """
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    """
    Initializes the database schema if the table does not already exist.
    
    WHY: This runs automatically when the server starts up. It guarantees
    that our 'registrations' table is ready before any API requests arrive.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                department TEXT,
                registered_at TEXT NOT NULL
            )
        """)
        conn.commit()


# Call init_db() once at module import so the database is ready immediately
init_db()


def get_registration_count() -> int:
    """
    Returns the total number of students currently registered.
    
    WHY: We need this to check if the event is full (capacity reached)
    before allowing any new registration, and to display seat stats in GET /registrations.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS total FROM registrations")
        row = cursor.fetchone()
        return row["total"] if row else 0


def get_registration_by_email(email: str) -> Optional[Dict[str, Any]]:
    """
    Searches for an existing registration with the given email.
    Case-insensitive search (LOWER) prevents 'Alice@test.com' and 'alice@test.com'
    from registering as duplicates.
    
    WHY PARAMETERIZED QUERY (?):
    Passing variables via '?' prevents SQL Injection attacks. SQLite treats the
    input strictly as a data value rather than executable SQL code.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM registrations WHERE LOWER(email) = LOWER(?)",
            (email.strip(),)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def create_registration(name: str, email: str, department: Optional[str], registered_at: str) -> Dict[str, Any]:
    """
    Inserts a new registration record into the database and returns the saved record.
    
    WHY conn.commit():
    Changes in SQLite are made in a transaction. We must commit() to permanently
    write the new row to the database file on disk.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO registrations (name, email, department, registered_at)
            VALUES (?, ?, ?, ?)
            """,
            (name.strip(), email.strip().lower(), department.strip() if department else None, registered_at)
        )
        conn.commit()
        new_id = cursor.lastrowid

    # Fetch and return the newly created record so we can send it back to the client
    return get_registration_by_id(new_id)  # type: ignore[return-value]


def get_all_registrations() -> List[Dict[str, Any]]:
    """
    Retrieves all registrations from the database ordered by registration order.
    
    WHY: Used by GET /registrations so organizers can view the full attendee list.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM registrations ORDER BY id ASC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_registration_by_id(registration_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieves a single registration by its unique primary key ID.
    
    WHY: Used by GET /registrations/{id}. Returns None if no record matches,
    which lets main.py return a 404 Not Found error.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM registrations WHERE id = ?", (registration_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def delete_registration(registration_id: int) -> bool:
    """
    Deletes a registration record by its unique ID.
    
    WHY: Used by DELETE /registrations/{id}. Allows attendees or organizers
    to cancel a registration, freeing up a seat for another student.
    Returns True if a row was found and deleted, False if no such row existed.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM registrations WHERE id = ?", (registration_id,))
        conn.commit()
        return cursor.rowcount > 0
