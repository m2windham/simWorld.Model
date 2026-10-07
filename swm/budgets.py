"""Triangle budgets per family, mirroring simWorld.Host/docs/triangle-budget.md.

`sourced` budgets fail a build; `proposed` ones only warn. Keep these in step with the Host's
`tools/measure_triangles.py`, which is the instrument of record. That tool sums every mesh in
the file, so a budget covers the visual mesh *and* its UCX collision hull together
(Sandstone_a = 192 + 66 = 258).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Budget:
    triangles: int
    sourced: bool


BUDGETS: dict[str, Budget] = {
    "scatter": Budget(400, sourced=True),
    "item": Budget(400, sourced=False),
    "ore": Budget(1200, sourced=False),
    "dwelling": Budget(2500, sourced=False),
}

COLLISION_TRIANGLES = 64  # UCX_* convex hulls shipped at 28-70 triangles
