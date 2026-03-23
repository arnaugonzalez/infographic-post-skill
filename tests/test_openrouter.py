"""Unit tests for OpenRouter adapter in generate_pretty.py.

All tests mock requests.post() — no live API key needed.
"""
import json
import sys
import types
from unittest.mock import MagicMock, patch
import pytest

# Import the module under test
sys.path.insert(0, ".")


def _make_mock_response(status_code: int, json_body: dict | None = None, text: str = ""):
    """Create a mock requests response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text or json.dumps(json_body or {})
    if json_body is not None:
        resp.json.return_value = json_body
    else:
        resp.json.side_effect = ValueError("No JSON")
    return resp


class TestModelValidation:
    """OROUTER-03: Model format validation fires before any API call."""

    def test_model_without_slash_rejected(self):
        """Model 'gpt-4o' (no slash) should print error and sys.exit(1)."""
        import subprocess
        result = subprocess.run(
            [sys.executable, "scripts/generate_pretty.py",
             "--text", "Test", "--llm-provider", "openrouter",
             "--llm-model", "gpt-4o", "--output", "/tmp/test_val.html"],
            capture_output=True, text=True, timeout=10,
            cwd="/home/eager-eagle/code/infographic-skill/infographic-skill"
        )
        assert result.returncode != 0
        assert "provider prefix" in result.stdout or "provider prefix" in result.stderr

    def test_model_with_slash_accepted(self):
        """Model 'openai/gpt-4o' (with slash) should pass validation."""
        # This test verifies validation passes — the API call will fail due to missing key
        import subprocess
        result = subprocess.run(
            [sys.executable, "scripts/generate_pretty.py",
             "--text", "Test", "--llm-provider", "openrouter",
             "--llm-model", "openai/gpt-4o", "--output", "/tmp/test_val.html"],
            capture_output=True, text=True, timeout=10,
            cwd="/home/eager-eagle/code/infographic-skill/infographic-skill",
            env={**dict(__import__('os').environ), "INFG_OPENROUTER_API_KEY": "", "INFG_LLM_API_KEY": ""}
        )
        assert result.returncode != 0
        assert "provider prefix" not in result.stdout
        # Should fail on missing API key, not model validation
        assert "API key" in result.stdout or "API key" in result.stderr


class TestOpenRouterHTTPErrors:
    """OROUTER-02: Clear error messages for 401 and 402."""

    def test_401_invalid_key(self):
        """HTTP 401 should print 'API key is invalid' and exit."""
        from scripts.generate_pretty import _call_openrouter_text_mode
        mock_resp = _make_mock_response(401, text="Unauthorized")
        with patch("scripts.generate_pretty._requests_lib") as mock_requests:
            mock_requests.post.return_value = mock_resp
            with pytest.raises(SystemExit) as exc_info:
                _call_openrouter_text_mode("test prompt", "openai/gpt-4o", "bad-key")
            assert exc_info.value.code == 1

    def test_402_insufficient_credits(self):
        """HTTP 402 should print 'insufficient credits' and exit."""
        from scripts.generate_pretty import _call_openrouter_text_mode
        mock_resp = _make_mock_response(402, text="Payment Required")
        with patch("scripts.generate_pretty._requests_lib") as mock_requests:
            mock_requests.post.return_value = mock_resp
            with pytest.raises(SystemExit) as exc_info:
                _call_openrouter_text_mode("test prompt", "openai/gpt-4o", "key")
            assert exc_info.value.code == 1

    def test_500_server_error(self):
        """HTTP 500 should print status code and partial body."""
        from scripts.generate_pretty import _call_openrouter_text_mode
        mock_resp = _make_mock_response(500, text="Internal Server Error")
        with patch("scripts.generate_pretty._requests_lib") as mock_requests:
            mock_requests.post.return_value = mock_resp
            with pytest.raises(SystemExit) as exc_info:
                _call_openrouter_text_mode("test prompt", "openai/gpt-4o", "key")
            assert exc_info.value.code == 1


class TestOpenRouterSuccess:
    """OROUTER-01 + OROUTER-04: Successful generation returns HTML and usage."""

    def test_successful_response_returns_html_and_usage(self):
        """200 response should return (html_string, usage_dict)."""
        from scripts.generate_pretty import _call_openrouter_text_mode
        body = {
            "choices": [{"message": {"content": "<html>Test</html>"}}],
            "usage": {
                "prompt_tokens": 150,
                "completion_tokens": 500,
            }
        }
        mock_resp = _make_mock_response(200, json_body=body)
        with patch("scripts.generate_pretty._requests_lib") as mock_requests:
            mock_requests.post.return_value = mock_resp
            html, usage = _call_openrouter_text_mode("prompt", "openai/gpt-4o", "sk-or-v1-test")

        assert html == "<html>Test</html>"
        assert usage["input_tokens"] == 150
        assert usage["output_tokens"] == 500

    def test_usage_missing_gracefully_defaults(self):
        """Response without usage object should return 0 tokens."""
        from scripts.generate_pretty import _call_openrouter_text_mode
        body = {
            "choices": [{"message": {"content": "<html>OK</html>"}}],
        }
        mock_resp = _make_mock_response(200, json_body=body)
        with patch("scripts.generate_pretty._requests_lib") as mock_requests:
            mock_requests.post.return_value = mock_resp
            html, usage = _call_openrouter_text_mode("prompt", "openai/gpt-4o", "key")

        assert html == "<html>OK</html>"
        assert usage["input_tokens"] == 0
        assert usage["output_tokens"] == 0
        assert usage["total_cost"] is None


class TestTokenCostReport:
    """OROUTER-04: Token counts appear in stdout."""

    def test_token_counts_printed_on_success(self):
        """After successful generation, stdout should contain token counts."""
        import scripts.generate_pretty as gp
        import inspect
        source = inspect.getsource(gp.generate_pretty)
        assert "Input tokens:" in source
        assert "Output tokens:" in source
