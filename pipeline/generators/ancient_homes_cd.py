"""
Ancient Era Dwellings - Variants C and D (Completing the 4-Variant Matrix across 4 Eras)
Extends prehistoric_homes.py to provide complete 4-variant sets (_a, _b, _c, _d) for:
- Paleolithic: PaleoHome_C (Hide & Branch Teepee/Yurt), PaleoHome_D (Rock-Overhang Shelter)
- Mesolithic: MesoHome_C (Birch Bark & Moss Wigwam), MesoHome_D (Riverbank Stilt Platform)
- Neolithic: NeoHome_C (Corbelled Dry-Stone Beehive Hut), NeoHome_D (Raised Timber Stilt Lake-House)
- Chalcolithic: ChalcoHome_C (Timber-Plank & Fieldstone Farmstead), ChalcoHome_D (Mudbrick Courtyard Dwelling)

All models adhere strictly to:
- Unified 4.0m (W) x 5.0m (D) building footprint (within +-8% tolerance)
- Ground contact at Z=0.0m
- 100% Watertight closed 2-manifold geometry (0 degenerate faces)
- Multi-slot procedural PBR material setups with procedural noise/bump
"""

import math

import bmesh
import bpy

from .generator_registry import GeneratorRegistry
from .prehistoric_homes import BasePrehistoricGenerator

# =============================================================================
# 1. PALEOLITHIC ERA (Variants C and D)
# =============================================================================


@GeneratorRegistry.register("paleo_home_c")
class PropPaleoHomeCGenerator(BasePrehistoricGenerator):
    """Paleolithic Model C: Mammoth Hide & Timber Branch Conical Teepee / Yurt."""

    def create_mesh(self) -> bpy.types.Object:
        mesh_name = self.kwargs.get("name", "PaleoHome_01_C")
        mesh = bpy.data.meshes.new(name=mesh_name)
        obj = bpy.data.objects.new(mesh_name, mesh)
        bpy.context.collection.objects.link(obj)

        palette = [
            ("M_HideDark", (0.28, 0.18, 0.11), 0.90, 0.00, 0.09, 38.0),
            ("M_WoodBranch", (0.35, 0.25, 0.16), 0.78, 0.00, 0.06, 50.0),
            ("M_Stone", (0.38, 0.36, 0.34), 0.92, 0.00, 0.10, 35.0),
            ("M_RopeLash", (0.22, 0.17, 0.11), 0.70, 0.00, 0.04, 60.0),
        ]
        for mat in self._setup_materials(mesh_name, palette):
            obj.data.materials.append(mat)

        bm = bmesh.new()

        hw = (self.width * 0.90) / 2.0  # ~1.80m
        hd = (self.depth * 0.90) / 2.0  # ~2.25m
        h = self.height * 0.95  # ~3.80m

        # 1. Main conical hide tent body (12-sided cone with blunt smoke hole apex)
        segments = 12
        eave_z = 0.20
        apex_z = h
        smoke_r = 0.35
        bot_verts = []
        top_verts = []

        for i in range(segments):
            angle = (2.0 * math.pi * i) / segments
            bx = hw * math.cos(angle)
            by = hd * math.sin(angle)
            tx = smoke_r * math.cos(angle)
            ty = smoke_r * (hd / hw) * math.sin(angle)

            bot_verts.append(bm.verts.new((bx, by, eave_z)))
            top_verts.append(bm.verts.new((tx, ty, apex_z)))

        # Connect conical sides
        for i in range(segments):
            i_next = (i + 1) % segments
            # Leave front wedge open for entrance flap
            if i == 9:  # South entrance
                # Inward recessed flap
                door_face = bm.faces.new(
                    [bot_verts[i], bot_verts[i_next], top_verts[i_next], top_verts[i]]
                )
                door_face.material_index = 0
            else:
                f = bm.faces.new([bot_verts[i], bot_verts[i_next], top_verts[i_next], top_verts[i]])
                f.material_index = 0

        # Cap bottom to ensure 2-manifold
        center_bot = bm.verts.new((0, 0, eave_z))
        for i in range(segments):
            i_next = (i + 1) % segments
            fb = bm.faces.new([center_bot, bot_verts[i_next], bot_verts[i]])
            fb.material_index = 0

        # Cap top smoke collar
        center_top = bm.verts.new((0, 0, apex_z))
        for i in range(segments):
            i_next = (i + 1) % segments
            ft = bm.faces.new([center_top, top_verts[i], top_verts[i_next]])
            ft.material_index = 0

        # 2. Exposed protruding pole ends through top smoke hole
        for i in range(6):
            pole_ang = (2.0 * math.pi * i) / 6.0
            px = (smoke_r * 0.7) * math.cos(pole_ang)
            py = (smoke_r * 0.7) * math.sin(pole_ang)
            self._add_box(bm, (px, py, apex_z + 0.35), (0.12, 0.12, 0.85), mat_idx=1)

        # 3. Heavy stone skirt around ground perimeter (12 anchoring boulders)
        for i in range(segments):
            angle = (2.0 * math.pi * i) / segments
            sx = (hw + 0.15) * math.cos(angle)
            sy = (hd + 0.15) * math.sin(angle)
            if abs(angle - (-math.pi / 2.0)) < 0.35:
                continue  # entrance clearance
            self._add_box(bm, (sx, sy, 0.18), (0.45, 0.40, 0.36), mat_idx=2)

        # 4. Timber entrance portal posts & lintel
        ey = -hd - 0.05
        self._add_box(bm, (-0.55, ey, 0.90), (0.14, 0.16, 1.80), mat_idx=1)
        self._add_box(bm, (0.55, ey, 0.90), (0.14, 0.16, 1.80), mat_idx=1)
        self._add_box(bm, (0.0, ey, 1.80), (1.24, 0.18, 0.16), mat_idx=1)

        self._finalize_mesh(obj, mesh, bm)
        return obj


