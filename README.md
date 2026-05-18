# AgentOps Control Plane

A production-grade observability, evaluation, and replay platform for enterprise AI agents.

## Project Vision

Build a comprehensive platform for:
- **Observability**: Monitor agent execution traces and spans
- **Evaluation**: Assess agent performance across metrics
- **Replay**: Debug and replay agent interactions

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Migrations**: Alembic
- **Validation**: Pydantic
- **Testing**: pytest
- **Async**: Uvicorn ASGI server

### Frontend (Phase 2)
- Next.js, Tailwind CSS, shadcn/ui, Recharts

### Infrastructure
- Docker Compose for local development
- GitHub Actions for CI/CD (Phase 2)

## Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Git

### 1. Clone and Setup

```bash
# Clone repository
git clone <repo-url>
cd agentops-control-plane

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows PowerShell
# or: source venv/bin/activate  # Linux/macOS

# Install dependencies
pip install -r backend/requirements.txt
```

### 2. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Update .env with your settings (optional for local dev)
# DB_HOST=localhost
# DB_PORT=5432
# DB_USER=agentops
# DB_PASSWORD=agentops_dev_password
# DB_NAME=agentops_db
```

### 3. Start Services with Docker Compose

```bash
# Start PostgreSQL and FastAPI backend
docker-compose up -d

# Verify containers are running
docker-compose ps

# View logs
docker-compose logs -f backend
docker-compose logs -f postgres
```

The backend will be available at `http://localhost:8000`

### 4. Run the Application (Without Docker)

If running locally without Docker:

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Test the Health Endpoint

```bash
curl http://localhost:8000/health

# Expected response:
# {"status":"ok","database":"connected"}
```

### 6. View API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 7. Run Tests

```bash
cd backend
pytest tests/ -v

# With coverage
pytest tests/ --cov=. --cov-report=html
```

### 8. Run Database Migrations

After the containers are up, apply the Alembic migration to create all tables:

```bash
# From repo root (venv active)
alembic -c backend/alembic.ini upgrade head
```

Inside the running backend container:

```bash
docker-compose exec backend alembic -c backend/alembic.ini upgrade head
```

### 9. Stop Services

```bash
# Stop all containers
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

## Project Structure

```
agentops-control-plane/
├── AGENTS.md                    # Agent documentation
├── README.md                    # This file
├── .env                         # Local environment config
├── .env.example                 # Environment variables template
├── .gitignore                   # Git exclusions
├── Dockerfile                   # Backend Docker image
├── docker-compose.yml           # PostgreSQL + FastAPI backend
├── backend/
│   ├── main.py                  # FastAPI application entry point
│   ├── config.py                # Configuration management (Pydantic Settings)
│   ├── requirements.txt         # Python dependencies
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py            # API endpoints (/health, etc.)
│   ├── models/
│   │   ├── base.py              # SQLAlchemy ORM declarative base
│   │   ├── agent_run.py         # AgentRun model
│   │   ├── trace_span.py        # TraceSpan model
│   │   ├── eval_result.py       # EvalResult model
│   │   ├── prompt_version.py    # PromptVersion model
│   │   └── __init__.py
│   ├── schemas/
│   │   ├── health.py            # HealthResponse schema
│   │   ├── agent_run.py         # AgentRun schemas (Create, Response, Update)
│   │   ├── trace_span.py        # TraceSpan schemas
│   │   ├── eval_result.py       # EvalResult schemas
│   │   ├── prompt_version.py    # PromptVersion schemas
│   │   └── __init__.py
│   ├── db/
│   │   ├── __init__.py
│   │   └── database.py          # SQLAlchemy engine and session factory
│   ├── tests/
│   │   ├── conftest.py          # pytest fixtures and configuration
│   │   ├── test_health.py       # Health endpoint tests
│   │   └── test_models.py       # Model and schema tests
│   └── alembic/                 # Database migrations (Alembic)
├── docs/
└── frontend/                    # Next.js frontend (Phase 2)
```

## Architecture

Following clean architecture principles:

- **API Layer** (`backend/api/`): FastAPI routes and request handling
- **Models Layer** (`backend/models/`): SQLAlchemy ORM models
- **Schemas Layer** (`backend/schemas/`): Pydantic request/response validation
- **Database Layer** (`backend/db/`): Database configuration and utilities
- **Tracing Layer** (`backend/tracing/`): OpenTelemetry instrumentation (phase 2+)
- **Evals Layer** (`backend/evals/`): Evaluation logic (phase 2+)
- **Agents Layer** (`backend/agents/`): Agent business logic (phase 2+)

## Engineering Rules

1. **Small, reviewable changes** - Keep PRs focused and concise
2. **No frontend yet** - Backend only in Phase 1
3. **Avoid unnecessary dependencies** - Keep the stack lean
4. **Tests with code** - Every backend feature includes tests
5. **pytest after changes** - Run test suite before commits
6. **Keep docs updated** - Update README when behavior changes
7. **No hardcoded secrets** - Use environment variables
8. **OpenTelemetry naming** - Use standard trace/span concepts

## Development Workflow

### Adding a Feature
1. Describe the feature in a plan
2. Use the Explore agent to understand existing patterns
3. Create or modify files following architecture
4. Add tests alongside code
5. Run pytest to verify
6. Update README if behavior changes

### Running Tests
```bash
cd backend

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_health.py -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

