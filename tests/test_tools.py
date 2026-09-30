"""Tests for FastMCP tool and prompt registrations and invocations."""

from typing import Any

import pytest


@pytest.mark.asyncio
async def test_tool_listing_read_only(mock_server: Any) -> None:
    """Verify that only the 6 read tools are exposed by default."""
    tools = await mock_server.list_tools()
    tool_names = [t.name for t in tools]

    expected_read_tools = [
        "get_course_progress",
        "list_enrolled_courses",
        "get_course_outline",
        "get_active_labs",
        "get_certifications",
        "get_learning_summary",
        "get_engineer_task",
        "get_engineer_profile",
        "list_engineer_history",
    ]
    for expected in expected_read_tools:
        assert expected in tool_names

    # Write tools must NOT be present by default
    assert "start_lab" not in tool_names
    assert "stop_lab" not in tool_names


@pytest.mark.asyncio
async def test_tool_listing_write_enabled(mock_write_server: Any) -> None:
    """Verify that write tools are exposed when KODEKLOUD_ENABLE_WRITE_TOOLS=true."""
    tools = await mock_write_server.list_tools()
    tool_names = [t.name for t in tools]

    assert "start_lab" in tool_names
    assert "stop_lab" in tool_names


def _get_tool_result_text(result: Any) -> str:
    """Helper to extract text content across MCP SDK return types."""
    if hasattr(result, "is_error"):
        assert not result.is_error
        return result.content[0].text
    if isinstance(result, tuple) and len(result) >= 1:
        content_list = result[0]
        if hasattr(content_list[0], "text"):
            return content_list[0].text
        return str(content_list[0])
    if isinstance(result, list) and len(result) >= 1:
        return getattr(result[0], "text", str(result[0]))
    return str(result)


@pytest.mark.asyncio
async def test_call_get_course_progress(mock_server: Any) -> None:
    """Test calling get_course_progress via FastMCP."""
    result = await mock_server.call_tool("get_course_progress", {})
    content_text = _get_tool_result_text(result)
    assert "CKA" in content_text or "Kubernetes" in content_text


@pytest.mark.asyncio
async def test_call_list_enrolled_courses(mock_server: Any) -> None:
    """Test calling list_enrolled_courses via FastMCP."""
    result = await mock_server.call_tool("list_enrolled_courses", {})
    content_text = _get_tool_result_text(result)
    assert "Docker" in content_text
    assert "Terraform" in content_text


@pytest.mark.asyncio
async def test_call_get_course_outline(mock_server: Any) -> None:
    """Test calling get_course_outline via FastMCP."""
    result = await mock_server.call_tool("get_course_outline", {"course_name": "CKA"})
    content_text = _get_tool_result_text(result)
    assert "Core Concepts & Architecture" in content_text


@pytest.mark.asyncio
async def test_call_get_active_labs(mock_server: Any) -> None:
    """Test calling get_active_labs via FastMCP."""
    result = await mock_server.call_tool("get_active_labs", {})
    content_text = _get_tool_result_text(result)
    assert "Running" in content_text or "Paused" in content_text


@pytest.mark.asyncio
async def test_call_get_certifications(mock_server: Any) -> None:
    """Test calling get_certifications via FastMCP."""
    result = await mock_server.call_tool("get_certifications", {})
    content_text = _get_tool_result_text(result)
    assert "CKA" in content_text


@pytest.mark.asyncio
async def test_call_get_learning_summary(mock_server: Any) -> None:
    """Test calling get_learning_summary via FastMCP."""
    result = await mock_server.call_tool("get_learning_summary", {})
    content_text = _get_tool_result_text(result)
    assert "streak" in content_text.lower()


