# CryptoWatch

A real-time cryptocurrency portfolio tracker, trading simulator, and price alert monitoring system built with **Django 5.x**, **Django REST Framework (DRF)**, and **Redis**.

---

## Key Features

- **Portfolio Valuation & P&L**: Tracks holdings, calculates weighted average buy prices, current market values, and net profit/loss in real-time.
- **Interactive Timeseries Visualizer**: Interactive Chart.js charts with duration controls, individual coin filters, and bullish/bearish trend indicators.
- **Instant Order Simulation**: Place simulated `BUY` and `SELL` market orders with instant portfolio balance updates.
- **Background Price Engine**: Asynchronous worker thread that continuously generates simulated market price drift and evaluates price threshold alerts without blocking web requests.
- **Resilient Dual Storage Architecture**: Seamlessly uses **Redis** (Hashes, Sorted Sets, Lists) for high-performance state, with an automatic, thread-safe in-memory fallback when Redis is offline.

---

## Quickstart

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.13)
- Redis (optional, automatically falls back to in-memory store if not installed)

### 2. Installation
```bash
# Clone repository
git clone https://github.com/rajputrajpalk/Crypto-Watch.git
cd Crypto-Watch

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Run Migrations & Start Server
```bash
# Apply Django migrations
python manage.py migrate

# Start development server
python manage.py runserver
```

Open your browser at `http://127.0.0.1:8000/` to access the trading terminal.

---

## REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/portfolio/` | Returns portfolio totals, holdings, price history, and recent transactions |
| `POST` | `/api/trade/` | Executes a `BUY` or `SELL` order (`symbol`, `action`, `quantity`, `price`) |
| `GET` | `/api/alerts/` | Lists all active and triggered price alerts |
| `POST` | `/api/alerts/create/` | Creates a price threshold alert (`symbol`, `target_price`, `alert_type`) |
| `POST` | `/api/alerts/deactivate/` | Dismisses/removes an alert (`symbol`) |
| `GET` | `/api/live-prices/` | Fetches the latest simulated price tick across all tracked coins |

---

## Running Tests

Run the test suite with Django's test runner:
```bash
python manage.py test
```

---

## Project Structure

```
CryptoWatch/
├── CryptoWatch/         # Django project settings and root routing
├── core/                # Main application package
│   ├── domain/          # Domain entities, value objects, and custom exceptions
│   ├── templates/       # Terminal dashboard UI template
│   ├── api.py           # REST API endpoints (DRF APIViews)
│   ├── apps.py          # App configuration and worker lifecycle
│   ├── forms.py         # Form validation
│   ├── mock_feed.py     # Simulated price feed provider
│   ├── price_engine.py  # Asynchronous background worker
│   ├── repositories.py  # Unified Redis & In-Memory repository layer
│   ├── serializers.py   # DRF request & response serializers
│   ├── tests.py         # Unit & integration test suite
│   ├── urls.py          # Application URL configuration
│   ├── validators.py    # Input sanitation and validation helpers
│   └── views.py         # Server-rendered frontend views
├── static/              # Stylesheets and frontend assets
├── mock_prices.json     # Base pricing configuration
├── requirements.txt     # Python package dependencies
└── manage.py            # Django CLI management entrypoint
```

---

## License
MIT
