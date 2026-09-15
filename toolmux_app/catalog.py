from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any

import requests

from .config import (
    ALLOW_OFFLINE_CACHE,
    API_TOKEN,
    CATALOG_CACHE_PATH,
    CATALOG_CONTRACT_VERSION,
    CATALOG_ETAG_PATH,
    CATALOG_SCHEMA_VERSION,
    CATALOG_TIMEOUT,
    CATALOG_URL,
)


class CatalogError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class CatalogInstallationType:
    name: str


@dataclass(frozen=True, slots=True)
class CatalogCategory:
    id: int
    name: str


@dataclass(frozen=True, slots=True)
class CatalogTool:
    id: int
    name: str
    alias: str
    installation_type: CatalogInstallationType
    executable: str | None = None
    package_name: str | None = None
    name_repo: str | None = None
    link: str | None = None
    dependencies: str | None = None
    installation_tip: str | None = None
    description: str | None = None
    categories: list[CatalogCategory] = field(default_factory=list)

    @property
    def dependency_packages(self) -> list[str]:
        return self.dependencies.split() if self.dependencies else []


@dataclass(slots=True)
class CatalogSnapshot:
    revision: str
    categories: list[CatalogCategory]
    tools: list[CatalogTool]
    source: str

    def tools_by_category(self, category_id: int) -> list[CatalogTool]:
        return [tool for tool in self.tools if any(c.id == category_id for c in tool.categories)]


