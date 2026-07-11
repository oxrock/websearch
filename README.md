# websearch

Lightweight, installable Python package for programmatic web search and content extraction.

`websearch` gives you three functions you can drop into agent workflows, scripts, or notebooks: a multi-backend web search (Bing via Playwright, DuckDuckGo, or Google Custom Search), a readable-text extractor for arbitrary URLs, and a timeout-bounded shell command runner. All backends are installed by default — no extras needed.

## Features

- **`web_search(query, max_results=3, backend="bing", ...)`** — Search the web via Bing (default, Playwright), DuckDuckGo (free, no key needed), or Google Custom Search API (requires `api_key` + `cx`).
- **`web_extract(url, max_chars=10000, timeout=15, user_agent=None, headers=None, strip_tags=("script","style","nav","footer","header"))`** — Fetch a URL, strip noise tags, return clean readable text.
- **`execute_system_command(cmd, timeout_seconds=180)`** — Run a shell command with a timeout, return stdout/stderr. **Not safe for untrusted input — see [Security](#security) below.**

## Installation

```bash
# From PyPI once published
pip install websearch-py

# From source (editable install for development)
pip install -e .

# With dev dependencies (pytest, build, etc.)
pip install -e ".[dev]"

# One-time setup: download the Chromium browser binary for the Bing backend
playwright install chromium
```

> **Distribution name vs. import name:** The package is distributed on PyPI as `websearch-py` (the bare `websearch` name was already registered by another project), but the import name is still `websearch`. So you `pip install websearch-py` and then `from websearch import web_search, ...` — only the `pip install` side uses the `-py` suffix.

> **Why `playwright install chromium`?** The `playwright` Python library is installed automatically by `pip install websearch-py`, but the Chromium browser binary it drives (~150 MB) is downloaded separately. This is a Playwright design constraint — browser binaries are too large to ship inside a pip package. Run `playwright install chromium` once per machine after the pip install.

## Quick Start

```python
from websearch import web_search, web_extract, execute_system_command

# Search the web (defaults to Bing via Playwright, no key needed)
results = web_search("python asyncio tutorial", max_results=5)
print(results)  # JSON string with query, backend, and results list

# Switch to DuckDuckGo backend (free, no key, no browser download needed)
results = web_search("rust vs go", backend="duckduckgo", region="us-en")

# Search with Google Custom Search API instead
results = web_search("machine learning", max_results=3, backend="google",
                     api_key=api_key, cx=cx)

# Extract clean text from a page
content = web_extract("https://en.wikipedia.org/wiki/Python_(programming_language)")
print(content[:500])  # First 500 chars of cleaned text

# Extract with custom timeout and additional headers
content = web_extract("https://example.com", timeout=30, headers={"Accept-Language": "en-US,en;q=0.9"})

# Run a shell command (TRUSTED INPUT ONLY — see Security section)
output = execute_system_command("echo hello from websearch")
print(output)
```

## Bing (Playwright) Setup

The `backend="bing"` default uses Playwright with a headless Chromium browser. The `playwright` Python library is installed automatically with `websearch-py`, but you also need to download the Chromium browser binary:

```bash
playwright install chromium
```

Run this once per machine. Bing via Playwright is free and needs no API keys or accounts.

If you skip this step, calling `web_search(...)` with the default backend will return an error like `Search error (backend=bing): Playwright is not installed...` or fail to launch the browser. You can always use `backend="duckduckgo"` instead, which needs no extra setup.

## Google Custom Search API Setup

To use `backend="google"` you need two things from Google Cloud:

1. **A Custom Search Engine (CX)** — https://cse.google.com/cse/all → create a search engine.
2. **An API Key** — https://console.cloud.google.com → enable "Custom Search API", create credentials.

Set them as environment variables or pass directly:

```bash
export GOOGLE_API_KEY="your-api-key-here"
export GOOGLE_CX="your-cse-id-here"
```

```python
# Via env vars (recommended — keeps keys out of code)
search = web_search("query", backend="google")

# Or inline
search = web_search("query", backend="google", api_key="...", cx="...")
```

The API is rate-limited to 100 queries/day on the free tier.

## Full API

### `web_search(query, max_results=3, backend="bing", timeout=10, ...)`

| Parameter | Default | Description |
|-----------|---------|-------------|
| `query` | — | Search query string (required) |
| `max_results` | `3` | Max results to return |
| `backend` | `"bing"` | Search backend: `"bing"` (default, via Playwright), `"duckduckgo"` (free, no key), or `"google"` (needs `api_key` + `cx`) |
| `timeout` | `10` | HTTP request timeout in seconds |
| `region` | `"wt-wt"` | DDG region code (`"us-en"`, `"de-de"`, etc.) |
| `safesearch` | `"moderate"` | DDG safe search: `"on"`, `"moderate"`, or `"off"` |
| `timelimit` | `None` | DDG time limit: `"d"` (day), `"w"`, `"m"`, `"y"` |
| `proxies` | `None` | Dict of proxy URLs per protocol |
| `verify` | `True` | SSL certificate verification (DDG) |
| `api_key` | `None` | Google Custom Search API key (also reads `GOOGLE_API_KEY` env var) |
| `cx` | `None` | Google Custom Search Engine ID (also reads `GOOGLE_CX` env var) |
| `google_lang` | `"en"` | Google search language |
| `google_safe` | `"active"` | Google safe search: `"active"` or `"off"` |

**Return value:** JSON string with keys `query`, `backend`, and `results` (list).

### `web_extract(url, max_chars=10000, timeout=15, user_agent=None, headers=None, strip_tags=...)`

| Parameter | Default | Description |
|-----------|---------|-------------|
| `url` | — | URL to fetch and extract (required) |
| `max_chars` | `10000` | Max characters to return |
| `timeout` | `15` | HTTP request timeout in seconds |
| `user_agent` | `None` | Custom User-Agent string (defaults to Chrome 120) |
| `headers` | `None` | Additional HTTP headers |
| `strip_tags` | `("script","style","nav","footer","header")` | HTML tags to strip from output |

### `execute_system_command(command, timeout_seconds=180)`

| Parameter | Default | Description |
|-----------|---------|-------------|
| `command` | — | Shell command to run (required, **trusted input only**) |
| `timeout_seconds` | `180` | Max seconds before timeout |

## Security

`execute_system_command` calls `subprocess.run(command, shell=True)`. This means **any shell metacharacters in `command` are interpreted by the shell**, which makes the function unsafe to call with untrusted input. If `command` is built from user input, search results, scraped page content, or LLM output, an attacker can inject arbitrary shell commands (e.g. `; rm -rf ~`).

**Mitigations:**

- Only pass command strings you fully control to this function.
- If you need to run a program with untrusted arguments, call `subprocess.run` directly with `shell=False` and an argument list.
- If you expose this as an LLM tool, wrap it with allow-listing, sandboxing, or human-in-the-loop confirmation.

The `web_search` and `web_extract` functions do not have this issue — they only construct HTTP requests and parse responses.

## Requirements

- Python 3.8+
- `beautifulsoup4` (core)
- `requests` (core)
- `duckduckgo-search` (core — needed for `backend="duckduckgo"`)
- `playwright` (core — needed for `backend="bing"`; also requires a one-time `playwright install chromium` to download the browser binary)

All dependencies install automatically via `pip install websearch-py`. The only manual step is `playwright install chromium` (run once per machine) to enable the Bing backend.

## Running Tests

```bash
# Run the full test suite (unit + smoke) via the provided script
./run_tests.sh

# Or run individually:
pip install -e ".[dev]"
pytest tests/ -v            # mocked unit tests, no network needed
python smoke_test.py        # live integration test, hits real sites
```

## Project Structure

```
websearch/
├── src/
│   └── websearch/
│       ├── __init__.py      # Public API exports + version
│       └── search.py        # Core implementation
├── tests/
│   └── test_search_engine.py  # Unit tests (mocked, no network)
├── .github/
│   └── workflows/
│       └── publish.yml      # Build + publish to PyPI on tag push
├── smoke_test.py            # Live integration test
├── run_tests.sh             # Test runner script
├── pyproject.toml           # Package configuration
├── LICENSE
└── README.md                # This file
```

## Importing in External Projects

After installing (`pip install websearch-py` or adding as a git dependency):

```python
from websearch import web_search, web_extract, execute_system_command

# Use directly in your codebase
data = web_search("your query")                        # default: Bing (needs `playwright install chromium` once)
data = web_search("your query", backend="duckduckgo")  # DuckDuckGo (free, no key, no browser download)
data = web_search("your query", backend="google")      # Google (needs key)
text = web_extract("https://example.com")
cmd_out = execute_system_command("ls -la")             # trusted input only
```

## License

MIT — see [LICENSE](LICENSE).
