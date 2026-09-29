# Security Policy

The `kodekloud-mcp` project takes user privacy, account security, and safe credential handling seriously.

## Threat Model & Core Security Tenets

1. **User-Owned Credentials Only**:
   - `kodekloud-mcp` is designed exclusively for **single-user, personal execution**.
   - **Never run this server as a shared multi-tenant service** where multiple untrusted users share a single process or submit cookies to a centralized database.
2. **Treat Credentials Like Passwords**:
   - Your `KODEKLOUD_SESSION_COOKIE` grants full access to your KodeKloud account.
   - Never commit `.env` files, shell history, or logs containing session tokens.
   - Do not share screenshots or HAR files without rigorously redacting cookies, authorization tokens, and personal identifying information (PII).
3. **Session Rotation**:
   - If you ever suspect your cookie has leaked, immediately log out of your KodeKloud account in your web browser. This invalidates all active session tokens on KodeKloud's servers. Then log back in and generate a fresh session token.
4. **Least Privilege**:
   - State-changing write actions (`start_lab`, `stop_lab`) are **disabled by default**. Only enable `KODEKLOUD_ENABLE_WRITE_TOOLS=true` if you specifically need your chatbot to trigger or terminate lab instances.
5. **No Credential Logging**:
   - The server code actively redacts session tokens from all error messages and exceptions.
   - Standard output (`stdout`) is reserved purely for MCP protocol RPC messages. All operational logs go to `stderr`.
6. **Network & Hosting**:
   - When using `stdio` transport, the server runs as a local child process within your machine, making no external listener ports accessible.
   - If hosting the server over HTTP/SSE, **always** place it behind a reverse proxy enforcing TLS/HTTPS (e.g. Caddy, Nginx, Cloudflare), and never expose unauthenticated endpoints to the public internet.

## Reporting a Vulnerability

If you discover a security vulnerability in `kodekloud-mcp`:
- **Do NOT open a public GitHub issue.**
- Please report security concerns via GitHub Private Vulnerability Reporting or email the maintainers directly.
- We will acknowledge receipt within 48 hours and work with you to patch and disclose the issue responsibly.
