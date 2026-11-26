"""Renders the default scene with EEVEE at 960x540 and 8 samples, and prints the time per frame.
Usage: EGL_PLATFORM=surfaceless python3 studio/setup/eevee_test.py out.png
In the cloud (no GPU) EEVEE runs on the CPU through Mesa llvmpipe. The EGL_BAD_MATCH lines it prints are harmless."""
import sys, time
import bpy

bpy.ops.wm.read_factory_settings(use_empty=False)
s = bpy.context.scene
s.render.engine = "BLENDER_EEVEE"
s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage = 960, 540, 100
s.eevee.taa_render_samples = 8
s.render.filepath = sys.argv[-1]
for i in range(3):
    t = time.time()
    bpy.ops.render.render(write_still=True)
    print(f"EEVEE frame {i + 1}: {time.time() - t:.1f} s")
