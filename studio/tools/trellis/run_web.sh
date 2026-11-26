#!/bin/bash
# Runs ON the GPU VM. Series-look heroes (sai, 2026-11-22: "Yes, all three"): body and high-detail head for Arjuna, Krishna
# and Karna from the web model sheets (gen_model_sheets.py --only web). Same settings as Karna take 3: 1536 cascade, 4096
# texture, up to 1M faces, seed 1. Each GLB is saved as soon as it is done, so a stop or preemption keeps what finished.
# HARD STOP ON THE VM ITSELF: the first line schedules a shutdown, so the VM stops even if the PC sleeps (20 Nov overrun).
# Log: ~/trellis_out/batch_web.log
sudo shutdown -h +${DEADLINE_MIN:-100} "web hero batch deadline"
source ~/miniforge3/etc/profile.d/conda.sh
conda activate trellis2
cd ~/TRELLIS.2 && cp ~/trellis_one.py ./trellis_one.py
export ATTN_BACKEND=xformers SPARSE_ATTN_BACKEND=xformers
mkdir -p ~/trellis_out; LOG=~/trellis_out/batch_web.log
run() {  # input stem seed
  [ -f ~/trellis_in/$1.png ] || { echo "SKIP $1 (no input)" >> $LOG; return; }
  echo "START $2 seed $3 $(date -u +%H:%M:%S)" >> $LOG
  python trellis_one.py ~/trellis_in/$1.png "$2" 1536_cascade "$3" 4096 1000000 >> $LOG 2>&1
  echo "END $2 seed $3 $(date -u +%H:%M:%S)" >> $LOG
}
for hero in arjuna krishna karna; do
  run ${hero}_web_front ${hero}_web_front 1
  run ${hero}_web_head ${hero}_web_head 1
done
echo "ALL_DONE $(date -u +%H:%M:%S)" >> $LOG
sudo shutdown -h +1 "web hero batch done"
