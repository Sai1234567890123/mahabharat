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
