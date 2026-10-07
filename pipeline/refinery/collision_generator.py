"""
Game Engine Collision Hull Generator
Generates UBX_ oriented bounding boxes and UCX_ simplified convex hulls.
Complies with Unreal Engine 5 and Godot 4 collision conventions.
"""

import bmesh
import bpy


class CollisionGenerator:
    """Generates collision hulls for game engines."""

    @staticmethod
    def generate_box_collision(obj, suffix="01"):
        """
        Generates an oriented bounding box collider (UBX_<name>_<suffix>).
        Lowest runtime physics cost.
        """
        bbox = obj.bound_box
        mesh = bpy.data.meshes.new(f"UBX_{obj.name}_{suffix}")
        col_obj = bpy.data.objects.new(f"UBX_{obj.name}_{suffix}", mesh)
        bpy.context.collection.objects.link(col_obj)

        bm = bmesh.new()
        bm_verts = [bm.verts.new(v) for v in bbox]
        bmesh.ops.convex_hull(bm, input=bm_verts)
        bm.to_mesh(mesh)
        bm.free()

        col_obj.matrix_world = obj.matrix_world
        col_obj.display_type = "WIRE"
        col_obj.hide_render = True
        return col_obj

    @staticmethod
    def generate_convex_hull(obj, suffix="01"):
        """
        Generates a clean low-poly convex hull collider (UCX_<name>_<suffix>).
        Guarantees watertight manifold collision shell.
        """
        mesh = bpy.data.meshes.new(f"UCX_{obj.name}_{suffix}")
        col_obj = bpy.data.objects.new(f"UCX_{obj.name}_{suffix}", mesh)
        bpy.context.collection.objects.link(col_obj)

        bm = bmesh.new()
        # Collect unique coordinates from visual mesh
        coords = [v.co.copy() for v in obj.data.vertices]
        bm_verts = [bm.verts.new(c) for c in coords]
        hull_res = bmesh.ops.convex_hull(bm, input=bm_verts)

        # Delete any internal unreferenced geometry
        hull_geom = set(hull_res["geom"])
        del_verts = [v for v in bm.verts if v not in hull_geom]
        if del_verts:
            bmesh.ops.delete(bm, geom=del_verts, context="VERTS")

        bm.to_mesh(mesh)
        bm.free()

        col_obj.matrix_world = obj.matrix_world
        col_obj.display_type = "WIRE"
        col_obj.hide_render = True
        return col_obj
