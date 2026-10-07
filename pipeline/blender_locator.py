"""
Blender Binary Path Resolution Utility
Locates blender.exe on Windows across environment variables, PATH, and standard directories.
"""

import os
import shutil
from pathlib import Path


def resolve_blender_binary() -> str:
    """
    Resolves the absolute path to blender.exe.
    Order of preference:
    1. BLENDER_PATH environment variable
    2. PATH environment variable (shutil.which)
    3. Standard Windows installation directories (4.5 LTS, 4.2 LTS, default)
    4. Local tools path (H:\\tools\\Blender, 5.2 LTS - used only when 4.5 is absent)

    Returns:
        str: Absolute path to blender.exe

    Raises:
        FileNotFoundError: If no valid Blender executable is discovered.
    """
    # 1. Explicit Environment Override
    if env_path := os.getenv("BLENDER_PATH"):
        p = Path(env_path)
        if p.is_file() and p.name.lower() == "blender.exe":
            return str(p)
        if (p / "blender.exe").is_file():
            return str(p / "blender.exe")

    # 2. System PATH
    if path_bin := shutil.which("blender"):
        return path_bin

    # 3. Standard Windows Installation Paths
    candidate_paths = [
        Path(r"C:\Program Files\Blender Foundation\Blender 4.5\blender.exe"),
        Path(r"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe"),
        Path(r"C:\Program Files\Blender Foundation\Blender 4.3\blender.exe"),
        Path(r"C:\Program Files\Blender Foundation\Blender 4.4\blender.exe"),
        Path(r"C:\Program Files\Blender Foundation\Blender\blender.exe"),
        Path(r"H:\tools\Blender\blender.exe"),
        Path(r"C:\Program Files (x86)\Blender Foundation\Blender\blender.exe"),
    ]

    for candidate in candidate_paths:
        if candidate.is_file():
            return str(candidate)

    raise FileNotFoundError(
        "Could not locate blender.exe. Please install Blender 4.5 LTS or set the BLENDER_PATH environment variable."
    )


if __name__ == "__main__":
    try:
        binary = resolve_blender_binary()
        print(f"[BlenderLocator] Found Blender executable: {binary}")
    except FileNotFoundError as e:
        print(f"[BlenderLocator ERROR] {e}")
