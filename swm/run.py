"""Host-side CLI.

swm build <defName> [...]     build orders/<defName>.toml into out/<defName>/
swm build --all
swm deliver <defName> [...]   copy a built family into the Host's Resources/Models and run
                              the Host's own checks
swm preview <defName>         open the built variants in interactive Blender
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from .order import load_order

ROOT = Path(__file__).resolve().parent.parent
ORDERS = ROOT / "orders"
OUT = ROOT / "out"
HOST = ROOT.parent / "simWorld.Host"
HOST_MODELS = HOST / "Assets" / "Resources" / "Models"
BLENDER = Path(os.environ.get("BLENDER_PATH", r"H:\tools\Blender\blender.exe"))


def build(def_name: str) -> bool:
    order_path = ORDERS / f"{def_name}.toml"
    order = load_order(order_path)
    out_dir = OUT / def_name
    cmd = [
        str(BLENDER),
        "-b",
        "--python",
        str(ROOT / "swm" / "blender_build.py"),
        "--",
        str(order_path),
        str(out_dir),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    if proc.returncode != 0 or "SWM_REPORT" not in proc.stdout:
        print(f"{def_name}: Blender failed\n{proc.stdout[-3000:]}\n{proc.stderr[-3000:]}")
        return False

    report = json.loads((out_dir / f"{def_name}.report.json").read_text())
    ok = True
    for v in report["variants"]:
        over = v["triangles"] > order.budget.triangles
        flag = "" if not over else ("  FAIL" if order.budget.sourced else "  note: over proposed")
        ok &= not (over and order.budget.sourced)
        dims = "x".join(f"{d:.2f}" for d in v["dimensions"])
        tris, vis, ucx = v["triangles"], v["visual_triangles"], v["collision_triangles"]
        print(f"  {v['name']:<24} {tris:>5} tris ({vis} + ucx {ucx})  {dims}{flag}")
    budget = f"budget {order.budget.triangles} ({order.family})"
    print(f"{def_name}: {len(report['variants'])} variants, {budget}")
    return ok


def deliver(def_name: str) -> bool:
    out_dir = OUT / def_name
    files = sorted(out_dir.glob(f"{def_name}_*.fbx"))
    if not files:
        print(f"{def_name}: nothing built; run `swm build {def_name}` first")
        return False
    report = json.loads((out_dir / f"{def_name}.report.json").read_text())
    if report["sourced"] and any(v["triangles"] > report["budget"] for v in report["variants"]):
        print(f"{def_name}: build is over its sourced budget; not delivering")
        return False
    HOST_MODELS.mkdir(parents=True, exist_ok=True)
    for f in files:
        shutil.copy2(f, HOST_MODELS / f.name)
        print(f"  -> {HOST_MODELS / f.name}")
    ok = True
    for tool in ("measure_triangles.py", "check_defnames.py"):
        proc = subprocess.run(
            [sys.executable, str(HOST / "tools" / tool)], cwd=HOST, capture_output=True, text=True
        )
        print(f"  {tool}: exit {proc.returncode}")
        ok &= proc.returncode == 0
    return ok


def snapshot(def_name: str, refs: list[str]) -> bool:
    """Workbench contact sheet of the built variants, with Host models as scale references."""
    ref_paths = [str(HOST_MODELS / f"{r}.fbx") for r in refs]
    cmd = [
        str(BLENDER),
        "-b",
        "--python",
        str(ROOT / "swm" / "blender_snapshot.py"),
        "--",
        str(OUT / def_name),
        def_name,
        *ref_paths,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    for line in proc.stdout.splitlines():
        if line.startswith("SWM_SNAPSHOT"):
            print(line.split(" ", 1)[1])
            return True
    print(f"{def_name}: snapshot failed\n{proc.stdout[-2000:]}\n{proc.stderr[-2000:]}")
    return False


def preview(def_name: str) -> None:
    files = sorted((OUT / def_name).glob(f"{def_name}_*.fbx"))
    script = "import bpy\n" + "".join(
        f"bpy.ops.import_scene.fbx(filepath={str(f)!r})\n"
        f"bpy.context.selected_objects[0].location.x = {i * 1.5}\n"
        for i, f in enumerate(files)
    )
    subprocess.Popen([str(BLENDER), "--python-expr", script], cwd=ROOT)


def main() -> None:
    ap = argparse.ArgumentParser(prog="swm")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("build", "deliver"):
        p = sub.add_parser(name)
        p.add_argument("defnames", nargs="*")
        p.add_argument("--all", action="store_true")
    sub.add_parser("preview").add_argument("defname")
    snap = sub.add_parser("snapshot")
    snap.add_argument("defname")
    snap.add_argument(
        "--ref", action="append", default=[], help="Host model name, e.g. Sandstone_a"
    )
    args = ap.parse_args()

    if args.cmd == "preview":
        preview(args.defname)
        return
    if args.cmd == "snapshot":
        sys.exit(0 if snapshot(args.defname, args.ref) else 1)
    names = args.defnames or ([p.stem for p in sorted(ORDERS.glob("*.toml"))] if args.all else [])
    if not names:
        ap.error("give defNames or --all")
    fn = build if args.cmd == "build" else deliver
    results = [fn(n) for n in names]
    sys.exit(0 if all(results) else 1)
