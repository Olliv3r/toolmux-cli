from pathlib import Path
import platform

import requests

from ..config import API_TOKEN, BUG_REPORT_URL, VERSION


class BugReportError(RuntimeError):
    pass


def _error_message(response: requests.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        payload = None
    if isinstance(payload, dict):
        detail = payload.get("error") or payload.get("message")
        if isinstance(detail, str) and detail.strip():
            return detail.strip()
    return f"HTTP {response.status_code}"


def send_bug_report(
    description: str,
    user_name: str = "Unknown",
    screenshot_path: str | None = None,
    timeout: float = 15.0,
    *,
    installation_type: str | None = None,
    tool_name: str | None = None,
) -> None:
    if not description.strip():
        raise BugReportError("A descrição do problema não pode ficar vazia.")

    data = {
        "description": description.strip(),
        "user_name": user_name.strip() or "Unknown",
        "cli_version": VERSION,
        "platform": platform.platform(),
        "python_version": platform.python_version(),
    }
    if installation_type:
        data["installation_type"] = installation_type.strip()
    if tool_name:
        data["tool_name"] = tool_name.strip()

    headers = {"Authorization": f"Bearer {API_TOKEN}"} if API_TOKEN else {}

    try:
        if screenshot_path:
            path = Path(screenshot_path).expanduser()
            with path.open("rb") as screenshot:
                response = requests.post(
                    BUG_REPORT_URL,
                    data=data,
                    files={"screenshot": screenshot},
                    headers=headers,
                    timeout=timeout,
                )
        else:
            response = requests.post(BUG_REPORT_URL, data=data, headers=headers, timeout=timeout)

        if not response.ok:
            detail = _error_message(response)
            if response.status_code == 429:
                raise BugReportError("Muitos relatórios enviados. Tente novamente mais tarde.")
            if response.status_code == 413:
                raise BugReportError("A captura de tela excede o tamanho permitido pela API.")
            raise BugReportError(f"A API recusou o relatório: {detail}")

        try:
            payload = response.json()
        except ValueError:
            payload = None
        if isinstance(payload, dict) and payload.get("success") is False:
            raise BugReportError(str(payload.get("error") or "A API não aceitou o relatório."))
    except BugReportError:
        raise
    except (OSError, requests.RequestException) as exc:
        raise BugReportError(f"Não foi possível enviar o relatório: {exc}") from exc
