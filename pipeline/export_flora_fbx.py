"""
Headless Blender script: generate flora FBX variants without the full
production pipeline (no PBR bake, no turntable renders, no collision hull).

Usage (called by Antigravity runner):
  blender.exe -b -P pipeline/export_flora_fbx.py -- --archetype wild_plant \
      --name WildPlant_a --seed 11 --width 0.6 --depth 0.6 --height 0.5 \
      --out_dir output/models
"""

import argparse
import json
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import bpy

from pipeline.exporters.production_exporter import export_production_fbx
from pipeline.generators.generator_registry import GeneratorRegistry


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def main():
    raw_args = sys.argv
    script_args = raw_args[raw_args.index("--") + 1 :] if "--" in raw_args else []

    parser = argparse.ArgumentParser(description="Flora FBX Exporter")
    parser.add_argument("--archetype", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--width", type=float, default=0.6)
    parser.add_argument("--depth", type=float, default=0.6)
    parser.add_argument("--height", type=float, default=0.5)
    parser.add_argument("--out_dir", required=True)
    args = parser.parse_args(script_args)

    print(f"\n[FloraExporter] {args.name} archetype={args.archetype} seed={args.seed}")

    clear_scene()

    generator = GeneratorRegistry.create(
        args.archetype,
        width=args.width,
        depth=args.depth,
        height=args.height,
        seed=args.seed,
    )

    asset_obj = generator.create_mesh()
    asset_obj.name = args.name

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    fbx_path = out_dir / f"{args.name}.fbx"

    export_production_fbx(str(fbx_path), asset_obj, collision_objs=[])

    poly_count = len(asset_obj.data.polygons)
    vert_count = len(asset_obj.data.vertices)

    manifest = {
        "asset_name": args.name,
        "archetype": args.archetype,
        "seed": args.seed,
        "fbx_path": str(fbx_path),
        "dimensions": [args.width, args.depth, args.height],
        "vertex_count": vert_count,
        "polygon_count": poly_count,
        "triangle_count": poly_count,  # all faces are tris after bmesh
    }
    manifest_path = out_dir / f"{args.name}_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"[FloraExporter] Done: {fbx_path}  polys={poly_count} verts={vert_count}")


if __name__ == "__main__":
    import traceback

    try:
        main()
    except Exception as e:
        print(f"\n[FloraExporter FATAL]: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)
