# CryptoWatch

A small Django + DRF app that tracks mock crypto prices, manages a demo portfolio, and triggers price alerts via a background price engine.

## Prerequisites
- Python 3.10+ recommended (tested here with 3.13)
- Redis (optional but recommended for full functionality)

## Setup
```bash
# 1) Create venv
python -m venv .venv

# 2) Activate
.venv\Scripts\activate

# 3) Install deps
pip install -r requirements.txt
```

## Redis (recommended)
If Redis is running locally:
- Host: `localhost`
- Port: `6379`

Start Redis (Windows):
- Install Redis, then run `redis-server`.

If Redis is NOT running:
- The server will still start, but portfolio/alerts may be empty because Redis-backed repositories will fall back to in-memory.

## Run (manual)

### 1) Start Redis (optional)
This app will **run even if Redis is not running**, but Redis-backed repositories will fall back to in-memory state.

If you want the “real” Redis storage behavior:
- Windows: start `redis-server` (after installing Redis).
- Default host/port used by the app:
  - `localhost:6379`

### 2) Run migrations
```bash
python manage.py migrate
```

### 3) Start the server
```bash
python manage.py runserver
```

### 4) Open the UI
- Dashboard: http://127.0.0.1:8000/

The dashboard shows:
- Portfolio totals and holdings
- A chart (portfolio value chart currently uses `price_history` returned by the backend)
- Active alerts + a form to create alerts

### 5) Use the API endpoints (useful for debugging)
Base path is your server URL (example: `http://127.0.0.1:8000/`).

- **GET** `/api/portfolio/`
  - Returns portfolio snapshot:
    - `holdings[]`
    - `totals`
    - `price_history[]`

- **GET** `/api/alerts/`
  - Returns list of alerts:
    - `alerts[]`

- **POST** `/api/alerts/create/`
  - Create an alert.
  - Content-Type: `application/json`
  - Example payload:
    ```json
    {
      "symbol": "BTC",
      "target_price": 65000,
      "alert_type": "above"
    }
    ```

## Project behavior (what is running)
- On Django startup, `core/apps.py` starts a **background price engine thread**.
- The engine periodically:
  1) Reads mock prices from `mock_prices.json`
  2) Logs per-symbol price history (Redis ZSET when available, otherwise in-memory)
  3) Checks alerts and marks them as triggered when thresholds are crossed

## Notes / limitations
- This is a demo architecture (no authentication/authorization).
- Current implementation stores demo state for a single user id (`user_id=55`).
- The app state is backed by Redis (when available) with an in-memory fallback.
- Production would require proper user auth and more robust persistence/testing.


