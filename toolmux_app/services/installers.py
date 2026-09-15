from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..catalog import CatalogTool
from .runner import CommandError, CommandRunner


class InstallerError(RuntimeError):
    pass


class BaseInstaller:
    def __init__(self, runner: CommandRunner, home: Path):
        self.runner = runner
        self.home = home

    def install(self, tool: "CatalogTool") -> None:
        raise NotImplementedError

    def install_dependencies(self, tool: "CatalogTool") -> None:
        dependencies = tool.dependency_packages
        if dependencies:
            self.runner.run(["apt", "install", *dependencies, "-y"])


class AptInstaller(BaseInstaller):
    def install(self, tool: "CatalogTool") -> None:
        self.install_dependencies(tool)
        if not getattr(tool, "package_name", None):
            raise InstallerError(f"{tool.name} não possui package_name configurado para APT.")
        self.runner.run(["apt", "install", tool.package_name, "-y"])


class GitInstaller(BaseInstaller):
    def install(self, tool: "CatalogTool") -> None:
        if not tool.link or not tool.name_repo:
            raise InstallerError(f"{tool.name} não possui repositório Git configurado.")

        self.install_dependencies(tool)
        destination = self.home / tool.name_repo

        if destination.exists():
            if not destination.is_dir():
                raise InstallerError(f"O destino existe e não é um diretório: {destination}")
            if (destination / ".git").is_dir():
                self.runner.run(["git", "-C", str(destination), "pull", "--ff-only"])
                return
            raise InstallerError(
                f"O diretório {destination} já existe e não é um repositório Git. "
                "Renomeie ou remova-o manualmente antes de continuar."
            )

        self.runner.run(["git", "clone", tool.link, str(destination)])

        if not destination.is_dir():
            raise InstallerError(f"O clone de {tool.name} terminou sem criar {destination}.")


class InstallerService:
    def __init__(self, runner: CommandRunner, home: Path):
        self._installers = {
            "apt": AptInstaller(runner, home),
            "git": GitInstaller(runner, home),
        }

    def install(self, tool: "CatalogTool") -> None:
        installer_name = tool.installation_type.name.lower()
        installer = self._installers.get(installer_name)
        if installer is None:
            raise InstallerError(
                f"Tipo de instalação '{installer_name}' ainda não é suportado pelo Toolmux CLI."
            )

        try:
            installer.install(tool)
        except CommandError as exc:
            raise InstallerError(str(exc)) from exc
