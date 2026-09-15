from pathlib import Path
import re
import shutil

class Fore:
    WHITE = "\033[37m"
    YELLOW = "\033[33m"
    GREEN = "\033[32m"
    RED = "\033[31m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    BLUE = "\033[34m"


class Style:
    RESET_ALL = "\033[0m"


_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
RESOURCE_DIR = Path(__file__).resolve().parent / "resources" / "banners"


def load_banner(name: str, center: bool = False) -> str:
    path = RESOURCE_DIR / f"{name}_banner.txt"
    if not path.exists():
        raise FileNotFoundError(f"Banner '{name}' não encontrado em {path}")

    lines = path.read_text(encoding="utf-8").splitlines()
    if center:
        width = shutil.get_terminal_size((80, 20)).columns
        lines = [line.strip().center(width) for line in lines]
    return "\n".join(line.rstrip() for line in lines)


def print_status(message: str, color: str = "white") -> None:
    colors = {
        "white": Fore.WHITE,
        "yellow": Fore.YELLOW,
        "green": Fore.GREEN,
        "red": Fore.RED,
        "magenta": Fore.MAGENTA,
        "cyan": Fore.CYAN,
        "blue": Fore.BLUE,
    }
    print(f"{colors.get(color, Fore.WHITE)}{message}{Style.RESET_ALL}")


def print_centered(text: str, fillchar: str = " ") -> None:
    width = shutil.get_terminal_size((80, 20)).columns
    print(f"\n{f' {text} '.center(width, fillchar)}\n")


def _visible_len(text: str) -> int:
    return len(_ANSI_RE.sub("", text))


def display_group(items: list[object], terminal_width: int | None = None) -> list[int]:
    if not items:
        print_centered("Nenhuma categoria ou ferramenta encontrada.")
        return []

    width = terminal_width or shutil.get_terminal_size((80, 20)).columns
    if width < 60:
        column_count = 1
    elif width < 90:
        column_count = 2
    elif width < 130:
        column_count = 3
    else:
        column_count = 4

    entries = [f"{Fore.CYAN}{index}) {Fore.WHITE}{item.name}{Style.RESET_ALL}" for index, item in enumerate(items, 1)]
    rows = (len(entries) + column_count - 1) // column_count
    columns = [entries[i * rows:(i + 1) * rows] for i in range(column_count)]
    cell_width = max(_visible_len(entry) for entry in entries) + 3

    for row_index in range(rows):
        cells: list[str] = []
        for column in columns:
            if row_index < len(column):
                entry = column[row_index]
                cells.append(entry + " " * max(0, cell_width - _visible_len(entry)))
        print("".join(cells).rstrip())

    return [item.id for item in items]