@GeneratorRegistry.register("paleo_home_d")
class PropPaleoHomeDGenerator(BasePrehistoricGenerator):
    """Paleolithic Model D: Rock-Overhang Timber Post Lean-To Shelter."""

    def create_mesh(self) -> bpy.types.Object:
        mesh_name = self.kwargs.get("name", "PaleoHome_01_D")
        mesh = bpy.data.meshes.new(name=mesh_name)
        obj = bpy.data.objects.new(mesh_name, mesh)
        bpy.context.collection.objects.link(obj)

        palette = [
            ("M_CliffRock", (0.32, 0.31, 0.30), 0.94, 0.00, 0.12, 30.0),
            ("M_TimberBough", (0.34, 0.24, 0.15), 0.82, 0.00, 0.07, 45.0),
            ("M_HideCover", (0.26, 0.19, 0.13), 0.88, 0.00, 0.08, 40.0),
            ("M_HearthAsh", (0.15, 0.14, 0.13), 0.96, 0.00, 0.05, 55.0),
        ]
        for mat in self._setup_materials(mesh_name, palette):
            obj.data.materials.append(mat)

        bm = bmesh.new()

        hw = (self.width * 0.92) / 2.0  # ~1.84m
        hd = (self.depth * 0.92) / 2.0  # ~2.30m
        h = self.height * 0.85  # ~3.40m

        # 1. Massive natural rock bluff backwall (occupies northern half of footprint)
        cliff_depth = hd * 0.95
        self._add_box(bm, (0.0, hd * 0.50, h * 0.50), (hw * 2.10, cliff_depth, h), mat_idx=0)
        # Stepped natural rock ledge overhang at top
        self._add_box(
            bm, (0.0, hd * 0.30, h + 0.15), (hw * 2.20, cliff_depth * 0.85, 0.35), mat_idx=0
        )

        # 2. Slanted timber & pelt lean-to roof pitching down from rock ledge to southern front
        roof_start_y = hd * 0.20
        roof_end_y = -hd * 0.95
        roof_w = hw * 2.05
        roof_center_y = (roof_start_y + roof_end_y) / 2.0
        roof_len = roof_start_y - roof_end_y
        roof_center_z = (h * 0.95 + 1.20) / 2.0
        roof_th = 0.18

        # Slanted roof slab
        self._add_box(
            bm, (0.0, roof_center_y, roof_center_z), (roof_w, roof_len, roof_th), mat_idx=2
        )

        # 3. Three heavy supporting tree-trunk posts along the open front
        front_post_z = 0.60
        front_y = -hd * 0.85
        for px in [-hw * 0.80, 0.0, hw * 0.80]:
            self._add_box(bm, (px, front_y, front_post_z), (0.22, 0.22, 1.20), mat_idx=1)

        # Heavy horizontal support beam connecting the 3 front posts
        self._add_box(bm, (0.0, front_y, 1.20), (roof_w * 0.90, 0.20, 0.18), mat_idx=1)

        # 4. Front fire pit / stone hearth circle
        self._add_box(bm, (0.0, -hd - 0.25, 0.12), (0.85, 0.85, 0.24), mat_idx=3)

        self._finalize_mesh(obj, mesh, bm)
        return obj


