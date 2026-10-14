# GCP GPU guide: setup, generation, and what not to do

This is what we learned running TRELLIS.2 on a Google Cloud GPU for the Krishna mesh. It covers the setup that worked, the mistakes that cost money, and the rules to keep to. No credentials are in this file.

## 1. What we ran

- **VM:** `trellis-l4-1024`, zone `us-central1-a`, machine type g2-standard-8, one NVIDIA L4 (23 GB VRAM).
- **Cost:** about $0.85 per hour (our estimate; check the live price in the console).
- **Model:** TRELLIS.2 (`microsoft/TRELLIS.2-4B`). Its valid pipeline types are `512`, `1024`, `1024_cascade` and `1536_cascade`. There is no 2K option.
- **Result that worked:** the full-body 1536 run took about 166 seconds of generation, with a peak of 4.2 GB VRAM. The head run took about 228 seconds, with a peak of 8.2 GB.

## 2. Rules, learned the hard way

1. **Stop the VM the moment a run finishes.** A stopped VM costs only its disk. A running L4 costs about $0.85 per hour whether it's busy or idle.
2. **Never restore a disk snapshot across zones or regions without a plan.** We restored a 37 GB snapshot in a loop while looking for capacity. Each restore downloaded the whole image and billed as data transfer: about $38 in total. This was our error.
3. **Don't loop retries or search zones automatically.** Stockouts (`ZONE_RESOURCE_POOL_EXHAUSTED`) happen. Retry once later, or ask before trying another zone.
4. **Check GPU quota before you plan a run.** A100 and RTX PRO 6000 quotas were 0 on this project, so those GPUs can't start at all. The L4 worked.
5. **Don't keep idle disks.** A 150 GB disk costs about $15 per month even when the VM is off. Delete disks and snapshots you no longer need, but only after confirming you don't need the files.
6. **Don't put tokens in files or chat.** A Hugging Face token was pasted in chat. Treat it as exposed, revoke it in Hugging Face, and create a new one. Keep tokens in an environment variable on the VM, never in the repo.
7. **Pin library versions.** Transformers 5.x broke the gated DINOv3 path. We pinned transformers 4.57.1, torch 2.6.0 (cu124) and xformers 0.0.29.post2. A `flash_attn` file was truncated, so we moved it aside and used xformers (`ATTN_BACKEND=xformers`, `SPARSE_ATTN_BACKEND=xformers`).
8. **Watch the cost each day.** Check the Billing console in the morning and compare with the day before. Set budget alerts.

## 3. Setup that worked

1. In the console, create the VM in `us-central1-a` with one L4, the Ubuntu 22.04 image, and a boot disk of about 150 GB (the size we used). Use an on-demand machine type (`g2-standard-8`).
2. Start it only when generating. Stop it straight after.
3. On the VM, create a conda env named `trellis2`. Install the pinned versions from rule 7.
4. Set `ATTN_BACKEND=xformers` and `SPARSE_ATTN_BACKEND=xformers`.
5. Log in to Hugging Face with a token in an environment variable (not in a file). Accept the gated model terms first.
6. Use a local copy of the model with the gated background-removal step swapped for an open one (we used BiRefNet).

## 4. Generating a mesh

1. Put a square full-body image on the VM (`~/krishna_fullbody_square.png`).
2. Run `scripts/trellis_run_max.py` with the pipeline type `1536_cascade`. If it fails, fall back to `1024`. Pass the input with `INPUT_IMAGE=...`.
3. Free GPU memory before the mesh step: `del pipe`, `gc.collect()`, `torch.cuda.empty_cache()`. Then `mesh.simplify(16777216)` and `o_voxel.postprocess.to_glb(decimation_target=500000, texture_size=2048, remesh=True, remesh_band=1, remesh_project=0)`.
4. Copy the GLB to your machine with `gcloud compute scp`, check it in Blender, then **stop the VM**.
5. Check the cost in the console before you start the next run.

## 5. What not to use

- **A100 and RTX PRO 6000:** quota 0 on this project.
- **Snapshot restores** across zones or regions for a GPU run.
- **Automatic zone-hopping scripts.**
- **Leaving the VM running** between sessions.
- **Attached extra disks** you don't need.
- **Any credential** in a repo file, a script, or chat.

## 6. Cleanup checklist

- [ ] VM status is TERMINATED
- [ ] No snapshots you don't need
- [ ] Unused disks deleted (after checking the files are saved elsewhere)
- [ ] Budget alert set
- [ ] Hugging Face token revoked if it was pasted anywhere
