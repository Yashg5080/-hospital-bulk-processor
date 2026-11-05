from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_serializer


class HospitalCSVRow(BaseModel):
    row: int
    name: str
    address: str
    phone: Optional[str] = None


class HospitalRowResult(BaseModel):
    row: int
    hospital_id: Optional[int] = None
    name: str
    status: str  # "created_and_activated", "created_inactive", "failed", "pending"
    error: Optional[str] = None

    @model_serializer(mode="wrap")
    def serialize_model(self, handler) -> Dict[str, Any]:
        dumped: Dict[str, Any] = handler(self)
        if dumped.get("error") is None:
            dumped.pop("error", None)
        return dumped


class BulkProcessResponse(BaseModel):
    batch_id: str
    total_hospitals: int
    processed_hospitals: int
    failed_hospitals: int
    processing_time_seconds: float
    batch_activated: bool
    hospitals: List[HospitalRowResult]


class ValidationIssue(BaseModel):
    row: int
    field: str
    message: str


class CSVValidationResponse(BaseModel):
    valid: bool
    total_rows: int
    issues: List[ValidationIssue] = Field(default_factory=list)


class BatchProgressResponse(BaseModel):
    batch_id: str
    state: str  # "processing", "completed", "partially_failed"
    total_hospitals: int
    processed_hospitals: int
    failed_hospitals: int
    batch_activated: bool
    processing_time_seconds: float
    hospitals: List[HospitalRowResult]