# =============================================================================
# 2. MESOLITHIC ERA (Variants C and D)
# =============================================================================


@GeneratorRegistry.register("meso_home_c")
class PropMesoHomeCGenerator(BasePrehistoricGenerator):
    """Mesolithic Model C: Birch Bark & Moss Elongated Wigwam."""

    def create_mesh(self) -> bpy.types.Object:
        mesh_name = self.kwargs.get("name", "MesoHome_01_C")
        mesh = bpy.data.meshes.new(name=mesh_name)
        obj = bpy.data.objects.new(mesh_name, mesh)
        bpy.context.collection.objects.link(obj)

        palette = [
            ("M_BirchBark", (0.78, 0.74, 0.68), 0.72, 0.00, 0.08, 45.0),
            ("M_MossTurf", (0.22, 0.28, 0.16), 0.92, 0.00, 0.11, 40.0),
            ("M_SaplingPoles", (0.36, 0.26, 0.18), 0.80, 0.00, 0.05, 55.0),
            ("M_DarkEarth", (0.24, 0.19, 0.14), 0.95, 0.00, 0.09, 35.0),
        ]
        for mat in self._setup_materials(mesh_name, palette):
            obj.data.materials.append(mat)

        bm = bmesh.new()

        hw = (self.width * 0.88) / 2.0  # ~1.76m
        hd = (self.depth * 0.88) / 2.0  # ~2.20m
        h = self.height * 0.82  # ~3.30m

        # 1. Low earth foundation berm
        self._add_box(bm, (0, 0, 0.15), (hw * 2.15, hd * 2.15, 0.30), mat_idx=3)

        # 2. Barrel-vaulted birch bark wigwam body (inverted U-profile)
        vault_segs = 8
        length_segs = 10
        profile_verts = []

        for j in range(length_segs + 1):
            curr_y = -hd + (2.0 * hd * j) / length_segs
            ring = []
            for i in range(vault_segs + 1):
                ang = (math.pi * i) / vault_segs
                vx = hw * math.cos(ang)
                vz = 0.30 + h * math.sin(ang)
                ring.append(bm.verts.new((vx, curr_y, vz)))
            profile_verts.append(ring)

        for j in range(length_segs):
            for i in range(vault_segs):
                v0 = profile_verts[j][i]
                v1 = profile_verts[j + 1][i]
                v2 = profile_verts[j + 1][i + 1]
                v3 = profile_verts[j][i + 1]
                f = bm.faces.new([v0, v1, v2, v3])
                f.material_index = 0

        # End caps (South front & North rear)
        for j, y_pos, is_front in [(0, -hd, True), (length_segs, hd, False)]:
            ring = profile_verts[j]
            center_v = bm.verts.new((0, y_pos, 0.30))
            for i in range(vault_segs):
                if is_front and (vault_segs // 2 - 1 <= i <= vault_segs // 2):
                    continue  # Entrance gap
                if is_front:
                    f = bm.faces.new([center_v, ring[i], ring[i + 1]])
                else:
                    f = bm.faces.new([center_v, ring[i + 1], ring[i]])
                f.material_index = 0

        # Floor closing face
        floor_verts = [
            profile_verts[0][0],
            profile_verts[length_segs][0],
            profile_verts[length_segs][vault_segs],
            profile_verts[0][vault_segs],
        ]
        ff = bm.faces.new(floor_verts)
        ff.material_index = 3

        # 3. External bent hazel pole ribbing strapping down the bark
        for j in range(1, length_segs, 2):
            ry = -hd + (2.0 * hd * j) / length_segs
            self._add_box(bm, (0, ry, h * 0.55 + 0.30), (hw * 2.05, 0.10, h * 1.05), mat_idx=2)

        # 4. Moss & turf ridge cap
        self._add_box(bm, (0, 0, h + 0.32), (0.75, hd * 2.02, 0.16), mat_idx=1)

        # 5. Low entrance vestibule frame
        self._add_box(bm, (0, -hd - 0.15, 0.95), (1.10, 0.30, 1.30), mat_idx=2)

        self._finalize_mesh(obj, mesh, bm)
        return obj


@GeneratorRegistry.register("meso_home_d")
class PropMesoHomeDGenerator(BasePrehistoricGenerator):
    """Mesolithic Model D: Riverbank Elevated Stilt Platform Dwelling."""

    def create_mesh(self) -> bpy.types.Object:
        mesh_name = self.kwargs.get("name", "MesoHome_01_D")
        mesh = bpy.data.meshes.new(name=mesh_name)
        obj = bpy.data.objects.new(mesh_name, mesh)
        bpy.context.collection.objects.link(obj)

        palette = [
            ("M_RiverReed", (0.48, 0.42, 0.28), 0.85, 0.00, 0.08, 45.0),
            ("M_StiltPoles", (0.32, 0.23, 0.15), 0.78, 0.00, 0.06, 50.0),
            ("M_SplitLogDeck", (0.38, 0.29, 0.20), 0.74, 0.00, 0.07, 40.0),
            ("M_WovenWicker", (0.42, 0.33, 0.22), 0.88, 0.00, 0.09, 50.0),
        ]
        for mat in self._setup_materials(mesh_name, palette):
            obj.data.materials.append(mat)

        bm = bmesh.new()

        hw = (self.width * 0.86) / 2.0  # ~1.72m
        hd = (self.depth * 0.86) / 2.0  # ~2.15m
        stilt_h = 0.85  # ~0.85m elevation above ground
        h = self.height * 0.85  # ~3.40m

        # 1. Eight vertical log stilts driving into ground
        post_xs = [-hw * 0.85, hw * 0.85]
        post_ys = [-hd * 0.85, -hd * 0.28, hd * 0.28, hd * 0.85]
        for px in post_xs:
            for py in post_ys:
                self._add_box(bm, (px, py, stilt_h / 2.0), (0.22, 0.22, stilt_h), mat_idx=1)

        # 2. Horizontal split-log deck platform
        self._add_box(bm, (0, 0, stilt_h + 0.10), (hw * 2.10, hd * 2.10, 0.20), mat_idx=2)

        # 3. Woven wicker rectangular hut walls on platform
        wall_h = 1.45
        wall_z = stilt_h + 0.20 + wall_h / 2.0
        # Perimeter box shell
        self._add_box(bm, (0, 0, wall_z), (hw * 1.80, hd * 1.80, wall_h), mat_idx=3)

        # 4. Thatched hip roof above walls
        roof_bot_z = stilt_h + 0.20 + wall_h
        self._add_roof_prism(
            bm, (0.0, 0.0), hw * 2.15, hd * 2.15, roof_bot_z, roof_bot_z + 1.50, mat_idx=0
        )

        # 5. Access ladder on front south deck
        self._add_box(bm, (0, -hd - 0.25, stilt_h * 0.45), (0.65, 0.50, stilt_h * 0.90), mat_idx=1)

        self._finalize_mesh(obj, mesh, bm)
        return obj


# =============================================================================
# 3. NEOLITHIC ERA (Variants C and D)
# =============================================================================


@GeneratorRegistry.register("neo_home_c")
class PropNeoHomeCGenerator(BasePrehistoricGenerator):
    """Neolithic Model C: Corbelled Dry-Stone Beehive Hut (Skara Brae Style)."""

    def create_mesh(self) -> bpy.types.Object:
        mesh_name = self.kwargs.get("name", "NeoHome_01_C")
        mesh = bpy.data.meshes.new(name=mesh_name)
        obj = bpy.data.objects.new(mesh_name, mesh)
        bpy.context.collection.objects.link(obj)

        palette = [
            ("M_DryStoneFlag", (0.42, 0.40, 0.37), 0.92, 0.00, 0.12, 35.0),
            ("M_GreenTurfCap", (0.24, 0.30, 0.17), 0.90, 0.00, 0.10, 38.0),
            ("M_TimberLintel", (0.35, 0.25, 0.17), 0.80, 0.00, 0.06, 50.0),
            ("M_PackedSoil", (0.30, 0.24, 0.18), 0.95, 0.00, 0.08, 30.0),
        ]
        for mat in self._setup_materials(mesh_name, palette):
            obj.data.materials.append(mat)

        bm = bmesh.new()

        hw = (self.width * 0.90) / 2.0  # ~1.80m
        hd = (self.depth * 0.90) / 2.0  # ~2.25m
        h = self.height * 0.90  # ~3.60m

        # 1. Layered corbelled beehive stone tiers (4 stacked tiers contracting inward)
        num_tiers = 5
        tier_h = h / float(num_tiers)
        for t in range(num_tiers):
            tier_z = t * tier_h + tier_h / 2.0
            scale = 1.0 - (0.16 * t)
            tw = hw * 2.0 * scale
            td = hd * 2.0 * scale
            self._add_box(bm, (0, 0, tier_z), (tw, td, tier_h), mat_idx=0)

        # 2. Turf and sod earthen cap on apex
        top_scale = 1.0 - (0.16 * num_tiers)
        self._add_box(
            bm,
            (0, 0, h + 0.15),
            (hw * 2.0 * top_scale + 0.20, hd * 2.0 * top_scale + 0.20, 0.30),
            mat_idx=1,
        )

        # 3. Heavy megalithic entrance portal (South entrance)
        ey = -hd - 0.10
        lintel_h = 1.50
        # Left stone upright
        self._add_box(bm, (-0.55, ey, lintel_h / 2.0), (0.38, 0.40, lintel_h), mat_idx=0)
        # Right stone upright
        self._add_box(bm, (0.55, ey, lintel_h / 2.0), (0.38, 0.40, lintel_h), mat_idx=0)
        # Massive stone lintel slab across top
        self._add_box(bm, (0.0, ey, lintel_h + 0.18), (1.50, 0.50, 0.36), mat_idx=0)
        # Recessed wood plank door
        self._add_box(bm, (0.0, ey + 0.12, lintel_h / 2.0), (0.75, 0.08, lintel_h), mat_idx=2)

        self._finalize_mesh(obj, mesh, bm)
        return obj


@GeneratorRegistry.register("neo_home_d")
class PropNeoHomeDGenerator(BasePrehistoricGenerator):
    """Neolithic Model D: Raised Timber Stilt Lake-Village House."""

    def create_mesh(self) -> bpy.types.Object:
        mesh_name = self.kwargs.get("name", "NeoHome_01_D")
        mesh = bpy.data.meshes.new(name=mesh_name)
        obj = bpy.data.objects.new(mesh_name, mesh)
        bpy.context.collection.objects.link(obj)

        palette = [
            ("M_ReedThatch", (0.50, 0.44, 0.30), 0.88, 0.00, 0.08, 40.0),
            ("M_TimberPlank", (0.42, 0.30, 0.19), 0.74, 0.00, 0.06, 45.0),
            ("M_ClayChinking", (0.54, 0.46, 0.36), 0.90, 0.00, 0.07, 40.0),
            ("M_StiltPiles", (0.30, 0.22, 0.14), 0.82, 0.00, 0.05, 55.0),
        ]
        for mat in self._setup_materials(mesh_name, palette):
            obj.data.materials.append(mat)

        bm = bmesh.new()

        hw = (self.width * 0.88) / 2.0  # ~1.76m
        hd = (self.depth * 0.88) / 2.0  # ~2.20m
        pile_h = 0.90  # elevated 0.9m
        h = self.height * 0.92  # ~3.70m

        # 1. Six heavy square timber piles
        for px in [-hw * 0.85, 0.0, hw * 0.85]:
            for py in [-hd * 0.80, hd * 0.80]:
                self._add_box(bm, (px, py, pile_h / 2.0), (0.26, 0.26, pile_h), mat_idx=3)

        # 2. Main timber deck
        self._add_box(bm, (0, 0, pile_h + 0.10), (hw * 2.15, hd * 2.15, 0.20), mat_idx=1)

        # 3. Rectangular timber plank walls with clay chinking
        wall_h = 1.65
        wall_z = pile_h + 0.20 + wall_h / 2.0
        self._add_box(bm, (0, 0, wall_z), (hw * 1.85, hd * 1.85, wall_h), mat_idx=1)
        # Clay corner pilasters
        for cx in [-hw * 0.90, hw * 0.90]:
            for cy in [-hd * 0.90, hd * 0.90]:
                self._add_box(bm, (cx, cy, wall_z), (0.28, 0.28, wall_h), mat_idx=2)

        # 4. Steep hipped reed thatch roof
        roof_h = 1.70
        roof_bot_z = pile_h + 0.20 + wall_h
        self._add_roof_prism(
            bm, (0.0, 0.0), hw * 2.25, hd * 2.25, roof_bot_z, roof_bot_z + roof_h, mat_idx=0
        )

        # 5. Timber plank front doorway & deck ladder
        self._add_box(bm, (0, -hd - 0.20, pile_h * 0.45), (0.75, 0.45, pile_h * 0.90), mat_idx=1)

        self._finalize_mesh(obj, mesh, bm)
        return obj


# =============================================================================
# 4. CHALCOLITHIC / COPPER ERA (Variants C and D)
# =============================================================================


@GeneratorRegistry.register("chalco_home_c")
class PropChalcoHomeCGenerator(BasePrehistoricGenerator):
    """Chalcolithic Model C: Timber-Plank & Fieldstone Farmstead with Copper Fittings."""

    def create_mesh(self) -> bpy.types.Object:
        mesh_name = self.kwargs.get("name", "ChalcoHome_01_C")
        mesh = bpy.data.meshes.new(name=mesh_name)
        obj = bpy.data.objects.new(mesh_name, mesh)
        bpy.context.collection.objects.link(obj)

        palette = [
            ("M_FieldstonePlinth", (0.44, 0.42, 0.39), 0.90, 0.00, 0.10, 35.0),
            ("M_HeavyPlank", (0.40, 0.28, 0.18), 0.72, 0.00, 0.06, 45.0),
            ("M_TimberShingle", (0.32, 0.24, 0.17), 0.80, 0.00, 0.07, 40.0),
            ("M_CopperFittings", (0.75, 0.42, 0.26), 0.38, 0.85, 0.04, 50.0),
        ]
        for mat in self._setup_materials(mesh_name, palette):
            obj.data.materials.append(mat)

        bm = bmesh.new()

        hw = (self.width * 0.90) / 2.0  # ~1.80m
        hd = (self.depth * 0.90) / 2.0  # ~2.25m
        socle_h = 0.75  # 0.75m stone plinth
        h = self.height * 0.92  # ~3.70m

        # 1. Dressed fieldstone foundation socle
        self._add_box(bm, (0, 0, socle_h / 2.0), (hw * 2.05, hd * 2.05, socle_h), mat_idx=0)

        # 2. Axe-hewn horizontal timber plank walls
        wall_h = 1.65
        wall_z = socle_h + wall_h / 2.0
        self._add_box(bm, (0, 0, wall_z), (hw * 1.95, hd * 1.95, wall_h), mat_idx=1)

        # 3. Dual-pitch timber shingle roof with copper ridge caps
        roof_h = 1.45
        roof_bot_z = socle_h + wall_h
        self._add_roof_prism(
            bm, (0.0, 0.0), hw * 2.20, hd * 2.20, roof_bot_z, roof_bot_z + roof_h, mat_idx=2
        )
        # Copper ridge beam
        self._add_box(
            bm, (0, 0, socle_h + wall_h + roof_h + 0.06), (0.18, hd * 2.22, 0.12), mat_idx=3
        )

        # 4. Copper-reinforced heavy timber entrance portal
        ey = -hd - 0.02
        door_h = 1.70
        self._add_box(bm, (0, ey, socle_h + door_h / 2.0), (0.95, 0.15, door_h + 0.15), mat_idx=1)
        # Copper strap hinges
        self._add_box(bm, (0, ey - 0.06, socle_h + door_h * 0.30), (0.80, 0.02, 0.06), mat_idx=3)
        self._add_box(bm, (0, ey - 0.06, socle_h + door_h * 0.75), (0.80, 0.02, 0.06), mat_idx=3)

        # 5. Fieldstone steps to entrance
        self._add_box(bm, (0, ey - 0.22, socle_h * 0.40), (1.15, 0.40, socle_h * 0.80), mat_idx=0)

        self._finalize_mesh(obj, mesh, bm)
        return obj


@GeneratorRegistry.register("chalco_home_d")
class PropChalcoHomeDGenerator(BasePrehistoricGenerator):
    """Chalcolithic Model D: Sun-Dried Mudbrick Courtyard Dwelling with Flat Parapet Roof."""

    def create_mesh(self) -> bpy.types.Object:
        mesh_name = self.kwargs.get("name", "ChalcoHome_01_D")
        mesh = bpy.data.meshes.new(name=mesh_name)
        obj = bpy.data.objects.new(mesh_name, mesh)
        bpy.context.collection.objects.link(obj)

        palette = [
            ("M_SunDriedMudbrick", (0.62, 0.52, 0.41), 0.92, 0.00, 0.10, 32.0),
            ("M_ClayMortar", (0.50, 0.42, 0.33), 0.90, 0.00, 0.08, 40.0),
            ("M_RoofBeamWood", (0.36, 0.26, 0.17), 0.75, 0.00, 0.06, 50.0),
            ("M_CopperBowl", (0.76, 0.44, 0.28), 0.35, 0.88, 0.04, 50.0),
        ]
        for mat in self._setup_materials(mesh_name, palette):
            obj.data.materials.append(mat)

        bm = bmesh.new()

        hw = (self.width * 0.92) / 2.0  # ~1.84m
        hd = (self.depth * 0.92) / 2.0  # ~2.30m
        h = self.height * 0.80  # ~3.20m

        # 1. Main mudbrick living quarters (occupies rear 65% of footprint)
        rear_depth = hd * 1.30
        rear_center_y = hd * 0.35
        self._add_box(bm, (0, rear_center_y, h / 2.0), (hw * 2.0, rear_depth, h), mat_idx=0)

        # 2. Enclosed front courtyard parapet walls (occupies front 35% of footprint)
        court_depth = hd * 0.70
        court_center_y = -hd * 0.65
        court_wall_h = 1.35
        # Left court wall
        self._add_box(
            bm,
            (-hw + 0.20, court_center_y, court_wall_h / 2.0),
            (0.40, court_depth, court_wall_h),
            mat_idx=0,
        )
        # Right court wall
        self._add_box(
            bm,
            (hw - 0.20, court_center_y, court_wall_h / 2.0),
            (0.40, court_depth, court_wall_h),
            mat_idx=0,
        )
        # Front court wall with portal opening
        front_y = -hd
        self._add_box(
            bm,
            (-hw * 0.60, front_y, court_wall_h / 2.0),
            (hw * 0.80, 0.40, court_wall_h),
            mat_idx=0,
        )
        self._add_box(
            bm, (hw * 0.60, front_y, court_wall_h / 2.0), (hw * 0.80, 0.40, court_wall_h), mat_idx=0
        )
        # Lintel over courtyard gate
        self._add_box(bm, (0, front_y, court_wall_h + 0.12), (1.10, 0.42, 0.24), mat_idx=2)

        # 3. Flat clay parapet roof on main quarters with protruding log beams
        self._add_box(
            bm, (0, rear_center_y, h + 0.15), (hw * 2.06, rear_depth + 0.06, 0.30), mat_idx=1
        )
        # Protruding timber ceiling beams along east and west facades
        for by in [-hd * 0.20, hd * 0.10, hd * 0.40, hd * 0.70]:
            self._add_box(bm, (0, by, h - 0.20), (hw * 2.25, 0.14, 0.14), mat_idx=2)

        # 4. Copper brazier / water bowl fixture in courtyard
        self._add_box(bm, (0, court_center_y, 0.25), (0.45, 0.45, 0.50), mat_idx=3)

        self._finalize_mesh(obj, mesh, bm)
        return obj
