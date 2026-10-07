"""Order files: one TOML per defName family. Shared by the host CLI and the in-Blender builder."""

import string
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from .budgets import BUDGETS, Budget


@dataclass(frozen=True)
class Order:
    def_name: str
    family: str
    recipe: str
    variants: int
    seed: int
    size: dict[str, float] = field(default_factory=dict)
    style: dict[str, str] = field(default_factory=dict)
    material: dict[str, object] = field(default_factory=dict)

    @property
    def budget(self) -> Budget:
        return BUDGETS[self.family]

    def variant_name(self, index: int) -> str:
        return f"{self.def_name}_{string.ascii_lowercase[index]}"

    def variant_seed(self, index: int) -> int:
        return self.seed * 100 + index


def load_order(path: Path) -> Order:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    if data["family"] not in BUDGETS:
        raise ValueError(
            f"{path.name}: unknown family {data['family']!r}; known: {sorted(BUDGETS)}"
        )
    return Order(
        def_name=data["defName"],
        family=data["family"],
        recipe=data["recipe"],
        variants=int(data.get("variants", 4)),
        seed=int(data["seed"]),
        size=data.get("size", {}),
        style=data.get("style", {}),
        material=data.get("material", {}),
    )
