"""
Headless Context Management and Safe BMesh Geometry Utilities
Prevents 'RuntimeError: poll() failed, context is incorrect' in headless Blender (blender -b).
Provides direct BMesh geometry operations bypassing fragile UI operator calls.
"""

from contextlib import contextmanager


@contextmanager
def headless_temp_override(active_obj=None, selected_objs=None, **kwargs):
    """
    Context manager wrapping bpy.context.temp_override safely for headless execution.
    Sets active and selected objects in view layer if provided.
    """
    try:
        import bpy
    except ImportError:
        yield
        return

    if active_obj:
        try:
            bpy.context.view_layer.objects.active = active_obj
        except Exception:
            pass

    if selected_objs:
        for obj in selected_objs:
            try:
                obj.select_set(True)
            except Exception:
                pass

    override_kwargs = {}
    if active_obj:
        override_kwargs["active_object"] = active_obj
    if selected_objs:
        override_kwargs["selected_objects"] = list(selected_objs)
        override_kwargs["selected_editable_objects"] = list(selected_objs)

    override_kwargs.update(kwargs)

    try:
        with bpy.context.temp_override(**override_kwargs):
            yield
    except Exception:
        # Fallback if temp_override fails in certain sub-contexts
        yield


def direct_bmesh_transform(obj, matrix):
    """
    Transforms object mesh vertices directly using matrix math,
    avoiding UI-dependent bpy.ops.object.transform_apply().
    """
    import bmesh

    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.transform(matrix)
    bm.to_mesh(me)
    bm.free()
    me.update()


def direct_bmesh_recalc_normals(bm):
    """
    Recalculates outward-pointing face normals directly in BMesh without bpy.ops.
    """
    import bmesh

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)


def direct_bmesh_remove_doubles(bm, dist: float = 0.0001):
    """
    Merges duplicate co-located vertices directly in BMesh without bpy.ops.
    """
    import bmesh

    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dist)


def direct_bmesh_triangulate_ngons(bm):
    """
    Triangulates strictly N-gons (faces with >4 vertices) using BEAUTY method,
    preserving intentional quad loops.
    """
    import bmesh

    ngon_faces = [f for f in bm.faces if len(f.verts) > 4]
    if ngon_faces:
        bmesh.ops.triangulate(bm, faces=ngon_faces, quad_method="BEAUTY", ngon_method="BEAUTY")


def clean_scene_datablocks():
    """
    Cleans all orphan meshes, materials, and textures from memory to prevent memory leaks.
    """
    try:
        import bpy

        for block in bpy.data.meshes:
            if block.users == 0:
                bpy.data.meshes.remove(block)
        for block in bpy.data.materials:
            if block.users == 0:
                bpy.data.materials.remove(block)
        for block in bpy.data.textures:
            if block.users == 0:
                bpy.data.textures.remove(block)
        for block in bpy.data.images:
            if block.users == 0:
                bpy.data.images.remove(block)
    except Exception:
        pass
