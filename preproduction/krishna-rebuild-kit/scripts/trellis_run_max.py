"""TRELLIS.2 on the approved Krishna front image.

Usage: python trellis_run_max.py PIPELINE_TYPE OUT_NAME
  PIPELINE_TYPE: 1536_cascade or 1024_cascade
  OUT_NAME: output file stem, saved to ~/OUT_NAME.glb
"""

import gc
import json
import os
import shutil
import sys
import time

os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

import torch  # noqa: E402
from huggingface_hub import snapshot_download  # noqa: E402
from PIL import Image  # noqa: E402

pipeline_type = sys.argv[1]
out_name = sys.argv[2]

src = snapshot_download("microsoft/TRELLIS.2-4B")
local = os.path.expanduser("~/trellis2-4b-local")
shutil.rmtree(local, ignore_errors=True)
os.makedirs(local)
for name in os.listdir(src):
    if name != "pipeline.json":
        os.symlink(os.path.join(src, name), os.path.join(local, name))
cfg = json.load(open(os.path.join(src, "pipeline.json")))
cfg["args"]["rembg_model"]["args"]["model_name"] = "ZhengPeng7/BiRefNet"
json.dump(cfg, open(os.path.join(local, "pipeline.json"), "w"), indent=2)

from trellis2.pipelines import Trellis2ImageTo3DPipeline  # noqa: E402
import o_voxel  # noqa: E402

pipe = Trellis2ImageTo3DPipeline.from_pretrained(local)
pipe.cuda()

img = Image.open(os.path.expanduser(os.environ.get("INPUT_IMAGE", "~/krishna_front_clean.png")))
t0 = time.time()
mesh = pipe.run(img, pipeline_type=pipeline_type, seed=1)[0]
print(f"GENERATE_SECONDS {time.time() - t0:.1f}", flush=True)
print("PEAK_VRAM_GB", round(torch.cuda.max_memory_allocated() / 1e9, 2), flush=True)

# Free everything the pipeline still holds on the GPU before the CuMesh steps,
# which allocate outside PyTorch's caching allocator and ran out of memory before.
del pipe
gc.collect()
torch.cuda.empty_cache()
print("VRAM_FREE_GB_BEFORE_SIMPLIFY", round(torch.cuda.mem_get_info()[0] / 1e9, 2), flush=True)

mesh.simplify(16777216)
gc.collect()
torch.cuda.empty_cache()

glb = o_voxel.postprocess.to_glb(
    vertices=mesh.vertices,
    faces=mesh.faces,
    attr_volume=mesh.attrs,
    coords=mesh.coords,
    attr_layout=mesh.layout,
    voxel_size=mesh.voxel_size,
    aabb=[[-0.5, -0.5, -0.5], [0.5, 0.5, 0.5]],
    decimation_target=500000,
    texture_size=2048,
    remesh=True,
    remesh_band=1,
    remesh_project=0,
    verbose=True,
)
out = os.path.expanduser(f"~/{out_name}.glb")
glb.export(out, extension_webp=True)
print("SAVED", out, os.path.getsize(out), flush=True)
print("RUN_DONE", flush=True)
