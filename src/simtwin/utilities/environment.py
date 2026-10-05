"""Automatic detection of the computational environment.

The study reports the hardware and software environment of every experiment.  All
fields are detected programmatically (``platform``, ``sysconf``, ``psutil``,
``importlib.metadata``); nothing is hard-coded.  If a value cannot be detected it is
set to ``"unknown"`` and flagged in ``missing``.
"""

from __future__ import annotations

import os
import platform
import sys
from importlib import metadata as importlib_metadata
from typing import Any

import numpy as np

#: Distribution names (PyPI) of the packages whose versions are recorded.
DEPENDENCY_PACKAGES: tuple[str, ...] = (
    "numpy",
    "pandas",
    "scipy",
    "matplotlib",
    "scikit-learn",
    "pyarrow",
    "psutil",
    "PyYAML",
    "paho-mqtt",
    "pytest",
)


def _cpu_count() -> int:
    try:
        return os.cpu_count() or 1
    except Exception:  # pragma: no cover - defensive
        return 1


def _memory_bytes() -> int:
    try:
        pages = os.sysconf("SC_PHYS_PAGES")
        page_size = os.sysconf("SC_PAGE_SIZE")
        if pages > 0 and page_size > 0:
            return int(pages) * int(page_size)
    except (ValueError, KeyError, OSError):
        pass
    try:  # pragma: no cover - non-POSIX fallback
        import psutil

        return int(psutil.virtual_memory().total)
    except Exception:
        return -1


def detect_environment(broker_version: str | None = None) -> dict[str, Any]:
    """Return a JSON-serialisable description of the local compute environment."""
    missing: list[str] = []

    machine = platform.machine()
    processor = platform.processor() or machine
    if not processor:
        processor = "unknown"
        missing.append("processor")

    mem = _memory_bytes()
    if mem <= 0:
        mem = -1
        missing.append("total_memory_bytes")

    deps: dict[str, str] = {}
    for name in DEPENDENCY_PACKAGES:
        try:
            deps[name] = importlib_metadata.version(name)
        except importlib_metadata.PackageNotFoundError:
            deps[name] = "not installed"

    env: dict[str, Any] = {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": machine,
        "processor": processor,
        "cpu_count_logical": _cpu_count(),
        "total_memory_bytes": mem,
        "total_memory_gib": round(mem / (1024**3), 2) if mem > 0 else None,
        "python_version": sys.version.split()[0],
        "python_implementation": platform.python_implementation(),
        "numpy_version": np.__version__,
        "dependencies": deps,
        "mqtt_broker_version": broker_version or "not used (in-process bus)",
        "hostname": platform.node(),
    }
    env["missing"] = missing
    return env


def environment_as_text(env: dict[str, Any]) -> str:
    """Human-readable one-paragraph rendering used in run logs."""
    return (
        f"{env['system']} {env['release']} ({env['machine']}, {env['processor']}), "
        f"{env['cpu_count_logical']} CPUs, "
        f"{env['total_memory_gib']} GiB RAM, Python {env['python_version']}, "
        f"NumPy {env['numpy_version']}, broker={env['mqtt_broker_version']}"
    )
