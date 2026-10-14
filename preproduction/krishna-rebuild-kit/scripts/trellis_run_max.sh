#!/bin/bash
# trellis_run_max.sh: runs the 1536 cascade first, falls back to the 1024 cascade if it fails.
# Copy trellis_run_max.py to the VM home folder and put the input image at ~/krishna_front_clean.png.
# Run 1536 cascade first; if it fails or saves no file, run 1024 cascade. Logs to ~/run_max.log.
source ~/miniforge3/etc/profile.d/conda.sh
conda activate trellis2
cd ~/TRELLIS.2
cp ~/trellis_run_max.py ~/TRELLIS.2/trellis_run_max.py
export ATTN_BACKEND=xformers
export SPARSE_ATTN_BACKEND=xformers
rm -f ~/krishna_front_1536.glb ~/krishna_front_1024.glb ~/run_max.log
echo "START_1536 $(date -u +%H:%M:%S)" >> ~/run_max.log
python trellis_run_max.py 1536_cascade krishna_front_1536 >> ~/run_max.log 2>&1
RC1=$?
echo "END_1536 rc=$RC1 $(date -u +%H:%M:%S)" >> ~/run_max.log
if [ $RC1 -ne 0 ] || [ ! -s ~/krishna_front_1536.glb ]; then
  echo "FALLBACK_1024 $(date -u +%H:%M:%S)" >> ~/run_max.log
  python trellis_run_max.py 1024_cascade krishna_front_1024 >> ~/run_max.log 2>&1
  RC2=$?
  echo "END_1024 rc=$RC2 $(date -u +%H:%M:%S)" >> ~/run_max.log
fi
echo "ALL_DONE $(date -u +%H:%M:%S)" >> ~/run_max.log
