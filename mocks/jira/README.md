# Mock Jira Integration (MockServer 7.6.0)

This directory provides the test double for Jira Cloud REST API v3 using MockServer 7.6.0.

## Pinned Technology Baseline

In accordance with `docs/architecture/TECHNICAL_STACK.md` and `AGENTS.md`:

- **Mock Engine:** `mockserver/mockserver:7.6.0` (pinned official Docker image).
- **Control API:** Official MockServer REST API:
  - `GET /mockserver/ready`: Deterministic readiness probe.
  - `PUT /mockserver/reset`: Flushes all active expectations and request history.
  - `PUT /mockserver/expectation`: Registers Jira REST v3 request matchers and mock responses.
- **Application Adapter:** `app/integrations/jira/adapter.py`.
  - Strictly read-only (`search_issues`, `get_issue`, `get_issue_comments`, `get_linked_issues`).
  - Zero runtime write capabilities (`POST /rest/api/3/issue`, `PUT /rest/api/3/issue`, etc.).
  - Normalizes Atlassian Document Format (ADF) comments into plain text domain models.

## Running MockServer 7.6.0

### Via Docker Compose
```bash
docker compose -f mocks/jira/docker-compose.yml up -d
```
MockServer will listen on `0.0.0.0:1080`.

### Health Check / Readiness Probe
```bash
curl http://localhost:1080/mockserver/ready
```
Returns HTTP 200 when ready.

## Expectation Loading
Expectations are programmatically registered via `MockServerController.load_expectations(get_jira_mock_expectations())` or using the seed loader in `seed/jira/minimal_loader.py`.
