# Antigravity 3D Modeling Studio (Local Engine)

Welcome to the **simWorld 3D Modeling Studio**. This workspace is configured as an autonomous 3D creation studio powered by Blender 4.5 LTS, Cycles AMD HIP acceleration, and Antigravity 2.0.

## Workspace Capabilities
- **DCC Platform**: Blender 4.5 LTS (`C:\Program Files\Blender Foundation\Blender 4.5\blender.exe`).
- **Hardware Acceleration**: AMD Radeon RX 6650 XT via Cycles HIP compute device + DirectML ONNX.
- **Dual Mode**:
  - **Headless CLI**: Subprocess execution for silent background generation and automated QA.
  - **Live MCP**: Real-time viewport streaming via `blender-mcp` on `localhost:9876`.
- **Target Standards**: Production game-ready assets for Unreal Engine 5, Godot 4, Unity, and WebGL.

## Mandatory New Asset Protocol
Whenever the user asks to build or generate a 3D model, prop, building, or scene:
1. **Always generate and show a visual concept first** via `generate_image` (Nano Banana / Imagen) to get user visual sign-off before writing or executing any 3D scripts.
2. Follow the standardized workflow in `.agents/rules/3d_studio_workflow.md`:
   - **External Anatomical Framing**: Structural ribs/tusks/beams must sweep prominently **outside** the core volume ($R_{\text{frame}} > R_{\text{core}}$) to define silhouette.
   - **Watertight Solid Primitive Architecture**: Every rafter, wedge, and beam must be a closed 2-manifold primitive (`_add_roof_prism`, `_add_slanted_beam`, `_add_box`) with 0 zero-area degenerate triangles.
   - **Grid Bounding Budgeting**: Proportion base envelopes to allow protruding porches and eaves while remaining strictly within the target bounding box $\pm 8\%$.
   - **Ground Plane Flush Alignment**: $Z_{\min} = 0.000\text{m}$ ground contact with articulated foundation perimeter courses.
3. Every asset must pass the **Stage 3.5 Quantitative Pre-Flight Gate** (`pipeline.qa.preflight_validator`) and **Stage 4 Multimodal Vision QA Judge** (`pipeline.qa.vision_evaluator`), producing a passing `vision_qa_report.json`.

## Key CLI Commands
```powershell
# Run full automated generation, pre-flight gate & multimodal vision QA
python run_pipeline.py --name Asset_01 --archetype paleo_home_a --prompt "Mammoth Bone Shelter"

# Run quantitative pre-flight check on an existing mesh
python -m pipeline.qa.preflight_validator output/models/Asset_01.glb

# Render 5-pass diagnostic studio turntable
python -m pipeline.qa.turntable_studio --input output/models/Asset_01.glb --name Asset_01
```
