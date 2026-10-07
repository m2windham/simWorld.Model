"""Rock chunk debris generators for mining output items.

Three archetypes: ChunkGranite, ChunkLimestone, ChunkSandstone.

The silhouette strategy differs from natural_rock.py. Natural rocks need to fill
their cell and hide grid repetition at ~13,000 instances; they use vertex
displacement on a subdivided cube. Chunks are loose debris: each should read as
a distinct broken piece, not a wall tile. The technique here is:

  1. Start from a box at the target aspect ratio.
  2. Run 3-4 passes of random face selection -> inset -> extrude (inward or
     outward) to chip facets into the silhouette.
  3. Flatten the underside so the chunk sits on the floor.
  4. _fit_to_bounds rescales to exact target dimensions (same contract as
     natural_rock: the dimension gate passes deterministically).

Shape character per archetype:
  ChunkGranite  — deep insets, steep extrusions, tight face selection → sharp
                  angular shards, close to cubic proportions.
  ChunkLimestone — moderate insets, shallow extrusions, wider face selection →
                  softer but still broken-looking chunk.
  ChunkSandstone — shallow insets, very shallow extrusions, horizontal face
                  bias → flatter piece with subtle laminar layering.
"""

import random

import bmesh
import bpy

from .generator_registry import GeneratorRegistry


def _build_chunk(
    bm,
    rng,
    passes,
    face_prob,
    inset_thickness,
    inset_depth,
    extrude_range,
    horizontal_bias,
):
    """Core chunk-shaping routine shared by all three archetypes.

    Args:
        bm: BMesh to operate on (must already contain geometry).
        rng: seeded random.Random instance.
        passes: number of inset+extrude rounds.
        face_prob: probability any given face is included in each round.
        inset_thickness: bmesh inset relative_thickness value.
        inset_depth: bmesh inset depth (pulls face inward before extrude).
        extrude_range: (lo, hi) tuple for extrude distance; negative = inward.
        horizontal_bias: when > 0, extrusion on top/bottom faces is scaled by
                         this factor relative to side faces, emphasising layers.
    """
    for _ in range(passes):
        candidates = [f for f in bm.faces if rng.random() < face_prob]
        if not candidates:
            continue

        # Inset selected faces to create a new inner polygon ring.
        bmesh.ops.inset_individual(
            bm,
            faces=candidates,
            thickness=inset_thickness,
            depth=inset_depth,
            use_even_offset=True,
        )

        # Re-gather: inset_individual returns new interior faces; the simplest
        # strategy is to collect all faces whose normal is predominantly
        # vertical or not, then pick a fresh random subset to extrude — this
        # avoids needing to track return geometry explicitly.
        inner = [f for f in bm.faces if rng.random() < face_prob * 0.8]
        if not inner:
            continue

        for face in inner:
            # Determine extrude distance; apply horizontal bias for top/bottom.
            dist = rng.uniform(*extrude_range)
            if horizontal_bias > 0:
                normal_z_abs = abs(face.normal.z)
                dist *= 1.0 + horizontal_bias * normal_z_abs
            ret = bmesh.ops.extrude_discrete_faces(bm, faces=[face])
            # extrude_discrete_faces returns {'faces': [BMFace, ...]}.
            new_faces = ret["faces"]
            if not new_faces:
                continue
            new_face = new_faces[0]
            bmesh.ops.translate(
                bm,
                verts=new_face.verts[:],
                vec=new_face.normal * dist,
            )

    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=0.001)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])


def _fit_to_bounds(bm, width, depth, height):
    """Scale displaced chunk to exact requested dimensions, pivot at z=0.

    Identical contract to NaturalRockGenerator._fit_to_bounds so the same
    pre-flight dimension gate works for both generators.
    """
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


def _flatten_underside(bm, amp):
    """Pull near-floor vertices to z=0, giving the chunk a stable base."""
    floor = min(v.co.z for v in bm.verts)
    for v in bm.verts:
        if v.co.z < floor + amp:
            v.co.z = floor


