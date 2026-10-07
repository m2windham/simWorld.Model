"""
Production 3D Asset Exporters for Game Engines
Exports glTF 2.0 (.glb) with precomputed tangents and FBX with Unreal/Unity scale and orientation.
"""

from pathlib import Path
from typing import Any


def export_production_glb(
    output_path: str,
    asset_obj: Any,
    collision_objs: list[Any] | None = None,
    enable_draco: bool = False,
) -> str:
    """
    Exports standard uncompressed .glb (default for Unreal, Godot 4, Unity)
    with precomputed tangents, materials, and collision shapes (-col suffix for Godot).
    Optional Draco compression (--draco) for web runtimes.

    Args:
        output_path: Target .glb file path
        asset_obj: Main visual asset object in Blender
        collision_objs: Optional list of collision objects
        enable_draco: Whether to apply Draco mesh compression

    Returns:
        str: Absolute path to exported .glb
    """
    import bpy

    out_file = Path(output_path).resolve()
    out_file.parent.mkdir(parents=True, exist_ok=True)

    # Select target objects
    bpy.ops.object.select_all(action="DESELECT")
    asset_obj.select_set(True)
    bpy.context.view_layer.objects.active = asset_obj

    if collision_objs:
        for col in collision_objs:
            if col:
                col.select_set(True)

    export_kwargs = {
        "filepath": str(out_file),
        "export_format": "GLB",
        "use_selection": True,
        "export_apply": True,
        "export_yup": True,
        "export_texcoords": True,
        "export_normals": True,
        "export_tangents": True,
        "export_materials": "EXPORT",
        "export_attributes": False,
        "export_image_format": "AUTO",
        "export_animations": False,
        "export_cameras": False,
        "export_lights": False,
    }

    if enable_draco:
        export_kwargs.update(
            {
                "export_draco_mesh_compression_enable": True,
                "export_draco_mesh_compression_level": 6,
                "export_draco_position_quantization": 14,
                "export_draco_normal_quantization": 10,
                "export_draco_texcoord_quantization": 12,
            }
        )
    else:
        export_kwargs["export_draco_mesh_compression_enable"] = False

    bpy.ops.export_scene.gltf(**export_kwargs)
    print(f"[Exporter] Exported Production glTF: {out_file} (Draco={enable_draco})")
    return str(out_file)


def export_production_fbx(
    output_path: str,
    asset_obj: Any,
    collision_objs: list[Any] | None = None,
    lod_objs: list[Any] | None = None,
) -> str:
    """
    Exports .fbx with apply_scale_options='FBX_SCALE_ALL', axis_forward='-Z',
    axis_up='Y', bake_space_transform=True (eliminating the -90 deg X-rotation in Unreal Engine),
    embedding LOD hierarchy and UCX_/UBX_ collision hulls.

    Args:
        output_path: Target .fbx file path
        asset_obj: Main visual asset object
        collision_objs: Optional list of collision objects
        lod_objs: Optional list of LOD objects

    Returns:
        str: Absolute path to exported .fbx
    """
    import bpy

    out_file = Path(output_path).resolve()
    out_file.parent.mkdir(parents=True, exist_ok=True)

    bpy.ops.object.select_all(action="DESELECT")
    asset_obj.select_set(True)
    bpy.context.view_layer.objects.active = asset_obj

    if collision_objs:
        for col in collision_objs:
            if col:
                col.select_set(True)

    if lod_objs:
        for lod in lod_objs:
            if lod:
                lod.select_set(True)

    bpy.ops.export_scene.fbx(
        filepath=str(out_file),
        use_selection=True,
        apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_ALL",
        axis_forward="-Z",
        axis_up="Y",
        bake_space_transform=True,
        object_types={"MESH"},
        mesh_smooth_type="FACE",
        use_mesh_modifiers=True,
        bake_anim=False,
    )
    print(f"[Exporter] Exported Production FBX: {out_file}")
    return str(out_file)
