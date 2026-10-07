"""Settlement-register props: the doorway and the storage hut.

Both are 1x1 core buildings. Authored centred on the footprint, front toward Blender +Y (the
Host's "front toward Unity -Z" once exported), hard edges, dark timber trim: the abrupt register
of orders/MANIFEST.md. Slot names are what the palette painter reads (M_WoodPlank -> plank,
M_Timber -> timber_dark, M_StrawThatch -> thatch, M_Iron -> iron).
"""

import bmesh
import bpy
from mathutils import Vector

from .construction_stages import _box
from .generator_registry import GeneratorRegistry

SLOTS = ("M_WoodPlank", "M_Timber", "M_StrawThatch", "M_Iron")
PLANK, TIMBER, THATCH, IRON = range(4)


def _slot_box(bm, centre, size, slot) -> None:
    before = set(bm.faces)
    _box(bm, centre, size)
    for f in set(bm.faces) - before:
        f.material_index = slot


def _finish(name: str, bm: bmesh.types.BMesh) -> bpy.types.Object:
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    for slot in SLOTS:
        obj.data.materials.append(bpy.data.materials.get(slot) or bpy.data.materials.new(slot))
    return obj


@GeneratorRegistry.register("door_frame")
class DoorFrameGenerator:
    """A doorway through a 1-cell wall: dark jambs and lintel, a recessed plank leaf, iron handle."""

    def __init__(self, width=1.0, depth=0.2, height=1.0, seed=0, **kwargs):
        self.width, self.depth, self.height = float(width), float(depth), float(height)

    def create_mesh(self) -> bpy.types.Object:
        w, d, h = self.width, self.depth, self.height
        jamb = 0.1
        bm = bmesh.new()
        for x in (-w / 2 + jamb / 2, w / 2 - jamb / 2):  # jambs
            _slot_box(bm, Vector((x, 0, h / 2)), Vector((jamb, d, h)), TIMBER)
        _slot_box(bm, Vector((0, 0, h - jamb / 2)), Vector((w, d, jamb)), TIMBER)  # lintel
        leaf_w, leaf_h = w - 2 * jamb, h - jamb
        _slot_box(bm, Vector((0, 0, leaf_h / 2)), Vector((leaf_w, d * 0.5, leaf_h)), PLANK)  # leaf
        for z in (leaf_h * 0.25, leaf_h * 0.75):  # two dark battens across the leaf
            _slot_box(bm, Vector((0, d * 0.28, z)), Vector((leaf_w, d * 0.08, 0.05)), TIMBER)
        _slot_box(
            bm, Vector((leaf_w * 0.3, d * 0.3, leaf_h * 0.45)), Vector((0.04, 0.03, 0.08)), IRON
        )
        return _finish("Door", bm)


@GeneratorRegistry.register("storage_hut")
class StorageHutGenerator:
    """A 1x1 roofed hut: plank walls on dark corner posts, pitched thatch with a ridge beam, a door."""

    def __init__(self, width=1.0, depth=1.0, height=1.0, seed=0, **kwargs):
        self.width, self.depth, self.height = float(width), float(depth), float(height)

    def create_mesh(self) -> bpy.types.Object:
        w, d, h = self.width * 0.9, self.depth * 0.9, self.height
        post, wall_h = 0.07, h * 0.62
        bm = bmesh.new()
        _slot_box(bm, Vector((0, 0, wall_h / 2)), Vector((w - post, d - post, wall_h)), PLANK)
        for x in (-w / 2 + post / 2, w / 2 - post / 2):
            for y in (-d / 2 + post / 2, d / 2 - post / 2):
                _slot_box(bm, Vector((x, y, wall_h / 2)), Vector((post, post, wall_h)), TIMBER)
        # Door on the front face (+Y), a dark recess with a plank leaf.
        _slot_box(
            bm, Vector((0, d / 2 - 0.01, wall_h * 0.4)), Vector((0.3, 0.04, wall_h * 0.8)), TIMBER
        )
        _slot_box(
            bm, Vector((0, d / 2 + 0.005, wall_h * 0.4)), Vector((0.24, 0.02, wall_h * 0.72)), PLANK
        )
        # Pitched roof: two thatch slabs meeting at a dark ridge, overhanging the walls.
        ow, od = self.width * 1.08, self.depth * 1.08
        slab_t, ridge_h = 0.08, h
        rise = ridge_h - wall_h
        for side in (-1, 1):
            geom = bmesh.ops.create_cube(bm, size=1.0)
            for v in geom["verts"]:
                # a slab lying across half the width, then tilted up to the ridge
                v.co = Vector((v.co.x * (ow / 2 + 0.05), v.co.y * od, v.co.z * slab_t))
                v.co.x += side * ow / 4
                v.co.z += wall_h + slab_t / 2 + rise * (1 - (v.co.x * side) / (ow / 2))
            for f in [
                f for f in bm.faces if f.material_index == 0 and f not in geom.get("faces", [])
            ]:
                pass
            new_faces = [f for f in bm.faces if all(v in geom["verts"] for v in f.verts)]
            for f in new_faces:
                f.material_index = THATCH
        _slot_box(
            bm, Vector((0, 0, ridge_h + 0.02)), Vector((0.08, od, 0.08)), TIMBER
        )  # ridge beam
        return _finish("StorageHut", bm)