@pytest.mark.asyncio
async def test_call_write_tools_enabled(mock_write_server: Any) -> None:
    """Test calling start_lab and stop_lab when write tools are enabled."""
    start_result = await mock_write_server.call_tool("start_lab", {"lab_id": "lab-cka-upgrade"})
    start_text = _get_tool_result_text(start_result)
    assert "Running" in start_text

    stop_result = await mock_write_server.call_tool("stop_lab", {"lab_id": "lab-cka-upgrade"})
    stop_text = _get_tool_result_text(stop_result)
    assert "Terminated" in stop_text


@pytest.mark.asyncio
async def test_study_plan_prompt(mock_server: Any) -> None:
    """Test invoking the study_plan prompt."""
    prompts = await mock_server.list_prompts()
    prompt_names = [p.name for p in prompts]
    assert "study_plan" in prompt_names

    prompt_res = await mock_server.get_prompt("study_plan", {"goal": "CKA in 8 weeks"})
    assert prompt_res.messages
    message_text = prompt_res.messages[0].content.text
    assert "CKA in 8 weeks" in message_text
    assert "get_learning_summary()" in message_text
    assert "get_course_progress()" in message_text


@pytest.mark.asyncio
async def test_call_get_engineer_task(mock_server: Any) -> None:
    """Test calling get_engineer_task via FastMCP."""
    result = await mock_server.call_tool("get_engineer_task", {})
    content_text = _get_tool_result_text(result)
    assert "Nginx" in content_text or "stapp01" in content_text


@pytest.mark.asyncio
async def test_call_get_engineer_profile(mock_server: Any) -> None:
    """Test calling get_engineer_profile via FastMCP."""
    result = await mock_server.call_tool("get_engineer_profile", {})
    content_text = _get_tool_result_text(result)
    assert "devops_ninja" in content_text or "DevOps Engineer" in content_text


@pytest.mark.asyncio
async def test_call_list_engineer_history(mock_server: Any) -> None:
    """Test calling list_engineer_history via FastMCP."""
    result = await mock_server.call_tool("list_engineer_history", {"limit": 5})
    content_text = _get_tool_result_text(result)
    assert "PostgreSQL" in content_text or "Kubernetes" in content_text


@pytest.mark.asyncio
async def test_troubleshoot_engineer_task_prompt(mock_server: Any) -> None:
    """Test invoking the troubleshoot_engineer_task prompt."""
    prompts = await mock_server.list_prompts()
    prompt_names = [p.name for p in prompts]
    assert "troubleshoot_engineer_task" in prompt_names

    prompt_res = await mock_server.get_prompt("troubleshoot_engineer_task", {})
    assert prompt_res.messages
    message_text = prompt_res.messages[0].content.text
    assert "xFusionCorp" in message_text
    assert "get_engineer_task()" in message_text


@pytest.mark.asyncio
async def test_tool_error_graceful_handling() -> None:
    """Verify that when mock mode is disabled and credentials are missing, tools return graceful error responses without crashing."""
    from kodekloud_mcp.config import Settings
    from kodekloud_mcp.server import create_server

    unauthed_server = create_server(Settings(use_mock=False, session_credential=None))
    result = await unauthed_server.call_tool("list_enrolled_courses", {})
    content_text = _get_tool_result_text(result)
    assert "Authentication credential missing" in content_text


def test_unified_asgi_app_routes(mock_settings: Any, mock_server: Any) -> None:
    """Verify that create_mcp_asgi_app configures all required endpoints for Claude, Gemini, and ChatGPT."""
    from starlette.testclient import TestClient
    from kodekloud_mcp.server import create_mcp_asgi_app

    app = create_mcp_asgi_app(mock_server, mock_settings)
    route_paths = [getattr(r, "path", "") for r in app.routes]

    assert "/" in route_paths
    assert "/health" in route_paths
    assert "/sse" in route_paths
    assert "/mcp" in route_paths
    assert any("/messages" in p for p in route_paths)

    client = TestClient(app)
    # Test GET /
    res_info = client.get("/")
    assert res_info.status_code == 200
    assert res_info.json()["status"] == "healthy"

    # Test GET /health
    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "ok"

