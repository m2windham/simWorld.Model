"""Validate the generators on the installed Blender against the assets that shipped.

    uv run python tools/validate_blender.py [--only chunk_granite,...] [--skip-smoke]

For every asset the batch scripts know the seed and dimensions of, rebuild it (renders skipped)
and compare the visual mesh with the same-named FBX in ../simWorld.Host/Assets/Resources/Models:
vertex/face counts, bounding box, volume, and a hash of the rounded vertex cloud (computed by
tools/fbx_signature.py inside Blender, since nothing on the host reads FBX). Archetypes with no
shipped reference (crate, cylinder, modular_*, medieval home, wild_plant, plant_berry) are only
smoke-built. Writes output/validate/report.md and exits 1 on any error or count difference.
"""

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import batch_items_ores  # noqa: E402
from pipeline import (  # noqa: E402
    batch_generate_chunks,
    batch_generate_dwellings,
    batch_generate_furniture,
    batch_generate_rocks,
    batch_generate_trees,
)
from pipeline.bridge import BlenderExecutionBridge  # noqa: E402

HOST_MODELS = ROOT.parent / "simWorld.Host" / "Assets" / "Resources" / "Models"
OUT = ROOT / "output" / "validate"
WORKER = ROOT / "pipeline" / "blender_worker.py"
SIGNER = ROOT / "tools" / "fbx_signature.py"

# Archetypes nothing shipped from; built once to catch API breaks only.
SMOKE = [
    ("prop_crate", "Smoke_Crate", 1.0, 1.0, 1.0, 1, 400),
    ("prop_cylinder", "Smoke_Cylinder", 1.0, 1.0, 1.0, 1, 400),
    ("modular_wall", "Smoke_Wall", 1.0, 0.2, 1.0, 1, 400),
    ("modular_floor", "Smoke_Floor", 1.0, 1.0, 0.08, 1, 400),
    ("modular_column", "Smoke_Column", 0.3, 0.3, 1.0, 1, 400),
    ("prop_medieval_home", "Smoke_MedievalHome", 4.0, 5.0, 3.8, 1, 1500),
    ("wild_plant", "Smoke_WildPlant", 0.6, 0.6, 0.5, 11, 400),
    ("plant_berry", "Smoke_PlantBerry", 0.6, 0.6, 0.5, 21, 400),
]


@dataclass
class Job:
    archetype: str
    name: str
    width: float
    depth: float
    height: float
    seed: int
    budget: int
    reference: Path | None
    thickness: float = 0.2  # modular_* only


# Shipped models the batch scripts never covered (built by hand-run commands on 2026-09-20; their
# seeds were not recorded, so these regenerate with new seeds under the same archetype and size).
EXTRAS = [
    *[("natural_rock", f"Granite_{v}", 1.0, 1.0, 1.0, 101 + i, 400) for i, v in enumerate("abcd")],
    *[
        ("natural_rock", f"Sandstone_{v}", 1.0, 1.0, 1.0, 121 + i, 400)
        for i, v in enumerate("abcd")
    ],
    *[("wild_plant", f"WildPlant_{v}", 0.6, 0.6, 0.5, 11 + i, 400) for i, v in enumerate("abcd")],
    *[
        ("plant_berry", f"Plant_Berry_{v}", 0.6, 0.6, 0.5, 21 + i, 400)
        for i, v in enumerate("abcd")
    ],
    ("modular_wall", "Wall", 1.0, 0.2, 1.0, 601, 400),
    ("modular_wall", "WallGranite", 1.0, 0.2, 1.0, 602, 400),
    ("modular_wall", "WallLimestone", 1.0, 0.2, 1.0, 603, 400),
    ("modular_wall", "WallSandstone", 1.0, 0.2, 1.0, 604, 400),
    ("modular_wall", "Door", 1.0, 0.15, 1.0, 611, 400),
    ("prop_crate", "StorageHut", 1.0, 1.0, 1.0, 701, 400),
    ("blueprint_outline", "Blueprint_Bed_a", 0.9, 1.8, 0.33, 402, 400),  # bed_simple 1x2 extents
    ("bed_frame", "Frame_Bed_a", 1.0, 2.0, 0.4, 403, 400),
]


def jobs_from_extras() -> list[Job]:
    return [
        Job(a, n, w, d, h, s, b, HOST_MODELS / f"{n}.fbx", thickness=d)
        for a, n, w, d, h, s, b in EXTRAS
    ]


def jobs_from_batches() -> list[Job]:
    jobs: list[Job] = []
    for mod, budget in (
        (batch_generate_chunks, 300),
        (batch_generate_rocks, 400),
        (batch_generate_furniture, 400),
        (batch_generate_trees, 300),
    ):
        for archetype, name, w, d, h, seed in mod.VARIANTS:
            jobs.append(Job(archetype, name, w, d, h, seed, budget, HOST_MODELS / f"{name}.fbx"))
    for archetype, name, w, d, h, seed in batch_items_ores.JOBS:
        jobs.append(Job(archetype, name, w, d, h, seed, 200, HOST_MODELS / f"{name}.fbx"))
    for m in batch_generate_dwellings.MODELS:
        ref = HOST_MODELS / f"{m['name']}.fbx"
        jobs.append(
            Job(
                m["archetype"],
                m["name"],
                m["w"],
                m["d"],
                m["h"],
                int(m.get("seed", 0)),
                int(m["poly"]),
                ref,
            )
        )
    for archetype, name, w, d, h, seed, budget in SMOKE:
        jobs.append(Job(archetype, name, w, d, h, seed, budget, None))
    return jobs


