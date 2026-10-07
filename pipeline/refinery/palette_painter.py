"""Palette painter: colour travels inside the mesh as UVs into palette/palette.png.

Replaces the PBR unwrap + bake for the game path. Every face is assigned a swatch (a role) and
a shade; its loops' UVs are set to the centre of that cell. The object leaves with exactly one
material, M_Palette, whose base colour is the atlas with nearest-neighbour sampling, so Blender
renders match what Unity shows once the Host remaps everything to its shared palette material.

Role resolution, first match wins:
  1. the face's material slot name (generators name slots like House_Paleo_Thatch, M_Timber)
  2. flora slot index (0 = bark, 1+ = leaf)
  3. the asset name prefix (Limestone_a -> limestone, ChunkGranite_b -> granite, ...)
  4. the archetype's default
Accent rules then nudge some faces (moss on upward rock faces, ore flecks, cloth on a bed top).
"""

import json
import random
from pathlib import Path

import bpy
from mathutils import Vector

PALETTE_DIR = Path(__file__).resolve().parent.parent.parent / "palette"
SHADE_WEIGHTS = [1, 2, 4, 2, 1]  # bell over the 5 shades: most faces sit near the base colour

# material-slot name fragment -> swatch (checked lowercase, longest fragment first)
SLOT_ROLES = {
    "rooftile": "roof_tile",
    "roof": "roof_tile",
    "woodplank": "plank",
    "plank": "plank",
    "door": "plank",
    "shutter": "plank",
    "timber": "timber_dark",
    "beam": "timber_dark",
    "stone": "stone_wall",
    "glass": "glass",
    "iron": "iron",
    "metal": "iron",
    "thatch": "thatch",
    "straw": "thatch",
    "reed": "thatch",
    "hide": "hide",
    "leather": "hide",
    "fur": "hide",
    "daub": "daub",
    "mud": "daub",
    "clay": "daub",
    "plaster": "plaster",
    "lime": "plaster",
    "wattle": "wattle",
    "wicker": "wattle",
    "cloth": "cloth",
    "bedding": "cloth",
    "bark": "bark",
    "stem": "bark",
    "trunk": "bark",
    "branch": "bark",
    "leaf": "leaf",
    "foliage": "leaf",
    "canopy": "leaf",
    "berry": "berry",
    "soil": "soil",
    "dirt": "soil",
    "moss": "moss",
    # prehistoric_homes / ancient_homes_cd slot names
    "birchbark": "bark",
    "bone": "plaster",
    "hearth": "daub",
    "clayroof": "roof_tile",
    "mudtile": "daub",
    "mudbrick": "daub",
    "adobe": "plaster",
    "drystone": "stone_wall",
    "tiles": "roof_tile",
    "copper": "copper",
    "rope": "wattle",
    "stick": "plank",
    "turf": "moss",
    "blueprint": "blueprint",
}

# asset-name prefix -> swatch
NAME_ROLES = {
    "Limestone": "limestone",
    "ChunkLimestone": "limestone",
    "BlocksLimestone": "limestone",
    "Granite": "granite",
    "ChunkGranite": "granite",
    "BlocksGranite": "granite",
    "Sandstone": "sandstone",
    "ChunkSandstone": "sandstone",
    "BlocksSandstone": "sandstone",
    "CollapsedRocks": "granite",
    "WoodLog": "bark",
    "Bow": "plank",
    "Mineable": "ore_rock",
    "Wall": "stone_wall",
    "WallGranite": "granite",
    "WallLimestone": "limestone",
    "WallSandstone": "sandstone",
    "Door": "plank",
    "StorageHut": "plank",
    "Bed": "plank",
    "Blueprint": "blueprint",
    "Frame": "plank",
    "House": "daub",
    "Plant": "leaf",
    "WildPlant": "leaf",
}

ARCHETYPE_ROLES = {
    "natural_rock": "granite",
    "chunk_granite": "granite",
    "chunk_limestone": "limestone",
    "chunk_sandstone": "sandstone",
    "wood_log": "bark",
    "bow_short": "plank",
    "mineable_gold": "ore_rock",
    "mineable_silver": "ore_rock",
    "mineable_steel": "ore_rock",
    "wild_plant": "leaf",
    "plant_berry": "leaf",
    "tree_poplar": "leaf",
    "bed_simple": "plank",
    "prop_crate": "plank",
    "prop_cylinder": "iron",
    "modular_wall": "stone_wall",
    "modular_floor": "plank",
    "modular_column": "stone_wall",
    "prop_medieval_home": "plaster",
}

