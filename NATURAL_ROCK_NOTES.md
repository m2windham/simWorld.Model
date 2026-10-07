# `natural_rock` — what landed, and the pipeline defects found on the way

Added for SimWorld, whose settlement interiors are mostly rock: one measured 200x200 map held
**12,991 rock instances**. That makes this the one generator whose polygon count decides frame
time.

## Usage

```powershell
python run_pipeline.py --name Granite_a --archetype natural_rock --dimensions 1.0 1.0 1.0 --seed 1 --prompt "Rough grey granite rock face"
```

`--seed` is new and is plumbed through `run_pipeline.py` -> `blender_worker.py` ->
`generator_kwargs`. Existing generators absorb it via `**kwargs`, so nothing else changed
behaviour. `natural_rock` and the previously-unreachable `modular_column` were both added to the
`--archetype` choices.

Same seed always gives the same rock. That is deliberate: a variant that drifted between runs
would mean the host's `Granite_a` stopped matching the `Granite_a` it shipped with.

## Verified

Four variants at seeds 1-4, measured with trimesh:

| | tris | extents | silhouette delta vs others |
| --- | --- | --- | --- |
| `Granite_a` | 242 | 1.000 x 1.000 x 1.000 | 0.032 / 0.045 |
| `Granite_b` | 256 | 1.000 x 1.000 x 1.000 | 0.032 / 0.036 |
| `Granite_c` | 242 | 1.000 x 1.000 x 1.000 | 0.045 / 0.036 |
| `Granite_d` | 248 | 1.000 x 1.000 x 1.000 | — |

Extents land on the requested cell **exactly**, because the mesh is fitted to bounds after
displacement rather than clamped during it. Seeds produce a real 3-4.5% silhouette difference, so
variants are genuinely different rocks and not one rock renamed.

## FIXED: the micro-bevel was inflating displaced meshes about 8x

`NormalProcessor.process` ran a BEVEL modifier at `segments = 2` on every edge sharper than 30
degrees. On hard-surface architecture that is a handful of edges and costs nothing. On a displaced
natural mass **every** edge qualifies, so the generator's ~100 triangles were leaving the refinery
as ~800.

`process()` now takes `bevel_segments`, **defaulting to 2 so every asset generated before this is
byte-for-byte unaffected**, and skips the bevel entirely at 0. `blender_worker` passes 0 for
`natural_rock` only. A displaced rock does not need micro-bevels: its facets already *are* the
silhouette, and the weighted-normal pass still gives the shading.

Measured before and after, same seeds:

| | before | after |
| --- | --- | --- |
| triangles per rock | 776 - 830 | **242 - 256** |
| rock at 12,991 instances | 10.4M triangles | **3.14M triangles** |
| `WallGranite` (control, bevel kept) | 52 | 52 |

## STILL OPEN: `--poly_budget` is never applied

`blender_worker.py` parses it, prints it, and **nothing reads it again**. There is no decimate step
anywhere in the pipeline. Every mention of a polygon budget in the docs is aspirational.

Not fixed here because it is a general change affecting every archetype, and rock — the case that
made it urgent — is now inside budget without it. The fix is a decimate modifier after the bevel
targeting the requested count.

## Also worth knowing

- `modular_wall` takes its depth from `--thickness`, not from the second `--dimensions` value, but
  the orchestrator validates against the dimensions you passed. So a wall fails the pre-flight
  gate unless `--thickness` equals the depth you asked for. Pass them matching.
- `prop_medieval_home` adds fixed roof overhang — 1.83 m actual on 1.0 m requested — so it cannot
  hit grid-cell bounds. Use `prop_crate` for anything that must fit one cell.
- `--prompt` does not affect geometry or materials in the headless CLI. Steps 1-2 of the 8-step
  protocol (concept generation, visual sign-off) are Antigravity agent steps; the CLI runs 3-8,
  which are driven entirely by `--archetype`, `--dimensions` and `--seed`. Five walls generated
  from five different prompts are five identical boxes, so material identity has to come from
  per-defName materials on the engine side.
- Every `_Normal_GL.png` and `_Normal_DX.png` in `output/models/textures/` is currently the same
  file (identical MD5 across every asset) — the bake produces no surface detail. ORM maps do differ
  per asset.
- Exported GLB extents are Y-up (glTF convention) while Blender is Z-up, so a 1 x 1 x 2.5 wall
  measures `[1, 2.5, 1]` when loaded with trimesh. Expected, not a defect; the FBX import handles
  it on the Unity side.
