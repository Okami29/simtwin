"""Printer and twin state machines.

The operational state machine is intentionally small and explicit; it is the subset of
a real FDM printer's lifecycle that matters for fleet-level cyber-physical research:
connectivity, job lifecycle, failure, and maintenance.

State graph::

    OFFLINE --> IDLE                      (link established)
    IDLE --> PREHEATING                   (job assigned, heaters on)
    PREHEATING --> PRINTING               (setpoints reached)
    PREHEATING --> IDLE                   (preheat timeout / abort)
    PRINTING --> PAUSED                   (operator / fault pause)
    PAUSED --> PRINTING                   (resume)
    PRINTING --> COMPLETED                (progress >= 1)
    PRINTING --> FAILED                   (unrecoverable fault)
    COMPLETED --> IDLE                    (job released)
    FAILED --> MAINTENANCE                (repair started)
    MAINTENANCE --> IDLE                  (repair finished)
    <any> --> OFFLINE                     (link lost)
"""

from __future__ import annotations

from enum import IntEnum


class PrinterState(IntEnum):
    OFFLINE = 0
    IDLE = 1
    PREHEATING = 2
    PRINTING = 3
    PAUSED = 4
    COMPLETED = 5
    FAILED = 6
    MAINTENANCE = 7


STATE_NAMES: tuple[str, ...] = tuple(s.name for s in PrinterState)
STATE_BY_NAME: dict[str, int] = {s.name: int(s) for s in PrinterState}

#: States in which the printer consumes filament and performs motion.
ACTIVE_STATES: frozenset[int] = frozenset({int(PrinterState.PRINTING)})
#: States in which heaters are energised.
HEATING_STATES: frozenset[int] = frozenset(
    {int(PrinterState.PREHEATING), int(PrinterState.PRINTING), int(PrinterState.PAUSED)}
)

#: Legal transitions, used by the state-transition unit tests.
LEGAL_TRANSITIONS: dict[int, frozenset[int]] = {
    int(PrinterState.OFFLINE): frozenset({int(PrinterState.IDLE)}),
    int(PrinterState.IDLE): frozenset(
        {int(PrinterState.PREHEATING), int(PrinterState.OFFLINE), int(PrinterState.MAINTENANCE)}
    ),
    int(PrinterState.PREHEATING): frozenset(
        {int(PrinterState.PRINTING), int(PrinterState.IDLE), int(PrinterState.OFFLINE), int(PrinterState.FAILED)}
    ),
    int(PrinterState.PRINTING): frozenset(
        {
            int(PrinterState.PAUSED),
            int(PrinterState.COMPLETED),
            int(PrinterState.FAILED),
            int(PrinterState.OFFLINE),
        }
    ),
    int(PrinterState.PAUSED): frozenset(
        {int(PrinterState.PRINTING), int(PrinterState.FAILED), int(PrinterState.OFFLINE)}
    ),
    int(PrinterState.COMPLETED): frozenset(
        {int(PrinterState.IDLE), int(PrinterState.OFFLINE)}
    ),
    int(PrinterState.FAILED): frozenset(
        {int(PrinterState.MAINTENANCE), int(PrinterState.OFFLINE)}
    ),
    int(PrinterState.MAINTENANCE): frozenset(
        {int(PrinterState.IDLE), int(PrinterState.OFFLINE)}
    ),
}


def is_legal_transition(src: int, dst: int) -> bool:
    return dst in LEGAL_TRANSITIONS.get(int(src), frozenset())


def state_name(code: int) -> str:
    return STATE_NAMES[int(code)]
