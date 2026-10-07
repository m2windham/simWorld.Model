# Production Order 004: Wooden Architecture & Settlement Furniture

> **Priority**: 🟡 P2 — Core Civilization Construction  
> **Target Consumer**: [`m2windham/simWorld.Host`](file:///a:/dev/simWorld.Host) (`Assets/Resources/Models/`)  
> **Order Status**: **READY FOR ASSIGNMENT**  
> **Assigned Team**: `simWorld.Model` 3D Studio  

---

## 1. Context & Motivation

Wood is the hero material of the Timberborn visual identity. The host currently has stone walls (`WallGranite`, `WallSandstone`, `WallLimestone`), but lacks basic wooden timber structures (`WallWood`, `DoorWood`, `Bed`, `Campfire`).

---

## 2. Deliverables Specification

### A. Wooden Wall: `WallWood` (2 Variants)
- **File Names**:
  - `WallWood_a.fbx`
  - `WallWood_b.fbx`
- **Footprint**: 1.0m (X) × 1.0m (Z) grid cell. Height: 1.0m (Y).
- **Pivot**: Corner-aligned ($Z=0$, $X=\text{Min}$, $Y=0$) or centered on 1x1 bottom.
- **Aesthetic Direction**: Horizontal interlocking timber logs with chinking or vertical timber planks with wooden support beams. Chunky, warm amber/brown wood.
- **Polygon Budget**: 250 – 500 triangles per variant.

### B. Wooden Doorway: `DoorWood`
- **File Name**: `DoorWood.fbx`
- **Footprint**: 1.0m (X) × 1.0m (Z) × 1.0m (Y).
- **Aesthetic Direction**: Wooden door frame with heavy plank door, iron/stone hinges.
- **Polygon Budget**: 300 – 600 triangles.

### C. Campfire: `Campfire`
- **File Name**: `Campfire.fbx`
- **Footprint**: 0.8m diameter ring of river stones with charred firewood logs inside.
- **Polygon Budget**: 250 – 450 triangles.

### D. Simple Bed: `Bed`
- **File Name**: `Bed.fbx`
- **Footprint**: 1.0m × 2.0m (occupies 1x2 cells). Height ~0.4m.
- **Aesthetic Direction**: Low-poly wooden post frame with coarse linen / hide mattress and pillow roll.
- **Polygon Budget**: 250 – 500 triangles.

---

## 3. Delivery Destination
Export production `.fbx` assets directly into:
`a:\dev\simWorld.Host\Assets\Resources\Models\`
