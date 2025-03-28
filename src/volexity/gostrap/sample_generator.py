"""Configurable GO sample generator."""

import logging
import os
import platform as sysplatform
import subprocess
from base64 import urlsafe_b64encode
from collections.abc import Iterable
from itertools import zip_longest
from pathlib import Path
from typing import Final

from multiprocess import Process, Queue  # type: ignore[import-untyped]
from yaspin import yaspin

from volexity.gittoolfetcher.git_tool_fetcher import GitToolFetcher

from .models.arch_types import ArchTypes
from .models.platform_types import PlatformTypes

GO_REPO_NAME: str = "golang/go"

DEFAULT_LIBS: list[str] = [
    "os",
    "compress/bzip2",
    "compress/flate",
    "compress/gzip",
    "compress/lzw",
    "compress/zlib",
    "archive/tar",
    "archive/zip",
    "crypto",
    "io",
    "net",
    "path",
    "regexp",
    "strings",
    "syscall",
    "unicode",
]

logging.getLogger("volexity.gittoolfetcher").setLevel(logging.WARNING)
logger: Final[logging.Logger] = logging.getLogger(__name__)


class SampleGenerator:
    """Configurable GO sample generator."""

    def __init__(self, storage_path: Path, display_progress: bool = False) -> None:
        """Initialize the sample generator context.

        Args:
            storage_path: The top level storage directory allocated to the SampleGenerator.
            display_progress: Weather to output progress updates to the console.
        """
        # Initialise the storage paths topology.
        self._storage_base: Final[Path] = storage_path.resolve()
        self._storage_git: Final[Path] = self._storage_base / "git_project_manager/golang"
        self._storage_build: Final[Path] = self._storage_base / "build"

        # Ensure the above paths are available on disk.
        self._storage_base.mkdir(parents=True, exist_ok=True)
        self._storage_git.mkdir(parents=True, exist_ok=True)
        self._storage_build.mkdir(parents=True, exist_ok=True)

        self._display_progress = display_progress

        # Initialize the underlying git project manager.
        self._git_project_manager: Final[GitToolFetcher] = GitToolFetcher(
            GO_REPO_NAME,
            self._storage_git,
            bin_path=Path("bin"),
            install_callback=self._go_install_proc,
            uninstall_callback=self._go_uninstall_proc,
            display_progress=display_progress,
        )

    @staticmethod
    def _go_install_proc(version: str, archive_data_path: Path, install_path: Path) -> None:  # noqa: ARG004
        """Callback procedure to install a GO version.

        Args:
            version: The Go version being installed.
            archive_data_path: The path to the extracted source archive data.
            install_path: The target installation path.
        """
        logger.debug(f"Installing from: {archive_data_path}")

        try:
            command: Final[list[str]] = ["cmd", "make.bat"] if os.name == "nt" else ["/bin/bash", "make.bash"]
            subprocess.check_output(command, cwd=str(archive_data_path / "src"), stderr=subprocess.STDOUT)  # noqa: S603
            archive_data_path.rename(install_path)
        except subprocess.CalledProcessError as e:
            logger.exception(f"CalledProcessError : \n\n{e.output.decode()}\n\n")

    @staticmethod
    def _go_uninstall_proc(version: str, install_path: Path) -> None:  # noqa: ARG004
        """Callback procedure to remove a GO version.

        Args:
            version: The Go version being uninstalled.
            install_path: The current install path.
        """
        logger.debug(f"Uninstalling: {install_path}")

    def get_installed_go_versions(self) -> Iterable[str]:
        """Returns the list of actually installed GO versions.

        Returns: A list of the currently installed GO versions strings.
        """
        return self._git_project_manager.list_installed()

    def get_available_go_versions(self) -> Iterable[str]:
        """Returns the list of availavle GO version to install.

        Returns: A list of available GO versions.
        """
        return self._git_project_manager.list_available(refresh=False)

    def add_go_version(self, *versions: str, force: bool = False) -> list[str]:
        """Selects an additional GO version (and installs it if missing).

        Args:
            versions: List of additional GO version to select.
            force: Whether or not to force the installation of already installed versions.

        Returns: The list of successfuly installed Go versions.
        """
        return [version for version in versions if self._git_project_manager.install(version, force=force)]

    def del_go_version(self, *versions: str) -> None:
        """Remove some GO version from the selection.

        Args:
            versions: List of the GO version to remove from the selection.
        """
        for version in versions:
            self._git_project_manager.uninstall(version)

    def _build_binary(
        self,
        source_path: Path,
        sample_name: str,
        go_version: str,
        arch: ArchTypes,
        platform: PlatformTypes,
        build_dir: Path,
    ) -> Path | None:
        """Build a sample for the selected GO version.

        Args:
            source_path: Path to the source file to build.
            sample_name: .
            go_version: .
            arch: Target build architecture.
            platform: Target operating system.
            build_dir: Path where to store the generated samples.

        Returns: Path of the generated clean sample (if any).
        """
        bin_type: Final[str] = ".exe" if platform == PlatformTypes.WINDOWS else ""

        # Set paths
        source_path = source_path.resolve()
        obj_path: Path = build_dir / f"{sample_name}{bin_type}"
        go_root: Path | None = self._git_project_manager.get_tool_path(go_version)

        if go_root:
            # TODO: Handle non-explicit building.
            env: dict[str, str] = {
                "GOROOT": str(go_root),
                "GOARCH": arch,
                "GOOS": platform,
            }

            # Build
            if self._display_progress:
                with yaspin() as spinner:
                    spinner.color = "green"
                    spinner.text = "Building with GO version {go_version} ..."
                    self._git_project_manager.run(
                        go_version, "go", "build", "-o", str(obj_path), str(source_path), env=env
                    )
            else:
                self._git_project_manager.run(go_version, "go", "build", "-o", str(obj_path), str(source_path), env=env)

            return obj_path
        return None

    def _build_process(
        self,
        build_queue: Queue,
        source_path: Path,
        out_path: Path | None,
        version: str,
        lib_list: list[str],
        arch: ArchTypes,
        platform: PlatformTypes,
        build_dir: Path,
        *,
        force: bool,
    ) -> None:
        """Build a clean sample.

        Args:
            build_queue: Outgoing queue of tupples (version, path) of the generated clean samples.
            source_path: Path to the source file to build for the selected GO version.
            out_path: Optional override of the newly built sample path.
            version: Version of GO to build the source file for.
            lib_list: The list of GO libraries included in the source file.
            arch: Target build architecture.
            platform: Target operating system.
            build_dir: Path where to store the generated samples (if any).
            force: Force re-build all samples.
        """
        sample_name: Final[str] = urlsafe_b64encode(f"{version}.{platform}.{','.join(lib_list)}".encode()).decode()
        # Test if already built
        if not force:
            for built_sample_path in build_dir.iterdir():
                if sample_name == built_sample_path.stem:
                    logger.debug(f'GO sample for "{version}" is already generated. Skipping ...')
                    build_queue.put((version, built_sample_path))
                    return
        # If not then build it
        if sample_path := self._build_binary(source_path, sample_name, version, arch, platform, build_dir):
            if out_path:
                sample_path = sample_path.rename(out_path)
            build_queue.put((version, sample_path))

    @staticmethod
    def _build_source(path: Path, libs: list[str]) -> None:
        """Generates a GO source file including the specified GO libraries.

        Args:
            path: The path of the GO source file to generate.
            libs: The list of libs to include.
        """
        if "fmt" in libs:
            libs.remove("fmt")

        with path.open("w") as source_file:
            source_file.write("package main\n")
            for lib in libs:
                source_file.write(f'import _ "{lib}"\n')
            source_file.write('import "fmt"\n')
            source_file.write("func main() {\n")
            source_file.write('fmt.Println("Built using the following libs :")\n')
            for lib in (*libs, "fmt"):
                source_file.write(f'fmt.Println(" - {lib}")\n')
            source_file.write("}\n")

    def generate(
        self,
        go_versions: list[str],
        libs: list[str],
        arch: ArchTypes | None = None,
        platform: PlatformTypes | None = None,
        *,
        out_paths: list[Path] | None = None,
        build_dir: Path | None = None,
        force: bool = False,
    ) -> list[tuple[str, Path]]:
        """Generate and build samples with the specified libraries and for the target architecture.

        Args:
            go_versions: List of go versions to generate samples for.
            libs: List of libs to include in the generated sample.
            arch: Target build architecture (Host architecture if None).
            platform: Target operating system.
            out_paths: Optional list of paths to copy each sample to.
            build_dir: Path where to store the generated samples (if any).
            force: Force re-build all samples.

        Returns:
            list[tuple[str, Path]] : List of tupples (version, path) of the generated clean samples.
        """
        source_path: Final[Path] = self._storage_build / "main.go"

        # NOTE: If the target architecture is not specified then we try to
        # detect the host architecture with a fallback to AMD64 if it can't be
        # determined.

        # Set default values
        if not arch:
            try:
                arch = ArchTypes(sysplatform.machine())
            except ValueError:
                arch = ArchTypes.AMD64
        if not platform:
            try:
                platform = PlatformTypes(sysplatform.system())
            except ValueError:
                platform = PlatformTypes.WINDOWS
        if not build_dir:
            build_dir = self._storage_build
        lib_list: Final[list[str]] = list(libs) if len(libs) else DEFAULT_LIBS

        # Ensure each go version is installed.
        go_versions = self.add_go_version(*go_versions, force=force)

        if not out_paths:
            out_paths = []

        # Generate the sample source file
        SampleGenerator._build_source(source_path, lib_list)

        # IPC Queue.
        build_queue: Queue = Queue()

        # Build for each go version
        process_pool: Final[list[Process]] = [
            Process(
                target=self._build_process,
                kwargs={
                    "build_queue": build_queue,
                    "source_path": source_path,
                    "out_path": out_path,
                    "version": version,
                    "lib_list": lib_list,
                    "arch": arch,
                    "platform": platform,
                    "build_dir": build_dir,
                    "force": force,
                },
            )
            for version, out_path in zip_longest(go_versions, out_paths)
        ]
        for process in process_pool:
            process.start()

        # Wait for the process to complete
        for process in process_pool:
            process.join()

        build_list: Final[list[tuple[str, Path]]] = []
        while not build_queue.empty():
            build_list.append(build_queue.get())

        # Strip the list of null values
        return build_list
