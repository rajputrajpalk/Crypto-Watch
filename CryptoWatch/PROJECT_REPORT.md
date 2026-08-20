# CryptoWatch - Cryptocurrency Portfolio & Alert Tracking System
## Comprehensive Detailed Project Report

---

### Chapter 1 — Introduction

#### 1.1 Project Background
Monitoring cryptocurrency markets requires constant attention due to their high volatility. Traders and enthusiasts need systems that can autonomously track prices, update portfolio valuations, and trigger alerts when specific price thresholds are met. **CryptoWatch** is a Django-based web application designed to demonstrate exactly this functionality through a simulated environment using mock price data and a background execution engine.

#### 1.2 Purpose of the System
The primary purpose of CryptoWatch is to serve as a lightweight, demo-ready architecture for tracking crypto prices, managing a user's portfolio, and processing asynchronous price alerts. It provides a robust RESTful API backend (using Django REST Framework) and a responsive front-end dashboard to visualize holdings, track transactions, and manage active price alerts.

#### 1.3 Scope of the Project
The scope encompasses three primary domains:
- **Portfolio Management:** Tracking asset holdings, calculating total value/cost/PnL based on current simulated market prices, and recording buy/sell transactions.
- **Alert System:** Creating custom price alerts (e.g., "Alert me when BTC goes above $65,000") and triggering them via a background engine.
- **Background Price Engine:** A background thread (`core/price_engine.py`) that periodically ingests mock market data, updates price histories in Redis, and evaluates active alerts without blocking the main web server.

#### 1.4 Document Overview
This document outlines the lifecycle of the CryptoWatch project, detailing its architecture, design decisions, implementation details (Django 5.x + DRF + Redis), repository patterns, limitations, and future scalability plans.

---

### Chapter 2 — Business & Problem Analysis

#### 2.1 Problem Statement
Building a real-time trading or tracking application requires seamless background task execution and fast data retrieval. Standard synchronous web-request lifecycles are insufficient for autonomous price polling. There is a need for an architecture that can handle background processing while still serving a fast, responsive API and dashboard.

#### 2.2 Business Objectives & Goals
- **Demonstrate Background Processing:** Implement a background price engine within a Django application that executes independently of the main web thread.
- **Provide a Robust API Layer:** Use Django REST Framework (DRF) to serve portfolio data, chart timelines, and manage alerts.
- **Showcase High-Performance Storage:** Utilize Redis for fast price history retrieval (via ZSETs) and state management, while providing an in-memory fallback for ease of setup.

#### 2.3 SWOT Analysis
- **Strengths:** Lightweight, easy to set up, zero external API dependencies (uses local mock data), fast Redis integration with a smart fallback mechanism (`repositories_fallback.py`).
- **Weaknesses:** Lacks authentication and multi-user support (hardcoded to `user_id=55`). Background thread running within the Django WSGI process is not ideal for large-scale production.
- **Opportunities:** Can be easily extended to integrate with real crypto exchanges (e.g., Binance, CoinGecko APIs) and Celery for distributed task management.
- **Threats:** Data persistence relies heavily on Redis; falling back to in-memory storage leads to data loss upon server restart.

---

### Chapter 3 — Feasibility Study

#### 3.1 Technical Feasibility
The project utilizes Python 3.10+, Django 5.x, and Django REST Framework, which are industry standards for rapid backend development. The integration of Redis for caching and storage is highly documented via the `redis-py` library. Thus, technical feasibility is very high.

#### 3.2 Economic Feasibility
The application relies entirely on open-source technologies (Python, Redis, SQLite). It does not consume paid external APIs because of the `mock_feed.py`, making it completely free to run and develop locally. Economic feasibility is extremely high.

#### 3.3 Operational Feasibility
Setup is frictionless. By simply installing requirements, running migrations (`python manage.py migrate`), and executing `python manage.py runserver`, the application—and its background engine—starts automatically. The in-memory fallback ensures it runs even if the user hasn't installed Redis.

#### 3.4 Legal & Ethical Feasibility
As a demo application utilizing mock data (`mock_prices.json`), it does not process real financial transactions or sensitive PII. It is entirely feasible legally and ethically.

---

### Chapter 4 — Requirements Engineering / SRS

#### 4.1 User Roles & Elicitation
- **Single Demo User:** The system is hardcoded to serve a single user (`user_id=55`) across all repositories for demonstration purposes.

