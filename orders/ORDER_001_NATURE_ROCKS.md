# Production Order 001: Natural Rock & Stone Chunks

> **Priority**: 🔴 P1 — Critical World Generation Blocker  
> **Target Consumer**: [`m2windham/simWorld.Host`](file:///a:/dev/simWorld.Host) (`Assets/Resources/Models/`)  
> **Order Status**: **IN PROGRESS — Section A (Sandstone) DELIVERED & VERIFIED**  
> **Assigned Team**: `simWorld.Model` 3D Studio  

---

## 1. Context & Motivation

Live telemetry on a generated 200x200 TribalStart settlement map measures **12,989 instances of `Sandstone`** and dozens of stone chunks (`ChunkSandstone`, `ChunkLimestone`, `ChunkGranite`).

Because `Sandstone` does not yet exist under `Assets/Resources/Models/`, `VisualRegistry.Resolve("Sandstone", id)` returns `null`, and the host falls back to drawing 12,989 colored unit cubes. Replacing these with stylized, faceted rock meshes will immediately transform the entire game world visual.

---

## 2. Deliverables Specification

### A. Solid Rock Deposit: `Sandstone` (4 Variants)
- **File Names**:
  - `Sandstone_a.fbx`
  - `Sandstone_b.fbx`
  - `Sandstone_c.fbx`
  - `Sandstone_d.fbx`
- **Footprint**: Sits in a 1.0m × 1.0m grid cell. Height: 1.0m (occupies cell volume).
- **Pivot**: Ground-centered ($Z=0$, $X=0$, $Y=0$ or center of the 1x1 bottom face).
- **Aesthetic Direction**:
  - Timberborn / stylized blocky silhouette: large planar facets, beveled edges, stepped sedimentary strata.
  - Avoid noisy high-frequency procedural displacement. The silhouette does the work.
  - Micro-bevel on prominent edges with weighted normals (`keep_sharp=True`).
- **Polygon Budget**: 250 – 500 triangles per variant.
- **UVs**: `UV0` unwrapped, non-overlapping with margin $\ge 0.02$.

### B. Loose Stone Chunks: `ChunkSandstone`, `ChunkLimestone`, `ChunkGranite`
- **File Names**:
  - `ChunkSandstone.fbx` (or `ChunkSandstone_a.fbx`, `ChunkSandstone_b.fbx`)
  - `ChunkLimestone.fbx`
  - `ChunkGranite.fbx`
- **Footprint**: ~0.4m – 0.6m diameter loose boulder sitting on the ground.
- **Height**: 0.25m – 0.35m.
- **Polygon Budget**: 150 – 300 triangles.

---

## 3. Execution Recipe (Blender CLI / Pipeline)

In `a:\dev\simWorld.Model`:

```powershell
# Example generating rock variants via procedural generator or pipeline
python run_pipeline.py --prompt "Stylized Sandstone Rock Boulder, blocky sedimentary strata" --archetype prop_crate --dimensions 1.0 1.0 1.0
```

Or craft directly in Blender 4.5 using `pipeline/generators/` with the Timberborn blocky bevel style.

---

## 4. Verification & Delivery Checklist
- [x] 4 distinct silhouettes for `Sandstone_a` through `Sandstone_d`.
- [x] Dimensions verify $\approx 1.0\text{m} \times 1.0\text{m} \times 1.0\text{m}$.
- [x] Pre-flight gate passes: zero non-manifold edges, zero degenerate triangles.
- [x] Export `.fbx` placed in `a:\dev\simWorld.Host\Assets\Resources\Models\`.
- [x] Host verifies with `VisualRegistry.VariantCount("Sandstone") == 4`.
