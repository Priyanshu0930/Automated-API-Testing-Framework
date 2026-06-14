"""
tests/test_users.py
───────────────────
Complete test suite for the /users endpoint of JSONPlaceholder.

Coverage
────────
  GET    /users          – list all users
  GET    /users/{id}     – get single user
  POST   /users          – create user
  PUT    /users/{id}     – full replace
  PATCH  /users/{id}     – partial update
  DELETE /users/{id}     – delete user
  Negative               – 404s, bad payloads

Run only this file:
    pytest tests/test_users.py -v

Run smoke tests only:
    pytest tests/test_users.py -m smoke -v
"""

import pytest
from utils.logger import get_logger

logger = get_logger(__name__)

# ── Expected JSON schema for a single user object ────────────
USER_SCHEMA_KEYS = {"id", "name", "username", "email", "address", "phone", "website", "company"}
ADDRESS_KEYS     = {"street", "suite", "city", "zipcode", "geo"}
COMPANY_KEYS     = {"name", "catchPhrase", "bs"}


# ─────────────────────────────────────────────────────────────
# Helper / shared assertions
# ─────────────────────────────────────────────────────────────

def assert_valid_user_schema(user: dict) -> None:
    """Assert that a user object contains all expected top-level fields."""
    missing = USER_SCHEMA_KEYS - user.keys()
    assert not missing, f"User object is missing fields: {missing}"

    # Nested schema checks
    assert ADDRESS_KEYS.issubset(user["address"].keys()), \
        f"Address missing fields: {ADDRESS_KEYS - user['address'].keys()}"
    assert COMPANY_KEYS.issubset(user["company"].keys()), \
        f"Company missing fields: {COMPANY_KEYS - user['company'].keys()}"


def assert_response_time(response, threshold_ms: int) -> None:
    """Assert the response arrived within the acceptable time window."""
    elapsed = response.elapsed_ms
    assert elapsed < threshold_ms, (
        f"Response too slow: {elapsed:.1f}ms > threshold {threshold_ms}ms"
    )


# ═════════════════════════════════════════════════════════════
# A. GET Tests
# ═════════════════════════════════════════════════════════════

@pytest.mark.smoke
@pytest.mark.users
class TestGetUsers:
    """GET /users and GET /users/{id}"""

    def test_get_all_users_status_code(self, api_client, response_threshold_ms):
        """GET /users should return HTTP 200."""
        logger.info("Test: GET all users – status code")
        response = api_client.get("/users")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    def test_get_all_users_returns_list(self, api_client):
        """GET /users should return a JSON array."""
        response = api_client.get("/users")
        data = response.json()
        assert isinstance(data, list), "Expected a JSON array"
        assert len(data) > 0, "User list should not be empty"

    def test_get_all_users_count(self, api_client):
        """JSONPlaceholder exposes exactly 10 seed users."""
        response = api_client.get("/users")
        assert len(response.json()) == 10, "Expected 10 seed users"

    def test_get_all_users_response_time(self, api_client, response_threshold_ms):
        """GET /users must respond within the configured threshold."""
        response = api_client.get("/users")
        assert_response_time(response, response_threshold_ms)

    def test_get_all_users_schema(self, api_client):
        """Every user object in the list must match the expected schema."""
        response = api_client.get("/users")
        for user in response.json():
            assert_valid_user_schema(user)

    def test_get_single_user_status_code(self, api_client, users_data):
        """GET /users/{id} should return HTTP 200 for a valid id."""
        user_id = users_data["valid_id"]
        response = api_client.get(f"/users/{user_id}")
        assert response.status_code == 200

    def test_get_single_user_schema(self, api_client, users_data):
        """Single user response must satisfy the full schema."""
        response = api_client.get(f"/users/{users_data['valid_id']}")
        user = response.json()
        assert_valid_user_schema(user)

    def test_get_single_user_id_matches(self, api_client, users_data):
        """Returned user id must equal the requested id."""
        user_id = users_data["valid_id"]
        response = api_client.get(f"/users/{user_id}")
        assert response.json()["id"] == user_id

    def test_get_single_user_response_time(self, api_client, users_data, response_threshold_ms):
        """Single user fetch must be within the response-time threshold."""
        response = api_client.get(f"/users/{users_data['valid_id']}")
        assert_response_time(response, response_threshold_ms)

    def test_get_single_user_content_type(self, api_client, users_data):
        """Response Content-Type should be application/json."""
        response = api_client.get(f"/users/{users_data['valid_id']}")
        assert "application/json" in response.headers.get("Content-Type", "")

    @pytest.mark.parametrize("user_id", [1, 2, 3, 5, 10])
    def test_get_user_parametrized(self, api_client, user_id):
        """Parametrized: each listed user id should return HTTP 200."""
        response = api_client.get(f"/users/{user_id}")
        assert response.status_code == 200, f"Failed for user_id={user_id}"
        assert response.json()["id"] == user_id


