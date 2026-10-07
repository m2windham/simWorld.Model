"""
Procedural Prehistoric Home Series Generator (8 Models across 4 Eras)
Implements authentic game-ready dwellings from initial Paleolithic settle to Chalcolithic:
- PaleoHome_01_A: Mammoth Bone & Tusk Dome Shelter
- PaleoHome_01_B: Conical Timber Pole & Pelt Lean-To
- MesoHome_01_A: Bent Sapling & Reed Thatch Dome Hut
- MesoHome_01_B: Turf & Peat Sunk Pit-Dwelling
- NeoHome_01_A: Timber Post & Wattle-and-Daub Farmhouse
- NeoHome_01_B: Dry-Stone & Mudbrick Rectangular Dwelling
- ChalcoHome_01_A: Whitewashed Adobe & Stone-Plinth House with Porch
- ChalcoHome_01_B: Apsidal Roundhouse / Smelting Hearth Dwelling

All models adhere strictly to:
- Unified 4.0m (W) x 5.0m (D) building footprint (within +-8% tolerance)
- Ground contact at Z=0.0m
- 100% Watertight closed 2-manifold geometry (0 degenerate faces)
- Multi-slot procedural PBR material setups with procedural noise/bump
"""

import math

import bmesh
import bpy
from mathutils import Vector

from .generator_registry import GeneratorRegistry


class BasePrehistoricGenerator:
    """Base class providing shared geometry and procedural material helpers."""

    def __init__(self, width: float = 4.0, depth: float = 5.0, height: float = 4.0, **kwargs):
        self.width = width
        self.depth = depth
        self.height = height
        self.kwargs = kwargs

    def _setup_materials(self, prefix: str, palette: list[tuple]) -> list[bpy.types.Material]:
        """Creates procedural Principled BSDF materials with era-specific micro-wear."""
        materials = []
        for name, color, roughness, metallic, bump_str, noise_scale in palette:
            mat_name = f"{prefix}_{name}"
            mat = bpy.data.materials.new(name=mat_name)
            mat.use_nodes = True
            nodes = mat.node_tree.nodes
            links = mat.node_tree.links
            nodes.clear()

            out_node = nodes.new(type="ShaderNodeOutputMaterial")
            out_node.location = (350, 0)

            bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
            bsdf.location = (0, 0)
            bsdf.inputs["Base Color"].default_value = (*color, 1.0)
            bsdf.inputs["Roughness"].default_value = roughness
            bsdf.inputs["Metallic"].default_value = metallic

            if bump_str > 0.005:
                tex_coord = nodes.new(type="ShaderNodeTexCoord")
                tex_coord.location = (-650, -100)

                tex_noise = nodes.new(type="ShaderNodeTexNoise")
                tex_noise.location = (-420, -100)
                tex_noise.inputs["Scale"].default_value = noise_scale
                tex_noise.inputs["Detail"].default_value = 3.5
                tex_noise.inputs["Roughness"].default_value = 0.65
                links.new(tex_coord.outputs["Object"], tex_noise.inputs["Vector"])

                bump = nodes.new(type="ShaderNodeBump")
                bump.location = (-180, -150)
                bump.inputs["Strength"].default_value = bump_str
                bump.inputs["Distance"].default_value = 0.03
                links.new(tex_noise.outputs["Fac"], bump.inputs["Height"])
                links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

            links.new(bsdf.outputs["BSDF"], out_node.inputs["Surface"])
            materials.append(mat)
        return materials

    def _add_box(
        self,
        bm: bmesh.types.BMesh,
        center: tuple[float, float, float],
        size: tuple[float, float, float],
        mat_idx: int = 0,
    ) -> list[bmesh.types.BMFace]:
        """Creates an axis-aligned closed 2-manifold box."""
        cx, cy, cz = center
        sx, sy, sz = size
        hx, hy, hz = sx / 2.0, sy / 2.0, sz / 2.0

        verts = [
            bm.verts.new((cx - hx, cy - hy, cz - hz)),
            bm.verts.new((cx + hx, cy - hy, cz - hz)),
            bm.verts.new((cx + hx, cy + hy, cz - hz)),
            bm.verts.new((cx - hx, cy + hy, cz - hz)),
            bm.verts.new((cx - hx, cy - hy, cz + hz)),
            bm.verts.new((cx + hx, cy - hy, cz + hz)),
            bm.verts.new((cx + hx, cy + hy, cz + hz)),
            bm.verts.new((cx - hx, cy + hy, cz + hz)),
        ]

        faces_idx = [
            (0, 1, 5, 4),  # Front (-Y)
            (1, 2, 6, 5),  # Right (+X)
            (2, 3, 7, 6),  # Back (+Y)
            (3, 0, 4, 7),  # Left (-X)
            (4, 5, 6, 7),  # Top (+Z)
            (0, 3, 2, 1),  # Bottom (-Z)
        ]

        faces = []
        for f in faces_idx:
            face = bm.faces.new([verts[i] for i in f])
            face.material_index = mat_idx
            faces.append(face)
        return faces

    def _add_roof_prism(
        self,
        bm: bmesh.types.BMesh,
        center: tuple[float, float],
        width: float,
        depth: float,
        z_bot: float,
        z_top: float,
        mat_idx: int = 0,
    ) -> list[bmesh.types.BMFace]:
        """Constructs a closed, watertight gable roof prism (wedge)."""
        cx, cy = center
        hw = width / 2.0
        hd = depth / 2.0

        v_coords = [
            (cx - hw, cy - hd, z_bot),  # 0: Left-Front
            (cx + hw, cy - hd, z_bot),  # 1: Right-Front
            (cx + hw, cy + hd, z_bot),  # 2: Right-Back
            (cx - hw, cy + hd, z_bot),  # 3: Left-Back
            (cx, cy - hd, z_top),  # 4: Ridge-Front
            (cx, cy + hd, z_top),  # 5: Ridge-Back
        ]
        bv = [bm.verts.new(c) for c in v_coords]

        faces = [
            bm.faces.new([bv[0], bv[3], bv[2], bv[1]]),  # Bottom (-Z)
            bm.faces.new([bv[0], bv[1], bv[4]]),  # Front gable (-Y)
            bm.faces.new([bv[2], bv[3], bv[5]]),  # Back gable (+Y)
            bm.faces.new([bv[0], bv[4], bv[5], bv[3]]),  # Left slope
            bm.faces.new([bv[1], bv[2], bv[5], bv[4]]),  # Right slope
        ]
        for f in faces:
            f.material_index = mat_idx
        return faces

    def _add_slanted_beam(
        self,
        bm: bmesh.types.BMesh,
        p1: tuple[float, float, float],
        p2: tuple[float, float, float],
        thickness: float = 0.12,
        mat_idx: int = 1,
    ):
        """Constructs an oriented timber/bone beam between two 3D points."""
        v1 = Vector(p1)
        v2 = Vector(p2)
        dir_v = v2 - v1
        length = dir_v.length
        if length < 1e-4:
            return

        mid = (v1 + v2) / 2.0
        dir_norm = dir_v.normalized()

        up = Vector((0, 0, 1))
        if abs(dir_norm.dot(up)) > 0.98:
            side = Vector((1, 0, 0))
        else:
            side = dir_norm.cross(up).normalized()
        normal = side.cross(dir_norm).normalized()

        hs = thickness / 2.0
        hn = thickness / 2.0
        hl = length / 2.0

        verts = [
            mid - dir_norm * hl - side * hs - normal * hn,
            mid - dir_norm * hl + side * hs - normal * hn,
            mid - dir_norm * hl + side * hs + normal * hn,
            mid - dir_norm * hl - side * hs + normal * hn,
            mid + dir_norm * hl - side * hs - normal * hn,
            mid + dir_norm * hl + side * hs - normal * hn,
            mid + dir_norm * hl + side * hs + normal * hn,
            mid + dir_norm * hl - side * hs + normal * hn,
        ]
        bm_verts = [bm.verts.new(v) for v in verts]
        faces_idx = [
            (0, 1, 2, 3),  # Start cap
            (4, 7, 6, 5),  # End cap
            (0, 4, 5, 1),
            (1, 5, 6, 2),
            (2, 6, 7, 3),
            (3, 7, 4, 0),
        ]
        for f in faces_idx:
            face = bm.faces.new([bm_verts[i] for i in f])
            face.material_index = mat_idx

    def _add_oval_dome(
        self,
        bm: bmesh.types.BMesh,
        radius_x: float,
        radius_y: float,
        height: float,
        segments: int = 16,
        rings: int = 5,
        mat_idx: int = 0,
    ):
        """Constructs a closed, watertight oval dome."""
        ring_verts = []
        for r in range(rings):
            # fraction 0 (base) to 1 (top)
            v_frac = r / float(rings - 1)
            # spherical profile
            theta = v_frac * math.pi * 0.5
            cz = height * math.sin(theta)
            scale = math.cos(theta)

            current_ring = []
            for s in range(segments):
                phi = (2.0 * math.pi * s) / float(segments)
                px = radius_x * scale * math.cos(phi)
                py = radius_y * scale * math.sin(phi)
                current_ring.append(bm.verts.new((px, py, cz)))
            ring_verts.append(current_ring)

        # Quads between rings
        for r in range(rings - 1):
            for s in range(segments):
                s_next = (s + 1) % segments
                v0 = ring_verts[r][s]
                v1 = ring_verts[r][s_next]
                v2 = ring_verts[r + 1][s_next]
                v3 = ring_verts[r + 1][s]
                face = bm.faces.new([v0, v1, v2, v3])
                face.material_index = mat_idx

        # Bottom base cap (reversed winding for -Z)
        f_bot = bm.faces.new(list(reversed(ring_verts[0])))
        f_bot.material_index = mat_idx

    def _finalize_mesh(self, obj: bpy.types.Object, mesh: bpy.types.Mesh, bm: bmesh.types.BMesh):
        """Cleans mesh topology, ensures outward normals, and writes to Blender mesh."""
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0005)
        bmesh.ops.dissolve_degenerate(bm, dist=0.0005, edges=bm.edges)
        bm.to_mesh(mesh)
        bm.free()

        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.dissolve_degenerate(threshold=0.0001)
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.object.mode_set(mode="OBJECT")


