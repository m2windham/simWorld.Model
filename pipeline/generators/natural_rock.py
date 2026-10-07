"""Natural rock masses for grid-based games.

Every other generator here is hard-surface architecture: a wall, a floor, a crate. Rock is the
opposite problem. In SimWorld a single generated settlement interior held 12,991 rock instances,
so this generator is the one whose polygon budget actually decides the frame time, and its output
is most of what is on screen.

Two things shape the design:

* **It must fill its cell.** A mined cave face is a grid of adjacent rock cells. An icosphere
  scaled to the cell leaves the corners empty and the wall reads as a row of beads, so this
  starts from a cube and displaces it rather than starting from a sphere.
* **The silhouette must vary.** At thirteen thousand instances one mesh reads as an obvious
  repeating grid, so the same type is generated 3-4 times under different seeds. Rotation is free
  at runtime and does not help; the outline has to differ.

**Displacement is measured in grid spacings, not in metres.** The first version jittered each
vertex by an absolute 0.16 of a cell while the subdivision grid at two cuts is only 0.33 apart,
so neighbouring vertices crossed and merged: an eighteen-vertex mesh that had collapsed most of
the way back to the cube it started as. Amplitude is now a fraction of the distance between
adjacent vertices, which cannot collapse the grid however the seed falls.

The mesh is fitted to the requested bounds *after* displacement, so the pre-flight dimension gate
passes exactly regardless of how far the jitter happened to push a vertex. The base is then
flattened and dropped to z=0, which both seats it on the floor and gives the flat underside a
mined face wants.
"""

import random

import bmesh
import bpy

from .generator_registry import GeneratorRegistry


@GeneratorRegistry.register("natural_rock")
class NaturalRockGenerator:
    """Procedural generator for irregular, cell-filling natural rock."""

    def __init__(self, width=1.0, depth=1.0, height=1.0, seed=0, roughness=0.42, cuts=3, **kwargs):
        self.width = width
        self.depth = depth
        self.height = height
        # Same seed, same rock, for ever: a variant that changed between runs would mean the
        # host's Granite_a stopped matching the Granite_a it shipped with.
        self.seed = int(seed)
        # Fraction of the GRID SPACING a vertex may wander, not a fraction of the cell. Above
        # ~0.5 adjacent vertices can cross and the merge pass welds them away.
        self.roughness = float(roughness)
        # 3 cuts -> 6 faces x 16 quads -> 96 quads -> 192 triangles, inside the 300 rock needs.
        self.cuts = int(cuts)

    def create_mesh(self):
        mesh = bpy.data.meshes.new(name="NaturalRock")
        obj = bpy.data.objects.new("NaturalRock", mesh)
        bpy.context.collection.objects.link(obj)

        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=self.cuts, use_grid_fill=True)

        # Unit cube of side 1 cut `cuts` times leaves vertices this far apart.
        spacing = 1.0 / (self.cuts + 1)
        amp = self.roughness * spacing

        # bmesh vertex order is deterministic for a fixed construction, so walking it with one
        # seeded stream reproduces the same rock every time without hashing coordinates.
        rng = random.Random(self.seed)
        for v in bm.verts:
            v.co.x += rng.uniform(-amp, amp)
            v.co.y += rng.uniform(-amp, amp)
            v.co.z += rng.uniform(-amp, amp)

        # Flatten the underside before fitting: any vertex that began on the bottom face is
        # pulled back to the floor. Moving vertices never changes topology, so the mesh stays the
        # closed manifold the pre-flight gate requires.
        floor = min(v.co.z for v in bm.verts)
        for v in bm.verts:
            if v.co.z < floor + amp * 2.0:
                v.co.z = floor

        self._fit_to_bounds(bm)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])

        bm.to_mesh(mesh)
        bm.free()
        return obj

    def _fit_to_bounds(self, bm):
        """Scale the displaced mass to exactly the requested dimensions, then seat it at z=0.

        Fitting after displacement rather than clamping during it is what makes the dimension
        gate deterministic: whatever the jitter did, the result measures width x depth x height.
        """
        xs = [v.co.x for v in bm.verts]
        ys = [v.co.y for v in bm.verts]
        zs = [v.co.z for v in bm.verts]
        spans = (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
        mins = (min(xs), min(ys), min(zs))
        targets = (self.width, self.depth, self.height)

        # A span can only collapse if roughness is zero and a cut landed flat; guard anyway
        # rather than divide by zero deep inside a headless Blender run.
        scale = [t / s if s > 1e-6 else 1.0 for t, s in zip(targets, spans)]

        for v in bm.verts:
            v.co.x = (v.co.x - mins[0]) * scale[0] - self.width / 2.0
            v.co.y = (v.co.y - mins[1]) * scale[1] - self.depth / 2.0
            # Ground-aligned pivot, the convention every prop generator here uses.
            v.co.z = (v.co.z - mins[2]) * scale[2]
