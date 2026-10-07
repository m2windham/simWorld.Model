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
    ("tree_poplar", "Plant_TreePoplar_a", 0.8, 0.8, 3.0, 501),
    ("tree_poplar", "Plant_TreePoplar_b", 0.8, 0.8, 3.0, 502),
    ("tree_poplar", "Plant_TreePoplar_c", 0.8, 0.8, 3.0, 503),
    ("tree_poplar", "Plant_TreePoplar_d", 0.8, 0.8, 3.0, 504),
]


def main():
    parser = argparse.ArgumentParser(description="Batch tree generator")
    parser.add_argument("--skip_renders", action="store_true")
    args = parser.parse_args()

    out_dir = project_root / "output" / "models"
    renders_dir = project_root / "output" / "renders"
    worker_script = project_root / "pipeline" / "blender_worker.py"

    bridge = BlenderExecutionBridge()
    results = []

    for archetype, name, width, depth, height, seed in VARIANTS:
        print(f"\n{'=' * 60}")
        print(f"  Generating: {name}")
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
                results.append((name, "OK"))
            else:
                results.append((name, "MISSING_FBX"))
        except Exception as exc:
            results.append((name, f"ERROR: {exc}"))

    failed = [n for n, s in results if s != "OK"]
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
