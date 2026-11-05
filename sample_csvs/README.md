# Sample CSV Test Files

This directory provides diverse sample CSV files to thoroughly test the **Hospital Bulk Processing System** against all constraints, edge cases, and validation rules.

---

## File Catalog

| File | Scenario Tested | Record Count | Expected Result |
|---|---|:---:|---|
| [`01_valid_standard.csv`](./01_valid_standard.csv) | Standard valid batch with mixed phone numbers (some present, some omitted). | 5 | **200 OK** (`created_and_activated: true`) |
| [`02_valid_boundary_20_records.csv`](./02_valid_boundary_20_records.csv) | Upper boundary testing (exactly 20 hospitals). | 20 | **200 OK** (All 20 created and activated) |
| [`03_valid_quoted_addresses.csv`](./03_valid_quoted_addresses.csv) | RFC 4180 compliance: commas inside quotes (e.g. `"Suite 400, Bldg B"`), special characters (`&`, `'`), and UTF-8 accents (`L'Hôpital Saint-Michel`). | 3 | **200 OK** (Parsed cleanly with commas preserved) |
| [`04_invalid_exceeds_20_limit.csv`](./04_invalid_exceeds_20_limit.csv) | Strict technical constraint enforcement (> 20 records). | 25 | **400 Bad Request** (`"CSV contains 25 hospitals, exceeding the maximum limit of 20."`) |
| [`05_invalid_missing_fields.csv`](./05_invalid_missing_fields.csv) | Row-level data validation (Row 2 missing address, Row 3 missing name). | 3 | **422 Unprocessable Entity** on `/hospitals/bulk`<br>**200 OK** (`valid: false, issues: [...]`) on `/hospitals/bulk/validate` |
| [`06_invalid_missing_headers.csv`](./06_invalid_missing_headers.csv) | Schema validation (missing required `address` header). | 2 | **400 Bad Request** (`"CSV is missing required columns: address."`) |

---

## Quick Testing via cURL

```bash
# 1. Test Standard Valid Batch
curl -X POST "https://paribus-hospital-bulk-processor-mx6v.onrender.com/hospitals/bulk" \
  -F "file=@sample_csvs/01_valid_standard.csv;type=text/csv"

# 2. Test 20-Record Boundary
curl -X POST "https://paribus-hospital-bulk-processor-mx6v.onrender.com/hospitals/bulk" \
  -F "file=@sample_csvs/02_valid_boundary_20_records.csv;type=text/csv"

# 3. Test Exceeding Limit (Expect 400)
curl -X POST "https://paribus-hospital-bulk-processor-mx6v.onrender.com/hospitals/bulk" \
  -F "file=@sample_csvs/04_invalid_exceeds_20_limit.csv;type=text/csv"

# 4. Test Pre-Validation Endpoint with Invalid Fields (Expect issues list)
curl -X POST "https://paribus-hospital-bulk-processor-mx6v.onrender.com/hospitals/bulk/validate" \
  -F "file=@sample_csvs/05_invalid_missing_fields.csv;type=text/csv"
```
