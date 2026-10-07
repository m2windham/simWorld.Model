import bmesh
import bpy

from .generator_registry import GeneratorRegistry


class PropBaseGenerator:
    """Base class for prop generators."""

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def create_mesh(self):
        pass


@GeneratorRegistry.register("prop_crate")
class PropCrateGenerator(PropBaseGenerator):
    """Procedural generator for supply crates."""

    def __init__(self, width=1.0, depth=1.0, height=1.0, **kwargs):
        super().__init__(**kwargs)
        self.width = width
        self.depth = depth
        self.height = height

    def create_mesh(self):
        mesh = bpy.data.meshes.new(name="PropCrate")
        obj = bpy.data.objects.new("PropCrate", mesh)
        bpy.context.collection.objects.link(obj)

        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)

        # Scale to dimensions
        bmesh.ops.scale(bm, verts=bm.verts, vec=(self.width, self.depth, self.height))
        # Ground-aligned pivot
        bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, self.height / 2))

        # Watertight closed manifold hull
        bm.to_mesh(mesh)
        bm.free()

        return obj


@GeneratorRegistry.register("prop_cylinder")
class PropCylinderGenerator(PropBaseGenerator):
    """Procedural generator for cylindrical storage containers."""

    def __init__(self, radius=0.5, height=1.2, **kwargs):
        super().__init__(**kwargs)
        self.radius = radius
        self.height = height

    def create_mesh(self):
        mesh = bpy.data.meshes.new(name="PropCylinder")
        obj = bpy.data.objects.new("PropCylinder", mesh)
        bpy.context.collection.objects.link(obj)

        bm = bmesh.new()
        bmesh.ops.create_cone(  # bmesh has no create_cylinder; a cone with equal radii is one
            bm,
            cap_ends=True,
            cap_tris=False,
            segments=32,
            radius1=self.radius,
            radius2=self.radius,
            depth=self.height,
        )

        # Ground-aligned pivot
        bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, self.height / 2))

        # Watertight closed manifold hull
        bm.to_mesh(mesh)
        bm.free()

        return obj
