# Production Order 005: Scalable Multi-Era Dwellings & Civic Architecture

> **Priority**: 🟡 P2 — Multi-Era Civilization Progression  
> **Target Consumer**: [`m2windham/simWorld.Host`](file:///a:/dev/simWorld.Host) (`Assets/Resources/Models/`)  
> **Order Status**: **READY FOR ASSIGNMENT**  
> **Assigned Team**: `simWorld.Model` 3D Studio  
> **Aesthetic Standard**: Timberborn-inspired stylized realism (warm wood, chunky legible silhouettes, soft lighting, 1m metric grid).  

---

## 1. Architectural Mandate & Scaling Strategy

In `simWorld`, housing represents the physical heartbeat and visual identity of a settlement as it advances through technological eras. Because the game will progress through numerous technological epochs—from the earliest prehistoric hunter-gatherers up through the Industrial era and beyond—the 3D building pipeline **must scale systematically without code collapse**.

### Core Invariants & Rules of Engagement
1. **Unified Footprint & Metric Contract**:
   - Standard dwelling footprint: **4.0m (Width) × 5.0m (Depth)** (within ±8% organic variation).
   - Occupies a clean **4 × 5 cell bounding box** on the simulation's 1-meter integer grid.
   - Ground contact strictly at **$Z_{\min} = 0.000\text{m}$** (no floating geometry, no deep sub-surface protrusion).
   - Pivot: Ground-centered $(X=0, Y=0, Z=0)$.
2. **Watertight 2-Manifold Topology**:
   - 100% closed, watertight 2-manifold geometry (zero non-manifold edges, zero degenerate zero-area faces).
   - Clean bevels or weighted normals on primary structural edges to catch specular cross-light at god zoom.
3. **Deterministic 4-Variant System**:
   - Every technological era provides **4 distinct variants** (`_a`, `_b`, `_c`, `_d`).
   - Selected in host engine deterministically via `ThingId % variantCount` (pure function, 0 random rolls).
4. **4-Stage Construction Protocol (Seam Invariant)**:
   - Every dwelling family supports a 4-stage visual construction sequence:
     * `_stage0`: Foundation pegs, rope trenching, excavated turf/dirt ($0\% - 15\%$ build progress).
     * `_stage1`: Main load-bearing upright posts, timber armature, or stone foundation socle ($15\% - 50\%$).
     * `_stage2`: Wall framing, rafters, rough daub / masonry shell ($50\% - 85\%$).
     * Completed (`_a`..`_d`): Full finished dwelling with weatherproofing, doors, and functional details ($100\%$).
   - Fallback seam safety: If a specific `_stageX` model is not yet authored, the host falls back gracefully to `_stage0` or the completed mesh, never halting the simulation.

---

## 2. Universal Naming & Taxonomy Standard

To prevent naming collisions across hundreds of buildings, all assets adhere to this formula:

$$\mathbf{AssetFileName} = \mathbf{Category}\_\mathbf{Era}\_\mathbf{Variant}.\mathbf{fbx}$$

$$\mathbf{ConstructionFileName} = \mathbf{Category}\_\mathbf{Era}\_\mathbf{stage}\{\mathbf{0,1,2}\}.\mathbf{fbx}$$

### Category Prefixes
- `House`: Residential dwellings & shelter huts
- `Storage`: Resource sheds, granaries, warehouses
- `Workshop`: Crafting huts, smithies, bakeries, factories
- `Civic`: Meeting halls, shrines, temples, town halls
- `Defense`: Palisade gates, watchtowers, bastions

---

## 3. The Multi-Era Progression Roadmap

| Era Index | Historical Epoch | Primary Hero Materials | Stylized Architectural Language | Poly Budget (Completed) |
| :--- | :--- | :--- | :--- | :--- |
| **Era 0** | **Paleolithic** | Mammoth bone/tusks, pine poles, cured hides | Mezhyrich bone domes, conical pelt lean-tos, brush shelters | 400 – 900 tris |
| **Era 1** | **Mesolithic** | Bent hazel/willow saplings, reed thatch, turf | Sunk pit-dwellings, reed thatch domes, bark wigwams | 500 – 1,100 tris |
| **Era 2** | **Neolithic** | Timber post-and-beam, wattle & daub, dry-stone | Rectangular longhouses, mudbrick dwellings, stilt lake huts | 700 – 1,500 tris |
| **Era 3** | **Chalcolithic (Copper)** | Adobe bricks, stone plinths, copper vent fittings | Whitewashed adobe, apsidal smelting hearths, courtyard homes | 800 – 1,800 tris |
| **Era 4** | **Bronze Age** | Timber frames, cyclopean masonry, clay tiles | Multi-room stone-base farmsteads, Aegean courtyard compounds | 1,000 – 2,200 tris |
| **Era 5** | **Iron Age** | Split-log timber, dry-stack granite, conical thatch | Celtic wattle roundhouses, timber mead halls, proto-insulae | 1,200 – 2,400 tris |
| **Era 6** | **Medieval** | Half-timbered oak, lime plaster, slate/tile roofs | Cruck houses, overhang jetties, dormer gables, stone cottages | 1,500 – 2,800 tris |
| **Era 7** | **Early Modern** | Flemish brickwork, lime mortar, central chimneys | Tiled townhouses, brick gable farmsteads, mullioned windows | 1,800 – 3,200 tris |
| **Era 8** | **Industrial** | Red brick, cast-iron girders, slate roofs, steam vents | Terraced worker rowhouses, tenement blocks, dock warehouses | 2,000 – 3,500 tris |
| **Era 9+** | **Modern & Beyond** | Reinforced concrete, steel framing, plate glass | Modular residential blocks, modern homesteads | 2,000 – 4,000 tris |

---

## 4. Phase 1 Execution Batch: Ancient Eras (16 Models)

The first batch implements 4 variants each for Eras 0 through 3 (16 models total), establishing the foundational visual progression from nomad survival to early metallurgy.

### Era 0: Paleolithic (`House_Paleo`)
- **`House_Paleo_a.fbx`**: Mammoth Bone & Tusk Dome Shelter (interlocking mandible base, curved tusk arch doorway).
- **`House_Paleo_b.fbx`**: Conical Timber Pole & Pelt Lean-To (heavy wooden tripod, stitched fur pelts, stone anchor skirt).
- **`House_Paleo_c.fbx`**: Mammoth Hide & Branch Teepee / Yurt (steep conical hide tent with smoke vent flap).
- **`House_Paleo_d.fbx`**: Rock-Overhang Timber Post Shelter (slanted timber bough roof supported by rough-hewn branch posts).

### Era 1: Mesolithic (`House_Meso`)
- **`House_Meso_a.fbx`**: Bent Sapling & Reed Thatch Dome Hut (interwoven hazel hoop armature, bundled reed siding).
- **`House_Meso_b.fbx`**: Turf & Peat Sunken Pit-Dwelling (bermed earth banks, low sod roof, timber smoke hole).
- **`House_Meso_c.fbx`**: Birch Bark & Moss Wigwam (overlapping bark shingles secured with cedar root lashing).
- **`House_Meso_d.fbx`**: Riverbank Stilt Platform Hut (raised wooden log stilts, ladder entry, woven wicker walls).

### Era 2: Neolithic (`House_Neo`)
- **`House_Neo_a.fbx`**: Timber Post & Wattle-and-Daub Farmhouse (split-oak posts, clay daub walls, steep wheat thatch roof).
- **`House_Neo_b.fbx`**: Dry-Stone & Mudbrick Rectangular Dwelling (layered fieldstone plinth, sundried mudbrick walls, flat clay terrace roof).
- **`House_Neo_c.fbx`**: Corbelled Dry-Stone Beehive Hut (Skara Brae style subterranean stone walls with turf caps).
- **`House_Neo_d.fbx`**: Raised Timber Stilt Lake-Village House (horizontal log decking, plank walls, split reed roof).

### Era 3: Chalcolithic / Copper Age (`House_Chalco`)
- **`House_Chalco_a.fbx`**: Whitewashed Adobe & Stone-Plinth House (pillared front porch, timber roof timbers, whitewash finish).
- **`House_Chalco_b.fbx`**: Apsidal Roundhouse with Smelting Hearth (curved rear apsidal wall, side furnace stack with copper cowl).
- **`House_Chalco_c.fbx`**: Timber-Plank & Fieldstone Farmstead (masonry corner quoins, heavy timber plank infill).
- **`House_Chalco_d.fbx`**: Sun-Dried Mudbrick Courtyard Dwelling (enclosed small entry court, clay coping).

---

## 5. Delivery Destination
Export production `.fbx` models directly into:
[`a:\dev\simWorld.Host\Assets\Resources\Models\`](file:///a:/dev/simWorld.Host/Assets/Resources/Models/)
