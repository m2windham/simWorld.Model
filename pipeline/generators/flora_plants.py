"""Flora generators: ground-cover plants and berry bushes.

Two archetypes for SimWorld's highest-volume surface flora:

* **wild_plant** — 775 instances per live map. A small ground-cover shrub built
  from a short stem cylinder and 3-5 icosphere leaf clusters merged together.
  Variants differ via seed-driven cluster count, radii, and offset angles.
  Target: ~150 triangles per variant at 0.6m x 0.6m x 0.5m.

* **plant_berry** — 605 instances. Same structure as wild_plant but wider and
  taller, plus a ring of small sphere nubs representing berry clusters.
  Target: ~180 triangles per variant at 0.8m x 0.8m x 0.7m.

Material slots:
  mat_idx 0 — stem / bark (host tints warm brown)
  mat_idx 1 — foliage / berries (host tints green or red)

Geometry is ground-seated: pivot at Z=0, centered X/Y. The host's MapRenderer
scales height dynamically by plant growth (0.25 + 0.75 * growth), so the mesh
is modelled at full-grown size and the engine handles the rest.

Icosphere subdivision level 1 gives 80 triangles per sphere. With 3-5 clusters
and a stem cylinder we land well inside the budget. Berry nubs use level 0
(20 triangles each) to stay within the 180-tri target.
"""

import math
import random

import bmesh
import bpy

from .generator_registry import GeneratorRegistry


def _clear_scene():
    """Remove all objects from the current scene."""
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def _new_object(name: str, mesh: bpy.types.Mesh) -> bpy.types.Object:
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def _ensure_material_slots(obj: bpy.types.Object, count: int):
    """Guarantee obj has exactly `count` material slots (may be empty)."""
    while len(obj.data.materials) < count:
        obj.data.materials.append(None)


def _build_stem_cylinder(
    bm: bmesh.types.BMesh, radius: float, height: float, segments: int = 6, mat_idx: int = 0
):
    """Add an upright closed cylinder representing the main plant stem.

    The cylinder base sits at Z=0. Faces are assigned mat_idx so the host
    shader can tint stem/bark independently from foliage.
    """
    verts_bottom = []
    verts_top = []
    for i in range(segments):
        angle = 2.0 * math.pi * i / segments
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        verts_bottom.append(bm.verts.new((x, y, 0.0)))
        verts_top.append(bm.verts.new((x, y, height)))

    # Side faces
    for i in range(segments):
        j = (i + 1) % segments
        f = bm.faces.new([verts_bottom[i], verts_bottom[j], verts_top[j], verts_top[i]])
        f.material_index = mat_idx

    # Cap faces
    center_bot = bm.verts.new((0.0, 0.0, 0.0))
    center_top = bm.verts.new((0.0, 0.0, height))
    for i in range(segments):
        j = (i + 1) % segments
        f_bot = bm.faces.new([center_bot, verts_bottom[j], verts_bottom[i]])
        f_bot.material_index = mat_idx
        f_top = bm.faces.new([center_top, verts_top[i], verts_top[j]])
        f_top.material_index = mat_idx

    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()


def _add_icosphere_cluster(
    bm: bmesh.types.BMesh,
    cx: float,
    cy: float,
    cz: float,
    radius: float,
    subdivisions: int = 1,
    mat_idx: int = 1,
):
    """Merge a subdivided icosphere into `bm` at the given centre offset.

    BMesh has no direct 'create icosphere at position' op, so we build it in a
    temporary BMesh, translate, then merge verts/faces into the target.
    """
    tmp = bmesh.new()
    bmesh.ops.create_icosphere(tmp, subdivisions=subdivisions, radius=radius)
    for v in tmp.verts:
        v.co.x += cx
        v.co.y += cy
        v.co.z += cz

    # Transfer geometry into target bm
    vert_map = {}
    for v in tmp.verts:
        nv = bm.verts.new(v.co)
        vert_map[v.index] = nv
    bm.verts.ensure_lookup_table()

    for f in tmp.faces:
        new_verts = [vert_map[v.index] for v in f.verts]
        try:
            nf = bm.faces.new(new_verts)
            nf.material_index = mat_idx
        except ValueError:
            pass  # duplicate face; skip

    tmp.free()


