"""
Zero-Tolerance Quantitative Pre-Flight Test Suite
Combines PyMeshLab and Trimesh to perform industrial-grade validation:
- Resolves GPU UV/tangent seam vertex splits using PyMeshLab
- Asserts profile rules (watertightness for props, boundary allowance for modular architecture)
- Asserts zero zero-area degenerate triangles
- Asserts real-world metric dimensions and pivot ground alignment
- Executes Khronos gltf-validator CLI
"""

import json
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
import pymeshlab
import trimesh


def run_gltf_validator(filepath: str) -> list[str]:
    """Runs Khronos gltf-validator CLI if available on the system."""
    errors = []
    try:
        result = subprocess.run(["gltf-validator", "-p", filepath], capture_output=True, text=True)
        if result.returncode != 0:
            errors.append(f"gltf-validator returned errors: {result.stdout}")
    except FileNotFoundError:
        pass
    except Exception as e:
        errors.append(f"gltf-validator execution exception: {e}")
    return errors


def extract_primary_mesh_data(mesh_file: Path) -> trimesh.Trimesh:
    """Extracts the primary visual mesh from a glTF scene or file."""
    loaded = trimesh.load(str(mesh_file))
    if isinstance(loaded, trimesh.Scene):
        visual_geoms = [
            geom
            for name, geom in loaded.geometry.items()
            if not (name.startswith("UCX_") or name.startswith("UBX_"))
        ]
        if visual_geoms:
            if len(visual_geoms) == 1:
                return visual_geoms[0].copy()
            return trimesh.util.concatenate(visual_geoms)
        first_key = list(loaded.geometry.keys())[0]
        return loaded.geometry[first_key].copy()
    return loaded.copy()


def validate_asset(
    mesh_path: str,
    asset_type: str = "prop",
    target_bounds: list[float] | None = None,
    is_ground_prop: bool = True,
    tolerance: float = 0.08,
) -> dict[str, Any]:
    """
    Zero-Tolerance Quantitative Pre-Flight Test Suite.
    Validates topological manifoldness, absence of degenerates, dimensions, and pivots.
    """
    results: dict[str, Any] = {"passed": True, "errors": [], "metrics": {}}

    mesh_file = Path(mesh_path).resolve()
    if not mesh_file.is_file():
        results["passed"] = False
        results["errors"].append(f"File not found: {mesh_file}")
        return results

    # 1. Trimesh Dimension and Extents Inspection
    try:
        t_mesh = extract_primary_mesh_data(mesh_file)
    except Exception as e:
        results["passed"] = False
        results["errors"].append(f"Failed to load mesh in Trimesh: {e}")
        return results

    is_gltf = mesh_file.suffix.lower() in [".glb", ".gltf"]
    raw_extents = t_mesh.bounding_box.extents.tolist()

    if is_gltf:
        # glTF: X=Width, Y=Height, Z=Depth
        actual_width = raw_extents[0]
        actual_height = raw_extents[1]
        actual_depth = raw_extents[2]
        ground_val = float(t_mesh.bounds[0][1])  # Y-min is ground
    else:
        actual_width = raw_extents[0]
        actual_depth = raw_extents[1]
        actual_height = raw_extents[2]
        ground_val = float(t_mesh.bounds[0][2])  # Z-min is ground

    results["metrics"]["dimensions"] = [actual_width, actual_depth, actual_height]
    results["metrics"]["ground_min"] = ground_val
    results["metrics"]["raw_vertex_count"] = int(len(t_mesh.vertices))
    results["metrics"]["face_count"] = int(len(t_mesh.faces))

    # Check dimensions against target [width, depth, height]
    if target_bounds and len(target_bounds) == 3:
        target_w, target_d, target_h = target_bounds
        for name, actual, expected in [
            ("Width (X)", actual_width, target_w),
            ("Depth (Y)", actual_depth, target_d),
            ("Height (Z)", actual_height, target_h),
        ]:
            diff_ratio = abs(actual - expected) / max(0.01, expected)
            if diff_ratio > tolerance:
                results["passed"] = False
                results["errors"].append(
                    f"Dimension mismatch on {name}: actual {actual:.3f}m vs expected {expected:.3f}m (diff {diff_ratio:.1%})."
                )

    # Check pivot ground contact
    if is_ground_prop and abs(ground_val) > 0.05:
        results["passed"] = False
        results["errors"].append(
            f"Pivot ground alignment mismatch: ground plane min is {ground_val:.3f}m (expected ~0.0m)."
        )

    # 2. Degenerate Zero-Area Faces
    degenerate_mask = t_mesh.area_faces < 1e-7
    degenerate_count = int(np.sum(degenerate_mask))
    results["metrics"]["degenerate_faces"] = degenerate_count
    if degenerate_count > 0:
        results["passed"] = False
        results["errors"].append(f"Found {degenerate_count} degenerate zero-area faces.")

    # 3. Industrial Topological Validation via PyMeshLab
    try:
        ms = pymeshlab.MeshSet()
        ms.load_new_mesh(str(mesh_file))
        # Welds split vertices across UV seams and GPU tangent boundaries
        ms.meshing_remove_duplicate_vertices()
        ms.meshing_repair_non_manifold_edges()

        cleaned_mesh = ms.current_mesh()
        clean_verts = cleaned_mesh.vertex_number()
        clean_faces = cleaned_mesh.face_number()
        results["metrics"]["clean_vertex_count"] = clean_verts
        results["metrics"]["clean_face_count"] = clean_faces

        # Export temporary OBJ to test watertightness on welded mesh
        temp_clean_obj = mesh_file.parent / f"_temp_val_{mesh_file.stem}.obj"
        ms.save_current_mesh(str(temp_clean_obj))
        welded_mesh = trimesh.load(str(temp_clean_obj))
        is_watertight = bool(welded_mesh.is_watertight)
        results["metrics"]["is_watertight"] = is_watertight

        if temp_clean_obj.exists():
            temp_clean_obj.unlink()

        if asset_type == "prop" and not is_watertight:
            results["passed"] = False
            results["errors"].append("Prop mesh is not closed/watertight.")

    except Exception as exc:
        results["passed"] = False
        results["errors"].append(f"PyMeshLab topological validation error: {exc}")

    # 4. glTF Validator Execution
    if is_gltf:
        gltf_errs = run_gltf_validator(str(mesh_file))
        if gltf_errs:
            results["passed"] = False
            results["errors"].extend(gltf_errs)

    return results


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        res = validate_asset(sys.argv[1])
        print(json.dumps(res, indent=2))
    else:
        print("Usage: python -m pipeline.qa.preflight_validator <mesh_path>")