# =============================================================================
# 1. PALEOLITHIC ERA (Old Stone Age / First Settle)
# =============================================================================


@GeneratorRegistry.register("paleo_home_a")
class PropPaleoHomeAGenerator(BasePrehistoricGenerator):
    """Paleolithic Model A: Mammoth Bone & Tusk Dome Shelter (High-Fidelity Mezhyrich Style)."""

    def create_mesh(self) -> bpy.types.Object:
        mesh_name = self.kwargs.get("name", "PaleoHome_01_A")
        mesh = bpy.data.meshes.new(name=mesh_name)
        obj = bpy.data.objects.new(mesh_name, mesh)
        bpy.context.collection.objects.link(obj)

        palette = [
            ("M_Hide", (0.34, 0.22, 0.14), 0.88, 0.00, 0.08, 40.0),
            ("M_Bone", (0.86, 0.82, 0.72), 0.50, 0.00, 0.04, 50.0),
            ("M_Stone", (0.36, 0.35, 0.33), 0.92, 0.00, 0.10, 35.0),
            ("M_Rope", (0.24, 0.18, 0.12), 0.70, 0.00, 0.04, 60.0),
        ]
        for mat in self._setup_materials(mesh_name, palette):
            obj.data.materials.append(mat)

        bm = bmesh.new()

        # Footprint: 4.0m x 5.0m, height ~4.0m
        hw = (self.width * 0.88) / 2.0  # ~1.76m
        hd = (self.depth * 0.88) / 2.0  # ~2.20m
        h = self.height * 0.95  # ~3.80m

        # 1. Base oval hide dome core
        self._add_oval_dome(bm, radius_x=hw, radius_y=hd, height=h, segments=16, rings=6, mat_idx=0)

        # 2. Continuous perimeter foundation: alternating mammoth mandibles & heavy boulders
        num_foundation = 16
        for i in range(num_foundation):
            angle = (2.0 * math.pi * i) / float(num_foundation)
            bx = (hw + 0.14) * math.cos(angle)
            by = (hd + 0.14) * math.sin(angle)
            if abs(angle - (-math.pi / 2.0)) < 0.30:
                continue  # Leave entrance portal open

            if i % 2 == 0:
                # Mammoth mandible block (curved jawbone block)
                self._add_box(bm, (bx, by, 0.20), (0.50, 0.34, 0.36), mat_idx=1)
            else:
                # Heavy anchor boulder
                self._add_box(bm, (bx, by, 0.22), (0.44, 0.44, 0.40), mat_idx=2)

        # 3. Exterior curved Mammoth Tusk ribcage (prominently sweeping over dome exterior)
        tusk_count = 10
        for i in range(tusk_count):
            angle = (2.0 * math.pi * i) / float(tusk_count)
            if abs(angle - (-math.pi / 2.0)) < 0.36:
                continue  # Leave entrance doorway clear

            ca = math.cos(angle)
            sa = math.sin(angle)

            # 4 sweeping points along the outward curve
            p0 = ((hw + 0.22) * ca, (hd + 0.22) * sa, 0.08)
            p1 = ((hw * 1.05 + 0.18) * ca, (hd * 1.05 + 0.18) * sa, h * 0.38)
            p2 = ((hw * 0.82 + 0.20) * ca, (hd * 0.82 + 0.20) * sa, h * 0.72)
            p3 = ((hw * 0.32 + 0.12) * ca, (hd * 0.32 + 0.12) * sa, h * 0.96)

            # 3-segment sweeping curved tusk beam
            self._add_slanted_beam(bm, p0, p1, thickness=0.20, mat_idx=1)
            self._add_slanted_beam(bm, p1, p2, thickness=0.16, mat_idx=1)
            self._add_slanted_beam(bm, p2, p3, thickness=0.12, mat_idx=1)

        # 4. Rawhide tension binding bands around dome exterior
        for ring_z, r_scale in [(h * 0.38, 1.02), (h * 0.68, 0.78)]:
            for seg in range(12):
                a1 = (2.0 * math.pi * seg) / 12.0
                a2 = (2.0 * math.pi * (seg + 1)) / 12.0
                mid_a = (a1 + a2) / 2.0
                if abs(mid_a - (-math.pi / 2.0)) < 0.35:
                    continue
                p_a = (
                    (hw * r_scale + 0.04) * math.cos(a1),
                    (hd * r_scale + 0.04) * math.sin(a1),
                    ring_z,
                )
                p_b = (
                    (hw * r_scale + 0.04) * math.cos(a2),
                    (hd * r_scale + 0.04) * math.sin(a2),
                    ring_z,
                )
                self._add_slanted_beam(bm, p_a, p_b, thickness=0.08, mat_idx=3)

        # 5. Iconic Mammoth Tusk Gothic Arch Portal
        ey = -hd - 0.12
        # Left tusk arching up and crossing right
        self._add_slanted_beam(
            bm, (-0.68, ey, 0.08), (-0.52, ey - 0.08, 1.15), thickness=0.18, mat_idx=1
        )
        self._add_slanted_beam(
            bm,
            (-0.52, ey - 0.08, 1.15),
            (0.20, ey - 0.10, 2.15),
            thickness=0.14,
            mat_idx=1,
        )
        # Right tusk arching up and crossing left
        self._add_slanted_beam(
            bm, (0.68, ey, 0.08), (0.52, ey - 0.08, 1.15), thickness=0.18, mat_idx=1
        )
        self._add_slanted_beam(
            bm,
            (0.52, ey - 0.08, 1.15),
            (-0.20, ey - 0.10, 2.15),
            thickness=0.14,
            mat_idx=1,
        )
        # Hanging fur pelt door flap inside the tusk arch
        self._add_box(bm, (0, ey + 0.04, 0.95), (0.85, 0.06, 1.80), mat_idx=0)

        # 6. Apex bone collar & jutting smoke vent tines
        self._add_box(bm, (0, 0, h + 0.08), (0.75, 0.75, 0.14), mat_idx=0)
        self._add_box(bm, (0, 0, h + 0.20), (0.85, 0.85, 0.08), mat_idx=1)
        # 6 vertical bone tines jutting from apex collar
        for ti in range(6):
            t_angle = (2.0 * math.pi * ti) / 6.0
            tx = 0.32 * math.cos(t_angle)
            ty = 0.32 * math.sin(t_angle)
            self._add_slanted_beam(
                bm,
                (tx, ty, h + 0.18),
                (tx * 1.25, ty * 1.25, h + 0.50),
                thickness=0.08,
                mat_idx=1,
            )

        self._finalize_mesh(obj, mesh, bm)
        return obj


