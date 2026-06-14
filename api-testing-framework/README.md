# Automated API Testing Framework

A professional, interview-ready REST API test automation framework built with **Python + PyTest**.  
Targets [JSONPlaceholder](https://jsonplaceholder.typicode.com) as the system under test.

---

## Table of Contents

1. [Project Architecture](#project-architecture)
2. [Technology Stack](#technology-stack)
3. [Installation](#installation)
4. [Execution](#execution)
5. [Test Coverage](#test-coverage)
6. [Framework Features](#framework-features)
7. [Testing Strategy](#testing-strategy)
8. [Sample Outputs](#sample-outputs)
9. [CI/CD – GitHub Actions](#cicd--github-actions)
10. [Extending the Framework](#extending-the-framework)

---

## Project Architecture

```
api-testing-framework/
│
├── tests/                      # All test modules
│   ├── __init__.py
│   ├── test_users.py           # /users endpoint – GET, POST, PUT, PATCH, DELETE, Negative
│   └── test_posts.py           # /posts endpoint – GET, POST, PUT, PATCH, DELETE, Negative
│
├── utils/                      # Reusable helper layer
│   ├── __init__.py
│   ├── api_client.py           # Stateful HTTP client wrapping requests.Session
│   └── logger.py               # Centralised logging (console + file)
│
├── data/
│   └── test_data.json          # All test input data – externalised from code
│
├── reports/                    # Auto-generated artefacts (gitignored at runtime)
│   └── .gitkeep
│
├── .github/
│   └── workflows/
│       └── api-tests.yml       # GitHub Actions CI/CD pipeline
│
├── conftest.py                 # Root pytest fixtures (api_client, test_data, …)
├── pytest.ini                  # pytest configuration, markers, log settings
├── requirements.txt            # Pinned dependencies
├── .gitignore
└── README.md
```

### Key Design Decisions

| Decision | Rationale |
|---|---|
| `requests.Session` inside `APIClient` | Reuses TCP connections; shares headers & cookies across calls |
| Session-scoped `api_client` fixture | One client instance for the full run – faster, realistic |
| `test_data.json` | Keeps test logic free of hard-coded values; easy to swap environments |
| Custom `elapsed_ms` attribute | Exposes wall-clock latency without coupling tests to `timeit` |
| Pytest markers | Enables targeted execution: smoke, regression, negative, users, posts |
| `pytest-xdist` | Parallel execution with `-n auto` |
| `pytest-html` | Self-contained single-file HTML report |

---

## Technology Stack

| Package | Version | Purpose |
|---|---|---|
| Python | ≥ 3.10 | Runtime |
| pytest | 7.4.3 | Test runner, fixtures, markers |
| requests | 2.31.0 | HTTP client |
| pytest-html | 4.1.1 | HTML test report generation |
| pytest-xdist | 3.5.0 | Parallel test execution |
| pytest-rerunfailures | 13.0 | Automatic retry on flaky tests |
| jsonschema | 4.20.0 | JSON schema validation helpers |
| python-dotenv | 1.0.0 | Environment variable management |

---

## Installation

### Prerequisites

- Python 3.10 or higher
- pip

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/your-org/api-testing-framework.git
cd api-testing-framework

# 2. Create and activate a virtual environment (recommended)
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 3. Install all dependencies
pip install -r requirements.txt
```

---

## Execution

### Run the full suite (default)

```bash
pytest
```

This uses the settings in `pytest.ini` and outputs:
- Console log in real time
- `reports/report.html` – self-contained HTML report
- `reports/test_run.log` – full DEBUG log file

### Run with explicit HTML report path

```bash
pytest --html=reports/report.html --self-contained-html
```

### Run a specific test module

```bash
pytest tests/test_users.py -v
pytest tests/test_posts.py -v
```

### Run by marker

```bash
pytest -m smoke          # Fast critical-path tests
pytest -m regression     # Full regression suite
pytest -m negative       # Negative / edge-case tests only
pytest -m "users and not negative"   # Users tests, excluding negatives
```

### Run in parallel (requires pytest-xdist)

```bash
pytest -n auto           # Uses all available CPU cores
pytest -n 4              # Exactly 4 workers
```

### Run a single test by name

```bash
pytest tests/test_users.py::TestGetUsers::test_get_all_users_status_code -v
```

### Parametrized tests

```bash
pytest tests/test_users.py -k "parametrized" -v
```

---

## Test Coverage

### `/users` endpoint

| Verb | Scenario | Assertion |
|---|---|---|
| GET | All users | Status 200, list length, schema, response time |
| GET | Single user | Status 200, id match, schema, content-type |
| GET | Parametrized ids (1,2,3,5,10) | Status 200 for each |
| POST | Create user | Status 201, id assigned, payload echoed |
| PUT | Full update | Status 200, all fields updated |
| PATCH | Partial update | Status 200, target field updated, others preserved |
| DELETE | Delete user | Status 200, empty body |
| Negative | Invalid id (9999) | Status 404 |
| Negative | String id | Status 404 |
| Negative | Boundary ids (0, -1, 99999) | Not 200 |
| Negative | Empty payload POST | No 5xx |

### `/posts` endpoint

| Verb | Scenario | Assertion |
|---|---|---|
| GET | All posts | Status 200, list length 100, schema, response time |
| GET | Single post | Status 200, id match, title/body type checks |
| GET | Filter by userId | All returned posts belong to that user |
| GET | Parametrized ids (1,5,10,50,100) | Status 200 for each |
| POST | Create post | Status 201, id assigned, payload echoed |
| POST | Parametrized userIds (1,2,3) | Status 201, userId matches |
| PUT | Full replace | Status 200, all fields updated, id preserved |
| PATCH | Partial update | Status 200, target field updated, others preserved |
| DELETE | Delete post | Status 200, empty body |
| Negative | Invalid id (9999) | Status 404 |
| Negative | Missing fields | No 5xx |
| Negative | Empty payload | No 5xx |
| Negative | Unknown endpoint | Status 404 |
| Negative | Boundary ids (0, -1, 999999) | Not 200 |

---

## Framework Features

### Reusable APIClient (`utils/api_client.py`)

```python
from utils.api_client import APIClient

client = APIClient(base_url="https://jsonplaceholder.typicode.com")

response = client.get("/users/1")
response = client.post("/posts", payload={"title": "Hello", "body": "World", "userId": 1})
response = client.put("/posts/1", payload={...})
response = client.patch("/posts/1", payload={"title": "Updated"})
response = client.delete("/posts/1")

# Response time is always available
print(f"Took {response.elapsed_ms:.1f}ms")
```

Key capabilities:
- All HTTP verbs: GET, POST, PUT, PATCH, DELETE
- Shared `requests.Session` – connection pooling, cookie persistence
- Custom `elapsed_ms` attribute on every response
- Descriptive `RuntimeError` on network failure (no silent swallowing)
- Context manager support (`with APIClient(...) as client:`)

### Logging (`utils/logger.py`)

- Coloured console output (INFO+)
- Full DEBUG log to `reports/framework.log`
- All third-party noise suppressed
- Call `get_logger(__name__)` in any module – no additional setup needed

### Fixtures (`conftest.py`)

| Fixture | Scope | Description |
|---|---|---|
| `api_client` | session | Shared APIClient instance |
| `test_data` | session | Full parsed `test_data.json` |
| `base_url` | session | Base URL string |
| `response_threshold_ms` | session | Max acceptable latency |
| `users_data` | function | `test_data["users"]` shortcut |
| `posts_data` | function | `test_data["posts"]` shortcut |
| `negative_data` | function | `test_data["negative_tests"]` shortcut |

### Test Data Externalisation (`data/test_data.json`)

All test inputs – payloads, expected IDs, field lists, thresholds – live in one JSON file.  
To test against a different environment: change `base_url` in that file, no code changes needed.

---

## Testing Strategy

### Pyramid alignment

```
          ┌─────────────────────┐
          │   E2E / Contract    │  (future: Pact / Dredd)
          ├─────────────────────┤
          │  Integration Tests  │  ← this framework
          │  (HTTP API layer)   │
          ├─────────────────────┤
          │    Unit Tests       │  (utils, helpers)
          └─────────────────────┘
```

### Marker strategy

- **smoke** – subset of critical-path tests; run on every commit and PR
- **regression** – exhaustive suite; runs nightly and on release branches
- **negative** – adversarial inputs; highlights error handling gaps
- **users / posts** – resource-specific; useful when working on one endpoint

### Response-time assertions

Every test class includes at least one response-time assertion using the configurable `response_time_threshold_ms` value (default 3000 ms) from `test_data.json`.

### Parametrized tests

`@pytest.mark.parametrize` is used to cover multiple IDs and user IDs in a single test definition, keeping the suite DRY while maximising data coverage.

---

## Sample Outputs

### Console (pytest -v)

```
tests/test_users.py::TestGetUsers::test_get_all_users_status_code PASSED    [  5%]
tests/test_users.py::TestGetUsers::test_get_all_users_returns_list PASSED    [ 10%]
tests/test_users.py::TestGetUsers::test_get_all_users_count PASSED           [ 15%]
tests/test_posts.py::TestGetPosts::test_get_all_posts_status_code PASSED     [ 20%]
...
================================ 58 passed in 12.34s ================================
```

### HTML Report

Open `reports/report.html` in any browser.  
Contains: test result table, duration, environment info, collapsible log output per test.

### Log file excerpt (`reports/test_run.log`)

```
2025-01-15 10:23:01 [INFO    ] conftest – TEST PASSED – tests/test_users.py::TestGetUsers::test_get_all_users_status_code
2025-01-15 10:23:01 [DEBUG   ] utils.api_client – → GET https://jsonplaceholder.typicode.com/users/1
2025-01-15 10:23:01 [INFO    ] utils.api_client – ← GET https://jsonplaceholder.typicode.com/users/1 | status=200 | time=234.5ms
```

---

## CI/CD – GitHub Actions

The workflow at `.github/workflows/api-tests.yml` provides:

| Job | Trigger | What it does |
|---|---|---|
| `test` (matrix) | push, PR, schedule, manual | Runs full suite on Python 3.10 and 3.11 in parallel |
| `smoke-check` | PR only | Runs `@pytest.mark.smoke` tests as a PR gate |

### Manual run with marker filter

In GitHub → Actions → `API Test Suite` → **Run workflow** → set `marker` input  
(e.g. `smoke`, `negative`, `users`)

### Artefacts

Both HTML reports and log files are uploaded as workflow artefacts (30-day retention for full runs, 7-day for smoke).

---

## Extending the Framework

### Add a new endpoint (e.g. `/comments`)

1. Add test data to `data/test_data.json` under a `"comments"` key
2. Create `tests/test_comments.py` following the same class structure
3. Add a `comments_data` fixture shortcut in `conftest.py`
4. Add a `comments` marker in `pytest.ini` and `conftest.py → pytest_configure`

### Switch to a different base URL / environment

```json
// data/test_data.json
{
  "base_url": "https://your-staging-api.example.com",
  ...
}
```

Or use an environment variable and update `conftest.py` to read `os.getenv("API_BASE_URL", data["base_url"])`.

### Enable retry on flaky tests

Uncomment in `pytest.ini`:

```ini
reruns = 1
reruns_delay = 2
```

---

*Built with ❤️ for interview-ready, production-grade QA automation.*
