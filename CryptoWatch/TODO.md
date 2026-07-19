# CryptoWatch - Build Progress

## Current status (high level)
- Django app + dashboard UI: **implemented**
- Mock price feed + background price engine thread: **implemented**
- Redis repositories with in-memory fallback: **implemented**
- DRF API endpoints used by the dashboard: **implemented**

This TODO focuses on the remaining work: correctness, robustness, and completion items (tests + run instructions).

---

## TODO (ordered)

- [ ] Fix dashboard chart to represent **portfolio value over time**
  - Current behavior: `price_history` is taken from a single symbol’s history (first holding) and plotted as “portfolio value chart”.
  - Desired behavior: aggregate each timestamp’s portfolio total value across all holdings.
  - Update backend aggregation logic (portfolio snapshot / history generation).
  - Update frontend label/dataset to match semantics (value vs price).

- [ ] Clarify/standardize time-series storage semantics
  - Confirm that ZSET member/score usage (member=price, score=epoch) supports required queries.
  - If multiple updates share the same epoch (possible), ensure aggregation/query behavior is deterministic.
  - Consider storing history per symbol and separately aggregating, or storing computed portfolio value in its own ZSET.

- [ ] Improve repository initialization & Redis availability check
  - `_redis_available()` currently creates a Redis client and pings; avoid repeated checks during request/engine lifecycle.
  - Add a connection factory / lazy initialization and better exception handling.

- [ ] Production hardening for the background engine
  - Ensure engine can shut down cleanly (daemon thread is currently used; add stop wiring where possible).
  - Avoid duplicate state across autoreload processes (currently guarded via env flag; validate behavior under common dev/server setups).
  - Add minimal logging (replace prints with a logger).

- [ ] Add basic automated tests
  - Repository unit tests (in-memory + redis fallback behavior where feasible).
  - PriceEngine behavior: logs prices and triggers alerts when thresholds are crossed.
  - API tests for `/api/portfolio/`, `/api/alerts/`, `/api/alerts/create/`.

- [ ] Update README with exact endpoint list + example payloads
  - Confirm routes from `core/urls.py` and project urls.
  - Document expected JSON schemas for portfolio snapshot and alert create.

- [ ] Add “known limitations” section
  - Single demo user (`user_id=55`).
  - One alert per symbol (demo behavior).
  - No authentication/authorization.

---

## Notes
- The project includes in-memory fallbacks so it remains runnable even if Redis is not running.
- Dashboard polling refreshes portfolio and alerts after creating an alert.

