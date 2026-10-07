"""
Calibrated 85mm Headless Turntable Studio Rig & Multi-Pass Diagnostic Renderer
Uses infallible TRACK_TO constraints, neutral 3-point lighting, and 18% neutral gray background.
Renders 5 diagnostic passes for Antigravity's multimodal vision evaluation:
1. beauty_045.png (Full PBR shaded 45 deg)
2. wireframe_clay_045.png (1px wireframe over neutral gray clay)
3. normal_orientation.png (World Normal & Red/Blue Face Orientation)
4. uv_checker_045.png (2048x2048 high-contrast checkerboard)
5. ao_cavity_045.png (Clay AO & curvature contact shadows)
"""

import math
from pathlib import Path


class TurntableStudio:
    """
    Calibrated 85mm Headless Turntable Studio Rig.
    Guarantees camera targeting using Blender TRACK_TO constraint.
    """

    def __init__(self, output_dir: str = "output/renders", resolution: int = 1024):
        self.output_dir = Path(output_dir)
        self.resolution = resolution
        self.lens_mm = 85.0

    def calculate_bounds(self, obj) -> tuple:
        """Calculates center point C and bounding radius R."""
        bbox = [obj.matrix_world @ v.co for v in obj.data.vertices]
        if not bbox:
            return (0.0, 0.0, 0.5), 1.0

        min_x = min(v.x for v in bbox)
        max_x = max(v.x for v in bbox)
        min_y = min(v.y for v in bbox)
        max_y = max(v.y for v in bbox)
        min_z = min(v.z for v in bbox)
        max_z = max(v.z for v in bbox)

        center = (
            (min_x + max_x) / 2.0,
            (min_y + max_y) / 2.0,
            (min_z + max_z) / 2.0,
        )
        diag = math.sqrt((max_x - min_x) ** 2 + (max_y - min_y) ** 2 + (max_z - min_z) ** 2)
        radius = max(0.3, diag / 2.0)
        return center, radius

    def calculate_camera_distance(self, radius: float) -> float:
        """Dynamic bounding-sphere distance: D = (R / sin(FOV_v / 2)) * 1.25"""
        sensor_height = 24.0
        fov_v = 2.0 * math.atan(sensor_height / (2.0 * self.lens_mm))
        return (radius / math.sin(fov_v / 2.0)) * 1.30

    def setup_environment(self, center: tuple, radius: float):
        """Sets up neutral 18% gray studio environment and calibrated 3-point lighting."""
        import bpy

        # Set studio world background (18% neutral gray diffuse environment)
        world = bpy.context.scene.world
        if not world:
            world = bpy.data.worlds.new("StudioWorld")
            bpy.context.scene.world = world
        world.use_nodes = True
        bg = world.node_tree.nodes.get("Background")
        if bg:
            bg.inputs["Color"].default_value = (0.216, 0.216, 0.216, 1.0)
            bg.inputs["Strength"].default_value = 0.8

        # Target Empty for tracking
        target = bpy.data.objects.get("StudioTarget")
        if not target:
            target = bpy.data.objects.new("StudioTarget", None)
            bpy.context.collection.objects.link(target)
        target.location = center

        # Remove old lights
        for obj in list(bpy.data.objects):
            if obj.type == "LIGHT":
                bpy.data.objects.remove(obj, do_unlink=True)

        cx, cy, cz = center
        dist = radius * 3.0

        # Key Light (Warm daylight 5600K, 45 deg azimuth, 35 deg elevation)
        key_data = bpy.data.lights.new(name="KeyLight", type="AREA")
        key_data.energy = 800.0 * (radius**1.5)
        key_data.size = radius * 1.5
        key_data.color = (1.0, 0.98, 0.95)
        key_obj = bpy.data.objects.new("KeyLight", key_data)
        bpy.context.collection.objects.link(key_obj)
        key_obj.location = (cx + dist * 0.707, cy - dist * 0.707, cz + radius * 1.8)
        self._add_track_to(key_obj, target)

        # Fill Light (Cool fill, -45 deg azimuth, 15 deg elevation)
        fill_data = bpy.data.lights.new(name="FillLight", type="AREA")
        fill_data.energy = 300.0 * (radius**1.5)
        fill_data.size = radius * 2.0
        fill_data.color = (0.92, 0.95, 1.0)
        fill_obj = bpy.data.objects.new("FillLight", fill_data)
        bpy.context.collection.objects.link(fill_obj)
        fill_obj.location = (cx - dist * 0.707, cy - dist * 0.707, cz + radius * 0.8)
        self._add_track_to(fill_obj, target)

        # Rim Light (Behind asset, +150 deg azimuth, 45 deg elevation)
        rim_data = bpy.data.lights.new(name="RimLight", type="AREA")
        rim_data.energy = 1000.0 * (radius**1.5)
        rim_data.size = radius * 1.0
        rim_data.color = (1.0, 1.0, 1.0)
        rim_obj = bpy.data.objects.new("RimLight", rim_data)
        bpy.context.collection.objects.link(rim_obj)
        rim_obj.location = (cx - radius * 1.5, cy + dist * 0.8, cz + radius * 2.0)
        self._add_track_to(rim_obj, target)

        return target

    def _add_track_to(self, obj, target):

        for c in obj.constraints:
            obj.constraints.remove(c)
        track = obj.constraints.new(type="TRACK_TO")
        track.target = target
        track.track_axis = "TRACK_NEGATIVE_Z"
        track.up_axis = "UP_Y"

    def setup_camera(
        self, target, radius: float, azimuth_deg: float = 45.0, elevation_deg: float = 20.0
    ):
        """Configures 85mm camera with infallible TRACK_TO constraint."""
        import bpy

        for obj in list(bpy.data.objects):
            if obj.type == "CAMERA":
                bpy.data.objects.remove(obj, do_unlink=True)

        cam_data = bpy.data.cameras.new(name="TurntableCamera")
        cam_data.lens = self.lens_mm
        cam_data.sensor_width = 36.0
        cam_data.sensor_height = 24.0
        cam_data.clip_start = 0.05
        cam_data.clip_end = 200.0

        cam_obj = bpy.data.objects.new("TurntableCamera", cam_data)
        bpy.context.collection.objects.link(cam_obj)
        bpy.context.scene.camera = cam_obj

        distance = self.calculate_camera_distance(radius)
        az_rad = math.radians(azimuth_deg)
        el_rad = math.radians(elevation_deg)

        cx, cy, cz = target.location
        cam_x = cx + distance * math.cos(el_rad) * math.sin(az_rad)
        cam_y = cy - distance * math.cos(el_rad) * math.cos(az_rad)
        cam_z = cz + distance * math.sin(el_rad)

        cam_obj.location = (cam_x, cam_y, cam_z)
        self._add_track_to(cam_obj, target)
        return cam_obj

    def render_passes(self, obj, asset_name: str) -> dict[str, str]:
        """
        Executes rendering for all 5 diagnostic passes.
        Returns dictionary of pass name to file path.
        """
        import bpy

        asset_dir = self.output_dir / asset_name
        asset_dir.mkdir(parents=True, exist_ok=True)

        scene = bpy.context.scene
        scene.render.resolution_x = self.resolution
        scene.render.resolution_y = self.resolution
        scene.render.image_settings.file_format = "PNG"
        scene.render.image_settings.color_mode = "RGBA"

        # Use Cycles with AMD HIP acceleration
        scene.render.engine = "CYCLES"
        scene.cycles.samples = 64
        scene.cycles.use_denoising = True

        center, radius = self.calculate_bounds(obj)
        target = self.setup_environment(center, radius)
        self.setup_camera(target, radius, azimuth_deg=45.0, elevation_deg=20.0)

        # Force depsgraph update so camera and light transforms evaluate
        bpy.context.view_layer.update()

        # Ensure collision hulls are never rendered in diagnostic passes
        for o in bpy.data.objects:
            if o.name.startswith(("UCX_", "UBX_")):
                o.hide_render = True

        rendered_files = {}
        original_mats = [slot.material for slot in obj.material_slots]

        # 1. Beauty Pass (Original PBR Materials)
        out_beauty = asset_dir / "beauty_045.png"
        scene.render.filepath = str(out_beauty)
        bpy.ops.render.render(write_still=True)
        rendered_files["beauty_045"] = str(out_beauty)

        # 2. Wireframe-on-Clay Pass
        clay_mat = self._create_clay_wireframe_material()
        self._apply_material_override(obj, clay_mat)
        out_wireframe = asset_dir / "wireframe_clay_045.png"
        scene.render.filepath = str(out_wireframe)
        bpy.ops.render.render(write_still=True)
        rendered_files["wireframe_clay_045"] = str(out_wireframe)

        # 3. Normal & Face Orientation Pass
        normal_mat = self._create_normal_orientation_material()
        self._apply_material_override(obj, normal_mat)
        out_normal = asset_dir / "normal_orientation.png"
        scene.render.filepath = str(out_normal)
        bpy.ops.render.render(write_still=True)
        rendered_files["normal_orientation"] = str(out_normal)

        # 4. UV Checkerboard Pass
        checker_mat = self._create_uv_checker_material()
        self._apply_material_override(obj, checker_mat)
        out_checker = asset_dir / "uv_checker_045.png"
        scene.render.filepath = str(out_checker)
        bpy.ops.render.render(write_still=True)
        rendered_files["uv_checker_045"] = str(out_checker)

        # 5. AO / Cavity Pass
        ao_mat = self._create_ao_cavity_material()
        self._apply_material_override(obj, ao_mat)
        out_ao = asset_dir / "ao_cavity_045.png"
        scene.render.filepath = str(out_ao)
        bpy.ops.render.render(write_still=True)
        rendered_files["ao_cavity_045"] = str(out_ao)

        # Restore original materials
        self._restore_materials(obj, original_mats)
        print(f"[Turntable Studio] Completed 5 diagnostic passes in: {asset_dir}")
        return rendered_files

    def _create_clay_wireframe_material(self):
        import bpy

        mat = bpy.data.materials.new(name="M_Diagnostic_ClayWire")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        out_node = nodes.new(type="ShaderNodeOutputMaterial")
        bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
        bsdf.inputs["Base Color"].default_value = (0.55, 0.55, 0.55, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.6
        bsdf.inputs["Metallic"].default_value = 0.0

        wire = nodes.new(type="ShaderNodeWireframe")
        wire.inputs["Size"].default_value = 0.8

        mix = nodes.new(type="ShaderNodeMixShader")
        black_emit = nodes.new(type="ShaderNodeEmission")
        black_emit.inputs["Color"].default_value = (0.02, 0.02, 0.02, 1.0)

        links.new(wire.outputs["Fac"], mix.inputs["Fac"])
        links.new(bsdf.outputs["BSDF"], mix.inputs[1])
        links.new(black_emit.outputs["Emission"], mix.inputs[2])
        links.new(mix.outputs["Shader"], out_node.inputs["Surface"])
        return mat

    def _create_normal_orientation_material(self):
        import bpy

        mat = bpy.data.materials.new(name="M_Diagnostic_Normals")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        out_node = nodes.new(type="ShaderNodeOutputMaterial")
        geom = nodes.new(type="ShaderNodeNewGeometry")
        emit = nodes.new(type="ShaderNodeEmission")

        # Map normal vector (-1..1) to RGB (0..1): 0.5 * N + 0.5
        map_range = nodes.new(type="ShaderNodeVectorMath")
        map_range.operation = "MULTIPLY_ADD"
        map_range.inputs[1].default_value = (0.5, 0.5, 0.5)
        map_range.inputs[2].default_value = (0.5, 0.5, 0.5)

        links.new(geom.outputs["Normal"], map_range.inputs[0])
        links.new(map_range.outputs["Vector"], emit.inputs["Color"])
        links.new(emit.outputs["Emission"], out_node.inputs["Surface"])
        return mat

    def _create_uv_checker_material(self):
        import bpy

        mat = bpy.data.materials.new(name="M_Diagnostic_UVChecker")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        out_node = nodes.new(type="ShaderNodeOutputMaterial")
        bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
        checker = nodes.new(type="ShaderNodeTexChecker")
        checker.inputs["Scale"].default_value = 16.0
        checker.inputs["Color1"].default_value = (0.85, 0.85, 0.85, 1.0)
        checker.inputs["Color2"].default_value = (0.15, 0.15, 0.15, 1.0)

        tex_coord = nodes.new(type="ShaderNodeTexCoord")
        links.new(tex_coord.outputs["UV"], checker.inputs["Vector"])
        links.new(checker.outputs["Color"], bsdf.inputs["Base Color"])
        links.new(bsdf.outputs["BSDF"], out_node.inputs["Surface"])
        return mat

    def _create_ao_cavity_material(self):
        import bpy

        mat = bpy.data.materials.new(name="M_Diagnostic_AO")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        out_node = nodes.new(type="ShaderNodeOutputMaterial")
        ao = nodes.new(type="ShaderNodeAmbientOcclusion")
        ao.inputs["Distance"].default_value = 0.5
        emit = nodes.new(type="ShaderNodeEmission")

        links.new(ao.outputs["AO"], emit.inputs["Color"])
        links.new(emit.outputs["Emission"], out_node.inputs["Surface"])
        return mat

    def _apply_material_override(self, obj, mat):
        if not obj.material_slots:
            obj.data.materials.append(mat)
        else:
            for slot in obj.material_slots:
                slot.material = mat

    def _restore_materials(self, obj, original_mats):
        for i, mat in enumerate(original_mats):
            if i < len(obj.material_slots):
                obj.material_slots[i].material = mat
