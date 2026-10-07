# simWorld Asset Manifest & Order Switchboard

> **Target Consumer**: [`m2windham/simWorld.Host`](file:///a:/dev/simWorld.Host) (`Assets/Resources/Models/`)  
> **Target Producer**: [`m2windham/simWorld.Model`](file:///a:/dev/simWorld.Model)  
> **Aesthetic Standard**: Timberborn-inspired stylized realism (warm wood, chunky legible silhouettes, soft lighting, metric grid).  
> **Last Updated**: 2026-09-20  

---

## 1. Engine & Ingestion Rules for 3D Artists

1. **Delivery Seam**: Dropping an asset is simply adding an `.fbx` into [`simWorld.Host/Assets/Resources/Models/`](file:///a:/dev/simWorld.Host/Assets/Resources/Models). Zero code changes or registrations required.
2. **Naming Convention**:
   - Must match the exact simulation `defName` (e.g., `Sandstone.fbx`, `WallWood.fbx`).
   - For variant sets, append lowercase single-letter suffixes: `Granite_a.fbx`, `Granite_b.fbx`, `Granite_c.fbx`, `Granite_d.fbx`. Variants are chosen deterministically by `ThingId % variantCount`.
3. **Scale & Metric Alignment**:
   - **1 unit = 1 meter = 1 simulation cell**.
   - Props & items: Ground-centered pivot ($Z=0$, centered $X/Y$).
   - Modular architecture (walls/doors): Corner-aligned or center-aligned on 1x1m cell footprint, height 1.0m (full wall) or 0.08m (floors).
4. **Target Poly Budgets**:
   - Loose props & items: 100 – 400 tris.
   - Natural rocks & boulders: 300 – 800 tris (with micro-bevel / weighted normals).
   - Vegetation & trees: 400 – 1,200 tris.
   - Structures & buildings: 500 – 2,500 tris.

---

## 2. Master Asset Status Board

### Priority 1: High-Volume World Generation Blockers (Immediate Impact)
*These defs currently appear thousands of times per map and render as fallback cubes.*

| DefName | Category | In-Game Count (Measured) | Variants Required | Status | Order File |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `Sandstone` | Natural Rock | **12,989** | 4 (`_a`..`_d`) | ✅ **DELIVERED** | [ORDER_001_NATURE_ROCKS.md](ORDER_001_NATURE_ROCKS.md) |
| `WildPlant` | Flora | **775** | 2-3 (`_a`..`_c`) | ✅ **DELIVERED** | [ORDER_002_FLORA_VEGETATION.md](ORDER_002_FLORA_VEGETATION.md) |
| `Plant_Berry` | Flora / Food | **605** | 2 (`_a`..`_b`) | ✅ **DELIVERED** | [ORDER_002_FLORA_VEGETATION.md](ORDER_002_FLORA_VEGETATION.md) |
| `ChunkGranite` | Loose Stone | 18 | 2 (`_a`..`_b`) | ✅ **DELIVERED** | [ORDER_001_NATURE_ROCKS.md](ORDER_001_NATURE_ROCKS.md) |
| `ChunkLimestone` | Loose Stone | 10 | 2 (`_a`..`_b`) | ✅ **DELIVERED** | [ORDER_001_NATURE_ROCKS.md](ORDER_001_NATURE_ROCKS.md) |
| `ChunkSandstone` | Loose Stone | 6 | 2 (`_a`..`_b`) | ✅ **DELIVERED** | [ORDER_001_NATURE_ROCKS.md](ORDER_001_NATURE_ROCKS.md) |
| `WoodLog` | Raw Material | 2+ | 2 (`_a`, `_b`) | ✅ **DELIVERED** | [ORDER_003_ITEMS_AND_PROPS.md](ORDER_003_ITEMS_AND_PROPS.md) |
| `Bow_Short` | Weapon / Prop | 2+ | 2 (`_a`, `_b`) | ✅ **DELIVERED** | [ORDER_003_ITEMS_AND_PROPS.md](ORDER_003_ITEMS_AND_PROPS.md) |

---

### Priority 2: Primary Architecture & Settlements

| DefName | Description | Variants | Status | Delivered In Host? |
| :--- | :--- | :--- | :--- | :--- |
| `Wall` | Basic generic wall | 1 | ✅ **DELIVERED** | [`Wall.fbx`](file:///a:/dev/simWorld.Host/Assets/Resources/Models/Wall.fbx) |
| `WallGranite` | Granite masonry wall | 1 | ✅ **DELIVERED** | [`WallGranite.fbx`](file:///a:/dev/simWorld.Host/Assets/Resources/Models/WallGranite.fbx) |
| `WallLimestone` | Limestone masonry wall | 1 | ✅ **DELIVERED** | [`WallLimestone.fbx`](file:///a:/dev/simWorld.Host/Assets/Resources/Models/WallLimestone.fbx) |
| `WallSandstone` | Sandstone masonry wall | 1 | ✅ **DELIVERED** | [`WallSandstone.fbx`](file:///a:/dev/simWorld.Host/Assets/Resources/Models/WallSandstone.fbx) |
| `WallWood` | Timber log wall (hero material) | 2 (`_a`, `_b`) | ⏳ **QUEUED** | Missing |
| `Door` | Generic hinged doorway | 1 | ✅ **DELIVERED** | [`Door.fbx`](file:///a:/dev/simWorld.Host/Assets/Resources/Models/Door.fbx) |
| `DoorWood` | Timber plank door | 1 | ⏳ **QUEUED** | Missing |
| `StorageHut` | Small settlement storage building | 1 | ✅ **DELIVERED** | [`StorageHut.fbx`](file:///a:/dev/simWorld.Host/Assets/Resources/Models/StorageHut.fbx) |
| `Campfire` | Fuelled gathering spot / heat | 1 | ⏳ **QUEUED** | Missing |
| `Bed` | Simple wooden frame bed | 1 | ⏳ **QUEUED** | Missing |
| `Table2x2c` | Wooden dining table | 1 | ⏳ **QUEUED** | Missing |
| `Stool` | Wooden dining stool | 1 | ⏳ **QUEUED** | Missing |

---

### Priority 2B: Multi-Era Architecture & Dwellings (Scalable Era Tree)
*Standard 4m x 5m footprint, 4 variants per era, 4-stage construction protocol.*

| DefName / Era | Architectural Language | Variants | Status | Order File |
| :--- | :--- | :--- | :--- | :--- |
| `House_Paleo` | Mammoth bone dome, pelt lean-to, hide yurt, rock shelter | 4 (`_a`..`_d`) | ✅ **DELIVERED** | [ORDER_005_MULTI_ERA_DWELLINGS.md](ORDER_005_MULTI_ERA_DWELLINGS.md) |
| `House_Meso` | Reed thatch dome, sunken turf pit, bark wigwam, stilt hut | 4 (`_a`..`_d`) | ✅ **DELIVERED** | [ORDER_005_MULTI_ERA_DWELLINGS.md](ORDER_005_MULTI_ERA_DWELLINGS.md) |
| `House_Neo` | Wattle-and-daub, dry-stone mudbrick, beehive, stilt house | 4 (`_a`..`_d`) | ✅ **DELIVERED** | [ORDER_005_MULTI_ERA_DWELLINGS.md](ORDER_005_MULTI_ERA_DWELLINGS.md) |
| `House_Chalco` | Adobe stone-plinth, apsidal hearth, timber-plank, courtyard | 4 (`_a`..`_d`) | ✅ **DELIVERED** | [ORDER_005_MULTI_ERA_DWELLINGS.md](ORDER_005_MULTI_ERA_DWELLINGS.md) |
| `House_Bronze` | Cyclopean longhouse, stone-base farmstead, Aegean court | 4 (`_a`..`_d`) | ⚪ **ROADMAP** | [ORDER_005_MULTI_ERA_DWELLINGS.md](ORDER_005_MULTI_ERA_DWELLINGS.md) |
| `House_Iron` | Conical wattle roundhouse, split-timber hall, proto-insula | 4 (`_a`..`_d`) | ⚪ **ROADMAP** | [ORDER_005_MULTI_ERA_DWELLINGS.md](ORDER_005_MULTI_ERA_DWELLINGS.md) |
| `House_Medieval` | Half-timbered wattle/plaster, cruck house, slate cottage | 4 (`_a`..`_d`) | ⚪ **ROADMAP** | [ORDER_005_MULTI_ERA_DWELLINGS.md](ORDER_005_MULTI_ERA_DWELLINGS.md) |
| `House_Industrial` | Red-brick worker rowhouse, stone tenement, dock shed | 4 (`_a`..`_d`) | ⚪ **ROADMAP** | [ORDER_005_MULTI_ERA_DWELLINGS.md](ORDER_005_MULTI_ERA_DWELLINGS.md) |

---

### Priority 3: Natural Geology & Minerals

| DefName | Description | Variants | Status | Delivered In Host? |
| :--- | :--- | :--- | :--- | :--- |
| `Granite` | Solid granite deposit | 4 (`Granite_a`..`d`) | 🟢 **DELIVERED** | [`Granite_a.fbx`](file:///a:/dev/simWorld.Host/Assets/Resources/Models/Granite_a.fbx) |
| `Limestone` | Solid limestone deposit | 4 (`_a`..`_d`) | 🟡 **QUEUED** | Missing |
| `Slate` | Solid slate deposit | 4 (`_a`..`_d`) | 🟡 **QUEUED** | Missing |
| `Marble` | Solid marble deposit | 4 (`_a`..`_d`) | 🟡 **QUEUED** | Missing |
| `MineableSteel` | Compacted steel vein | 2 (`_a`, `_b`) | 🟢 **DELIVERED** | [`MineableSteel_a.fbx`](file:///a:/dev/simWorld.Host/Assets/Resources/Models/MineableSteel_a.fbx) |
| `MineableGold` | Gold vein | 2 (`_a`, `_b`) | 🟢 **DELIVERED** | [`MineableGold_a.fbx`](file:///a:/dev/simWorld.Host/Assets/Resources/Models/MineableGold_a.fbx) |
| `MineableSilver` | Silver vein | 2 (`_a`, `_b`) | 🟢 **DELIVERED** | [`MineableSilver_a.fbx`](file:///a:/dev/simWorld.Host/Assets/Resources/Models/MineableSilver_a.fbx) |

---

### Priority 4: Trees, Crops & Agriculture

| DefName | Description | Variants / Scale | Status |
| :--- | :--- | :--- | :--- |
| `Plant_TreeOak` | Broadleaf oak tree | 3 (`_a`..`_c`) | 🟡 **QUEUED** |
| `Plant_TreePine` | Conifer evergreen pine | 2 (`_a`..`_b`) | 🟡 **QUEUED** |
| `Plant_TreeBirch` | White-bark birch tree | 2 (`_a`..`_b`) | 🟡 **QUEUED** |
| `Plant_Bush` | Dense leafy shrub | 2 (`_a`..`_b`) | 🟡 **QUEUED** |
| `Plant_Grass` | Tufts of ground grass | 3 (`_a`..`_c`) | 🟡 **QUEUED** |
| `Plant_Corn` | Tall crop stalks | 1 | 🟡 **QUEUED** |
| `Plant_Rice` | Rice crop paddy plant | 1 | 🟡 **QUEUED** |

---

### Priority 5: Characters, Animals & Equipment

| DefName | Description | Requirement | Status |
| :--- | :--- | :--- | :--- |
| `Pawn_Humanoid` | Stylized humanoid settler | Chunky Timberborn proportions, readable silhouette | 🟡 **QUEUED** |
| `Pawn_Boar` | Wild / tamed boar | Low-poly stylized mammal | 🟡 **QUEUED** |
| `Pawn_Deer` | Grazing deer | Elegant low-poly silhouette | 🟡 **QUEUED** |
| `Spear` | Tribal wooden/stone spear | Ground item pickup | 🟡 **QUEUED** |
| `Club` | Wooden melee club | Ground item pickup | 🟡 **QUEUED** |

---

### Priority 6: Environment, Water & Backgrounds

| Asset | Description | Format | Status |
| :--- | :--- | :--- | :--- |
| `Skybox_Timberborn` | Warm-gradient diorama sky / ambient cubemap | HDR / EXR / Skybox Material | 🟡 **QUEUED** |
| `Water_Stylized` | Low-poly river & lake foam/normal shader | URP Shader Graph | 🟡 **QUEUED** |
| `Terrain_Ground` | Hand-painted stylized ground tile textures (Soil, Sand, Gravel) | 1024x1024 Albedo/Normal/ORM | 🟡 **QUEUED** |

---

## 3. Active Orders Index

- [ORDER_001_NATURE_ROCKS.md](ORDER_001_NATURE_ROCKS.md) — Sandstone variants & loose stone chunks (**Blocker: 12,989 map instances**).
- [ORDER_002_FLORA_VEGETATION.md](ORDER_002_FLORA_VEGETATION.md) — Wild plants, berry bushes, and oak trees (**Blocker: 1,380 map instances**).
- [ORDER_003_ITEMS_AND_PROPS.md](ORDER_003_ITEMS_AND_PROPS.md) — Wood logs, bows, spears, and raw resource piles.
- [ORDER_004_WOODEN_ARCHITECTURE.md](ORDER_004_WOODEN_ARCHITECTURE.md) — Timber walls, timber doors, beds, campfires, and tables.
- [ORDER_005_MULTI_ERA_DWELLINGS.md](ORDER_005_MULTI_ERA_DWELLINGS.md) — Scalable multi-era dwellings (16 initial models across 4 ancient eras + future era roadmap).
