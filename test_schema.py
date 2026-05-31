from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
# We mock authentication or just fetch schema using Pydantic directly to see serialization

from app.schemas.run_sheet import RunSheetPaginatedResponse, RunSheetListContainer, RunSheet
from datetime import datetime, timezone
import json

dummy_runsheet = {
    "id": 1,
    "arrival_time": datetime(2026, 5, 31, 20, 58, 21, tzinfo=timezone.utc),
    "total_minutes_to_hospital": 5.0,
    "distance_covered": 5.05
}

# Simulate what the endpoint does
resp = RunSheetPaginatedResponse(
    success=True,
    message="Fetched",
    data=RunSheetListContainer(items=[RunSheet(**dummy_runsheet)]),
    totalCount=1
)
print(resp.model_dump_json(by_alias=True))
