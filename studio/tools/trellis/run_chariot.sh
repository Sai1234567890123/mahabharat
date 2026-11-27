#!/bin/bash
# Runs ON the GPU VM. Karna's own chariot (sai, 2026-11-27 "Yes") from the model sheet cast/karna/model/chariot_v1.png
# (gen_model_sheets.py --only chariot). Three seeds of the 1536 cascade so the cleanest car can be picked; 4096 texture, up to 1M
# faces. Each GLB is saved as soon as it is done. HARD STOP ON THE VM ITSELF: the first line schedules a shutdown.
# Log: ~/trellis_out/batch_chariot.log
sudo shutdown -h +${DEADLINE_MIN:-60} "chariot batch deadline"
source ~/miniforge3/etc/profile.d/conda.sh
conda activate trellis2
cd ~/TRELLIS.2 && cp ~/trellis_one.py ./trellis_one.py
export ATTN_BACKEND=xformers SPARSE_ATTN_BACKEND=xformers
mkdir -p ~/trellis_out; LOG=~/trellis_out/batch_chariot.log
run() {  # input stem seed
  [ -f ~/trellis_in/$1.png ] || { echo "SKIP $1 (no input)" >> $LOG; return; }
  echo "START $2 seed $3 $(date -u +%H:%M:%S)" >> $LOG
  python trellis_one.py ~/trellis_in/$1.png "$2_s$3" 1536_cascade "$3" 4096 1000000 >> $LOG 2>&1
  echo "END $2 seed $3 $(date -u +%H:%M:%S)" >> $LOG
}
run karna_chariot karna_chariot 1
run karna_chariot karna_chariot 2
run karna_chariot karna_chariot 3
echo "ALL_DONE $(date -u +%H:%M:%S)" >> $LOG
sudo shutdown -h +1 "chariot batch done"
