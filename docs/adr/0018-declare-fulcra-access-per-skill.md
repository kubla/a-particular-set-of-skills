---
status: accepted
---

# Declare Fulcra access per skill

Each skill declares the Fulcra interface it requires instead of inheriting a repository-wide CLI requirement. CLI-backed skills use the current unpinned CLI and are retested for each CLI release; MCP-backed skills use an authenticated host-provided Fulcra MCP connection. Every declared interface requires live acceptance coverage.
