"""Runs ON the GPU VM. TRELLIS.2 on one prepared image -> one GLB. Based on preproduction/krishna-rebuild-kit/scripts/trellis_run_max.py.

  python trellis_one.py INPUT_PNG OUT_STEM [1536_cascade|1024_cascade]
Writes ~/trellis_out/OUT_STEM_<res>.glb. Never overwrites a file.
"""
import gc, json, os, shutil, sys, time

os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
import torch  # noqa: E402
from huggingface_hub import snapshot_download  # noqa: E402
from PIL import Image  # noqa: E402

inp, stem = os.path.expanduser(sys.argv[1]), sys.argv[2]
ptype = sys.argv[3] if len(sys.argv) > 3 else "1536_cascade"
outdir = os.path.expanduser("~/trellis_out"); os.makedirs(outdir, exist_ok=True)
out = os.path.join(outdir, f"{stem}_{ptype.split('_')[0]}.glb")
if os.path.exists(out):
    sys.exit(f"exists, not overwriting: {out}")

src = snapshot_download("microsoft/TRELLIS.2-4B")
local = os.path.expanduser("~/trellis2-4b-local")
shutil.rmtree(local, ignore_errors=True); os.makedirs(local)
for name in os.listdir(src):
    if name != "pipeline.json":
        os.symlink(os.path.join(src, name), os.path.join(local, name))
cfg = json.load(open(os.path.join(src, "pipeline.json")))
cfg["args"]["rembg_model"]["args"]["model_name"] = "ZhengPeng7/BiRefNet"     # see trellis-vm-setup notes: load in float32
json.dump(cfg, open(os.path.join(local, "pipeline.json"), "w"), indent=2)

from trellis2.pipelines import Trellis2ImageTo3DPipeline  # noqa: E402
import o_voxel  # noqa: E402

pipe = Trellis2ImageTo3DPipeline.from_pretrained(local); pipe.cuda()
t0 = time.time()
mesh = pipe.run(Image.open(inp), pipeline_type=ptype, seed=1)[0]
print(f"GENERATE_SECONDS {time.time() - t0:.1f}", flush=True)
print("PEAK_VRAM_GB", round(torch.cuda.max_memory_allocated() / 1e9, 2), flush=True)
del pipe; gc.collect(); torch.cuda.empty_cache()
mesh.simplify(16777216); gc.collect(); torch.cuda.empty_cache()
glb = o_voxel.postprocess.to_glb(vertices=mesh.vertices, faces=mesh.faces, attr_volume=mesh.attrs, coords=mesh.coords,
                                 attr_layout=mesh.layout, voxel_size=mesh.voxel_size, aabb=[[-0.5, -0.5, -0.5], [0.5, 0.5, 0.5]],
                                 decimation_target=500000, texture_size=2048, remesh=True, remesh_band=1, remesh_project=0, verbose=True)
glb.export(out, extension_webp=True)
print("SAVED", out, os.path.getsize(out), flush=True)
