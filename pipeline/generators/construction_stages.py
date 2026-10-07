"""Construction stages: what the player sees before a thing is built.

`blueprint_outline` is a ghost: thin bars along the twelve edges of the footprint box, in the
`blueprint` swatch. It is generic over width/depth/height, so Blueprint_<anything> can use it.
`bed_frame` is the bare timber frame of the 1x1 bed: four posts, four rails, three slats, no
mattress. Both stay far under the 400 item budget.
"""

import bmesh
import bpy
from mathutils import Vector

from .generator_registry import GeneratorRegistry


def _box(bm: bmesh.types.BMesh, centre: Vector, size: Vector) -> None:
    ret = bmesh.ops.create_cube(bm, size=1.0)
    for v in ret["verts"]:
        v.co = Vector((v.co.x * size.x, v.co.y * size.y, v.co.z * size.z)) + centre


def _object(name: str, bm: bmesh.types.BMesh, slot: str) -> bpy.types.Object:
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    # The slot name is what the palette painter reads; the material itself is replaced.
    mat = bpy.data.materials.get(slot) or bpy.data.materials.new(slot)
    obj.data.materials.append(mat)
    return obj


@GeneratorRegistry.register("blueprint_outline")
class BlueprintOutlineGenerator:
    """Ghost outline of a width x depth x height box, resting on z = 0."""

    def __init__(self, width=1.0, depth=1.0, height=0.4, seed=0, **kwargs):
        self.width, self.depth, self.height = float(width), float(depth), float(height)
        self.bar = 0.03

    def create_mesh(self) -> bpy.types.Object:
        w, d, h, b = self.width, self.depth, self.height, self.bar
        bm = bmesh.new()
        xs, ys = (-w / 2, w / 2), (-d / 2, d / 2)
        for x in xs:
            for y in ys:  # uprights
                _box(bm, Vector((x, y, h / 2)), Vector((b, b, h)))
        for z in (b / 2, h - b / 2):  # bottom and top rectangles
            for y in ys:
                _box(bm, Vector((0, y, z)), Vector((w, b, b)))
            for x in xs:
                _box(bm, Vector((x, 0, z)), Vector((b, d, b)))
        return _object("Blueprint", bm, "M_Blueprint")


@GeneratorRegistry.register("bed_frame")
class BedFrameGenerator:
    """The bed's timber frame before the mattress arrives. Matches bed_simple's footprint."""

    def __init__(self, width=1.0, depth=1.0, height=0.4, seed=0, **kwargs):
        self.width, self.depth = float(width) * 0.9, float(depth) * 0.9
        self.post = 0.06
        self.rail_z = 0.12  # rails sit at the height of bed_simple's frame top

    def create_mesh(self) -> bpy.types.Object:
        w, d, p, z = self.width, self.depth, self.post, self.rail_z
        bm = bmesh.new()
        xs, ys = (-w / 2 + p / 2, w / 2 - p / 2), (-d / 2 + p / 2, d / 2 - p / 2)
        for x in xs:
            for y in ys:  # posts, head posts a little taller
                top = z + (0.12 if y > 0 else 0.04)
                _box(bm, Vector((x, y, top / 2)), Vector((p, p, top)))
        for y in ys:  # long rails
            _box(bm, Vector((0, y, z)), Vector((w - 2 * p, p, p)))
        for x in xs:  # short rails
            _box(bm, Vector((x, 0, z)), Vector((p, d - 2 * p, p)))
        for i in range(3):  # slats
            y = -d / 2 + d * (i + 1) / 4
            _box(bm, Vector((0, y, z)), Vector((w - 2 * p, p * 0.8, p * 0.5)))
        return _object("Frame", bm, "M_WoodPlank")
