import subprocess
from collections.abc import Sequence


class CommandError(RuntimeError):
    pass


class CommandRunner:
    def run(self, args: Sequence[str]) -> None:
        try:
            subprocess.run(list(args), check=True)
        except FileNotFoundError as exc:
            raise CommandError(f"Comando não encontrado: {args[0]}") from exc
        except subprocess.CalledProcessError as exc:
            raise CommandError(
                f"Comando falhou com código {exc.returncode}: {' '.join(args)}"
            ) from exc
