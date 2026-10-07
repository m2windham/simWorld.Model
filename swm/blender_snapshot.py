"""Runs inside Blender (background): renders a contact sheet of built variants with Workbench.

    blender -b --python swm/blender_snapshot.py -- <out dir> <defName> [<reference.fbx> ...]

Variants line up along X with 1.5 units between them; reference models (e.g. the Host's
Sandstone_a) go on the same row so scale can be judged by eye.
"""

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def main() -> None:
    args = sys.argv[sys.argv.index("--") + 1 :]
    out_dir, def_name, refs = Path(args[0]), args[1], [Path(p) for p in args[2:]]
    files = sorted(out_dir.glob(f"{def_name}_*.fbx")) + refs

    bpy.ops.wm.read_factory_settings(use_empty=True)
    for i, f in enumerate(files):
        bpy.ops.import_scene.fbx(filepath=str(f))
        for o in bpy.context.selected_objects:
            if o.name.startswith("UCX_"):
                bpy.data.objects.remove(o)
            else:
                o.location.x = i * 1.5

    # Orthographic three-quarter view: no perspective, so sizes compare directly across the row.
    span = (len(files) - 1) * 1.5
    centre = Vector((span / 2, 0, 0.35))
    cam_data = bpy.data.cameras.new("cam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = span + 2.2
    cam = bpy.data.objects.new("cam", cam_data)
    bpy.context.collection.objects.link(cam)
    yaw = math.radians(30)  # three-quarter view reads depth; a straight elevation hides gables
    offset = Vector((10 * math.sin(yaw), -10 * math.cos(yaw), 7))
    cam.location = centre + offset
    cam.rotation_euler = (math.radians(55), 0, yaw)
    bpy.context.scene.camera = cam

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "TEXTURE"  # palette atlas, not the flat material colour
    scene.render.resolution_x = int(220 * (span + 2.2))
    scene.render.resolution_y = 480
    scene.render.filepath = str(out_dir / f"{def_name}.snapshot.png")
    bpy.ops.render.render(write_still=True)
    print(f"SWM_SNAPSHOT {scene.render.filepath}")


if __name__ == "__main__":
    main()
