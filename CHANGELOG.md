# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-09-30

### Added
- Initial open-source release of `kodekloud-mcp`.
- **MCP Tools**:
  - `get_course_progress`: Check completion percentage, completed vs total labs, and last active timestamp.
  - `list_enrolled_courses`: View enrolled course catalog with category and progress state.
  - `get_course_outline`: Retrieve structured course modules, lessons, lab flags, and status.
  - `get_active_labs`: Monitor running, paused, and stopped lab instances with remaining lease times.
  - `get_certifications`: Track target certifications (CKA, CKAD, CKS, Terraform, etc.) and readiness scores.
  - `get_learning_summary`: Compact digest with streaks, total study hours, and AI-driven next suggested lesson.
  - `get_engineer_task`: Fetch current active assigned task/ticket scenario and target servers on KodeKloud Engineer.
  - `get_engineer_profile`: Retrieve engineering role, XP, leaderboard rank, and success rate.
  - `list_engineer_history`: Inspect completed, failed, and historical task records.
  - `start_lab` (write tool): Launch an interactive lab environment (disabled by default).
  - `stop_lab` (write tool): Terminate an active lab session (disabled by default).
- **MCP Prompts**:
  - `study_plan`: Generates a personalized weekly study plan towards a certification or career goal by orchestrating tool calls.
  - `troubleshoot_engineer_task`: Acts as a Senior DevOps Tech Lead mentor guiding investigation and debugging without spoiling solutions.
- **Transports**:
  - `stdio` (default) for local desktop clients (Claude Desktop, Claude Code, Cursor).
  - `sse` / `streamable-http` for remote and connector clients (ChatGPT, remote MCP agents).
- **Security & Resilience**:
  - Automatic detection of Bearer JWT vs Cookie header formats.
  - Zero-credential leakage: automated redaction from logs and error messages.
  - Read-only by default protection via `KODEKLOUD_ENABLE_WRITE_TOOLS=false`.
  - Exponential backoff retry handler for HTTP 429 rate limits.
  - In-memory async-safe TTL caching (default 60s).
  - Schema drift tolerance preventing crashes on upstream JSON variations.
  - Clear, user-friendly guidance for expired sessions (401/403).
- **Packaging & Testing**:
  - Standalone mock mode (`KODEKLOUD_USE_MOCK=true`) enabled by default with realistic sample data.
  - Isolated client endpoint table in `kodekloud_client.py` for seamless upstream endpoint mapping.
  - Full test suite covering mock mode, `httpx.MockTransport` real-mode simulation, edge errors, and caching.
  - Non-root `Dockerfile` and `docker-compose.yml`.
  - GitHub Actions CI workflow for linting, typing, and pytest.