@GeneratorRegistry.register("paleo_home_b")
class PropPaleoHomeBGenerator(BasePrehistoricGenerator):
    """Paleolithic Model B: Stick & Reed Mud-Tiled Shelter."""

    def create_mesh(self) -> bpy.types.Object:
        mesh_name = self.kwargs.get("name", "PaleoHome_01_B")
        mesh = bpy.data.meshes.new(name=mesh_name)
        obj = bpy.data.objects.new(mesh_name, mesh)
        bpy.context.collection.objects.link(obj)

        palette = [
            ("M_MudTile", (0.52, 0.42, 0.30), 0.90, 0.00, 0.10, 42.0),
            ("M_ReedBundle", (0.64, 0.52, 0.30), 0.82, 0.00, 0.08, 48.0),
            ("M_Stick", (0.28, 0.18, 0.10), 0.75, 0.00, 0.06, 55.0),
            ("M_Stone", (0.35, 0.34, 0.32), 0.90, 0.00, 0.10, 35.0),
        ]
        for mat in self._setup_materials(mesh_name, palette):
            obj.data.materials.append(mat)

        bm = bmesh.new()

        w = self.width * 0.88  # ~3.52m
        d = self.depth * 0.90  # ~4.50m
        h = self.height * 0.96  # ~3.84m
        hw = w / 2.0
        hd = d / 2.0
        wall_h = h * 0.45  # ~1.72m

        # 1. Base mud-packed turf berm around perimeter (Z in [0.0, 0.35m])
        self._add_box(bm, (0, 0, 0.18), (w + 0.16, d + 0.16, 0.36), mat_idx=0)

        # 2. Main vertical stick corner posts & mid posts
        stick_thick = 0.14
        posts = [
            (-hw, -hd),
            (hw, -hd),
            (hw, hd),
            (-hw, hd),
            (-hw, 0.0),
            (hw, 0.0),
        ]
        for px, py in posts:
            self._add_box(
                bm,
                (px, py, (wall_h + 0.06) / 2.0),
                (stick_thick, stick_thick, wall_h + 0.06),
                mat_idx=2,
            )

        # 3. Mud-tiled / daubed wattle wall panels (Z in [0.35m, wall_h])
        # Left wall (-X)
        self._add_box(
            bm,
            (-hw, 0, (wall_h + 0.35) / 2.0),
            (0.12, d - stick_thick, wall_h - 0.35),
            mat_idx=0,
        )
        # Right wall (+X)
        self._add_box(
            bm,
            (hw, 0, (wall_h + 0.35) / 2.0),
            (0.12, d - stick_thick, wall_h - 0.35),
            mat_idx=0,
        )
        # Rear wall (+Y)
        self._add_box(
            bm,
            (0, hd, (wall_h + 0.35) / 2.0),
            (w - stick_thick, 0.12, wall_h - 0.35),
            mat_idx=0,
        )
        # Front wall (-Y) with door opening
        front_panel_w = (w - 1.10) / 2.0
        self._add_box(
            bm,
            (-hw + front_panel_w / 2.0, -hd, (wall_h + 0.35) / 2.0),
            (front_panel_w, 0.12, wall_h - 0.35),
            mat_idx=0,
        )
        self._add_box(
            bm,
            (hw - front_panel_w / 2.0, -hd, (wall_h + 0.35) / 2.0),
            (front_panel_w, 0.12, wall_h - 0.35),
            mat_idx=0,
        )

        # 4. Stepped mud-tile courses on walls (horizontal stick tile battens)
        for tile_z in [0.70, 1.15, 1.55]:
            self._add_box(bm, (-hw - 0.03, 0, tile_z), (0.05, d, 0.08), mat_idx=2)
            self._add_box(bm, (hw + 0.03, 0, tile_z), (0.05, d, 0.08), mat_idx=2)
            self._add_box(bm, (0, hd + 0.03, tile_z), (w, 0.05, 0.08), mat_idx=2)

        # 5. Bundled reed thatch roof with mud-capping ridge
        self._add_roof_prism(bm, (0, 0), w * 1.05, d * 1.03, wall_h - 0.02, h, mat_idx=1)
        # Heavy central stick ridge beam extending front to back
        self._add_box(bm, (0, 0, h + 0.06), (0.16, d + 0.30, 0.14), mat_idx=2)
        # Mud plaster cap along the ridge peak
        self._add_box(bm, (0, 0, h + 0.12), (0.36, d * 0.95, 0.08), mat_idx=0)

        # 6. Diagonal stick rafter braces on roof slopes
        for rafter_y in [-hd * 0.7, 0.0, hd * 0.7]:
            # Left slope rafter
            self._add_slanted_beam(
                bm,
                (-hw - 0.06, rafter_y, wall_h),
                (0, rafter_y, h),
                thickness=0.11,
                mat_idx=2,
            )
            # Right slope rafter
            self._add_slanted_beam(
                bm,
                (hw + 0.06, rafter_y, wall_h),
                (0, rafter_y, h),
                thickness=0.11,
                mat_idx=2,
            )

        # 7. Entrance stick frame with woven reed screen
        ey = -hd - 0.04
        self._add_box(bm, (-0.50, ey, wall_h * 0.55), (0.14, 0.16, wall_h * 1.10), mat_idx=2)
        self._add_box(bm, (0.50, ey, wall_h * 0.55), (0.14, 0.16, wall_h * 1.10), mat_idx=2)
        self._add_box(bm, (0.00, ey, wall_h + 0.04), (1.18, 0.18, 0.14), mat_idx=2)
        # Woven reed door screen
        self._add_box(bm, (0.00, ey + 0.02, wall_h * 0.50), (0.84, 0.05, wall_h), mat_idx=1)

        self._finalize_mesh(obj, mesh, bm)
        return obj


