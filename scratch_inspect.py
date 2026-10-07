import pymeshlab
import trimesh

ms = pymeshlab.MeshSet()
ms.load_new_mesh("output/models/SciFiHeavyMilitary.glb")
print("PyMeshLab loaded mesh!")
print("Faces:", ms.current_mesh().face_number(), "Verts:", ms.current_mesh().vertex_number())

# PyMeshLab topological check
ms.meshing_remove_duplicate_vertices()
ms.meshing_repair_non_manifold_edges()
m_clean = ms.current_mesh()
print("After PyMeshLab clean:")
print("Faces:", m_clean.face_number(), "Verts:", m_clean.vertex_number())

# Save to temp and load with trimesh
ms.save_current_mesh("output/models/temp_clean.obj")
t_mesh = trimesh.load("output/models/temp_clean.obj")
print("Trimesh watertight after PyMeshLab:", t_mesh.is_watertight)
