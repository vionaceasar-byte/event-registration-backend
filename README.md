# Event Registration Backend API

This project is a backend API for registering students for a workshop. It was built with FastAPI and SQLite for the Celestius backend recruitment task.

---

## Event Details
- **Event Name:** Backend Development Workshop
- **Event Date:** 24 October 2026
- **Maximum Capacity:** 50 participants

---

## Tech Stack
- **Language:** Python 3.10+
- **Framework:** [FastAPI](https://fastapi.tiangolo.com/) (modern, fast web framework for building APIs)
- **Database:** SQLite (using Python's built-in `sqlite3` module — lightweight, serverless, zero external setup)
- **Data Validation:** [Pydantic](https://docs.pydantic.dev/) (automatic data parsing, email validation, and request schemas)
- **ASGI Server:** [Uvicorn](https://www.uvicorn.org/) (asynchronous web server to run FastAPI)

---

## Project Structure

```text
event-registration-backend/
├── main.py           # FastAPI application, route handlers, constants, and server lifespan
├── database.py       # SQLite database connection manager and SQL query helper functions
├── schemas.py        # Pydantic schemas for request validation, sanitization, and response models
├── requirements.txt  # Python package dependencies
├── .gitignore        # Excludes virtual environment, cache files, and SQLite database
├── test_app.py       # Automated test suite (7 tests verifying all endpoints & edge cases)
└── README.md         # Comprehensive project documentation
```

---

## Setup and Installation

### 1. Clone the Repository
```powershell
git clone https://github.com/vionaceasar-byte/event-registration-backend.git
cd event-registration-backend
```

### 2. Create a Virtual Environment
A virtual environment isolates this project's dependencies from your system's global Python.

**On Windows (PowerShell):**
```powershell
python -m venv venv
```

### 3. Activate the Virtual Environment
**On Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```
*(If PowerShell shows an execution policy error, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` and then run the activate command again).*

**On macOS / Linux:**
```bash
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## Running the Server

Start the development server with live reload enabled:
```bash
uvicorn main:app --reload
```

You should see output similar to:
```text
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Application startup complete.
```

- **Base URL:** `http://127.0.0.1:8000`
API docs are available at /docs when the server is running.

---

## API Endpoints Table

| Method | Endpoint | Description | Status Code | Error Codes |
|---|---|---|---|---|
| `GET` | `/` | Event overview & docs link | `200 OK` | - |
| `POST` | `/register` | Register a new participant | `201 Created` | `400`, `409`, `422` |
| `GET` | `/registrations` | View all registered participants & seat count | `200 OK` | - |
| `GET` | `/registrations/{id}` | View a single registration by ID | `200 OK` | `404 Not Found` |
| `DELETE` | `/registrations/{id}` | Cancel a registration & free up a seat | `200 OK` | `404 Not Found` |

---

## Endpoint Details and Examples

### 1. `POST /register`
Registers a participant. Server automatically validates fields, verifies capacity and duplicate emails before saving, and attaches a server timestamp.

**Request Body:**
```json
{
  "name": "Rahul Sharma",
  "email": "rahul.sharma@example.com",
  "department": "Information Technology"
}
```
*Note: `department` is optional.*

**Success Response (`201 Created`):**
```json
{
  "id": 1,
  "name": "Rahul Sharma",
  "email": "rahul.sharma@example.com",
  "department": "Information Technology",
  "registered_at": "2026-10-20 10:15:30"
}
```

---

### 2. `GET /registrations`
Returns all registered attendees along with seats filled out of total capacity.

**Success Response (`200 OK`):**
```json
{
  "total_registered": 1,
  "capacity": 50,
  "seats_status": "1 / 50 seats filled",
  "registrations": [
    {
      "id": 1,
      "name": "Rahul Sharma",
      "email": "rahul.sharma@example.com",
      "department": "Information Technology",
      "registered_at": "2026-10-20 10:15:30"
    }
  ]
}
```

---

### 3. `GET /registrations/{id}`
Retrieves a single attendee record by their numerical `id`.

**Example:** `GET /registrations/1`

**Success Response (`200 OK`):**
```json
{
  "id": 1,
  "name": "Rahul Sharma",
  "email": "rahul.sharma@example.com",
  "department": "Information Technology",
  "registered_at": "2026-10-20 10:15:30"
}
```

---

### 4. `DELETE /registrations/{id}`
Cancels an attendee's registration and automatically frees up their seat.

**Example:** `DELETE /registrations/1`

**Success Response (`200 OK`):**
```json
{
  "message": "Registration for 'Rahul Sharma' was cancelled successfully. 1 seat has been freed.",
  "cancelled_id": 1,
  "seats_status": "0 / 50 seats filled"
}
```

---

## Error Cases Handled

| Scenario | HTTP Status | Response Body | Why It Triggers |
|---|---|---|---|
| **Duplicate Email** | `409 Conflict` | `{"detail": "Already registered"}` | Email is already registered in the database (case-insensitive check). |
| **Event Capacity Full** | `400 Bad Request` | `{"detail": "Event is full"}` | Total registrations have reached the limit of `50`. |
| **Registration Not Found** | `404 Not Found` | `{"detail": "Registration not found"}` | Requested `{id}` does not exist in the database (for GET or DELETE). |
| **Invalid Email Format** | `422 Unprocessable Entity` | `{"detail": [...]}` | Email string is missing `@`, has invalid domain, etc. (caught by Pydantic `EmailStr`). |
| **Missing or Blank Name** | `422 Unprocessable Entity` | `{"detail": [...]}` | `name` key omitted, empty string `""`, or contains only spaces `"   "`. |

---

## Running Automated Tests

Run the full automated test suite (7 tests verifying all endpoints and edge cases):
```powershell
python -m pytest
```

---

## What I learned

- **What an API endpoint is:** I learned that an API endpoint is a specific URL path that our backend exposes so users or clients can send requests to it, like using POST to send registration data or GET to view attendees.
- **Why status codes matter (409 vs 404):** I learned how to use correct HTTP status codes to communicate what happened—returning 409 Conflict when an email is already registered, and 404 Not Found when someone looks up an ID that does not exist.
- **Checking limits before saving:** I learned that business rules like the 50-seat capacity limit must be checked on the server first before saving to the database, ensuring we never exceed capacity.
- **How SQLite stores data:** I learned how SQLite saves all tables and records directly into a local file (`event.db`), and how parameterized queries with `?` keep database operations clean and safe from SQL injection.
- **How automated tests work:** I learned how pytest and FastAPI's TestClient let us test every endpoint automatically in code, verifying both success responses and error codes like 400, 404, 409, and 422.