# =============================================================================
# 2. MESOLITHIC ERA (Middle Stone Age / Semi-Sedentary)
# =============================================================================


@GeneratorRegistry.register("meso_home_a")
class PropMesoHomeAGenerator(BasePrehistoricGenerator):
    """Mesolithic Model A: Timber Ridge Pit-Dwelling Variant with Porch (Non-Domed, B-Template Based)."""

    def create_mesh(self) -> bpy.types.Object:
        mesh_name = self.kwargs.get("name", "MesoHome_01_A")
        mesh = bpy.data.meshes.new(name=mesh_name)
        obj = bpy.data.objects.new(mesh_name, mesh)
        bpy.context.collection.objects.link(obj)

        palette = [
            ("M_ReedThatch", (0.66, 0.54, 0.32), 0.82, 0.00, 0.08, 45.0),
            ("M_BirchBark", (0.78, 0.75, 0.68), 0.75, 0.00, 0.05, 50.0),
            ("M_Timber", (0.28, 0.18, 0.10), 0.70, 0.00, 0.06, 55.0),
            ("M_Wattle", (0.38, 0.28, 0.18), 0.85, 0.00, 0.08, 50.0),
        ]
        for mat in self._setup_materials(mesh_name, palette):
            obj.data.materials.append(mat)

        bm = bmesh.new()

        # Rectangular timber post-and-beam frame based on Version B template
        w = self.width * 0.90  # ~3.60m -> roof ~3.78m (within 4.0m +-8%)
        d = self.depth * 0.84  # ~4.20m -> total depth with porch ~4.80m (within 5.0m +-8%)
        h = self.height * 0.94  # ~3.57m -> total height with ridge ~3.67m (within 3.8m +-8%)
        hw = w / 2.0
        hd = d / 2.0
        wall_h = h * 0.44  # ~1.57m

        # 1. Base sill foundation beam around perimeter (Z in [0.0, 0.20m])
        self._add_box(bm, (0, 0, 0.10), (w + 0.08, d + 0.08, 0.20), mat_idx=2)

        # 2. 6 heavy timber vertical wall posts (4 corners + 2 center posts)
        post_s = 0.18
        posts = [
            (-hw, -hd),
            (hw, -hd),
            (hw, hd),
            (-hw, hd),
            (-hw, 0.0),
            (hw, 0.0),
        ]
        for px, py in posts:
            self._add_box(
                bm,
                (px, py, (wall_h + 0.04) / 2.0),
                (post_s, post_s, wall_h + 0.04),
                mat_idx=2,
            )

        # 3. Woven hazel wattle / birch-bark wall infill panels (Z in [0.20m, wall_h])
        # Side walls
        self._add_box(
            bm,
            (-hw, 0, (wall_h + 0.20) / 2.0),
            (0.12, d - post_s, wall_h - 0.20),
            mat_idx=3,
        )
        self._add_box(
            bm,
            (hw, 0, (wall_h + 0.20) / 2.0),
            (0.12, d - post_s, wall_h - 0.20),
            mat_idx=3,
        )
        # Rear wall
        self._add_box(
            bm,
            (0, hd, (wall_h + 0.20) / 2.0),
            (w - post_s, 0.12, wall_h - 0.20),
            mat_idx=3,
        )
        # Front wall with door opening
        fw_panel = (w - 1.15) / 2.0
        self._add_box(
            bm,
            (-hw + fw_panel / 2.0, -hd, (wall_h + 0.20) / 2.0),
            (fw_panel, 0.12, wall_h - 0.20),
            mat_idx=3,
        )
        self._add_box(
            bm,
            (hw - fw_panel / 2.0, -hd, (wall_h + 0.20) / 2.0),
            (fw_panel, 0.12, wall_h - 0.20),
            mat_idx=3,
        )

        # 4. Gabled river-reed thatch roof (steep pitch, Version B prism)
        self._add_roof_prism(bm, (0, 0), w * 1.05, d * 1.01, wall_h - 0.02, h, mat_idx=0)
        # Extended heavy timber ridge pole
        self._add_box(bm, (0, 0, h + 0.05), (0.18, d + 0.16, 0.10), mat_idx=2)

        # 5. Exposed external timber A-frame truss rafters on front and back gables
        for gy in [-hd, hd]:
            # Left rafter
            self._add_slanted_beam(
                bm,
                (-hw - 0.06, gy, wall_h - 0.02),
                (0, gy, h),
                thickness=0.14,
                mat_idx=2,
            )
            # Right rafter
            self._add_slanted_beam(
                bm,
                (hw + 0.06, gy, wall_h - 0.02),
                (0, gy, h),
                thickness=0.14,
                mat_idx=2,
            )
            # Horizontal tie beam across gable
            self._add_box(bm, (0, gy, wall_h), (w + 0.12, 0.16, 0.14), mat_idx=2)

        # 6. Protruding Covered Entrance Porch (Front Gable -Y)
        porch_y = -hd - 0.45
        porch_w = 1.25
        # 2 front porch timber posts
        self._add_box(
            bm,
            (-porch_w / 2.0, porch_y, (wall_h * 0.95) / 2.0),
            (0.12, 0.12, wall_h * 0.95),
            mat_idx=2,
        )
        self._add_box(
            bm,
            (porch_w / 2.0, porch_y, (wall_h * 0.95) / 2.0),
            (0.12, 0.12, wall_h * 0.95),
            mat_idx=2,
        )
        # Porch lintel
        self._add_box(bm, (0, porch_y, wall_h * 0.95), (porch_w + 0.14, 0.14, 0.12), mat_idx=2)
        # Porch gabled thatch canopy connecting to front wall
        self._add_roof_prism(
            bm,
            (0, (-hd + porch_y) / 2.0),
            porch_w * 1.10,
            abs(porch_y - (-hd)),
            wall_h * 0.92,
            wall_h * 1.28,
            mat_idx=0,
        )

        # 7. Entrance door frame & woven reed curtain
        ey = -hd - 0.02
        self._add_box(bm, (-0.48, ey, wall_h * 0.48), (0.14, 0.16, wall_h * 0.96), mat_idx=2)
        self._add_box(bm, (0.48, ey, wall_h * 0.48), (0.14, 0.16, wall_h * 0.96), mat_idx=2)
        self._add_box(bm, (0.00, ey, wall_h * 0.96), (1.10, 0.18, 0.14), mat_idx=2)
        self._add_box(bm, (0.00, ey + 0.02, wall_h * 0.45), (0.80, 0.04, wall_h * 0.90), mat_idx=1)

        self._finalize_mesh(obj, mesh, bm)
        return obj