#### 4.2 Functional Requirements
- **FR1 (Dashboard):** The system shall display a dashboard showing portfolio totals, asset holdings, recent transactions, and a multi-line price history chart for top coins.
- **FR2 (Alerts):** The system shall allow the user to create price alerts specifying the symbol, target price, and direction ("above" or "below").
- **FR3 (Price Engine):** A background engine shall poll `mock_prices.json` at configurable intervals (e.g., every 5 seconds) and log the latest prices.
- **FR4 (Alert Trigger):** The engine shall evaluate pending alerts against the latest prices and mark them as triggered if conditions are met.
- **FR5 (API):** The system shall expose REST APIs (`/api/portfolio/`, `/api/alerts/`) to decouple the frontend from the backend.

#### 4.3 Non-Functional Requirements
- **NFR1 (Performance):** Price history retrieval must be extremely fast, utilizing Redis ZSETs to fetch recent data points in $O(\log(N))$ time.
- **NFR2 (Resilience):** The system must not crash if Redis is unavailable; it must seamlessly fall back to an in-memory dictionary store via `repositories_fallback.py`.
- **NFR3 (Portability):** The application must be runnable locally with standard Python virtual environments without requiring Docker or complex orchestration.

---

### Chapter 5 — Project Methodology (Agile/Scrum)

#### 5.1 Rationale for Agile
An iterative, Agile approach was used to construct the core data models first, followed by the background execution context, and finally the front-end dashboard visualization.

#### 5.2 Development Iterations
- **Phase 1 (Core & Storage):** Django setup, Repository pattern implementation for `PortfolioRepository` and `AlertsRepository` with Redis and Fallback implementations.
- **Phase 2 (Engine):** Implementation of `core/price_engine.py` and `MockPriceFeed` to ingest `mock_prices.json` asynchronously.
- **Phase 3 (API Layer):** DRF Views creation (`PortfolioAPIView`, `AlertsAPIView`) and serializers to map repository data to JSON.
- **Phase 4 (Frontend):** Dashboard UI integration using HTML/CSS/JS and Chart.js to visualize `price_history` and `coin_histories`.

---

### Chapter 6 — System Architecture & HLD

#### 6.1 Architectural Pattern
The application follows a hybrid of the **Model-View-Template (MVT)** pattern and a **Repository Pattern**. It strictly abstracts data storage logic out of Django Models into `repositories.py` to allow seamless switching between Redis and in-memory storage.

#### 6.2 N-Tier Architecture
1. **Client Tier:** Web browser executing vanilla JavaScript `fetch()` calls and rendering charts.
2. **Web Server Tier:** Django 5.x handling HTTP requests, with `api.py` managing REST endpoints and `views.py` serving HTML.
3. **Background Processing Tier:** A daemonized Python thread `PriceEngine` started via `core/apps.py` on Django initialization.
4. **Data Tier:** Redis acting as the primary transactional and timeseries database, utilizing ZSETs, Hashes, and Lists.

#### 6.3 High-Level Data Flow
1. **Engine Flow:** `PriceEngine._run()` polls `MockPriceFeed` $\rightarrow$ saves price history to Redis ZSET $\rightarrow$ checks pending alerts in Redis Hash $\rightarrow$ updates status to triggered if target reached.
2. **Client Flow:** User visits Dashboard $\rightarrow$ AJAX GET `/api/portfolio/` $\rightarrow$ `PortfolioRepository` fetches holdings and histories $\rightarrow$ computes PnL $\rightarrow$ returns JSON $\rightarrow$ Frontend renders chart and tables.

---

### Chapter 7 — Detailed Design / LLD

#### 7.1 API & View Design
Located in `core/api.py`:
- `PortfolioAPIView`: Calls `PortfolioRepository().get_portfolio_snapshot()` returning holdings, totals, price_history, and recent transactions.
- `AlertsAPIView`: Calls `AlertsRepository().list_alerts()`.
- `AlertCreateAPIView`: Validates payload via DRF serializers and calls `AlertsRepository().create_alert()`.
- `ExecuteTradeAPIView`: Allows simulating a buy/sell action via `PortfolioRepository().execute_trade()`.

#### 7.2 Background Engine Design
- **Initialization:** `core/apps.py` hooks into Django's `ready()` method to spawn the `PriceEngine` thread.
- **Execution Loop:** `core/price_engine.py` runs a continuous `while not self._stop_event.is_set():` loop.
- **Safety:** The engine silently catches `UnsupportedAssetWarning` and standard Exceptions to ensure a bad data tick never crashes the main Django server.

#### 7.3 Repository Pattern (The Core Abstraction)
- `_redis_available()` pings Redis on startup.
- **Redis Mode (`repositories.py`):** Uses `RedisHandle` to connect to `localhost:6379`.
- **Fallback Mode (`repositories_fallback.py`):** If Redis is offline, classes like `InMemoryPortfolioRepository` are instantiated, holding state in global Python `dict` and `list` variables.

