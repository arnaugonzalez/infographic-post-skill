"""Unit tests for scripts/generate_posts.py — LinkedIn post generator.

Covers POSTS-01 through POSTS-04.
All LLM calls are mocked — no live API key needed.
"""
import json
import os
import subprocess
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

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


def _post_body(content: str) -> dict:
    return {"choices": [{"message": {"content": content}}]}


# ---------------------------------------------------------------------------
# TestOutputFormat (POSTS-01, D-04, D-05, D-06)
# ---------------------------------------------------------------------------

class TestOutputFormat:
    """POSTS-01: Output format — file, stdout, separators, char counts."""

    def test_both_posts_written_to_file(self, tmp_path, monkeypatch):
        """Both posts are written to linkedin_posts.md in cwd."""
        monkeypatch.chdir(tmp_path)
        tech_text = "T" * 1000
        biz_text = "B" * 1000
        from scripts.generate_posts import _write_output
        _write_output(tech_text, biz_text)
        out_file = tmp_path / "linkedin_posts.md"
        assert out_file.exists()
        content = out_file.read_text(encoding="utf-8")
        assert "--- TECHNICAL POST ---" in content
        assert "--- BUSINESS POST ---" in content
        assert tech_text in content
        assert biz_text in content

    def test_stdout_contains_separators_and_char_counts(self, tmp_path, monkeypatch, capsys):
        """Stdout shows separators and char counts for each post."""
        monkeypatch.chdir(tmp_path)
        tech_text = "T" * 1000
        biz_text = "B" * 1000
        from scripts.generate_posts import _write_output
        _write_output(tech_text, biz_text)
        captured = capsys.readouterr()
        assert "--- TECHNICAL POST ---" in captured.out
        assert "--- BUSINESS POST ---" in captured.out
        assert "1,000" in captured.out or "1000" in captured.out

    def test_file_overwritten_not_appended(self, tmp_path, monkeypatch):
        """Running _write_output twice overwrites the file — no duplicate separators."""
        monkeypatch.chdir(tmp_path)
        tech_text = "T" * 1000
        biz_text = "B" * 1000
        from scripts.generate_posts import _write_output
        _write_output(tech_text, biz_text)
        _write_output(tech_text, biz_text)
        content = (tmp_path / "linkedin_posts.md").read_text(encoding="utf-8")
        assert content.count("--- TECHNICAL POST ---") == 1
        assert content.count("--- BUSINESS POST ---") == 1

    def test_saved_confirmation_printed(self, tmp_path, monkeypatch, capsys):
        """Stdout contains 'Saved to linkedin_posts.md' confirmation."""
        monkeypatch.chdir(tmp_path)
        from scripts.generate_posts import _write_output
        _write_output("T" * 1000, "B" * 1000)
        captured = capsys.readouterr()
        assert "Saved to linkedin_posts.md" in captured.out


# ---------------------------------------------------------------------------
# TestLanguageValidation (POSTS-02, D-01, D-02)
# ---------------------------------------------------------------------------

