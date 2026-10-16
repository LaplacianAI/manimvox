"""Checks that decide whether a video is done."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Finding:
    check: str
    subject: str
    message: str

    def __str__(self) -> str:
        return f"{self.check}: {self.subject}: {self.message}"