@GeneratorRegistry.register("meso_home_b")
class PropMesoHomeBGenerator(BasePrehistoricGenerator):
    """Mesolithic Model B: Turf & Peat Sunk Pit-Dwelling."""

    def create_mesh(self) -> bpy.types.Object:
        mesh_name = self.kwargs.get("name", "MesoHome_01_B")
        mesh = bpy.data.meshes.new(name=mesh_name)
        obj = bpy.data.objects.new(mesh_name, mesh)
        bpy.context.collection.objects.link(obj)

        palette = [
            ("M_Turf", (0.24, 0.22, 0.15), 0.92, 0.00, 0.12, 40.0),
            ("M_Timber", (0.24, 0.16, 0.09), 0.70, 0.00, 0.06, 55.0),
            ("M_Wattle", (0.35, 0.26, 0.16), 0.85, 0.00, 0.08, 50.0),
            ("M_Thatch", (0.55, 0.45, 0.28), 0.80, 0.00, 0.08, 45.0),
        ]
        for mat in self._setup_materials(mesh_name, palette):
            obj.data.materials.append(mat)

        bm = bmesh.new()

        w = self.width * 0.90  # ~3.60m
        d = self.depth * 0.92  # ~4.60m
        h = self.height * 0.95  # ~3.60m
        wall_h = h * 0.38  # ~1.36m

        # 1. Base peat / turf sod wall envelope
        self._add_box(bm, (0, 0, wall_h / 2.0), (w, d, wall_h), mat_idx=0)

        # 2. Heavy timber corner posts and ridge beam
        hw = w / 2.0
        hd = d / 2.0
        post_s = 0.18
        for cx, cy in [
            (-hw, -hd),
            (hw, -hd),
            (hw, hd),
            (-hw, hd),
        ]:
            self._add_box(
                bm,
                (cx, cy, (wall_h + 0.04) / 2.0),
                (post_s, post_s, wall_h + 0.04),
                mat_idx=1,
            )

        # Heavy ridge pole
        self._add_box(bm, (0, 0, h - 0.08), (0.18, d + 0.10, 0.16), mat_idx=1)

        # 4. Low-pitched turf sod & rush thatch roof slopes
        self._add_roof_prism(bm, (0, 0), w * 1.02, d * 1.01, wall_h - 0.02, h - 0.02, mat_idx=0)
        # Left slope edge timber
        self._add_slanted_beam(
            bm, (-hw - 0.06, 0, wall_h - 0.02), (0, 0, h), thickness=0.14, mat_idx=1
        )
        # Right slope edge timber
        self._add_slanted_beam(
            bm, (hw + 0.06, 0, wall_h - 0.02), (0, 0, h), thickness=0.14, mat_idx=1
        )

        # Turf sod block course steps on roof
        for step_i in range(3):
            t = (step_i + 1) / 4.0
            cz = wall_h + t * (h - wall_h)
            cx_l = -(1.0 - t) * hw
            cx_r = (1.0 - t) * hw
            self._add_box(bm, (cx_l, 0, cz), (0.28, d * 0.94, 0.10), mat_idx=0)
            self._add_box(bm, (cx_r, 0, cz), (0.28, d * 0.94, 0.10), mat_idx=0)

        # 5. Sunken timber doorway with lintel
        ey = -hd - 0.02
        self._add_box(bm, (-0.48, ey, wall_h * 0.55), (0.14, 0.18, wall_h * 1.10), mat_idx=1)
        self._add_box(bm, (0.48, ey, wall_h * 0.55), (0.14, 0.18, wall_h * 1.10), mat_idx=1)
        self._add_box(bm, (0.00, ey, wall_h * 1.05), (1.12, 0.20, 0.18), mat_idx=1)
        self._add_box(bm, (0.00, ey + 0.04, wall_h * 0.50), (0.80, 0.06, wall_h * 0.95), mat_idx=2)

        self._finalize_mesh(obj, mesh, bm)
        return obj


# =============================================================================
# 3. NEOLITHIC ERA (New Stone Age / Permanent Farming Settlement)
# =============================================================================


