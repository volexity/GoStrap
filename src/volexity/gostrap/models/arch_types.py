"""Enumerations of the differents architecture types available to build for."""

from enum import StrEnum, auto


class ArchTypes(StrEnum):
    """Enumerations of the differents architecture types available to build for."""

    I386 = auto()
    AMD64 = auto()
    ARM = auto()
    ARM64 = auto()
    MIPS = auto()
    MIPS64 = auto()
    MIPS64LE = auto()
    MIPSLE = auto()
    PPC64 = auto()
    PPC64LE = auto()
    RISCV64 = auto()
    S390X = auto()
