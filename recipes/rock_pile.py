"""Recipe: a loose heap of angular boulders (CollapsedRocks and the like).

A recipe exposes `build(ctx) -> bpy.types.Object`: one mesh object for one variant, built
entirely from `ctx.rng` so the same seed always yields the same geometry. Everything that is
true of every asset (origin, budget, collision, material, export) is the pipeline's job, not
the recipe's.
"""

import math

import bmesh
import bpy
from mathutils import Matrix, Vector


def _boulder(bm: bmesh.types.BMesh, rng, radius: float, at: Vector) -> None:
    # bmesh subdivisions=2 is the 80-face icosphere (1 is the bare icosahedron): 4-7 of these
    # land around the 400 budget before the pipeline's decimate pass trims overlap.
    scale = Matrix.Diagonal(
        (rng.uniform(0.7, 1.3), rng.uniform(0.7, 1.3), rng.uniform(0.5, 0.9))
    ).to_4x4()
    rot = (
        Matrix.Rotation(rng.uniform(0, math.tau), 4, "Z")
        @ Matrix.Rotation(rng.uniform(-0.5, 0.5), 4, "X")
        @ Matrix.Rotation(rng.uniform(-0.5, 0.5), 4, "Y")
    )
    created = bmesh.ops.create_icosphere(
        bm, subdivisions=2, radius=radius, matrix=Matrix.Translation(at) @ rot @ scale
    )
    # Push each vertex along its radial direction so no two boulders share a silhouette.
    for v in created["verts"]:
        v.co += (v.co - at).normalized() * rng.uniform(-0.12, 0.12) * radius


def build(ctx):
    rng = ctx.rng
    footprint = float(ctx.order.size.get("footprint", 1.0))
    height = float(ctx.order.size.get("height", 0.55))

    # Five 80-face boulders is the 400 budget exactly, so the pipeline never has to decimate
    # and each rock keeps its own silhouette. Ground rocks sit on a ring so they touch rather
    # than merge; the last one or two perch on top.
    bm = bmesh.new()
    count = rng.randint(4, 5)
    ground = count - rng.randint(1, 2)
    start = rng.uniform(0, math.tau)
    for i in range(count):
        if i < ground:
            radius = rng.uniform(0.22, 0.30) * footprint
            angle = start + i * math.tau / ground + rng.uniform(-0.3, 0.3)
            dist = 0.5 * footprint - radius * rng.uniform(0.95, 1.15)
            at = Vector((math.cos(angle) * dist, math.sin(angle) * dist, radius * 0.7))
        else:
            radius = rng.uniform(0.14, 0.20) * footprint
            at = Vector((rng.uniform(-0.12, 0.12), rng.uniform(-0.12, 0.12), height - radius))
        _boulder(bm, rng, radius, at)

    mesh = bpy.data.meshes.new(ctx.name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(ctx.name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj
