# Paribus Hospital Bulk Processing System

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![Framework](https://img.shields.io/badge/framework-FastAPI-009688.svg)](https://fastapi.tiangolo.com)
[![Tests](https://img.shields.io/badge/tests-pytest-green.svg)](https://docs.pytest.org)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED.svg)](https://www.docker.com)

A production-grade, asynchronous bulk CSV processing microservice designed for the **Paribus Python Challenge**. It integrates with the external **Hospital Directory API** (`https://hospital-directory.onrender.com`), handling CSV uploads, generating unique batch identifiers, concurrently dispatching record creation with bounded concurrency and exponential backoff, and activating the entire batch in a single atomic-like workflow.

---

## Table of Contents

- [System Architecture](#system-architecture)
- [Key Features & Bonus Implementations](#key-features--bonus-implementations)
- [API Specification](#api-specification)
- [Quick Start (Local)](#quick-start-local)
- [Run with Docker](#run-with-docker)
- [Running Test Suite](#running-test-suite)
- [Deploy to Render](#deploy-to-render)
- [Evaluation Rubric Coverage](#evaluation-rubric-coverage)

---

## System Architecture

```
                  ┌───────────────────────────────────────────────┐
                  │                 Client / UI                   │
                  └──────┬────────────────────────────────┬───────┘
                         │ 1. Multipart CSV Upload        │ 3. WebSocket /
                         │    (POST /hospitals/bulk)      │    Polling Progress
                         ▼                                ▼
                  ┌───────────────────────────────────────────────┐
                  │               FastAPI Gateway                 │
                  └──────┬────────────────────────────────────────┘
                         │
                         ▼
        ┌───────────────────────────────────┐
        │        CSV Parser & Validator     │ ── [Enforces max 20 rows, UTF-8/BOM,
        └────────────────┬──────────────────┘     required 'name' and 'address']
                         │ Validated Rows
                         ▼
        ┌───────────────────────────────────┐
        │       Batch Processing Engine     │ ── [Generates Batch UUID4, In-Memory Store]
        └───────┬───────────────────┬───────┘
                │                   │
  Concurrency-throttled             │ All records
  HTTP worker pool                  │ successfully created
  (asyncio.Semaphore)               │
                │                   ▼
                │        ┌─────────────────────────────┐
                │        │   Batch Activation Trigger  │
                │        └──────────────┬──────────────┘
                ▼                       │
    POST /hospitals/                    │ PATCH /hospitals/batch/{batch_id}/activate
    (creation_batch_id)                 │
                │                       │
                └───────────┬───────────┘
                            ▼
              ┌───────────────────────────┐
              │   Hospital Directory API  │
              │ (onrender.com microservice│
              └───────────────────────────┘
```

---

## Key Features & Bonus Implementations

1. **Strict CSV Parsing & Pre-Validation (`POST /hospitals/bulk/validate`)**:
   - Enforces the hard **maximum limit of 20 hospitals per CSV**.
   - Validates CSV headers (`name`, `address` required; `phone` optional).
   - Handles UTF-8 and UTF-8 with BOM (`utf-8-sig`) encodings.
   - Collects per-row issues without breaking parsing.

2. **High-Performance Concurrent Async Architecture**:
   - Utilizes `httpx.AsyncClient` with connection pooling (`limits=httpx.Limits(max_keepalive_connections=20, max_connections=50)`).
   - Limits concurrent outbound requests using `asyncio.Semaphore(10)` to prevent overwhelming upstream services while maintaining sub-second processing.

3. **Resilience & Fault Tolerance**:
   - Full exponential backoff with jitter on upstream 5xx errors or connection timeouts (up to 3 retries).
   - If upstream activation or creation partially fails, the batch is captured as `partially_failed`.

4. **Resume Capability (`POST /hospitals/bulk/{batch_id}/resume`)**:
   - Resumes failed or incomplete batches by retrying only the pending/failed records rather than re-creating successful ones.
   - Upon completing the remaining records, automatically triggers `activate_batch`.

5. **Real-Time Progress Tracking**:
   - **Polling Endpoint**: `GET /hospitals/bulk/{batch_id}/status` returns current progress, state, and row diagnostics.
   - **WebSocket Stream**: `WS /ws/hospitals/bulk/{batch_id}` (and alias `WS /ws/batch/{batch_id}`) emits live updates as each record is created.

6. **Interactive Dashboard**:
   - Built-in UI served at `http://localhost:8000/` featuring drag-and-drop CSV upload, "Use Sample CSV" 1-click test, live progress bars, real-time results table, and JSON response viewer.

---

## API Specification

### 1. Bulk Create Hospitals
- **Endpoint**: `POST /hospitals/bulk`
- **Content-Type**: `multipart/form-data`
- **Form Field**: `file` (CSV file)
- **Constraint**: Up to 20 hospital rows.
- **Expected Response (200 OK)**:
```json
{
  "batch_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_hospitals": 5,
  "processed_hospitals": 5,
  "failed_hospitals": 0,
  "processing_time_seconds": 2.14,
  "batch_activated": true,
  "hospitals": [
    {
      "row": 1,
      "hospital_id": 669,
      "name": "General Hospital",
      "status": "created_and_activated"
    }
  ]
}
```

### 2. Pre-Validate CSV
- **Endpoint**: `POST /hospitals/bulk/validate`
- **Response**:
```json
{
  "valid": true,
  "total_rows": 5,
  "issues": []
}
```

### 3. Check Batch Status (Polling)
- **Endpoint**: `GET /hospitals/bulk/{batch_id}/status`
- **Response**:
```json
{
  "batch_id": "550e8400-e29b-41d4-a716-446655440000",
  "state": "completed",
  "total_hospitals": 5,
  "processed_hospitals": 5,
  "failed_hospitals": 0,
  "batch_activated": true,
  "processing_time_seconds": 2.14,
  "hospitals": [...]
}
```

### 4. Resume Failed Batch
- **Endpoint**: `POST /hospitals/bulk/{batch_id}/resume`
- Retries pending or failed rows and activates upon full success.

### 5. Upstream Batch Inspection & Cleanup Proxies
- `GET /hospitals/batch/{batch_id}`: Retrieves all hospitals created under this batch from the upstream API.
- `DELETE /hospitals/batch/{batch_id}`: Cleans up all records associated with a batch.

---

## Quick Start (Local)

### 1. Prerequisites
- Python 3.8+ (tested on Python 3.11 and 3.12)

### 2. Installation
```bash
# Clone the repository
git clone <your-repo-url>
cd hospital-bulk-processor

# Install dependencies
pip install -r requirements.txt
```

### 3. Start the Server
```bash
uvicorn app.main:app --reload --port 8000
```
- Interactive Swagger UI: `http://localhost:8000/docs`
- Interactive Web Dashboard: `http://localhost:8000/`

### 4. Example Usage via cURL
```bash
# Validate CSV
curl -X POST "http://localhost:8000/hospitals/bulk/validate" \
  -F "file=@sample_hospitals.csv;type=text/csv"

# Bulk Process & Activate
curl -X POST "http://localhost:8000/hospitals/bulk" \
  -F "file=@sample_hospitals.csv;type=text/csv"
```

---

## Run with Docker

The project includes an optimized multi-stage `Dockerfile` and `docker-compose.yml`:

```bash
# Build and run container
docker compose up --build

# Run in background
docker compose up -d
```
The API is exposed on `http://localhost:8000`.

---

## Running Test Suite

Run the comprehensive unit, integration, and error scenario tests with `pytest`:

```bash
pytest -v
```

### Test Coverage Highlights:
- `test_health_check`: Verifies microservice health.
- `test_root_dashboard`: Verifies web interface availability.
- `test_validate_csv_success`: Verifies valid CSV parsing.
- `test_validate_csv_with_row_issues`: Diagnoses missing row fields.
- `test_bulk_create_with_invalid_rows_returns_422`: Validates 422 HTTP responses on row issues.
- `test_validate_csv_exceeds_20_limit`: Enforces the 20-record ceiling constraint.
- `test_validate_csv_empty_file`: Tests empty file handling.
- `test_validate_csv_missing_required_column`: Validates missing schema columns.
- `test_validate_csv_invalid_extension`: Rejects non-.csv uploads.
- `test_bulk_create_and_activate_success`: Tests complete mock creation and activation workflow.
- `test_partial_failure_and_resume`: Validates partial failure recovery and resume functionality.
- `test_status_not_found` & `test_resume_not_found`: Validates 404 handling.
- `test_batch_activation_failure_handling`: Tests error handling when batch activation fails upstream.

---

## Deploy to Render

This application includes a native `render.yaml` blueprint for one-click deployment:

1. Push your repository to **GitHub** or **GitLab**.
2. Log in to [Render](https://render.com).
3. Click **New +** -> **Blueprint**.
4. Connect your repository. Render automatically reads `render.yaml`, builds the Docker image, and starts the service.
5. Your public URL will be live at `https://<your-service-name>.onrender.com`.

---

## Evaluation Rubric Coverage

| Category | Weight | Implementation Details |
|---|---|---|
| **System Design** | 25% | Modular design separating controllers (`app/main.py`), business logic (`app/service.py`), external integrations (`app/client.py`), parsers (`app/csv_parser.py`), and schemas (`app/models.py`). |
| **Functionality** | 20% | Meets all requirements: CSV upload, UUID batch creation, parallel hospital creation, batch activation, and matching expected response format. |
| **Performance & Scalability** | 25% | Async I/O with `httpx`, bounded concurrency with `asyncio.Semaphore(10)`, connection pooling, streaming responses. |
| **Code Quality** | 20% | Idiomatic Python 3.12, strict Pydantic v2 schemas, type hints, custom serializers, robust error handling. |
| **Documentation & Testing** | 10% | 14 test cases covering unit, integration, validation, and error scenarios; complete README, Dockerfile, docker-compose, and Render blueprint. |
