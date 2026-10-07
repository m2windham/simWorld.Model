# Antigravity 3D Modeling Studio: Operating Rules & Workflow

This project is a dedicated, production-grade **3D Asset Creation Studio** running locally in Antigravity 2.0. Whenever a user requests a 3D model, prop, environment, modular architecture, or animation, follow this mandatory end-to-end protocol.

---

## The Mandatory 8-Step Studio Protocol

### STEP 1: Vision & Concept Pre-Approval (MANDATORY BEFORE ANY 3D CODING)
1. **Analyze User Request**: Identify key aesthetic requirements, art style (e.g., sci-fi, realistic, stylized, industrial), dimensions, and functionality.
2. **Generate Concept Vision**:
   - Call the `generate_image` tool with a descriptive prompt representing the planned 3D model (turntable or studio product shot on a neutral background).
   - Format: `generate_image(Prompt="Studio product render of [Subject], neutral gray background, 3-point lighting, clean hard-surface details, 3D asset concept", ImageName="concept_[subject]")`
3. **Present to User for Sign-Off**:
   - Show the generated concept image to the user.
   - Explain the planned dimensions, target poly budget, and material breakdown.
   - **STOP and wait for the user's explicit approval** ("Does this visual match your vision?") before initiating any mesh generation or code execution.

---

### STEP 2: Technical Specification & Archetype Routing
Once the concept is approved, classify the asset archetype:
- **Archetype A: Standalone Enclosed Prop** (crates, barrels, mechanical units, pickups, weapons):
  - Strict Watertightness: Mandatory closed 2-manifold (`is_watertight == True`).
  - Pivot: Ground center ($Z=0$, centered $X/Y$).
  - Collision: `UBX_` (oriented box) or `UCX_` ($<32$ vertices convex hull).
- **Archetype B: Modular Architecture** (walls, floor tiles, stairs, columns, corridors):
  - Modularity: Aligned to metric power grid (1.0m, 2.0m, 3.0m, 4.0m widths; 0.1m, 0.2m thickness).
  - Open Boundary Permitted: Occluded back/bottom faces are culled to prevent overdraw.
  - Pivot: Corner origin ($Z=0, X=\text{Min}, Y=0$) for metric grid snapping.
  - Secondary UV: Mandatory **UV1 `LightmapUV`** non-overlapping channel for static lighting.
- **Archetype C: Animated / Rigged Asset**:
  - Armature root bone at `(0, 0, 0)`, normalized vertex weights (max 4 influences/vert).

---

### STEP 3: Core Mesh Synthesis (Procedural BMesh / Geometry Nodes)
- Execute the generator via `pipeline/bridge.py` or `python run_pipeline.py`.
- Base meshes must use clean quad loops with **0 N-gons** in final output.
- **External Anatomical Framing Mandate**:
  - Structural ribs, posts, rafters, and tusks must sweep prominently **outside** the core envelope volume ($R_{\text{frame}}(z) > R_{\text{core}}(z)$).
  - Never submerge structural members inside the primary volume. They define the silhouette.
- **Watertight Solid Primitive Architecture**:
  - All roof sections, rafters, posts, and portals must be constructed as closed, watertight 2-manifold volumes (e.g. `_add_roof_prism`, `_add_slanted_beam`, `_add_box`).
  - Zero single-sided planar sheets or see-through rafter gaps.
  - Finalize with bmesh `remove_doubles(dist=0.0005)` + `dissolve_degenerate(dist=0.0005)`, followed by edit-mode `dissolve_degenerate(threshold=0.0001)`.
- **Architectural Portals & Articulated Foundations**:
  - Ground contact must align flush at $Z_{\min} = 0.000\text{m}$.
  - Foundation perimeter must feature articulated alternating courses (e.g., mandible blocks + boulders, or stone socle + timber sills).
  - Entrance portals must be architecturally framed (e.g., interlocking curved tusk gothic arches or post-and-lintel porticos with gabled canopies).
