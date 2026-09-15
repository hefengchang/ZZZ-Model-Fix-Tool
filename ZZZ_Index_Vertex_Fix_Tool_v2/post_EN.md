# ZZZ Index & Vertex Fix Tool v2

A standalone repair tool for Zenless Zone Zero mods. It fixes the two things that break after a game update:

- **Bent legs / collapsed or twisted models** (textures still look fine) — wrong bone indices inside `blend.buf`
- **Scrambled textures** (model shape still perfect) — the vertex format in `texcoord.buf` no longer matches the game

Plus a one-click **Universal Face Fix** for the faces broken by the 3.1 → 3.2 update.

Chinese and English UI. Type `lang` in the window to switch at any time. Everything is backed up before anything is written, and one keystroke restores it.

**The package ships with a set of ready-made references** for common meshes — those work out of the box. Anything not covered, you capture yourself with **gui_collect** in a few minutes; the author does not keep the bundled set updated. The Universal Face Fix needs no reference at all.

---

## Before you start

1. **XXMI / 3DMigoto is installed and the mod loads in game.** If the mod does not show up at all, this tool cannot help — that is a different problem.
2. **The mod's hashes are up to date.** If the mod was made for an older game version, update its hashes to the current version first — with whatever hash-update tool you use (they all do the same thing, names differ). This tool matches mods by hash; a stale hash means nothing matches and nothing gets fixed.
3. **One mod at a time.** Drop the folder that contains *that one mod's* `ini` and `Buffer` files — never the whole `Mods` folder, or you will scan other people's mods too.
4. **Never run the tool twice on the same mod.** Already-fixed files are detected and skipped, but do not test your luck.
5. **Bone-index and vertex-format fixes need a reference for that mesh.** The package bundles common ones; for anything else, capture it with gui_collect (see below). The Universal Face Fix (mode 2) needs no reference.

---

## How to use it

1. Unzip the package anywhere. Keep the `Dump` folder next to the script — it ships with ready-made references, and your own captures go there too.
2. Double-click the tool.
3. Pick your language: `1` = 中文, `2` = English.
4. Pick a mode:
   - `1` = **Index & Vertex Fix** — the everyday mode. Fixes bone indices and vertex format together.
   - `2` = **Universal Face Fix** — for the 3.1 → 3.2 broken faces only.
   - `3` = list which characters the Universal Face Fix covers.
5. In mode 1, pick a reference set (a folder inside `Dump`; the list at startup shows exactly which ones are there and what each covers, e.g. `Dialyn-Face — Face`).
6. Drag the mod's folder into the window and press Enter.
7. Choose `1` = fix, `2` = restore, `c` = pick another reference set, Enter = skip, `q` = quit.
8. Read the plan the tool prints. If it looks right, type `start` and press Enter.

That is it. Fix in game, done.

If `Dump` is empty, the tool prints the capture instructions and both links at startup — you do not have to remember them.

While the window is open you can also type:

| Input | What it does |
| --- | --- |
| `lang` | switch between 中文 and English |
| `m` | switch mode |
| `c` | pick a different reference set |
| `3` | list the characters covered by the Universal Face Fix |
| `q` | quit |

Command line, if you prefer: `python ZZZ_Index_Vertex_Fix_Tool.py [-zh|-en] [universal] [restore] <mod folder>`

---

## Capturing a reference dump with gui_collect

Needed for any mesh that is not already in the bundled `Dump` folder. Once per mesh, a few minutes the first time.

