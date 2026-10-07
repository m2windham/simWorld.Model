"""
Master Blender Headless Worker Script
Invoked by Antigravity via:
blender.exe -b -P pipeline/blender_worker.py -- [args]
Executes end-to-end procedural generation, refinery, PBR texturing, turntable rendering, and export.
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to sys.path so pipeline imports work inside Blender's embedded Python
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import bpy

from pipeline.exporters.production_exporter import (
    export_production_fbx,
    export_production_glb,
)
from pipeline.generators.generator_registry import GeneratorRegistry
from pipeline.hardware import configure_cycles_hardware_acceleration
from pipeline.qa.turntable_studio import TurntableStudio
from pipeline.refinery import palette_painter as PalettePainter
from pipeline.refinery.collision_generator import CollisionGenerator
from pipeline.refinery.normal_processor import NormalProcessor
from pipeline.refinery.pbr_baker import PBRBaker
from pipeline.refinery.uv_unwrapper import UVUnwrapper


def clear_scene():
    """Wipes default cube, camera, and lights from Blender scene."""
    bpy.ops.wm.read_factory_settings(use_empty=True)


def main():
    # Split arguments passed after '--'
    raw_args = sys.argv
    script_args = []
    if "--" in raw_args:
        script_args = raw_args[raw_args.index("--") + 1 :]

    parser = argparse.ArgumentParser(description="Autonomous Blender Asset Generator Worker")
    parser.add_argument("--archetype", type=str, default="prop_crate", help="Asset archetype")
    parser.add_argument("--name", type=str, default="Asset_01", help="Asset name")
    parser.add_argument("--width", type=float, default=1.0, help="Width (X)")
    parser.add_argument("--depth", type=float, default=1.0, help="Depth (Y)")
    parser.add_argument("--height", type=float, default=1.0, help="Height (Z)")
    parser.add_argument("--seed", type=int, default=0, help="Deterministic shape seed")
    parser.add_argument("--thickness", type=float, default=0.2, help="Wall thickness for modular")
    parser.add_argument("--poly_budget", type=int, default=3000, help="Target polycount budget")
    parser.add_argument(
        "--out_dir", type=str, default="output/models", help="Output model directory"
    )
    parser.add_argument(
        "--renders_dir",
        type=str,
        default="output/renders",
        help="Output render directory",
    )
    parser.add_argument("--skip_renders", action="store_true", help="Skip turntable rendering")
    parser.add_argument(
        "--pbr",
        action="store_true",
        help="Legacy path: procedural PBR material + baked ORM/normal textures instead of the palette",
    )
    parser.add_argument(
        "--enable_draco", action="store_true", help="Enable Draco compression on glTF"
    )

    args = parser.parse_args(script_args)

    print("\n=======================================================")
    print(f"[Blender Worker] Starting Generation for: {args.name}")
    print(f"  Archetype: {args.archetype} | Poly Budget: {args.poly_budget}")
    print(f"  Dimensions: {args.width}m x {args.depth}m x {args.height}m")
    print("=======================================================\n")

    # 1. Reset Scene & Configure Compute
    clear_scene()
    compute_mode = configure_cycles_hardware_acceleration()
    print(f"[Blender Worker] Compute Mode: {compute_mode}")

    # 2. Instantiate Generator
    generator_kwargs = {
        "width": args.width,
        "depth": args.depth,
        "height": args.height,
        "thickness": args.thickness,
        "seed": args.seed,
        # The Host's variant suffix (Human_a -> "a") for generators that key silhouettes on it;
        # generators that do not take it ignore it through **kwargs.
        "variant": args.name.rsplit("_", 1)[-1] if "_" in args.name else "a",
    }

    try:
        generator = GeneratorRegistry.create(args.archetype, **generator_kwargs)
    except ValueError as e:
        print(
            f"[Blender Worker ERROR] {e}. Available generators: {list(GeneratorRegistry._generators.keys())}"
        )
        sys.exit(1)

    # 3. Generate Base Mesh
    asset_obj = generator.create_mesh()
    asset_obj.name = args.name

    # 4. Production Refinery: Normals & Bevels
    # A displaced natural mass has no flat faces, so every edge would take a micro-bevel and the
    # mesh leaves ~8x heavier. Rock is the most-instanced thing in the game; it skips the bevel.
    no_bevel_archetypes = [
        "natural_rock",
        "chunk_granite",
        "chunk_limestone",
        "chunk_sandstone",
        "wild_plant",
        "plant_berry",
        "ore_deposit",
        "tree_poplar",
        "blueprint_outline",
        "bed_frame",
        "door_frame",
        "storage_hut",
        "cell_wall",
        "human",
    ]
    _bevel_segments = 0 if args.archetype in no_bevel_archetypes else 2
    NormalProcessor.process(
        asset_obj, bevel_width=0.005, angle_limit_deg=30, bevel_segments=_bevel_segments
    )

    # Decimate modifier to enforce poly budget
    if args.poly_budget > 0:
        tri_count = sum(len(p.vertices) - 2 for p in asset_obj.data.polygons)
        if tri_count > args.poly_budget:
            target_tris = max(20, args.poly_budget - 20)
            ratio = float(target_tris) / float(tri_count)
            dec_mod = asset_obj.modifiers.new("Decimate_Budget", "DECIMATE")
            dec_mod.ratio = ratio
            bpy.context.view_layer.objects.active = asset_obj
            bpy.ops.object.modifier_apply(modifier="Decimate_Budget")

    # 5. Production Refinery: 2-Channel UV Unwrapping
    UVUnwrapper.unwrap(asset_obj, texel_density=5.12)

    # 6. Production Refinery: Collision Hulls
    col_type = "box" if "modular" in args.archetype else "convex"
    if col_type == "box":
        col_obj = CollisionGenerator.generate_box_collision(asset_obj, suffix="01")
    else:
        col_obj = CollisionGenerator.generate_convex_hull(asset_obj, suffix="01")

    # 7. Colour. Default: palette UVs + the single M_Palette material (the game never sees baked
    # textures; see orders/MANIFEST.md "Style"). --pbr keeps the original bake for comparison.
    texture_paths = {}
    palette_faces = {}
    if args.pbr:
        if not asset_obj.data.materials:
            PBRBaker.apply_procedural_pbr_material(asset_obj, mat_name=f"M_{args.name}_PBR")
        tex_dir = Path(args.out_dir) / "textures"
        texture_paths = PBRBaker.generate_orm_and_normal_textures(str(tex_dir), args.name)
    else:
        palette_faces = PalettePainter.paint(asset_obj, args.name, args.archetype, args.seed)
        print(f"[Palette] {args.name}: {palette_faces}")

    # 8. Headless Turntable Studio: 5 Diagnostic Passes
    rendered_passes = {}
    if not args.skip_renders:
        studio = TurntableStudio(output_dir=args.renders_dir, resolution=1024)
        rendered_passes = studio.render_passes(asset_obj, args.name)

    # 9. Standards-Compliant Export (glTF & FBX)
    out_models_dir = Path(args.out_dir)
    out_models_dir.mkdir(parents=True, exist_ok=True)

    glb_path = out_models_dir / f"{args.name}.glb"
    fbx_path = out_models_dir / f"{args.name}.fbx"

    export_production_glb(
        str(glb_path),
        asset_obj,
        collision_objs=[col_obj],
        enable_draco=args.enable_draco,
    )
    export_production_fbx(str(fbx_path), asset_obj, collision_objs=[col_obj])

    # 10. Write Manifest
    manifest = {
        "asset_name": args.name,
        "archetype": args.archetype,
        "compute_mode": compute_mode,
        "glb_path": str(glb_path),
        "fbx_path": str(fbx_path),
        "textures": texture_paths,
        "palette_faces": palette_faces,
        "diagnostic_renders": rendered_passes,
        "dimensions": [args.width, args.depth, args.height],
        "vertex_count": len(asset_obj.data.vertices),
        "polygon_count": len(asset_obj.data.polygons),
    }

    manifest_path = out_models_dir / f"{args.name}_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"\n[Blender Worker SUCCESS] Asset complete! Manifest: {manifest_path}")


if __name__ == "__main__":
    import traceback

    try:
        main()
    except Exception as e:
        print(f"\n[Blender Worker FATAL EXCEPTION]: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)