def _make_chunk_object(
    name,
    width,
    depth,
    height,
    seed,
    passes,
    face_prob,
    inset_thickness,
    inset_depth,
    extrude_range,
    horizontal_bias,
):
    """Construct a chunk BMesh, apply shaping, export to a Blender object."""
    mesh = bpy.data.meshes.new(name=name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    # Start from a box scaled to the target aspect ratio so the face
    # areas are representative of the final proportions before any cuts.
    bmesh.ops.create_cube(bm, size=1.0)
    # Scale to target proportions immediately so horizontal_bias has
    # geometrically correct face normal information during shaping.
    for v in bm.verts:
        v.co.x *= width
        v.co.y *= depth
        v.co.z *= height

    rng = random.Random(seed)
    _build_chunk(
        bm, rng, passes, face_prob, inset_thickness, inset_depth, extrude_range, horizontal_bias
    )

    _flatten_underside(bm, height * 0.12)
    _fit_to_bounds(bm, width, depth, height)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])

    bm.to_mesh(mesh)
    bm.free()
    return obj


# ---------------------------------------------------------------------------
# ChunkGranite
# ---------------------------------------------------------------------------


@GeneratorRegistry.register("chunk_granite")
class ChunkGraniteGenerator:
    """Angular, sharp-edged granite debris chunk (~0.5 x 0.5 x 0.4 m).

    Granite is the hardest stone in the simulation; its chunks break with
    conchoidal fracture — flat, sharp faces at steep angles. Three or four
    passes with deep insets and steep extrusions produce this character.
    """

    def __init__(self, width=0.5, depth=0.5, height=0.4, seed=201, **kwargs):
        self.width = float(width)
        self.depth = float(depth)
        self.height = float(height)
        self.seed = int(seed)

    def create_mesh(self):
        return _make_chunk_object(
            name="ChunkGranite",
            width=self.width,
            depth=self.depth,
            height=self.height,
            seed=self.seed,
            passes=2,
            face_prob=0.55,
            inset_thickness=0.18,
            inset_depth=0.04,
            extrude_range=(-0.12, 0.18),
            horizontal_bias=0.0,  # granite: no directional preference
        )


# ---------------------------------------------------------------------------
# ChunkLimestone
# ---------------------------------------------------------------------------


@GeneratorRegistry.register("chunk_limestone")
class ChunkLimestoneGenerator:
    """Moderately rough limestone debris chunk (~0.5 x 0.5 x 0.35 m).

    Limestone is softer than granite; it breaks with rounder edges and less
    dramatic angular relief. Shallower insets and a wider face selection give
    a more softly faceted silhouette.
    """

    def __init__(self, width=0.5, depth=0.5, height=0.35, seed=211, **kwargs):
        self.width = float(width)
        self.depth = float(depth)
        self.height = float(height)
        self.seed = int(seed)

    def create_mesh(self):
        return _make_chunk_object(
            name="ChunkLimestone",
            width=self.width,
            depth=self.depth,
            height=self.height,
            seed=self.seed,
            passes=2,
            face_prob=0.65,
            inset_thickness=0.14,
            inset_depth=0.025,
            extrude_range=(-0.08, 0.13),
            horizontal_bias=0.0,
        )


# ---------------------------------------------------------------------------
# ChunkSandstone
# ---------------------------------------------------------------------------


@GeneratorRegistry.register("chunk_sandstone")
class ChunkSandstoneGenerator:
    """Flat, layered sandstone debris chunk (~0.5 x 0.5 x 0.3 m).

    Sandstone is sedimentary: it fractures along near-horizontal bedding
    planes. The horizontal_bias parameter amplifies extrusion distance on
    top/bottom faces relative to side faces, producing the laminar steps
    that read as stratification. The lower height target (0.3 m) reinforces
    the flatter, slab-like silhouette.
    """

    def __init__(self, width=0.5, depth=0.5, height=0.3, seed=221, **kwargs):
        self.width = float(width)
        self.depth = float(depth)
        self.height = float(height)
        self.seed = int(seed)

    def create_mesh(self):
        return _make_chunk_object(
            name="ChunkSandstone",
            width=self.width,
            depth=self.depth,
            height=self.height,
            seed=self.seed,
            passes=3,
            face_prob=0.60,
            inset_thickness=0.12,
            inset_depth=0.015,
            extrude_range=(-0.05, 0.10),
            horizontal_bias=0.9,  # sandstone: strong layering emphasis
        )