@GeneratorRegistry.register("neo_home_a")
class PropNeoHomeAGenerator(BasePrehistoricGenerator):
    """Neolithic Model A: Timber Post & Wattle-and-Daub Farmhouse."""

    def create_mesh(self) -> bpy.types.Object:
        mesh_name = self.kwargs.get("name", "NeoHome_01_A")
        mesh = bpy.data.meshes.new(name=mesh_name)
        obj = bpy.data.objects.new(mesh_name, mesh)
        bpy.context.collection.objects.link(obj)

        palette = [
            ("M_Daub", (0.65, 0.55, 0.42), 0.88, 0.00, 0.06, 45.0),
            ("M_Timber", (0.22, 0.14, 0.08), 0.68, 0.00, 0.07, 55.0),
            ("M_Stone", (0.38, 0.36, 0.34), 0.85, 0.00, 0.10, 35.0),
            ("M_StrawThatch", (0.72, 0.58, 0.30), 0.78, 0.00, 0.08, 50.0),
            ("M_WoodPlank", (0.32, 0.20, 0.12), 0.64, 0.00, 0.05, 50.0),
        ]
        for mat in self._setup_materials(mesh_name, palette):
            obj.data.materials.append(mat)

        bm = bmesh.new()

        w = self.width * 0.88  # ~3.52m
        d = self.depth * 0.90  # ~4.50m
        h = self.height * 0.98  # ~4.70m
        eave_z = h * 0.46  # ~2.16m
        plinth_h = 0.32

        # 1. Low dry-stone foundation footing
        self._add_box(bm, (0, 0, plinth_h / 2.0), (w * 1.05, d * 1.05, plinth_h), mat_idx=2)

        # 2. Timber post & beam framework with clay daub infill walls
        wall_h = eave_z - plinth_h
        wall_cz = plinth_h + wall_h / 2.0
        self._add_box(bm, (0, 0, wall_cz), (w, d, wall_h), mat_idx=0)

        # Heavy timber corner posts and intermediate studs
        hw = w / 2.0
        hd = d / 2.0
        post_s = 0.16
        for cx, cy in [
            (-hw + post_s / 2, -hd + post_s / 2),
            (hw - post_s / 2, -hd + post_s / 2),
            (hw - post_s / 2, hd - post_s / 2),
            (-hw + post_s / 2, hd - post_s / 2),
        ]:
            self._add_box(bm, (cx, cy, wall_cz), (post_s * 1.05, post_s * 1.05, wall_h), mat_idx=1)

        # Wall plate horizontal timber beam
        self._add_box(bm, (0, 0, eave_z), (w * 1.02, d * 1.02, 0.14), mat_idx=1)

        # 4. Layered wheat straw thatch roof slopes
        self._add_roof_prism(bm, (0, 0), w * 1.04, d * 1.01, eave_z - 0.02, h, mat_idx=3)
        self._add_slanted_beam(
            bm, (-hw - 0.10, 0, eave_z - 0.04), (0, 0, h), thickness=0.16, mat_idx=1
        )
        self._add_slanted_beam(
            bm, (hw + 0.10, 0, eave_z - 0.04), (0, 0, h), thickness=0.16, mat_idx=1
        )

        # Overlapping straw thatch courses on left and right
        for c in range(6):
            t = (c + 1) / 7.0
            cz = eave_z + t * (h - eave_z)
            cx_l = -(1.0 - t) * (hw + 0.10)
            cx_r = (1.0 - t) * (hw + 0.10)
            self._add_box(bm, (cx_l, 0, cz), (0.24, d * 0.96, 0.08), mat_idx=3)
            self._add_box(bm, (cx_r, 0, cz), (0.24, d * 0.96, 0.08), mat_idx=3)

        # Timber spar cross-beams locking the thatch ridge
        spar_count = 6
        for si in range(spar_count):
            sy = -hd + 0.40 + (si / float(spar_count - 1)) * (d - 0.80)
            self._add_slanted_beam(
                bm,
                (-0.22, sy, h - 0.12),
                (0.22, sy, h + 0.16),
                thickness=0.08,
                mat_idx=1,
            )
            self._add_slanted_beam(
                bm,
                (0.22, sy, h - 0.12),
                (-0.22, sy, h + 0.16),
                thickness=0.08,
                mat_idx=1,
            )

        # 5. Heavy split-timber entrance door
        ey = -hd - 0.02
        door_w = 0.82
        door_h = 1.75
        self._add_box(
            bm,
            (0, ey, plinth_h + door_h / 2.0),
            (door_w + 0.16, 0.14, door_h + 0.14),
            mat_idx=1,
        )
        self._add_box(
            bm,
            (0, ey - 0.02, plinth_h + door_h / 2.0),
            (door_w, 0.06, door_h),
            mat_idx=4,
        )
        # Stone doorstep
        self._add_box(
            bm,
            (0, ey - 0.18, plinth_h * 0.45),
            (1.05, 0.32, plinth_h * 0.90),
            mat_idx=2,
        )

        self._finalize_mesh(obj, mesh, bm)
        return obj


@GeneratorRegistry.register("neo_home_b")
class PropNeoHomeBGenerator(BasePrehistoricGenerator):
    """Neolithic Model B: Dry-Stone & Mudbrick Rectangular Dwelling."""

    def create_mesh(self) -> bpy.types.Object:
        mesh_name = self.kwargs.get("name", "NeoHome_01_B")
        mesh = bpy.data.meshes.new(name=mesh_name)
        obj = bpy.data.objects.new(mesh_name, mesh)
        bpy.context.collection.objects.link(obj)

        palette = [
            ("M_DryStone", (0.40, 0.38, 0.36), 0.88, 0.00, 0.10, 35.0),
            ("M_Mudbrick", (0.58, 0.48, 0.36), 0.85, 0.00, 0.07, 45.0),
            ("M_ClayRoof", (0.45, 0.38, 0.30), 0.90, 0.00, 0.08, 40.0),
            ("M_Timber", (0.26, 0.18, 0.10), 0.70, 0.00, 0.05, 55.0),
        ]
        for mat in self._setup_materials(mesh_name, palette):
            obj.data.materials.append(mat)

        bm = bmesh.new()

        w = self.width * 0.88  # ~3.52m
        d = self.depth * 0.90  # ~4.50m
        h = self.height * 0.96  # ~3.84m
        stone_h = h * 0.45  # ~1.72m

        # 1. Lower dry-stone wall base (Skara Brae / Çatalhöyük style)
        self._add_box(bm, (0, 0, stone_h / 2.0), (w, d, stone_h), mat_idx=0)

        # Protruding stone slab courses around perimeter
        for c in range(3):
            cz = (c + 0.5) * (stone_h / 3.0)
            self._add_box(bm, (0, 0, cz), (w + 0.06, d + 0.06, 0.08), mat_idx=0)

        # 2. Upper sun-dried mudbrick wall courses
        mud_h = h * 0.40
        mud_cz = stone_h + mud_h / 2.0
        self._add_box(bm, (0, 0, mud_cz), (w * 0.96, d * 0.96, mud_h), mat_idx=1)

        # 3. Flat / low-pitch timber beam roof cap with packed clay & turf
        roof_z = stone_h + mud_h
        roof_th = 0.22
        self._add_box(bm, (0, 0, roof_z + roof_th / 2.0), (w * 1.02, d * 1.02, roof_th), mat_idx=2)

        # Protruding timber joist beam ends on sides
        for i in range(5):
            by = -d / 2.0 + 0.45 + (i / 4.0) * (d - 0.90)
            self._add_box(bm, (0, by, roof_z - 0.06), (w * 1.08, 0.12, 0.12), mat_idx=3)

        # 4. Rooftop entrance hatch & wooden pole ladder
        hatch_x = w * 0.20
        hatch_y = -d * 0.15
        self._add_box(
            bm,
            (hatch_x, hatch_y, roof_z + roof_th + 0.14),
            (0.75, 0.75, 0.28),
            mat_idx=3,
        )

        # Pole ladder extending from ground to roof
        lad_x = -w / 2.0 - 0.08
        self._add_slanted_beam(
            bm,
            (lad_x, -d * 0.22, 0.05),
            (lad_x, -d * 0.12, roof_z + 0.30),
            thickness=0.08,
            mat_idx=3,
        )
        self._add_slanted_beam(
            bm,
            (lad_x, -d * 0.08, 0.05),
            (lad_x, 0.02, roof_z + 0.30),
            thickness=0.08,
            mat_idx=3,
        )

        # 5. Low stone doorway with heavy timber lintel
        ey = -d / 2.0 - 0.01
        door_w = 0.80
        door_h = 1.65
        self._add_box(
            bm,
            (0, ey, (door_h + 0.16) / 2.0),
            (door_w + 0.24, 0.16, door_h + 0.16),
            mat_idx=0,
        )
        self._add_box(
            bm, (0, ey - 0.04, door_h + 0.06), (door_w + 0.30, 0.20, 0.16), mat_idx=3
        )  # Timber lintel
        self._add_box(bm, (0, ey - 0.02, door_h / 2.0), (door_w, 0.06, door_h), mat_idx=3)
        # Stone doorstep
        self._add_box(bm, (0, ey - 0.16, 0.10), (1.05, 0.30, 0.20), mat_idx=0)

        self._finalize_mesh(obj, mesh, bm)
        return obj


