"""Regenerate every shipped asset through the palette path and deliver it to the Host.

    uv run python tools/regenerate_all.py [--only chunk_granite,...] [--no-deliver]

Uses the same job table as tools/validate_blender.py (the batch scripts' seeds and sizes), builds
into output/models with renders skipped, then copies each FBX into
../simWorld.Host/Assets/Resources/Models. swm-built families (CollapsedRocks) are rebuilt through
`swm build` + `swm deliver` afterwards.
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline.bridge import BlenderExecutionBridge  # noqa: E402
from tools.validate_blender import (  # noqa: E402
    HOST_MODELS,
    WORKER,
    jobs_from_batches,
    jobs_from_extras,
)

OUT = ROOT / "output" / "models"
SWM_FAMILIES = ["CollapsedRocks"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="comma-separated archetypes")
    ap.add_argument("--no-deliver", action="store_true")
    ap.add_argument("--extras-only", action="store_true", help="only the hand-built leftovers")
    opts = ap.parse_args()

    jobs = [j for j in jobs_from_batches() if j.reference is not None] + jobs_from_extras()
    if opts.extras_only:
        jobs = jobs_from_extras()
    if opts.only:
        wanted = set(opts.only.split(","))
        jobs = [j for j in jobs if j.archetype in wanted]

    bridge = BlenderExecutionBridge()
    print(f"Blender: {bridge.blender_binary}")
    failed = []
    for job in jobs:
        args = [
            "--archetype",
            job.archetype,
            "--name",
            job.name,
            "--width",
            str(job.width),
            "--depth",
            str(job.depth),
            "--height",
            str(job.height),
            "--seed",
            str(job.seed),
            "--thickness",
            str(job.thickness),
            "--poly_budget",
            str(job.budget),
            "--out_dir",
            str(OUT),
            "--renders_dir",
            str(ROOT / "output" / "renders"),
            "--skip_renders",
        ]
        try:
            bridge.run_headless_script(str(WORKER), args)
        except Exception as exc:
            failed.append(job.name)
            print(f"  FAILED  {job.name}: {str(exc).splitlines()[-1] if str(exc) else exc}")
            continue
        fbx = OUT / f"{job.name}.fbx"
        if not fbx.is_file():
            failed.append(job.name)
            print(f"  FAILED  {job.name}: no FBX produced")
            continue
        if not opts.no_deliver:
            shutil.copy2(fbx, HOST_MODELS / fbx.name)
        print(f"  ok      {job.name}")

    if not opts.only:
        for family in SWM_FAMILIES:
            cmd = ["uv", "run", "swm", "build", family]
            if subprocess.run(cmd, cwd=ROOT).returncode != 0:
                failed.append(family)
            elif not opts.no_deliver:
                subprocess.run(["uv", "run", "swm", "deliver", family], cwd=ROOT)

    print(f"\n{len(jobs)} assets, {len(failed)} failed: {failed}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
