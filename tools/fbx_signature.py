"""Runs inside Blender: signature of the visual mesh in each FBX given on the command line.

    blender -b --python tools/fbx_signature.py -- <out.json> <a.fbx> <b.fbx> ...

Collision meshes (UCX_*) are ignored. Output maps each path to vertices, faces, extents, volume
and a hash of the rounded, sorted vertex cloud, so two files with the same geometry hash equal.
"""

import hashlib
import json
import sys
from pathlib import Path

import bmesh
import bpy


def signature(objs: list[bpy.types.Object]) -> dict:
    verts, faces, volume = [], 0, 0.0
    lo = [float("inf")] * 3
    hi = [float("-inf")] * 3
    for o in objs:
        mw = o.matrix_world
        for v in o.data.vertices:
            p = mw @ v.co
            verts.append((round(p.x, 4), round(p.y, 4), round(p.z, 4)))
            for i, c in enumerate(p):
                lo[i], hi[i] = min(lo[i], c), max(hi[i], c)
        faces += len(o.data.polygons)
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bm.transform(mw)
        volume += abs(bm.calc_volume(signed=True))
        bm.free()
    verts.sort()
    digest = hashlib.sha256(repr(verts).encode()).hexdigest()[:12]
    return {
        "vertices": len(verts),
        "faces": faces,
        "extents": [round(hi[i] - lo[i], 3) for i in range(3)],
        "volume": round(volume, 4),
        "hash": digest,
    }


def main() -> None:
    args = sys.argv[sys.argv.index("--") + 1 :]
    out, files = Path(args[0]), args[1:]
    result = {}
    for f in files:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        try:
            bpy.ops.import_scene.fbx(filepath=f)
        except Exception as exc:  # report, keep going with the rest of the list
            result[f] = {"error": str(exc)}
            continue
        objs = [o for o in bpy.data.objects if o.type == "MESH" and not o.name.startswith("UCX_")]
        result[f] = signature(objs) if objs else {"error": "no visual mesh"}
    out.write_text(json.dumps(result, indent=2))
    print(f"FBX_SIGNATURES {out}")


if __name__ == "__main__":
    main()
