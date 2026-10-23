"""
main.py - FastAPI Application and Event Registration Endpoints

WHY THIS FILE EXISTS:
This is the entry point of our backend service. It configures the FastAPI application,
defines the constant configurations (like EVENT_CAPACITY), and handles all HTTP routes.

EVENT DETAILS:
- Event: Backend Development Workshop
- Date: 20 October 2026
- Capacity: 50 participants
"""

from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status, Path

# Import database functions and Pydantic schemas
from database import (
    init_db,
    get_registration_count,
    get_registration_by_email,
    create_registration,
    get_all_registrations,
    get_registration_by_id,
    delete_registration,
)
from schemas import (
    RegistrationCreate,
    RegistrationResponse,
    RegistrationListResponse,
    CancelRegistrationResponse,
)

# ============================================================================
# EVENT CONFIGURATION CONSTANTS
# WHY CONSTANTS AT THE TOP:
# Hardcoding numbers like 50 across multiple functions makes code brittle and error-prone.
# Defining EVENT_CAPACITY here in ONE place means if the club changes the venue or capacity,
# we only update this single variable.
# ============================================================================
EVENT_NAME: str = "Backend Development Workshop"
EVENT_DATE: str = "20 October 2026"
EVENT_CAPACITY: int = 50


# ============================================================================
# APPLICATION LIFESPAN (STARTUP / SHUTDOWN)
# WHY LIFESPAN:
# The lifespan context manager is FastAPI's standard way to run startup tasks.
# We ensure the SQLite database and table exist before any client sends requests.
# ============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once when the FastAPI server starts
    init_db()
    yield
    # Code after yield would run on shutdown (if needed)


# Initialize FastAPI app with descriptive metadata for /docs
app = FastAPI(
    title="Event Registration API",
    description=f"Backend API for '{EVENT_NAME}' on {EVENT_DATE}. Maximum capacity: {EVENT_CAPACITY} participants.",
    version="1.0.0",
    lifespan=lifespan,
)


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/", tags=["Info"])
def root_info():
    """
    Root endpoint providing event overview and documentation links.
    WHY: Friendly landing endpoint so anyone opening the server URL knows it is active.
    """
    total = get_registration_count()
    return {
        "event": EVENT_NAME,
        "date": EVENT_DATE,
        "capacity": EVENT_CAPACITY,
        "seats_status": f"{total} / {EVENT_CAPACITY} seats filled",
        "docs_url": "/docs",
    }


@app.post(
    "/register",
    response_model=RegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Registrations"],
    summary="Register a new student for the event",
)
def register_participant(payload: RegistrationCreate):
    """
    Registers a student for the Backend Development Workshop.
    
    VALIDATION FLOW (Checked BEFORE saving to database):
    1. Duplicate email check -> Returns 409 Conflict if email already exists.
    2. Capacity check -> Returns 400 Bad Request if 50 participants already registered.
    3. Automatic server timestamp added -> Saves to SQLite and returns 201 Created.
    
    Note: Pydantic automatically validates name and email format before entering
    this function, returning 422 if missing or invalid.
    """
    # Check 1: Duplicate email check
    # WHY: Prevent the same person from taking multiple seats.
    existing_registration = get_registration_by_email(str(payload.email))
    if existing_registration:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Already registered",
        )

    # Check 2: Event capacity check
    # WHY: Workshop has limited physical seats (50 participants max).
    current_count = get_registration_count()
    if current_count >= EVENT_CAPACITY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event is full",
        )

    # Step 3: Automatically generate server registration timestamp
    # WHY: Timestamps should be determined by the server clock, not the client,
    # to avoid falsified registration times.
    registration_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Step 4: Save to database
    new_registration = create_registration(
        name=payload.name,
        email=str(payload.email),
        department=payload.department,
        registered_at=registration_time,
    )

    return new_registration


@app.get(
    "/registrations",
    response_model=RegistrationListResponse,
    tags=["Registrations"],
    summary="List all registered participants",
)
def list_registrations():
    """
    Returns all registered participants along with seat progress (e.g. '12 / 50 seats filled').
    
    WHY: Allows club organizers to view the attendee list and monitor remaining capacity.
    """
    registrations = get_all_registrations()
    total = len(registrations)

    return {
        "total_registered": total,
        "capacity": EVENT_CAPACITY,
        "seats_status": f"{total} / {EVENT_CAPACITY} seats filled",
        "registrations": registrations,
    }


@app.get(
    "/registrations/{id}",
    response_model=RegistrationResponse,
    tags=["Registrations"],
    summary="Get details of a single registration by ID",
)
def get_registration(
    id: int = Path(..., description="The unique ID of the registration", ge=1)
):
    """
    Fetches a single registration by its primary key ID.
    
    WHY: Useful when an organizer or attendee wants to verify an individual ticket/registration.
    Returns 404 Not Found if no registration exists with the requested ID.
    """
    registration = get_registration_by_id(id)
    if not registration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registration not found",
        )
    return registration


@app.delete(
    "/registrations/{id}",
    response_model=CancelRegistrationResponse,
    status_code=status.HTTP_200_OK,
    tags=["Registrations"],
    summary="Cancel a registration and free up a seat",
)
def cancel_registration(
    id: int = Path(..., description="The unique ID of the registration to cancel", ge=1)
):
    """
    Cancels a participant's registration and frees up their seat.
    
    WHY THIS ENDPOINT MATTERS:
    Real events have cancellations. Implementing DELETE completes the CRUD cycle
    and ensures capacity counts update automatically when participants cancel.
    Returns 404 if the registration ID does not exist.
    """
    registration = get_registration_by_id(id)
    if not registration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registration not found",
        )

    deleted = delete_registration(id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registration not found",
        )

    remaining_seats = get_registration_count()

    return {
        "message": f"Registration for '{registration['name']}' was cancelled successfully. 1 seat has been freed.",
        "cancelled_id": id,
        "seats_status": f"{remaining_seats} / {EVENT_CAPACITY} seats filled",
    }
