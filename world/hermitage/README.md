# S1E01 `sc01` Vedic Hermitage Set (`world/hermitage`)

Vedic riverbank ashram set for `studio/episodes/s1e01_the_scribe/sc01/` ("The Scribe: Vyasa, Brahma & Ganesha"), built reproducibly via [build_hermitage.py](build_hermitage.py) in Blender 5.2 (EEVEE, `1280×720`) using pure CC0 Poly Haven assets and custom Vedic procedural props.

## Deliverables
- [hermitage_set.blend](hermitage_set.blend) (`32.77 MB`, self-contained packed textures, 12 named `CAM_S01..CAM_S12` cameras)
- [LICENSES.md](LICENSES.md) (100% CC0 1.0 Poly Haven credits + `canon_check.md` compliance log)
- [checks/](checks/) — 12 `1280×720` EEVEE check stills matching [sc01/shots.json](../../studio/episodes/s1e01_the_scribe/sc01/shots.json) & indexed in [sc01/set_cameras.md](../../studio/episodes/s1e01_the_scribe/sc01/set_cameras.md)

## Rebuild / Re-render
```powershell
& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b --python-exit-code 1 --python world/hermitage/build_hermitage.py
```

## Canon & Look Checklist
- Stepped earthen Vedic *Homa Kunda* fire altar with Agni flame tongues and curling rising smoke (`S01`, `S03`, `S06`, `S10`)
- Ancient banyan with CC0 buttress root clusters (`root_cluster_01/02`), wide horizontal boughs, and hanging aerial roots keeping dead-center sky clear above the altar for Brahma's lotus seat (`S03`, `S05`, `S06`)
- Open-doorway *kusa*-grass thatched earthen hut (`Ashram_KusaHut_Root`), misty Malini river bank, and two grazing *chital* spotted deer (`S01`)
- Vyasa (`-X`) and Ganesha (`+X`) symmetrical *kusa* mats, incised palm-leaf (`Talapatra`) bundles, curled birch-bark (`Bhurja-patra`) sheets, cast bronze stylus (`S08`), and glass-free open brass/clay *diya* (`S11`, `S12`)
- `studio/bible.md` EEVEE palette: warm gold key (`#FFC27A`) + cool blue dawn shadow (`#3E5A86`)
