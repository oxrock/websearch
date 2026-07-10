"""
websearch - Lightweight web search and extraction utilities.

Public API:
    web_search: Search the web via Bing (default, via Playwright), DuckDuckGo
      (free, no key), or Google Custom Search API (needs api_key + cx).
    web_extract: Fetch and clean readable text from a URL.
    execute_system_command: Run a shell command with a timeout.

    Note: execute_system_command uses shell=True and is NOT safe for untrusted
    input. See its docstring for details.
"""

from .search import (
    web_search,
    web_extract,
    execute_system_command,
)

__all__ = [
    "web_search",
    "web_extract",
    "execute_system_command",
]


def _read_version() -> str:
    # Read the installed package metadata when available; fall back to a
    # static string for source checkouts that haven't been installed yet.
    try:
        from importlib.metadata import PackageNotFoundError, version  # py3.8+
        try:
            return version("websearch-py")
        except PackageNotFoundError:
            return "0.1.0"
    except Exception:  # pragma: no cover - extremely defensive
        return "0.1.0"


__version__ = _read_version()
