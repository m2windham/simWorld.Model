"""Batch generator for all 12 rock chunk FBX variants.

Dispatches one headless Blender subprocess per variant, then copies the
resulting FBX files into simWorld.Host/Assets/Resources/Models/.

Usage (from simWorld.Model root):
    python pipeline/batch_generate_chunks.py
    python pipeline/batch_generate_chunks.py --skip_renders
"""

import argparse
import shutil
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from pipeline.bridge import BlenderExecutionBridge

HOST_MODELS = project_root.parent / "simWorld.Host" / "Assets" / "Resources" / "Models"

VARIANTS = [
    # (archetype, name, width, depth, height, seed)
    ("chunk_granite", "ChunkGranite_a", 0.5, 0.5, 0.4, 201),
    ("chunk_granite", "ChunkGranite_b", 0.5, 0.5, 0.4, 202),
    ("chunk_granite", "ChunkGranite_c", 0.5, 0.5, 0.4, 203),
    ("chunk_granite", "ChunkGranite_d", 0.5, 0.5, 0.4, 204),
    ("chunk_limestone", "ChunkLimestone_a", 0.5, 0.5, 0.35, 211),
    ("chunk_limestone", "ChunkLimestone_b", 0.5, 0.5, 0.35, 212),
    ("chunk_limestone", "ChunkLimestone_c", 0.5, 0.5, 0.35, 213),
    ("chunk_limestone", "ChunkLimestone_d", 0.5, 0.5, 0.35, 214),
    ("chunk_sandstone", "ChunkSandstone_a", 0.5, 0.5, 0.3, 221),
    ("chunk_sandstone", "ChunkSandstone_b", 0.5, 0.5, 0.3, 222),
    ("chunk_sandstone", "ChunkSandstone_c", 0.5, 0.5, 0.3, 223),
    ("chunk_sandstone", "ChunkSandstone_d", 0.5, 0.5, 0.3, 224),
]


def main():
    parser = argparse.ArgumentParser(description="Batch rock chunk generator")
    parser.add_argument(
        "--skip_renders", action="store_true", help="Skip turntable rendering (faster)"
    )
    args = parser.parse_args()

    out_dir = project_root / "output" / "models"
    renders_dir = project_root / "output" / "renders"
    worker_script = project_root / "pipeline" / "blender_worker.py"

    bridge = BlenderExecutionBridge()
    results = []

    for archetype, name, width, depth, height, seed in VARIANTS:
        print(f"\n{'=' * 60}")
        print(f"  Generating: {name}  (archetype={archetype}, seed={seed})")
        print(f"{'=' * 60}")

        worker_args = [
            "--archetype",
            archetype,
            "--name",
            name,
            "--width",
            str(width),
            "--depth",
            str(depth),
            "--height",
            str(height),
            "--seed",
            str(seed),
            "--poly_budget",
            "300",
            "--out_dir",
            str(out_dir),
            "--renders_dir",
            str(renders_dir),
        ]
        if args.skip_renders:
            worker_args.append("--skip_renders")

        try:
            completed = bridge.run_headless_script(str(worker_script), worker_args)
            print(completed.stdout)
            fbx_src = out_dir / f"{name}.fbx"
            if fbx_src.is_file():
                dst = HOST_MODELS / f"{name}.fbx"
                shutil.copy2(str(fbx_src), str(dst))
                print(f"  [DELIVERED] {dst}")
                results.append((name, "OK"))
            else:
                print(f"  [WARN] FBX not found at {fbx_src}", file=sys.stderr)
                results.append((name, "MISSING_FBX"))
        except Exception as exc:
            print(f"  [FAIL] {name}: {exc}", file=sys.stderr)
            results.append((name, f"ERROR: {exc}"))

    print("\n" + "=" * 60)
    print("  BATCH COMPLETE")
    print("=" * 60)
    failed = []
    for name, status in results:
        icon = "OK" if status == "OK" else "FAIL"
        print(f"  [{icon}] {name}: {status}")
        if status != "OK":
            failed.append(name)

    if failed:
        print(f"\n{len(failed)} variant(s) failed.", file=sys.stderr)
        sys.exit(1)
    print(f"\nAll {len(results)} variants delivered to {HOST_MODELS}")


if __name__ == "__main__":
    main()
