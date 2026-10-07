"""Items and ore-vein generators for simWorld.

Five archetypes, all low-instance-count (1-2 per map) but important for world
fidelity. Low poly budgets: 60-128 tris. All follow the same ground-aligned
pivot convention as natural_rock (Z=0 at base, centred X/Y).

WoodLog
-------
Cylinder lying flat on the ground. 8-sided cross-section built manually in
bmesh (two cap rings + two cap centre verts + barrel quads). A slight taper
and per-vertex radial noise give the organic feel of a real log.

Bow_Short
---------
A D-shaped arc traced as a 10-point edge loop in the XZ plane, extruded along
Y to give a flat cross-section. A thin 4-sided string cylinder is built
manually in bmesh. Total ~60 tris.

MineableGold / MineableSilver / MineableSteel
---------------------------------------------
Start from the same displaced-cube rock base as natural_rock (roughness 0.35,
cuts=2). Then 2-4 randomly chosen faces are extruded outward to form crystal
veins / ore seams.
"""

import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

from .generator_registry import GeneratorRegistry

# ---------------------------------------------------------------------------
# Shared utility
# ---------------------------------------------------------------------------


def _fit_to_bounds(bm, width, depth, height):
    """Scale displaced mass to exactly (width, depth, height) and seat at z=0."""
    xs = [v.co.x for v in bm.verts]
    ys = [v.co.y for v in bm.verts]
    zs = [v.co.z for v in bm.verts]
    spans = (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
    mins = (min(xs), min(ys), min(zs))
    targets = (width, depth, height)
    scale = [t / s if s > 1e-6 else 1.0 for t, s in zip(targets, spans)]
    for v in bm.verts:
        v.co.x = (v.co.x - mins[0]) * scale[0] - width / 2.0
        v.co.y = (v.co.y - mins[1]) * scale[1] - depth / 2.0
        v.co.z = (v.co.z - mins[2]) * scale[2]


def _make_object(name):
    """Create a new mesh + object linked into the active collection."""
    mesh = bpy.data.meshes.new(name=name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj, mesh


def _build_cylinder_bmesh(bm, radius_bot, radius_top, depth, segments):
    """Add a capped cylinder to an existing bmesh.

    The cylinder axis is Z, centred at origin, from z=-depth/2 to z=+depth/2.
    Uses explicit vert/face creation — no bmesh.ops.create_cylinder (not in
    Blender 4.5 API).

    Returns (bot_ring, top_ring, bot_cap, top_cap) vert lists.
    """
    half = depth / 2.0
    angle_step = 2.0 * math.pi / segments

    bot_ring = []
    top_ring = []
    for i in range(segments):
        a = i * angle_step
        cos_a = math.cos(a)
        sin_a = math.sin(a)
        bot_ring.append(bm.verts.new(Vector((radius_bot * cos_a, radius_bot * sin_a, -half))))
        top_ring.append(bm.verts.new(Vector((radius_top * cos_a, radius_top * sin_a, half))))

    bot_cap = bm.verts.new(Vector((0.0, 0.0, -half)))
    top_cap = bm.verts.new(Vector((0.0, 0.0, half)))
    bm.verts.ensure_lookup_table()

    # Barrel quads
    for i in range(segments):
        j = (i + 1) % segments
        bm.faces.new([bot_ring[i], bot_ring[j], top_ring[j], top_ring[i]])

    # Bottom cap triangles (winding: outward normal = -Z)
    for i in range(segments):
        j = (i + 1) % segments
        bm.faces.new([bot_cap, bot_ring[j], bot_ring[i]])

    # Top cap triangles (winding: outward normal = +Z)
    for i in range(segments):
        j = (i + 1) % segments
        bm.faces.new([top_cap, top_ring[i], top_ring[j]])

    return bot_ring, top_ring, bot_cap, top_cap


# ---------------------------------------------------------------------------
# WoodLog
# ---------------------------------------------------------------------------


@GeneratorRegistry.register("wood_log")
class WoodLogGenerator:
    """Cut log segment lying flat on the ground.

    8-sided cylinder (upright Z axis), then rotated 90° around X so it lies
    along Y. Slight taper (r1 != r2) and per-vertex radial noise for organic
    bark feel.
    """

    def __init__(self, width=0.9, depth=0.35, height=0.35, seed=301, **kwargs):
        self.length = float(width)  # 0.9 m log length
        self.radius = float(depth) / 2.0  # 0.175 m radius
        self.seed = int(seed)

    def create_mesh(self):
        obj, mesh = _make_object("WoodLog")
        bm = bmesh.new()

        segments = 8
        r1 = self.radius
        r2 = self.radius * 0.90  # 10% taper

        _build_cylinder_bmesh(bm, r1, r2, self.length, segments)

        # Radial noise on barrel verts (skip cap centres at origin XY)
        rng = random.Random(self.seed)
        amp = self.radius * 0.12
        for v in bm.verts:
            r = math.sqrt(v.co.x**2 + v.co.y**2)
            if r < 1e-4:
                continue
            nx = v.co.x / r
            ny = v.co.y / r
            delta = rng.uniform(-amp, amp)
            v.co.x += nx * delta
            v.co.y += ny * delta
            v.co.z += rng.uniform(-amp * 0.4, amp * 0.4)

        # Rotate 90° around X: cylinder (Z-axis) → lies along Y-axis
        rot = Matrix.Rotation(math.pi / 2.0, 3, "X")
        for v in bm.verts:
            v.co = rot @ v.co

        # Seat at z=0
        min_z = min(v.co.z for v in bm.verts)
        for v in bm.verts:
            v.co.z -= min_z

        bmesh.ops.triangulate(bm, faces=bm.faces[:])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])

        bm.to_mesh(mesh)
        bm.free()
        return obj