- **Bounding Budget Allocation**:
  - Global footprint constraints (e.g. $4.0\text{m} \times 5.0\text{m} \pm 8\%$) encompass all protruding porches, eaves, and curved framing.
  - Scale base core envelopes proportionally (e.g. width $\times 0.90$, depth $\times 0.84$) so the composite outer bounds strictly satisfy grid-plot specifications.
- Apply micro-bevel (2 segments, angle limit $30^\circ$, or 0 segments for displaced natural rock) + `WEIGHTED_NORMAL` modifier (`keep_sharp=True`).

---

### STEP 4: UV Unwrapping & Production Refinery
- **UV0 (`UVMap`)**: Sharp edges marked as seams, Smart UV unwrap, scaled to **5.12 px/cm** texel density, island margin $\ge 0.02$ (~16px padding at 2048x2048 to prevent mipmap bleed).
- **UV1 (`LightmapUV`)**: Non-overlapping lightmap pack clamped inside $[0.0, 1.0]$.
- **PBR Baking (Cycles AMD HIP)**:
  - Bake flat-diffuse Albedo (0 directional lighting), AO, Roughness, Metallic, Tangent Normal.
  - Pack **ORM Map** (`<Name>_ORM.png`: Red = AO, Green = Roughness, Blue = Metallic).
  - Pack dual normal maps: `<Name>_Normal_GL.png` (+Y) and `<Name>_Normal_DX.png` (-Y).

---

### STEP 5: Quantitative Pre-Flight Gate (Zero-Tolerance Math)
Before launching visual renders, run `pipeline/qa/preflight_validator.py`. The mesh must achieve 100% pass rate:
- [x] Profile compliance: Watertight for props; 0 interior non-manifold edges ($>2$ faces) for architecture.
- [x] Zero zero-area degenerate triangles (`area < 1e-7`).
- [x] Zero unreferenced floating vertices.
- [x] Texel density coefficient of variation $< 15\%$.
- [x] Bounding box dimensions within $8\%$ of specification; pivot $Z=0$ verified.
- [x] Khronos `gltf-validator` CLI reports 0 errors and 0 warnings.

---

### STEP 6 & 7: 5-Pass Turntable Studio & Multimodal Vision QA Judge
1. Render 5 diagnostic passes via `pipeline/qa/turntable_studio.py` (85mm camera, 3-point lighting):
   - `beauty_045.png` (PBR shaded beauty pass)
   - `wireframe_clay_045.png` (quad topology and edge flow)
   - `normal_orientation.png` (world normals, red flags for inverted normals)
   - `uv_checker_045.png` (texel uniformity and stretch)
   - `ao_cavity_045.png` (contact shadows and cavity darkening)
2. **Autonomous Multimodal Vision Judge** (`pipeline/qa/vision_evaluator.py`):
   - Multimodal model inspects all 5 passes via `view_file`.
   - Audits against the standardized 5-axis rubric:
     - **Silhouette & Organic Anatomy (30%)**: Curved framing, entrance portals, foundation courses matching concept.
     - **Topology & Edge Flow (25%)**: Clean quads/tris, absence of clustering or pinching.
     - **Normal & Shading Fidelity (20%)**: Blue front-facing orientation, smooth vs hard edge clarity.
     - **UV & Texel Uniformity (15%)**: Minimal distortion along seams, uniform grid squares.
     - **Contact & AO Depth (10%)**: Firm contact shadow at $Z=0.0\text{m}$, deep recess darkening.
   - Emits validated `output/renders/<ModelName>/vision_qa_report.json`.
   - Minimum passing threshold: Weighted score $\ge 0.70$ and 0 blocker findings.
   - If flawed: trigger `remediation_dispatcher.py` for automated repair (max 2 loops).

---

### STEP 8: Packaging & Final Delivery
- Export standard uncompressed `.glb` with precomputed tangents.
- Export `.fbx` with embedded collision (`UCX_`) and LOD chains (LOD0 100%, LOD1 50%, LOD2 25%).
- If user has Blender open, stream live geometry via `blender-mcp`.
- Present the final renders, model files, and validation summary in chat.
