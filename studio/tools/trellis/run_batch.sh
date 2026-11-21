#!/bin/bash
# Runs ON the GPU VM. One model per input in ~/trellis_in/*.png, one at a time, each saved as soon as it is done.
# 1536 cascade first; if it fails or writes nothing, 1024 cascade for that input only. Log: ~/trellis_out/batch.log
source ~/miniforge3/etc/profile.d/conda.sh
conda activate trellis2
cd ~/TRELLIS.2 && cp ~/trellis_one.py ./trellis_one.py
export ATTN_BACKEND=xformers SPARSE_ATTN_BACKEND=xformers
mkdir -p ~/trellis_out; LOG=~/trellis_out/batch.log
for f in ~/trellis_in/*.png; do
  stem=$(basename "$f" .png)
  echo "START $stem 1536 $(date -u +%H:%M:%S)" >> $LOG
  python trellis_one.py "$f" "$stem" 1536_cascade >> $LOG 2>&1
  if [ ! -s ~/trellis_out/${stem}_1536.glb ]; then
    echo "FALLBACK $stem 1024 $(date -u +%H:%M:%S)" >> $LOG
    python trellis_one.py "$f" "$stem" 1024_cascade >> $LOG 2>&1
  fi
  echo "END $stem $(date -u +%H:%M:%S)" >> $LOG
done
echo "ALL_DONE $(date -u +%H:%M:%S)" >> $LOG