# ---------------------------------------------------------------------------
# Bow_Short
# ---------------------------------------------------------------------------


@GeneratorRegistry.register("bow_short")
class BowShortGenerator:
    """Short bow: D-shaped limb arc + thin bowstring.

    The D-arc is traced as a 10-vertex edge loop in the XZ plane (upright),
    extruded along Y for limb cross-section depth. Bowstring is a 4-sided
    cylinder built manually. Assembly is then rotated 90° around Y so it lies
    flat on the ground.
    """

    def __init__(self, width=0.1, depth=0.05, height=0.9, seed=401, **kwargs):
        self.bow_height = float(height)  # 0.9 m
        self.bow_width = float(width)  # 0.1 m belly depth
        self.thickness = float(depth)  # 0.05 m limb Y-depth
        self.seed = int(seed)

    def _arc_pts(self, rng):
        """10 (x, z) points: sinusoidal D-belly, zero at tips."""
        n = 10
        half_h = self.bow_height / 2.0
        belly = self.bow_width * (1.0 + rng.uniform(-0.08, 0.08))
        pts = []
        for i in range(n):
            t = i / (n - 1)
            z = -half_h + t * self.bow_height
            x = belly * math.sin(t * math.pi)
            pts.append((x, z))
        return pts

    def create_mesh(self):
        obj, mesh = _make_object("Bow_Short")
        bm = bmesh.new()
        rng = random.Random(self.seed)

        arc_pts = self._arc_pts(rng)
        half_t = self.thickness / 2.0
        n = len(arc_pts)

        # Two parallel edge loops: front (y=-half_t) and back (y=+half_t)
        fv = [bm.verts.new(Vector((x, -half_t, z))) for x, z in arc_pts]
        bv = [bm.verts.new(Vector((x, half_t, z))) for x, z in arc_pts]
        bm.verts.ensure_lookup_table()

        # Outer (belly) side faces
        for i in range(n - 1):
            bm.faces.new([fv[i], fv[i + 1], bv[i + 1], bv[i]])

        # Inner (straight-back) seam face
        bm.faces.new([fv[0], bv[0], bv[n - 1], fv[n - 1]])

        # Bottom tip cap
        bot = bm.verts.new(Vector((0.0, 0.0, -self.bow_height / 2.0)))
        bm.faces.new([fv[0], bv[0], bot])

        # Top tip cap
        top = bm.verts.new(Vector((0.0, 0.0, self.bow_height / 2.0)))
        bm.faces.new([bv[n - 1], fv[n - 1], top])

        # Bowstring: thin 4-sided cylinder along Z (back of D, x=0)
        _build_cylinder_bmesh(bm, 0.006, 0.006, self.bow_height * 0.95, 4)

        bmesh.ops.triangulate(bm, faces=bm.faces[:])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])

        # Lay flat: rotate 90° around Y (upright Z → lying along X)
        rot = Matrix.Rotation(-math.pi / 2.0, 3, "Y")
        for v in bm.verts:
            v.co = rot @ v.co

        # Seat at z=0
        min_z = min(v.co.z for v in bm.verts)
        for v in bm.verts:
            v.co.z -= min_z

        bm.to_mesh(mesh)
        bm.free()
        return obj