class CatalogService:
    """Loads the authoritative Web API catalog.

    By default an API error is surfaced to the user instead of being hidden by stale
    local data. A validated cache may be used only when TOOLMUX_ALLOW_OFFLINE_CACHE=1.
    """

    def __init__(
        self,
        *,
        url: str = CATALOG_URL,
        cache_path: Path = CATALOG_CACHE_PATH,
        etag_path: Path = CATALOG_ETAG_PATH,
        timeout: float = CATALOG_TIMEOUT,
        allow_offline_cache: bool = ALLOW_OFFLINE_CACHE,
    ) -> None:
        self.url = url
        self.cache_path = cache_path
        self.etag_path = etag_path
        self.timeout = timeout
        self.allow_offline_cache = allow_offline_cache
        self._snapshot: CatalogSnapshot | None = None

    def load(self, *, refresh: bool = False) -> CatalogSnapshot:
        if self._snapshot is not None and not refresh:
            return self._snapshot

        try:
            payload, source = self._fetch_remote()
            self._snapshot = self._from_payload(payload, source=source)
            return self._snapshot
        except (CatalogError, OSError, requests.RequestException, ValueError, json.JSONDecodeError) as exc:
            if self.allow_offline_cache:
                cached = self._read_cache(suppress_errors=True)
                if cached is not None:
                    try:
                        self._snapshot = self._from_payload(cached, source="cache-offline")
                        return self._snapshot
                    except CatalogError:
                        pass
            raise CatalogError(
                f"Não foi possível carregar o catálogo da API em {self.url}: {exc}. "
                "Verifique TOOLMUX_API_BASE_URL e TOOLMUX_API_TOKEN. "
                "Para permitir cache validado quando estiver offline, defina TOOLMUX_ALLOW_OFFLINE_CACHE=1."
            ) from exc

    def _fetch_remote(self) -> tuple[dict[str, Any], str]:
        headers = {"Accept": "application/json", "User-Agent": "toolmux-cli/0.2"}
        if API_TOKEN:
            headers["Authorization"] = f"Bearer {API_TOKEN}"
        if self.etag_path.exists() and self.cache_path.exists():
            etag = self.etag_path.read_text(encoding="utf-8").strip()
            if etag:
                headers["If-None-Match"] = etag

        response = requests.get(self.url, headers=headers, timeout=self.timeout)
        if response.status_code == 304:
            payload = self._read_cache()
            if payload is None:
                # A 304 without a local cache is unusable. Retry once without ETag.
                headers.pop("If-None-Match", None)
                response = requests.get(self.url, headers=headers, timeout=self.timeout)
            else:
                return payload, "api-304"

        response.raise_for_status()
        payload = response.json()
        self._validate_payload(payload)
        self._write_cache(payload, response.headers.get("ETag"))
        return payload, "api"

    def _write_cache(self, payload: dict[str, Any], etag: str | None) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.cache_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.cache_path)
        if etag:
            self.etag_path.write_text(etag, encoding="utf-8")

    def _read_cache(self, *, suppress_errors: bool = False) -> dict[str, Any] | None:
        if not self.cache_path.exists():
            return None
        try:
            payload = json.loads(self.cache_path.read_text(encoding="utf-8"))
            self._validate_payload(payload)
            return payload
        except (OSError, ValueError, json.JSONDecodeError, CatalogError):
            if suppress_errors:
                return None
            raise

    @staticmethod
    def _validate_payload(payload: dict[str, Any]) -> None:
        if not isinstance(payload, dict):
            raise CatalogError("Catálogo da API inválido: objeto JSON esperado.")
        if payload.get("schema_version") != CATALOG_SCHEMA_VERSION:
            raise CatalogError("Versão de schema do catálogo incompatível.")
        if payload.get("contract_version") != CATALOG_CONTRACT_VERSION:
            raise CatalogError("Versão do contrato da API incompatível.")
        if not isinstance(payload.get("revision"), str) or not payload["revision"]:
            raise CatalogError("Catálogo da API sem revision válida.")
        if not isinstance(payload.get("generated_at"), str) or not payload["generated_at"]:
            raise CatalogError("Catálogo da API sem generated_at válido.")
        if not isinstance(payload.get("tools"), list):
            raise CatalogError("Catálogo da API sem lista de tools.")
        tool_count = payload.get("tool_count")
        if not isinstance(tool_count, int) or isinstance(tool_count, bool) or tool_count < 0:
            raise CatalogError("Catálogo da API sem tool_count válido.")
        if tool_count != len(payload["tools"]):
            raise CatalogError("tool_count do catálogo não corresponde à lista de tools.")

    def _from_payload(self, payload: dict[str, Any], *, source: str) -> CatalogSnapshot:
        self._validate_payload(payload)
        category_ids: dict[str, int] = {}
        categories: list[CatalogCategory] = []
        tools: list[CatalogTool] = []

        for raw in payload["tools"]:
            if not isinstance(raw, dict) or not all(isinstance(raw.get(k), (str, int)) for k in ("id", "name", "alias")):
                raise CatalogError("Entrada de ferramenta inválida.")
            installations = raw.get("installations")
            if not isinstance(installations, list) or not installations:
                raise CatalogError(f"Ferramenta {raw.get('alias')} sem installations.")
            defaults = [item for item in installations if isinstance(item, dict) and item.get("default") is True]
            if len(defaults) != 1:
                raise CatalogError(f"Ferramenta {raw.get('alias')} deve possuir exatamente uma instalação default.")
            installation = defaults[0]
            install_type = installation.get("type")
            if install_type not in {"apt", "git"}:
                raise CatalogError(f"Tipo de instalação não suportado: {install_type}.")
            repository = installation.get("repository") or {}
            if not isinstance(repository, dict):
                raise CatalogError(f"Repositório inválido para {raw.get('alias')}.")
            deps = installation.get("dependencies") or []
            if not isinstance(deps, list):
                raise CatalogError(f"Dependências inválidas para {raw.get('alias')}.")
            dependency_packages = []
            for dep in deps:
                if not isinstance(dep, dict) or not isinstance(dep.get("name"), str) or not isinstance(dep.get("package_name"), str):
                    raise CatalogError(f"Dependência inválida para {raw.get('alias')}.")
                if dep.get("kind") not in {"runtime", "build"} or not isinstance(dep.get("optional"), bool):
                    raise CatalogError(f"Metadados de dependência inválidos para {raw.get('alias')}.")
                if not dep["optional"]:
                    dependency_packages.append(dep["package_name"])

            tool_categories: list[CatalogCategory] = []
            for category_name in raw.get("categories") or []:
                if not isinstance(category_name, str) or not category_name:
                    continue
                if category_name not in category_ids:
                    category_ids[category_name] = len(category_ids) + 1
                    categories.append(CatalogCategory(category_ids[category_name], category_name))
                tool_categories.append(CatalogCategory(category_ids[category_name], category_name))

            package_name = installation.get("package_name")
            if install_type == "apt" and not package_name:
                raise CatalogError(f"Ferramenta {raw.get('alias')} sem package_name para APT.")
            if install_type == "git" and (not repository.get("name") or not repository.get("url")):
                raise CatalogError(f"Ferramenta {raw.get('alias')} sem repositório Git completo.")

            tools.append(CatalogTool(
                id=int(raw["id"]), name=str(raw["name"]), alias=str(raw["alias"]),
                executable=raw.get("executable"), package_name=package_name,
                name_repo=repository.get("name"), link=repository.get("url"),
                dependencies=" ".join(dependency_packages) or None,
                installation_tip=installation.get("tip"), description=raw.get("description"),
                installation_type=CatalogInstallationType(install_type), categories=tool_categories,
            ))

        categories.sort(key=lambda c: c.name.lower())
        tools.sort(key=lambda t: t.name.lower())
        return CatalogSnapshot(payload["revision"], categories, tools, source)
