"""Enumeration of the differents operating systems available to build for."""

from enum import StrEnum, auto


class PlatformTypes(StrEnum):
    """Enumeration of the differents operating systems available to build for."""

    ANDROID = auto()
    DARWIN = auto()
    DRAGONFLY = auto()
    FREEBSD = auto()
    ILLUMOS = auto()
    IOS = auto()
    JS = auto()
    LINUX = auto()
    NETBSD = auto()
    OPENBSD = auto()
    PLAN9 = auto()
    SOLARIS = auto()
    WASIP1 = auto()
    WINDOWS = auto()
