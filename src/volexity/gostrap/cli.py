"""Implements the GoStrap command line interface."""

import logging
import shutil
import sys
from cmd import Cmd
from pathlib import Path
from typing import Final

from .models.cli_arguments import CLIArguments
from .sample_generator import SampleGenerator

logging.basicConfig()
logging.getLogger(__name__.rsplit(".", 1)[0]).setLevel(logging.INFO)

logger: Final[logging.Logger] = logging.getLogger(__name__)


def run_cli() -> None:
    """Implements the GoStrap command line interface."""
    args: Final[CLIArguments] = CLIArguments(sys.argv)

    storage_path: Final[Path] = Path("./storage")
    libs: Final[list[str]] = args.libs if len(args.libs) else []

    sample_gen: SampleGenerator = SampleGenerator(storage_path, display_progress=True)

    if args.show:
        available: Final[list[str]] = [*sample_gen.get_available_go_versions()]
        cmd: Final[Cmd] = Cmd()
        cmd.columnize(available, displaywidth=shutil.get_terminal_size().columns)
        return

    if len(args.output) > len(args.go_versions):
        logger.error("The number of output paths cannot exceed the number of samples.")
        sys.exit()

    install_paths: Final[list[tuple[str, Path]]] = sample_gen.generate(
        args.go_versions, libs, args.arch, args.platform, out_paths=args.output, force=args.force
    )

    for version, path in install_paths:
        logger.info(f'Sample for GO version "{version}" built at "{path}"')
