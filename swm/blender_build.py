"""Runs inside Blender (background): builds every variant of one order and exports FBX.

    blender -b --python swm/blender_build.py -- <order.toml> <out dir>

Writes <out>/<Name>.fbx per variant plus <out>/<defName>.report.json for the host CLI.
"""

import importlib
import json
import random
import sys
from dataclasses import dataclass
from pathlib import Path

import bmesh
import bpy

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from swm.budgets import COLLISION_TRIANGLES  # noqa: E402
from swm.order import Order, load_order  # noqa: E402


@dataclass
class RecipeContext:
    order: Order
    variant: int
    name: str
    rng: random.Random


def triangle_count(obj: bpy.types.Object) -> int:
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


def apply_modifier(obj: bpy.types.Object, modifier: bpy.types.Modifier) -> None:
    with bpy.context.temp_override(object=obj, active_object=obj, selected_objects=[obj]):
        bpy.ops.object.modifier_apply(modifier=modifier.name)


def decimate_to(obj: bpy.types.Object, budget: int) -> None:
    # Collapse decimation overshoots the ratio on small or convex meshes, so step down until
    # the count is actually under budget.
    for _ in range(6):
        tris = triangle_count(obj)
        if tris <= budget:
            return
        mod = obj.modifiers.new("Decimate", "DECIMATE")
        mod.ratio = budget / tris * 0.9
        mod.use_collapse_triangulate = True
        apply_modifier(obj, mod)


def ground_origin(obj: bpy.types.Object) -> None:
    """Origin at the centre of the footprint, mesh resting on z = 0 (Sandstone_a convention)."""
    verts = obj.data.vertices
    xs = [v.co.x for v in verts]
    ys = [v.co.y for v in verts]
    zmin = min(v.co.z for v in verts)
    shift = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, zmin)
    for v in verts:
        v.co.x -= shift[0]
        v.co.y -= shift[1]
        v.co.z -= shift[2]


def set_shading(obj: bpy.types.Object, shading: str) -> None:
    smooth = shading == "smooth"
    for p in obj.data.polygons:
        p.use_smooth = smooth


def assign_material(obj: bpy.types.Object, order: Order, name: str) -> None:
    mat = bpy.data.materials.new(f"M_{name}_PBR")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = order.material.get("base_color", (0.6, 0.6, 0.6, 1.0))
    bsdf.inputs["Roughness"].default_value = float(order.material.get("roughness", 0.8))
    obj.data.materials.append(mat)


def collision_hull(obj: bpy.types.Object, name: str) -> bpy.types.Object:
    # Hull a coarse copy rather than decimating the hull: collapse decimation stalls on convex
    # meshes, but a convex hull over ~40 triangles' worth of vertices is reliably small.
    coarse = bpy.data.objects.new("coarse", obj.data.copy())
    bpy.context.collection.objects.link(coarse)
    decimate_to(coarse, COLLISION_TRIANGLES * 2 // 3)
    bm = bmesh.new()
    bm.from_mesh(coarse.data)
    bpy.data.objects.remove(coarse)
    hull = bmesh.ops.convex_hull(bm, input=bm.verts)
    bmesh.ops.delete(bm, geom=hull["geom_interior"] + hull["geom_unused"], context="VERTS")
    mesh = bpy.data.meshes.new(f"UCX_{name}_01")
    bm.to_mesh(mesh)
    bm.free()
    ucx = bpy.data.objects.new(f"UCX_{name}_01", mesh)
    bpy.context.collection.objects.link(ucx)
    return ucx


def export_fbx(objects: list[bpy.types.Object], path: Path) -> None:
    for o in bpy.data.objects:
        o.select_set(o in objects)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.export_scene.fbx(
        filepath=str(path),
        use_selection=True,
        object_types={"MESH"},
        apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_NONE",
        axis_forward="-Z",
        axis_up="Y",
        use_mesh_modifiers=True,
        mesh_smooth_type="OFF",
        add_leaf_bones=False,
        bake_anim=False,
        path_mode="AUTO",
        embed_textures=False,
    )


def build_variant(order: Order, recipe, index: int, out_dir: Path) -> dict:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    name = order.variant_name(index)
    ctx = RecipeContext(order, index, name, random.Random(order.variant_seed(index)))
    obj = recipe.build(ctx)
    obj.name = obj.data.name = name

    decimate_to(obj, order.budget.triangles - COLLISION_TRIANGLES)
    ground_origin(obj)
    set_shading(obj, order.style.get("shading", "flat"))
    assign_material(obj, order, name)
    ucx = collision_hull(obj, name)

    fbx = out_dir / f"{name}.fbx"
    export_fbx([obj, ucx], fbx)
    d = obj.dimensions
    return {
        "name": name,
        "file": str(fbx),
        "triangles": triangle_count(obj) + triangle_count(ucx),  # what the Host's tool counts
        "visual_triangles": triangle_count(obj),
        "collision_triangles": triangle_count(ucx),
        "dimensions": [round(d.x, 3), round(d.y, 3), round(d.z, 3)],
    }


def main() -> None:
    args = sys.argv[sys.argv.index("--") + 1 :]
    order_path, out_dir = Path(args[0]), Path(args[1])
    out_dir.mkdir(parents=True, exist_ok=True)
    order = load_order(order_path)
    recipe = importlib.import_module(f"recipes.{order.recipe}")

    report = {
        "defName": order.def_name,
        "family": order.family,
        "budget": order.budget.triangles,
        "sourced": order.budget.sourced,
        "variants": [build_variant(order, recipe, i, out_dir) for i in range(order.variants)],
    }
    (out_dir / f"{order.def_name}.report.json").write_text(json.dumps(report, indent=2))
    print(f"SWM_REPORT {out_dir / f'{order.def_name}.report.json'}")


if __name__ == "__main__":
    main()