# ---------------------------------------------------------------------------
# Mineable base (shared displaced-rock + crystal-vein logic)
# ---------------------------------------------------------------------------


class _MineableBase:
    """Displaced-cube rock base with extruded crystal/vein faces.

    Subclasses set crystal_count, extrude_dist, scale_in, and roughness.
    """

    crystal_count = 3
    extrude_dist = 0.18
    scale_in = 0.30
    roughness = 0.38

    def __init__(self, width=0.8, depth=0.8, height=0.6, seed=501, **kwargs):
        self.width = float(width)
        self.depth = float(depth)
        self.height = float(height)
        self.seed = int(seed)

    def create_mesh(self):
        obj, mesh = _make_object(self.__class__.__name__)
        bm = bmesh.new()

        cuts = 2
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=cuts, use_grid_fill=True)

        spacing = 1.0 / (cuts + 1)
        amp = self.roughness * spacing

        rng = random.Random(self.seed)
        for v in bm.verts:
            v.co.x += rng.uniform(-amp, amp)
            v.co.y += rng.uniform(-amp, amp)
            v.co.z += rng.uniform(-amp, amp)

        # Flatten underside
        floor = min(v.co.z for v in bm.verts)
        for v in bm.verts:
            if v.co.z < floor + amp * 2.0:
                v.co.z = floor

        # Crystal / vein extrusions
        bm.faces.ensure_lookup_table()
        candidate_faces = [f for f in bm.faces if f.normal.z > -0.3]

        rng2 = random.Random(self.seed + 1000)
        rng2.shuffle(candidate_faces)
        shard_faces = candidate_faces[: self.crystal_count]

        for face in shard_faces:
            # Save normal before extrusion (face will be invalidated after)
            nrm = face.normal.copy()
            center = face.calc_center_median()

            ret = bmesh.ops.extrude_face_region(bm, geom=list(face.verts) + [face])
            extruded_geom = ret["geom"]
            new_verts = [g for g in extruded_geom if isinstance(g, bmesh.types.BMVert)]

            # Translate new verts outward along original face normal
            offset = nrm * self.extrude_dist
            for v in new_verts:
                v.co += offset

            # Scale new verts toward their centroid for taper (crystal tip)
            tip_center = center + offset
            for v in new_verts:
                diff = v.co - tip_center
                v.co = tip_center + diff * self.scale_in

        _fit_to_bounds(bm, self.width, self.depth, self.height)
        bmesh.ops.triangulate(bm, faces=bm.faces[:])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])

        bm.to_mesh(mesh)
        bm.free()
        return obj


@GeneratorRegistry.register("mineable_gold")
class MineableGoldGenerator(_MineableBase):
    """Gold ore vein: 3-4 sharp angular crystal shards protruding from rock."""

    crystal_count = 4
    extrude_dist = 0.22
    scale_in = 0.20
    roughness = 0.36

    def __init__(self, width=0.8, depth=0.8, height=0.6, seed=501, **kwargs):
        super().__init__(width=width, depth=depth, height=height, seed=seed, **kwargs)


@GeneratorRegistry.register("mineable_silver")
class MineableSilverGenerator(_MineableBase):
    """Silver ore vein: 2-3 medium crystal clusters, slightly flatter than gold."""

    crystal_count = 3
    extrude_dist = 0.16
    scale_in = 0.30
    roughness = 0.38

    def __init__(self, width=0.8, depth=0.8, height=0.6, seed=511, **kwargs):
        super().__init__(width=width, depth=depth, height=height, seed=seed, **kwargs)


@GeneratorRegistry.register("mineable_steel")
class MineableSteelGenerator(_MineableBase):
    """Steel/iron ore vein: 2-3 wide flat seams, blocky and massive."""

    crystal_count = 2
    extrude_dist = 0.10
    scale_in = 0.70
    roughness = 0.42

    def __init__(self, width=0.8, depth=0.8, height=0.55, seed=521, **kwargs):
        super().__init__(width=width, depth=depth, height=height, seed=seed, **kwargs)
