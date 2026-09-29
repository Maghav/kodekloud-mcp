"""Command-line interface (CLI) for launching the kodekloud-mcp server.

Supports stdio (default, for local clients like Claude Desktop, Cursor, Claude Code)
and SSE / Streamable HTTP (for remote clients like ChatGPT).
All logs are strictly routed to stderr to preserve stdout for JSON-RPC messages.
"""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Sequence

from kodekloud_mcp import __version__
from kodekloud_mcp.config import Settings
from kodekloud_mcp.server import create_server


def setup_logging(level_name: str) -> logging.Logger:
    """Configure logging strictly directed to stderr to protect MCP stdio protocol."""
    level = getattr(logging, level_name.upper(), logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers to avoid accidental stdout emission
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(level)
    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] [kodekloud-mcp] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    stderr_handler.setFormatter(formatter)
    root_logger.addHandler(stderr_handler)

    return logging.getLogger("kodekloud_mcp.cli")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog="kodekloud-mcp",
        description="KodeKloud Model Context Protocol (MCP) Server for AI Chat Clients.",
    )
    parser.add_argument(
        "-t",
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default=None,
        help="Transport protocol (stdio, sse, streamable-http). Default: from KODEKLOUD_MCP_TRANSPORT or 'stdio'.",
    )
    parser.add_argument(
        "--host",
        default=None,
        help="Host address for HTTP/SSE transport. Default: from KODEKLOUD_MCP_HOST or '127.0.0.1'.",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=None,
        help="Port number for HTTP/SSE transport. Default: from KODEKLOUD_MCP_PORT or 8000.",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        default=None,
        help="Force enable offline mock mode (default if unset).",
    )
    parser.add_argument(
        "--no-mock",
        action="store_false",
        dest="mock",
        help="Disable mock mode and connect to live KodeKloud endpoints.",
    )
    parser.add_argument(
        "--enable-write-tools",
        action="store_true",
        default=None,
        help="Enable state-modifying tools (start_lab, stop_lab). Disabled by default.",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=None,
        help="Set logging verbosity (sent strictly to stderr). Default: INFO.",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"kodekloud-mcp {__version__}",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Entrypoint function for the kodekloud-mcp executable."""
    args = parse_args(argv)

    # Build overrides from explicit CLI arguments
    overrides: dict[str, object] = {}
    if args.transport is not None:
        overrides["transport"] = args.transport
    if args.host is not None:
        overrides["host"] = args.host
    if args.port is not None:
        overrides["port"] = args.port
    if args.mock is not None:
        overrides["use_mock"] = args.mock
    if args.enable_write_tools is not None:
        overrides["enable_write_tools"] = args.enable_write_tools
    if args.log_level is not None:
        overrides["log_level"] = args.log_level

    settings = Settings.from_env(**overrides)
    logger = setup_logging(settings.log_level)

    # Log safe operational status to stderr
    logger.info("Initializing kodekloud-mcp v%s", __version__)
    logger.info("Transport: %s", settings.transport)
    logger.info(
        "Mock Mode: %s",
        "ENABLED (offline simulated data)" if settings.use_mock else "DISABLED (live endpoints)",
    )
    logger.info(
        "Write Tools: %s", "ENABLED" if settings.enable_write_tools else "DISABLED (read-only mode)"
    )
    logger.info("Session Credential: %s", settings.masked_credential())

    server = create_server(settings=settings)

    try:
        if settings.transport == "stdio":
            logger.info("Starting MCP server over stdio transport...")
            server.run(transport="stdio")
        elif settings.transport == "sse":
            logger.info(
                "Starting MCP server over SSE transport at http://%s:%d/sse ...",
                settings.host,
                settings.port,
            )
            server.run(transport="sse", host=settings.host, port=settings.port)
        elif settings.transport == "streamable-http":
            logger.info(
                "Starting MCP server over Streamable HTTP transport at http://%s:%d/mcp ...",
                settings.host,
                settings.port,
            )
            server.run(transport="streamable-http", host=settings.host, port=settings.port)
        else:
            logger.error(
                "Unknown transport '%s'. Choose stdio, sse, or streamable-http.", settings.transport
            )
            return 1
    except KeyboardInterrupt:
        logger.info("Received interrupt signal. Shutting down gracefully.")
        return 0
    except Exception as exc:
        logger.exception("Server runtime error: %s", exc)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