ORE_FLECK = {
    "mineable_gold": "ore_gold",
    "mineable_silver": "ore_silver",
    "mineable_steel": "ore_steel",
}
ROCK_ROLES = {"limestone", "granite", "sandstone", "ore_rock"}


def load_palette() -> dict:
    return json.loads((PALETTE_DIR / "palette.json").read_text(encoding="utf-8"))


def _slot_role(slot_name: str | None) -> str | None:
    if not slot_name:
        return None
    s = slot_name.lower()
    for fragment in sorted(SLOT_ROLES, key=len, reverse=True):
        if fragment in s:
            return SLOT_ROLES[fragment]
    return None


def _name_role(asset_name: str) -> str | None:
    for prefix in sorted(NAME_ROLES, key=len, reverse=True):
        if asset_name.startswith(prefix):
            return NAME_ROLES[prefix]
    return None


def _base_role(obj: bpy.types.Object, face, asset_name: str, archetype: str) -> str:
    # Walls are named for their stone (WallGranite...), and that beats the modular generator's
    # generic slot names; everything else trusts the generator's slot first.
    if asset_name.startswith("Wall"):
        return _name_role(asset_name) or "stone_wall"
    slots = obj.data.materials
    slot = slots[face.material_index] if face.material_index < len(slots) else None
    role = _slot_role(slot.name if slot else None)
    if role:
        return role
    if archetype in ("wild_plant", "plant_berry", "tree_poplar"):
        return "bark" if face.material_index == 0 else "leaf"
    return _name_role(asset_name) or ARCHETYPE_ROLES.get(archetype, "granite")


def _accent(role: str, face, obj, asset_name: str, archetype: str, rng: random.Random) -> str:
    up = face.normal.z
    if role in ROCK_ROLES and up > 0.75 and archetype != "mineable_gold" and rng.random() < 0.18:
        return "moss"
    if archetype in ORE_FLECK and rng.random() < 0.3:
        return ORE_FLECK[archetype]
    if archetype == "plant_berry" and role == "leaf" and rng.random() < 0.15:
        return "berry"
    if archetype == "tree_poplar" and role == "leaf" and rng.random() < 0.12:
        return "leaf_dry"
    if asset_name.startswith("Bed") and up > 0.9 and face.center.z > 0.15:
        return "cloth"
    if asset_name.startswith("StorageHut") and up > 0.3 and face.center.z > obj.dimensions.z * 0.5:
        return "thatch"
    return role


def _ensure_material(palette_png: Path) -> bpy.types.Material:
    mat = bpy.data.materials.get("M_Palette")
    if mat:
        return mat
    mat = bpy.data.materials.new("M_Palette")
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.85
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(palette_png), check_existing=True)
    tex.interpolation = "Closest"
    tex.location = (-400, 200)
    links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


def paint(obj: bpy.types.Object, asset_name: str, archetype: str, seed: int) -> dict[str, int]:
    """Assign palette UVs and the single M_Palette material. Returns faces per swatch."""
    palette = load_palette()
    swatches = palette["swatches"]
    rng = random.Random(seed * 7919 + len(asset_name))
    mesh = obj.data

    roles = []
    for face in mesh.polygons:
        role = _accent(
            _base_role(obj, face, asset_name, archetype), face, obj, asset_name, archetype, rng
        )
        if role not in swatches:
            role = "granite"
        roles.append(role)

    uv = mesh.uv_layers.get("UVMap") or mesh.uv_layers.new(name="UVMap")
    mesh.uv_layers.active = uv
    for face, role in zip(mesh.polygons, roles, strict=True):
        cells = swatches[role]["uvs"]
        shade = rng.choices(range(len(cells)), weights=SHADE_WEIGHTS[: len(cells)])[0]
        u, v = cells[shade]
        for li in face.loop_indices:
            uv.data[li].uv = Vector((u, v))

    mesh.materials.clear()
    mesh.materials.append(_ensure_material(PALETTE_DIR / "palette.png"))
    for face in mesh.polygons:
        face.material_index = 0

    counts: dict[str, int] = {}
    for role in roles:
        counts[role] = counts.get(role, 0) + 1
    return counts
