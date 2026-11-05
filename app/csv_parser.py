import csv
import io
from typing import List, Tuple
from fastapi import HTTPException, UploadFile
from app.models import HospitalCSVRow, ValidationIssue

MAX_HOSPITALS = 20
REQUIRED_COLUMNS = {"name", "address"}
ALLOWED_COLUMNS = {"name", "address", "phone"}


async def parse_and_validate_csv(
    upload_file: UploadFile,
) -> Tuple[List[HospitalCSVRow], List[ValidationIssue]]:
    if not upload_file.filename or not upload_file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a .csv file.")

    raw_bytes = await upload_file.read()
    try:
        content = raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="CSV file must be UTF-8 encoded.")

    if not content.strip():
        raise HTTPException(status_code=400, detail="CSV file is empty.")

    reader = csv.DictReader(io.StringIO(content))
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV file is missing a header row.")

    normalized_headers = [h.strip().lower() for h in reader.fieldnames if h]
    missing_cols = REQUIRED_COLUMNS - set(normalized_headers)
    if missing_cols:
        raise HTTPException(
            status_code=400,
            detail=f"CSV is missing required columns: {', '.join(sorted(missing_cols))}. Expected: name, address[, phone]",
        )

    rows: List[HospitalCSVRow] = []
    issues: List[ValidationIssue] = []

    for idx, raw_row in enumerate(reader, start=1):
        cleaned = {
            (k.strip().lower() if k else ""): (v.strip() if v else "")
            for k, v in raw_row.items()
        }
        if not any(cleaned.values()):
            continue

        name = cleaned.get("name", "")
        address = cleaned.get("address", "")
        phone = cleaned.get("phone", "") or None

        if not name:
            issues.append(ValidationIssue(row=idx, field="name", message="Hospital name is required."))
        if not address:
            issues.append(ValidationIssue(row=idx, field="address", message="Hospital address is required."))

        rows.append(
            HospitalCSVRow(
                row=idx,
                name=name,
                address=address,
                phone=phone,
            )
        )

    if len(rows) == 0:
        raise HTTPException(status_code=400, detail="CSV contains headers but no hospital records.")

    if len(rows) > MAX_HOSPITALS:
        raise HTTPException(
            status_code=400,
            detail=f"CSV contains {len(rows)} hospitals, exceeding the maximum limit of {MAX_HOSPITALS}.",
        )

    return rows, issues