### Database Migrations (Phase 2)
```bash
cd backend

# Create a new migration
alembic revision --autogenerate -m "migration message"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Tracing SDK

`backend/app/tracing/tracer.py` provides a lightweight SDK for instrumenting
agent workflows directly from Python code.

### Basic usage

```python
from sqlalchemy.orm import Session
from backend.app.tracing import AgentTracer
from backend.schemas.enums import SpanType

def run_agent(db: Session) -> None:
    tracer = AgentTracer(db=db)

    with tracer.start_run(
        "PlannerAgent",
        user_query="Plan a trip to Tokyo",
        model_name="gpt-4o",
    ) as run:
        print(f"trace_id: {run.trace_id}")

        with tracer.start_span(SpanType.LLM_CALL, "outline_trip", input="Tokyo trip") as span:
            result = "Day 1: Shinjuku, Day 2: Shibuya"   # real LLM call goes here
            span.set_output(result)
            span.set_metadata({"model": "gpt-4o", "prompt_tokens": 120})

            # Nested span
            with tracer.start_span(
                SpanType.RETRIEVAL, "web_search",
                input="Tokyo attractions",
                parent_span_id=span.span_id,
            ) as child:
                child.set_output(["Senso-ji", "Shibuya Crossing"])
```

### Supported span types

| Value | Use for |
|-------|---------|
| `SpanType.LLM_CALL` | Language model inference |
| `SpanType.TOOL_CALL` | External tool or function call |
| `SpanType.RETRIEVAL` | Vector search or document fetch |
| `SpanType.EVALUATION` | Scoring or grading step |
| `SpanType.HANDOFF` | Agent-to-agent delegation |
| `SpanType.GUARDRAIL` | Safety or policy check |
| `SpanType.ERROR` | Explicit error capture |
| `SpanType.CUSTOM` | Anything that doesn't fit above |

### Error recording

```python
with tracer.start_run("MyAgent") as run:
    with tracer.start_span(SpanType.TOOL_CALL, "risky_call") as span:
        try:
            result = might_fail()
            span.set_output(result)
        except Exception as exc:
            span.set_error(str(exc))
            raise
```

### What gets recorded automatically

| Field | When |
|-------|------|
| `started_at` | Set by the ORM default when the row is created |
| `completed_at` / `ended_at` | Set on context-manager exit |
| `duration_ms` | Computed from start → end on exit |
| `status` | `"completed"` on clean exit, `"failed"` on exception |
| `error_message` | Populated from the exception or `set_error()` |

## API Endpoints

### Health Check
- **Endpoint**: `GET /health`
- **Description**: System health and database connectivity status
- **Response**: `{"status": "ok", "database": "connected"}`

### Agent Runs & Spans

Create a run, add spans, and inspect them:

```bash
# Create an agent run — returns a unique trace_id
curl -s -X POST http://localhost:8000/api/runs \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "agent_001", "agent_name": "PlannerAgent"}' | jq .

# List all runs
curl -s http://localhost:8000/api/runs | jq .

# Retrieve a specific run by trace_id
TRACE_ID="<trace_id from create response>"
curl -s http://localhost:8000/api/runs/$TRACE_ID | jq .

# Add a span to the run
curl -s -X POST http://localhost:8000/api/runs/$TRACE_ID/spans \
  -H "Content-Type: application/json" \
  -d '{"span_name": "llm_call", "span_type": "llm", "status": "started"}' | jq .

