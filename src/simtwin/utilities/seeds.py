"""Deterministic random-stream helpers.

Every stochastic component of SimTwin draws from a :class:`numpy.random.Generator`
that is spawned from a single root :class:`numpy.random.SeedSequence`.  Spawning
gives each component an independent, reproducible stream that does not depend on
the order in which components happen to be constructed, which is what makes
repeated runs bit-for-bit reproducible.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def root_seed_sequence(seed: int) -> np.random.SeedSequence:
    """Return the root seed sequence for a simulation run."""
    if seed < 0:
        raise ValueError("seed must be a non-negative integer")
    return np.random.SeedSequence(seed)


def spawn(seed_sequence: np.random.SeedSequence, key: tuple[int, ...]) -> np.random.Generator:
    """Spawn an independent generator for ``key`` from ``seed_sequence``."""
    return np.random.default_rng(seed_sequence.spawn(key[0])[0] if len(key) == 1
                                else np.random.SeedSequence(entropy=key[0], spawn_key=key[1:]))


def child(seed_sequence: np.random.SeedSequence, n: int) -> list[np.random.SeedSequence]:
    """Spawn ``n`` child seed sequences (one per simulated device)."""
    return list(seed_sequence.spawn(n))


@dataclass(frozen=True)
class SeedPlan:
    """Named random streams used by a simulation run."""

    seed: int
    fleet: int = 0
    jobs: int = 1
    faults: int = 2
    network: int = 3
    sensor: int = 4
    process: int = 5
    thermal: int = 6

    def root(self) -> np.random.SeedSequence:
        return root_seed_sequence(self.seed)

    def generator(self, name: str) -> np.random.Generator:
        """Return the generator for a named stream (``fleet``, ``jobs``, ...)."""
        key = getattr(self, name)
        return np.random.default_rng(self.root().spawn(key + 1)[key])