# ═════════════════════════════════════════════════════════════
# B. POST Tests
# ═════════════════════════════════════════════════════════════

@pytest.mark.users
class TestPostUsers:
    """POST /users – create a new user."""

    def test_create_user_status_code(self, api_client, users_data):
        """POST /users should return HTTP 201 Created."""
        response = api_client.post("/users", payload=users_data["new_user"])
        assert response.status_code == 201, f"Expected 201, got {response.status_code}"

    def test_create_user_returns_json(self, api_client, users_data):
        """Response body must be valid JSON."""
        response = api_client.post("/users", payload=users_data["new_user"])
        assert response.json() is not None

    def test_create_user_response_contains_id(self, api_client, users_data):
        """New resource must have an auto-assigned 'id' field."""
        response = api_client.post("/users", payload=users_data["new_user"])
        data = response.json()
        assert "id" in data, "Created user must include an 'id'"
        assert isinstance(data["id"], int)

    def test_create_user_data_echoed(self, api_client, users_data):
        """Server should echo back the submitted fields."""
        payload = users_data["new_user"]
        response = api_client.post("/users", payload=payload)
        data = response.json()
        assert data["name"]  == payload["name"],     "Name mismatch"
        assert data["email"] == payload["email"],    "Email mismatch"

    def test_create_user_response_time(self, api_client, users_data, response_threshold_ms):
        """POST must respond within the threshold."""
        response = api_client.post("/users", payload=users_data["new_user"])
        assert_response_time(response, response_threshold_ms)


# ═════════════════════════════════════════════════════════════
# C. PUT Tests
# ═════════════════════════════════════════════════════════════

@pytest.mark.users
class TestPutUsers:
    """PUT /users/{id} – full resource replacement."""

    def test_put_user_status_code(self, api_client, users_data):
        """PUT /users/{id} should return HTTP 200."""
        user_id = users_data["valid_id"]
        response = api_client.put(f"/users/{user_id}", payload=users_data["update_user"])
        assert response.status_code == 200

    def test_put_user_updated_values(self, api_client, users_data):
        """Updated fields must be reflected in the response."""
        user_id  = users_data["valid_id"]
        payload  = users_data["update_user"]
        response = api_client.put(f"/users/{user_id}", payload=payload)
        data     = response.json()
        assert data["name"]     == payload["name"],     "Name not updated"
        assert data["username"] == payload["username"], "Username not updated"
        assert data["email"]    == payload["email"],    "Email not updated"

    def test_put_user_response_time(self, api_client, users_data, response_threshold_ms):
        """PUT must respond within the threshold."""
        user_id  = users_data["valid_id"]
        response = api_client.put(f"/users/{user_id}", payload=users_data["update_user"])
        assert_response_time(response, response_threshold_ms)


# ═════════════════════════════════════════════════════════════
# D. PATCH Tests
# ═════════════════════════════════════════════════════════════

