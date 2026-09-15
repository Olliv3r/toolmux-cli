from __future__ import annotations

from enum import Enum, auto
import shutil
import sys

from .config import APP_NAME, AUTHOR, TERMUX_DIR, TERMUX_HOME, VERSION
from .catalog import CatalogError, CatalogService
from .services.installers import InstallerError, InstallerService
from .services.reporting import BugReportError, send_bug_report
from .services.runner import CommandRunner
from .ui import Fore, Style, display_group, load_banner, print_centered, print_status


PROMPT = f"\033[1;34m{APP_NAME}\033[0m > "


class Screen(Enum):
    MAIN = auto()
    CATEGORIES = auto()
    TOOLS = auto()
    REPORT = auto()
    HELP = auto()
    EXIT = auto()


class ToolmuxCLI:
    def __init__(self) -> None:
        self.selected_category_id: int | None = None
        self.runner = CommandRunner()
        self.installer_service = InstallerService(self.runner, TERMUX_HOME)
        self.catalog_service = CatalogService()
        self.menu_banner = load_banner("menu")
        self.report_banner = load_banner("report", center=True)

    @staticmethod
    def _clear() -> None:
        print("\033[2J\033[H", end="")

    @staticmethod
    def _input(prompt: str = PROMPT) -> str | None:
        try:
            return input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            return None

    def run(self) -> None:
        screen = Screen.MAIN
        while screen is not Screen.EXIT:
            if screen is Screen.MAIN:
                screen = self.main_menu()
            elif screen is Screen.CATEGORIES:
                screen = self.categories_menu()
            elif screen is Screen.TOOLS:
                screen = self.tools_menu()
            elif screen is Screen.REPORT:
                screen = self.report_menu()
            elif screen is Screen.HELP:
                screen = self.help_menu()

        print_status("\nPrograma encerrado.\n", "red")

    def main_menu(self) -> Screen:
        self._clear()
        print(self.menu_banner)
        try:
            catalog = self.catalog_service.load()
        except CatalogError as exc:
            print_status(f"Erro ao carregar catálogo: {exc}", "red")
            self._pause()
            return Screen.EXIT
        total_tools = len(catalog.tools)

        print(
            f"\t{Fore.GREEN}v{VERSION}\n\n"
            f"{Fore.WHITE}+ -- -- +=[ Author: {AUTHOR} | Homepage: https://toolmuxapp.pythonanywhere.com\n"
            f"+ -- -- +=[ {total_tools} Tools | Fonte: {catalog.source}{Style.RESET_ALL}"
        )
        print(
            f"\n\n{Fore.CYAN}1) {Fore.WHITE}View Categories\n"
            f"{Fore.CYAN}2) {Fore.WHITE}Report Bugs\n"
            f"{Fore.CYAN}3) {Fore.WHITE}Help\n"
            f"{Fore.CYAN}q) {Fore.WHITE}Exit{Style.RESET_ALL}\n"
        )

        choice = self._input()
        return {
            "1": Screen.CATEGORIES,
            "2": Screen.REPORT,
            "3": Screen.HELP,
            "q": Screen.EXIT,
        }.get(choice, Screen.MAIN) if choice is not None else Screen.EXIT

    def categories_menu(self) -> Screen:
        self._clear()
        print(self.menu_banner)
        try:
            categories = self.catalog_service.load().categories
        except CatalogError as exc:
            print_status(f"Erro ao carregar catálogo: {exc}", "red")
            self._pause()
            return Screen.MAIN

        print_centered("Todas as categorias", "*")
        ids = display_group(categories, shutil.get_terminal_size((80, 20)).columns)
        print("\nSelecione uma categoria, [Enter] para retornar ou [q] para encerrar.")

        choice = self._input()
        if choice is None or choice.lower() == "q":
            return Screen.EXIT
        if choice == "":
            return Screen.MAIN
        if choice.isdigit() and 1 <= int(choice) <= len(ids):
            self.selected_category_id = ids[int(choice) - 1]
            return Screen.TOOLS

        print_status(f"Opção inválida. Use valores entre 1 e {len(ids)}.", "red")
        self._pause()
        return Screen.CATEGORIES

    def tools_menu(self) -> Screen:
        if self.selected_category_id is None:
            return Screen.CATEGORIES

        self._clear()
        print(self.menu_banner)
        try:
            tools = self.catalog_service.load().tools_by_category(self.selected_category_id)
        except CatalogError as exc:
            print_status(f"Erro ao carregar catálogo: {exc}", "red")
            self._pause()
            return Screen.CATEGORIES

        print_centered("Todas as Ferramentas", "*")
        display_group(tools, shutil.get_terminal_size((80, 20)).columns)
        print("\nSelecione uma ou mais ferramentas separadas por vírgula, [Enter] para voltar ou [q] para encerrar.")

        choice = self._input()
        if choice is None or choice.lower() == "q":
            return Screen.EXIT
        if choice == "":
            return Screen.CATEGORIES

        selected_tools = []
        invalid_options = []
        for raw_option in choice.split(","):
            option = raw_option.strip()
            if option.isdigit() and 1 <= int(option) <= len(tools):
                selected_tools.append(tools[int(option) - 1])
            else:
                invalid_options.append(option or "<vazio>")

        if invalid_options:
            print_status(f"Opções inválidas: {', '.join(invalid_options)}", "red")
            self._pause()
            return Screen.TOOLS

        for tool in selected_tools:
            self._install_tool(tool)

        self._pause("\nPressione [Enter] para voltar às ferramentas...")
        return Screen.TOOLS

    def _install_tool(self, tool) -> None:
        print_status(f"\nInstalando {tool.name} via {tool.installation_type.name.upper()}...", "green")
        try:
            self.installer_service.install(tool)
        except InstallerError as exc:
            print_status(f"❌ {tool.name}: {exc}", "red")
            return

        print_status(f"✅ {tool.name} instalado com sucesso!", "green")
        tip = (tool.installation_tip or "").strip()
        if tip:
            print_status("Dica para finalizar a configuração:", "blue")
            print_status(tip, "yellow")

    def report_menu(self) -> Screen:
        self._clear()
        print(self.report_banner)
        print_centered("Relatório de Bug - Toolmux")

        description = self._input("Descreva o problema encontrado:\n> ")
        if description is None:
            return Screen.EXIT
        if not description:
            print_status("A descrição não pode ficar vazia.", "red")
            self._pause()
            return Screen.REPORT

        screenshot = self._input("Caminho da captura de tela (ou Enter para pular):\n> ")
        if screenshot is None:
            return Screen.EXIT
        user_name = self._input("Seu nome (ou Enter para pular):\n> ")
        if user_name is None:
            return Screen.EXIT

        try:
            send_bug_report(description, user_name or "Unknown", screenshot or None)
        except BugReportError as exc:
            print_status(str(exc), "red")
        else:
            print_status("Bug report enviado com sucesso!", "green")
        self._pause()
        return Screen.MAIN

    def help_menu(self) -> Screen:
        self._clear()
        print(self.menu_banner)
        print_centered("Ajuda")
        print("1. Escolha uma categoria.\n2. Digite o número de uma ferramenta ou vários números separados por vírgula.\n3. O Toolmux instala dependências e a ferramenta sem executar comandos armazenados no banco.\n4. Dicas pós-instalação são apenas exibidas para você revisar e executar manualmente.")
        self._pause()
        return Screen.MAIN

    def _pause(self, message: str = "\nPressione [Enter] para continuar...") -> None:
        self._input(message)


def check_termux_os() -> bool:
    return TERMUX_DIR.exists()


def main() -> int:
    if not check_termux_os():
        print_status("[×] Termux OS não foi detectado", "red")
        return 1

    print_status("[√] Termux OS detectado", "green")
    ToolmuxCLI().run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