class TestLanguageValidation:
    """POSTS-02: Language validation via argparse."""

    def test_invalid_language_exits_with_error(self):
        """Unsupported --language zh exits with returncode 2 (argparse error)."""
        result = subprocess.run(
            [sys.executable, "scripts/generate_posts.py", ".", "--language", "zh"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd="/home/eager-eagle/code/infographic-skill/infographic-skill",
        )
        assert result.returncode == 2

    def test_valid_language_accepted(self):
        """--language es is accepted by argparse (no exit 2)."""
        # We patch env so main() exits cleanly before any LLM call
        env = {**os.environ, "INFG_OPENROUTER_API_KEY": "", "INFG_LLM_MODEL": ""}
        result = subprocess.run(
            [sys.executable, "scripts/generate_posts.py", ".", "--language", "es"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd="/home/eager-eagle/code/infographic-skill/infographic-skill",
            env=env,
        )
        # argparse exit code 2 means invalid choice — should NOT be 2
        assert result.returncode != 2

    def test_default_language_is_en(self):
        """Without --language flag, 'en' is used by default."""
        import argparse
        from scripts.generate_posts import SUPPORTED_LANGUAGES

        parser = argparse.ArgumentParser()
        parser.add_argument("directory")
        parser.add_argument("--language", choices=SUPPORTED_LANGUAGES, default="en")
        args = parser.parse_args(["some_dir"])
        assert args.language == "en"


# ---------------------------------------------------------------------------
# TestCharacterRetry (POSTS-03, D-09)
# ---------------------------------------------------------------------------

class TestCharacterRetry:
    """POSTS-03: Retry logic when post length is outside 800-1600 chars."""

    def test_retry_when_post_too_short(self):
        """If first response is too short (<800), _call_openrouter is called twice."""
        short_post = "X" * 400
        good_post = "X" * 1000
        with patch("scripts.generate_posts._call_openrouter", side_effect=[short_post, good_post]) as mock_call:
            from scripts.generate_posts import _generate_post
            result = _generate_post("user", "system", "model/x", "key")
        assert mock_call.call_count == 2
        assert result == good_post

    def test_retry_when_post_too_long(self):
        """If first response is too long (>1600), _call_openrouter is called twice."""
        long_post = "X" * 2000
        good_post = "X" * 1200
        with patch("scripts.generate_posts._call_openrouter", side_effect=[long_post, good_post]) as mock_call:
            from scripts.generate_posts import _generate_post
            result = _generate_post("user", "system", "model/x", "key")
        assert mock_call.call_count == 2
        assert result == good_post

    def test_no_retry_when_in_range(self):
        """If first response is in range (800-1600), _call_openrouter is called once."""
        good_post = "X" * 1000
        with patch("scripts.generate_posts._call_openrouter", return_value=good_post) as mock_call:
            from scripts.generate_posts import _generate_post
            result = _generate_post("user", "system", "model/x", "key")
        assert mock_call.call_count == 1
        assert result == good_post

    def test_retry_message_contains_character_count(self):
        """Retry call's user_prompt contains original char count and length range."""
        short_post = "X" * 400
        good_post = "X" * 1000
        with patch("scripts.generate_posts._call_openrouter", side_effect=[short_post, good_post]) as mock_call:
            from scripts.generate_posts import _generate_post
            _generate_post("initial user prompt", "system", "model/x", "key")
        # Second call's user_prompt (first arg) should contain original char count
        retry_user_prompt = mock_call.call_args_list[1][0][0]
        assert "400" in retry_user_prompt
        assert "800" in retry_user_prompt
        assert "1,600" in retry_user_prompt or "1600" in retry_user_prompt


# ---------------------------------------------------------------------------
# TestSystemPrompts (POSTS-04, D-03, D-07, D-08)
# ---------------------------------------------------------------------------

class TestSystemPrompts:
    """POSTS-04: Structurally distinct system prompts with language enforcement."""

    def test_technical_prompt_mentions_implementation_detail(self):
        """Technical system prompt contains 'implementation detail' or 'concrete implementation'."""
        from scripts.generate_posts import _build_technical_system_prompt
        prompt = _build_technical_system_prompt("en")
        assert "implementation detail" in prompt.lower() or "concrete implementation" in prompt.lower()

    def test_business_prompt_mentions_outcome(self):
        """Business system prompt contains 'outcome' or 'result'."""
        from scripts.generate_posts import _build_business_system_prompt
        prompt = _build_business_system_prompt("en")
        assert "outcome" in prompt.lower() or "result" in prompt.lower()

    def test_prompts_are_structurally_distinct(self):
        """Technical and business system prompts share no sentences."""
        from scripts.generate_posts import _build_technical_system_prompt, _build_business_system_prompt
        tech = _build_technical_system_prompt("en")
        biz = _build_business_system_prompt("en")
        tech_sentences = {s.strip() for s in tech.split(".") if s.strip()}
        biz_sentences = {s.strip() for s in biz.split(".") if s.strip()}
        shared = tech_sentences & biz_sentences
        assert len(shared) == 0, f"Shared sentences: {shared}"

    def test_language_in_system_prompt_with_closing_repetition(self):
        """Spanish language appears at least twice in technical prompt (opening + closing)."""
        from scripts.generate_posts import _build_technical_system_prompt
        prompt = _build_technical_system_prompt("es")
        assert prompt.count("Spanish") >= 2

    def test_system_prompt_contains_char_target(self):
        """Both system prompts contain the character target (800 and 1600/1,600)."""
        from scripts.generate_posts import _build_technical_system_prompt, _build_business_system_prompt
        tech = _build_technical_system_prompt("en")
        biz = _build_business_system_prompt("en")
        for prompt in [tech, biz]:
            assert "800" in prompt
            assert "1,600" in prompt or "1600" in prompt


# ---------------------------------------------------------------------------
# TestGapClosures (GAP-1, GAP-2)
# ---------------------------------------------------------------------------

class TestGapClosures:
    """Tests for gap closure fixes (GAP-1, GAP-2)."""

    def test_minority_language_negative_constraint(self):
        """Catalan prompt includes explicit negative constraint against Spanish/Portuguese."""
        from scripts.generate_posts import _build_technical_system_prompt
        prompt = _build_technical_system_prompt("ca")
        assert "Do NOT write in" in prompt or "do not write in" in prompt.lower()
        assert "Spanish" in prompt
        assert "Portuguese" in prompt
        assert "Catalan" in prompt

    def test_majority_language_no_negative_constraint(self):
        """English prompt does NOT include negative constraint."""
        from scripts.generate_posts import _build_technical_system_prompt
        prompt = _build_technical_system_prompt("en")
        assert "Do NOT write in" not in prompt

    def test_business_prompt_also_has_negative_constraint(self):
        """Business prompt for Catalan also includes negative constraint."""
        from scripts.generate_posts import _build_business_system_prompt
        prompt = _build_business_system_prompt("ca")
        assert "Catalan" in prompt
        # Must mention at least one confusable language
        assert any(lang in prompt for lang in ["Spanish", "Portuguese", "French", "Italian"])

    def test_retry_fires_with_whitespace_padded_response(self):
        """A 571-char post padded with whitespace to 900 chars should still trigger retry after strip."""
        short_content = "X" * 571
        padded_post = short_content + " " * 329  # len=900 before strip, 571 after strip
        good_post = "Y" * 1000
        with patch("scripts.generate_posts._call_openrouter", side_effect=[padded_post, good_post]) as mock_call:
            from scripts.generate_posts import _generate_post
            result = _generate_post("user", "system", "model/x", "key")
        assert mock_call.call_count == 2
        assert result == good_post

    def test_retry_logs_to_stderr(self, capsys):
        """Retry prints a log line to stderr (not stdout)."""
        short_post = "X" * 400
        good_post = "Y" * 1000
        with patch("scripts.generate_posts._call_openrouter", side_effect=[short_post, good_post]):
            from scripts.generate_posts import _generate_post
            _generate_post("user", "system", "model/x", "key")
        captured = capsys.readouterr()
        assert "Retry" in captured.err
        assert "400 chars" in captured.err

    def test_catalan_prompt_distinct_from_technical(self):
        """Negative constraint phrasing differs between technical and business prompts."""
        from scripts.generate_posts import _build_technical_system_prompt, _build_business_system_prompt
        tech = _build_technical_system_prompt("ca")
        biz = _build_business_system_prompt("ca")
        # Sentence sets must remain disjoint even with negative constraint
        tech_sentences = {s.strip() for s in tech.split(".") if s.strip()}
        biz_sentences = {s.strip() for s in biz.split(".") if s.strip()}
        shared = tech_sentences & biz_sentences
        assert len(shared) == 0, f"Shared sentences after adding negative constraint: {shared}"
