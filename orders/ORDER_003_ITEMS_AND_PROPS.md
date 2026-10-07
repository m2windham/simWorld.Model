# Production Order 003: Raw Materials, Items & Equipment

> **Priority**: 🟡 P2 — High Visibility Colony Items  
> **Target Consumer**: [`m2windham/simWorld.Host`](file:///a:/dev/simWorld.Host) (`Assets/Resources/Models/`)  
> **Order Status**: **READY FOR ASSIGNMENT**  
> **Assigned Team**: `simWorld.Model` 3D Studio  

---

## 1. Context & Motivation

When colonists harvest trees or drop items on the ground (raw wood logs, weapons, tools), they render as small generic cubes. Providing stylized items makes stockpiles and work areas immediately identifiable.

---

## 2. Deliverables Specification

### A. Wood Logs: `WoodLog`
- **File Name**: `WoodLog.fbx` (or `WoodLog_a.fbx`, `WoodLog_b.fbx`)
- **Footprint**: Stack of 2-3 stylized chopped wooden logs. Length ~0.8m, width ~0.4m, height ~0.25m.
- **Aesthetic Direction**: Warm timber texture, cut-end growth rings, faceted bark surface. Hero material of Timberborn.
- **Polygon Budget**: 150 – 300 triangles.

### B. Short Bow: `Bow_Short`
- **File Name**: `Bow_Short.fbx`
- **Footprint**: Curved wooden hunting bow resting flat on ground. Length ~0.7m, width ~0.15m.
- **Polygon Budget**: 100 – 200 triangles.

### C. Tribal Spear: `Spear`
- **File Name**: `Spear.fbx`
- **Footprint**: Long wooden shaft with bound stone or flint tip. Length ~1.2m.
- **Polygon Budget**: 120 – 220 triangles.

---

## 3. Delivery Destination
Export production `.fbx` assets directly into:
`a:\dev\simWorld.Host\Assets\Resources\Models\`
