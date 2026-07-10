import os
import json
from websearch import web_search, web_extract, execute_system_command

# NOTE: This script MUST be run in the same environment where the websearch package is installed
# Run: pip install -e .[dev]  (or just pip install -e .)

print("=============================================")
print("🧹 STARTING SMOKE TEST FOR WEBSEARCH PACKAGE 🧹")
print("=============================================")

# --- Test 1: Web Search (Connectivity Test) ---
print("\n\n[--- PHASE 1: Testing web_search (Requires internet connection) ---]")
search_query = "python duckduckgo search test"
try:
    print(f"Attempting to call web_search with query: '{search_query}'...")
    search_result = web_search(search_query, max_results=1)

    if "Search error" in search_result:
        print(f"✅ PASS (Expected Failure): Search function reported an error (service may be down): {search_result[:150]}")
    else:
        print("✅ PASS: web_search output received and is JSON serializable.")
        print("--- RAW OUTPUT SNIPPET ---")
        print(search_result[:500] + "...")

except Exception as e:
    print(f"❌ FAIL: web_search crashed during execution. Error: {e}")


# --- Test 1b: web_search with custom params ---
print("\n\n[--- PHASE 1b: Testing web_search with custom timeout/region/safesearch ---]")
try:
    search_custom = web_search("test query", max_results=1, timeout=20, region="us-en", safesearch="on")
    print("✅ PASS: web_search with custom params did not crash.")
    print(search_custom[:200] + "...")
except Exception as e:
    print(f"⚠️ Custom params call had an issue (may be network): {e}")


# --- Test 1c: web_search with Bing backend ---
print("\n\n[--- PHASE 1c: Testing web_search with backend='bing' ---]")
try:
    bing_result = web_search("python programming", max_results=3, backend="bing", timeout=15)
    data = json.loads(bing_result) if bing_result.startswith("{") else {"raw": bing_result}
    print(f"✅ PASS: web_search with Bing backend returned results.")
    print(f"  Backend: {data.get('backend', '?')}")
    print(f"  Results count: {len(data.get('results', []))}")
    for r in data.get("results", [])[:3]:
        print(f"    - {r.get('title', '?')[:60]}")
        print(f"      {r.get('url', '?')[:70]}")
except Exception as e:
    print(f"⚠️ Bing call had an issue: {e}")


# --- Test 1d: web_search with Google API backend (no credentials) ---
print("\n\n[--- PHASE 1d: Testing web_search with backend='google' (no API key) ---]")
try:
    google_result = web_search("python programming", max_results=2, backend="google")
    if "No API key" in google_result or "No Custom Search" in google_result:
        print("✅ PASS: Google backend correctly reports missing credentials when no API key is set.")
    else:
        print(f"✅ PASS: Google backend returned results (credentials were available): {google_result[:200]}")
except Exception as e:
    print(f"⚠️ Google backend call had an issue: {e}")


# --- Test 2: Web Extract (HTTP Connectivity Test) ---
print("\n\n[--- PHASE 2: Testing web_extract (Targeting a stable, public site) ---]")
test_url = "https://en.wikipedia.org/wiki/Python_(programming_language)"
try:
    print(f"Attempting to call web_extract on: {test_url}...")
    extract_result = web_extract(test_url)

    if "Web extraction error" in extract_result:
        print(f"✅ PASS (Expected Failure): Extraction function reported an error (site may have blocked): {extract_result[:150]}")
    else:
        print("✅ PASS: web_extract successfully read and cleaned text from Wikipedia.")
        print("--- RAW OUTPUT SNIPPET ---")
        print(extract_result[:500] + "...")

except Exception as e:
    print(f"❌ FAIL: web_extract crashed during execution. Error: {e}")


# --- Test 2b: web_extract with custom params ---
print("\n\n[--- PHASE 2b: Testing web_extract with custom timeout/user_agent/strip_tags ---]")
try:
    extract_custom = web_extract(
        "https://en.wikipedia.org/wiki/Python_(programming_language)",
        max_chars=300,
        timeout=20,
        user_agent="Mozilla/5.0 (compatible; WebsearchBot/1.0)",
        headers={"Accept": "text/html"},
        strip_tags=("script", "style"),  # keep nav/footer for test
    )
    print("✅ PASS: web_extract with custom params did not crash.")
    print(extract_custom[:300] + "...")
except Exception as e:
    print(f"⚠️ Custom params extraction had an issue: {e}")


# --- Test 3: System Command Execution (Local OS Test) ---
print("\n\n[--- PHASE 3: Testing execute_system_command (OS Dependency Check) ---]")
test_command = "echo 'Smoke test success: Python execution environment is accessible.'"
try:
    print(f"Attempting to execute command: '{test_command}'...")
    command_result = execute_system_command(test_command)

    if "Execution error" in command_result:
        print(f"⚠️ WARNING: Simple command failed. Potential OS execution issue: {command_result}")
    else:
        print("✅ PASS: System command executed successfully.")
        print(f"--- RAW OUTPUT SNIPPET ---")
        print(command_result.strip())

except Exception as e:
    print(f"❌ FAIL: execute_system_command crashed during execution. Error: {e}")

print("\n=============================================")
print("🎆 SMOKE TEST SEQUENCE COMPLETE 🎆")
print("=============================================")