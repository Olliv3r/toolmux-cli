from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from toolmux_app.services.reporting import BugReportError, send_bug_report


def test_empty_bug_description_is_rejected():
    with pytest.raises(BugReportError):
        send_bug_report("   ")


def test_missing_screenshot_is_reported(tmp_path):
    missing = tmp_path / "missing.png"
    with pytest.raises(BugReportError):
        send_bug_report("erro", screenshot_path=str(missing))


def test_request_has_timeout():
    response = Mock()
    response.raise_for_status.return_value = None
    with patch("toolmux_app.services.reporting.requests.post", return_value=response) as post:
        send_bug_report("erro", timeout=3.5)
    assert post.call_args.kwargs["timeout"] == 3.5


def test_bug_report_uses_official_web_api_and_sends_cli_metadata():
    response = Mock()
    response.ok = True
    response.status_code = 200
    response.json.return_value = {"success": True}
    with patch("toolmux_app.services.reporting.requests.post", return_value=response) as post:
        send_bug_report("erro")

    assert post.call_args.args[0].endswith("/api/v1/reports/bugs")
    data = post.call_args.kwargs["data"]
    assert data["cli_version"]
    assert data["platform"]
    assert data["python_version"]


def test_bug_report_surfaces_api_rate_limit():
    response = Mock()
    response.ok = False
    response.status_code = 429
    response.json.return_value = {"success": False, "error": "rate limit exceeded"}
    with patch("toolmux_app.services.reporting.requests.post", return_value=response):
        with pytest.raises(BugReportError, match="Muitos relatórios"):
            send_bug_report("erro")


def test_bug_report_sends_bearer_api_token():
    response = Mock()
    response.ok = True
    response.status_code = 200
    response.json.return_value = {"success": True}
    with patch("toolmux_app.services.reporting.API_TOKEN", "api-secret"), patch("toolmux_app.services.reporting.requests.post", return_value=response) as post:
        send_bug_report("erro")
    assert post.call_args.kwargs["headers"]["Authorization"] == "Bearer api-secret"