@GeneratorRegistry.register("wild_plant")
class WildPlantGenerator:
    """Procedural low-poly ground-cover plant for high-density map placement.

    Builds a short stem cylinder plus 3-5 icosphere leaf clusters merged into
    one continuous mesh. Seed controls cluster count, radii, angular offsets,
    and height scatter so each variant reads distinctly from above.
    """

    def __init__(self, width=0.6, depth=0.6, height=0.5, seed=0, **kwargs):
        self.width = float(width)
        self.depth = float(depth)
        self.height = float(height)
        self.seed = int(seed)

    def create_mesh(self) -> bpy.types.Object:
        mesh = bpy.data.meshes.new("WildPlant")
        obj = _new_object("WildPlant", mesh)
        _ensure_material_slots(obj, 2)

        rng = random.Random(self.seed)

        bm = bmesh.new()

        # Stem: thin cylinder, roughly 1/4 of total height
        stem_r = 0.03
        stem_h = self.height * 0.28
        _build_stem_cylinder(bm, stem_r, stem_h, segments=6, mat_idx=0)

        # 3-5 leaf clusters, varying by seed
        n_clusters = rng.randint(3, 5)
        spread = self.width * 0.42  # max radial offset from centre
        base_cluster_r = self.height * 0.30

        for i in range(n_clusters):
            angle = rng.uniform(0, 2 * math.pi)
            dist = rng.uniform(0.0, spread)
            cx = dist * math.cos(angle)
            cy = dist * math.sin(angle)
            # Height: lower clusters nearer centre, higher ones at spread edge
            cz = stem_h + rng.uniform(0.0, self.height * 0.55)
            r = base_cluster_r * rng.uniform(0.75, 1.25)
            _add_icosphere_cluster(bm, cx, cy, cz, radius=r, subdivisions=1, mat_idx=1)

        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        bm.to_mesh(mesh)
        bm.free()

        return obj


@GeneratorRegistry.register("plant_berry")
class PlantBerryGenerator:
    """Procedural berry bush — wider, taller WildPlant with berry-nub ring.

    Same leaf-cluster construction as WildPlantGenerator, but the bush is
    slightly larger and a ring of small icosphere-0 nubs (level=0, 20 tris
    each) encircles the mid-height as berry clusters. mat_idx 1 covers both
    foliage and berries so the host can give them a unified green-then-red tint.
    """

    def __init__(self, width=0.8, depth=0.8, height=0.7, seed=0, **kwargs):
        self.width = float(width)
        self.depth = float(depth)
        self.height = float(height)
        self.seed = int(seed)

    def create_mesh(self) -> bpy.types.Object:
        mesh = bpy.data.meshes.new("Plant_Berry")
        obj = _new_object("Plant_Berry", mesh)
        _ensure_material_slots(obj, 2)

        rng = random.Random(self.seed)

        bm = bmesh.new()

        # Stem
        stem_r = 0.04
        stem_h = self.height * 0.25
        _build_stem_cylinder(bm, stem_r, stem_h, segments=6, mat_idx=0)

        # 4-5 main leaf clusters
        n_clusters = rng.randint(4, 5)
        spread = self.width * 0.40
        base_cluster_r = self.height * 0.30

        for i in range(n_clusters):
            angle = rng.uniform(0, 2 * math.pi)
            dist = rng.uniform(0.0, spread)
            cx = dist * math.cos(angle)
            cy = dist * math.sin(angle)
            cz = stem_h + rng.uniform(0.0, self.height * 0.55)
            r = base_cluster_r * rng.uniform(0.80, 1.20)
            _add_icosphere_cluster(bm, cx, cy, cz, radius=r, subdivisions=1, mat_idx=1)

        # Berry nubs: 4-6 small spheres at mid-height ring
        n_berries = rng.randint(4, 6)
        berry_ring_r = self.width * 0.28
        berry_r = 0.045
        berry_z = self.height * 0.48
        for i in range(n_berries):
            angle = (2 * math.pi * i / n_berries) + rng.uniform(-0.2, 0.2)
            bx = berry_ring_r * math.cos(angle)
            by = berry_ring_r * math.sin(angle)
            bz = berry_z + rng.uniform(-0.04, 0.04)
            _add_icosphere_cluster(bm, bx, by, bz, radius=berry_r, subdivisions=0, mat_idx=1)

        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        bm.to_mesh(mesh)
        bm.free()

        return obj


@GeneratorRegistry.register("tree_poplar")
class TreePoplarGenerator:
    def __init__(self, width=1.0, depth=1.0, height=3.0, seed=0, **kwargs):
        self.width = float(width)
        self.depth = float(depth)
        self.height = float(height)
        self.seed = int(seed)

    def create_mesh(self) -> bpy.types.Object:
        mesh = bpy.data.meshes.new("PlantTreePoplar")
        obj = _new_object("PlantTreePoplar", mesh)
        _ensure_material_slots(obj, 2)
        rng = random.Random(self.seed)
        bm = bmesh.new()

        stem_r = 0.1
        stem_h = self.height * 0.4
        _build_stem_cylinder(bm, stem_r, stem_h, segments=8, mat_idx=0)

        num_clusters = rng.randint(5, 7)
        for i in range(num_clusters):
            fraction = i / float(num_clusters - 1)
            cr = rng.uniform(0.3, 0.45) * (1.0 - fraction * 0.4)
            cx = rng.uniform(-0.1, 0.1)
            cy = rng.uniform(-0.1, 0.1)
            cz = stem_h * 0.8 + fraction * (self.height - stem_h - cr)
            _add_icosphere_cluster(bm, cx, cy, cz, radius=cr, subdivisions=1, mat_idx=1)

        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        bm.to_mesh(mesh)
        bm.free()
        return obj
