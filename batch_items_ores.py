"""
Batch generator: runs blender_worker.py headless for all 10 item/ore variants.
Exits with code 1 on the first failure.
"""

import subprocess
import sys
from pathlib import Path

BLENDER = r"C:\Program Files\Blender Foundation\Blender 4.5\blender.exe"
ROOT = Path(__file__).resolve().parent
WORKER = ROOT / "pipeline" / "blender_worker.py"
OUT_DIR = ROOT / "output" / "models"

JOBS = [
    # archetype              name               w      d      h     seed
    ("wood_log", "WoodLog_a", 0.9, 0.35, 0.35, 301),
    ("wood_log", "WoodLog_b", 0.9, 0.35, 0.35, 302),
    ("bow_short", "Bow_Short_a", 0.1, 0.05, 0.9, 401),
    ("bow_short", "Bow_Short_b", 0.1, 0.05, 0.9, 402),
    ("mineable_gold", "MineableGold_a", 0.8, 0.8, 0.6, 501),
    ("mineable_gold", "MineableGold_b", 0.8, 0.8, 0.6, 502),
    ("mineable_silver", "MineableSilver_a", 0.8, 0.8, 0.6, 511),
    ("mineable_silver", "MineableSilver_b", 0.8, 0.8, 0.6, 512),
    ("mineable_steel", "MineableSteel_a", 0.8, 0.8, 0.55, 521),
    ("mineable_steel", "MineableSteel_b", 0.8, 0.8, 0.55, 522),
]


def run_job(archetype, name, w, d, h, seed):
    args = [
        BLENDER,
        "-b",
        "-P",
        str(WORKER),
        "--",
        "--archetype",
        archetype,
        "--name",
        name,
        "--width",
        str(w),
        "--depth",
        str(d),
        "--height",
        str(h),
        "--seed",
        str(seed),
        "--poly_budget",
        "200",
        "--out_dir",
        str(OUT_DIR),
        "--renders_dir",
        str(ROOT / "output" / "renders"),
        "--skip_renders",
    ]
    print(f"\n{'=' * 60}")
    print(f"[Batch] Generating {name}  ({archetype}  seed={seed})")
    print(f"{'=' * 60}")
    result = subprocess.run(args, capture_output=True, text=True)
    print(result.stdout[-4000:] if len(result.stdout) > 4000 else result.stdout)
    if result.returncode != 0:
        print(result.stderr[-2000:], file=sys.stderr)
        print(f"[Batch FAILED] {name} exited {result.returncode}", file=sys.stderr)
        sys.exit(1)
    print(f"[Batch OK] {name}")


if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for job in JOBS:
        run_job(*job)
    print("\n[Batch] All 10 variants complete.")
