"""
Batch Generator for Multi-Era Dwellings (16 Models across 4 Ancient Eras)
Executes headless Blender generation for all 16 variants and copies production FBX assets
directly into simWorld.Host/Assets/Resources/Models/.
"""

import shutil
import subprocess
import sys
from pathlib import Path

# Paths
MODEL_ROOT = Path(__file__).resolve().parent.parent
BLENDER_EXE = Path("C:/Program Files/Blender Foundation/Blender 4.5/blender.exe")
WORKER_SCRIPT = MODEL_ROOT / "pipeline" / "blender_worker.py"
OUTPUT_DIR = MODEL_ROOT / "output" / "models"
HOST_MODELS_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "simWorld.Host"
    / "Assets"
    / "Resources"
    / "Models"
)

MODELS = [
    # Paleolithic
    {
        "name": "House_Paleo_a",
        "archetype": "paleo_home_a",
        "w": 4.0,
        "d": 5.0,
        "h": 3.8,
        "poly": 900,
    },
    {
        "name": "House_Paleo_b",
        "archetype": "paleo_home_b",
        "w": 4.0,
        "d": 5.0,
        "h": 3.6,
        "poly": 800,
    },
    {
        "name": "House_Paleo_c",
        "archetype": "paleo_home_c",
        "w": 4.0,
        "d": 5.0,
        "h": 3.8,
        "poly": 900,
    },
    {
        "name": "House_Paleo_d",
        "archetype": "paleo_home_d",
        "w": 4.0,
        "d": 5.0,
        "h": 3.4,
        "poly": 850,
    },
    # Mesolithic
    {"name": "House_Meso_a", "archetype": "meso_home_a", "w": 4.0, "d": 5.0, "h": 3.5, "poly": 950},
    {"name": "House_Meso_b", "archetype": "meso_home_b", "w": 4.0, "d": 5.0, "h": 3.2, "poly": 900},
    {"name": "House_Meso_c", "archetype": "meso_home_c", "w": 4.0, "d": 5.0, "h": 3.3, "poly": 950},
    {
        "name": "House_Meso_d",
        "archetype": "meso_home_d",
        "w": 4.0,
        "d": 5.0,
        "h": 3.4,
        "poly": 1000,
    },
    # Neolithic
    {"name": "House_Neo_a", "archetype": "neo_home_a", "w": 4.0, "d": 5.0, "h": 3.8, "poly": 1200},
    {"name": "House_Neo_b", "archetype": "neo_home_b", "w": 4.0, "d": 5.0, "h": 3.5, "poly": 1100},
    {"name": "House_Neo_c", "archetype": "neo_home_c", "w": 4.0, "d": 5.0, "h": 3.6, "poly": 1150},
    {"name": "House_Neo_d", "archetype": "neo_home_d", "w": 4.0, "d": 5.0, "h": 3.7, "poly": 1250},
    # Chalcolithic / Copper
    {
        "name": "House_Chalco_a",
        "archetype": "chalco_home_a",
        "w": 4.0,
        "d": 5.0,
        "h": 3.8,
        "poly": 1400,
    },
    {
        "name": "House_Chalco_b",
        "archetype": "chalco_home_b",
        "w": 4.0,
        "d": 5.0,
        "h": 3.6,
        "poly": 1350,
    },
    {
        "name": "House_Chalco_c",
        "archetype": "chalco_home_c",
        "w": 4.0,
        "d": 5.0,
        "h": 3.7,
        "poly": 1400,
    },
    {
        "name": "House_Chalco_d",
        "archetype": "chalco_home_d",
        "w": 4.0,
        "d": 5.0,
        "h": 3.2,
        "poly": 1200,
    },
]


def run_batch(deliver_to_host: bool = True):
    print("=======================================================")
    print(f"[Batch Generator] Generating {len(MODELS)} Ancient Era Dwelling Models")
    print("=======================================================\n")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if deliver_to_host:
        HOST_MODELS_DIR.mkdir(parents=True, exist_ok=True)

    success_count = 0
    for idx, m in enumerate(MODELS, 1):
        print(f"[{idx}/{len(MODELS)}] Generating {m['name']} (Archetype: {m['archetype']})...")
        cmd = [
            str(BLENDER_EXE),
            "-b",
            "-P",
            str(WORKER_SCRIPT),
            "--",
            "--archetype",
            m["archetype"],
            "--name",
            m["name"],
            "--width",
            str(m["w"]),
            "--depth",
            str(m["d"]),
            "--height",
            str(m["h"]),
            "--poly_budget",
            str(m["poly"]),
            "--out_dir",
            str(OUTPUT_DIR),
            "--skip_renders",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"  [ERROR] Generation failed for {m['name']}:\n{res.stderr[-500:]}")
            continue

        fbx_path = OUTPUT_DIR / f"{m['name']}.fbx"
        if fbx_path.exists():
            success_count += 1
            print(f"  [SUCCESS] Created {fbx_path.name} ({fbx_path.stat().st_size / 1024:.1f} KB)")
            if deliver_to_host:
                dst = HOST_MODELS_DIR / fbx_path.name
                shutil.copy2(fbx_path, dst)
                print(f"  -> Delivered to {dst}")
        else:
            print(f"  [WARN] FBX file not found: {fbx_path}")

    print("\n=======================================================")
    print(
        f"[Batch Generator Complete] {success_count}/{len(MODELS)} models generated successfully."
    )
    print("=======================================================\n")


if __name__ == "__main__":
    deliver = "--deliver" in sys.argv or "-d" in sys.argv
    run_batch(deliver_to_host=deliver)
