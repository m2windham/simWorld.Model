import bmesh
import bpy

from .generator_registry import GeneratorRegistry


class ModularBaseGenerator:
    """Base class for modular generators."""

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def create_mesh(self):
        """Override to generate the mesh."""
        pass


@GeneratorRegistry.register("modular_wall")
class ModularWallGenerator(ModularBaseGenerator):
    """Procedural generator for modular walls."""

    def __init__(self, width=2.0, height=3.0, thickness=0.1, **kwargs):
        super().__init__(**kwargs)
        self.width = width
        self.height = height
        self.thickness = thickness

    def create_mesh(self):
        # Create mesh and object
        mesh = bpy.data.meshes.new(name="ModularWall")
        obj = bpy.data.objects.new("ModularWall", mesh)
        bpy.context.collection.objects.link(obj)

        bm = bmesh.new()
        # Corner-aligned pivot (Z=0, X=0 (min), Y=0)
        # Assuming facing Y

        verts = [
            (0, 0, 0),
            (self.width, 0, 0),
            (self.width, self.thickness, 0),
            (0, self.thickness, 0),
            (0, 0, self.height),
            (self.width, 0, self.height),
            (self.width, self.thickness, self.height),
            (0, self.thickness, self.height),
        ]

        bm_verts = [bm.verts.new(v) for v in verts]

        faces = [
            (0, 1, 5, 4),  # Front
            (1, 2, 6, 5),  # Right
            (2, 3, 7, 6),  # Back (cullable)
            (3, 0, 4, 7),  # Left
            (4, 5, 6, 7),  # Top
            (0, 3, 2, 1),  # Bottom (cullable)
        ]

        for face_idx, f in enumerate(faces):
            # Culling back and bottom face
            if face_idx == 2 or face_idx == 5:
                continue
            bm.faces.new([bm_verts[i] for i in f])

        bm.to_mesh(mesh)
        bm.free()

        # Add recesses/panels as needed (placeholder)
        return obj


@GeneratorRegistry.register("modular_floor")
class ModularFloorGenerator(ModularBaseGenerator):
    """Procedural generator for modular floor tiles."""

    def __init__(self, length=2.0, width=2.0, thickness=0.1, **kwargs):
        super().__init__(**kwargs)
        self.length = length
        self.width = width
        self.thickness = thickness

    def create_mesh(self):
        mesh = bpy.data.meshes.new(name="ModularFloor")
        obj = bpy.data.objects.new("ModularFloor", mesh)
        bpy.context.collection.objects.link(obj)

        bm = bmesh.new()
        verts = [
            (0, 0, -self.thickness),
            (self.width, 0, -self.thickness),
            (self.width, self.length, -self.thickness),
            (0, self.length, -self.thickness),
            (0, 0, 0),
            (self.width, 0, 0),
            (self.width, self.length, 0),
            (0, self.length, 0),
        ]

        bm_verts = [bm.verts.new(v) for v in verts]
        faces = [
            (4, 5, 6, 7),  # Top
            (0, 1, 5, 4),  # Front
            (1, 2, 6, 5),  # Right
            (2, 3, 7, 6),  # Back
            (3, 0, 4, 7),  # Left
        ]

        for f in faces:
            bm.faces.new([bm_verts[i] for i in f])

        bm.to_mesh(mesh)
        bm.free()
        return obj


@GeneratorRegistry.register("modular_column")
class ModularColumnGenerator(ModularBaseGenerator):
    """Procedural generator for modular columns/pillars."""

    def __init__(self, radius=0.2, height=3.0, **kwargs):
        super().__init__(**kwargs)
        self.radius = radius
        self.height = height

    def create_mesh(self):
        mesh = bpy.data.meshes.new(name="ModularColumn")
        obj = bpy.data.objects.new("ModularColumn", mesh)
        bpy.context.collection.objects.link(obj)

        bm = bmesh.new()
        bmesh.ops.create_cylinder(
            bm,
            cap_ends=True,
            cap_tris=False,
            segments=16,
            radius1=self.radius,
            radius2=self.radius,
            depth=self.height,
        )

        # Translate to ground-aligned pivot for column
        bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, self.height / 2))

        # Cull bottom face
        for face in list(bm.faces):
            if face.normal.z < -0.99:
                bm.faces.remove(face)

        bm.to_mesh(mesh)
        bm.free()
        return obj
