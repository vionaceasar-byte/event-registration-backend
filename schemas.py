"""
schemas.py - Data Validation & Serialization Models

WHY THIS FILE EXISTS:
FastAPI relies on Pydantic models to define the 'shape' of incoming and outgoing data.
This provides two major backend superpowers:
1. Automatic Input Validation: If a user sends bad data (like an invalid email or missing name),
   FastAPI automatically catches it and returns a 422 Unprocessable Entity error BEFORE
   any database operation runs.
2. Clean Documentation: FastAPI reads these models to auto-generate the interactive Swagger UI at /docs.
"""

from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, field_validator


class RegistrationCreate(BaseModel):
    """
    Schema for the incoming POST /register request body.
    
    WHY: We only ask the client for name, email, and department.
    Fields like 'id' and 'registered_at' must NOT be provided by the user;
    the server will generate them automatically for security and accuracy.
    """
    # min_length=1 prevents users from submitting an empty string
    name: str = Field(..., min_length=1, description="Full name of the participant")
    
    # EmailStr automatically validates email format (e.g., checks for '@' and valid domain)
    email: EmailStr = Field(..., description="Valid email address of the participant")
    
    # Optional field with default None because department is optional in the requirements
    department: Optional[str] = Field(default=None, description="Department/branch (optional)")

    @field_validator("name")
    @classmethod
    def strip_and_validate_name(cls, value: str) -> str:
        """
        WHY: A user might submit spaces only (e.g. "   ").
        Pydantic min_length=1 would technically accept spaces unless we strip it.
        This ensures clean, meaningful names in our database.
        """
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Name cannot be blank or contain only whitespace.")
        return cleaned

    @field_validator("department")
    @classmethod
    def clean_department(cls, value: Optional[str]) -> Optional[str]:
        """Strip whitespace from department if provided."""
        if value is not None:
            cleaned = value.strip()
            return cleaned if cleaned else None
        return None


class RegistrationResponse(BaseModel):
    """
    Schema for returning a single registration object.
    
    WHY: Explicitly defines what fields are sent back to the client.
    This guarantees that the client always receives a predictable JSON structure.
    """
    id: int
    name: str
    email: str
    department: Optional[str] = None
    registered_at: str


class RegistrationListResponse(BaseModel):
    """
    Schema for returning all registrations with capacity summary.
    
    WHY: The requirement specifies returning participants plus a count like
    '12 / 50 seats filled'. Grouping them in a structured response makes it easy
    for both humans and frontend/client apps to consume.
    """
    total_registered: int
    capacity: int
    seats_status: str
    registrations: List[RegistrationResponse]


class CancelRegistrationResponse(BaseModel):
    """
    Schema for the response when a registration is cancelled (DELETE).
    
    WHY: Giving clear feedback (which participant was removed and how many seats remain)
    is good API design.
    """
    message: str
    cancelled_id: int
    seats_status: str