---

### Chapter 8 — Database Design

#### 8.1 Storage Overview
To handle high-frequency price ticks effectively, the system bypasses SQLite/PostgreSQL in favor of Redis Data Structures.

#### 8.2 Redis Data Structures
1. **Price History (ZSET):** `prices:history:<symbol>`. Score = UTC Epoch timestamp. Member = Price. 
   - *Advantage:* Allows slicing the last 1000 data points natively using `zrevrange` and `zremrangebyrank`.
2. **Portfolio Holdings (Hash):** `portfolio:user:55`. Field = Symbol. Value = JSON string containing `{"quantity": x, "avg_buy_price": y}`.
3. **Alerts (Hash):** `alerts:user:55`. Field = Symbol. Value = JSON string containing target price and trigger status.
4. **Transactions (List):** `transactions:user:55`. Capped list of recent trade payloads (BUY/SELL).

---

### Chapter 9 — Module & Functional Design

#### 9.1 Dashboard Module
Provides a unified view. Fetches data asynchronously. The UI is built to instantly reflect changes when the background engine triggers an alert or updates prices, though it relies on standard polling or manual refresh rather than WebSockets.

#### 9.2 Trading & Portfolio Module
The `execute_trade` function dynamically calculates new `avg_buy_price` using weighted averages on BUY actions and deducts `quantity` on SELL actions, automatically updating the Holdings hash and appending a record to the Transactions list.

#### 9.3 Engine Module
The `PriceEngine` handles the core business logic of comparing the latest simulated price against the `target_price` of active alerts. It handles conditions like 'above', 'increase', 'below', and 'decrease'.

---

### Chapter 10 — Security Architecture

#### 10.1 Authentication & Authorization
Currently, this is a **demo architecture**. Authentication and authorization are intentionally bypassed to simplify demonstration. All repository calls hardcode the user to `self.user_id = 55`.

#### 10.2 Vulnerability Mitigation
- **CSRF Protection:** Django's default CSRF middleware protects the API endpoints (`/api/alerts/create/`, `/api/trade/`).
- **Input Validation:** API payloads are sanitized. For example, `execute_trade` strictly casts `quantity` and `price` to floats and handles `ValueError`.

---

### Chapter 11 — API Design & Documentation

#### 11.1 Endpoints
- **GET `/api/portfolio/`**
  - **Response:** JSON containing `holdings[]`, `totals` (total_cost, total_value, pnl_pct), `price_history[]` (portfolio value timeline), `coin_histories` (per-coin timeline), and `transactions[]`.
- **GET `/api/alerts/`**
  - **Response:** JSON list `alerts[]` containing `symbol`, `target_price`, `is_triggered`, etc.
- **POST `/api/alerts/create/`**
  - **Payload:** `{ "symbol": "BTC", "target_price": 65000, "alert_type": "above" }`
  - **Response:** `201 Created` with success confirmation.
- **POST `/api/trade/`**
  - **Payload:** `{ "symbol": "ETH", "action": "BUY", "quantity": 10 }`
  - **Response:** `200 OK` or `400 Bad Request` if parameters are invalid.

---

### Chapter 12 — UI/UX Design

#### 12.1 Design Philosophy
The dashboard is designed to be a single-page heads-up display reminiscent of a simplified Bloomberg terminal or Binance interface.
- **Simplicity:** Chart, Holdings table, Transactions list, and Alerts are visible concurrently.
- **Visual Cues:** Alerts turn distinct colors (e.g., green/red) based on their `is_triggered` status. PnL displays in green for profit and red for loss.

---

### Chapter 13 — Implementation

#### 13.1 Environment & Tooling
- **Language:** Python 3.10+ (Tested extensively on 3.13)
- **Frameworks:** Django 5.x, Django REST Framework.
- **Dependencies:** `redis-py` (for data access).
- **Frontend:** HTML5, CSS3, Chart.js (via CDN).

#### 13.2 Startup Execution Hook
The application does not require a separate command to start the worker. 
In `core/apps.py`:
```python
def ready(self):
    if os.environ.get('RUN_MAIN', None) != 'true':
        # Spawns thread only once, avoiding the Django auto-reloader double execution.
        engine = PriceEngine()
        engine.start()
```

---

### Chapter 14 — Testing & Quality Assurance

