"""
simWorld.Model - Master 3D Asset Creation Orchestrator
Coordinates end-to-end execution:
1. Spec Analysis
2. Headless Blender Execution (Generation, Refinery, PBR, Turntable)
3. Quantitative Pre-Flight Test Gate (Trimesh / gltf-validator)
4. Vision QA Preparation
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from pipeline.bridge import BlenderExecutionBridge
from pipeline.qa.preflight_validator import validate_asset
from pipeline.qa.vision_evaluator import VisionEvaluator


def sanitize_name(prompt: str) -> str:
    """Converts a descriptive prompt into a clean CamelCase asset identifier."""
    words = re.findall(r"[a-zA-Z0-9]+", prompt)
    if not words:
        return "Asset_01"
    return "".join(w.capitalize() for w in words[:4])


def infer_archetype(prompt: str, requested_archetype: str) -> str:
    """Infers archetype if not explicitly set."""
    if requested_archetype != "auto":
        return requested_archetype

    p_lower = prompt.lower()
    if any(
        k in p_lower
        for k in [
            "medieval",
            "house",
            "home",
            "cottage",
            "tavern",
            "dwelling",
            "building",
        ]
    ):
        return "prop_medieval_home"
    elif any(k in p_lower for k in ["wall", "panel", "bunker", "barrier", "partition"]):
        return "modular_wall"
    elif any(k in p_lower for k in ["floor", "tile", "ground", "slab", "ceiling"]):
        return "modular_floor"
    elif any(k in p_lower for k in ["cylinder", "canister", "barrel", "tank", "drum"]):
        return "prop_cylinder"
    else:
        return "prop_crate"


def main():
    parser = argparse.ArgumentParser(description="Antigravity 3D Asset Creation Orchestrator")
    parser.add_argument(
        "--prompt", type=str, required=True, help="User text description of the asset"
    )
    prehistoric_archetypes = [
        "paleo_home_a",
        "paleo_home_b",
        "meso_home_a",
        "meso_home_b",
        "neo_home_a",
        "neo_home_b",
        "chalco_home_a",
        "chalco_home_b",
    ]
    parser.add_argument(
        "--archetype",
        type=str,
        default="auto",
        choices=[
            "auto",
            "prop_crate",
            "prop_cylinder",
            "modular_wall",
            "modular_floor",
            "modular_column",
            "prop_medieval_home",
            "natural_rock",
        ]
        + prehistoric_archetypes,
        help="Asset archetype",
    )
    parser.add_argument("--name", type=str, default=None, help="Asset name identifier")
    parser.add_argument(
        "--dimensions",
        type=float,
        nargs=3,
        default=[1.0, 1.0, 1.0],
        help="Dimensions: width depth height in meters",
    )
    parser.add_argument(
        "--thickness",
        type=float,
        default=0.2,
        help="Wall thickness for modular architecture",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Deterministic shape seed for natural archetypes",
    )
    parser.add_argument("--poly_budget", type=int, default=3500, help="Target polycount budget")
    parser.add_argument(
        "--enable_draco", action="store_true", help="Enable Draco compression on glTF"
    )
    parser.add_argument("--skip_renders", action="store_true", help="Skip turntable rendering")

    args = parser.parse_args()

    asset_name = args.name or sanitize_name(args.prompt)
    archetype = infer_archetype(args.prompt, args.archetype)
    all_home_archetypes = ["prop_medieval_home"] + prehistoric_archetypes
    if archetype in all_home_archetypes and args.dimensions == [1.0, 1.0, 1.0]:
        h_map = {
            "prop_medieval_home": 6.5,
            "paleo_home_a": 4.0,
            "paleo_home_b": 4.2,
            "meso_home_a": 3.8,
            "meso_home_b": 3.6,
            "neo_home_a": 4.8,
            "neo_home_b": 4.0,
            "chalco_home_a": 5.0,
            "chalco_home_b": 4.6,
        }
        width, depth, height = [4.0, 5.0, h_map.get(archetype, 4.5)]
    else:
        width, depth, height = args.dimensions

    print("\n" + "=" * 60)
    print("      ANTIGRAVITY 3D MODELING STUDIO: ASSET PIPELINE")
    print("=" * 60)
    print(f"Prompt:        '{args.prompt}'")
    print(f"Asset Name:    {asset_name}")
    print(f"Archetype:     {archetype}")
    print(f"Dimensions:    {width:.2f}m (W) x {depth:.2f}m (D) x {height:.2f}m (H)")
    print(f"Poly Budget:   {args.poly_budget} tris")
    print("=" * 60 + "\n")

    # 1. Execute Blender Worker Subprocess
    bridge = BlenderExecutionBridge()
    worker_script = project_root / "pipeline" / "blender_worker.py"

    worker_args = [
        "--archetype",
        archetype,
        "--name",
        asset_name,
        "--width",
        str(width),
        "--depth",
        str(depth),
        "--height",
        str(height),
        "--thickness",
        str(args.thickness),
        "--seed",
        str(args.seed),
        "--poly_budget",
        str(args.poly_budget),
        "--out_dir",
        str(project_root / "output" / "models"),
        "--renders_dir",
        str(project_root / "output" / "renders"),
    ]
    if args.enable_draco:
        worker_args.append("--enable_draco")
    if args.skip_renders:
        worker_args.append("--skip_renders")

    print("[Orchestrator] Launching Headless Blender Subprocess...")
    try:
        completed = bridge.run_headless_script(str(worker_script), worker_args)
        print(completed.stdout)
    except Exception as e:
        print(
            f"[Orchestrator FATAL ERROR] Blender execution failed:\n{e}",
            file=sys.stderr,
        )
        sys.exit(1)

    # 2. Stage 3.5: Zero-Tolerance Quantitative Pre-Flight Gate
    print("\n" + "-" * 60)
    print("[Orchestrator] Running Stage 3.5 Quantitative Pre-Flight Gate...")
    print("-" * 60)

    glb_file = project_root / "output" / "models" / f"{asset_name}.glb"
    asset_profile = "modular" if "modular" in archetype else "prop"

    preflight_res = validate_asset(
        mesh_path=str(glb_file),
        asset_type=asset_profile,
        target_bounds=[width, depth, height],
        is_ground_prop=(asset_profile == "prop"),
    )

    print(f"Pre-Flight Validation Status: {'PASSED' if preflight_res['passed'] else 'FAILED'}")
    print(f"Metrics: {json.dumps(preflight_res['metrics'], indent=2)}")

    if not preflight_res["passed"]:
        print("\n[PRE-FLIGHT ERRORS DETECTED]:", file=sys.stderr)
        for err in preflight_res["errors"]:
            print(f"  -> {err}", file=sys.stderr)
        sys.exit(2)

    # 3. Stage 4: Diagnostic Render Paths for Multimodal Vision QA
    renders_dir = project_root / "output" / "renders" / asset_name
    print("\n" + "=" * 60)
    print("        STAGE 4: MULTIMODAL VISION QA READY")
    print("=" * 60)
    print(f"Model GLB:      {glb_file}")
    print(f"Model FBX:      {project_root / 'output' / 'models' / f'{asset_name}.fbx'}")
    print(f"Textures:       {project_root / 'output' / 'models' / 'textures'}")
    print("\nDiagnostic Render Passes Generated for Antigravity Vision Review:")
    passes = [
        "beauty_045.png",
        "wireframe_clay_045.png",
        "normal_orientation.png",
        "uv_checker_045.png",
        "ao_cavity_045.png",
    ]
    for p in passes:
        img_path = renders_dir / p
        print(f"  [{'READY' if img_path.is_file() else 'MISSING'}] {img_path}")

    # Initialize Vision QA Audit Report
    evaluator = VisionEvaluator(str(project_root / "output" / "renders"))
    audit = evaluator.prepare_audit(asset_name)
    report_file = renders_dir / "vision_qa_report.json"
    renders_dir.mkdir(parents=True, exist_ok=True)  # absent when --skip_renders
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(audit, f, indent=2)
    print(f"\n[Vision QA Audit Prepared] {report_file}")
    print("[Orchestrator SUCCESS] Ready for Antigravity view_file multimodal inspection.")


if __name__ == "__main__":
    main()
