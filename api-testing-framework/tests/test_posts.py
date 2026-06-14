"""
tests/test_posts.py
───────────────────
Complete test suite for the /posts endpoint of JSONPlaceholder.

Coverage
────────
  GET    /posts          – list all posts
  GET    /posts/{id}     – get single post
  GET    /posts?userId=  – filter posts by user
  POST   /posts          – create post
  PUT    /posts/{id}     – full replace
  PATCH  /posts/{id}     – partial update
  DELETE /posts/{id}     – delete post
  Negative               – 404s, bad payloads, missing fields

Run only this file:
    pytest tests/test_posts.py -v

Run smoke tests only:
    pytest tests/test_posts.py -m smoke -v
"""

import pytest
from utils.logger import get_logger

logger = get_logger(__name__)

# ── Expected JSON schema for a single post object ────────────
POST_SCHEMA_KEYS = {"userId", "id", "title", "body"}


# ─────────────────────────────────────────────────────────────
# Helper / shared assertions
# ─────────────────────────────────────────────────────────────

def assert_valid_post_schema(post: dict) -> None:
    """Assert that a post object contains all expected fields."""
    missing = POST_SCHEMA_KEYS - post.keys()
    assert not missing, f"Post object is missing fields: {missing}"


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
@pytest.mark.posts
class TestGetPosts:
    """GET /posts and GET /posts/{id}"""

    def test_get_all_posts_status_code(self, api_client):
        """GET /posts should return HTTP 200."""
        logger.info("Test: GET all posts – status code")
        response = api_client.get("/posts")
        assert response.status_code == 200

    def test_get_all_posts_returns_list(self, api_client):
        """GET /posts should return a JSON array."""
        response = api_client.get("/posts")
        data = response.json()
        assert isinstance(data, list), "Expected a JSON array"
        assert len(data) > 0, "Posts list should not be empty"

    def test_get_all_posts_count(self, api_client):
        """JSONPlaceholder exposes exactly 100 seed posts."""
        response = api_client.get("/posts")
        assert len(response.json()) == 100, "Expected 100 seed posts"

    def test_get_all_posts_response_time(self, api_client, response_threshold_ms):
        """GET /posts must respond within the configured threshold."""
        response = api_client.get("/posts")
        assert_response_time(response, response_threshold_ms)

    def test_get_all_posts_schema(self, api_client):
        """Every post in the list must match the expected schema."""
        response = api_client.get("/posts")
        for post in response.json():
            assert_valid_post_schema(post)

    def test_get_single_post_status_code(self, api_client, posts_data):
        """GET /posts/{id} should return HTTP 200 for a valid id."""
        response = api_client.get(f"/posts/{posts_data['valid_id']}")
        assert response.status_code == 200

    def test_get_single_post_schema(self, api_client, posts_data):
        """Single post response must satisfy the full schema."""
        response = api_client.get(f"/posts/{posts_data['valid_id']}")
        assert_valid_post_schema(response.json())

    def test_get_single_post_id_matches(self, api_client, posts_data):
        """Returned post id must equal the requested id."""
        post_id  = posts_data["valid_id"]
        response = api_client.get(f"/posts/{post_id}")
        assert response.json()["id"] == post_id

    def test_get_single_post_title_is_string(self, api_client, posts_data):
        """Post title must be a non-empty string."""
        response = api_client.get(f"/posts/{posts_data['valid_id']}")
        title = response.json().get("title", "")
        assert isinstance(title, str) and title.strip(), "Title should be a non-empty string"

    def test_get_single_post_body_is_string(self, api_client, posts_data):
        """Post body must be a non-empty string."""
        response = api_client.get(f"/posts/{posts_data['valid_id']}")
        body = response.json().get("body", "")
        assert isinstance(body, str) and body.strip(), "Body should be a non-empty string"

    def test_get_single_post_response_time(self, api_client, posts_data, response_threshold_ms):
        """Single post fetch must be within the response-time threshold."""
        response = api_client.get(f"/posts/{posts_data['valid_id']}")
        assert_response_time(response, response_threshold_ms)

    def test_get_single_post_content_type(self, api_client, posts_data):
        """Response Content-Type should be application/json."""
        response = api_client.get(f"/posts/{posts_data['valid_id']}")
        assert "application/json" in response.headers.get("Content-Type", "")

    def test_get_posts_filter_by_user_id(self, api_client):
        """GET /posts?userId=1 should return only posts belonging to user 1."""
        response = api_client.get("/posts", params={"userId": 1})
        assert response.status_code == 200
        posts = response.json()
        assert len(posts) > 0, "Expected at least one post for userId=1"
        for post in posts:
            assert post["userId"] == 1, f"Post {post['id']} does not belong to userId=1"

    @pytest.mark.parametrize("post_id", [1, 5, 10, 50, 100])
    def test_get_post_parametrized(self, api_client, post_id):
        """Parametrized: each listed post id should return HTTP 200."""
        response = api_client.get(f"/posts/{post_id}")
        assert response.status_code == 200, f"Failed for post_id={post_id}"
        assert response.json()["id"] == post_id


