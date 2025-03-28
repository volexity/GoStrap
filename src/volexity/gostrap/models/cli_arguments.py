"""CLI Arguments data model."""

import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Final

from .arch_types import ArchTypes
from .platform_types import PlatformTypes


class CLIArguments:
    """CLI Arguments data model."""

    def __init__(self, argv: list[str]) -> None:
        """Initialize a new instance of the CLI Arguments data model.

        Args:
            argv: Raw CLI arguments.
        """
        parser: Final[ArgumentParser] = ArgumentParser(prog=Path(argv[0]).name)

        parser.add_argument(
            "-l", "--libs", metavar="LIBS", nargs="*", help="List of GO libs to include in the generated samples."
        )
        parser.add_argument(
            "-g", "--go", metavar="VERSIONS", nargs="*", help="List of GO version to build the samples with."
        )
        parser.add_argument("-a", "--arch", metavar="ARCH", help="Target CPU architecture.")
        parser.add_argument("-p", "--platform", metavar="PLATFORM", help="Target Operaring System.")
        parser.add_argument("-o", "--output", nargs="*", help="Path where to save the generated files.")
        parser.add_argument("-f", "--force", action="store_true", help="Force build existing samples.")
        parser.add_argument("-s", "--show", action="store_true", help="Show available go versions.")

        parsed_args: Final[Namespace] = parser.parse_args(argv[1:])

        if len(argv) <= 1:
            parser.print_usage()
            sys.exit()

        self._libs: Final[list[str]] = (
            [lib for row in (libs.split(",") for libs in parsed_args.libs) for lib in row] if parsed_args.libs else []
        )

        self._go_versions: Final[list[str]] = (
            [ver for row in (go.split(",") for go in parsed_args.go) for ver in row] if parsed_args.go else []
        )

        self._arch: Final[ArchTypes | None] = ArchTypes(parsed_args.arch) if parsed_args.arch else None
        self._platform: Final[PlatformTypes | None] = (
            PlatformTypes(parsed_args.platform) if parsed_args.platform else None
        )
        self._output: Final[list[Path]] = (
            [Path(path).resolve() for row in (out_path.split(",") for out_path in parsed_args.output) for path in row]
            if parsed_args.output
            else []
        )
        self._force: Final[bool] = parsed_args.force
        self._show: Final[bool] = parsed_args.show

    @property
    def libs(self) -> list[str]:
        """Returns the list of GO libraries to use.

        Returns: The necessary GO libraries.
        """
        return self._libs.copy()

    @property
    def go_versions(self) -> list[str]:
        """Returns the targetted GO version.

        Returns: GO versions to build with.
        """
        return self._go_versions.copy()

    @property
    def arch(self) -> ArchTypes | None:
        """Returns the target architecture.

        Returns: The target architecture.
        """
        return self._arch

    @property
    def platform(self) -> PlatformTypes | None:
        """Returns the target operating system.

        Returns: The target operating system.
        """
        return self._platform

    @property
    def output(self) -> list[Path]:
        """Returns the path where to save the generated files.

        Returns: The path where to save the generated files.
        """
        return self._output.copy()

    @property
    def force(self) -> bool:
        """Return wether samples should be forced built.

        Returns: Whether samples should be forced built.
        """
        return self._force

    @property
    def show(self) -> bool:
        """Returns wether to show available GO versions.

        Returns: Whether to show available GO versions.
        """
        return self._show
