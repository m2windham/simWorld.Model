import math

import bmesh


class NormalProcessor:
    """Processor for applying normals and bevels to meshes."""

    @staticmethod
    def process(obj, bevel_width=0.005, angle_limit_deg=30, bevel_segments=2):
        """Applies micro-bevel, weighted normals, and auto-smooth configuration.

        bevel_segments=0 skips the bevel entirely and keeps everything else. The bevel runs on
        every edge sharper than angle_limit_deg, which on hard-surface architecture is a handful
        of edges and on a displaced natural mass is ALL of them: a 50-face rock leaves here as
        ~800 triangles, which at the ~13,000 rock instances a SimWorld map carries is 10.4M
        triangles for rock alone. A displaced rock does not need micro-bevels - its facets are
        already the silhouette, and the weighted-normal pass below still gives the shading.

        The default is unchanged, so every asset generated before this parameter existed is
        unaffected."""
        if obj.type != "MESH":
            return

        # Micro-bevel modifier
        if bevel_segments > 0:
            bevel_mod = obj.modifiers.new(name="MicroBevel", type="BEVEL")
            bevel_mod.segments = bevel_segments
            bevel_mod.width = bevel_width
            bevel_mod.limit_method = "ANGLE"
            bevel_mod.angle_limit = math.radians(angle_limit_deg)
            bevel_mod.profile = 0.5
            bevel_mod.miter_outer = "MITER_SHARP"
            bevel_mod.use_clamp_overlap = True

        # Weighted Normal modifier
        weighted_normal_mod = obj.modifiers.new(name="WeightedNormal", type="WEIGHTED_NORMAL")
        weighted_normal_mod.mode = "FACE_AREA"
        weighted_normal_mod.weight = 50
        weighted_normal_mod.keep_sharp = True

        # Triangulate N-Gons only (guarantees tangent calculation for glTF export)
        tri_mod = obj.modifiers.new(name="TriangulateNgons", type="TRIANGULATE")
        tri_mod.min_vertices = 5
        tri_mod.quad_method = "BEAUTY"
        tri_mod.ngon_method = "BEAUTY"

        # Auto-smooth enabled (via mesh properties)
        mesh = obj.data
        if hasattr(mesh, "use_auto_smooth"):
            mesh.use_auto_smooth = True
            mesh.auto_smooth_angle = math.radians(angle_limit_deg)

        # Mark sharp edges as UV seams
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bm.edges.ensure_lookup_table()

        for edge in bm.edges:
            if len(edge.link_faces) == 2:
                if edge.calc_face_angle() > math.radians(angle_limit_deg):
                    edge.smooth = False
                    edge.seam = True
            elif len(edge.link_faces) == 1:
                # Boundary edge on open modular geometry
                edge.smooth = False
                edge.seam = True

        bm.to_mesh(mesh)
        bm.free()
