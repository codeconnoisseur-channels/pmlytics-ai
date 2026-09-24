# Mock Zendesk Integration

This directory provides the test double for Zendesk Customer Support.

## Architecture & Pinned Revision

In accordance with `docs/architecture/TECHNICAL_STACK.md` and `AGENTS.md`:

1. **Pinned Upstream:** `allan-simon/http-zendesk-mock` at commit `704b3ce1e3bac0c21c46b9a850abefd1acf33da2`.
   - Located in `mocks/zendesk/upstream/`.
   - Native Python runtime using `http.server.HTTPServer` (no ASGI / `uvicorn`).
2. **Pocket Compatibility Layer:** `mocks/zendesk/compat_handler.py`.
   - Subclasses upstream `MockHandler` to provide case-insensitive keyword and tag search over `TICKETS_STORE`.
   - Formats search results in standard Zendesk JSON pagination envelopes `{results, count, next_page, previous_page}`.
3. **Application Adapter:** `app/integrations/zendesk/adapter.py`.
   - Strictly read-only runtime access (`search_tickets`, `get_ticket`, `get_ticket_comments`).
   - Zero runtime write capabilities (`PUT` / `POST`).
   - Seed-time ticket creation is isolated to `seed/zendesk/`.

## Running the Mock Server

### Locally via Python
```bash
python -m mocks.zendesk.server
```
Runs on `0.0.0.0:8080` by default.

### Via Docker
```bash
docker build -t pocket-mock-zendesk -f mocks/zendesk/Dockerfile .
docker run -p 8080:8080 pocket-mock-zendesk
```

## Health-Check
```bash
curl -u "mock@pocket.test/token:mock-zendesk-token-pocket" http://localhost:8080/api/v2/tickets.json
```
Returns HTTP 200 with `{"tickets": [...], "count": ...}`.