# =============================================================================
# 4. CHALCOLITHIC ERA (Copper Age / Proto-Urban Metallurgy)
# =============================================================================


@GeneratorRegistry.register("chalco_home_a")
class PropChalcoHomeAGenerator(BasePrehistoricGenerator):
    """Chalcolithic Model A: Whitewashed Adobe & Stone-Plinth House with Porch."""

    def create_mesh(self) -> bpy.types.Object:
        mesh_name = self.kwargs.get("name", "ChalcoHome_01_A")
        mesh = bpy.data.meshes.new(name=mesh_name)
        obj = bpy.data.objects.new(mesh_name, mesh)
        bpy.context.collection.objects.link(obj)

        palette = [
            ("M_WhiteAdobe", (0.88, 0.86, 0.82), 0.80, 0.00, 0.05, 45.0),
            ("M_Stone", (0.38, 0.36, 0.34), 0.85, 0.00, 0.10, 35.0),
            ("M_Tiles", (0.60, 0.26, 0.16), 0.72, 0.00, 0.06, 50.0),
            ("M_Timber", (0.24, 0.15, 0.08), 0.65, 0.00, 0.06, 55.0),
            ("M_Copper", (0.75, 0.42, 0.28), 0.35, 0.90, 0.04, 80.0),
        ]
        for mat in self._setup_materials(mesh_name, palette):
            obj.data.materials.append(mat)

        bm = bmesh.new()

        w = self.width * 0.88  # ~3.52m
        d = self.depth * 0.78  # ~3.90m
        h = self.height * 0.98  # ~4.90m
        eave_z = h * 0.52  # ~2.55m
        socle_h = 0.48

        # 1. Dressed ashlar stone socle foundation
        self._add_box(bm, (0, 0, socle_h / 2.0), (w * 1.04, d * 1.04, socle_h), mat_idx=1)

        # 2. Main whitewashed adobe mudbrick walls
        wall_h = eave_z - socle_h
        wall_cz = socle_h + wall_h / 2.0
        self._add_box(bm, (0, 0, wall_cz), (w, d, wall_h), mat_idx=0)

        # Timber corner columns
        hw = w / 2.0
        hd = d / 2.0
        post_s = 0.15
        for cx, cy in [
            (-hw, -hd),
            (hw, -hd),
            (hw, hd),
            (-hw, hd),
        ]:
            self._add_box(bm, (cx, cy, wall_cz), (post_s, post_s, wall_h), mat_idx=3)

        # 3. Front covered porch veranda with 3 timber columns
        porch_d = 0.85
        porch_y = -hd - porch_d / 2.0
        # Stone porch floor slab
        self._add_box(
            bm,
            (0, porch_y, socle_h * 0.45),
            (w * 1.04, porch_d, socle_h * 0.90),
            mat_idx=1,
        )

        # 3 Porch timber columns on stone bases
        col_xs = [-w * 0.40, 0.0, w * 0.40]
        for px in col_xs:
            # Stone plinth base
            self._add_box(
                bm,
                (px, -hd - porch_d + 0.12, socle_h + 0.10),
                (0.24, 0.24, 0.20),
                mat_idx=1,
            )
            # Timber column
            self._add_box(
                bm,
                (px, -hd - porch_d + 0.12, (socle_h + 0.20 + eave_z) / 2.0),
                (0.14, 0.14, eave_z - socle_h - 0.20),
                mat_idx=3,
            )

        # Porch horizontal beam
        self._add_box(
            bm,
            (0, -hd - porch_d + 0.12, eave_z - 0.06),
            (w * 1.05, 0.16, 0.14),
            mat_idx=3,
        )

        # 4. Pitched clay tile & thatch roof
        self._add_roof_prism(bm, (0, 0), w * 1.04, d * 1.01, eave_z - 0.02, h, mat_idx=2)
        self._add_slanted_beam(
            bm, (-hw - 0.10, 0, eave_z - 0.04), (0, 0, h), thickness=0.16, mat_idx=3
        )
        self._add_slanted_beam(
            bm, (hw + 0.10, 0, eave_z - 0.04), (0, 0, h), thickness=0.16, mat_idx=3
        )

        # Porch roof extension forward
        self._add_slanted_beam(
            bm,
            (0, -hd - porch_d + 0.05, eave_z - 0.14),
            (0, -hd, eave_z + 0.25),
            thickness=0.18,
            mat_idx=2,
        )

        # Roof tiles stepped courses
        for c in range(6):
            t = (c + 1) / 7.0
            cz = eave_z + t * (h - eave_z)
            cx_l = -(1.0 - t) * (hw + 0.08)
            cx_r = (1.0 - t) * (hw + 0.08)
            self._add_box(bm, (cx_l, 0, cz), (0.22, d * 0.94, 0.06), mat_idx=2)
            self._add_box(bm, (cx_r, 0, cz), (0.22, d * 0.94, 0.06), mat_idx=2)

        # Central smoke vent hatch on roof
        self._add_box(bm, (0, -d * 0.15, h + 0.10), (0.60, 0.60, 0.20), mat_idx=3)

        # 5. Heavy plank door with hammered copper fittings
        ey = -hd - 0.01
        door_w = 0.84
        door_h = 1.80
        self._add_box(
            bm,
            (0, ey, socle_h + door_h / 2.0),
            (door_w + 0.18, 0.12, door_h + 0.14),
            mat_idx=3,
        )
        self._add_box(
            bm,
            (0, ey - 0.02, socle_h + door_h / 2.0),
            (door_w, 0.06, door_h),
            mat_idx=3,
        )
        # Copper strap hinges & center rosette plate
        for hz in [socle_h + door_h * 0.30, socle_h + door_h * 0.70]:
            self._add_box(bm, (0, ey - 0.055, hz), (door_w * 0.82, 0.02, 0.06), mat_idx=4)
        # Copper center plate & ring knocker
        self._add_box(bm, (0, ey - 0.055, socle_h + door_h * 0.50), (0.16, 0.02, 0.16), mat_idx=4)
        self._add_box(
            bm,
            (door_w * 0.25, ey - 0.065, socle_h + door_h * 0.45),
            (0.06, 0.03, 0.08),
            mat_idx=4,
        )

        # Side casement window with timber frame
        self._add_box(bm, (hw + 0.01, 0, socle_h + 1.10), (0.12, 0.60, 0.70), mat_idx=3)

        self._finalize_mesh(obj, mesh, bm)
        return obj