@pytest.mark.users
class TestPatchUsers:
    """PATCH /users/{id} – partial update."""

    def test_patch_user_status_code(self, api_client, users_data):
        """PATCH /users/{id} should return HTTP 200."""
        user_id  = users_data["valid_id"]
        response = api_client.patch(f"/users/{user_id}", payload=users_data["patch_user"])
        assert response.status_code == 200

    def test_patch_user_field_updated(self, api_client, users_data):
        """Only the patched field should reflect the new value."""
        user_id  = users_data["valid_id"]
        payload  = users_data["patch_user"]
        response = api_client.patch(f"/users/{user_id}", payload=payload)
        data     = response.json()
        assert data["email"] == payload["email"], "Patched email not reflected"

    def test_patch_user_other_fields_present(self, api_client, users_data):
        """PATCH must not strip non-updated fields from the response."""
        user_id  = users_data["valid_id"]
        response = api_client.patch(f"/users/{user_id}", payload=users_data["patch_user"])
        data     = response.json()
        # 'id' and 'name' must still be present
        assert "id"   in data, "Field 'id' disappeared after PATCH"
        assert "name" in data, "Field 'name' disappeared after PATCH"


# ═════════════════════════════════════════════════════════════
# E. DELETE Tests
# ═════════════════════════════════════════════════════════════

@pytest.mark.users
class TestDeleteUsers:
    """DELETE /users/{id} – resource deletion."""

    def test_delete_user_status_code(self, api_client, users_data):
        """DELETE /users/{id} should return HTTP 200."""
        user_id  = users_data["valid_id"]
        response = api_client.delete(f"/users/{user_id}")
        assert response.status_code == 200

    def test_delete_user_response_is_empty_or_json(self, api_client, users_data):
        """Response body should be empty JSON object {} or empty."""
        user_id  = users_data["valid_id"]
        response = api_client.delete(f"/users/{user_id}")
        body = response.text.strip()
        # JSONPlaceholder returns "{}"
        assert body in ("{}", ""), f"Unexpected delete response body: {body}"

    def test_delete_user_response_time(self, api_client, users_data, response_threshold_ms):
        """DELETE must respond within the threshold."""
        user_id  = users_data["valid_id"]
        response = api_client.delete(f"/users/{user_id}")
        assert_response_time(response, response_threshold_ms)


# ═════════════════════════════════════════════════════════════
# F. Negative Tests
# ═════════════════════════════════════════════════════════════

@pytest.mark.negative
@pytest.mark.users
class TestUsersNegative:
    """Edge cases and invalid inputs for /users."""

    def test_get_nonexistent_user_returns_404(self, api_client, users_data):
        """GET /users/{invalid_id} should return HTTP 404."""
        invalid_id = users_data["invalid_id"]
        response   = api_client.get(f"/users/{invalid_id}")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"

    def test_get_user_string_id_returns_404(self, api_client):
        """GET /users/not-a-number should return HTTP 404."""
        response = api_client.get("/users/not-a-number")
        assert response.status_code == 404

    def test_put_nonexistent_user(self, api_client, users_data):
        """PUT on a nonexistent user may return 404 or 500 (not 200)."""
        invalid_id = users_data["invalid_id"]
        response   = api_client.put(f"/users/{invalid_id}", payload=users_data["update_user"])
        # JSONPlaceholder returns 500 for unknown ids on PUT; we accept 4xx/5xx
        assert response.status_code not in (200, 201), \
            "Should not return success for nonexistent user"

    def test_delete_nonexistent_user(self, api_client, users_data):
        """DELETE on nonexistent user – JSONPlaceholder still returns 200 (by design)."""
        invalid_id = users_data["invalid_id"]
        response   = api_client.delete(f"/users/{invalid_id}")
        # Document the actual behaviour rather than asserting a specific code
        assert response.status_code in (200, 404), \
            f"Unexpected status {response.status_code} for DELETE nonexistent user"

    def test_post_empty_payload(self, api_client):
        """POST with no payload – server should not crash (2xx or 4xx acceptable)."""
        response = api_client.post("/users", payload={})
        assert response.status_code in range(200, 500), \
            f"Unexpected server error: {response.status_code}"

    @pytest.mark.parametrize("user_id", [0, -1, 99999])
    def test_get_invalid_user_ids(self, api_client, user_id):
        """Parametrized: boundary and invalid ids should not return 200."""
        response = api_client.get(f"/users/{user_id}")
        assert response.status_code != 200, \
            f"user_id={user_id} unexpectedly returned 200"
