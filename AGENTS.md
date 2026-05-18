# AgentOps Control Plane - Available Agents

This document describes the specialized agents available to assist with development on the AgentOps Control Plane project. These agents provide domain-specific guidance aligned with the project's architecture, tech stack, and engineering practices.

## Project Context

**Goal:** Build a production-grade observability, evaluation and replay platform for enterprise AI agents.

**Tech Stack:**
- Backend: FastAPI, Python 3.11+, SQLAlchemy, Alembic, PostgreSQL, Pydantic, pytest
- Frontend (later): Next.js, Tailwind, shadcn/ui, Recharts
- Infra: Docker Compose, GitHub Actions (later)

**Engineering Rules:**
- Make small, reviewable changes
- Do not implement frontend yet
- Avoid unnecessary dependencies
- Prefer clean architecture: api, models, schemas, db, tracing, evals, agents
- Every backend feature must include tests where practical
- Run pytest after code changes
- Keep README and docs updated when behavior changes
- No hardcoded secrets
- Use OpenTelemetry-style naming for trace/span concepts

---

## Available Agents

### Explore Agent
**Purpose:** Fast read-only codebase exploration and Q&A.

**When to use:**
- Understand project structure and existing code
- Answer questions about how features are implemented
- Find relevant files and components
- Review patterns used across the codebase
- Investigate dependencies and relationships

**Usage Example:**
> "Use the Explore agent to find how database models are structured across the project."

---

## Recommended Workflows

### Backend Feature Development
1. **Plan:** Describe the feature you want to build
2. **Explore:** Use the Explore agent to understand existing patterns
3. **Implement:** Create or modify files following established conventions
4. **Test:** Add tests alongside implementation
5. **Verify:** Run pytest to ensure quality

### Database Schema Changes
1. **Design:** Define the new models or schema changes
2. **Explore:** Review existing SQLAlchemy models in `backend/models/`
3. **Implement:** Create/modify models and run Alembic migrations
4. **Test:** Include database tests in test suite
5. **Document:** Update schema documentation if applicable

### API Endpoint Development
1. **Design:** Define the endpoint contract (request/response schemas)
2. **Explore:** Review existing FastAPI routes and schemas in `backend/api/`
3. **Implement:** Create route, schemas, and business logic
4. **Test:** Add endpoint tests covering happy path and error cases
5. **Document:** Update API documentation

### Test Coverage
1. **Implement:** Write your feature code
2. **Test:** Create corresponding tests in `backend/tests/`
3. **Verify:** Run pytest with coverage to identify gaps
4. **Improve:** Add tests for edge cases and error scenarios

---

## Engineering Practices

### Architecture Guidelines
- **API Layer** (`backend/api/`): FastAPI routes and request handling
- **Models Layer** (`backend/models/`): SQLAlchemy ORM models
- **Schemas Layer** (`backend/schemas/`): Pydantic request/response schemas
- **Database Layer** (`backend/db/`): Database configuration and utilities
- **Tracing Layer** (`backend/tracing/`): OpenTelemetry instrumentation
- **Evals Layer** (`backend/evals/`): Evaluation logic and metrics
- **Agents Layer** (`backend/agents/`): Agent-related business logic

### Code Review Checklist
- [ ] Changes are small and focused
- [ ] Tests are included for new functionality
- [ ] pytest passes without errors
- [ ] Code follows existing patterns
- [ ] No hardcoded secrets or config
- [ ] README/docs updated if behavior changed
- [ ] OpenTelemetry naming conventions used (where applicable)

### Testing Standards
- Unit tests for business logic
- Integration tests for API endpoints
- Database tests for schema changes
- Minimum coverage expectations: 70% for new code
- Use pytest fixtures for common test setup

---

## Phase 1 Scope

**Day 1 deliverables (backend skeleton):**
- Basic project structure and dependencies
- Database models and migrations
- Docker Compose configuration
- Health check endpoint
- Core tests

**What NOT to do in Phase 1:**
- Frontend implementation
- User authentication/authorization
- Advanced observability features
- Production deployment configuration

---

## Getting Help

For assistance with:
- **Codebase questions:** Ask the Explore agent
- **Architecture decisions:** Reference the architecture guidelines above
- **Specific implementations:** Ask for help with your specific task
- **Testing strategies:** Ask for test implementation guidance
- **Documentation:** Request help updating README or docs

---

## Contact & Resources

- **Repository:** AgentOps Control Plane
- **Tech Stack Docs:** FastAPI, SQLAlchemy, Pydantic documentation
- **Testing Framework:** pytest
- **Database Migrations:** Alembic
