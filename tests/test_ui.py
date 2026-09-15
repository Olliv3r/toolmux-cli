import pytest

from toolmux_app.ui import load_banner


def test_existing_banner_loads():
    assert "Toolmux" in load_banner("menu")


def test_missing_banner_raises_correct_exception():
    with pytest.raises(FileNotFoundError):
        load_banner("does-not-exist")
