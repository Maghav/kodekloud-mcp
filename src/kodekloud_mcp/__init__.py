"""KodeKloud Model Context Protocol (MCP) Server.

Connects KodeKloud learner accounts to AI chat clients (Claude Desktop, Claude Code,
ChatGPT, Cursor, and any MCP-compatible agent) to review course progress, plan study,
and manage labs.
"""

from kodekloud_mcp.config import Settings
from kodekloud_mcp.server import create_server

__version__ = "0.1.0"
__all__ = ["create_server", "Settings", "__version__"]