#### 14.1 Testing Strategy
- **Fallback Verification:** The application gracefully detects if Redis is unavailable via the `_redis_available()` ping. It dynamically injects `repositories_fallback.py` classes, logging a fallback warning but preventing a crash.
- **Engine Resilience Testing:** The engine thread wraps its core loop in a `try...except Exception` block, guaranteeing that corrupted JSON in `mock_prices.json` will not cause the thread to exit permanently.

---

### Chapter 15 — Deployment & DevOps

#### 15.1 Local Deployment
1. Initialize virtual environment: `python -m venv .venv`
2. Activate: `.venv\Scripts\activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Migrate local SQLite (for Django defaults): `python manage.py migrate`
5. Run server: `python manage.py runserver`

#### 15.2 Production Considerations
For a real production environment, hooking into `AppConfig.ready()` is anti-pattern because WSGI servers (like Gunicorn/uWSGI) spawn multiple worker processes. This would result in multiple redundant price engines running concurrently. 
**Mandatory Production Change:** Move the `PriceEngine` logic into a separate process managed by **Celery Beat** or an independent Python daemon.

---

### Chapter 16 — Performance & Scalability

#### 16.1 Performance Optimization
- **Redis `ZSET` Complexity:** By using Redis Sorted Sets for `prices:history:<symbol>`, appending prices and fetching the last $N$ prices (via `zrevrange`) operates in $O(\log(N) + M)$ time. This guarantees charting endpoints remain millisecond-fast regardless of historical data size.
- **Data Capping:** `zremrangebyrank` is called continuously to prune histories older than 1000 points, keeping Redis memory footprint minimal.

#### 16.2 Scalability Plan
1. **Task Queue Migration:** Transition from threading to Celery + Redis for distributed background tasks.
2. **WebSocket Integration:** Replace standard HTTP polling on the frontend with Django Channels for pushing real-time price updates.
3. **Multi-Tenancy:** Migrate hardcoded `user_id=55` to standard Django User sessions, utilizing PostgreSQL for permanent portfolio state.

---

### Chapter 17 — Risk Management

#### 17.1 Risk Identification
- **Data Volatility (High Risk):** If Redis is not installed, the app falls back to in-memory storage. All alerts, transactions, and price history will be wiped when the Django server restarts.
- **Concurrency (Medium Risk):** Without distributed locks, multiple concurrent BUY requests could hypothetically cause a race condition in the portfolio hash updating logic.

#### 17.2 Mitigation
- Documenting the explicit need for Redis in `README.md`.
- Scoping the current iteration strictly as a "Demo/Prototype" architecture, clearly demarcating its limitations.

---

### Chapter 18 — Results & Evaluation

#### 18.1 Key Achievements
The project successfully demonstrates a cohesive full-stack application capable of asynchronous task processing without heavy external dependencies. It perfectly simulates a live trading environment. The implementation of the Repository Pattern ensures a clean boundary between business logic and database access.

---

### Chapter 19 — Limitations & Future Scope

#### 19.1 Current Limitations
- Hardcoded to `user_id = 55`.
- No authentication or multi-tenant isolation.
- Relies on mock JSON data instead of live market feeds.

#### 19.2 Future Enhancements
1. **Live Data Integration:** Hook into Binance or CoinGecko public APIs for real price ticks instead of `mock_feed.py`.
2. **Authentication:** Implement JWT-based authentication via DRF SimpleJWT.
3. **Real-time Notifications:** Currently, alerts just change status in the UI. Future versions could trigger actual emails or SMS via Twilio/SendGrid integration.

---

### Chapter 20 — Maintenance & Support

#### 20.1 Routine Maintenance
- Keeping Python dependencies updated via `pip`.
- Ensuring the local Redis instance is running and implementing periodic persistence (`RDB` or `AOF`) so that demo states survive reboots.

---

### Chapter 21 — Conclusion

#### 21.1 Final Summary
**CryptoWatch** is a highly effective demonstration of modern Python backend capabilities. By combining Django 5.x, DRF, and Redis, it creates a responsive, asynchronous environment capable of tracking simulated crypto markets and evaluating user alerts in real-time.

#### 21.2 Value Proposition
It provides a solid architectural foundation for building real-world trading bots or portfolio trackers. Its fallback mechanisms ensure a frictionless developer experience out-of-the-box, while its clean separation of concerns leaves room for enterprise-grade scalability integrations like Celery and WebSockets in the future.

---
### References
- Django 5.x Documentation: https://docs.djangoproject.com/
- Django REST Framework: https://www.django-rest-framework.org/
- Redis Data Structures: https://redis.io/docs/data-types/
- redis-py: https://redis-py.readthedocs.io/