# ═════════════════════════════════════════════════════════════
# B. POST Tests
# ═════════════════════════════════════════════════════════════

@pytest.mark.posts
class TestPostPosts:
    """POST /posts – create a new post."""

    def test_create_post_status_code(self, api_client, posts_data):
        """POST /posts should return HTTP 201 Created."""
        response = api_client.post("/posts", payload=posts_data["new_post"])
        assert response.status_code == 201, f"Expected 201, got {response.status_code}"

    def test_create_post_returns_json(self, api_client, posts_data):
        """Response body must be valid JSON."""
        response = api_client.post("/posts", payload=posts_data["new_post"])
        assert response.json() is not None

    def test_create_post_response_contains_id(self, api_client, posts_data):
        """Newly created post must have an auto-assigned 'id'."""
        response = api_client.post("/posts", payload=posts_data["new_post"])
        data = response.json()
        assert "id" in data, "Created post must include an 'id'"
        assert isinstance(data["id"], int)

    def test_create_post_data_echoed(self, api_client, posts_data):
        """Server should echo back the submitted payload fields."""
        payload  = posts_data["new_post"]
        response = api_client.post("/posts", payload=payload)
        data     = response.json()
        assert data["title"]  == payload["title"],  "Title mismatch"
        assert data["body"]   == payload["body"],   "Body mismatch"
        assert data["userId"] == payload["userId"], "UserId mismatch"

    def test_create_post_response_time(self, api_client, posts_data, response_threshold_ms):
        """POST must respond within the threshold."""
        response = api_client.post("/posts", payload=posts_data["new_post"])
        assert_response_time(response, response_threshold_ms)

    @pytest.mark.parametrize("user_id", [1, 2, 3])
    def test_create_post_for_different_users(self, api_client, posts_data, user_id):
        """Parametrized: create a post on behalf of different user ids."""
        payload = {**posts_data["new_post"], "userId": user_id}
        response = api_client.post("/posts", payload=payload)
        assert response.status_code == 201
        assert response.json()["userId"] == user_id


# ═════════════════════════════════════════════════════════════
# C. PUT Tests
# ═════════════════════════════════════════════════════════════

@pytest.mark.posts
class TestPutPosts:
    """PUT /posts/{id} – full resource replacement."""

    def test_put_post_status_code(self, api_client, posts_data):
        """PUT /posts/{id} should return HTTP 200."""
        post_id  = posts_data["valid_id"]
        response = api_client.put(f"/posts/{post_id}", payload=posts_data["update_post"])
        assert response.status_code == 200

    def test_put_post_updated_values(self, api_client, posts_data):
        """All submitted fields must be reflected in the response."""
        post_id  = posts_data["valid_id"]
        payload  = posts_data["update_post"]
        response = api_client.put(f"/posts/{post_id}", payload=payload)
        data     = response.json()
        assert data["title"]  == payload["title"],  "Title not updated"
        assert data["body"]   == payload["body"],   "Body not updated"
        assert data["userId"] == payload["userId"], "UserId not updated"

    def test_put_post_response_time(self, api_client, posts_data, response_threshold_ms):
        """PUT must respond within the threshold."""
        post_id  = posts_data["valid_id"]
        response = api_client.put(f"/posts/{post_id}", payload=posts_data["update_post"])
        assert_response_time(response, response_threshold_ms)

    def test_put_post_id_preserved(self, api_client, posts_data):
        """PUT must not change the resource's id."""
        post_id  = posts_data["valid_id"]
        response = api_client.put(f"/posts/{post_id}", payload=posts_data["update_post"])
        assert response.json()["id"] == post_id, "Post id changed after PUT"


# ═════════════════════════════════════════════════════════════
# D. PATCH Tests
# ═════════════════════════════════════════════════════════════

