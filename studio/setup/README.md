# Studio tech stack

These are the tools the twelve-step pipeline in `../pipeline.md` uses. Everything here is free.

| Tool | Pipeline steps | Cloud container | sai's PC |
|---|---|---|---|
| Blender 5.2 (EEVEE, Cycles, Grease Pencil, compositor) | 2, 5, 6, 8, 9, 10, 11 | `bpy` 5.3.0 Python module | installed 5.2: update to 5.3 to open the repo files without data loss |
| EEVEE on the CPU (Mesa llvmpipe, no GPU) | 10 | works: about 3.5 s a frame at 960x540, 8 samples, default scene | GTX 1650 |
| Krita | 3, 5, 6, 9 | not needed (painting is sai's) | `install_pc.ps1` |
| Rhubarb Lip Sync 1.14 | 7 | installed | `install_pc.ps1` |
| FFmpeg, sox | 2, 11, 12 | installed | `install_pc.ps1` (FFmpeg) |
| numpy, scipy, soundfile | 12 (code-made sound) | installed | optional |
| OpenTimelineIO | 2, 12 (edit lists) | installed | optional |
| Unreal Engine 5.8 | 6 (plates only) | no | installed |
| SheepIt client + Java 21 | 10 (free render farm) | no | `install_pc.ps1` (Java; client page opens) |
| TRELLIS.2 / Meshy free | 5 (new meshes) | rented GPU only, with sai's go | no |

**Cloud setup.** The cloud container is wiped when a session ends, so run these first in every new session:

```
bash studio/setup/install_cloud.sh
bash studio/setup/check_stack.sh
```

Before any EEVEE render in the cloud, run `export EGL_PLATFORM=surfaceless`.

**PC setup.** On sai's PC, run this in PowerShell, with Unreal and Blender closed:

```
powershell -ExecutionPolicy Bypass -File studio\setup\install_pc.ps1
```
