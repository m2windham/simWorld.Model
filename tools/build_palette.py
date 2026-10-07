"""Build palette/palette.png and palette/palette.json from palette/palette.toml.

    uv run python tools/build_palette.py

The PNG is the one texture the game uses. The JSON tells the Blender-side painter where each
swatch's shade cells sit in UV space (cell centres), plus each swatch's register.
"""

import colorsys
import json
import tomllib
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
PALETTE = ROOT / "palette"


def hex_rgb(s: str) -> tuple[float, float, float]:
    s = s.lstrip("#")
    return tuple(int(s[i : i + 2], 16) / 255 for i in (0, 2, 4))


def shade(rgb: tuple[float, float, float], delta: float) -> tuple[int, int, int]:
    h, s, v = colorsys.rgb_to_hsv(*rgb)
    v = min(1.0, max(0.0, v + delta))
    # Lighter shades lose a little saturation and darker ones gain a little, like paint
    # rather than a dimmer.
    s = min(1.0, max(0.0, s - delta * 0.5))
    return tuple(round(c * 255) for c in colorsys.hsv_to_rgb(h, s, v))


def main() -> None:
    spec = tomllib.loads((PALETTE / "palette.toml").read_text(encoding="utf-8"))
    cell, cols, shades = spec["atlas"]["cell_px"], spec["atlas"]["cols"], spec["atlas"]["shades"]
    if shades > cols:
        raise ValueError("shades must fit in one row")
    swatches = spec["swatch"]
    # Terrain swatches are JSON-only (atlas = false): the host paints ground from host.json, and
    # keeping them out of the atlas means existing mesh UVs never move when terrain is tuned.
    atlas_swatches = {n: s for n, s in swatches.items() if s.get("atlas", True)}
    rows = int(spec["atlas"].get("rows", len(atlas_swatches)))
    if len(atlas_swatches) > rows:
        raise ValueError(
            f"{len(atlas_swatches)} atlas swatches do not fit in {rows} rows; "
            "raise atlas.rows and regenerate everything"
        )
    width, height = cols * cell, rows * cell
    img = Image.new("RGB", (width, height), (255, 0, 255))
    index: dict[str, dict] = {}

    for row, (name, sw) in enumerate(atlas_swatches.items()):
        register = sw["register"]
        spread = spec["registers"][register]["spread"]
        base = hex_rgb(sw["rgb"])
        uvs = []
        for i in range(shades):
            t = (i - (shades - 1) / 2) / ((shades - 1) / 2)  # -1 .. 1
            colour = shade(base, t * spread)
            x0, y0 = i * cell, row * cell
            for px in range(x0, x0 + cell):
                for py in range(y0, y0 + cell):
                    img.putpixel((px, py), colour)
            # Blender/Unity UV origin is bottom-left; PIL's is top-left.
            uvs.append([(x0 + cell / 2) / width, 1 - (y0 + cell / 2) / height])
        index[name] = {"register": register, "uvs": uvs}

    img.save(PALETTE / "palette.png")
    (PALETTE / "palette.json").write_text(
        json.dumps({"size": [width, height], "cell_px": cell, "swatches": index}, indent=2)
    )
    # The host's copy (delivered as Assets/Art/Palette/palette.json): every swatch's base colour
    # as hex, plus the core terrain defName -> swatch map, so no colour lives in host code.
    terrain = spec.get("terrain", {})
    missing = sorted(set(terrain.values()) - set(swatches))
    if missing:
        raise ValueError(f"[terrain] names swatches that do not exist: {missing}")
    host = {
        "version": 1,
        "swatches": {name: sw["rgb"].upper() for name, sw in swatches.items()},
        "registers": {name: sw["register"] for name, sw in swatches.items()},
        "terrain": terrain,
    }
    (PALETTE / "host.json").write_text(json.dumps(host, indent=2))
    print(
        f"palette.png {width}x{height}, {len(atlas_swatches)} atlas swatches x {shades} shades; "
        f"host.json {len(swatches)} swatches, {len(terrain)} terrain defNames"
    )


if __name__ == "__main__":
    main()
