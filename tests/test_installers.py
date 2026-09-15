from types import SimpleNamespace

import pytest

from toolmux_app.services.installers import AptInstaller, GitInstaller, InstallerError


class FakeRunner:
    def __init__(self):
        self.commands = []

    def run(self, args):
        self.commands.append(list(args))


def tool(**overrides):
    values = {
        "name": "Example",
        "alias": "example-alias",
        "package_name": "example-package",
        "dependencies": "git python3",
        "link": "https://github.com/example/example.git",
        "name_repo": "example",
    }
    values.update(overrides)
    obj = SimpleNamespace(**values)
    obj.dependency_packages = obj.dependencies.split() if obj.dependencies else []
    return obj


def test_apt_installs_dependencies_then_explicit_package_name(tmp_path):
    runner = FakeRunner()
    AptInstaller(runner, tmp_path).install(tool())
    assert runner.commands == [
        ["apt", "install", "git", "python3", "-y"],
        ["apt", "install", "example-package", "-y"],
    ]


def test_apt_rejects_missing_package_name(tmp_path):
    with pytest.raises(InstallerError):
        AptInstaller(FakeRunner(), tmp_path).install(tool(package_name=""))


def test_git_uses_argument_list_not_shell_string(tmp_path):
    target = tmp_path / "example"

    class CreatingRunner(FakeRunner):
        def run(self, args):
            super().run(args)
            if args[:2] == ["git", "clone"]:
                target.mkdir()

    runner = CreatingRunner()
    GitInstaller(runner, tmp_path).install(tool())
    assert runner.commands[-1] == [
        "git", "clone", "https://github.com/example/example.git", str(target),
    ]


def test_git_rejects_missing_repository_data(tmp_path):
    with pytest.raises(InstallerError):
        GitInstaller(FakeRunner(), tmp_path).install(tool(link=""))


def test_git_existing_repository_is_updated_without_deletion(tmp_path):
    runner = FakeRunner()
    target = tmp_path / "example"
    (target / ".git").mkdir(parents=True)
    marker = target / "local-change.txt"
    marker.write_text("preserve me")
    GitInstaller(runner, tmp_path).install(tool())
    assert marker.read_text() == "preserve me"
    assert runner.commands == [
        ["apt", "install", "git", "python3", "-y"],
        ["git", "-C", str(target), "pull", "--ff-only"],
    ]
