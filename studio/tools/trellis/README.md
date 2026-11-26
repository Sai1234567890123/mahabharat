# TRELLIS.2 run for the hero models (Gate 3)

Turns approved model sheets into 3D models on the existing spot GPU VM `krk-trellis-l4` (us-central1-a, g2-standard-8 with one L4,
TRELLIS.2 already installed in the conda env `trellis2`). BILLED: the VM costs about $0.25 to $0.30 an hour on spot (about $0.85
on-demand). Needs sai's own approval line. One run at a time. The VM is stopped at the end, success or failure.

## Steps (run from the repo root on the PC)

1. Free: prepare square cut-outs, never overwriting:
   `python studio/tools/trellis/prep_input.py studio/cast/karna/model/front_v2.png studio/cast/karna/model/trellis_in/karna_front.png`
   `python studio/tools/trellis/prep_input.py studio/cast/karna/model/bow_vijaya_v1.png studio/cast/karna/model/trellis_in/karna_bow.png`
2. Start the VM: `gcloud compute instances start krk-trellis-l4 --zone us-central1-a --project cs-project-07zg2j2c`.
   If it reports no capacity or the VM is reclaimed, stop and report. Do not try other zones and do not switch to on-demand.
3. Copy up: `trellis_one.py`, `run_batch.sh` and the two PNGs (into `~/trellis_in/`) with `gcloud compute scp`.
4. Run: `bash ~/run_batch.sh` (in `nohup` or `tmux`), then watch `~/trellis_out/batch.log`. About 8 to 15 minutes a model.
5. Copy back every GLB and `batch.log` into `studio/cast/karna/model/trellis_out/`. If a long copy drops, copy in 4 MB pieces
   with a SHA-256 check (see the trellis-vm notes).
6. Stop the VM and confirm `TERMINATED`: `gcloud compute instances stop krk-trellis-l4 --zone us-central1-a --project cs-project-07zg2j2c`.
7. Log each GLB, the minutes the VM ran and the estimated cost in `studio/log.md`. Do not delete the VM or its disk.

Limits: a 60 minute ceiling from VM start to stop. Never a broad `pkill -f` over SSH (it killed its own session once); kill by PID.
If setup is broken on the VM (missing package, gated model), stop the VM and report instead of repairing it at length.

## Karna take 3 (17 Nov 2026, sai: "karna is not good, build a high quality 1536 model again")

Re-running seed 1 on the same picture would give the same model, so take 3 changes the inputs and the export:

- Inputs (free, already in the repo): `studio/cast/karna/model/trellis_in/karna_front_v3.png` (front_v2 upscaled 2x and
  sharpened) and `karna_head_v1.png` (his head and crown close up, for a separate high-detail head that is joined in Blender).
- `trellis_one.py` now takes seed, texture size and face target: `... 1536_cascade SEED 4096 1000000`.
- Batch: `run_karna_v3.sh`, five models in priority order (body seed 2, head seed 2, body seed 3, head seed 3, body seed 4), each
  saved as soon as it is done, log `~/trellis_out/batch_v3.log`. If the 60 minute ceiling comes first, stop after the model
  that is running and keep what is done.

Steps as above: start the VM, copy `trellis_one.py`, `run_karna_v3.sh` and the two PNGs (into `~/trellis_in/`), run
`bash ~/run_karna_v3.sh` under `nohup`, copy every new GLB and `batch_v3.log` back into `studio/cast/karna/model/trellis_out/`,
stop the VM and confirm TERMINATED, log minutes and cost. Estimate: about 45 minutes of VM time, about $0.25 at the spot rate.

## Arjuna (20 Nov 2026, sai: "generate 1536 model of arjuna using trellis")

Arjuna has no model sheets yet; his locked `cast/arjuna/sheet.png` holds the bow, which TRELLIS.2 would fuse into his hand.
So, as for Karna:

1. BILLED, about $0.21: `python studio/tools/gen_model_sheets.py --project cs-project-07zg2j2c --only arjuna` paints
   `cast/arjuna/model/front_v1.png` (A-pose, empty hands, quiver on his back), `back_v1.png` (Blender guide) and
   `bow_gandiva_v1.png`. Review before step 2.
2. Free: `prep_sharp.py` on front_v1 into `trellis_in/src_front_v1_up2x.png`, then `prep_input.py` on that into
   `trellis_in/arjuna_front.png`, and `prep_input.py` on bow_gandiva_v1 into `trellis_in/arjuna_bow.png`.
3. BILLED, about 35 to 45 min spot VM, about $0.20: steps 2 to 7 above with `run_arjuna.sh` (body seed 1, bow, body seeds 2
   and 3), log `batch_arjuna.log`, GLBs into `studio/cast/arjuna/model/trellis_out/`. Stop the VM and confirm TERMINATED.

## Series-look heroes (22 Nov 2026, sai: "Yes, all three")

3D models of the LOCKED web series hero set, each with a separate high-detail head for the face rig (`tools/blender/face_rig.py`).

1. BILLED, about $0.42: `python studio/tools/gen_model_sheets.py --project cs-project-07zg2j2c --only web` paints
   `cast/<hero>/model/web_front_v1.png` and `web_head_v1.png` for karna, arjuna and krishna. Review before step 2.
2. Free, per hero and view: `prep_sharp.py cast/<hero>/model/web_<view>_v1.png cast/<hero>/model/trellis_in/src_web_<view>_v1_up2x.png`,
   then `prep_input.py` on that into `cast/<hero>/model/trellis_in/<hero>_web_<view>.png`.
3. BILLED: start `krk-trellis-l4`, copy `trellis_one.py`, `run_web.sh` and the six PNGs into `~/trellis_in/`, run
   `DEADLINE_MIN=100 nohup bash ~/run_web.sh &`. The script schedules `shutdown -h` on the VM itself before anything else,
   so the VM stops by the deadline even if the PC sleeps. Six models at 1536, about 8 to 15 min each: 50 to 90 min,
   about $0.45 on spot or about $1.30 on-demand. Copy back each GLB and `batch_web.log` into
   `studio/cast/<hero>/model/trellis_out/`, confirm the VM is TERMINATED, log minutes and cost. Never delete the VM or disk.
