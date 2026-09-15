ZZZ Index & Vertex Fix Tool v2  ——  使用说明 / User Guide
绝区零 索引与顶点修复工具 v2
========================================================

中文
--------------------------------------------------------
修什么
    一、骨骼索引（VGX）
        症状：模型变形 —— 腿弯、塌陷、扭曲，但贴图正常
        做法：把 blend.buf 里的骨骼索引按正确映射逐个换掉

    二、顶点格式（texcoord）
        症状：贴图整体错乱，但模型形状完全正常
        做法：按游戏当前格式重排每个顶点的字节，并同步改 ini 里的 stride

    三、通用脸部修复（模式 2）
        专修 3.1 -> 3.2 更新后坏掉的那批脸：
        顶点 COLOR 从 4 字节变成 4 个 float（每顶点 36 -> 48 字节）
        这个模式不需要参照数据。

怎么用
    1. 解压到任意位置，Dump 文件夹要跟脚本放在一起
    2. 双击脚本
    3. 选语言：1 = 中文，2 = English
    4. 选模式：1 = 索引与顶点修复（常用）/ 2 = 通用脸部修复 / 3 = 看名单
    5. 模式 1 还要选一组参照（Dump 里的一个文件夹，列表里写明了管哪个部位）
    6. 把【那个 mod 的文件夹】拖进窗口，按 Enter
    7. 选 1 = 修复 / 2 = 还原 / c = 换一组参照 / 回车 = 跳过 / q = 退出
    8. 看清它列出的改动，确认无误就输入 start 回车

    窗口里还能输：
        lang = 换语言        m = 换模式
        c    = 换参照组      3 = 看通用脸部修复能修哪些角色
        q    = 退出

    【重要】跑之前先把 mod 的 hash 更新到当前版本 —— 你手上那个更新工具
    （各人叫法不同，效果一样）先跑一遍。本工具靠 hash 认网格。

参照数据（Dump 文件夹）
    包里预置了一些常用网格，覆盖到的角色直接就能修。作者不再更新这份数据，
    也不覆盖别的网格 —— 缺什么自己抓一份丢进去，抓一次一直能用。

        1. 装 gui_collect：https://github.com/Petrascyll/gui_collect
           （要 Python 3.9+，texconv/texdiag 在它的 modules 目录里，双击 launch.bat）
        2. XXMI 齿轮设置里进对应游戏的 MI 页，勾 Enable Hunting
           —— 必须在启动游戏之前勾
        3. 关掉 mod 再进游戏（F6；更保险是把 Mods 改名或加 DISABLED 前缀）
        4. 走到那个角色出现，小键盘 0 进狩猎模式（F12 看按键），
           找到目标网格，复制它的 IB hash
        5. 抓一次 Frame Analysis，用 gui_collect 打开那个文件夹、填 IB hash、
           给对象起名（字母数字，不能有空格），导出
        6. 一个网格一个文件夹丢进 Dump\，文件夹名写成「角色-部位」：

               Dump\
                   Dialyn-Face\
                       hash.json
                       DialynFaceA-vb0=c44d2531.txt
                       DialynFaceA-ib=facb2461.txt

    图文教程：https://leotorrez.github.io/modding/guides/hunting

    两条规矩
        - 一个网格一个文件夹，别按角色合并（合并会把修过的网格再修一遍）
        - 文件名只影响显示，随便改

注意
    - 一次只拖一个 mod 的文件夹（它自己的 ini 和 Buffer），别拖整个 Mods 目录
    - 不要在同一个 mod 上跑两次
    - 改之前都会自动备份，选 2 就能还原

原理
    为什么坏、怎么算出来的、判断规则、已知局限 —— 见同目录的 原理说明.md。

开源
    本工具完全开源。随便改、随便二次创作、随便发布自己的版本。
    它的定位是提供一个解决思路，不是一个成品：可能并不完善，后期不再更新。

========================================================

English
--------------------------------------------------------
What it fixes
    1. Bone indices (VGX)
       Symptom: model deforms — bent legs, collapse, twisting — textures fine
       Fix: rewrite every bone index inside blend.buf using the correct mapping

    2. Vertex format (texcoord)
       Symptom: texture scrambled everywhere, model shape perfectly fine
       Fix: re-pack every vertex to the game's current layout and sync the ini stride

    3. Universal Face Fix (mode 2)
       For the faces broken by the 3.1 -> 3.2 update:
       the vertex COLOR block went from 4 bytes to 4 floats (36 -> 48 bytes per vertex)
       This mode needs no reference data.

How to use
    1. Unzip anywhere. Keep the Dump folder next to the script.
    2. Double-click the script.
    3. Pick a language: 1 = 中文, 2 = English
    4. Pick a mode: 1 = Index & Vertex Fix / 2 = Universal Face Fix / 3 = list coverage
    5. In mode 1, pick a reference set (a folder inside Dump; the list shows what it covers)
    6. Drag THAT MOD's folder into the window and press Enter.
    7. Choose 1 = fix / 2 = restore / c = pick another reference / Enter = skip / q = quit
    8. Read the plan, then type start and press Enter to apply.

    In the window you can also type:
        lang = switch language     m = switch mode
        c    = re-pick reference   3 = list universal face fix coverage
        q    = quit

    IMPORTANT: update the mod's hashes to the current game version first, with
    whatever hash-update tool you use. This tool matches mods by hash.

Reference data (the Dump folder)
    A handful of common meshes ship in here, enough for the characters they cover.
    The author does not keep this data updated and covers nothing else — capture
    anything missing yourself and drop it in. One capture lasts forever.

        1. Install gui_collect: https://github.com/Petrascyll/gui_collect
           (needs Python 3.9+; texconv/texdiag live in its modules folder; run launch.bat)
        2. In the XXMI launcher, game's MI tab, tick Enable Hunting — BEFORE launching
           the game.
        3. Launch with mods off (F6; renaming the Mods folder or adding DISABLED is safer).
        4. Walk to the character, press numpad 0 for hunting mode (F12 shows the keys),
           find the mesh and copy its IB hash.
        5. Capture a Frame Analysis dump, point gui_collect at that folder, paste the
           IB hash, name the object (letters/digits, no spaces) and export.
        6. Drop one folder per mesh into Dump\, named "character-part":

               Dump\
                   Dialyn-Face\
                       hash.json
                       DialynFaceA-vb0=c44d2531.txt
                       DialynFaceA-ib=facb2461.txt

    Illustrated guide: https://leotorrez.github.io/modding/guides/hunting

    Two rules
        - One mesh per folder, never merged by character (merging would fix an
          already-fixed mesh twice)
        - Names only affect the display, so rename them freely

Notes
    - ONE mod folder at a time (its own ini + Buffer). Never the whole Mods folder.
    - Never run the tool twice on the same mod.
    - Everything is backed up before writing. Option 2 restores.

How it works
    Why it breaks, how the mapping is derived, the decision rules and the known
    limits: see 原理说明.md in the same folder.

Open source
    Completely open source. Modify it, build on it, publish your own version.
    It is meant to share an approach, not to be a finished product: it may be
    incomplete and it will not be updated further.
