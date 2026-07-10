import pytest
from unittest.mock import patch, MagicMock
from websearch import web_search, web_extract


@pytest.fixture
def mock_ddgs():
    """Mock the DDGS context manager for web_search."""
    with patch("websearch.search.DDGS") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value.__enter__.return_value = mock_instance
        mock_class.return_value.__exit__.return_value = None
        yield mock_instance


@pytest.fixture
def mock_requests():
    """Mock the requests library for web_extract."""
    with patch("websearch.search.requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.status_code = 200
        mock_resp.text = (
            "<html><body><h1>Mock Content</h1>"
            "<p>This is sample text.</p>"
            "<script>console.log('script');</script>"
            "<style>...</style></body></html>"
        )
        mock_get.return_value = mock_resp
        yield mock_get


def test_web_search_structure(mock_ddgs):
    """Test that web_search runs without crashing and returns expected JSON structure."""
    query = "test query for search"
    mock_ddgs.text.return_value = [{"text": "Mock result 1"}, {"text": "Mock result 2"}]

    result = web_search(query, backend="duckduckgo")

    assert isinstance(result, str)
    assert "Mock result 1" in result
    print(f"✅ Web Search Mocked Successfully: Result starts with {result[:30]}...")


def test_web_extract_structure(mock_requests):
    """Test that web_extract handles HTTP requests and BeautifulSoup parsing."""
    mock_requests.return_value.text = (
        "<html><body><h1>A</h1>"
        "<p>Visible text here.</p>"
        "<script>alert();</script>"
        "<footer></footer></body></html>"
    )

    test_url = "http://mock-test.com/page"
    result = web_extract(test_url)

    assert isinstance(result, str)
    assert "Visible text here" in result
    assert "script" not in result  # Checks if the soup cleanup worked
    print("✅ Web Extract Mocked Successfully: Content seems clean.")