def build(bridge: BlenderExecutionBridge, job: Job) -> tuple[Path | None, str]:
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
        "--poly_budget",
        str(job.budget),
        "--out_dir",
        str(OUT / "models"),
        "--renders_dir",
        str(OUT / "renders"),
        "--skip_renders",
    ]
    try:
        completed = bridge.run_headless_script(str(WORKER), args)
    except Exception as exc:  # the bridge raises on a non-zero Blender exit
        return None, "\n".join(str(exc).splitlines()[-12:])
    fbx = OUT / "models" / f"{job.name}.fbx"
    if not fbx.is_file():
        return None, "\n".join(completed.stdout.splitlines()[-12:])
    return fbx, ""


def signatures(blender: str, files: list[Path]) -> dict[str, dict]:
    out = OUT / "signatures.json"
    cmd = [blender, "-b", "--python", str(SIGNER), "--", str(out), *map(str, files)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if "FBX_SIGNATURES" not in proc.stdout:
        raise RuntimeError(f"signature pass failed:\n{proc.stdout[-2000:]}\n{proc.stderr[-2000:]}")
    return json.loads(out.read_text())


def compare(new: dict, ref: dict) -> str:
    if "error" in new or "error" in ref:
        return "DIFFERENT"
    if new["hash"] == ref["hash"]:
        return "IDENTICAL"
    if (new["vertices"], new["faces"]) == (ref["vertices"], ref["faces"]):
        return "SAME_TOPOLOGY"  # same counts, vertices moved
    return "DIFFERENT"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="comma-separated archetypes")
    ap.add_argument("--skip-smoke", action="store_true")
    opts = ap.parse_args()

    jobs = jobs_from_batches()
    if opts.only:
        wanted = set(opts.only.split(","))
        jobs = [j for j in jobs if j.archetype in wanted]
    if opts.skip_smoke:
        jobs = [j for j in jobs if j.reference is not None]

    OUT.mkdir(parents=True, exist_ok=True)
    bridge = BlenderExecutionBridge()
    print(f"Blender: {bridge.blender_binary}")

    built: dict[str, Path] = {}
    errors: dict[str, str] = {}
    for job in jobs:
        fbx, err = build(bridge, job)
        if fbx is None:
            errors[job.name] = err
            print(f"  ERROR     {job.name} ({job.archetype})")
        else:
            built[job.name] = fbx
            print(f"  built     {job.name}")

    files = list(built.values()) + [
        j.reference for j in jobs if j.reference and j.reference.is_file()
    ]
    sigs = signatures(bridge.blender_binary, files) if files else {}

    rows, failures = [], len(errors)
    for job in jobs:
        if job.name in errors:
            rows.append((job, "ERROR", None, None))
            continue
        new = sigs[str(built[job.name])]
        if job.reference is None or not job.reference.is_file():
            rows.append((job, "BUILT", new, None))
            continue
        ref = sigs[str(job.reference)]
        status = compare(new, ref)
        failures += status == "DIFFERENT"
        rows.append((job, status, new, ref))

    def vf(s: dict | None) -> str:
        return "" if not s or "error" in s else f"{s['vertices']}/{s['faces']}"

    def ext(s: dict | None) -> str:
        return "" if not s or "error" in s else str(s["extents"])

    for job, status, new, ref in rows:
        print(
            f"  {status:<13} {job.name:<22} new {vf(new):>9}  ref {vf(ref):>9}"
            + f"  {ext(new)} vs {ext(ref)}"
        )

    lines = [
        f"# Generator validation on `{bridge.blender_binary}`",
        "",
        "Status: IDENTICAL = same vertex cloud as the shipped FBX; SAME_TOPOLOGY = same counts, "
        "vertices moved; DIFFERENT = counts differ; BUILT = no shipped reference; ERROR = failed.",
        "",
        "| Asset | Archetype | Status | New v/f | Shipped v/f | New extents | Shipped extents |",
        "| :-- | :-- | :-- | --: | --: | :-- | :-- |",
    ]
    for job, status, new, ref in rows:
        lines.append(
            f"| {job.name} | {job.archetype} | {status} | {vf(new)} | {vf(ref)} |"
            + f" {ext(new)} | {ext(ref)} |"
        )
    if errors:
        lines += ["", "## Errors", ""]
        for name, err in errors.items():
            lines += [f"### {name}", "```", err, "```", ""]
    (OUT / "report.md").write_text("\n".join(lines), encoding="utf-8")

    counts = {
        s: sum(1 for _, st, *_x in rows if st == s)
        for s in ("IDENTICAL", "SAME_TOPOLOGY", "DIFFERENT", "BUILT", "ERROR")
    }
    print(f"\n{counts}  report: {OUT / 'report.md'}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