@pytest.mark.posts
class TestPatchPosts:
    """PATCH /posts/{id} – partial update."""

    def test_patch_post_status_code(self, api_client, posts_data):
        """PATCH /posts/{id} should return HTTP 200."""
        post_id  = posts_data["valid_id"]
        response = api_client.patch(f"/posts/{post_id}", payload=posts_data["patch_post"])
        assert response.status_code == 200

    def test_patch_post_field_updated(self, api_client, posts_data):
        """Only the patched field must reflect the new value."""
        post_id  = posts_data["valid_id"]
        payload  = posts_data["patch_post"]
        response = api_client.patch(f"/posts/{post_id}", payload=payload)
        assert response.json()["title"] == payload["title"], "Patched title not reflected"

    def test_patch_post_other_fields_preserved(self, api_client, posts_data):
        """PATCH must not strip non-patched fields."""
        post_id  = posts_data["valid_id"]
        response = api_client.patch(f"/posts/{post_id}", payload=posts_data["patch_post"])
        data     = response.json()
        assert "id"     in data, "Field 'id' missing after PATCH"
        assert "userId" in data, "Field 'userId' missing after PATCH"
        assert "body"   in data, "Field 'body' missing after PATCH"

    def test_patch_post_response_time(self, api_client, posts_data, response_threshold_ms):
        """PATCH must respond within the threshold."""
        post_id  = posts_data["valid_id"]
        response = api_client.patch(f"/posts/{post_id}", payload=posts_data["patch_post"])
        assert_response_time(response, response_threshold_ms)


# ═════════════════════════════════════════════════════════════
# E. DELETE Tests
# ═════════════════════════════════════════════════════════════

@pytest.mark.posts
class TestDeletePosts:
    """DELETE /posts/{id} – resource deletion."""

    def test_delete_post_status_code(self, api_client, posts_data):
        """DELETE /posts/{id} should return HTTP 200."""
        post_id  = posts_data["valid_id"]
        response = api_client.delete(f"/posts/{post_id}")
        assert response.status_code == 200

    def test_delete_post_response_body(self, api_client, posts_data):
        """Response body should be empty JSON object {} or empty."""
        post_id  = posts_data["valid_id"]
        response = api_client.delete(f"/posts/{post_id}")
        body = response.text.strip()
        assert body in ("{}", ""), f"Unexpected delete response body: {body}"

    def test_delete_post_response_time(self, api_client, posts_data, response_threshold_ms):
        """DELETE must respond within the threshold."""
        post_id  = posts_data["valid_id"]
        response = api_client.delete(f"/posts/{post_id}")
        assert_response_time(response, response_threshold_ms)


# ═════════════════════════════════════════════════════════════
# F. Negative Tests
# ═════════════════════════════════════════════════════════════

@pytest.mark.negative
@pytest.mark.posts
class TestPostsNegative:
    """Edge cases and invalid inputs for /posts."""

    def test_get_nonexistent_post_returns_404(self, api_client, posts_data):
        """GET /posts/{invalid_id} should return HTTP 404."""
        invalid_id = posts_data["invalid_id"]
        response   = api_client.get(f"/posts/{invalid_id}")
        assert response.status_code == 404

    def test_get_post_string_id_returns_404(self, api_client):
        """GET /posts/not-a-number should return HTTP 404."""
        response = api_client.get("/posts/not-a-number")
        assert response.status_code == 404

    def test_post_missing_required_fields(self, api_client, negative_data):
        """POST with only a title (missing body) – should not crash."""
        payload  = negative_data["missing_fields_post"]
        response = api_client.post("/posts", payload=payload)
        # JSONPlaceholder is lenient; we assert it doesn't 5xx
        assert response.status_code < 500, "Server should not 500 on missing fields"

    def test_post_empty_payload(self, api_client):
        """POST with an empty object should return a non-5xx status."""
        response = api_client.post("/posts", payload={})
        assert response.status_code < 500

    def test_post_null_payload(self, api_client):
        """POST with no payload (None) should return a non-5xx status."""
        response = api_client.post("/posts", payload=None)
        assert response.status_code < 500

    def test_get_invalid_endpoint(self, api_client):
        """GET on a completely unknown path should return 404."""
        response = api_client.get("/nonexistent-endpoint")
        assert response.status_code == 404

    @pytest.mark.parametrize("post_id", [0, -1, 999999])
    def test_get_boundary_post_ids(self, api_client, post_id):
        """Parametrized: boundary ids should not return 200."""
        response = api_client.get(f"/posts/{post_id}")
        assert response.status_code != 200, \
            f"post_id={post_id} unexpectedly returned 200"
