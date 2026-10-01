"""Shared types for the worked examples: an Enum and a dataclass."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SpinType(Enum):
    NONE = "none"
    COLLINEAR = "collinear"
    NON_COLLINEAR = "non_collinear"


@dataclass
class Settings:
    nspin: int = 1
