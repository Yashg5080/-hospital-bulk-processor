import io
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app, bulk_service

client = TestClient(app)


def setup_function():
    bulk_service.batches.clear()


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_dashboard():
    response = client.get("/")
    assert response.status_code == 200
    assert "Paribus Hospital Bulk Processor" in response.text


def test_validate_csv_success():
    csv_content = "name,address,phone\nGeneral Hospital,123 Main St,555-1234\nCity Clinic,456 Oak Ave,\n"
    response = client.post(
        "/hospitals/bulk/validate",
        files={"file": ("hospitals.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["total_rows"] == 2
    assert data["issues"] == []


def test_validate_csv_with_row_issues():
    # Row 1 is missing address; Row 2 is missing name
    csv_content = "name,address,phone\nGeneral Hospital,,555-1234\n,456 Oak Ave,555-9999\n"
    response = client.post(
        "/hospitals/bulk/validate",
        files={"file": ("hospitals.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert len(data["issues"]) == 2
    assert data["issues"][0]["field"] == "address"
    assert data["issues"][1]["field"] == "name"


def test_bulk_create_with_invalid_rows_returns_422():
    csv_content = "name,address,phone\n,,555-1234\n"
    response = client.post(
        "/hospitals/bulk",
        files={"file": ("hospitals.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")},
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert "issues" in data["detail"]


def test_validate_csv_exceeds_20_limit():
    rows = ["name,address,phone"] + [
        f"Hospital {i},{i} Health Way,555-00{i:02d}" for i in range(1, 22)
    ]
    csv_content = "\n".join(rows)
    response = client.post(
        "/hospitals/bulk",
        files={"file": ("too_many.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")},
    )
    assert response.status_code == 400
    assert "exceeding the maximum limit of 20" in response.json()["detail"]


def test_validate_csv_empty_file():
    response = client.post(
        "/hospitals/bulk/validate",
        files={"file": ("empty.csv", io.BytesIO(b""), "text/csv")},
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_validate_csv_missing_required_column():
    csv_content = "name,phone\nGeneral Hospital,555-1234\n"
    response = client.post(
        "/hospitals/bulk/validate",
        files={"file": ("missing_col.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")},
    )
    assert response.status_code == 400
    assert "missing required columns: address" in response.json()["detail"]


def test_validate_csv_invalid_extension():
    response = client.post(
        "/hospitals/bulk/validate",
        files={"file": ("data.txt", io.BytesIO(b"hello world"), "text/plain")},
    )
    assert response.status_code == 400
    assert "must be a .csv file" in response.json()["detail"]


def test_bulk_create_and_activate_success():
    csv_content = "name,address,phone\nGeneral Hospital,123 Main St,555-1234\nMetro Health,789 Pine Rd,\n"

    with patch.object(
        bulk_service.directory_client,
        "create_hospital",
        new_callable=AsyncMock,
    ) as mock_create, patch.object(
        bulk_service.directory_client,
        "activate_batch",
        new_callable=AsyncMock,
    ) as mock_activate:
        mock_create.side_effect = [
            {"id": 101, "name": "General Hospital", "active": False},
            {"id": 102, "name": "Metro Health", "active": False},
        ]
        mock_activate.return_value = {"activated": True}

        response = client.post(
            "/hospitals/bulk",
            files={"file": ("hospitals.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["total_hospitals"] == 2
        assert body["processed_hospitals"] == 2
        assert body["failed_hospitals"] == 0
        assert body["batch_activated"] is True
        assert body["hospitals"][0]["status"] == "created_and_activated"
        assert body["hospitals"][0]["hospital_id"] == 101
        # Verify error field is omitted when None
        assert "error" not in body["hospitals"][0]
        assert mock_create.call_count == 2
        mock_activate.assert_called_once_with(
            mock_activate.call_args[0][0], body["batch_id"]
        )

        # Test polling status endpoint
        status_res = client.get(f"/hospitals/bulk/{body['batch_id']}/status")
        assert status_res.status_code == 200
        status_data = status_res.json()
        assert status_data["batch_id"] == body["batch_id"]
        assert status_data["state"] == "completed"
        assert status_data["processed_hospitals"] == 2


def test_partial_failure_and_resume():
    csv_content = "name,address,phone\nGeneral Hospital,123 Main St,555-1234\nFailing Hospital,999 Err St,555-9999\n"

    with patch.object(
        bulk_service.directory_client,
        "create_hospital",
        new_callable=AsyncMock,
    ) as mock_create, patch.object(
        bulk_service.directory_client,
        "activate_batch",
        new_callable=AsyncMock,
    ) as mock_activate:
        mock_create.side_effect = [
            {"id": 101, "name": "General Hospital", "active": False},
            RuntimeError("Upstream timeout"),
        ]

        res1 = client.post(
            "/hospitals/bulk",
            files={"file": ("hospitals.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")},
        )
        assert res1.status_code == 200
        data1 = res1.json()
        batch_id = data1["batch_id"]
        assert data1["processed_hospitals"] == 1
        assert data1["failed_hospitals"] == 1
        assert data1["batch_activated"] is False
        mock_activate.assert_not_called()

        # Check status endpoint shows partially_failed
        status_res = client.get(f"/hospitals/bulk/{batch_id}/status")
        assert status_res.status_code == 200
        assert status_res.json()["state"] == "partially_failed"

        mock_create.reset_mock()
        mock_create.side_effect = [
            {"id": 102, "name": "Failing Hospital", "active": False}
        ]
        mock_activate.return_value = {"activated": True}

        res2 = client.post(f"/hospitals/bulk/{batch_id}/resume")
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["processed_hospitals"] == 2
        assert data2["failed_hospitals"] == 0
        assert data2["batch_activated"] is True
        assert mock_create.call_count == 1
        mock_activate.assert_called_once()


def test_status_not_found():
    response = client.get("/hospitals/bulk/non-existent-batch-id/status")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_resume_not_found():
    response = client.post("/hospitals/bulk/non-existent-batch-id/resume")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_batch_activation_failure_handling():
    csv_content = "name,address,phone\nGeneral Hospital,123 Main St,555-1234\n"

    with patch.object(
        bulk_service.directory_client,
        "create_hospital",
        new_callable=AsyncMock,
    ) as mock_create, patch.object(
        bulk_service.directory_client,
        "activate_batch",
        new_callable=AsyncMock,
    ) as mock_activate:
        mock_create.return_value = {"id": 101, "name": "General Hospital", "active": False}
        mock_activate.side_effect = RuntimeError("Upstream 500: Activation failed")

        response = client.post(
            "/hospitals/bulk",
            files={"file": ("hospitals.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["batch_activated"] is False
        assert body["hospitals"][0]["error"] is not None
        assert "Activation failed" in body["hospitals"][0]["error"]