1. Install **[gui_collect](https://github.com/Petrascyll/gui_collect)** — needs Python 3.9+. `texconv.exe` and `texdiag.exe` are in its `modules` folder. Start it with `launch.bat`.
2. In the **XXMI launcher**, open the cog settings, go to your game's **MI tab** and tick **Enable Hunting**. Do this **before** launching the game.
3. Launch the game **with mods disabled** — press `F6`, or rename your `Mods` folder / add a `DISABLED` prefix, which is more reliable since shader mods can stay active.
4. Walk to a spot where the character you need is on screen. Press **numpad 0** to enter hunting mode (green text appears on screen). `F12` shows the keys, `Ctrl + F12` the hunting-specific ones.
5. Hunt down the mesh you want and copy its **IB hash** (marking a hash copies it to the clipboard).
6. Capture a **Frame Analysis dump**, then in gui_collect select that Frame Analysis folder, paste the IB hash, name the object (ASCII letters/digits, no spaces) and export.

You now have a folder with `hash.json` plus the text dumps. Put it into `Dump\` — one folder per mesh, named `character-part`:

```
Dump\
    Dialyn-Face\
        hash.json
        DialynFaceA-vb0=c44d2531.txt
        DialynFaceA-ib=facb2461.txt
```

Full illustrated walkthrough: **[3DMigoto Hunting & Dumping Tutorial](https://leotorrez.github.io/modding/guides/hunting)**

Two rules for this folder:

- **One mesh per folder, never merged by character.** One folder = one reference set = one fix scope. Merging would drag an already-fixed mesh back in and fix it twice.
- Names only affect the display, so rename them however you like — the tool reads `hash.json`, not the name.

You can also drag a dump folder straight into the tool window to load it for that session without copying anything.

---

## How it works (short version)

**Bone indices.** Every vertex in `blend.buf` carries four bone indices. A game update renumbers the skeleton, so a mod's baked-in numbers now point at the wrong bones. The tool pairs the mod's vertices with the game's by position (spatial grid, radius 0.01 game units). For every pair that also agrees on a skin weight it casts a vote `mod index → game index`, then resolves the votes into a one-to-one mapping and writes it back into the buf. Weights are the second signal: same position *and* same weight means the same bone.

**Vertex format.** The game changed the vertex COLOR element from 4 bytes to 4 floats, so the texcoord layout went from 36 to 48 bytes per vertex — the mod's buf and the `stride` line in its ini no longer match, and the texture is read from the wrong offsets. The tool re-packs every vertex and updates the stride. It only touches a buf when the buf size, the vertex count (from the blend buffer, found by hash) and the layout read from the live dump all agree — otherwise it prints a note and skips.

**Hashes.** The `hash =` lines in the ini are the game's buffer hashes. A mesh is only touched when the mod belongs to the reference set you picked, which is decided by matching those hashes. That is why stale hashes mean nothing matches.

Full write-up — tolerances, thresholds and the known limits — is in `原理说明.md` (How It Works) inside the package.

---

## Which problem do I have?

| What you see in game | What it is | Fixed by |
| --- | --- | --- |
| Legs bent backwards, body collapsed, arms twisted — textures fine | Bone indices | Mode 1 (VGX) |
| Texture smeared / scrambled across the whole model — shape perfect | Vertex format | Mode 1 (texcoord) |
| Only the **face** is broken after the 3.1 → 3.2 update | The COLOR block layout change | Mode 2, or mode 1 |
| Model is invisible / the mod does not load at all | Not this tool | Check your XXMI setup and the mod's hashes |

Both problems in mode 1 are checked, listed and fixed in one pass. If a mesh does not match, nothing happens to it.

---

## Safety

- Every file is backed up before it is modified: `*.texfmt_BACKUP.buf`, `*.vgx_BACKUP.buf` for buffers, `*.texfmt.bak` for inis.
- Choose `2` = restore in the window to roll back everything this tool changed in that folder.
- The tool refuses to touch a mod that does not belong to the reference set you picked. If not one single reference hash appears in the mod's ini, the whole folder is left alone — that prevents cross-fixing the wrong character.
- It never invents data. If it cannot determine the vertex count or the format, it prints a note and skips the file instead of guessing.

---

## FAQ

**The tool says "nothing matched, or everything was already fixed".**
Either that mesh genuinely needs no fix, or the mod's hashes are stale (update them to the current version first), or you picked the wrong reference set — type `c` and pick the matching one.

**My character is not in the bundled references.**
Capture that mesh with gui_collect — see the section above. The tool prints the same instructions and links at startup when `Dump` is empty. Except for the Universal Face Fix, no reference means no fix: there is nothing to compare the mod against.

**Can I fix several mods at once?**
Drop them one after another in the same window. Do not drop the parent folder of many mods.

**Can I share my captured dump folder?**
Yes, they are interchangeable — same layout, same tool.

**Does it work for other games?**
No. The reference format and the hash list are Zenless Zone Zero specific.

**Something broke.**
Type `2` = restore on the same folder. Everything is rolled back to the original files.

---

## Credits

- Capture workflow built on **gui_collect** by Petrascyll and on the [hunting guide](https://leotorrez.github.io/modding/guides/hunting) by Satan1c / LeoMods (XXMI Tools).
- VGX remap and texcoord tables are maintained by hand and cross-checked against live dumps.

---

## Open source, and final

This tool is **completely open source**. Anyone is free to modify it, build on it, and publish their own version — take the code, the idea, or just the approach.

It is meant to **share a way of solving the problem, not to be a finished product**. It may be incomplete, it may not cover your case, and it may never be improved. There are no further updates planned.

If it helps you understand the problem, or helps you build something better, it did its job.
