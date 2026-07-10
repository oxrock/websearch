"""
Core web search and extraction utilities.

This module provides three primary functions for programmatic web interaction:
- web_search: Query DuckDuckGo (free), Google (Custom Search API, needs key + CX),
  or Bing (via Playwright headless browser, free, needs playwright installed).
- web_extract: Fetch a URL, strip scripts/styles/nav, return clean text.
- execute_system_command: Run a shell command safely with timeout.

All functions are designed to be imported and used directly in other projects
without side effects at import time.
"""

import os
import json
import subprocess
import urllib.parse
import base64
import requests
from typing import Optional

from bs4 import BeautifulSoup
from duckduckgo_search import DDGS


# ── Helpers ──────────────────────────────────────────────────────────────────

_GOOGLE_CSE_ENDPOINT = "https://www.googleapis.com/customsearch/v1"


def execute_system_command(command: str, timeout_seconds: int = 180) -> str:
    """
    Run a shell command; return stdout if successful, else stderr or a safe note.

    .. warning::

        **SECURITY: This function uses ``shell=True`` and is NOT safe to call
        with untrusted input.** Passing user-supplied strings (e.g. search
        results, scraped page content, LLM output) directly as the ``command``
        argument enables arbitrary shell injection and remote code execution.

        Only call this with command strings you fully control. If you need to
        run a program with untrusted arguments, use :func:`subprocess.run`
        directly with ``shell=False`` and an argument list. Never expose this
        function as an LLM tool without additional sandboxing, allow-listing,
        or human-in-the-loop confirmation.

    Args:
        command: The shell command to execute. Must be a trusted string.
        timeout_seconds: Maximum time to wait for completion.

    Returns:
        Command output as string, or error description.
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=int(timeout_seconds),
        )

        out_text = (result.stdout or "").strip()
        err_text = (result.stderr or "").strip()

        if not out_text:
            return err_text or "Command ran but produced no direct visible output."

        return out_text.strip()

    except subprocess.TimeoutExpired:
        return f"Execution error: command timed out after {timeout_seconds} seconds."

    except Exception as e:
        return f"Execution error: {str(e)}"


# ── Search entry point ──────────────────────────────────────────────────────

def web_search(
    query: str,
    max_results: int = 3,
    backend: str = "bing",
    # DuckDuckGo-specific params
    timeout: int = 10,
    region: str = "wt-wt",
    safesearch: str = "moderate",
    timelimit: Optional[str] = None,
    proxies: Optional[dict] = None,
    verify: bool = True,
    # Google API-specific params
    api_key: Optional[str] = None,
    cx: Optional[str] = None,
    google_lang: str = "en",
    google_safe: str = "active",
) -> str:
    """
    Search the public web using DuckDuckGo (free, no key), Google Custom Search
    API (requires api_key + cx), or Bing (via Playwright, free, needs playwright
    package installed).

    Args:
        query: Search query string.
        max_results: Maximum number of results to return (default: 3).
        backend: Search backend — "bing" (default via Playwright), "duckduckgo", or "google".

        # DuckDuckGo params
        timeout: HTTP request timeout in seconds (DDG, default: 10).
        region: DDG region code (default: 'wt-wt' for worldwide).
        safesearch: DDG safe search: 'on', 'moderate', or 'off' (default: 'moderate').
        timelimit: DDG time limit: 'd' (day), 'w' (week), 'm' (month), 'y' (year).
        proxies: Dict of proxy URLs per protocol.
        verify: Verify SSL certificates (DDG, default: True).

        # Google API params
        api_key: Google Custom Search API key (required for backend="google").
        cx: Google Custom Search Engine ID (required for backend="google").
        google_lang: Search language (default: 'en').
        google_safe: Safe search: 'active' or 'off' (default: 'active').

    Returns:
        JSON string with query, backend, and results list, or error message.
    """
    try:
        if backend == "google":
            return _search_google_api(
                query=query,
                max_results=max_results,
                api_key=api_key,
                cx=cx,
                lang=google_lang,
                safe=google_safe,
                timeout=timeout,
            )
        elif backend == "bing":
            return _search_bing(
                query=query,
                max_results=max_results,
                timeout=timeout,
            )
        else:
            return _search_duckduckgo(
                query=query,
                max_results=max_results,
                timeout=timeout,
                region=region,
                safesearch=safesearch,
                timelimit=timelimit,
                proxies=proxies,
                verify=verify,
            )

    except Exception as e:
        return f"Search error (backend={backend}): {str(e)}"


# ── DuckDuckGo backend ──────────────────────────────────────────────────────

def _search_duckduckgo(
    query: str,
    max_results: int = 3,
    timeout: int = 10,
    region: str = "wt-wt",
    safesearch: str = "moderate",
    timelimit: Optional[str] = None,
    proxies: Optional[dict] = None,
    verify: bool = True,
) -> str:
    """Internal: run search via DuckDuckGo."""
    try:
        with DDGS(
            timeout=timeout,
            proxies=proxies,
            verify=verify,
        ) as ddgs:
            results_iter = list(
                ddgs.text(
                    str(query),
                    region=region,
                    safesearch=safesearch,
                    timelimit=timelimit,
                    max_results=int(max_results or 3),
                )
            )

            out_rows = []
            for item in (results_iter or []):
                if isinstance(item, dict):
                    out_rows.append({k: v for k, v in item.items() if isinstance(v, (str, int, float))})
                else:
                    out_rows.append(str(item))

            return json.dumps({"query": str(query), "backend": "duckduckgo", "results": out_rows}, indent=2)

    except Exception as e:
        return f"Search error (backend=duckduckgo): {str(e)}"


# ── Google Custom Search API backend ────────────────────────────────────────

def _search_google_api(
    query: str,
    max_results: int = 3,
    api_key: Optional[str] = None,
    cx: Optional[str] = None,
    lang: str = "en",
    safe: str = "active",
    timeout: int = 10,
) -> str:
    """Internal: run search via Google Custom Search JSON API."""

    api_key = api_key or os.getenv("GOOGLE_API_KEY")
    cx = cx or os.getenv("GOOGLE_CX")

    if not api_key:
        return (
            'Search error (backend=google): No API key provided. '
            'Pass api_key= to web_search() or set the GOOGLE_API_KEY environment variable.'
        )
    if not cx:
        return (
            'Search error (backend=google): No Custom Search Engine ID provided. '
            'Pass cx= to web_search() or set the GOOGLE_CX environment variable.'
        )

    params = {
        "key": api_key,
        "cx": cx,
        "q": query,
        "num": min(int(max_results or 3), 10),  # API limit: max 10 per request
        "hl": lang,
        "safe": safe,
    }

    try:
        resp = requests.get(_GOOGLE_CSE_ENDPOINT, params=params, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()

        items = data.get("items", [])
        out_rows = []
        for item in items:
            out_rows.append({
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "description": item.get("snippet", ""),
            })

        return json.dumps(
            {"query": str(query), "backend": "google", "results": out_rows},
            indent=2,
        )

    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if hasattr(e, 'response') else 0
        body = e.response.text[:500] if hasattr(e, 'response') and e.response else ""
        return f"Search error (backend=google): HTTP {status} — {body or str(e)}"

    except Exception as e:
        return f"Search error (backend=google): {str(e)}"


# ── Bing (Playwright headless browser) backend ──────────────────────────────

def _extract_bing_url(data: str) -> str:
    """Extract real URL from a Bing tracking link by decoding the u parameter."""
    try:
        parsed = urllib.parse.urlparse(data)
        qs = urllib.parse.parse_qs(parsed.query)
        u_param = qs.get("u", [None])[0]
        if u_param:
            # Bing prefixes the base64 with a 2-byte tag (e.g. 'a1')
            # Strip it, then pad and decode
            b64_data = u_param[2:] if len(u_param) > 2 else u_param
            rem = len(b64_data) % 4
            if rem:
                b64_data += "=" * (4 - rem)
            decoded = base64.b64decode(b64_data).decode("utf-8")
            return decoded
    except Exception:
        pass
    return data


def _search_bing(
    query: str,
    max_results: int = 3,
    timeout: int = 15,
) -> str:
    """
    Internal: run search via Bing using Playwright headless browser.

    Bing does not block headless Playwright like Google does. Results are
    extracted from the rendered DOM using standard CSS selectors.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return (
            'Search error (backend=bing): Playwright is not installed. '
            'Run: pip install playwright && playwright install chromium'
        )

    try:
        results = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(
                f"https://www.bing.com/search?q={urllib.parse.quote(str(query))}",
                timeout=timeout * 1000,
            )
            page.wait_for_timeout(3000)

            containers = page.query_selector_all(".b_algo")
            for i, container in enumerate(containers):
                if i >= int(max_results):
                    break

                title_el = container.query_selector("h2")
                link_el = container.query_selector("h2 a")
                snippet_el = container.query_selector(
                    ".b_caption p, .b_lineclamp2, .b_snippet"
                )

                title = title_el.inner_text().strip() if title_el else ""
                raw_url = link_el.get_attribute("href") if link_el else ""
                snippet = snippet_el.inner_text().strip() if snippet_el else ""

                clean_url = _extract_bing_url(raw_url) if raw_url else ""

                results.append({
                    "title": title,
                    "url": clean_url,
                    "description": snippet,
                })

            browser.close()

        return json.dumps(
            {"query": str(query), "backend": "bing", "results": results},
            indent=2,
        )

    except Exception as e:
        return f"Search error (backend=bing): {str(e)}"


