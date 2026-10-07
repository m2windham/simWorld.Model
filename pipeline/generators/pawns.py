"""Settlers: Human_a..d, chunky stylized figures in the settlement register.

Contract (Host MapRenderer): 1x1, centred, feet at z = 0, facing Blender +Y (Unity -Z), 1 unit per
cell, drawn as a static instance rotated by Rot4 and scaled by BodySize; lying pawns are tipped by
the host. Budget 300 triangles including the hull.

One generator, four silhouettes chosen by variant: build (slim / stocky), headgear (bare, hood,
cap, headband). Large head and hands, no face, hard-edged tunic with a dark belt and trim. Slot
names drive the palette: M_Skin, M_Tunic, M_Trim, M_Hair, M_Headgear.
"""

import bmesh
import bpy
from mathutils import Vector

from .construction_stages import _box
from .generator_registry import GeneratorRegistry

SLOTS = ("M_Skin", "M_Tunic", "M_Trim", "M_Hair", "M_Headgear")
SKIN, TUNIC, TRIM, HAIR, HEADGEAR = range(5)

VARIANTS = {
    "a": {"build": 1.00, "head": "bare"},
    "b": {"build": 1.12, "head": "hood"},
    "c": {"build": 0.92, "head": "cap"},
    "d": {"build": 1.06, "head": "band"},
}


def _slot_box(bm, centre, size, slot) -> None:
    before = set(bm.faces)
    _box(bm, centre, size)
    for f in set(bm.faces) - before:
        f.material_index = slot


@GeneratorRegistry.register("human")
class HumanGenerator:
    def __init__(self, width=1.0, depth=1.0, height=0.9, seed=0, variant="a", **kwargs):
        self.height = float(height)
        self.variant = VARIANTS.get(variant, VARIANTS["a"])

    def create_mesh(self) -> bpy.types.Object:
        h = self.height
        b = self.variant["build"]  # widens the torso and limbs, not the height
        bm = bmesh.new()

        leg_h, torso_h, head = h * 0.36, h * 0.34, h * 0.24
        neck = h * 0.02
        torso_w, torso_d = 0.30 * b, 0.18 * b
        leg_w = 0.10 * b
        # legs, slightly apart; dark trim as boots
        for x in (-leg_w * 0.75, leg_w * 0.75):
            _slot_box(
                bm, Vector((x, 0, leg_h * 0.55)), Vector((leg_w, leg_w * 1.1, leg_h * 0.9)), TUNIC
            )
            _slot_box(
                bm,
                Vector((x, 0.01, leg_h * 0.07)),
                Vector((leg_w * 1.15, leg_w * 1.5, leg_h * 0.14)),
                TRIM,
            )
        # torso with a dark belt and hem trim
        z0 = leg_h
        _slot_box(bm, Vector((0, 0, z0 + torso_h / 2)), Vector((torso_w, torso_d, torso_h)), TUNIC)
        _slot_box(
            bm,
            Vector((0, 0, z0 + torso_h * 0.18)),
            Vector((torso_w + 0.01, torso_d + 0.01, torso_h * 0.1)),
            TRIM,
        )
        # arms hang at the sides; big hands
        arm_w = 0.08 * b
        for x in (-torso_w / 2 - arm_w / 2 - 0.01, torso_w / 2 + arm_w / 2 + 0.01):
            _slot_box(
                bm,
                Vector((x, 0, z0 + torso_h * 0.55)),
                Vector((arm_w, arm_w, torso_h * 0.8)),
                TUNIC,
            )
            _slot_box(
                bm,
                Vector((x, 0.005, z0 + torso_h * 0.1)),
                Vector((arm_w * 1.3, arm_w * 1.3, torso_h * 0.18)),
                SKIN,
            )
        # head: oversized block, neck, no face
        z1 = z0 + torso_h
        _slot_box(bm, Vector((0, 0, z1 + neck / 2)), Vector((0.10 * b, 0.10 * b, neck)), SKIN)
        head_w = 0.26
        _slot_box(
            bm, Vector((0, 0, z1 + neck + head / 2)), Vector((head_w, head_w * 0.95, head)), SKIN
        )
        # headgear per variant
        kind = self.variant["head"]
        top = z1 + neck + head
        if kind == "bare":
            _slot_box(
                bm,
                Vector((0, -0.02, top - head * 0.12)),
                Vector((head_w + 0.01, head_w * 0.9, head * 0.3)),
                HAIR,
            )
        elif kind == "hood":
            _slot_box(
                bm,
                Vector((0, -0.03, z1 + neck + head * 0.55)),
                Vector((head_w + 0.06, head_w * 1.05, head * 1.0)),
                HEADGEAR,
            )
        elif kind == "cap":
            _slot_box(
                bm,
                Vector((0, 0, top + 0.015)),
                Vector((head_w + 0.02, head_w * 0.95, 0.05)),
                HEADGEAR,
            )
            _slot_box(
                bm,
                Vector((0, head_w * 0.6, top - 0.01)),
                Vector((head_w * 0.8, head_w * 0.35, 0.02)),
                HEADGEAR,
            )  # brim, front
        else:  # band
            _slot_box(
                bm,
                Vector((0, 0, top - head * 0.2)),
                Vector((head_w + 0.015, head_w + 0.015, head * 0.12)),
                TRIM,
            )
            _slot_box(
                bm,
                Vector((0, -0.02, top - head * 0.06)),
                Vector((head_w, head_w * 0.9, head * 0.12)),
                HAIR,
            )

        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        mesh = bpy.data.meshes.new("Human")
        bm.to_mesh(mesh)
        bm.free()
        obj = bpy.data.objects.new("Human", mesh)
        bpy.context.collection.objects.link(obj)
        for slot in SLOTS:
            obj.data.materials.append(bpy.data.materials.get(slot) or bpy.data.materials.new(slot))
        return obj
