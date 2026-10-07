---
name: project-modeling-standard
description: "Standardized 3D procedural modeling synthesis rules, bounding budget allocation, and multimodal vision QA judge rubric"
metadata:
  node_type: memory
  type: project
  originSessionId: "6e7a2eb1-5495-4306-b6bb-14b77eb33bd1"
  created: "2026-09-20T11:13:00.000Z"
  modified: "2026-09-20T11:13:00.000Z"
  tags: [3d-modeling, procedural, blender, vision-qa, standard]
---

# Procedural 3D Modeling & Vision QA Production Standard

Verified architectural rules for procedural generation and QA in `simWorld.Model`:

## 1. External Anatomical Framing Mandate
- Structural ribs, rafters, timber posts, and tusks must sweep prominently **outside** the core volume envelope ($R_{\text{frame}}(z) > R_{\text{core}}(z)$).
- Submerging structural framing inside the primary volume destroys silhouette fidelity and leads to generic geometric blobs.
- Framework members must use tapered multi-segment beams (`_add_slanted_beam`) that curve visibly outward from ground anchor to peak.

## 2. Watertight Solid Primitive Architecture
- All geometry elements (roof wedges, beams, posts, lintels, foundation blocks) must be closed 2-manifold watertight volumes (`_add_roof_prism`, `_add_slanted_beam`, `_add_box`).
- Zero single-sided planar sheets or open rafter voids.
- Clean mesh with bmesh `remove_doubles(dist=0.0005)` + `dissolve_degenerate(dist=0.0005)` before writing to mesh, followed by edit-mode `dissolve_degenerate(threshold=0.0001)`.

## 3. Metric Plot Bounding Budgeting
- Game grid bounds (e.g. $4.0\text{m} \times 5.0\text{m} \pm 8\%$) apply to the composite outer bounding box.
- Core dwelling envelopes must be budgeted smaller (e.g., width $\times 0.90$, depth $\times 0.84$) so that protruding features (covered entrance porches, extended ridge poles, sweeping tusk ribs) strictly respect grid cell limits.
- Ground contact must align flush at $Z_{\min} = 0.000\text{m}$ with alternating articulated foundation blocks (mandibles/boulders or stone socle/timber sills).

## 4. Multimodal Vision QA Judge
- 5 diagnostic turntable passes (`beauty_045`, `wireframe_clay_045`, `normal_orientation`, `uv_checker_045`, `ao_cavity_045`).
- 5-axis weighted rubric via `VisionEvaluator`:
  - Silhouette & Anatomy (30%)
  - Topology & Edge Flow (25%)
  - Normal & Shading Fidelity (20%)
  - UV & Texel Uniformity (15%)
  - Contact Shadows & AO Depth (10%)
- Emits validated `output/renders/<ModelName>/vision_qa_report.json`. Minimum threshold: $\ge 0.70$ and 0 blockers.
