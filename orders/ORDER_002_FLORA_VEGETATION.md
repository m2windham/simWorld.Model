# Production Order 002: Flora & Vegetation

> **Priority**: 🔴 P1 — Critical Surface Flora Blocker  
> **Target Consumer**: [`m2windham/simWorld.Host`](file:///a:/dev/simWorld.Host) (`Assets/Resources/Models/`)  
> **Order Status**: **READY FOR ASSIGNMENT**  
> **Assigned Team**: `simWorld.Model` 3D Studio  

---

## 1. Context & Motivation

On the active generated settlement interior:
- **`WildPlant`**: **775 instances**
- **`Plant_Berry`**: **605 instances**

Totaling nearly **1,400 instances** of plant life currently rendering as generic colored cubes. In `MapRenderer.cs`, plant heights scale dynamically with growth ($0.25 + 0.75 \times \text{growth}$), so the base models should have their pivot at the base roots ($Z=0$).

---

## 2. Deliverables Specification

### A. Wild Vegetation: `WildPlant` (2-3 Variants)
- **File Names**:
  - `WildPlant_a.fbx`
  - `WildPlant_b.fbx`
  - `WildPlant_c.fbx`
- **Footprint**: 0.6m – 0.8m spread, height ~0.5m – 0.8m.
- **Pivot**: Ground root center ($Z=0$, centered $X/Y$).
- **Aesthetic Direction**:
  - Stylized lush grass tufts / broadleaf ground foliage.
  - Geometry-driven silhouettes rather than alpha-cutout cards: chunky, low-poly solid leaves with stylized creases.
  - Vibrant green hues matching Timberborn natural ground cover.
- **Polygon Budget**: 150 – 350 triangles per variant.

### B. Berry Bush: `Plant_Berry` (2 Variants)
- **File Names**:
  - `Plant_Berry_a.fbx`
  - `Plant_Berry_b.fbx`
- **Footprint**: 0.8m × 0.8m spread, height ~0.7m – 0.9m.
- **Pivot**: Ground center ($Z=0$).
- **Aesthetic Direction**:
  - Dense round stylized bush volume with distinct clusters of bright red/purple berries.
  - Reads clearly from god-view camera pitch (30°).
- **Polygon Budget**: 250 – 500 triangles.

### C. Standard Broadleaf Tree: `Plant_TreeOak` (2 Variants)
- **File Names**:
  - `Plant_TreeOak_a.fbx`
  - `Plant_TreeOak_b.fbx`
- **Footprint**: Trunk 0.4m, canopy 1.8m – 2.5m diameter. Height: 3.0m – 4.5m.
- **Pivot**: Base of trunk ($Z=0$).
- **Aesthetic Direction**:
  - Chunky stylized wooden trunk with warm bark tone.
  - Cloud-like faceted foliage volumes (low-poly stylized canopy clumps).
- **Polygon Budget**: 500 – 1,000 triangles.

---

## 3. Delivery Destination
Export production `.fbx` assets directly into:
`a:\dev\simWorld.Host\Assets\Resources\Models\`