# List all spans for the run
curl -s http://localhost:8000/api/runs/$TRACE_ID/spans | jq .
```

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/runs` | Create a new agent run |
| `GET` | `/api/runs` | List all runs (supports `?skip=&limit=`) |
| `GET` | `/api/runs/{trace_id}` | Get a run by its trace_id |
| `POST` | `/api/runs/{trace_id}/spans` | Add a trace span to a run |
| `GET` | `/api/runs/{trace_id}/spans` | List all spans for a run |

## Data Models

The backend supports the following core data models:

### AgentRun
Tracks the execution of an agent, including input/output, status, and duration.

**Fields:**
- `id` (int): Unique identifier
- `agent_id` (str): Agent identifier
- `agent_name` (str): Human-readable agent name
- `status` (str): pending | running | completed | failed
- `input_data` (str, optional): Serialized input to the agent
- `output_data` (str, optional): Serialized output from the agent
- `error_message` (str, optional): Error details if failed
- `started_at` (datetime): Execution start time
- `completed_at` (datetime, optional): Execution completion time
- `duration_ms` (int, optional): Total execution time in milliseconds

### TraceSpan
Captures individual spans within an agent's execution trace (e.g., tool calls, LLM requests).

**Fields:**
- `id` (int): Unique identifier
- `agent_run_id` (int): Foreign key to AgentRun
- `parent_span_id` (int, optional): Parent span for nested traces
- `span_name` (str): Name of the span
- `span_type` (str): tool | llm | chain | agent | etc.
- `status` (str): started | completed | failed
- `input_data` (str, optional): Span input
- `output_data` (str, optional): Span output
- `error_message` (str, optional): Error details
- `started_at` (datetime): When span started
- `ended_at` (datetime, optional): When span ended
- `duration_ms` (float, optional): Span duration in milliseconds
- `token_count` (int, optional): LLM tokens consumed

### EvalResult
Stores evaluation metrics and results for agent runs.

**Fields:**
- `id` (int): Unique identifier
- `agent_run_id` (int): Foreign key to AgentRun
- `eval_name` (str): Name of the evaluation (e.g., "correctness_check")
- `eval_type` (str): correctness | efficiency | safety | etc.
- `score` (float): Score from 0.0 to 1.0
- `meta_data` (str, optional): JSON with additional evaluation details
- `created_at` (datetime): When evaluation was run

### PromptVersion
Manages versioned prompt templates for reproducibility.

**Fields:**
- `id` (int): Unique identifier
- `prompt_key` (str): Prompt identifier (e.g., "agent_planning")
- `version` (int): Version number
- `content` (str): The prompt template content
- `description` (str, optional): Human-readable description
- `meta_data` (str, optional): JSON with model, temperature, etc.
- `created_at` (datetime): When version was created
- `is_active` (int): Flag for active version

## Troubleshooting

### PostgreSQL Connection Error
```
Error: could not connect to server: No such file or directory
```
**Solution**: Ensure `docker-compose up -d` has completed and database is healthy:
```bash
docker-compose ps
docker-compose logs postgres
```

### Database Already Exists
```
ERROR: database "agentops_db" already exists
```
**Solution**: Clean up Docker volumes:
```bash
docker-compose down -v
docker-compose up -d
```

### Port Already in Use
```
Error: bind: address already in use
```
**Solution**: Change ports in `docker-compose.yml` or kill existing process on port 5432.

## Contributing

1. Create a feature branch
2. Make small, focused changes
3. Write tests for new code
4. Run pytest to verify
5. Update README if needed
6. Submit PR with clear description

## Day 1 Deliverables ✓

- [x] Basic project structure and dependencies
- [x] SQLAlchemy models: AgentRun, TraceSpan, EvalResult, PromptVersion
- [x] Docker Compose configuration (PostgreSQL + FastAPI)
- [x] Health check endpoint
- [x] Core tests
- [x] README with quick start

## Day 2 Deliverables ✓

- [x] Alembic initial migration (all 4 tables + indexes)
- [x] Repository layer (agent_run, trace_span)
- [x] REST API: POST/GET /api/runs and /api/runs/{trace_id}/spans
- [x] Full test coverage for all new endpoints
- [x] README with runnable curl examples

## Later

- Frontend (Next.js)
- Authentication & Authorization
- Evaluation framework
- Replay functionality
- OpenTelemetry integration
- CI/CD automation

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [pytest Documentation](https://docs.pytest.org/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

## License

To be determined

## Contact

For questions or feedback on the AgentOps Control Plane, refer to AGENTS.md for development guidance.