# ── Web extraction ──────────────────────────────────────────────────────────

def web_extract(
    url: str,
    max_chars: int = 10_000,
    timeout: int = 15,
    user_agent: Optional[str] = None,
    headers: Optional[dict] = None,
    strip_tags: tuple = ("script", "style", "nav", "footer", "header"),
) -> str:
    """
    Fetch a page, strip fluff tags and scripts, then return readable text chunks.

    Args:
        url: The URL to fetch and extract text from.
        max_chars: Maximum characters to return (default: 10000).
        timeout: HTTP request timeout in seconds (default: 15).
        user_agent: Custom User-Agent string (default: Chrome 120 on Windows).
        headers: Additional HTTP headers to send with the request.
        strip_tags: Tuple of HTML tags to strip from the page.

    Returns:
        Cleaned text content, or error message.
    """
    url = str(url or "").strip()
    if not url:
        return "Web extraction skipped: no valid URL supplied."

    req_headers = {
        "User-Agent": (
            user_agent
            or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
    }
    if headers:
        req_headers.update(headers)

    try:
        resp = requests.get(url, headers=req_headers, timeout=timeout)
        if not 200 <= (resp.status_code or 0) < 300:
            return f"Web extraction returned status {resp.status_code}; skipped page."

        html_text = (resp.text or "").strip()
        soup = BeautifulSoup(html_text, "html.parser")

        for tag in strip_tags:
            for el in soup.find_all(tag):
                el.decompose()

        pieces = []
        for line in soup.stripped_strings:
            line = " ".join(line.split())
            if line:
                pieces.append(line)

        clean_text = "\n".join(pieces).strip() or "(page contained unreadable content)"

        if len(clean_text) > int(max_chars):
            return clean_text[:int(max_chars)] + "\n... [trimmed]"

        return clean_text

    except Exception as e:
        return f"Web extraction error for {url or '(no URL)'}:\n{str(e)}"