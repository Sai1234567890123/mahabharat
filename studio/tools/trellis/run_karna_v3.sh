#!/bin/bash
# Runs ON the GPU VM. Karna take 3 (sai, 17 Nov: "karna is not good, build a high quality 1536 model again").
# Inputs in ~/trellis_in/: karna_front_v3.png (front_v2 upscaled and sharpened) and karna_head_v1.png (head close-up for a
# separate high-detail head, as done for Krishna). Same 1536 cascade, three seeds for the body and two for the head so the best
# can be picked, a 4096 texture and up to 1M faces. Each GLB is saved as soon as it is done. Log: ~/trellis_out/batch_v3.log
source ~/miniforge3/etc/profile.d/conda.sh
conda activate trellis2
cd ~/TRELLIS.2 && cp ~/trellis_one.py ./trellis_one.py
export ATTN_BACKEND=xformers SPARSE_ATTN_BACKEND=xformers
mkdir -p ~/trellis_out; LOG=~/trellis_out/batch_v3.log
run() {  # input stem seed
  echo "START $2 seed $3 $(date -u +%H:%M:%S)" >> $LOG
  python trellis_one.py ~/trellis_in/$1.png "$2" 1536_cascade "$3" 4096 1000000 >> $LOG 2>&1
  echo "END $2 seed $3 $(date -u +%H:%M:%S)" >> $LOG
}
run karna_front_v3 karna_front_v3 2
run karna_head_v1 karna_head_v1 2
run karna_front_v3 karna_front_v3 3
run karna_head_v1 karna_head_v1 3
run karna_front_v3 karna_front_v3 4
echo "ALL_DONE $(date -u +%H:%M:%S)" >> $LOG
