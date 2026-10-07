"""
Hardware Detection and Cycles AMD HIP Acceleration Utility
Configures Blender Cycles compute devices for AMD Radeon RX 6650 XT with CPU fallback.
Provides socket health check for live blender-mcp session.
"""

import socket
import sys


def configure_cycles_hardware_acceleration(scene=None) -> str:
    """
    Configures Blender Cycles to utilize AMD HIP hardware acceleration on RDNA2 GPUs
    (e.g., AMD Radeon RX 6650 XT) with graceful multi-threaded CPU fallback.

    Args:
        scene: Optional bpy.types.Scene. If None, uses bpy.context.scene.

    Returns:
        str: 'HIP_GPU' if AMD HIP was configured, or 'CPU_FALLBACK' if fallback was used.
    """
    try:
        import bpy
    except ImportError:
        return "NO_BPY_CONTEXT"

    scene = scene or bpy.context.scene
    scene.render.engine = "CYCLES"

    cycles_addon = bpy.context.preferences.addons.get("cycles")
    if not cycles_addon:
        try:
            bpy.ops.preferences.addon_enable(module="cycles")
            cycles_addon = bpy.context.preferences.addons["cycles"]
        except Exception as e:
            print(f"[Hardware Warning] Could not enable cycles addon: {e}", file=sys.stderr)
            scene.cycles.device = "CPU"
            return "CPU_FALLBACK"

    cprefs = cycles_addon.preferences

    try:
        # Request HIP compute device backend
        cprefs.compute_device_type = "HIP"
        # Force refresh of available compute devices
        cprefs.get_devices()

        hip_devices = [d for d in cprefs.devices if d.type == "HIP"]

        if not hip_devices:
            raise RuntimeError("No AMD HIP compute devices discovered by Blender.")

        print(f"[Hardware] Discovered {len(hip_devices)} AMD HIP device(s):")
        for d in cprefs.devices:
            if d.type == "HIP":
                d.use = True
                print(f"  -> ENABLED: {d.name} (Type: {d.type})")
            else:
                d.use = False

        scene.cycles.device = "GPU"
        scene.cycles.tile_size = 512
        scene.cycles.use_denoising = True
        scene.cycles.denoiser = "OPENIMAGEDENOISE"
        print("[Hardware] AMD HIP hardware acceleration active.")
        return "HIP_GPU"

    except Exception as exc:
        print(
            f"[Hardware Warning] HIP initialization failed ({exc}). Falling back to multi-threaded CPU.",
            file=sys.stderr,
        )
        cprefs.compute_device_type = "NONE"
        scene.cycles.device = "CPU"
        scene.render.threads_mode = "AUTO"
        return "CPU_FALLBACK"


def is_blender_mcp_alive(host: str = "localhost", port: int = 9876, timeout: float = 1.0) -> bool:
    """
    Performs a non-blocking TCP socket ping to check if a live Blender GUI session
    is running the blender-mcp server.

    Args:
        host: Host address (default: 'localhost')
        port: Port number (default: 9876)
        timeout: Socket timeout in seconds

    Returns:
        bool: True if blender-mcp is reachable, False otherwise.
    """
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (TimeoutError, ConnectionRefusedError, OSError):
        return False


if __name__ == "__main__":
    mcp_status = is_blender_mcp_alive()
    print(f"[Hardware Diagnostic] blender-mcp socket live: {mcp_status}")
