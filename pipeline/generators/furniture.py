import bmesh
import bpy

from .generator_registry import GeneratorRegistry


@GeneratorRegistry.register("bed_simple")
class BedSimpleGenerator:
    """A very simple 1x1 bed for the settlers.

    Budget: 400 tris.
    Since footprints are 1x1, it needs to fit within 1.0x1.0x1.0.
    A wooden frame with a small mattress/roll on top.
    """

    def __init__(self, width=1.0, depth=1.0, height=0.4, seed=0, **kwargs):
        self.width = float(width)
        self.depth = float(depth)
        self.height = float(height)

    def create_mesh(self):
        mesh = bpy.data.meshes.new(name="Bed")
        obj = bpy.data.objects.new("Bed", mesh)
        bpy.context.collection.objects.link(obj)

        bm = bmesh.new()

        # Wooden Frame base
        frame_h = 0.15
        bmesh.ops.create_cube(bm, size=1.0)
        # Scale down
        for v in bm.verts:
            v.co.x *= self.width * 0.95
            v.co.y *= self.depth * 0.95
            v.co.z = v.co.z * frame_h + frame_h / 2.0

        bm.free()

        bm2 = bmesh.new()
        # Frame
        ret = bmesh.ops.create_cube(bm2, size=1.0)
        for v in ret["verts"]:
            v.co.x *= self.width * 0.9
            v.co.y *= self.depth * 0.9
            v.co.z = v.co.z * 0.15 + 0.075

        # Mattress
        ret = bmesh.ops.create_cube(bm2, size=1.0)
        for v in ret["verts"]:
            v.co.x *= self.width * 0.85
            v.co.y *= self.depth * 0.85
            v.co.z = v.co.z * 0.1 + 0.2

        # Pillow
        ret = bmesh.ops.create_cube(bm2, size=1.0)
        for v in ret["verts"]:
            v.co.x *= self.width * 0.7
            v.co.y *= self.depth * 0.25
            v.co.z = v.co.z * 0.08 + 0.29
            v.co.y += self.depth * 0.25

        bmesh.ops.recalc_face_normals(bm2, faces=bm2.faces[:])
        bm2.to_mesh(mesh)
        bm2.free()

        return obj