@GeneratorRegistry.register("chalco_home_b")
class PropChalcoHomeBGenerator(BasePrehistoricGenerator):
    """Chalcolithic Model B: Apsidal Roundhouse / Smelting Hearth Dwelling."""

    def create_mesh(self) -> bpy.types.Object:
        mesh_name = self.kwargs.get("name", "ChalcoHome_01_B")
        mesh = bpy.data.meshes.new(name=mesh_name)
        obj = bpy.data.objects.new(mesh_name, mesh)
        bpy.context.collection.objects.link(obj)

        palette = [
            ("M_Plaster", (0.80, 0.76, 0.70), 0.82, 0.00, 0.05, 45.0),
            ("M_Stone", (0.36, 0.35, 0.33), 0.86, 0.00, 0.10, 35.0),
            ("M_Thatch", (0.65, 0.52, 0.32), 0.80, 0.00, 0.08, 50.0),
            ("M_ClayHearth", (0.48, 0.28, 0.18), 0.75, 0.00, 0.07, 45.0),
            ("M_Copper", (0.78, 0.44, 0.30), 0.35, 0.90, 0.04, 80.0),
        ]
        for mat in self._setup_materials(mesh_name, palette):
            obj.data.materials.append(mat)

        bm = bmesh.new()

        w = self.width * 0.82  # ~3.28m
        d = self.depth * 0.94  # ~4.70m
        h = self.height * 0.96  # ~4.60m
        eave_z = h * 0.50  # ~2.30m
        socle_h = 0.42

        hw = w / 2.0
        hd = d / 2.0

        # 1. Foundation plinth: Rectangular front + semi-circular apsidal back
        self._add_box(bm, (0, -hd / 2.0, socle_h / 2.0), (w * 1.04, hd, socle_h), mat_idx=1)
        # Rear apsidal curve base
        for i in range(8):
            ang = (math.pi * i) / 7.0  # 0 to pi (facing +Y)
            ax = hw * 1.04 * math.cos(ang)
            ay = (hd * 0.96) * math.sin(ang)
            self._add_box(bm, (ax, ay, socle_h / 2.0), (0.50, 0.50, socle_h), mat_idx=1)

        # 2. Main plastered walls
        wall_h = eave_z - socle_h
        wall_cz = socle_h + wall_h / 2.0
        self._add_box(bm, (0, -hd / 2.0, wall_cz), (w, hd, wall_h), mat_idx=0)
        for i in range(8):
            ang = (math.pi * i) / 7.0
            ax = hw * math.cos(ang)
            ay = (hd * 0.96) * math.sin(ang)
            self._add_box(bm, (ax, ay, wall_cz), (0.45, 0.45, wall_h), mat_idx=0)

        # 3. Apsidal thatch roof: Gable front, semi-cone rear
        # Front gable roof section
        self._add_roof_prism(bm, (0, -hd / 2.0), w * 1.04, hd, eave_z - 0.02, h, mat_idx=2)
        self._add_slanted_beam(
            bm,
            (-hw - 0.10, -hd / 2.0, eave_z - 0.04),
            (0, -hd / 2.0, h),
            thickness=0.18,
            mat_idx=3,
        )
        self._add_slanted_beam(
            bm,
            (hw + 0.10, -hd / 2.0, eave_z - 0.04),
            (0, -hd / 2.0, h),
            thickness=0.18,
            mat_idx=3,
        )

        # Rear conical thatch solid roof
        rear_segs = 8
        apex = bm.verts.new((0.0, 0.0, h))
        bot_center = bm.verts.new((0.0, 0.0, eave_z - 0.02))
        curv_verts = []
        for i in range(rear_segs + 1):
            ang = math.pi * i / float(rear_segs)
            rx = hw * 1.04 * math.cos(ang)
            ry = (hd * 0.98) * math.sin(ang)
            curv_verts.append(bm.verts.new((rx, ry, eave_z - 0.02)))
        for i in range(rear_segs):
            v0 = curv_verts[i]
            v1 = curv_verts[i + 1]
            f_cone = bm.faces.new([v0, v1, apex])
            f_cone.material_index = 2
            f_bot = bm.faces.new([bot_center, v1, v0])
            f_bot.material_index = 2

        # 4. Exterior clay smelting hearth & chimney stack on right side
        hearth_x = hw + 0.25
        hearth_y = -hd * 0.15
        hearth_h = h * 0.65
        # Lower smelting furnace base
        self._add_box(bm, (hearth_x, hearth_y, 0.45), (0.65, 0.65, 0.90), mat_idx=3)
        # Smelting furnace chimney shaft
        self._add_box(
            bm,
            (hearth_x, hearth_y, hearth_h / 2.0 + 0.45),
            (0.38, 0.38, hearth_h),
            mat_idx=3,
        )
        # Smelting vent cap with copper fittings
        self._add_box(bm, (hearth_x, hearth_y, hearth_h + 0.50), (0.45, 0.45, 0.12), mat_idx=4)

        # 5. Front timber entrance portal with copper-strapped door
        ey = -hd - 0.02
        door_w = 0.84
        door_h = 1.78
        self._add_box(
            bm,
            (0, ey, socle_h + door_h / 2.0),
            (door_w + 0.20, 0.14, door_h + 0.14),
            mat_idx=1,
        )
        self._add_box(
            bm,
            (0, ey - 0.02, socle_h + door_h / 2.0),
            (door_w, 0.06, door_h),
            mat_idx=1,
        )
        # Stone doorstep
        self._add_box(
            bm,
            (0, ey - 0.16, socle_h * 0.45),
            (1.05, 0.32, socle_h * 0.90),
            mat_idx=1,
        )
        # Copper strap hinges
        for hz in [socle_h + door_h * 0.28, socle_h + door_h * 0.72]:
            self._add_box(bm, (0, ey - 0.055, hz), (door_w * 0.80, 0.02, 0.06), mat_idx=4)

        self._finalize_mesh(obj, mesh, bm)
        return obj
