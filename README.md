# Vendor Settlement System

A scalable event-driven Vendor Settlement System built with FastAPI, Celery, Redis, and PostgreSQL. The system processes vendor payout events, applies settlement rules, schedules payout decisions, handles reprocessing workflows, and maintains complete audit tracking.

---

# Project Overview

This project is designed to simulate a real-world vendor payout settlement workflow where incoming order events are validated, processed, and evaluated through multiple settlement rules before generating payout decisions.

The system supports:

* Event ingestion and processing
* Scheduled payout decisions
* Fraud and manual review handling
* Reprocessing failed or blocked settlements
* Audit logging and decision history
* Asynchronous background workers using Celery
* Redis-based task queue management
* Dockerized deployment setup

---

# Features

* Event-driven architecture
* Vendor payout workflow automation
* Celery workers for asynchronous task processing
* Scheduled settlement processing
* Reprocessing pipeline for failed orders
* Manual override support
* Audit logs for traceability
* PostgreSQL database integration
* Redis queue management
* Docker and Docker Compose support
* Alembic database migrations

---

# Tech Stack

| Technology            | Purpose                       |
| --------------------- | ----------------------------- |
| Python                | Backend language              |
| FastAPI               | REST API framework            |
| PostgreSQL            | Primary database              |
| SQLModel / SQLAlchemy | ORM and database operations   |
| Redis                 | Task broker and caching       |
| Celery                | Background task processing    |
| Alembic               | Database migrations           |
| Docker                | Containerization              |
| Docker Compose        | Multi-container orchestration |
| Uvicorn               | ASGI application server       |

---

# Project Structure

```bash
Vender_Settlement/
│
├── src/
│   ├── DB/                # Database connection and locks
│   ├── Model/             # Database models
│   ├── Routes/            # API routes
│   ├── Schema/            # Request and response schemas
│   ├── Service/           # Business logic layer
│   ├── Tasks/             # Celery task definitions
│   ├── Worker/            # Worker implementations
│   ├── config/            # Logger and app configuration
│   ├── celery_app.py      # Celery initialization
│   └── main.py            # FastAPI entry point
│
├── migrations/            # Alembic migrations
├── logs/                  # Application logs
├── docker-compose.yml     # Docker compose configuration
├── Dockerfile             # Docker image setup
├── requirements.txt       # Python dependencies
└── alembic.ini            # Alembic configuration
```

---

# Workflow

## 1. Event Ingestion

Vendor order events are received through API endpoints.

Example event:

```json
{
  "event_id": "demo-prepaid-001",
  "order_id": "ORD-1001",
  "event_type": "ORDER_UPDATE",
  "payload": {
    "payment_method": "PREPAID",
    "total_amount": 1000,
    "paid_amount": 1000,
    "refund_amount": 0,
    "delivery_status": true,
    "settlement_status": true,
    "kyc_status": true,
    "invoice_status": true,
    "fraud_flag": false
  }
}
```

---

## 2. Rule Engine Processing

The event passes through settlement rules such as:

* Payment validation
* Refund validation
* KYC verification
* Invoice verification
* Fraud checks
* Delivery confirmation

---

## 3. Decision Generation

Based on rule evaluation, the system generates decisions such as:

* RELEASED
* PARTIALLY_RELEASED
* ON_HOLD
* MANUAL_REVIEW
* BLOCKED

---

## 4. Scheduled Processing

Celery Beat schedules delayed payout evaluations and retry mechanisms.

---

## 5. Reprocessing Workflow

Orders that fail or remain blocked can be reprocessed through dedicated APIs.

---

## 6. Audit Logging

Every decision and event update is stored for complete tracking and history management.

---

# API Endpoints

## Event APIs

| Method | Endpoint                            | Description                       |
| ------ | ----------------------------------- | --------------------------------- |
| POST   | `/api/v1/event`                     | Create and process an event       |
| GET    | `/api/v1/payout/{order_id}`         | Get latest payout decision        |
| GET    | `/api/v1/payout/{order_id}/history` | Get payout history                |
| GET    | `/api/v1/review-cases`              | Fetch blocked/manual review cases |
| POST   | `/api/v1/overrides`                 | Override payout decision          |
| POST   | `/api/v1/reprocessing`              | Reprocess an order                |

---

# Requirements

Before running the project, ensure the following are installed:

* Python 3.11+
* PostgreSQL
* Redis
* Docker
* Docker Compose
* Git

---

# Environment Variables

Create a `.env` file inside the project root.

Example:

```env
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/vendor_db
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```
env.docker
```env
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=database
DATABASE_URL=postgresql+asyncpg://postgres:password@host.docker.internal:5432/database
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```
---

# Installation Setup

## 1. Clone Repository

```bash
git clone <your-repository-url>
cd Vender_Settlement
```

---

## 2. Create Virtual Environment

```bash
python -m venv myvenv
```

---

## 3. Activate Virtual Environment

### Windows

```bash
myvenv\Scripts\activate
```

### Linux / Mac

```bash
source myvenv/bin/activate
```

---

## 4. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Database Setup

## Run Alembic Migrations

```bash
alembic upgrade head
```

---

# Running the Project

## 1. Start FastAPI Server

```bash
uvicorn src.main:app --reload
```

Application runs on:

```bash
http://127.0.0.1:8000
```

Swagger Documentation:

```bash
http://127.0.0.1:8000/docs
```

---

## 2. Start Redis Server

If Redis is installed locally:

```bash
redis-server
```

---

## 3. Start Celery Worker

```bash
celery -A src.celery_app.celery worker --loglevel=info
```

---

## 4. Start Celery Beat Scheduler

```bash
celery -A src.celery_app.celery beat --loglevel=info
```

---

# Docker Setup

## Build Containers

```bash
docker-compose build
```

---

## Start Containers

```bash
docker-compose up
```

---

## Run in Detached Mode

```bash
docker-compose up -d
```

---

## Stop Containers

```bash
docker-compose down
```

---

# Logs

Application logs are stored inside:

```bash
logs/
```

Log categories:

* audit logs
* scheduler logs
* decision logs

---

# Settlement Decision Flow

```text
Event Received
      ↓
Validation Layer
      ↓
Rule Engine
      ↓
Fraud / Verification Checks
      ↓
Decision Generation
      ↓
Scheduled Processing
      ↓
Payout Release / Hold / Manual Review
```





# Author
@Aa-ra-dhana

Developed for vendor payout settlement workflow automation using modern backend architecture and asynchronous processing.
