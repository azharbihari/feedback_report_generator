from typing import List, Literal
from datetime import datetime
from pydantic import BaseModel, Field, validator

class EventSchema(BaseModel):
    type: Literal["saved_code", "submission"] = Field(
        ..., 
        description="The type of event (saved_code or submission)"
    )
    created_time: datetime = Field(
        ..., 
        description="Timestamp when the event occurred"
    )
    unit: int = Field(
        ..., 
        description="Unit ID associated with the event",
        ge=0
    )
    
    @validator('created_time', pre=True)
    def parse_datetime(cls, value):
        if isinstance(value, str):
            if value.endswith('Z'):
                value = value[:-1] + '+00:00'
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                raise ValueError(f"Invalid datetime format: {value}")
        return value


class StudentSchema(BaseModel):
    namespace: str = Field(
        ..., 
        description="Namespace the student belongs to",
        min_length=1,
        max_length=255
    )
    student_id: str = Field(
        ..., 
        description="Unique identifier for the student",
        min_length=1,
        max_length=255
    )
    events: List[EventSchema] = Field(
        ..., 
        description="List of events associated with the student"
    )
    
    @validator('events')
    def events_not_empty(cls, v):
        if not v:
            raise ValueError("At least one event is required")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "namespace": "ns_example",
                "student_id": "00a9a76518624b02b0ed57263606fc26",
                "events": [
                    {
                        "type": "saved_code",
                        "created_time": "2024-07-21T03:04:55.939000+00:00",
                        "unit": 17
                    },
                    {
                        "type": "submission",
                        "created_time": "2024-07-21T03:10:12.001000+00:00",
                        "unit": 23
                    }
                ]
            }
        }
