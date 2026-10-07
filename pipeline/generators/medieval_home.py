"""
Procedural Medieval Home Generator (High-Effort AAA Edition)
Generates an authentic historic half-timbered (Fachwerk / Colombage) two-story home
closely matching concept art:
- Layered terracotta clay tile roof with overlapping staggered courses, ridge capping tiles, and rafter tails
- Rustic ashlar stone foundation with staggered masonry courses and two-tiered entrance steps
- Segmented stone masonry chimney stack with corbel collar, 4 stone pillars, and rain cap
- Full half-timber framing with jetty corbels, diagonal cross-braces, and gable king-post trusses
- 4-pane cross-mullion casement windows with recessed reflective glass and planked shutters
- Heavy studded plank door with iron strap hinges and iron ring pull knocker
- Rich procedural PBR shader graphs with micro-bump, wood grain, and stone noise
"""

import bmesh
import bpy
from mathutils import Vector

from .generator_registry import GeneratorRegistry


@GeneratorRegistry.register("prop_medieval_home")
class PropMedievalHomeGenerator:
    """High-effort procedural generator for medieval dwelling/home props."""

    def __init__(self, width: float = 4.0, depth: float = 5.0, height: float = 6.5, **kwargs):
        self.width = width
        self.depth = depth
        self.height = height
        self.kwargs = kwargs

    def create_mesh(self) -> bpy.types.Object:
        """Constructs and returns the complete high-effort medieval home asset."""
        mesh_name = self.kwargs.get("name", "MedievalHome")
        mesh = bpy.data.meshes.new(name=mesh_name)
        obj = bpy.data.objects.new(mesh_name, mesh)
        bpy.context.collection.objects.link(obj)

        # 1. Setup multi-slot PBR materials with procedural bump & surface character
        materials = self._setup_materials(mesh_name)
        for mat in materials:
            obj.data.materials.append(mat)

        # Material Slot Indices:
        # 0: M_Plaster (Lime plaster / stucco wall infill)
        # 1: M_Timber (Aged rustic oak structural framing & corbels)
        # 2: M_Stone (Rustic ashlar foundation, steps & chimney masonry)
        # 3: M_RoofTiles (Terracotta clay roof tiles & ridge caps)
        # 4: M_WoodPlank (Pine plank door & window shutters)
        # 5: M_Glass (Dark reflective leaded window glass)
        # 6: M_Iron (Wrought iron hinges, ring knocker, chimney braces)

        # 2. Geometric construction via BMesh
        bm = bmesh.new()

        # Key parametric dimensions
        hw = self.width / 2.0
        hd = self.depth / 2.0

        # Vertical elevations (Z-axis)
        z_ground = 0.0
        z_plinth_top = self.height * 0.095  # ~0.62m
        z_jetty_bot = self.height * 0.40  # ~2.60m
        z_jetty_top = self.height * 0.435  # ~2.83m
        z_upper_top = self.height * 0.67  # ~4.35m
        z_roof_ridge = self.height * 0.93  # ~6.05m
        z_chimney_top = self.height  # ~6.50m (exact apex)

        # Horizontal footprints
        upper_w = self.width * 0.84  # ~3.36m (jetty width)
        upper_d = self.depth * 0.82  # ~4.10m (jetty depth)
        ground_w = upper_w * 0.90  # ~3.02m (ground floor inset)
        ground_d = upper_d * 0.90  # ~3.69m (ground floor inset)
        plinth_w = ground_w * 1.04  # ~3.14m (stone foundation)
        plinth_d = ground_d * 1.04  # ~3.84m (stone foundation)

        # -------------------------------------------------------------
        # PART 1: Rustic Ashlar Stone Foundation & Entrance Steps
        # -------------------------------------------------------------
        self._build_stone_foundation(
            bm,
            width=plinth_w,
            depth=plinth_d,
            z_bot=z_ground,
            z_top=z_plinth_top,
            courses=3,
            mat_idx=2,
        )

        # Two-tier rounded entrance doorstep
        door_center_x = -ground_w * 0.18
        step1_w = 1.05
        step1_d = (self.depth / 2.0) - (plinth_d / 2.0) + 0.02
        step1_h = z_plinth_top * 0.35
        step1_y = -plinth_d / 2.0 - step1_d / 2.0 + 0.01
        self._add_box(
            bm, (door_center_x, step1_y, step1_h / 2.0), (step1_w, step1_d, step1_h), mat_idx=2
        )

        step2_w = 0.88
        step2_d = step1_d * 0.65
        step2_h = z_plinth_top * 0.65
        step2_y = -plinth_d / 2.0 - step2_d / 2.0 + 0.01
        self._add_box(
            bm, (door_center_x, step2_y, step2_h / 2.0), (step2_w, step2_d, step2_h), mat_idx=2
        )

        # -------------------------------------------------------------
        # PART 2: Ground Floor (Plaster Core + Timber Fachwerk Framing)
        # -------------------------------------------------------------
        g_h = z_jetty_bot - z_plinth_top + 0.02
        g_cz = z_plinth_top + g_h / 2.0 - 0.01

        # Solid plaster wall core
        self._add_box(bm, (0, 0, g_cz), (ground_w, ground_d, g_h), mat_idx=0)

        # Structural timber posts (heavy corner columns)
        post_s = 0.16
        g_corners = [
            (-ground_w / 2.0 + post_s / 2.0, -ground_d / 2.0 + post_s / 2.0),
            (ground_w / 2.0 - post_s / 2.0, -ground_d / 2.0 + post_s / 2.0),
            (ground_w / 2.0 - post_s / 2.0, ground_d / 2.0 - post_s / 2.0),
            (-ground_w / 2.0 + post_s / 2.0, ground_d / 2.0 - post_s / 2.0),
        ]
        for cx, cy in g_corners:
            self._add_box(bm, (cx, cy, g_cz), (post_s * 1.05, post_s * 1.05, g_h), mat_idx=1)

        # Ground floor intermediate vertical studs
        for cy in [-ground_d * 0.22, ground_d * 0.22]:
            self._add_box(bm, (-ground_w / 2.0, cy, g_cz), (post_s, post_s * 0.85, g_h), mat_idx=1)
            self._add_box(bm, (ground_w / 2.0, cy, g_cz), (post_s, post_s * 0.85, g_h), mat_idx=1)

        # Diagonal half-timber bracing beams (Side Fachwerk)
        side_x = ground_w / 2.0
        for sx in [-side_x, side_x]:
            self._add_slanted_beam(
                bm,
                (sx, -ground_d / 2.0 + post_s, z_plinth_top),
                (sx, -ground_d * 0.22, z_jetty_bot),
                thickness=0.12,
                mat_idx=1,
            )
            self._add_slanted_beam(
                bm,
                (sx, ground_d * 0.22, z_plinth_top),
                (sx, ground_d / 2.0 - post_s, z_jetty_bot),
                thickness=0.12,
                mat_idx=1,
            )

        # Front facade diagonal timber bracing
        self._add_slanted_beam(
            bm,
            (-ground_w / 2.0 + post_s, -ground_d / 2.0, z_plinth_top),
            (door_center_x - 0.50, -ground_d / 2.0, z_jetty_bot),
            thickness=0.12,
            mat_idx=1,
        )
        self._add_slanted_beam(
            bm,
            (ground_w / 2.0 - post_s, -ground_d / 2.0, z_plinth_top),
            (ground_w * 0.18, -ground_d / 2.0, z_jetty_bot),
            thickness=0.12,
            mat_idx=1,
        )

        # Front entrance door with vertical planks, iron strap hinges, and ring pull
        door_w = 0.86
        door_h = 1.82
        door_y = -ground_d / 2.0 - 0.01
        door_cz = z_plinth_top + door_h / 2.0
        self._build_authentic_door(
            bm, center=(door_center_x, door_y, door_cz), width=door_w, height=door_h
        )

        # Ground floor front window (to the right of the entrance door)
        win_w = 0.64
        win_h = 0.78
        win_z = z_plinth_top + 1.05
        self._build_4pane_window(
            bm,
            center=(ground_w * 0.26, -ground_d / 2.0 - 0.01, win_z),
            size=(win_w, 0.12, win_h),
            facing="-Y",
        )

        # Ground floor right side windows (Two window bays matching concept)
        self._build_4pane_window(
            bm,
            center=(ground_w / 2.0 + 0.01, -ground_d * 0.22, win_z),
            size=(0.12, win_w, win_h),
            facing="+X",
        )
        self._build_4pane_window(
            bm,
            center=(ground_w / 2.0 + 0.01, ground_d * 0.22, win_z),
            size=(0.12, win_w, win_h),
            facing="+X",
        )

        # -------------------------------------------------------------
        # PART 3: Cantilevered Jetty Overhang & Exposed Floor Corbels
        # -------------------------------------------------------------
        jetty_th = z_jetty_top - z_jetty_bot
        jetty_cz = (z_jetty_top + z_jetty_bot) / 2.0

        # Main horizontal bressummer beam belt
        self._add_box(bm, (0, 0, jetty_cz), (upper_w, upper_d, jetty_th), mat_idx=1)

        # Exposed floor joist corbel brackets underneath overhang
        corbel_count = 7
        for i in range(corbel_count):
            t = i / float(corbel_count - 1)
            cx = -upper_w / 2.0 + 0.22 + t * (upper_w - 0.44)
            # Front corbel
            self._add_box(
                bm, (cx, -ground_d / 2.0 - 0.07, z_jetty_bot - 0.08), (0.12, 0.22, 0.11), mat_idx=1
            )
            # Back corbel
            self._add_box(
                bm, (cx, ground_d / 2.0 + 0.07, z_jetty_bot - 0.08), (0.12, 0.22, 0.11), mat_idx=1
            )

        # -------------------------------------------------------------
        # PART 4: Upper Floor (Jettied Living Quarters)
        # -------------------------------------------------------------
        u_h = z_upper_top - z_jetty_top + 0.02
        u_cz = z_jetty_top + u_h / 2.0 - 0.01
        u_wall_w = upper_w * 0.96
        u_wall_d = upper_d * 0.96

        # Plaster wall body
        self._add_box(bm, (0, 0, u_cz), (u_wall_w, u_wall_d, u_h), mat_idx=0)

        # Upper floor timber corner posts
        for cx, cy in [
            (-u_wall_w / 2.0 + post_s / 2.0, -u_wall_d / 2.0 + post_s / 2.0),
            (u_wall_w / 2.0 - post_s / 2.0, -u_wall_d / 2.0 + post_s / 2.0),
            (u_wall_w / 2.0 - post_s / 2.0, u_wall_d / 2.0 - post_s / 2.0),
            (-u_wall_w / 2.0 + post_s / 2.0, u_wall_d / 2.0 - post_s / 2.0),
        ]:
            self._add_box(bm, (cx, cy, u_cz), (post_s * 1.05, post_s * 1.05, u_h), mat_idx=1)

        # Upper floor mid-rail horizontal belt
        rail_z = z_jetty_top + u_h * 0.48
        self._add_box(
            bm, (0, -u_wall_d / 2.0, rail_z), (u_wall_w, post_s * 0.70, post_s * 0.70), mat_idx=1
        )
        self._add_box(
            bm, (0, u_wall_d / 2.0, rail_z), (u_wall_w, post_s * 0.70, post_s * 0.70), mat_idx=1
        )
        self._add_box(
            bm, (-u_wall_w / 2.0, 0, rail_z), (post_s * 0.70, u_wall_d, post_s * 0.70), mat_idx=1
        )
        self._add_box(
            bm, (u_wall_w / 2.0, 0, rail_z), (post_s * 0.70, u_wall_d, post_s * 0.70), mat_idx=1
        )

        # Diagonal cross-braces on upper side walls
        for sx in [-u_wall_w / 2.0, u_wall_w / 2.0]:
            self._add_slanted_beam(
                bm,
                (sx, -u_wall_d / 2.0 + post_s, z_jetty_top),
                (sx, -u_wall_d * 0.20, rail_z),
                thickness=0.11,
                mat_idx=1,
            )
            self._add_slanted_beam(
                bm, (sx, -u_wall_d * 0.20, rail_z), (sx, 0, z_upper_top), thickness=0.11, mat_idx=1
            )
            self._add_slanted_beam(
                bm, (sx, 0, z_jetty_top), (sx, u_wall_d * 0.20, rail_z), thickness=0.11, mat_idx=1
            )
            self._add_slanted_beam(
                bm,
                (sx, u_wall_d * 0.20, rail_z),
                (sx, u_wall_d / 2.0 - post_s, z_upper_top),
                thickness=0.11,
                mat_idx=1,
            )

        # Upper floor front windows (Twin shuttered windows matching concept)
        u_win_z = z_jetty_top + u_h * 0.52
        u_win_w = 0.62
        u_win_h = 0.75
        self._build_4pane_window(
            bm,
            (-u_wall_w * 0.26, -u_wall_d / 2.0 - 0.01, u_win_z),
            (u_win_w, 0.12, u_win_h),
            facing="-Y",
        )
        self._build_4pane_window(
            bm,
            (u_wall_w * 0.26, -u_wall_d / 2.0 - 0.01, u_win_z),
            (u_win_w, 0.12, u_win_h),
            facing="-Y",
        )

        # Upper floor right side window
        self._build_4pane_window(
            bm, (u_wall_w / 2.0 + 0.01, 0, u_win_z), (0.12, u_win_w, u_win_h), facing="+X"
        )

        # -------------------------------------------------------------
        # PART 5: Attic Gables & Timber Truss Framing
        # -------------------------------------------------------------
        r_w = self.width * 0.92
        r_d = self.depth * 0.95
        r_eave_z = z_upper_top - 0.12

        # Triangular gable plaster walls Front (-Y) and Back (+Y)
        self._add_gable_wall(
            bm,
            y_pos=-u_wall_d / 2.0,
            width=u_wall_w,
            z_bot=z_upper_top - 0.03,
            z_top=z_roof_ridge - 0.06,
            thickness=0.14,
            mat_idx=0,
        )
        self._add_gable_wall(
            bm,
            y_pos=u_wall_d / 2.0,
            width=u_wall_w,
            z_bot=z_upper_top - 0.03,
            z_top=z_roof_ridge - 0.06,
            thickness=0.14,
            mat_idx=0,
        )

        # Front gable attic window (small casement window)
        attic_win_z = z_upper_top + (z_roof_ridge - z_upper_top) * 0.38
        self._build_4pane_window(
            bm,
            center=(0, -u_wall_d / 2.0 - 0.02, attic_win_z),
            size=(0.46, 0.10, 0.54),
            facing="-Y",
            shutters=False,
        )

        # Front gable timber trussing (Bargeboards, King Post, and Collar Tie)
        # Horizontal collar tie beam
        self._add_box(
            bm,
            center=(0, -u_wall_d / 2.0 - 0.03, z_upper_top + 0.04),
            size=(u_wall_w * 0.98, 0.12, 0.14),
            mat_idx=1,
        )
        # Vertical king post
        self._add_box(
            bm,
            center=(0, -u_wall_d / 2.0 - 0.04, (z_upper_top + z_roof_ridge) / 2.0),
            size=(0.14, 0.12, z_roof_ridge - z_upper_top),
            mat_idx=1,
        )
        # Angled queen struts
        self._add_slanted_beam(
            bm,
            (-u_wall_w * 0.38, -u_wall_d / 2.0 - 0.03, z_upper_top + 0.04),
            (0, -u_wall_d / 2.0 - 0.03, z_upper_top + (z_roof_ridge - z_upper_top) * 0.65),
            thickness=0.10,
            mat_idx=1,
        )
        self._add_slanted_beam(
            bm,
            (u_wall_w * 0.38, -u_wall_d / 2.0 - 0.03, z_upper_top + 0.04),
            (0, -u_wall_d / 2.0 - 0.03, z_upper_top + (z_roof_ridge - z_upper_top) * 0.65),
            thickness=0.10,
            mat_idx=1,
        )

        # -------------------------------------------------------------
        # PART 6: High-Fidelity Layered Terracotta Roof & Ridge System
        # -------------------------------------------------------------
        self._build_terracotta_tile_roof(
            bm,
            r_w=r_w,
            r_d=r_d,
            z_bot=r_eave_z,
            z_top=z_roof_ridge,
            courses=10,
            tiles_per_row=12,
            mat_idx=3,
        )

        # Exposed timber rafter tails beneath eaves
        rafter_count = 10
        for i in range(rafter_count):
            t = i / float(rafter_count - 1)
            ry = -r_d / 2.0 + 0.30 + t * (r_d - 0.60)
            # Left rafter tail
            self._add_box(
                bm, (-r_w / 2.0 + 0.14, ry, r_eave_z - 0.05), (0.24, 0.10, 0.09), mat_idx=1
            )
            # Right rafter tail
            self._add_box(
                bm, (r_w / 2.0 - 0.14, ry, r_eave_z - 0.05), (0.24, 0.10, 0.09), mat_idx=1
            )

        # -------------------------------------------------------------
        # PART 7: Segmented Stone Masonry Chimney Stack
        # -------------------------------------------------------------
        chim_w = self.width * 0.17  # ~0.68m
        chim_d = self.depth * 0.15  # ~0.75m
        chim_x = upper_w * 0.32  # ~1.08m
        chim_y = upper_d * 0.18  # ~0.74m

        self._build_stone_chimney(
            bm,
            center_x=chim_x,
            center_y=chim_y,
            base_z=z_upper_top * 0.85,
            ridge_z=z_roof_ridge,
            top_z=z_chimney_top,
            width=chim_w,
            depth=chim_d,
            mat_idx=2,
        )

        # 3. Clean and transfer BMesh to Object
        bmesh.ops.dissolve_degenerate(bm, dist=0.0005, edges=bm.edges)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0005)
        bm.to_mesh(mesh)
        bm.free()

        # 4. Make normals consistently face outwards
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.object.mode_set(mode="OBJECT")

        return obj

    # =========================================================================
    # High-Fidelity Geometry Builders
    # =========================================================================

    def _build_stone_foundation(
        self,
        bm: bmesh.types.BMesh,
        width: float,
        depth: float,
        z_bot: float,
        z_top: float,
        courses: int = 3,
        mat_idx: int = 2,
    ):
        """Constructs an authentic multi-course ashlar stone masonry plinth with relief."""
        total_h = z_top - z_bot
        course_h = total_h / courses
        hw = width / 2.0
        hd = depth / 2.0

        # Base solid core
        self._add_box(bm, (0, 0, (z_bot + z_top) / 2.0), (width, depth, total_h), mat_idx=mat_idx)

        # Exterior protruding ashlar stone blocks around perimeter
        for c in range(courses):
            cz = z_bot + (c + 0.5) * course_h
            # Stagger offset for alternating courses
            offset = 0.15 if (c % 2 == 1) else 0.0

            # Front (-Y) stone face blocks
            n_front = 5
            for i in range(n_front):
                bx = -hw + 0.30 + (i / float(n_front - 1)) * (width - 0.60) + offset * 0.5
                if abs(bx) < hw - 0.20:
                    self._add_box(
                        bm,
                        (bx, -hd - 0.02, cz),
                        (width / n_front * 0.88, 0.04, course_h * 0.88),
                        mat_idx=mat_idx,
                    )

            # Right (+X) stone face blocks
            n_side = 6
            for i in range(n_side):
                by = -hd + 0.30 + (i / float(n_side - 1)) * (depth - 0.60) + offset * 0.5
                if abs(by) < hd - 0.20:
                    self._add_box(
                        bm,
                        (hw + 0.02, by, cz),
                        (0.04, depth / n_side * 0.88, course_h * 0.88),
                        mat_idx=mat_idx,
                    )

    def _build_authentic_door(
        self, bm: bmesh.types.BMesh, center: tuple[float, float, float], width: float, height: float
    ):
        """Constructs a heavy timber entrance door with vertical planks and iron strap hinges."""
        cx, cy, cz = center

        # Heavy timber door casing / lintel
        casing_th = 0.14
        self._add_box(
            bm, (cx, cy, cz), (width + casing_th * 2.0, 0.14, height + casing_th), mat_idx=1
        )

        # Recessed door panel (Pine planks)
        self._add_box(bm, (cx, cy - 0.02, cz - 0.02), (width, 0.06, height), mat_idx=4)

        # Vertical plank grooves (3 distinct planks)
        plank_w = width / 3.0
        for i in range(3):
            px = cx - width / 2.0 + (i + 0.5) * plank_w
            self._add_box(
                bm, (px, cy - 0.035, cz - 0.02), (plank_w * 0.92, 0.02, height * 0.98), mat_idx=4
            )

        # Wrought iron strap hinges (two horizontal bands extending across door)
        for h_z in [cz + height * 0.32, cz - height * 0.32]:
            self._add_box(bm, (cx, cy - 0.055, h_z), (width * 0.86, 0.02, 0.06), mat_idx=6)
            # Hinge barrel pivot on left side
            self._add_box(bm, (cx - width * 0.44, cy - 0.065, h_z), (0.05, 0.05, 0.10), mat_idx=6)

        # Wrought iron ring knocker / pull handle
        handle_x = cx + width * 0.28
        handle_z = cz
        self._add_box(bm, (handle_x, cy - 0.06, handle_z), (0.07, 0.03, 0.09), mat_idx=6)
        self._add_box(bm, (handle_x, cy - 0.08, handle_z - 0.04), (0.06, 0.02, 0.07), mat_idx=6)

    def _build_4pane_window(
        self,
        bm: bmesh.types.BMesh,
        center: tuple[float, float, float],
        size: tuple[float, float, float],
        facing: str = "-Y",
        shutters: bool = True,
    ):
        """Constructs an authentic 4-pane cross-mullion casement window with shutters."""
        cx, cy, cz = center
        w, th, h = size

        # Outer timber casing frame
        self._add_box(bm, (cx, cy, cz), (w, th, h), mat_idx=1)

        # Protruding timber sill at bottom
        sill_th = 0.06
        sill_depth = th * 1.6
        if facing in ["-Y", "+Y"]:
            sill_y = (
                cy - (sill_depth - th) / 2.0 if facing == "-Y" else cy + (sill_depth - th) / 2.0
            )
            self._add_box(
                bm,
                (cx, sill_y, cz - h / 2.0 - sill_th / 2.0),
                (w * 1.15, sill_depth, sill_th),
                mat_idx=1,
            )
        else:
            sill_x = (
                cx - (sill_depth - th) / 2.0 if facing == "-X" else cx + (sill_depth - th) / 2.0
            )
            self._add_box(
                bm,
                (sill_x, cy, cz - h / 2.0 - sill_th / 2.0),
                (sill_depth, w * 1.15, sill_th),
                mat_idx=1,
            )

        # Recessed reflective glass panes
        glass_w = w * 0.76
        glass_h = h * 0.76
        self._add_box(bm, (cx, cy, cz), (glass_w, th * 0.35, glass_h), mat_idx=5)

        # 4-Pane cross mullion bars (vertical & horizontal timber dividers)
        mullion_s = 0.035
        self._add_box(bm, (cx, cy, cz), (glass_w, th * 0.45, mullion_s), mat_idx=1)
        self._add_box(bm, (cx, cy, cz), (mullion_s, th * 0.45, glass_h), mat_idx=1)

        # Rustic plank shutters with center groove and iron pintles
        if shutters:
            shutter_w = w * 0.38
            shutter_h = h * 0.92
            shutter_th = 0.045
            if facing == "-Y":
                # Left shutter
                lx = cx - w / 2.0 - shutter_w / 2.0 + 0.02
                self._add_box(
                    bm, (lx, cy - 0.03, cz), (shutter_w, shutter_th, shutter_h), mat_idx=4
                )
                # Shutter center groove
                self._add_box(bm, (lx, cy - 0.045, cz), (0.015, 0.02, shutter_h * 0.90), mat_idx=1)
                # Right shutter
                rx = cx + w / 2.0 + shutter_w / 2.0 - 0.02
                self._add_box(
                    bm, (rx, cy - 0.03, cz), (shutter_w, shutter_th, shutter_h), mat_idx=4
                )
                self._add_box(bm, (rx, cy - 0.045, cz), (0.015, 0.02, shutter_h * 0.90), mat_idx=1)
            elif facing == "+X":
                # Left shutter (towards -Y)
                sy1 = cy - w / 2.0 - shutter_w / 2.0 + 0.02
                self._add_box(
                    bm, (cx + 0.03, sy1, cz), (shutter_th, shutter_w, shutter_h), mat_idx=4
                )
                # Right shutter (towards +Y)
                sy2 = cy + w / 2.0 + shutter_w / 2.0 - 0.02
                self._add_box(
                    bm, (cx + 0.03, sy2, cz), (shutter_th, shutter_w, shutter_h), mat_idx=4
                )

    def _build_terracotta_tile_roof(
        self,
        bm: bmesh.types.BMesh,
        r_w: float,
        r_d: float,
        z_bot: float,
        z_top: float,
        courses: int = 10,
        tiles_per_row: int = 12,
        mat_idx: int = 3,
    ):
        """Constructs an authentic multi-course terracotta clay tile roof with overlapping tiles."""
        hw = r_w / 2.0
        hd = r_d / 2.0

        # 1. Base solid wedge core
        v_coords = [
            (-hw, -hd, z_bot),  # 0: Left-Front eave
            (hw, -hd, z_bot),  # 1: Right-Front eave
            (hw, hd, z_bot),  # 2: Right-Back eave
            (-hw, hd, z_bot),  # 3: Left-Back eave
            (0.0, -hd, z_top),  # 4: Ridge-Front
            (0.0, hd, z_top),  # 5: Ridge-Back
        ]
        bv = [bm.verts.new(c) for c in v_coords]

        f_bot = bm.faces.new([bv[0], bv[3], bv[2], bv[1]])
        f_bot.material_index = 1  # Timber soffit
        f_front = bm.faces.new([bv[0], bv[1], bv[4]])
        f_front.material_index = 1  # Timber bargeboard
        f_back = bm.faces.new([bv[2], bv[3], bv[5]])
        f_back.material_index = 1  # Timber bargeboard
        f_left = bm.faces.new([bv[0], bv[4], bv[5], bv[3]])
        f_left.material_index = mat_idx
        f_right = bm.faces.new([bv[1], bv[2], bv[5], bv[4]])
        f_right.material_index = mat_idx

        # Timber bargeboards along gable slope edges
        bb_th = 0.12
        for y_edge in [-hd + 0.02, hd - 0.02]:
            # Left slope bargeboard
            self._add_slanted_beam(
                bm, (-hw, y_edge, z_bot), (0, y_edge, z_top), thickness=bb_th, mat_idx=1
            )
            # Right slope bargeboard
            self._add_slanted_beam(
                bm, (hw, y_edge, z_bot), (0, y_edge, z_top), thickness=bb_th, mat_idx=1
            )

        # 2. Overlapping terracotta clay tile courses
        tile_len = (hw / float(courses)) * 1.25
        tile_w = (r_d / float(tiles_per_row)) * 0.94
        tile_th = 0.035

        for c in range(courses):
            # t = 0.0 (eave) to 1.0 (ridge)
            t = c / float(courses)
            # Course center coordinates
            dist_from_ridge = (1.0 - t) * (hw - tile_len * 0.35)
            cz = z_top - (1.0 - t) * (z_top - z_bot) + 0.035

            # Stagger alternating courses along Y
            y_shift = (tile_w * 0.5) if (c % 2 == 1) else 0.0

            for ti in range(tiles_per_row):
                ty = -hd + 0.25 + (ti / float(tiles_per_row - 1)) * (r_d - 0.50) + y_shift
                if abs(ty) > hd - 0.18:
                    continue

                # Left slope tile (-X)
                self._add_box(
                    bm,
                    center=(-dist_from_ridge, ty, cz),
                    size=(tile_len, tile_w, tile_th),
                    mat_idx=mat_idx,
                )
                # Right slope tile (+X)
                self._add_box(
                    bm,
                    center=(dist_from_ridge, ty, cz),
                    size=(tile_len, tile_w, tile_th),
                    mat_idx=mat_idx,
                )

        # 3. Half-round ceramic ridge capping tiles along the roof crest
        ridge_tile_count = 14
        r_step = (r_d - 0.30) / float(ridge_tile_count - 1)
        for ri in range(ridge_tile_count):
            ry = -hd + 0.15 + ri * r_step
            # Ridge cap tile
            self._add_box(
                bm,
                center=(0.0, ry, z_top + 0.05),
                size=(0.28, r_step * 1.15, 0.10),
                mat_idx=mat_idx,
            )

    def _build_stone_chimney(
        self,
        bm: bmesh.types.BMesh,
        center_x: float,
        center_y: float,
        base_z: float,
        ridge_z: float,
        top_z: float,
        width: float,
        depth: float,
        mat_idx: int = 2,
    ):
        """Constructs an authentic multi-course stone masonry chimney with corbel collar and cap."""
        collar_z = ridge_z + 0.14
        stack_h = collar_z - base_z

        # 1. Main stone chimney stack
        self._add_box(
            bm,
            center=(center_x, center_y, base_z + stack_h / 2.0),
            size=(width, depth, stack_h),
            mat_idx=mat_idx,
        )

        # 2. Horizontal masonry course relief on chimney
        chim_courses = 5
        c_h = stack_h / float(chim_courses)
        for ci in range(1, chim_courses):
            cz = base_z + ci * c_h
            if cz > ridge_z - 0.50:
                self._add_box(
                    bm,
                    center=(center_x, center_y, cz),
                    size=(width + 0.03, depth + 0.03, 0.04),
                    mat_idx=mat_idx,
                )

        # 3. Projecting stone corbel collar
        self._add_box(
            bm,
            center=(center_x, center_y, collar_z),
            size=(width + 0.12, depth + 0.12, 0.10),
            mat_idx=mat_idx,
        )

        # 4. Four stone smoke vent pillars
        pillar_s = 0.11
        pillar_h = 0.22
        pillar_cz = collar_z + 0.05 + pillar_h / 2.0
        for px in [-width / 2.0 + pillar_s / 2.0, width / 2.0 - pillar_s / 2.0]:
            for py in [-depth / 2.0 + pillar_s / 2.0, depth / 2.0 - pillar_s / 2.0]:
                self._add_box(
                    bm,
                    center=(center_x + px, center_y + py, pillar_cz),
                    size=(pillar_s, pillar_s, pillar_h),
                    mat_idx=mat_idx,
                )

        # 5. Heavy stone slab rain cap
        cap_cz = collar_z + 0.05 + pillar_h + 0.05
        cap_h = max(0.08, top_z - cap_cz)
        self._add_box(
            bm,
            center=(center_x, center_y, cap_cz),
            size=(width + 0.16, depth + 0.16, cap_h),
            mat_idx=mat_idx,
        )

    # =========================================================================
    # Basic BMesh Primitives
    # =========================================================================

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

    def _add_slanted_beam(
        self,
        bm: bmesh.types.BMesh,
        p1: tuple[float, float, float],
        p2: tuple[float, float, float],
        thickness: float = 0.12,
        mat_idx: int = 1,
    ):
        """Constructs an oriented timber beam between two 3D points."""
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
            (0, 4, 5, 1),  # Side 1
            (1, 5, 6, 2),  # Side 2
            (2, 6, 7, 3),  # Side 3
            (3, 7, 4, 0),  # Side 4
        ]
        for f in faces_idx:
            face = bm.faces.new([bm_verts[i] for i in f])
            face.material_index = mat_idx

    def _add_gable_wall(
        self,
        bm: bmesh.types.BMesh,
        y_pos: float,
        width: float,
        z_bot: float,
        z_top: float,
        thickness: float = 0.14,
        mat_idx: int = 0,
    ):
        """Constructs a triangular gable wall prism."""
        hw = width / 2.0
        ht = thickness / 2.0

        v_coords = [
            (-hw, y_pos - ht, z_bot),
            (hw, y_pos - ht, z_bot),
            (0, y_pos - ht, z_top),
            (-hw, y_pos + ht, z_bot),
            (hw, y_pos + ht, z_bot),
            (0, y_pos + ht, z_top),
        ]
        bv = [bm.verts.new(c) for c in v_coords]
        faces_idx = [
            (0, 1, 2),  # Front triangle
            (3, 5, 4),  # Back triangle
            (0, 3, 4, 1),  # Bottom quad
            (1, 4, 5, 2),  # Right sloped quad
            (2, 5, 3, 0),  # Left sloped quad
        ]
        for f in faces_idx:
            face = bm.faces.new([bv[i] for i in f])
            face.material_index = mat_idx

    # =========================================================================
    # High-Fidelity Procedural PBR Shader Networks
    # =========================================================================

    def _setup_materials(self, prefix: str) -> list[bpy.types.Material]:
        """Creates rich production-grade Principled BSDF materials with procedural micro-wear."""
        palette = [
            # 0: Plaster (Warm lime plaster with stucco micro-bump)
            ("M_Plaster", (0.86, 0.83, 0.76), 0.85, 0.00, 0.05, 45.0),
            # 1: Timber (Aged rustic dark oak with fiber bump)
            ("M_Timber", (0.18, 0.11, 0.06), 0.68, 0.00, 0.08, 60.0),
            # 2: Stone (Rustic chiseled ashlar masonry)
            ("M_Stone", (0.36, 0.34, 0.32), 0.88, 0.00, 0.12, 35.0),
            # 3: RoofTiles (Terracotta red clay tiles with porosity bump)
            ("M_RoofTiles", (0.58, 0.22, 0.12), 0.74, 0.00, 0.07, 50.0),
            # 4: WoodPlank (Pine plank door & window shutters)
            ("M_WoodPlank", (0.30, 0.18, 0.10), 0.64, 0.00, 0.06, 55.0),
            # 5: Glass (Dark reflective leaded window glass)
            ("M_Glass", (0.08, 0.12, 0.15), 0.10, 0.10, 0.00, 1.0),
            # 6: Iron (Cast wrought iron fittings)
            ("M_Iron", (0.06, 0.06, 0.06), 0.45, 0.95, 0.04, 80.0),
        ]

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
