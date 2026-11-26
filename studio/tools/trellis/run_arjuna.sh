#!/bin/bash
# Runs ON the GPU VM. Arjuna 1536 (sai, 20 Nov 2026: "generate 1536 model of arjuna using trellis").
# Inputs in ~/trellis_in/: arjuna_front.png (front_v1 model sheet, upscaled 2x, sharpened, cut out at 1536) and arjuna_bow.png
# (Gandiva prop sheet). Karna take 3 settings: 1536 cascade, 4096 texture, up to 1M faces. Priority order, each GLB saved as
# soon as it is done, so a spot preemption keeps what finished. Log: ~/trellis_out/batch_arjuna.log
source ~/miniforge3/etc/profile.d/conda.sh
conda activate trellis2
cd ~/TRELLIS.2 && cp ~/trellis_one.py ./trellis_one.py
export ATTN_BACKEND=xformers SPARSE_ATTN_BACKEND=xformers
mkdir -p ~/trellis_out; LOG=~/trellis_out/batch_arjuna.log
run() {  # input stem seed
  echo "START $2 seed $3 $(date -u +%H:%M:%S)" >> $LOG
  python trellis_one.py ~/trellis_in/$1.png "$2" 1536_cascade "$3" 4096 1000000 >> $LOG 2>&1
  echo "END $2 seed $3 $(date -u +%H:%M:%S)" >> $LOG
}
run arjuna_front arjuna_front 1
run arjuna_bow arjuna_bow 1
run arjuna_front arjuna_front 2
run arjuna_front arjuna_front 3
echo "ALL_DONE $(date -u +%H:%M:%S)" >> $LOG
