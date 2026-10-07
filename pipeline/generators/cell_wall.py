"""A wall segment that fills its 1x1 cell: centred, base on the ground, 1 unit per cell.

The modular_wall generator authors from the cell corner and 0.2 deep, which the host (which
places models unstretched at the footprint centre) draws half a cell west against the cell's edge.
This one is a full-cell block in the settlement register: a slightly inset body, a dark mortar
course a third of the way up, and a proud cap slab, so it reads as built stone next to a rock.
The stone colour comes from the asset name (WallGranite -> granite) via the palette painter.
"""

import bmesh
import bpy
from mathutils import Vector

from .construction_stages import _box
from .generator_registry import GeneratorRegistry

SLOTS = ("M_Stone", "M_Timber")  # body / dark course (the painter overrides stone by name)
STONE, DARK = range(2)


def _slot_box(bm, centre, size, slot) -> None:
    before = set(bm.faces)
    _box(bm, centre, size)
    for f in set(bm.faces) - before:
        f.material_index = slot


@GeneratorRegistry.register("cell_wall")
class CellWallGenerator:
    def __init__(self, width=1.0, depth=1.0, height=1.0, seed=0, **kwargs):
        self.width, self.depth, self.height = float(width), float(depth), float(height)

    def create_mesh(self) -> bpy.types.Object:
        w, d, h = self.width, self.depth, self.height
        inset, cap_h, course_h = 0.04, 0.08, 0.03
        body_h = h - cap_h
        bm = bmesh.new()
        _slot_box(bm, Vector((0, 0, body_h / 2)), Vector((w - inset, d - inset, body_h)), STONE)
        # Dark mortar course, recessed a hair so the body's facets catch light above and below it.
        _slot_box(
            bm,
            Vector((0, 0, body_h * 0.36)),
            Vector((w - inset + 0.002, d - inset + 0.002, course_h)),
            DARK,
        )
        _slot_box(bm, Vector((0, 0, h - cap_h / 2)), Vector((w, d, cap_h)), STONE)  # proud cap
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        mesh = bpy.data.meshes.new("Wall")
        bm.to_mesh(mesh)
        bm.free()
        obj = bpy.data.objects.new("Wall", mesh)
        bpy.context.collection.objects.link(obj)
        for slot in SLOTS:
            obj.data.materials.append(bpy.data.materials.get(slot) or bpy.data.materials.new(slot))
        return obj
