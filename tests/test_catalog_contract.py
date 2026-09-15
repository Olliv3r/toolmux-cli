import pytest
import json
from unittest.mock import Mock, patch

from toolmux_app.catalog import CatalogError, CatalogService


def sample_catalog():
    return {
        "contract_version": "2.0",
        "schema_version": 2,
        "revision": "abc123",
        "generated_at": "2026-09-14T00:00:00+00:00",
        "tool_count": 1,
        "tools": [
            {
                "id": 7,
                "name": "Example Tool",
                "alias": "example-tool",
                "executable": "example",
                "description": "Example",
                "author": "Toolmux",
                "status": "Ativa",
                "categories": ["Recon"],
                "installations": [
                    {
                        "type": "git",
                        "default": True,
                        "package_name": None,
                        "repository": {
                            "name": "example-tool",
                            "url": "https://github.com/example/example-tool.git",
                        },
                        "dependencies": [
                            {"name": "git", "package_name": "git", "kind": "runtime", "optional": False},
                            {"name": "python3", "package_name": "python3", "kind": "runtime", "optional": False},
                        ],
                        "tip": "run example",
                    }
                ],
                "updated_at": "2026-09-14T00:00:00+00:00",
            }
        ],
    }


def test_remote_catalog_maps_web_contract_to_installer_model(tmp_path):
    response = Mock()
    response.status_code = 200
    response.headers = {"ETag": '"abc"'}
    response.json.return_value = sample_catalog()
    response.raise_for_status.return_value = None

    service = CatalogService(cache_path=tmp_path / "catalog.json", etag_path=tmp_path / "catalog.etag")
    with patch("toolmux_app.catalog.requests.get", return_value=response):
        catalog = service.load()

    assert catalog.source == "api"
    assert catalog.categories[0].name == "Recon"
    tool = catalog.tools[0]
    assert tool.installation_type.name == "git"
    assert tool.dependency_packages == ["git", "python3"]
    assert tool.link == "https://github.com/example/example-tool.git"
    assert tool.name_repo == "example-tool"


def test_apt_contract_uses_package_name_not_alias(tmp_path):
    payload = sample_catalog()
    payload["tools"][0]["installations"][0] = {
        "type": "apt",
        "default": True,
        "package_name": "real-debian-package",
        "repository": {"name": None, "url": None},
        "dependencies": [],
        "tip": None,
    }
    response = Mock(status_code=200, headers={})
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    service = CatalogService(cache_path=tmp_path / "catalog.json", etag_path=tmp_path / "catalog.etag")
    with patch("toolmux_app.catalog.requests.get", return_value=response):
        tool = service.load().tools[0]
    assert tool.alias == "example-tool"
    assert tool.package_name == "real-debian-package"


def test_304_uses_validated_cache(tmp_path):
    cache = tmp_path / "catalog.json"
    cache.write_text(json.dumps(sample_catalog()), encoding="utf-8")
    etag = tmp_path / "catalog.etag"
    etag.write_text('"abc"', encoding="utf-8")
    response = Mock(status_code=304)
    service = CatalogService(cache_path=cache, etag_path=etag)
    with patch("toolmux_app.catalog.requests.get", return_value=response) as get:
        catalog = service.load()
    assert catalog.tools[0].alias == "example-tool"
    assert get.call_args.kwargs["headers"]["If-None-Match"] == '"abc"'


def test_incompatible_contract_is_not_hidden_by_legacy_fallback(tmp_path):
    payload = sample_catalog()
    payload["contract_version"] = "1.0"
    response = Mock(status_code=200, headers={})
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    service = CatalogService(cache_path=tmp_path / "missing.json", etag_path=tmp_path / "missing.etag")
    with patch("toolmux_app.catalog.requests.get", return_value=response):
        with pytest.raises(CatalogError, match="contrato"):
            service.load()


def test_network_failure_does_not_use_cache_by_default(tmp_path):
    cache = tmp_path / "catalog.json"
    cache.write_text(json.dumps(sample_catalog()), encoding="utf-8")
    service = CatalogService(cache_path=cache, etag_path=tmp_path / "missing.etag")
    with patch("toolmux_app.catalog.requests.get", side_effect=OSError("offline")):
        with pytest.raises(CatalogError, match="Não foi possível carregar"):
            service.load()


def test_offline_cache_requires_explicit_opt_in(tmp_path):
    cache = tmp_path / "catalog.json"
    cache.write_text(json.dumps(sample_catalog()), encoding="utf-8")
    service = CatalogService(cache_path=cache, etag_path=tmp_path / "missing.etag", allow_offline_cache=True)
    with patch("toolmux_app.catalog.requests.get", side_effect=OSError("offline")):
        catalog = service.load()
    assert catalog.source == "cache-offline"
    assert len(catalog.tools) == 1


def test_catalog_rejects_multiple_default_installations(tmp_path):
    payload = sample_catalog()
    payload["tools"][0]["installations"].append({
        "type": "apt", "default": True, "package_name": "second-package",
        "repository": {"name": None, "url": None}, "dependencies": [], "tip": None,
    })
    service = CatalogService(cache_path=tmp_path / "catalog.json", etag_path=tmp_path / "catalog.etag")
    with pytest.raises(CatalogError, match="exatamente uma instalação default"):
        service._from_payload(payload, source="test")


def test_catalog_rejects_invalid_dependency_metadata(tmp_path):
    payload = sample_catalog()
    payload["tools"][0]["installations"][0]["dependencies"][0]["kind"] = "unknown"
    service = CatalogService(cache_path=tmp_path / "catalog.json", etag_path=tmp_path / "catalog.etag")
    with pytest.raises(CatalogError, match="Metadados de dependência inválidos"):
        service._from_payload(payload, source="test")


def test_catalog_rejects_inconsistent_tool_count(tmp_path):
    payload = sample_catalog()
    payload["tool_count"] = 99
    service = CatalogService(cache_path=tmp_path / "catalog.json", etag_path=tmp_path / "catalog.etag")
    with pytest.raises(CatalogError, match="tool_count"):
        service._from_payload(payload, source="test")


def test_catalog_rejects_missing_generated_at(tmp_path):
    payload = sample_catalog()
    payload.pop("generated_at")
    service = CatalogService(cache_path=tmp_path / "catalog.json", etag_path=tmp_path / "catalog.etag")
    with pytest.raises(CatalogError, match="generated_at"):
        service._from_payload(payload, source="test")


def test_catalog_sends_bearer_api_token(tmp_path):
    response = Mock(status_code=200, headers={})
    response.json.return_value = sample_catalog()
    response.raise_for_status.return_value = None
    service = CatalogService(cache_path=tmp_path / "catalog.json", etag_path=tmp_path / "catalog.etag")
    with patch("toolmux_app.catalog.API_TOKEN", "api-secret"), patch("toolmux_app.catalog.requests.get", return_value=response) as get:
        service.load()
    assert get.call_args.kwargs["headers"]["Authorization"] == "Bearer api-secret"
