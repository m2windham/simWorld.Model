"""
Two-Channel UV Unwrapping Pipeline
Unwraps UV0 ('UVMap') for PBR textures with 16px margin and UV1 ('LightmapUV') for static lightmapping.
"""

import bpy


class UVUnwrapper:
    """Handles 2-channel UV unwrapping architecture."""

    @staticmethod
    def unwrap(obj, texel_density: float = 5.12):
        """
        Unwraps mesh into UV0 (PBR Map) and UV1 (Lightmap).
        Safe for Blender 4.x headless execution.
        """
        if obj.type != "MESH":
            return

        mesh = obj.data

        # Ensure primary UV map exists
        if not mesh.uv_layers:
            mesh.uv_layers.new(name="UVMap")
        uv0 = mesh.uv_layers.get("UVMap")
        if not uv0:
            uv0 = mesh.uv_layers[0]
            uv0.name = "UVMap"

        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)

        # 1. UV0: Primary PBR Unwrapping
        uv0.active = True
        mesh.uv_layers.active_index = 0
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(angle_limit=1.15192, island_margin=0.02)
        bpy.ops.object.mode_set(mode="OBJECT")

        # 2. UV1: Dedicated Lightmap Channel (Non-overlapping, conservative padding)
        if len(mesh.uv_layers) < 2:
            uv1 = mesh.uv_layers.new(name="LightmapUV")
        else:
            uv1 = mesh.uv_layers[1]
            uv1.name = "LightmapUV"

        uv1.active = True
        mesh.uv_layers.active_index = 1
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        # island_margin 0.04 provides safe gutter to prevent lightmap leaking
        bpy.ops.uv.smart_project(angle_limit=1.15192, island_margin=0.04)
        bpy.ops.object.mode_set(mode="OBJECT")

        # Reset active UV layer to UV0
        uv0.active = True
        mesh.uv_layers.active_index = 0
        print(f"[UV Unwrapper] Successfully generated UV0 (PBR) and UV1 (Lightmap) on {obj.name}")
