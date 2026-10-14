#!/bin/bash
# Run TRELLIS.2 on the head image: 1536 cascade first, 1024 cascade if it fails. Logs to ~/run_head.log.
source ~/miniforge3/etc/profile.d/conda.sh
conda activate trellis2
cd ~/TRELLIS.2
cp ~/trellis_run_max.py ~/TRELLIS.2/trellis_run_max.py
export ATTN_BACKEND=xformers
export SPARSE_ATTN_BACKEND=xformers
export INPUT_IMAGE=~/krishna_head.png
rm -f ~/krishna_head_1536.glb ~/krishna_head_1024.glb ~/run_head.log
echo "START_1536 $(date -u +%H:%M:%S)" >> ~/run_head.log
python trellis_run_max.py 1536_cascade krishna_head_1536 >> ~/run_head.log 2>&1
RC1=$?
echo "END_1536 rc=$RC1 $(date -u +%H:%M:%S)" >> ~/run_head.log
if [ $RC1 -ne 0 ] || [ ! -s ~/krishna_head_1536.glb ]; then
  echo "FALLBACK_1024 $(date -u +%H:%M:%S)" >> ~/run_head.log
  python trellis_run_max.py 1024_cascade krishna_head_1024 >> ~/run_head.log 2>&1
  echo "END_1024 rc=$? $(date -u +%H:%M:%S)" >> ~/run_head.log
fi
echo "ALL_DONE $(date -u +%H:%M:%S)" >> ~/run_head.log