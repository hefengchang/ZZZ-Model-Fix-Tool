# 作者：GreenLzz
# 感谢 Leotorrez、CaveRabbit、SilentNightSound 、HammyCatte的帮助

import os
import re
import time
import struct
import argparse
import shlex
import traceback
import sys
import json
import queue
import threading
import ssl
import shutil
import subprocess
import urllib.request
import urllib.parse
import webbrowser

# 程序版本号：唯一维护处，更新版本只改这一行
APP_VERSION = 'v3.2A'

# ================= 自动更新配置 =================
# 发布新版本的仓库："用户名/仓库名"（Gitee 优先，GitHub 兜底）。
# 留空则不检查更新；发布时填好再打 tag（版本号，如 3.1D）并上传 exe/py 资产即可。
# 也可在 zzz_fix_设置.json 里写 update_gitee_repo / update_github_repo 覆盖（便于测试）。
# 启动自动检查开关在设置文件 update_auto_start（默认 true）。
GITEE_REPO = 'hefengchang/ZZZ-Model-Fix-Tool'
GITHUB_REPO = 'hefengchang/ZZZ-Model-Fix-Tool'
# 界面链接按钮指向的网址（mod指南 / 更多修复工具）
URL_MOD_GUIDE = 'https://hefengchang.github.io/ZZZ-Mod-Help/'
URL_MORE_TOOLS = 'https://www.caimogu.cc/user/1761398.html'
from collections import deque
import ctypes
from dataclasses import dataclass, field
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ================= 内嵌更新历史（与 zzz_fix更新日志.txt 同步维护；
# ================= 同目录存在 txt 时程序优先读文件，打包后无 txt 用此内嵌版）
CHANGELOG_TEXT = '''==============================
ZZZ Fix 工具 - 全部更新历史
==============================
版本 3.2
--------
1.重构：为程序添加GUI界面和自动更新功能，新增了默认修复路径和手动修复路径选择功能，优化了拖放修复逻辑。
2.更新：蕾米埃尔、蕾米埃尔黑白皮肤 Hash 值支持对应的修复。
3.新增：克拉蕾Claret Hash 值支持对应的修复。

版本 3.1
--------
1. 新增：蕾米埃尔、蕾米埃尔皮肤、希格莉德、露西皮肤 Hash 值支持对应的修复。
2. 更新：维琳娜、维琳娜皮肤、诺姆、铃校服 Hash 值支持对应的修复。
3. 修复：对程序进行优化，修复拖放文件夹逻辑bug，修复索引节更新逻辑中因索引节不全导致意外丢失节的bug,修复工作目录异常bug。
4. 取消：不再提供对脸部vb的修复，不建议对脸部模型进行修改，可能会导致脸部贴图错位。请参考最新版的hash表或者hash变动日志在ini配置文件中进行手动替换。
5. 新增与更新：希格莉德皮肤 Hash 值支持对应的修复。
6. 热更新：更新希格莉德-身体  Hash 值支持对应的修复。

版本 3.0
--------
1. 新增：铃校服、哲校服、佩洛伊斯、诺姆、维琳娜、维琳娜皮肤 Hash 值支持对应的修复。
2. 更新：哲、哲道观、铃、铃道观、星见雅皮肤、普罗米娅 Hash 值支持对应的修复。
3. 由于哲与铃原皮与皮肤模型产生变化，无法通过简单的 hash 值替换来进行修复，
   故取消 3.0 之前的更新。
4. 更新妮可 Hash 值支持对应的修复。
5. 对程序进行优化，修复run = CommandListSkinTexture添加逻辑的bug，新增拖放文件夹或者输入路径进行修复的功能。

版本 2.8
--------
1. 新增：星徽比利、星见雅皮肤、普罗米娅 Hash 值支持对应的修复。
2. 更新：南宫羽、希希芙、莱特 Hash 值支持对应的修复。
3. 更新普罗米娅、星见雅皮肤 hash 值支持对应的修复。

版本 2.7
--------
1. 新增：南宫羽、南宫羽皮肤、希希芙 Hash 值支持对应的修复。
2. 更新：哲、千夏皮肤、爱芮皮肤 Hash 值支持对应的修复。

版本 2.6
--------
1. 新增：千夏/皮肤、爱芮/皮肤、潘引壶皮肤 Hash 值支持对应的修复。
2. 为琉音腿部变形单独制作了修复工具（需要先运行版本修复工具，确认变形后再修复）。

版本 2.5（重要）
----------------
已全面更新，更新内容与注意事项如下：
1. 更新角色琉音身体 blend，修复缓冲区（buf 文件），解决了腿部弯曲。
   修复腿部弯曲的注意事项：
   - 使用过 2.5A 修复工具或者香蕉网上的修复工具或手动修改过 ini 的，
     需要恢复原始备份 ini 文件，重新修复，否则无法解决该问题。
   - 修复需谨慎，该工具会在更新缓冲区时自动备份原始的 buf 格式的文件，
     如果产生异常，可修改备份文件名为原来的名字。
   - 如果你仍然无法解决，那么请去作者那里重新下载 Mod，再进行修复。
2. 更新角色哲和铃道服身体 hash。
   注意事项：
   - 哲和铃的道服模型将脖子一部分独立出来，产生了一个新的 IB，
     所以以往的 Mod 在修复后可能会产生一些异常，这是无法解决的问题。
3. 更新角色莱卡恩身体 Diffuse 贴图 hash。新增角色叶瞬光和皮肤、照高低显 hash。
4. 已知问题：角色简的模型权重发生变化（比如头发），无法通过该工具进行修复。

版本 2.4
--------
1. 添加角色琉音高低显。
2. 更新角色月城柳 blend、薇薇安皮肤 blend、伊德海莉 LightMap 值。

版本 2.3
--------
1. 添加角色：卢西娅、狛野真斗、伊德海莉、薇薇安皮肤高低显。
2. 更新角色扳机脸部 Texcoord。

版本 2.2
--------
1. 更新角色：哲·泳装、铃·泳装。
2. 添加角色：席德、奥菲丝。

版本 2.1
--------
1. 取消铃的脸部 Texcoord 值的更新，已知铃与皮肤之间脸部虽然使用了相同的 ib 值，
   但 Texcoord 和 blend 的值不同，无法进行自动更新。使用了脸部 Texcoord 和 blend
   的 mod 将会导致铃与铃皮肤脸部冲突，需要删除脸部相关内容，使用原脸。
2. 更新角色有：铃道服、潘引壶、哲、仪玄（葫芦）。
3. 2.1B 更新浮波柚叶皮肤身体 hash。
4. 2.1C 更新低显支持，更新仪玄皮肤，优化逻辑，修复错误添加 bug。

=======================================
'''

# ================= 内嵌 Hash 变动日志（与 Hash变动日志.txt 同步维护；打包后无 txt 用此内嵌版）
HASHLOG_TEXT = r'''
===============================================================================
  3.1 -> 3.2
===============================================================================
【蕾米埃尔Remielle】
IB: 785b21f5 -> 28e05a59（身体）
  draw_vb: 7a92a10a -> 97664f2f
  position_vb: 679a1bd8 -> d16f6790
  texcoord_vb: 9e33a8b6 -> b943ec9e
  blend_vb: 9e8a27ae -> da54a57a
  object_indexes: [0, 57612] -> [0, 59094]
  object_classifications: ['A', 'B']

【蕾米埃尔-白皮肤RemielleSkinWhite】
IB: 241deac5 -> 2cd6516a（身体）
  draw_vb: 48288582 -> df41c403
  position_vb: 13c77c3a -> 22d04ad5
  texcoord_vb: c55c57ce -> d637a74d
  blend_vb: 9bca83d8 -> 5ec5e567
  object_indexes: [0, 56376] -> [0, 56736]
  object_classifications: ['A', 'B']

【蕾米埃尔-黑皮肤RemielleSkinBlack】
IB: f57f3e40 -> 92cb56c9（身体）
  draw_vb: 22ec622c -> 6a0d36f2
  position_vb: 554d46cf -> 0929171b
  texcoord_vb: 5dcc6ee1 -> c24cc6a1
  blend_vb: 7f6fe876 -> 93b69961
  object_indexes: [0, 64092] -> [0, 64626]
  object_classifications: ['A', 'B']
  Diffuse: 0e408177 -> bb0f08b9
  Diffuse: abb0d69d -> 578353ea
  LightMap: 6102ae18 -> 0e9d14dc
  LightMap: 2aab9aa7 -> 312bbc0c
  MaterialMap: cccb8109 -> 8240c688
  MaterialMap: e9f33a20 -> 2367a92b
IB: 09a51ed3 -> 24a512cb（腿部）
  draw_vb: 96dc0a8e -> ea50e1d1
  position_vb: fa9635bc -> 11fbd4a3
  texcoord_vb: 7c0db158 -> 14ab0adc
  blend_vb: ff05e5f9 -> 3841a909
  object_indexes: [0, 15618] -> [0, 15546]
  object_classifications: ['A', 'B']
  Diffuse: 877b0ce6 -> 017c13e4
  Diffuse: 4c49a23c -> d0eb079f
  LightMap: baeb2662 -> 0a902460
  LightMap: 17b9c313 -> b9a73372
  MaterialMap: 3b0c9e0a -> fb096287
  MaterialMap: 2dce69bd -> 0b54d931

【琉音Dialyn】
IB: d860525e（眉毛）
  texcoord_vb: d90368ed -> 27fd9193
IB: facb2461（脸部）
  texcoord_vb: f6c5296e -> dafc9647

【珂蕾妲Koleda】
IB: 0e74656e（脸）
  Texcoord: f41b27e6 -> 57994826

【薇薇安Vivian】
IB: 39944f20（脸）
  Texcoord: 0afe5a44 -> 50c5d703

===============================================================================
  版本 3.1 -> 3.11
===============================================================================
【希格莉德Sigrid】
IB: a23aa8a3 -> 38daef11（身体）
  draw_vb: 01b35c45 -> d0bf0e87
  position_vb: 08c15b45 -> e2a28287
  texcoord_vb: f6474154 -> 08ddaed3
  blend_vb: 8c0622d7 -> 018ea72c
  object_indexes: [0, 42759] -> [0, 42963]
  object_classifications: ['A', 'B']

=======================================================================
  版本 3.0 → 3.1
=======================================================================
【哲泳装WiseSwimwear/哲皮肤WiseSkin/哲Wise/哲校服WiseSchoolUnifor】 
IB: 1fdaf388（脸）
  Texcoord: c83b6cbf -> 2b320847

【简皮肤JaneSkin/简Jane】
IB: ef86fc9f（脸）
  Texcoord: 1fa404c1 -> 3c32a411

【维琳娜皮肤VelinaSkin/维琳娜Velina】
IB: 6cfb2498 -> 2414f4b9（脸）
  draw_vb: 19ead1b7 -> bfa3b361
  position_vb: 23f842f0 -> 85b12026
  texcoord_vb: 641bedfb -> 69304ff6
  blend_vb: 98ecf569 -> 76fe8eed
  object_indexes: [0, 7182, 9888] -> [0, 7398, 9888]

【莱特Lighter】
IB: dcc7bb78（脸）
  Texcoord: af14829b -> 04cc2dfd

【诺姆Norma】
IB: ca38d6a1（武器）
  position_vb: 38e511a4 -> 07e51b64
  texcoord_vb: 89a25f1a -> c4173b6e
  blend_vb: d3a66db9 -> aa195b0b
  NormalMap: 4050da0a -> ebac056e
  NormalMap: 0139f54e -> 798adba3
  MaterialMap: 7ae5f4d6 -> 79a583ad
  MaterialMap: 1db67ade -> b70b6037
IB: 85361021（炮弹）
  position_vb: e2a92567 -> e3fafeeb
  texcoord_vb: 1d67e673 -> 44991f30
  NormalMap: 4050da0a -> ebac056e
  NormalMap: 0139f54e -> 798adba3
  MaterialMap: 7ae5f4d6 -> 79a583ad
  MaterialMap: 1db67ade -> b70b6037
IB: a2150d3b（头发）/bcc7e369（帽子）
  NormalMap: fc98a89c -> ebac056e
  NormalMap: dc5bc6d9 -> 798adba3
IB: 773f390c（身体）
  NormalMap: 37da98f5 -> ebac056e
  NormalMap: 02cbd89d -> 798adba3

【赛斯Seth】
IB: 52f5aa74（脸）
  Texcoord: bff3e0b3 -> b3f6842f

【铃Belle/铃校服BelleSchoolUniform/铃皮肤BelleSkin/铃泳装BelleSwimwear】
IB: 9a9780a7（脸）
  texcoord_vb: d3000b22 -> 228f5a8b

【铃校服BelleSchoolUniform】
IB: feb1c4cd（身体）
  Diffuse: a292d07d -> fd906f9b
  Diffuse: 639ad374 -> d9dc65da

【露西Lucy】
IB: df3e3965（脸）
  Texcoord: 1ca0ae1a -> e78a4ee2

【青衣Qingyi】
IB: f6e96452（脸）
  Texcoord: 6a492df0 -> db1f2dfa 
  ※ 青衣与零号安比脸部的旧hash冲突，请勿使用修复工具修复，请在ini配置中手动替换为新的hash

【希格莉德-皮肤SigridSkin】
IB: d9e49957（身体）/b4f608f5(转轮轴承)
  Diffuse: b07c43ef -> 8874c184
  LightMap: 5e907c41 -> 2772f644


=======================================================================
  版本 2.8 → 3.0
=======================================================================

【哲Wise】
  IB: 8d6acf4e（身体）
    Diffuse2048: f2fb7a37 -> a9652fa4
    Diffuse1024: dea7a8ca -> 53b3623f
    Blend: 46462bd8 -> 03dadd2a

【哲Wise / 哲-皮肤WiseSkin（头发共用）】
  IB: d5ca0411（头发）
    Blend: edfd1666 -> 68e4f572

【哲-皮肤WiseSkin】
  IB: 01c42a1d（颈部）
    Blend: 458bbde3 -> e0b1e734
  IB: 1eca2097（身体）
    Blend: 8612559a -> f28a6363
    Diffuse2048: 81406abe -> 669191ec
    Diffuse1024: 9fc3646e -> 23876240

【哲Wise / 哲-皮肤WiseSkin / 泳装WiseSwimwear（脸共用）】
  IB: 1fdaf388（脸）
    Blend: 757bc7cc -> 015fbf96

【哲-泳装WiseSwimwear】
  IB: cb272754 -> 0ec31440（头发）※ 模型变化不可修复
  IB: 3f771e63 -> 8d08b190（头发阴影）
  IB: 4fe696c8 -> 19a3f02e（身体）※ 模型变化不可修复

【铃Belle】
  IB: bea4a483 -> 3acf9aea（头发）※ 模型变化不可修复
  IB: 1817f3ca -> c2b4ce3a（身体）※ 模型变化不可修复
  IB: 9a9780a7（脸）
    Texcoord: 1de8fc08 -> d3000b22
    Blend: 36138f65 -> 6ade3fdc

【铃皮肤BelleSkin】
  IB: aa9ffb85（头发）
    Blend: 39ac6700 -> 8f7ae834
  IB: 20d3a340（头饰）
    Blend: db7add33 -> f18dd23f
  IB: 62ed56cc -> d0627e1f（颈部）※ 模型变化不可修复
  IB: d509bdd4（身体）
    Blend: f3dedb50 -> 4d74d5e9
  IB: bcc9e4e1（腿部）
    Blend: f53b2eba -> 922a7db6

【铃皮肤BelleSkin / 泳装BelleSwimwear（脸共用）】
  IB: 9a9780a7（脸）
    Blend: 0c9a075b -> 359e4502

【铃-泳装BelleSwimwear】
  IB: ea055cac -> a7683988（头发）※ 模型变化不可修复
  IB: 43ed3c22 -> 619c5c94（身体）※ 模型变化不可修复
  IB: 69148073（T恤）
    Texcoord: 881514bf -> 325b4a1c
    Blend: 0139f7e8 -> 0a00d846
    LightMap2048: e0a86379 -> 60250d24
    LightMap1024: a189eccd -> 5978a2ca

【星见雅-皮肤MiyabiSkin】
  IB: fbb18630（衣服）
    Diffuse2048: 66724f5a -> 4e6c90bd
    MaterialMap2048: 1e1485e7 -> 30590865
    Diffuse1024: 88e357af -> 7d80f565
    MaterialMap1024: 85aad660 -> 2fbabf2e

【普罗米娅Promeia】
  IB: 36e794ea -> b386901d（身体-束缚状态）
    VertexLimitRaise: 19ad87f6 -> dd86f5ae
    Position: ffaa183a -> 68e2baef
    Texcoord: 2a9842a1 -> 6fe5f8c1
    Blend: dae4abd0 -> 112582ea
  IB: 62a6b4bd -> 10c77d62（身体-正常状态）
    Position: bf938187 -> 2dbfe8c9
    Texcoord: d99d21e0 -> 1fc95f5b
    Blend: 575d8b1b -> ee35cc06
  IB: 93f1f568 -> 0ae14c24（衣服）
    Position: 1d63183b -> f6cc27b6
    Texcoord: 826446a7 -> bf00cc95
    Blend: 58f42be3 -> 4b0d6867
    Diffuse2048: b9367016 -> e1492a53
    LightMap2048: d743acd0 -> 9bf7f5cc
    MaterialMap2048: 31d7cbad -> d37b40a9
    Diffuse1024: 406b1373 -> 47d294f4
    LightMap1024: 044d2d39 -> 562616d5
    MaterialMap1024: 01a5ba27 -> 73aaae54
  IB: fd054d1d -> ec003379（腿部）
    Position: 0b822797 -> 4c1d0a70
    Texcoord: f5fd0e92 -> 03d6f933
    Blend: 9839b071 -> 65bba179
  IB: 8995db58（环刃）
    Position: d242b77a -> 35ecba91
    Texcoord: f2f5bd28 -> 064658e2
    Diffuse2048: d1399215 -> 328135c5
    LightMap2048: 369f0efd -> 82f4146a
    MaterialMap2048: a179a69c -> d672b87c
    Diffuse1024: 138bcaa1 -> 7750fc88
    LightMap1024: 5e59380e -> a1988612
    MaterialMap1024: 09271c02 -> 7559d574

【v3.01热更新 - 妮可Nicole】
  IB: 6847bbbd -> 7dcfe907（头发）
    draw_vb: f6344432 -> d9b8d61a
    position_vb: 199853eb -> 6f931ca7
    texcoord_vb: 06e4fd79 -> e04f4893
    blend_vb: 347e4a48 -> 8171f5c9
  IB: 4ed9a81f（头发阴影）
    texcoord_vb: 322345a6 -> e6b9e50e
  IB: 5a4c1ef3 -> e53364dd（身体）
    draw_vb: 8cc1262b -> b19da99e
    position_vb: 89df5a07 -> 4af0a4cd
    texcoord_vb: 91c1b779 -> ed4c47a9
    blend_vb: 7ecda89f -> b793c804
  IB: 40e64ae2（艾米莉安）
    texcoord_vb: 077c3500 -> f9f810ed
  IB: 7435fc0e -> 93b02078（脸）
    VertexLimit: 9274e401 -> 967c2f1c
    Texcoord: 5714e5e6 -> d5958556
    Blend: b25ebcf6 -> 292d1b1f
    Position: a8667746 -> ac6ebc5b


=======================================================================
  版本 2.7 → 2.8
=======================================================================

【南宫羽Nanyu】
  IB: cd884c0a / 3b4190ce / 4586e530
    Diffuse: 2d290490 -> 11254966
    Diffuse: fe06152c -> dc41fbbf

【希希芙Cissia】
  IB: ff2ec4d6 / 4c11c155 / 29b5b0b0 / 29123d5a / bad668cc / d49a5866
    Diffuse: f8739729 -> ec85e98d
    Diffuse: f5ecd616 -> 6d861173

【莱特Lighter】
  IB: 542b8aa9 / 2de659bd
    Diffuse: c5d60a1d -> 4e088042
    MaterialMap: d5ba9ea6 -> d331b850
    Diffuse: 1cd2d442 -> 0ee07935
    MaterialMap: 8687f7b8 -> 99ad14f1

【普罗米娅Promeia】
  IB: 6cca89ab -> 31178971
    position_vb: 35096cb6 -> 681aceaa
    texcoord_vb: 9c0aad96 -> 84d40d91
    blend_vb: 5a263750 -> 3d4a4881
  IB: a633d5b7 -> 36e794ea
    draw_vb: dd86f5ae -> 19ad87f6
    position_vb: a7769c93 -> ffaa183a
    texcoord_vb: bfcfb2f7 -> 2a9842a1
    blend_vb: 61c399b6 -> dae4abd0
  IB: 6abaa60a -> 62a6b4bd
    texcoord_vb: b1ec331c -> d99d21e0
    blend_vb: bca960d0 -> 575d8b1b
  IB: 68f34958 -> 93f1f568
    position_vb: d43597aa -> 1d63183b
    texcoord_vb: 9f083955 -> 826446a7
    blend_vb: 870f56b5 -> 58f42be3
  IB: 21871660 -> fd054d1d
    position_vb: 595bd76e -> 0b822797
    texcoord_vb: 2918714e -> f5fd0e92
    blend_vb: fd3c3d9f -> 9839b071
  IB: cb9d17fc -> e032287a
    texcoord_vb: 3a00aa76 -> d3d65ca5
  IB: 5ea47a32 -> ef3c4506
    texcoord_vb: b7a6479f -> dcd61276
    blend_vb: 5ff41c34 -> bf5b785d
  IB: 947ceb88 -> 8995db58
    draw_vb: 7d76d686 -> 0a06059e
    position_vb: 2f3a560d -> d242b77a
    texcoord_vb: 23587131 -> f2f5bd28
    blend_vb: 21ac80fa -> a864dc82
  IB: de6eb63b -> ff223b2c

【星见雅皮肤MiyabiSkin】
  IB: a913e9a9
    blend_vb: f2f19cb2 -> 5121459b

【5/13热更新】
  普罗米娅Promeia（见上方普罗米娅条目）


=======================================================================
  版本 2.6 → 2.7
=======================================================================

【哲Wise】
  IB: 8d6acf4e
    Diffuse: 868709f2 -> f2fb7a37
    Diffuse: 3d7a53b0 -> dea7a8ca

【千夏皮肤ChinatsuSkin】
  IB: 6cc4d486 -> a6d82ba5
    draw_vb: 22c82346 -> 74cc56df
    position_vb: 327644ee -> 4b93d8eb
    texcoord_vb: 5e70dde6 -> b9030f86
    blend_vb: 79de92c7 -> 4a795f2a
  IB: ee17c9a2
    position_vb: c77b3235 -> 25cf6bf7
    texcoord_vb: 0c6b95ca -> 7a31eb8b

【爱芮-皮肤ArieSkin】
  IB: c6bb960b
    Diffuse: a55f187e -> 677f73d9
    Diffuse: 3c6bd181 -> 303c63bc


=======================================================================
  版本 2.5 → 2.6
=======================================================================

【铃泳装/皮肤（共用）】
  IB: 9a9780a7
    texcoord_vb: ccc76aea -> bcfc3326


=======================================================================
  版本 2.4 → 2.5
=======================================================================

【哲皮肤WiseSkin】
  IB: 6acc1eb8 -> 1eca2097
    draw_vb: 4fa228f9 -> ca02f614
    position_vb: ae59eabb -> a388eb6b
    texcoord_vb: a83ada4e -> b39870e1
    blend_vb: 177ad7e8 -> 8612559a

【琉音Dialyn】
  IB: af39a873
    blend_vb: 6ff0e4ad -> 3d7e53cf
  IB: 1d8f8de6
    position_vb: 79fc6a95 -> fd32eb72
    texcoord_vb: c0f5d550 -> 5455d3c6
    blend_vb: 35709db4 -> 8fe19cc1

【简Jane】
  IB: 9268a5af -> 3275b812
    draw_vb: 2d06e785 -> 74bc0b7f
    position_vb: e7a3b7dc -> 33a09cfe
    texcoord_vb: acec29f8 -> fa617c9a
    blend_vb: 8721477f -> e42171df
    object_indexes: [0, 33780] -> [0, 16986]
  IB: ef86fc9f
    Texcoord: 9f2f7c53 -> 1fa404c1

【铃皮肤BelleSkin】
  IB: 860e1558 -> d509bdd4
    draw_vb: 02c9dc4b -> 19e5f486
    position_vb: 0b3c5e7c -> 8a4e97cd
    texcoord_vb: 862dc27a -> d761e076
    blend_vb: 01b0c8b6 -> f3dedb50

【莱卡恩Lycaon】
  IB: 6749b6e7 / c28ea8d7
    Diffuse: 7169ec86 -> 4cb6928e
    Diffuse: 82ad0c28 -> 7a22ad61

【叶瞬光YeShunguang】
  IB: c209c22b
    texcoord_vb: d1ffd339 -> dbb027eb

【模型结构变化说明】
  ※ 简：新增 手和配饰 IB:294a319a；头发权重发生变化，无法修复
  ※ 铃-道服：新增 脖子 IB:62ed56cc
  ※ 哲-道服：新增 脖子 IB:01c42a1d


=======================================================================
  版本 2.3 → 2.4
=======================================================================

【月城柳Yanagi】
  IB: f478ee4c
    blend_vb: fd363c76 -> b558d482

【爱丽丝皮肤AliceSkin】
  IB: 2c37d8c9
    position_vb: e3a50a16 -> 5324c543
    texcoord_vb: c6899a42 -> 3136fbad
    blend_vb: 4fbccfe1 -> e52f08c3

【薇薇安皮肤VivianSkin】
  IB: 3060793b
    blend_vb: f32eec8a -> 723bccec

【伊德海莉Yidhair】
  IB: 12251f42
    LightMap: 2ae9bee8 -> 5b985a6f
    LightMap: 9ad20501 -> 381e8e5a


=======================================================================
  版本 2.2 → 2.3
=======================================================================

【席德seed】
  IB: 75e1ae0a
    position_vb: b095c5cf -> 567f9bcd
    texcoord_vb: 56979e94 -> 030e0aca
    NormalMap: fc59be11 -> b35534a9
    NormalMap: b35534a9 -> b87d9c50

【扳机Trigger】
  IB: 40cd4182
    Texcoord: b9f0d595 -> d4a12ab7


=======================================================================
  版本 2.1 → 2.2
=======================================================================

【哲-泳装WiseSwimwear】
  IB: 4fe696c8
    blend_vb: 9741e2f0 -> d4147320

【铃-泳装BelleSwimwear】
  IB: 43ed3c22
    blend_vb: 6af00597 -> 4f3ddd5c
  IB: 69148073
    blend_vb: 65481194 -> 0139f7e8

【爱丽丝皮肤AliceSkin】
  IB: 2c37d8c9
    position_vb: 5324c543 -> e3a50a16
    texcoord_vb: 3136fbad -> c6899a42
    blend_vb: e52f08c3 -> 4fbccfe1

【简Jane】
  IB: 602c545a
    Position: 850d4cbf -> eace2dfa
    Texcoord: 7fd655de -> 535e2453
    Blend: a14461d9 -> 7310ad6a


=======================================================================
  版本 2.0 → 2.1
=======================================================================

【哲皮肤WiseSkin】
  IB: f6cac296 -> d5ca0411
    draw_vb: ba59bf09 -> ef9c0510
    position_vb: 6235fa7f -> e8df7ff3
    texcoord_vb: fe89498c -> 774071dd
    blend_vb: 1273c7b0 -> edfd1666
  IB: 83e07a1b -> 8d08b190
    draw_vb: af5fc216 -> 681651f9
    position_vb: 1a438b0d -> 4af493e5
    texcoord_vb: 7b7957fa -> ad7d7eca
    blend_vb: 52bd07dd -> 795e9a7c
  IB: 1fdaf388
    Texcoord: ebe9f31b -> c83b6cbf

【哲Wise】
  IB: f6cac296 -> d5ca0411
    draw_vb: ba59bf09 -> ef9c0510
    position_vb: 6235fa7f -> e8df7ff3
    texcoord_vb: fe89498c -> 774071dd
    blend_vb: 1273c7b0 -> edfd1666
  IB: 83e07a1b -> 8d08b190
    draw_vb: af5fc216 -> 681651f9
    position_vb: 1a438b0d -> 4af493e5
    texcoord_vb: 7b7957fa -> ad7d7eca
    blend_vb: 52bd07dd -> 795e9a7c
  IB: 8d6acf4e
    texcoord_vb: f425bd04 -> 91fbd2fa
  IB: b1df5d22
    texcoord_vb: 2ae08ae7 -> 8d825ff1
  IB: 1fdaf388
    Texcoord: ebe9f31b -> c83b6cbf

【扳机Trigger】
  IB: 40cd4182
    Position: ba455625 -> dfc69ad0
  IB: f61f6acd
    Position: 988144a6 -> 862efc96
    Texcoord: b6d507d9 -> a58b916d

【月城柳Yanagi】
  IB: 44d9123b
    draw_vb: （新增） -> 178a1ff8
    position_vb: （新增） -> 8e3cf210
    texcoord_vb: （新增） -> dd32963a
    blend_vb: （新增） -> 6b5d6e39

【本Ben】
  IB: 9c4f1a9a
    Position: 4465b35d -> 3e601b7c

【比利Billy】
  IB: dc7978f3
    Position: f88a6fbe -> ed6468f9

【波可娜Pulchra】
  IB: 425a7565
    position_vb: d82af72e -> a9d915fc
    texcoord_vb: 13af1533 -> ac887af1
  IB: 5b644956
    Position: 49b9e647 -> b410f6f4
    Texcoord: 8d36ab74 -> 5e8cc065
  IB: bfc94dff
    Position: 49b9e647 -> b410f6f4
    Texcoord: 8d36ab74 -> 5e8cc065

【潘引壶PanYinhu】
  IB: ebb6a59b
    position_vb: 523c1dca -> 784ab863

【铃皮肤BelleSkin】
  IB: 403eace9
    texcoord_vb: 7bf983ed -> 31746eaa
  IB: 860e1558
    Diffuse: cac9fd5d -> da2bfe2f
    Diffuse: 59218fac -> fdf0b49e

【格莉丝Grace】
  IB: 8b240678
    Diffuse: 210b3ebf -> 9c7057e8
    Diffuse: 21794bd6 -> ac361185

【浮波柚叶皮肤YuzuhaSkin】
  IB: f34fdc84 -> b298482d
    draw_vb: cf3319f6 -> 07437c27
    position_vb: a3b56c9b -> 2a7b9144
    texcoord_vb: 3d3199c5 -> 0c9062c5
    blend_vb: be70426a -> 523cf99d

【仪玄-皮肤YixuanSkin】
  IB: 95de0d39 / 064cd7d3
    Diffuse: 487db3e0 -> 7683c132
    MaterialMap: 16a1fb10 -> 7e6747ac
    Diffuse: c13cac2c -> 89509335
    MaterialMap: 9a79cf64 -> 229c5b0f
'''

# 使用标准库的 ANSI 转义码替代 colorama，无需额外安装
class _Style:
    """ANSI 颜色/样式常量，替代 colorama 的 Fore/Back/Style"""
    YELLOW = '\033[93m'
    ORANGE = '\033[38;2;255;165;0m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    BRIGHT = '\033[1m'
    RESET = '\033[0m'
    WHITE_BG = '\033[107m'
    RESET_BG = '\033[49m'

def _enable_ansi():
    """Windows 10+ 启用虚拟终端处理，使 ANSI 转义码生效"""
    if sys.platform == 'win32':
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            hStdout = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
            mode = ctypes.c_uint32(0)
            kernel32.GetConsoleMode(hStdout, ctypes.byref(mode))
            mode.value |= 0x0004  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
            kernel32.SetConsoleMode(hStdout, mode)
        except Exception:
            pass  # 不支持 ANSI 的控制台也能正常运行，只是没有颜色

# 额外的预防措施，以避免多次“修复”相同的缓冲区
global_modified_buffers: dict[str, list[str]] = {}


def _clean_path_token(raw):
    """清理单个路径：去引号、处理 file:/// 前缀、正斜杠转反斜杠。"""
    path = raw.strip().strip('"\'')
    if not path:
        return None
    low = path.lower()
    if low.startswith('file:///'):
        path = path[8:]
    elif low.startswith('file://'):
        path = path[7:]
    elif low.startswith('file:'):
        path = path[5:]
    return path.replace('/', '\\')


def _repair_path(path):
    """修复单个文件或文件夹（文件夹递归处理其下所有 .ini）。"""
    if os.path.isdir(path):
        print('处理文件夹: {}'.format(path))
        process_folder(path)
    elif os.path.isfile(path):
        filename = os.path.basename(path)
        if filename.upper().startswith('DISABLED') and filename.lower().endswith('.ini'):
            print('跳过已禁用的 .ini 文件: {}'.format(path))
        elif path.lower().endswith('.ini'):
            print('处理文件: {}'.format(path))
            if not upgrade_ini(path)[0]:
                print('未修复: {}'.format(path))
        else:
            print('跳过非 .ini 文件: {}'.format(path))


def _process_paths(paths):
    """
    依次处理一组路径。

    cmd 中不加引号的含空格路径会被拆成多个参数（如 "C:\\New Folder\\mod" 被拆成
    "C:\\New" 和 "Folder\\mod"），单个参数都不存在时尝试与后续参数用空格拼接，
    恢复成原始路径后再处理。
    """
    i = 0
    n = len(paths)
    while i < n:
        path = paths[i]
        if os.path.isdir(path) or os.path.isfile(path):
            _repair_path(path)
            i += 1
            continue

        # 尝试与后续参数拼接，恢复被 cmd 拆开的含空格路径
        # （cmd 会把连续空格折叠成一个分隔符，因此依次尝试用 1~4 个空格连接）
        found = False
        j = i
        while j + 1 < n:
            j += 1
            for k in range(1, 5):
                joined = (' ' * k).join(paths[i:j + 1])
                if os.path.isdir(joined) or os.path.isfile(joined):
                    found = True
                    break
            if found:
                break
        if found:
            _repair_path(joined)
            i = j + 1
        else:
            print('路径不存在: {}'.format(path))
            i += 1


def main():
    parser = argparse.ArgumentParser(
        prog="ZZZ Fix {} 中文版".format(APP_VERSION),
        description=('')  # 描述
    )

    parser.add_argument('paths', nargs='*', default=None, type=str)
    # parse_known_args: 以 "-" 开头的路径（如文件夹名 "-mods"）会被放入 unknown，
    # 与位置参数合并处理而不是报错；--help 仍正常显示帮助
    args, unknown = parser.parse_known_args()
    raw_paths = list(args.paths or []) + list(unknown)

    if raw_paths:
        # 支持命令行/拖放传入多个文件或文件夹（含空格路径未加引号时自动拼接恢复）
        paths = []
        for p in raw_paths:
            clean = _clean_path_token(p)
            if clean:
                paths.append(clean)
        _process_paths(paths)

    else:
        # 将当前工作目录更改为此脚本所在的目录
        # 否则通过右键"打开方式"选择 Python 运行时，当前工作目录会是
        # C:\Windows\system32 而不是程序所在目录，导致找不到旁边的 .ini
        # Nuitka: "Onefile: Finding files" in https://nuitka.net/doc/user-manual.pdf
        # 打包成 exe 时 __file__ 可能指向临时解压目录，因此用 sys.frozen 区分
        if getattr(sys, 'frozen', False):
            script_dir = os.path.dirname(os.path.abspath(sys.executable))
        else:
            script_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(script_dir)
        print('由踩蘑菇网绿林小子进行汉化并制作')
        print('当前工作目录: {}'.format(os.path.abspath('.')))
        process_folder('.')

    print('自动修复已完成!')
    drag_drop_loop()


# 无耻地（大部分）从 genshin 修复脚本中剥离
def process_folder(folder_path, visited=None):
    """递归处理文件夹下所有 .ini。

    visited 按真实路径(realpath)去重，防止 junction/符号链接导致的循环递归。
    枚举失败的文件夹(如权限不足)打印错误后继续，不中断整个修复。
    """
    if visited is None:
        visited = set()
    try:
        real = os.path.realpath(folder_path)
    except OSError:
        real = folder_path
    if real in visited:
        print('跳过已处理过的文件夹(可能为链接循环): {}'.format(folder_path))
        return
    visited.add(real)

    try:
        entries = os.listdir(folder_path)
    except OSError as e:
        print('无法读取文件夹 {}: {}'.format(folder_path, e))
        return

    for filename in entries:
        if filename.upper().startswith('DISABLED') and filename.lower().endswith('.ini'):
            continue
        if filename.upper().startswith('DESKTOP'):
            continue

        filepath = os.path.join(folder_path, filename)
        try:
            is_dir = os.path.isdir(filepath)
        except OSError:
            is_dir = False
        if is_dir:
            process_folder(filepath, visited)
        elif filename.endswith('.ini'):
            print('找到 .ini 文件:', filepath)
            upgrade_ini(filepath)


def upgrade_ini(filepath):
    """返回 (是否成功, 本文件 hash 级语义日志行列表)；失败时日志为 []"""
    hash_log = []
    try:
        # 这里发生的错误是可以接受的，因为没有对 ini 或任何缓冲区进行写操作
        ini = Ini(filepath).upgrade()
    except Exception as x:
        print('发生错误: {}'.format(x))
        print('未对 {} 应用任何更改!'.format(filepath))
        print()
        print(traceback.format_exc())
        print()
        return (False, [])

    try:
        # ini 的内容和任何修改的缓冲区将在此函数中写入磁盘
        # 由于此函数的代码更简洁且可预测，失败的可能性较低，但如果 Windows 不愿意写入，可能会发生这种情况。
        ini.save()
    except Exception:
        print('保存 {} 更改时发生致命错误!'.format(filepath))
        print('您的 mod 可能已损坏。您必须从源重新下载它，然后再尝试修复。')
        print()
        print(traceback.format_exc())
        print()
        return (False, [])

    hash_log = list(getattr(ini, '_hash_log', []))
    return (True, hash_log)

def drag_drop_loop():
    """
    修复完成后，允许用户拖放文件/文件夹到控制台窗口来继续触发修复。
    拖放文件到控制台窗口会粘贴其路径文本，按 Enter 后执行修复。
    """
    print()
    print('=' * 60)
    print('可以拖放 .ini 文件或文件夹到本窗口，或者直接输入路径(如果不行，可以在路径首尾添加引号)，然后按 Enter 触发修复')
    print('输入 exit 或 quit 或 q 退出程序')
    print('=' * 60)
    print()

    while True:
        try:
            raw = input('拖放文件/文件夹 (或输入 exit 退出): ').strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not raw:
            continue

        lower = raw.lower()
        if lower in ('update', 'up', '更新', '检查更新'):
            try:
                if cli_check_update(manual=True):
                    return
            except Exception as x:
                print('检查更新失败: {}'.format(x))
            continue
        if lower in ('exit', 'quit', 'q', '退出'):
            print('正在退出...')
            break

        print()
        print('-' * 60)
        print('收到输入: {}'.format(raw))
        print('-' * 60)

        # 一次性拖入多个文件/文件夹时，控制台会把所有路径拼在一行粘贴进来
        # （空格分隔、含空格的路径带引号），因此按引号规则拆分成多个路径逐个处理
        try:
            tokens = shlex.split(raw, posix=False)
        except ValueError:
            # 引号不匹配时退化为把整行当作一个路径
            tokens = [raw.strip('"\'')]

        paths = []
        for t in tokens:
            clean = _clean_path_token(t)
            if clean:
                paths.append(clean)
        if not paths:
            continue

        _process_paths(paths)
        print('修复已完成!')
        print('-' * 60)
        print()


# MARK: Ini
class Ini():
    def __init__(self, filepath):
        self.filepath = filepath
        try:
            self.content  = Path(self.filepath).read_text(encoding='utf-8')
            self.encoding = 'utf-8'
        except UnicodeDecodeError:
            self.content  = Path(self.filepath).read_text(encoding='gb2312')
            self.encoding = 'gb2312'
        

        # 集合的随机排序很烦人
        # 使用列表来迭代哈希
        # 使用集合来记录已经迭代过的哈希
        self._hashes = []
        self._touched = False
        self._done_hashes = set()
        self._touched_hashes = set()   # 本次实际被修改内容的 hash
        self._hash_log = []           # 本文件 hash 级命令的语义说明行（log 命令收集）

        # 只在ini保存后将修改过的缓冲区写入磁盘，
        # 因为ini可以被备份，而备份缓冲区并不合理。
        # 对于有多个修复的缓冲区：第一次修复将从模组目录中读取，
        # 后续修复将从内存中的这个字典中读取
        self.modified_buffers = {
            # buffer_filepath: buffer_data
        }

        # 获取ini中的所有（未注释的）哈希
        pattern = re.compile(r'\n\s*hash\s*=\s*([a-f0-9]*)', flags=re.IGNORECASE)
        self._hashes = pattern.findall(self.content)
    
    def upgrade(self):
        while len(self._hashes) > 0:
            hash = self._hashes.pop()
            if hash not in self._done_hashes:
                if hash in hash_commands:
                    print(f'\t处理 {hash}:')
                    default_args = DefaultArgs(hash=hash, ini=self, data={}, tabs=2)
                    self.execute(hash_commands[hash], default_args)
                else:
                    print(f'\t跳过 {hash}: 没有可执行的任务')
            else:
                print(f'\t跳过 {hash}: 已经检查/处理过')

            self._done_hashes.add(hash)

        return self

    def execute(self, commands, default_args):
        for command in commands:
            clss = command[0]
            args = command[1] if len(command) > 1 else {}
            instance = clss(**args) if type(args) is dict else clss(*args) 
            result: ExecutionResult = instance.execute(default_args)

            if result.touched:
                self._touched = True
                self._touched_hashes.add(default_args.hash)
            if result.failed:
                print()
                return

            if result.queue_hashes:
                # 只添加我还没有迭代过的哈希
                self._hashes.extend(set(result.queue_hashes).difference(self._done_hashes))

            if result.queue_commands:
                # sub_default_args = DefaultArgs(
                #     hash = default_args.hash,
                #     ini  = default_args.ini,
                #     data = default_args.data,
                #     tabs = default_args.tabs
                # )
                self.execute(result.queue_commands, default_args)

            if result.signal_break:
                return

        return default_args

    def save(self):
        if self._touched:
            basename = os.path.basename(self.filepath).split('.ini')[0]
            dir_path = os.path.abspath(self.filepath.split(basename+'.ini')[0])
            backup_filename = f'DISABLED_BACKUP_{int(time.time())}.{basename}.ini'
            backup_fullpath = os.path.join(dir_path, backup_filename)

            os.rename(self.filepath, backup_fullpath)
            print(_Style.WHITE_BG + _Style.ORANGE + f'已创建备份: {backup_filename} 在 {dir_path}' + _Style.RESET)
            with open(self.filepath, 'w', encoding=self.encoding) as updated_ini:
                updated_ini.write(self.content)
            # 将open（'DISABLED_BACKUP_debug.ini'，'w'，encoding='utf-8'）设置为updated_ini：
            #     updated_ini.write(self.content)

            if len(self.modified_buffers) > 0:
                print('写入更新的缓冲区')
                for filepath, data in self.modified_buffers.items():
                    # === 建议添加的备份逻辑开始 ===
                    # 检查文件是否存在，避免重复备份或文件不存在时报错
                    if os.path.exists(filepath) and not filepath.startswith('DISABLED_'):
                        backup_filepath = os.path.join(
                            os.path.dirname(filepath), 
                            f'DISABLED_BACKUP_{int(time.time())}.{os.path.basename(filepath)}'
                        )
                        # 如果备份文件已存在（极短时间内多次运行），也可以做判断，这里直接覆盖或重命名
                        if not os.path.exists(backup_filepath):
                            try:
                                os.rename(filepath, backup_filepath)
                                print(f'\t已备份缓冲区: {backup_filepath}')
                            except Exception as e:
                                print(f'\t备份缓冲区失败: {e}')
                    # === 建议添加的备份逻辑结束 ===

                    # 原有的写入逻辑
                    with open(filepath, 'wb') as f:
                        f.write(data)
                    print('\t保存: {}'.format(filepath))

            print(_Style.RESET_BG + _Style.GREEN + _Style.BRIGHT + '已对该ini文件进行更新修复' + _Style.RESET)
        else:
            print(_Style.WHITE_BG + _Style.RED + '没有对该ini文件进行更新修复,因为所有hash已经是最新的了' + _Style.RESET)
        print()

    def has_hash(self, hash):
        return (
            (hash in self._hashes)
            or (hash in self._done_hashes)
        )


# MARK: 命令

def get_critical_content(section):
    hash = None
    match_first_index = None
    critical_lines = []
    pattern = re.compile(r'^\s*(.*?)\s*=\s*(.*?)\s*$', flags=re.IGNORECASE)

    for line in section.splitlines():
        line_match = pattern.match(line)
        
        if line.strip().startswith('['):
            continue
        elif line_match and line_match.group(1).lower() == 'hash':
            hash = line_match.group(2)
        elif line_match and line_match.group(1).lower() == 'match_first_index':
            match_first_index = line_match.group(2)
        else:
            critical_lines.append(line)

    return '\n'.join(critical_lines), hash, match_first_index


# 返回命令列表使用的所有资源
# 硬编码仅返回vb1，即目前的texcoord资源
# （TextureOverride部分是特殊的命令列表）
def process_commandlist(ini_content: str, commandlist: str, target: str):
    line_pattern = re.compile(r'^\s*(run|{})\s*=\s*(.*)\s*$'.format(target), flags=re.IGNORECASE)
    resources = []

    for line in commandlist.splitlines():
        line_match = line_pattern.match(line)
        if not line_match: continue

        if line_match.group(1) == target:
            resources.append(line_match.group(2))

        # Must check the commandlists that are run within the
        # the current commandlist for the resource as well
        # Recursion yay
        elif line_match.group(1) == 'run':
            commandlist_title = line_match.group(2)
            pattern = get_section_title_pattern(commandlist_title)
            commandlist_match = pattern.search(ini_content + '\n[')
            if commandlist_match:
                sub_resources = process_commandlist(ini_content, commandlist_match.group(1), target)
                resources.extend(sub_resources)

    return resources


@dataclass
class DefaultArgs():
    hash : str
    ini  : Ini
    tabs : int
    data : dict[str, str]


@dataclass
class ExecutionResult():
    touched        : bool = False
    failed         : bool = False
    signal_break   : bool = False
    queue_hashes   : tuple[str] = None
    queue_commands : tuple[str] = None


@dataclass(init=False)
class log():
    text: tuple[str]

    def __init__(self, *text):
        self.text = text

    def execute(self, default_args: DefaultArgs):
        tabs        = default_args.tabs

        info  = self.text[0]
        hash  = self.text[1] if len(self.text) > 1 else ''
        title = self.text[2] if len(self.text) > 2 else ''
        rest  = self.text[3:] if len(self.text) > 3 else []

        s = '{}{:34}'.format('\t'*tabs, info)
        if hash  : s += ' - {:8}'.format(hash)
        if title : s += ' - {}'.format(title) 
        if rest  : s += ' - '.join(rest)

        try:
            ini = default_args.ini
            if getattr(ini, '_hash_log', None) is not None:
                ini._hash_log.append((getattr(default_args, 'hash', '') or '', s.strip()))
        except Exception:
            pass
        print(s)

        return ExecutionResult(
            touched        = False,
            failed         = False,
            signal_break   = False,
            queue_hashes   = None,
            queue_commands = None
        )


@dataclass
class update_hash():
    new_hash: str

    def execute(self, default_args: DefaultArgs):
        ini         = default_args.ini
        active_hash = default_args.hash

        pattern = re.compile(r'(\n\s*)(hash\s*=\s*{})'.format(active_hash), flags=re.IGNORECASE)
        ini.content, sub_count = pattern.subn(r'\1hash = {}\n; \2'.format(self.new_hash), ini.content)

        default_args.hash = self.new_hash

        if sub_count:
            note = '+ hash = {} 更新为 hash = {} ×{} 处'.format(active_hash, self.new_hash, sub_count)
        else:
            note = '+ hash = {} 已是最新'.format(active_hash)
        return ExecutionResult(
            touched        = sub_count > 0,
            failed         = False,
            signal_break   = False,
            queue_hashes   = (self.new_hash,),
            queue_commands = (
                (log, (note,)),
            )
        )


@dataclass
class comment_sections():

    def execute(self, default_args: DefaultArgs):
        ini  = default_args.ini
        hash = default_args.hash

        pattern = get_section_hash_pattern(hash)
        new_ini_content = ''   # ini内容，所有匹配的部分都已注释

        prev_j = 0
        commented_count = 0
        section_matches = pattern.finditer(ini.content)
        for section_match in section_matches:
            i, j = section_match.span(1)
            commented_section = '\n'.join(['; ' + line for line in section_match.group(1).splitlines()])
            commented_count  += 1

            new_ini_content += ini.content[prev_j:i] + commented_section
            prev_j = j

        new_ini_content += ini.content[prev_j:]
        
        ini.content = new_ini_content

        return ExecutionResult(
            touched        = True,
            failed         = False,
            signal_break   = False,
            queue_hashes   = None,
            queue_commands = (
                (log, ('- Commented {} relevant section(s)'.format(commented_count),)),
            )
        )


@dataclass
class comment_commandlists():
    commandlist_title: str

    def execute(self, default_args: DefaultArgs):
        ini  = default_args.ini

        pattern = get_section_title_pattern(self.commandlist_title)
        new_ini_content = ''   # ini内容与匹配的命令列表已注释掉

        prev_j = 0
        commented_count = 0
        commandlist_matches = pattern.finditer(ini.content)
        for commandlist_match in commandlist_matches:
            i, j = commandlist_match.span(1)
            commented_commandlist = '\n'.join(['; ' + line for line in commandlist_match.group(1).splitlines()])
            commented_count  += 1

            new_ini_content += ini.content[prev_j:i] + commented_commandlist
            prev_j = j

        new_ini_content += ini.content[prev_j:]
        
        ini.content = new_ini_content

        return ExecutionResult(
            touched        = True,
            failed         = False,
            signal_break   = False,
            queue_hashes   = None,
            queue_commands = (
                (log, ('- Commented {} relevant commandlist(s)'.format(commented_count),)),
            )
        )


@dataclass(kw_only=True)
class remove_section():
    capture_content : str = None
    capture_position: str = None

    def execute(self, default_args: DefaultArgs):
        ini         = default_args.ini
        active_hash = default_args.hash
        data        = default_args.data

        pattern = get_section_hash_pattern(active_hash)
        section_match = pattern.search(ini.content)
        if not section_match: raise Exception('Bad regex')
        start, end = section_match.span(1)

        if self.capture_content:
            data[self.capture_content] = get_critical_content(section_match.group(1))[0]
        if self.capture_position:
            data[self.capture_position] = str(start)

        ini.content = ini.content[:start] + ini.content[end:]

        return ExecutionResult(
            touched        = True,
            failed         = False,
            signal_break   = False,
            queue_hashes   = None,
            queue_commands = None
        )


@dataclass(kw_only=True)
class capture_section():
    capture_content  : str = None
    capture_position : str = None

    def execute(self, default_args: DefaultArgs):
        ini         = default_args.ini
        active_hash = default_args.hash
        data        = default_args.data

        pattern = get_section_hash_pattern(active_hash)
        section_match = pattern.search(ini.content)
        if not section_match: raise Exception('Bad regex')
        _, end = section_match.span(1)

        if self.capture_content:
            data[self.capture_content] = get_critical_content(section_match.group(1))[0]
        if self.capture_position:
            data[self.capture_position] = str(end + 1)

        return ExecutionResult(
            touched        = False,
            failed         = False,
            signal_break   = False,
            queue_hashes   = None,
            queue_commands = None
        )


@dataclass(kw_only=True)
class create_new_section():
    section_content  : str
    saved_position   : str = None
    capture_position : str = None

    def execute(self, default_args: DefaultArgs):
        ini         = default_args.ini
        data        = default_args.data

        pos = -1
        if self.saved_position and self.saved_position in data:
            pos = int(data[self.saved_position])

        for placeholder, value in data.items():
            if placeholder.startswith('_'):
                # conditions are not to be used for substitution
                continue
            self.section_content = self.section_content.replace(placeholder, value)

        # 半损坏/修复的mods'ini将没有我们期望的对象索引
        # 也可能由于哈希命令中的拼写错误而触发
        for emoji in ['🍰', '🌲', '🤍']:
            if emoji in self.section_content:
                print('Section substitution failed')
                print(self.section_content)
                return ExecutionResult(
                    touched        = False,
                    failed         = True,
                    signal_break   = False,
                    queue_hashes   = None,
                    queue_commands = None
                )
  
        if self.capture_position:
            data[self.capture_position] = str(len(self.section_content) + pos)

        ini.content = ini.content[:pos] + self.section_content + ini.content[pos:]

        return ExecutionResult(
            touched        = True,
            failed         = False,
            signal_break   = False,
            queue_hashes   = None,
            queue_commands = None
        )


@dataclass(kw_only=True)
class transfer_indexed_sections():
    trg_indices: tuple[str] = None
    src_indices: tuple[str] = None

    def execute(self, default_args: DefaultArgs):
        ini         = default_args.ini
        hash        = default_args.hash

        # 扫描该 hash 下实际存在的索引（match_first_index）
        p = get_section_hash_pattern(hash)
        section_matches = list(p.finditer(ini.content))

        actual_indices = set()
        for m in section_matches:
            idx = re.search(r'\n\s*match_first_index\s*=\s*([\d]+)', m.group(1), flags=re.IGNORECASE)
            if idx:
                actual_indices.add(idx.group(1))

        if not actual_indices:
            # 没有索引节，无需迁移
            return ExecutionResult()

        # 推导节名前缀（与原实现一致；仅用于新建 ib = null 节的命名）
        title = None
        TITLE = re.compile(r'^\[([^\]]+)\]')
        for m in section_matches:
            mt = re.match(r'^\[TextureOverride(.*?)\]', m.group(1), flags=re.IGNORECASE)
            if not mt: continue
            if re.search(r'\n\s*match_first_index\s*=', m.group(1), flags=re.IGNORECASE):
                title = mt.group(1)[:-1]
            else:
                title = mt.group(1)[:-2]
            break

        # 配对：src -> trg；'-1' 表示没有源节，新建 ib = null 节；缺失的 src 跳过并记录
        # （ib = null 节用 'Null{索引}' 命名，避免与保留的原节重名）
        remap      = {}
        null_pairs = []
        missing    = []
        for trg_index, src_index in zip(self.trg_indices, self.src_indices):
            if src_index == '-1':
                null_pairs.append(trg_index)
            elif src_index in actual_indices:
                remap[src_index] = trg_index
            else:
                missing.append(src_index)

        # 原地改写 match_first_index / match_index_count：只动配对的节，其余一律不碰
        # （match_index_count 是分段边界：前一段的 count 常等于后一段的 first_index，
        #   所以 count 也参与同一张位置映射，即使该节自身的 first_index 未变）
        new_content = ''
        prev_end    = 0
        migrated    = 0
        section_notes = []
        for m in section_matches:
            new_content += ini.content[prev_end:m.start()]

            new_section = m.group(0)
            idx = re.search(r'\n\s*match_first_index\s*=\s*([\d]+)', new_section, flags=re.IGNORECASE)
            if idx and idx.group(1) in remap and remap[idx.group(1)] != idx.group(1):
                new_section = re.sub(
                    r'(\n\s*match_first_index\s*=\s*)[\d]+',
                    r'\g<1>' + remap[idx.group(1)],
                    new_section, count=1, flags=re.IGNORECASE
                )

            cnt = re.search(r'\n\s*match_index_count\s*=\s*([\d]+)', new_section, flags=re.IGNORECASE)
            if cnt and cnt.group(1) in remap and remap[cnt.group(1)] != cnt.group(1):
                new_section = re.sub(
                    r'(\n\s*match_index_count\s*=\s*)[\d]+',
                    r'\g<1>' + remap[cnt.group(1)],
                    new_section, count=1, flags=re.IGNORECASE
                )

            if new_section != m.group(0):
                tmt = TITLE.search(m.group(0))
                tname = tmt.group(1) if tmt else '?'
                old_sec = m.group(0)
                oi = re.search(r'match_first_index\s*=\s*([\d]+)', old_sec, flags=re.IGNORECASE)
                ni = re.search(r'match_first_index\s*=\s*([\d]+)', new_section, flags=re.IGNORECASE)
                oc = re.search(r'match_index_count\s*=\s*([\d]+)', old_sec, flags=re.IGNORECASE)
                nc = re.search(r'match_index_count\s*=\s*([\d]+)', new_section, flags=re.IGNORECASE)
                if oi and ni and oi.group(1) != ni.group(1):
                    section_notes.append('+ {}: match_first_index = {} 更新为 {}'.format(tname, oi.group(1), ni.group(1)))
                if oc and nc and oc.group(1) != nc.group(1):
                    section_notes.append('+ {}: match_index_count = {} 更新为 {}'.format(tname, oc.group(1), nc.group(1)))
                new_content += new_section
                migrated += 1
            else:
                new_content += m.group(0)

            # 新建 ib = null 节（'-1' 对），插在该 hash 最后一个节之后
            if m is section_matches[-1] and null_pairs:
                for trg_index in null_pairs:
                    new_content += '\n'.join([
                        f'[TextureOverride{title}Null{trg_index}]',
                        f'hash = {hash}',
                        f'match_first_index = {trg_index}',
                        'ib = null',
                        '',
                        ''
                    ])

            prev_end = m.end()

        new_content += ini.content[prev_end:]

        changed = (migrated > 0 or bool(null_pairs))
        if changed:
            ini.content = new_content

        queue_commands = []
        if migrated:
            queue_commands.append((log, ('+ 迁移 {} 个索引节'.format(migrated),)))
        if null_pairs:
            queue_commands.append((log, ('+ 新建 {} 个 ib = null 节'.format(len(null_pairs)),)))
        if missing:
            queue_commands.append((log, ('/ 跳过缺失的源索引: {}'.format(', '.join(missing)),)))
        for note in section_notes:
            queue_commands.append((log, (note,)))

        return ExecutionResult(
            touched        = changed,
            failed         = False,
            signal_break   = False,
            queue_hashes   = None,
            queue_commands = tuple(queue_commands) if queue_commands else None
        )


@dataclass()
class multiply_section_if_missing():
    equiv_hashes: tuple[str] | str
    extra_title : tuple[str]

    def execute(self, default_args: DefaultArgs):
        ini  = default_args.ini

        if (type(self.equiv_hashes) is not tuple):
            self.equiv_hashes = (self.equiv_hashes,)
        for equiv_hash in self.equiv_hashes:
            if ini.has_hash(equiv_hash):
                return ExecutionResult(
                    touched        = False,
                    failed         = False,
                    signal_break   = False,
                    queue_hashes   = None,
                    queue_commands = (
                        (log, ('/ 跳过部分高低显',  f'{equiv_hash}', f'[...{self.extra_title}]',)),
                    ),
                )
        equiv_hash = self.equiv_hashes[0]

        content = '\n'.join([
            '',
            f'[TextureOverride{self.extra_title}]',
            f'hash = {equiv_hash}',
            '🍰',
            '',
        ])

        return ExecutionResult(
            touched        = False,
            failed         = False,
            signal_break   = False,
            queue_hashes   = (equiv_hash,),
            queue_commands = (
                (log,                ('+ 添加对应高低显', f'{equiv_hash}', f'[...{self.extra_title}]')),
                (capture_section,    {'capture_content': '🍰', 'capture_position': '🌲'}),
                (create_new_section, {'saved_position': '🌲', 'section_content': content}),
            ),
        )


@dataclass()
class add_ib_check_if_missing():

    def execute(self, default_args: DefaultArgs):
        ini  = default_args.ini
        hash = default_args.hash
        
        pattern         = get_section_hash_pattern(hash)
        section_matches = pattern.finditer(ini.content)

        has_indexed = False
        needs_check = False

        # 第一遍：判断是否存在索引节，以及是否已经都有 run = CommandListSkinTexture
        for section_match in section_matches:
            if not re.search(r'\n\s*match_first_index\s*=', section_match.group(1), flags=re.IGNORECASE):
                continue
            has_indexed = True
            if not re.search(r'\n\s*run\s*=\s*CommandListSkinTexture', section_match.group(1), flags=re.IGNORECASE):
                needs_check = True
                break

        if not has_indexed:
            # 没有索引节，重新遍历，找含 handling = skip 的无索引节
            last_section_match = None
            found_skip = False
            for section_match in pattern.finditer(ini.content):
                last_section_match = section_match
                if re.search(r'\n\s*handling\s*=\s*skip', section_match.group(1), flags=re.IGNORECASE):
                    found_skip = True
                    if not re.search(r'\n\s*run\s*=\s*CommandListSkinTexture', section_match.group(1),
                                     flags=re.IGNORECASE):
                        needs_check = True
                    break

            # 兜底：没有 handling = skip 的节，取最后一个节
            if not found_skip and last_section_match is not None:
                if not re.search(r'\n\s*run\s*=\s*CommandListSkinTexture', last_section_match.group(1),
                                 flags=re.IGNORECASE):
                    needs_check = True

        if not needs_check:
            return ExecutionResult(
                touched=False,
                failed=False,
                signal_break=False,
                queue_hashes=None,
                queue_commands=(
                    (log, ('/ 跳过 `run = CommandListSkinTexture` Addition',)),
                ),
            )

        # 第二遍：原地修改，只动需要动的节，其余全部不碰
        section_matches = pattern.finditer(ini.content)
        new_content = ini.content
        for section_match in section_matches:
            has_index = re.search(r'\n\s*match_first_index\s*=', section_match.group(1), flags=re.IGNORECASE)
            has_run = re.search(r'\n\s*run\s*=\s*CommandListSkinTexture', section_match.group(1), flags=re.IGNORECASE)
            has_skip = re.search(r'\n\s*handling\s*=\s*skip', section_match.group(1), flags=re.IGNORECASE)

            if has_run:
                continue  # 已有，跳过

            if has_indexed and has_index:
                # 索引节，在 match_first_index 后插入
                new_section = re.sub(
                    r'\n\s*match_first_index\s*=.*?\n',
                    r'\g<0>run = CommandListSkinTexture\n',
                    section_match.group(),
                    flags=re.IGNORECASE, count=1
                )
                new_content = new_content.replace(section_match.group(), new_section, 1)

            elif not has_indexed:
                if has_skip:
                    # 无索引情况，只动 handling = skip 的主节，在 hash 行后插入
                    new_section = re.sub(
                        r'\n\s*hash\s*=.*?\n',
                        r'\g<0>run = CommandListSkinTexture\n',
                        section_match.group(),
                        flags=re.IGNORECASE, count=1
                    )
                    new_content = new_content.replace(section_match.group(), new_section, 1)
                    break  # 只动第一个 handling = skip 的节，后续不再处理

            # 其他无索引节（CheckHash 等）→ 完全不动

        # 兜底：第二遍没有找到 handling = skip 的节，对最后一个节插入
        if not has_indexed and not any(
                re.search(r'\n\s*handling\s*=\s*skip', m.group(1), flags=re.IGNORECASE)
                for m in pattern.finditer(ini.content)
        ):
            last_match = None
            for last_match in pattern.finditer(ini.content):
                pass
            if last_match and not re.search(r'\n\s*run\s*=\s*CommandListSkinTexture', last_match.group(1),
                                            flags=re.IGNORECASE):
                new_section = re.sub(
                    r'\n\s*hash\s*=.*?\n',
                    r'\g<0>run = CommandListSkinTexture\n',
                    last_match.group(),
                    flags=re.IGNORECASE, count=1
                )
                new_content = new_content.replace(last_match.group(), new_section, 1)

        ini.content = new_content


        return ExecutionResult(
            touched=True,
            failed=False,
            signal_break=False,
            queue_hashes=None,
            queue_commands=(
                (log, ('+ 添加 `run = CommandListSkinTexture`',)),
            ),
        )


@dataclass
class add_section_if_missing():
    equiv_hashes    : tuple[str] | str
    section_title   : str = None
    section_content : str = field(default='')

    def execute(self, default_args: DefaultArgs):
        ini = default_args.ini

        if (type(self.equiv_hashes) is not tuple):
            self.equiv_hashes = (self.equiv_hashes,)
        for equiv_hash in self.equiv_hashes:
            if ini.has_hash(equiv_hash):
                return ExecutionResult(
                    touched        = False,
                    failed         = False,
                    signal_break   = False,
                    queue_hashes   = None,
                    queue_commands = (
                        (log, ('/ 跳过节添加', equiv_hash, f'[...{self.section_title}]',)),
                    ),
                )
        equiv_hash = self.equiv_hashes[0]

        section = '\n[TextureOverride{}]\n'.format(self.section_title)
        section += 'hash = {}\n'.format(equiv_hash)
        section += self.section_content

        return ExecutionResult(
            touched        = False,
            failed         = False,
            signal_break   = False,
            queue_hashes   = (equiv_hash,),
            queue_commands = (
                (log,                ('+ 添加节', equiv_hash, f'[...{self.section_title}]',)),
                (capture_section,    {'capture_position': '🌲'}),
                (create_new_section, {'saved_position': '🌲', 'section_content': section}),
            ),
        )


@dataclass
class zzz_13_remap_texcoord():
    id: str
    old_format: tuple[str] # = ('4B','2e','2f','2e')
    new_format: tuple[str] # = ('4B','2f','2f','2f')

    def execute(self, default_args: DefaultArgs):
        ini  = default_args.ini
        hash = default_args.hash
        tabs = default_args.tabs

        # 预计算新缓冲区的步幅和偏移量
        # 检查现有缓冲区步幅是否符合我们的预期
        # 在重新映射之前
        if (len(self.old_format) != len(self.new_format)): raise Exception()
        old_stride = struct.calcsize('<' + ''.join(self.old_format))
        new_stride = struct.calcsize('<' + ''.join(self.new_format))

        offset = 0
        offsets = [0]
        for format_chunk in self.old_format:
            offset += struct.calcsize(f'<{format_chunk}')
            offsets.append(offset)

        # 调试
        # print(f'\t\t旧格式步幅: {struct.calcsize('<' + ''.join(self.old_format))}')
        # print(f'\t\t新格式步幅: {struct.calcsize('<' + ''.join(self.new_format))}')
        # print(f'\t\t缓冲区步幅: {stride}')
        # print(f'\t\t偏移量: {offsets}')

        # 需要找到这个哈希直接使用的所有Texcoord资源
        # 通过TextureOverrides或通过Commandlists运行...
        pattern = get_section_hash_pattern(hash)
        section_match = pattern.search(ini.content)
        resources = process_commandlist(ini.content, section_match.group(1), 'vb1')

        # - 匹配资源部分以找到缓冲区的文件名
        # - 更新资源的步幅值，而不是再次迭代
        buffer_filenames = set()
        line_pattern = re.compile(r'^\s*(filename|stride)\s*=\s*(.*)\s*$', flags=re.IGNORECASE)
        for resource in resources:
            pattern = get_section_title_pattern(resource)
            resource_section_match = pattern.search(ini.content)
            if not resource_section_match: continue

            modified_resource_section = []
            for line in resource_section_match.group(1).splitlines():
                line_match = line_pattern.match(line)
                if not line_match:
                    modified_resource_section.append(line)

                # 捕获缓冲区文件名
                elif line_match.group(1) == 'filename':
                    modified_resource_section.append(line)
                    buffer_filenames.add(line_match.group(2))

                # 在ini中更新资源的步幅值
                elif line_match.group(1) == 'stride':
                    stride = int(line_match.group(2))
                    if stride != old_stride:
                        print('{}X 警告 [{}]! 预期的缓冲区步幅为 {} 但得到的是 {}。正在覆盖并继续。'.format('\t'*tabs, resource, old_stride, stride))
                    #     raise Exception('Remap failed for {}! Expected buffer stride {} but got {} instead.'.format(resource, old_stride, stride))

                    modified_resource_section.append('stride = {}'.format(new_stride))
                    modified_resource_section.append(';'+line)

            # 更新ini
            modified_resource_section = '\n'.join(modified_resource_section)
            i, j = resource_section_match.span(1)
            ini.content = ini.content[:i] + modified_resource_section + ini.content[j:]

        for buffer_filename in buffer_filenames:
            buffer_filepath = Path(Path(ini.filepath).parent/buffer_filename)
            buffer_dict_key = str(buffer_filepath.absolute())

            if buffer_dict_key not in global_modified_buffers:
                global_modified_buffers[buffer_dict_key] = []
            fix_id = f'{self.id}-texcoord_remap'
            if fix_id in global_modified_buffers[buffer_dict_key]: continue
            else: global_modified_buffers[buffer_dict_key].append(fix_id)

            if buffer_dict_key not in ini.modified_buffers:
                buffer = buffer_filepath.read_bytes()
            else:
                buffer = ini.modified_buffers[buffer_dict_key]

            vcount = len(buffer) // stride
            new_buffer = bytearray()
            for i in range(vcount):
                for j, (old_chunk, new_chunk) in enumerate(zip(self.old_format, self.new_format)):

                    if offsets[j] < stride and offsets[j+1] <= stride:

                        if old_chunk != new_chunk:
                            # 硬编码VColor重新映射
                            if (j == 0 and old_chunk == '4B' and new_chunk == '4f'):
                                new_buffer.extend(struct.pack('<4f', *[b/255 for b in struct.unpack_from('<4B', buffer, i*stride + 0)]))
                            elif (j == 0 and old_chunk == '4f' and new_chunk == '4B'):
                                new_buffer.extend(struct.pack('<4B', *[int(b*255) for b in struct.unpack_from('<4f', buffer, i*stride + 0)]))

                            # 通用元素重新映射
                            else:
                                new_buffer.extend(struct.pack(f'<{new_chunk}', *struct.unpack_from(f'<{old_chunk}', buffer, i*stride+offsets[j])))

                        # 不需要重新映射元素
                        else:
                            new_buffer.extend(buffer[i*stride + offsets[j]: i*stride + offsets[j+1]])

                    # 模texcoord顶点数据没有达到预期的旧步幅
                    else: # 应对
                        new_buffer.extend(struct.pack(f'<{new_chunk}', *([0] * int(new_chunk[0]))))
            
            ini.modified_buffers[buffer_dict_key] = new_buffer    

        return ExecutionResult(
            touched=True
        )


# 已弃用。使用通用的remap_texcoord代替
@dataclass
class zzz_12_shrink_texcoord_color():
    id: str

    def execute(self, default_args: DefaultArgs):
        ini  = default_args.ini
        hash = default_args.hash

        # 需要找到这个哈希直接使用的所有Texcoord资源
        # 通过TextureOverrides或通过Commandlists运行...
        pattern = get_section_hash_pattern(hash)
        section_match = pattern.search(ini.content)
        resources = process_commandlist(ini.content, section_match.group(1), 'vb1')

        # - 匹配资源部分以找到缓冲区的文件名 
        # - 更新资源的步幅值，而不是再次迭代
        buffer_filenames = set()
        line_pattern = re.compile(r'^\s*(filename|stride)\s*=\s*(.*)\s*$', flags=re.IGNORECASE)
        for resource in resources:
            pattern = get_section_title_pattern(resource)
            resource_section_match = pattern.search(ini.content)
            if not resource_section_match: continue

            modified_resource_section = []
            for line in resource_section_match.group(1).splitlines():
                line_match = line_pattern.match(line)
                if not line_match:
                    modified_resource_section.append(line)

                # 捕获缓冲区文件名
                elif line_match.group(1) == 'filename':
                    modified_resource_section.append(line)
                    buffer_filenames.add(line_match.group(2))

                # 在ini中更新资源的步幅值
                elif line_match.group(1) == 'stride':
                    stride = int(line_match.group(2))
                    modified_resource_section.append('stride = {}'.format(stride - 12))
                    modified_resource_section.append(';'+line)

            # 更新ini
            modified_resource_section = '\n'.join(modified_resource_section)
            i, j = resource_section_match.span(1)
            ini.content = ini.content[:i] + modified_resource_section + ini.content[j:]

        for buffer_filename in buffer_filenames:
            buffer_filepath = Path(Path(ini.filepath).parent/buffer_filename)
            buffer_dict_key = str(buffer_filepath.absolute())

            if buffer_dict_key not in global_modified_buffers:
                global_modified_buffers[buffer_dict_key] = []
            fix_id = f'{self.id}-zzz_12_shrink_texcoord_color'
            if fix_id in global_modified_buffers[buffer_dict_key]: continue
            else: global_modified_buffers[buffer_dict_key].append(fix_id)

            if buffer_dict_key not in ini.modified_buffers:
                buffer = buffer_filepath.read_bytes()
            else:
                buffer = ini.modified_buffers[buffer_dict_key]

            vcount = len(buffer) // stride
            new_buffer = bytearray()
            for i in range(vcount):
                # 调试(*[ int((f*255)) for f in struct.unpack_from('<4f', buffer, i*stride + 0)])
                new_buffer.extend(struct.pack(
                        '<4B',
                        *[
                            int(f * 255)
                            for f in struct.unpack_from('<4f', buffer, i*stride + 0)
                        ]
                    ))
                new_buffer.extend(buffer[i*stride + 16: i*stride + stride])
            
            ini.modified_buffers[buffer_dict_key] = new_buffer            

        return ExecutionResult(
            touched=True
        )

@dataclass
class update_buffer_blend_indices():
    hash       : str
    old_indices: tuple[int]
    new_indices: tuple[int]

    def execute(self, default_args: DefaultArgs):
        ini  = default_args.ini

        # 需要找到这个哈希直接通过TextureOverrides或通过Commandlists使用的所有Texcoord资源
        pattern = get_section_hash_pattern(self.hash)
        section_match = pattern.search(ini.content)
        resources = process_commandlist(ini.content, section_match.group(1), 'vb2')

        # - 匹配资源部分以找到缓冲区的文件名
        # - 更新资源的stride值，而不是再次迭代
        buffer_filenames = set()
        line_pattern = re.compile(r'^\s*(filename|stride)\s*=\s*(.*)\s*$', flags=re.IGNORECASE)
        for resource in resources:
            pattern = get_section_title_pattern(resource)
            resource_section_match = pattern.search(ini.content)
            if not resource_section_match: continue

            modified_resource_section = []
            for line in resource_section_match.group(1).splitlines():
                line_match = line_pattern.match(line)
                if not line_match:
                    modified_resource_section.append(line)

                # 捕获缓冲区文件名
                elif line_match.group(1) == 'filename':
                    modified_resource_section.append(line)
                    buffer_filenames.add(line_match.group(2))

        for buffer_filename in buffer_filenames:
            buffer_filepath = Path(Path(ini.filepath).parent/buffer_filename)
            buffer_dict_key = str(buffer_filepath.absolute())

            if buffer_dict_key not in ini.modified_buffers:
                buffer = buffer_filepath.read_bytes()
            else:
                buffer = ini.modified_buffers[buffer_dict_key]
    
            new_buffer = bytearray()
            blend_stride = 32
            vertex_count = len(buffer)//blend_stride
            for i in range(vertex_count):
                blend_weights  = struct.unpack_from('<4f', buffer, i*blend_stride + 0)
                blend_indices  = struct.unpack_from('<4I', buffer, i*blend_stride + 16)

                new_buffer.extend(struct.pack('<4f4I', *blend_weights, *[
                    vgx if vgx not in self.old_indices
                    else self.new_indices[self.old_indices.index(vgx)]
                    for vgx in blend_indices
                ]))

            ini.modified_buffers[buffer_dict_key] = new_buffer

        return ExecutionResult(
            touched=True
        )

@dataclass
class convert_to_slots():
    hash        : str              # = IB HASH
    slot_hashes : dict[int, tuple] # = {
    #     SLOT: [list of texture hashes that go in this slot...],
    #     ...
    # }
    '''
    If a slot is already overriden in the ib section, then all discovered sections with texture hashes
    corresponding to this slot will be commented out. If the ib section lacks an override for the slot,
    then the first discovered section with texture hash corresponding to this slot will be converted to
    a commandlist and have `this` replaced with `ps-t#`. A `run = CommandList` line will be added to the
    ib override before any drawindexed lines. The remaining sections with texture hashes corresponding
    to this slot will be commented out if they exist.
    '''

    def execute(self, default_args: DefaultArgs):
        pass

hash_commands = {
    # MARK: Alice爱丽丝
    #IB
    'd131acb1': [(log, ('2.1: Alice Hair IB Hash',)), (add_ib_check_if_missing,)],
    '8a512b21': [(log, ('2.1: Alice Body IB Hash',)), (add_ib_check_if_missing,)],
    '625c2692': [(log, ('2.1: Alice Legs IB Hash',)), (add_ib_check_if_missing,)],
    'b078ff22': [(log, ('2.1: Alice Face IB Hash',)), (add_ib_check_if_missing,)],
    #VB
    
    #Texture纹理
    # Face脸部
    '9f3e582c': [
        (log,                           ('2.1: Alice FaceA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('33fdeb6d', 'Alice.FaceA.Diffuse.1024')),
    ],
    '33fdeb6d': [
        (log,                           ('2.1: Alice FaceA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('9f3e582c', 'Alice.FaceA.Diffuse.2048')),
    ],

    # Hair头发 Legs
    '705caac9': [
        (log,                           ('2.1: Alice HairA, LegsA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   (('5f504114', '91d2f9fd',), 'Alice.HairA.Diffuse.1024')),
    ],
    '91d2f9fd': [
        (log,                           ('2.1: Alice HairA, LegsA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('705caac9', 'Alice.HairA.Diffuse.2048')),
    ],
    '03543db2': [
        (log,                           ('2.1: Alice HairA, LegsA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('6c957d8f', 'Alice.HairA.LightMap.1024')),
    ],
    '6c957d8f': [
        (log,                           ('2.1: Alice HairA, LegsA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('03543db2', 'Alice.HairA.LightMap.2048')),
    ],
    '508530fe': [
        (log,                           ('2.1: Alice HairA, LegsA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('bc4c87fd', 'Alice.HairA.MaterialMap.1024')),
    ],
    'bc4c87fd': [
        (log,                           ('2.1: Alice HairA, LegsA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('508530fe', 'Alice.HairA.MaterialMap.2048')),
    ],

    # Body身体
    '269185ed': [
        (log,                           ('2.1: Alice BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('9201609a', 'Alice.BodyA.Diffuse.1024')),
    ],
    '9201609a': [
        (log,                           ('2.1: Alice BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('269185ed', 'Alice.BodyA.Diffuse.2048')),
    ],
    '0d72cb85': [
        (log,                           ('2.1: Alice BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('548623cd', 'Alice.BodyA.LightMap.1024')),
    ],
    '548623cd': [
        (log,                           ('2.1: Alice BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('0d72cb85', 'Alice.BodyA.LightMap.2048')),
    ],
    '95967afb': [
        (log,                           ('2.1: Alice BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('e05e4c54', 'Alice.BodyA.MaterialMap.1024')),
    ],
    'e05e4c54': [
        (log,                           ('2.1: Alice BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('95967afb', 'Alice.BodyA.MaterialMap.2048')),
    ],

    # MARK: AliceSkin爱丽丝皮肤
    #IB
    'cf8612e6': [(log, ('2.1: AliceSkin Body IB Hash',)), (add_ib_check_if_missing,)],
    #VB
    #Texture纹理
    # Body身体
    '18601d57': [
        (log,                           ('2.1: AliceSkin BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('7283db21', 'AliceSkin.BodyA.Diffuse.1024')),
    ],
    '7283db21': [
        (log,                           ('2.1: AliceSkin BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('18601d57', 'AliceSkin.BodyA.Diffuse.2048')),
    ],
    '3409fcce': [
        (log,                           ('2.1: AliceSkin BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('8087d734', 'AliceSkin.BodyA.LightMap.1024')),
    ],
    '8087d734': [
        (log,                           ('2.1: AliceSkin BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('3409fcce', 'AliceSkin.BodyA.LightMap.2048')),
    ],
    '212fc22a': [
        (log,                           ('2.1: AliceSkin BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('e4f01bb0', 'AliceSkin.BodyA.MaterialMap.1024')),
    ],
    'e4f01bb0': [
        (log,                           ('2.1: AliceSkin BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('212fc22a', 'AliceSkin.BodyA.MaterialMap.2048')),
    ],


    # MARK: Anby安比
    #IB
    '5c0240db': [(log, ('1.0: Anby Hair IB Hash',)), (add_ib_check_if_missing,)],
    '4816de84': [(log, ('1.0: Anby Body IB Hash',)), (add_ib_check_if_missing,)],
    '19df8e84': [(log, ('1.0: Anby Face IB Hash',)), (add_ib_check_if_missing,)],
    #VB
    #不再提供对脸部vb的修复，不建议对脸部模型进行修改，可能会导致脸部贴图错位
    #'ba016a6e': [(log, ('1.7 -> 2.0: Anby Face Texcoord Hash',)),    (update_hash, ('f818271a',)),],

    #Remap
    # reverted in 1.2
    # '496a781d': [
    #     (log, ('1.0: -> 1.1: Anby Hair Texcoord Hash',)),
    #     (update_hash, ('39538886',)),
    #     (log, ('+ Remapping texcoord buffer from stride 20 to 32',)),
    #     (update_buffer_element_width, (('BBBB', 'ee', 'ff', 'ee'), ('ffff', 'ee', 'ff', 'ee'), '1.1')),
    #     (log, ('+ Setting texcoord vcolor alpha to 1',)),
    #     (update_buffer_element_value, (('ffff', 'ee', 'ff', 'ee'), ('xxx1', 'xx', 'xx', 'xx'), '1.1'))
    # ],

    '39538886': [
        (log, ('1.1 -> 1.2: Anby Hair Texcoord Hash',)),
        (update_hash, ('496a781d',)),
        (log, ('+ Remapping texcoord buffer',)),
        (zzz_12_shrink_texcoord_color, ('1.2',))
    ],

    #Texture纹理
    # Face脸部
    'cc114f4f': [(log, ('1.5 -> 1.6: Anby FaceA Diffuse 1024p Hash',)), (update_hash, ('692c6d2b',))],
    '692c6d2b': [
        (log,                           ('1.6: Anby FaceA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   (('05d7b504', '2a29cb9b', '2a23f612'), 'Anby.FaceA.Diffuse.2048')),
    ],
    '2a23f612': [(log, ('1.5 -> 1.6: Anby FaceA Diffuse 2048p Hash',)), (update_hash, ('05d7b504',))],
    '2a29cb9b': [(log, ('1.0 -> 1.4: Anby FaceA Diffuse 2048p Hash',)), (update_hash, ('2a23f612',))],
    '05d7b504': [
        (log,                           ('1.6: Anby FaceA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   (('692c6d2b', 'cc114f4f'), 'Anby.FaceA.Diffuse.1024')),
    ],

    # Hair头发
    '6ea0023c': [
        (log,                           ('1.0: Anby HairA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('5c0240db', 'Anby.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('7c7f96d2', 'Anby.HairA.Diffuse.1024')),
    ],
    '7c7f96d2': [
        (log,                           ('1.0: Anby HairA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('5c0240db', 'Anby.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('6ea0023c', 'Anby.HairA.Diffuse.2048')),
    ],
    'b54f2a3d': [(log, ('1.7 -> 2.0: Anby HairA LightMap 2048p Hash',)), (update_hash, ('057f3c55',))],
    '057f3c55': [
        (log,                           ('1.0: Anby HairA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('5c0240db', 'Anby.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('476ab69c','9ceea795'), 'Anby.HairA.LightMap.1024')),
    ],
    '9ceea795': [(log, ('1.7 -> 2.0: Anby HairA LightMap 1024p Hash',)), (update_hash, ('476ab69c',))],
    '476ab69c': [
        (log,                           ('1.0: Anby HairA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('5c0240db', 'Anby.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('057f3c55','b54f2a3d'), 'Anby.HairA.LightMap.2048')),
    ],

    # Body身体
    'b37c3b4e': [(log, ('1.5 -> 1.6: Anby BodyA Diffuse 2048p Hash',)), (update_hash, ('215ff74d',))],
    '215ff74d': [
        (log,                           ('1.6: Anby BodyA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('4816de84', 'Anby.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('8df45cb8', '8bd7966f'), 'Anby.BodyA.Diffuse.1024')),
    ],
    '8bd7966f': [(log, ('1.5 -> 1.6: Anby BodyA Diffuse 1024p Hash',)), (update_hash, ('8df45cb8',))],
    '8df45cb8': [
        (log,                           ('1.6: Anby BodyA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('4816de84', 'Anby.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('215ff74d', 'b37c3b4e'), 'Anby.BodyA.Diffuse.2048')),
    ],
    '7c24acc9': [(log, ('1.7 -> 2.0: Anby BodyA LightMap 2048p Hash',)), (update_hash, ('59b123c2',))],
    '59b123c2': [
        (log,                           ('1.0: Anby BodyA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('4816de84', 'Anby.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('9b57e140','9cddbf1e'), 'Anby.BodyA.LightMap.1024')),
    ],
    '9cddbf1e': [(log, ('1.7 -> 2.0: Anby BodyA LightMap 1024p Hash',)), (update_hash, ('9b57e140',))],
    '9b57e140': [
        (log,                           ('1.0: Anby BodyA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('4816de84', 'Anby.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('59b123c2','7c24acc9'), 'Anby.BodyA.LightMap.2048')),
    ],
    'ccca3b8e': [
        (log,                           ('1.0: Anby BodyA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        ('4816de84', 'Anby.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('1115f163', 'Anby.BodyA.MaterialMap.1024')),
    ],
    '1115f163': [
        (log,                           ('1.0: Anby BodyA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        ('4816de84', 'Anby.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('ccca3b8e', 'Anby.BodyA.MaterialMap.2048')),
    ],

    # MARK: Anton安东
    #IB
    '6b95c80d': [(log, ('1.0: Anton Hair IB Hash',)),   (add_ib_check_if_missing,)],
    '653fb27c': [(log, ('1.0: Anton Body IB Hash',)),   (add_ib_check_if_missing,)],
    'a21fcee4': [(log, ('1.0: Anton Jacket IB Hash',)), (add_ib_check_if_missing,)],
    'a0201907': [(log, ('1.0: Anton Face IB Hash',)),   (add_ib_check_if_missing,)],
    #VB

    #Texture纹理
    # Face脸部
    '842119d6': [
        (log,                           ('1.0: Anton FaceA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('a0201907', 'Anton.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('15cb1aee', 'Anton.FaceA.Diffuse.1024')),
    ],
    '15cb1aee': [
        (log,                           ('1.0: Anton FaceA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('a0201907', 'Anton.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('842119d6', 'Anton.FaceA.Diffuse.2048')),
    ],
    'ac7fb2e2': [
        (log,                           ('1.0: Anton FaceA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('a0201907', 'Anton.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('654134c1', 'Anton.FaceA.LightMap.1024')),
    ],
    '654134c1': [
        (log,                           ('1.0: Anton FaceA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('a0201907', 'Anton.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('ac7fb2e2', 'Anton.FaceA.LightMap.2048')),
    ],

    # Hair头发
    '571aa398': [
        (log,                           ('1.0: Anton HairA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('6b95c80d', 'Anton.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('d4c4c604', 'Anton.HairA.Diffuse.1024')),
    ],
    'd4c4c604': [
        (log,                           ('1.0: Anton HairA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('6b95c80d', 'Anton.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('571aa398', 'Anton.HairA.Diffuse.2048')),
    ],
    'ee06579e': [(log, ('1.7 -> 2.0: Anton HairA LightMap 2048p Hash',)), (update_hash, ('41601dfa',))],
    '41601dfa': [
        (log,                           ('1.0: Anton HairA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('6b95c80d', 'Anton.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('f6e280b0','21ee9a3f'), 'Anton.HairA.LightMap.1024')),
    ],
    '21ee9a3f': [(log, ('1.7 -> 2.0: Anton HairA LightMap 1024p Hash',)), (update_hash, ('f6e280b0',))],
    'f6e280b0': [
        (log,                           ('1.0: Anton HairA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('6b95c80d', 'Anton.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('41601dfa','ee06579e'), 'Anton.HairA.LightMap.2048')),
    ],
    '24caeb1f': [(log, ('1.7 -> 2.0: Anton HairA MaterialMap 2048p Hash',)), (update_hash, ('d47c5823',))],
    'd47c5823': [
        (log,                           ('1.0: Anton HairA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        ('6b95c80d', 'Anton.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('05bd454d','6fc654e1'), 'Anton.HairA.MaterialMap.1024')),
    ],
    '6fc654e1': [(log, ('1.7 -> 2.0: Anton HairA MaterialMap 1024p Hash',)), (update_hash, ('05bd454d',))],
    '05bd454d': [
        (log,                           ('1.0: Anton HairA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        ('6b95c80d', 'Anton.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('d47c5823','24caeb1f'), 'Anton.HairA.MaterialMap.2048')),
    ],

    # Body身体
    '00abcf22': [
        (log,                           ('1.0: Anton BodyA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('653fb27c', 'Anton.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('581a0958', 'Anton.BodyA.Diffuse.1024')),
    ],
    '581a0958': [
        (log,                           ('1.0: Anton BodyA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('653fb27c', 'Anton.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('00abcf22', 'Anton.BodyA.Diffuse.2048')),
    ],
    '17cf1b74': [(log, ('1.7 -> 2.0: Anton BodyA LightMap 2048p Hash',)), (update_hash, ('ed6f4199',))],
    'ed6f4199': [
        (log,                           ('1.0: Anton BodyA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('653fb27c', 'Anton.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('a937bcee','8e5ba7d0'), 'Anton.BodyA.LightMap.1024')),
    ],
    '8e5ba7d0': [(log, ('1.7 -> 2.0: Anton HairA LightMap 1024p Hash',)), (update_hash, ('a937bcee',))],
    'a937bcee': [
        (log,                           ('1.0: Anton BodyA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('653fb27c', 'Anton.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('ed6f4199','17cf1b74'), 'Anton.BodyA.LightMap.2048')),
    ],
    '0238b0ff': [(log, ('1.7 -> 2.0: Anton BodyA MaterialMap 2048p Hash',)), (update_hash, ('986c9716',))],
    '986c9716': [
        (log,                           ('1.0: Anton BodyA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        ('653fb27c', 'Anton.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('bb25e0f0','b7ce5f0b'), 'Anton.BodyA.MaterialMap.1024')),
    ],
    'b7ce5f0b': [(log, ('1.7 -> 2.0: Anton BodyA MaterialMap 1024p Hash',)), (update_hash, ('bb25e0f0',))],
    'bb25e0f0': [
        (log,                           ('1.0: Anton BodyA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        ('653fb27c', 'Anton.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('986c9716','0238b0ff'), 'Anton.BodyA.MaterialMap.2048')),
    ],

    # Jacket夹克
    'd4b15508': [
        (log,                           ('1.0: Anton JacketA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('a21fcee4', 'Anton.Jacket.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('f7831517', 'Anton.JacketA.Diffuse.1024')),
    ],
    'f7831517': [
        (log,                           ('1.0: Anton JacketA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('a21fcee4', 'Anton.Jacket.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('d4b15508', 'Anton.JacketA.Diffuse.2048')),
    ],
    '886a664a': [(log, ('1.7 -> 2.0: Anton JacketA LightMap 2048p Hash',)), (update_hash, ('ef7880e3',))],
    'ef7880e3': [
        (log,                           ('1.0: Anton JacketA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('a21fcee4', 'Anton.Jacket.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('edb33cec','c42628a5'), 'Anton.JacketA.LightMap.1024')),
    ],
    'c42628a5': [(log, ('1.7 -> 2.0: Anton JacketA LightMap 1024p Hash',)), (update_hash, ('edb33cec',))],
    'edb33cec': [
        (log,                           ('1.0: Anton JacketA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('a21fcee4', 'Anton.Jacket.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('ef7880e3','886a664a'), 'Anton.JacketA.LightMap.2048')),
    ],
    'd36a2f7a': [
        (log,                           ('1.0: Anton JacketA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        ('a21fcee4', 'Anton.Jacket.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('75bccc40', 'Anton.JacketA.MaterialMap.1024')),
    ],
    '75bccc40': [
        (log,                           ('1.0: Anton JacketA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        ('a21fcee4', 'Anton.Jacket.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('d36a2f7a', 'Anton.JacketA.MaterialMap.2048')),
    ],

    # MARK: Arie爱芮
    #IB
    '8a7ae9c2': [(log, ('2.6: Arie Hair IB Hash',)), (add_ib_check_if_missing,)],
    '8c5b553a': [(log, ('2.6: Arie Body IB Hash',)), (add_ib_check_if_missing,)],
    'e6ff7471': [(log, ('2.6: Arie Leg IB Hash',)), (add_ib_check_if_missing,)],
    '27966f80': [(log, ('2.6: Arie Face IB Hash',)), (add_ib_check_if_missing,)],
    #VB

    #Texture纹理
    # Face脸部
    '1b2ae01f': [
        (log,                           ('2.6: Arie FaceA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('6146195d', 'Arie.FaceA.Diffuse.1024')),
    ],
    '6146195d': [
        (log,                           ('2.6: Arie FaceA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('1b2ae01f', 'Arie.FaceA.Diffuse.2048')),
    ],

    # Hair头发
    'a572a368': [
        (log,                           ('2.6: Arie HairA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('dc18e71c', 'Arie.HairA.Diffuse.1024')),
    ],
    'dc18e71c': [
        (log,                           ('2.6: Arie HairA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('a572a368', 'Arie.HairA.Diffuse.2048')),
    ],
    '34c4faaa': [
        (log,                           ('2.6: Arie HairA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('34583b2b', 'Arie.HairA.LightMap.1024')),
    ],
    '34583b2b': [
        (log,                           ('2.6: Arie HairA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('34c4faaa', 'Arie.HairA.LightMap.2048')),
    ],
    '4309b48e': [
        (log,                           ('2.6: Arie HairA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('e32c606c', 'Arie.HairA.MaterialMap.1024')),
    ],
    'e32c606c': [
        (log,                           ('2.6: Arie HairA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('4309b48e', 'Arie.HairA.MaterialMap.2048')),
    ],

    # Body身体
    'a33c5da6': [
        (log,                           ('2.6: Arie BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('fda652ce', 'Arie.BodyA.Diffuse.1024')),
    ],
    'fda652ce': [
        (log,                           ('2.6: Arie BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('a33c5da6', 'Arie.BodyA.Diffuse.2048')),
    ],
    'ab389fa7': [
        (log,                           ('2.6: Arie BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('f575fc9d', 'Arie.BodyA.LightMap.1024')),
    ],
    'f575fc9d': [
        (log,                           ('2.6: Arie BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('ab389fa7', 'Arie.BodyA.LightMap.2048')),
    ],
    '40eff501': [
        (log,                           ('2.6: Arie BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('aaec2e94', 'Arie.BodyA.MaterialMap.1024')),
    ],
    'aaec2e94': [
        (log,                           ('2.6: Arie BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('40eff501', 'Arie.BodyA.MaterialMap.2048')),
    ],

    # MARK: ArieSkin爱芮皮肤
    #IB
    'c6bb960b': [(log, ('2.6: ArieSkin Body IB Hash',)), (add_ib_check_if_missing,)],
    '923c64c0': [(log, ('2.6: ArieSkin Leg IB Hash',)), (add_ib_check_if_missing,)],
    #VB
    #Texture纹理
    # Leg
    'a34313c8': [
        (log,                           ('2.6: ArieSkin LegA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('d754c95b', 'ArieSkin.LegA.Diffuse.1024')),
    ],
    'd754c95b': [
        (log,                           ('2.6: ArieSkin LegA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('a34313c8', 'ArieSkin.LegA.Diffuse.2048')),
    ],
    'd378c273': [
        (log,                           ('2.6: ArieSkin LegA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('83d872c2', 'ArieSkin.LegA.LightMap.1024')),
    ],
    '83d872c2': [
        (log,                           ('2.6: ArieSkin LegA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('d378c273', 'ArieSkin.LegA.LightMap.2048')),
    ],
    'd3da0d5a': [
        (log,                           ('2.6: ArieSkin LegA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('e86b5691', 'ArieSkin.LegA.MaterialMap.1024')),
    ],
    'e86b5691': [
        (log,                           ('2.6: ArieSkin LegA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('d3da0d5a', 'ArieSkin.LegA.MaterialMap.2048')),
    ],

    # Body身体
    'a55f187e': [(log, ('2.6 -> 2.7: ArieSkin BodyA Diffuse 2048p Hash',)), (update_hash, ('677f73d9',))],
    '677f73d9': [
        (log,                           ('2.6: ArieSkin BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   (('3c6bd181','303c63bc'), 'ArieSkin.BodyA.Diffuse.1024')),
    ],
    '3c6bd181': [(log, ('2.6 -> 2.7: ArieSkin BodyA Diffuse 1024p Hash',)), (update_hash, ('303c63bc',))],
    '303c63bc': [
        (log,                           ('2.6: ArieSkin BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   (('a55f187e','677f73d9'), 'ArieSkin.BodyA.Diffuse.2048')),
    ],
    'acee133c': [
        (log,                           ('2.6: ArieSkin BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('a97204aa', 'ArieSkin.BodyA.LightMap.1024')),
    ],
    'a97204aa': [
        (log,                           ('2.6: ArieSkin BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('acee133c', 'ArieSkin.BodyA.LightMap.2048')),
    ],
    '6ac35f02': [
        (log,                           ('2.6: ArieSkin BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('2418c407', 'ArieSkin.BodyA.MaterialMap.1024')),
    ],
    '2418c407': [
        (log,                           ('2.6: ArieSkin BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('6ac35f02', 'ArieSkin.BodyA.MaterialMap.2048')),
    ],

    # MARK: ArieAgent爱芮智能体
    #IB
    '1173ff78': [(log, ('2.6: ArieAgent Hair IB Hash',)), (add_ib_check_if_missing,)],
    '046400d3': [(log, ('2.6: ArieAgent Body IB Hash',)), (add_ib_check_if_missing,)],
    'ffa703e8': [(log, ('2.6: ArieAgent Face IB Hash',)), (add_ib_check_if_missing,)],
    #VB

    #Texture纹理
    # Face脸部
    '741d7c8f': [
        (log,                           ('2.6: ArieAgent FaceA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('6611eaa1', 'ArieAgent.FaceA.Diffuse.1024')),
    ],
    '6611eaa1': [
        (log,                           ('2.6: ArieAgent FaceA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('741d7c8f', 'ArieAgent.FaceA.Diffuse.2048')),
    ],

    # Hair头发
    'be70c507': [
        (log,                           ('2.6: ArieAgent HairA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('f0aec120', 'ArieAgent.HairA.Diffuse.1024')),
    ],
    'f0aec120': [
        (log,                           ('2.6: ArieAgent HairA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('be70c507', 'ArieAgent.HairA.Diffuse.2048')),
    ],
    '41124010': [
        (log,                           ('2.6: ArieAgent HairA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('9e2e56b3', 'ArieAgent.HairA.LightMap.1024')),
    ],
    '9e2e56b3': [
        (log,                           ('2.6: ArieAgent HairA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('41124010', 'ArieAgent.HairA.LightMap.2048')),
    ],
    '01087a99': [
        (log,                           ('2.6: ArieAgent HairA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('002360e1', 'ArieAgent.HairA.MaterialMap.1024')),
    ],
    '002360e1': [
        (log,                           ('2.6: ArieAgent HairA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('01087a99', 'ArieAgent.HairA.MaterialMap.2048')),
    ],

    # Body身体
    '859bb461': [
        (log,                           ('2.6: ArieAgent BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('702063c7', 'ArieAgent.BodyA.Diffuse.1024')),
    ],
    '702063c7': [
        (log,                           ('2.6: ArieAgent BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('859bb461', 'ArieAgent.BodyA.Diffuse.2048')),
    ],
    'ba534b39': [
        (log,                           ('2.6: ArieAgent BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('a588ea59', 'ArieAgent.BodyA.LightMap.1024')),
    ],
    'a588ea59': [
        (log,                           ('2.6: ArieAgent BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('ba534b39', 'ArieAgent.BodyA.LightMap.2048')),
    ],
    '14aa84e5': [
        (log,                           ('2.6: ArieAgent BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('0a8badcd', 'ArieAgent.BodyA.MaterialMap.1024')),
    ],
    '0a8badcd': [
        (log,                           ('2.6: ArieAgent BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('14aa84e5', 'ArieAgent.BodyA.MaterialMap.2048')),
    ],

    # MARK: ArieAgentSkin爱芮智能体皮肤
    #IB
    #VB

    #Texture纹理
    # Face脸部
    '6b11a215': [
        (log,                           ('2.6: ArieAgentSkin FaceA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('28466273', 'ArieAgentSkin.FaceA.Diffuse.1024')),
    ],
    '28466273': [
        (log,                           ('2.6: ArieAgentSkin FaceA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('6b11a215', 'ArieAgentSkin.FaceA.Diffuse.2048')),
    ],

    # Hair头发
    'fb2c3964': [
        (log,                           ('2.6: ArieAgentSkin HairA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('fc3231cd', 'ArieAgentSkin.HairA.Diffuse.1024')),
    ],
    'fc3231cd': [
        (log,                           ('2.6: ArieAgentSkin HairA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('fb2c3964', 'ArieAgentSkin.HairA.Diffuse.2048')),
    ],
    '21aac04f': [
        (log,                           ('2.6: ArieAgentSkin HairA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('380fbecb', 'ArieAgentSkin.HairA.LightMap.1024')),
    ],
    '380fbecb': [
        (log,                           ('2.6: ArieAgentSkin HairA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('21aac04f', 'ArieAgentSkin.HairA.LightMap.2048')),
    ],
    'e1ccfca4': [
        (log,                           ('2.6: ArieAgentSkin HairA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('8f3cfb68', 'ArieAgentSkin.HairA.MaterialMap.1024')),
    ],
    '8f3cfb68': [
        (log,                           ('2.6: ArieAgentSkin HairA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('e1ccfca4', 'ArieAgentSkin.HairA.MaterialMap.2048')),
    ],

    # Body身体
    '282c7753': [
        (log,                           ('2.6: ArieAgentSkin BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('1bf43198', 'ArieAgentSkin.BodyA.Diffuse.1024')),
    ],
    '1bf43198': [
        (log,                           ('2.6: ArieAgentSkin BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('282c7753', 'ArieAgentSkin.BodyA.Diffuse.2048')),
    ],
    '263f8811': [
        (log,                           ('2.6: ArieAgentSkin BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('99f9094c', 'ArieAgentSkin.BodyA.LightMap.1024')),
    ],
    '99f9094c': [
        (log,                           ('2.6: ArieAgentSkin BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('263f8811', 'ArieAgentSkin.BodyA.LightMap.2048')),
    ],
    'f5b45cc2': [
        (log,                           ('2.6: ArieAgentSkin BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('ab411caa', 'ArieAgentSkin.BodyA.MaterialMap.1024')),
    ],
    'ab411caa': [
        (log,                           ('2.6: ArieAgentSkin BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('f5b45cc2', 'ArieAgentSkin.BodyA.MaterialMap.2048')),
    ],

    # MARK: AstraYao耀佳音
    #IB
    '53cdac6c': [(log, ('1.5: AstraYao Hair IB Hash',)), (add_ib_check_if_missing,)],
    '7a110804': [(log, ('1.5: AstraYao Body IB Hash',)), (add_ib_check_if_missing,)],
    '92f33156': [(log, ('1.5: AstraYao Legs IB Hash',)), (add_ib_check_if_missing,)],
    '51831437': [(log, ('1.5: AstraYao Face IB Hash',)), (add_ib_check_if_missing,)],
    #VB

    '3cd13d03': [(log, ('1.5 -> 1.6: AstraYao Body Blend Hash',)),    (update_hash, ('9d35c352',)),],
    'f8b92870': [(log, ('1.5 -> 1.6: AstraYao Hair Texcoord Hash',)), (update_hash, ('8ba0b335',)),],
    'da86a32e': [(log, ('1.5 -> 1.6: AstraYao Legs Texcoord Hash',)), (update_hash, ('1433ee78',)),],

    #Texture纹理
    # Face脸部
    '3a8d0dfc': [(log, ('1.5 -> 1.6: AstraYao Face Diffuse 2048p Hash',)), (update_hash, ('c41341b2',))],
    'c41341b2': [
        (log,                           ('1.6: AstraYao FaceA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('51831437', 'AstraYao.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('3283b8be', '77670042'), 'AstraYao.FaceA.Diffuse.1024')),
    ],
    '77670042': [(log, ('1.5 -> 1.6: AstraYao Face Diffuse 1024p Hash',)), (update_hash, ('3283b8be',))],
    '3283b8be': [
        (log,                           ('1.6: AstraYao FaceA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('51831437', 'AstraYao.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('c41341b2', '3a8d0dfc'), 'AstraYao.FaceA.Diffuse.2048')),
    ],

    # Hair头发 Legs
    'da673df0': [(log, ('1.5A -> 1.5B: AstraYao HairA, LegsA Diffuse 2048p Hash',)), (update_hash, ('2daa2443',))],
    '2daa2443': [(log, ('1.5 -> 1.6: AstraYao HairA, LegsA Diffuse 2048p Hash',)),   (update_hash, ('e634238a',))],
    'e634238a': [
        (log,                           ('1.6: AstraYao HairA, LegsA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   (('56c71ea2', '4b1c1b47', '7a507e4a'), 'AstraYao.HairA.Diffuse.1024')),
    ],
    '7a507e4a': [(log, ('1.5A -> 1.5B: AstraYao HairA, LegsA Diffuse 1024p Hash',)), (update_hash, ('4b1c1b47',))],
    '4b1c1b47': [(log, ('1.5 -> 1.6: AstraYao HairA, LegsA Diffuse 1024p Hash',)),   (update_hash, ('56c71ea2',))],
    '56c71ea2': [
        (log,                           ('1.6: AstraYao HairA, LegsA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   (('e634238a', '2daa2443', 'da673df0'), 'AstraYao.HairA.Diffuse.2048')),
    ],
    '34aad3b4': [(log, ('1.5A -> 1.5B: AstraYao HairA, LegsA LightMap 2048p Hash',)), (update_hash, ('b085765e',))],
    'b085765e': [(log, ('1.5 -> 1.6: AstraYao HairA, LegsA LightMap 2048p Hash',)),   (update_hash, ('34f0706c',))],
    '34f0706c': [
        (log,                           ('1.6: AstraYao HairA, LegsA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   (('fd3ca2a6', 'c47a524a', 'e4a4f975'), 'AstraYao.HairA.LightMap.1024')),
    ],
    'e4a4f975': [(log, ('1.5A -> 1.5B: AstraYao HairA, LegsA LightMap 1024p Hash',)), (update_hash, ('c47a524a',))],
    'c47a524a': [(log, ('1.5 -> 1.6: AstraYao HairA, LegsA LightMap 1024p Hash',)),   (update_hash, ('fd3ca2a6',))],
    'fd3ca2a6': [
        (log,                           ('1.6: AstraYao HairA, LegsA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   (('34f0706c', 'b085765e', '34aad3b4'), 'AstraYao.HairA.LightMap.2048')),
    ],
    'b53b2e12': [(log, ('1.5 -> 1.6: AstraYao HairA, LegsA MaterialMap 2048p Hash',)), (update_hash, ('883a578f',))],
    '883a578f': [
        (log,                           ('1.6: AstraYao HairA, LegsA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   (('759c15e0', '0be99d44'), 'AstraYao.HairA.MaterialMap.1024')),
    ],
    '0be99d44': [(log, ('1.5 -> 1.6: AstraYao HairA, LegsA MaterialMap 1024p Hash',)), (update_hash, ('759c15e0',))],
    '759c15e0': [
        (log,                           ('1.6: AstraYao HairA, LegsA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   (('883a578f', 'b53b2e12'), 'AstraYao.HairA.MaterialMap.2048')),
    ],

    # Body身体
    'd7f1c157': [
        (log,                           ('1.5: AstraYao BodyA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('7a110804', 'AstraYao.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('e523eb0f', 'AstraYao.BodyA.Diffuse.1024')),
    ],
    'e523eb0f': [
        (log,                           ('1.5: AstraYao BodyA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('7a110804', 'AstraYao.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('d7f1c157', 'AstraYao.BodyA.Diffuse.2048')),
    ],
    'dba7d767': [
        (log,                           ('1.5: AstraYao BodyA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('7a110804', 'AstraYao.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('3f9f0d8a', 'AstraYao.BodyA.LightMap.1024')),
    ],
    '3f9f0d8a': [
        (log,                           ('1.5: AstraYao BodyA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('7a110804', 'AstraYao.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('dba7d767', 'AstraYao.BodyA.LightMap.2048')),
    ],
    '21d5f5e3': [
        (log,                           ('1.5: AstraYao BodyA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        ('7a110804', 'AstraYao.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('c4248e2d', 'AstraYao.BodyA.MaterialMap.1024')),
    ],
    'c4248e2d': [
        (log,                           ('1.5: AstraYao BodyA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        ('7a110804', 'AstraYao.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('21d5f5e3', 'AstraYao.BodyA.MaterialMap.2048')),
    ],

    # MARK: AstraSkin耀佳音皮肤
    #IB
    '02d8a2cb': [(log, ('1.5: AstraSkin Body IB Hash',)), (add_ib_check_if_missing,)],
    #VB
    #Texture纹理
    # Body身体
    '7301ca3a': [
        (log,                           ('1.5: AstraSkin BodyA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('02d8a2cb', 'AstraSkin.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('8212713f', 'AstraSkin.BodyA.Diffuse.1024')),
    ],
    '8212713f': [
        (log,                           ('1.5: AstraSkin BodyA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('02d8a2cb', 'AstraSkin.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('7301ca3a', 'AstraSkin.BodyA.Diffuse.2048')),
    ],
    '7ce9f1db': [(log, ('1.6 -> 2.0: AstraSkin BodyA LightMap 2048p Hash',)), (update_hash, ('515f9beb',))],
    '515f9beb': [
        (log,                           ('1.5: AstraSkin BodyA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('02d8a2cb', 'AstraSkin.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('83ede428', 'cf8ecb3b'), 'AstraSkin.BodyA.LightMap.1024')),
    ],
    '83ede428': [(log, ('1.6 -> 2.0: AstraSkin BodyA LightMap 1024p Hash',)), (update_hash, ('cf8ecb3b',))],
    'cf8ecb3b': [
        (log,                           ('1.5: AstraSkin BodyA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('02d8a2cb', 'AstraSkin.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('7ce9f1db', '515f9beb'), 'AstraSkin.BodyA.LightMap.2048')),
    ],
    '43a4d256': [(log, ('1.6 -> 2.0: AstraSkin BodyA MaterialMap 2048p Hash',)), (update_hash, ('fa2f509f',))],
    '56abc3a3': [(log, ('1.5 -> 1.6: AstraSkin BodyA MaterialMap 2048p Hash',)), (update_hash, ('43a4d256',))],
    'fa2f509f': [
        (log,                           ('1.6: AstraSkin BodyA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        ('02d8a2cb', 'AstraSkin.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('6da1b76a', '6989dc5a', '03df0be9'), 'AstraSkin.BodyA.MaterialMap.1024')),
    ],
    '6da1b76a': [(log, ('1.6 -> 2.0: AstraSkin BodyA MaterialMap 1024p Hash',)), (update_hash, ('03df0be9',))],
    '6989dc5a': [(log, ('1.5 -> 1.6: AstraSkin BodyA MaterialMap 1024p Hash',)), (update_hash, ('6da1b76a',))],
    '03df0be9': [
        (log,                           ('1.6: AstraSkin BodyA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        ('02d8a2cb', 'AstraSkin.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('43a4d256', '56abc3a3', 'fa2f509f'), 'AstraSkin.BodyA.MaterialMap.2048')),
    ],

    # MARK: Banyue般岳
    #IB
    '698046e6': [(log, ('2.4: Banyue Body IB Hash',)),      (add_ib_check_if_missing,)],
    '635709b5': [(log, ('2.4: Banyue BothArms IB Hash',)),  (add_ib_check_if_missing,)],
    '5f855404': [(log, ('2.4: Banyue Leg IB Hash',)),       (add_ib_check_if_missing,)],
    'f3b6e869': [(log, ('2.4: Banyue Face IB Hash',)),      (add_ib_check_if_missing,)],
    #VB

    #Texture纹理
    # Face脸部
    '0a1f42fb': [
        (log,                           ('2.4: Banyue FaceA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('fc9c6235', 'Banyue.FaceA.Diffuse.1024')),
    ],
    'fc9c6235': [
        (log,                           ('2.4: Banyue FaceA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('0a1f42fb', 'Banyue.FaceA.Diffuse.2048')),
    ],
    '81cd7414': [
        (log,                           ('2.4: Banyue FaceA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('6c0d6d52', 'Banyue.FaceA.LightMap.1024')),
    ],
    '6c0d6d52': [
        (log,                           ('2.4: Banyue FaceA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('81cd7414', 'Banyue.FaceA.LightMap.2048')),
    ],
    'ef8ba12a': [
        (log,                           ('2.4: Banyue FaceA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('ca2b8ca8', 'Banyue.FaceA.MaterialMap.1024')),
    ],
    'ca2b8ca8': [
        (log,                           ('2.4: Banyue FaceA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('ef8ba12a', 'Banyue.FaceA.MaterialMap.2048')),
    ],

    # Body身体
    '19c3125c': [
        (log,                           ('2.4: Banyue BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('b3b968a5', 'Banyue.BodyA.Diffuse.1024')),
    ],
    'b3b968a5': [
        (log,                           ('2.4: Banyue BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('19c3125c', 'Banyue.BodyA.Diffuse.2048')),
    ],
    'f44f6316': [
        (log,                           ('2.4: Banyue BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('cdecf7ef', 'Banyue.BodyA.LightMap.1024')),
    ],
    'cdecf7ef': [
        (log,                           ('2.4: Banyue BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('f44f6316', 'Banyue.BodyA.LightMap.2048')),
    ],
    '7099d2dc': [
        (log,                           ('2.4: Banyue BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('77d743f8', 'Banyue.BodyA.MaterialMap.1024')),
    ],
    '77d743f8': [
        (log,                           ('2.4: Banyue BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('7099d2dc', 'Banyue.BodyA.MaterialMap.2048')),
    ],

    # BothArms
    'd6a9d46e': [
        (log,                           ('2.4: Banyue BothArmsA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('b91ab7b9', 'Banyue.BothArmsA.Diffuse.1024')),
    ],
    'b91ab7b9': [
        (log,                           ('2.4: Banyue BothArmsA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('d6a9d46e', 'Banyue.BothArmsA.Diffuse.2048')),
    ],
    '46d2edd3': [
        (log,                           ('2.4: Banyue BothArmsA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('a2b682d6', 'Banyue.BothArmsA.LightMap.1024')),
    ],
    'a2b682d6': [
        (log,                           ('2.4: Banyue BothArmsA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('46d2edd3', 'Banyue.BothArmsA.LightMap.2048')),
    ],
    '721a29de': [
        (log,                           ('2.4: Banyue BothArmsA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('d6ac66fa', 'Banyue.BothArmsA.MaterialMap.1024')),
    ],
    'd6ac66fa': [
        (log,                           ('2.4: Banyue BothArmsA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('721a29de', 'Banyue.BothArmsA.MaterialMap.2048')),
    ],
 
    # Leg
    'a75cf25e': [
        (log,                           ('2.4: Banyue LegA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('950ca70a', 'Banyue.LegA.Diffuse.1024')),
    ],
    '950ca70a': [
        (log,                           ('2.4: Banyue LegA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('a75cf25e', 'Banyue.LegA.Diffuse.2048')),
    ],
    '1003c4df': [
        (log,                           ('2.4: Banyue LegA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('62c9fcaa', 'Banyue.LegA.LightMap.1024')),
    ],
    '62c9fcaa': [
        (log,                           ('2.4: Banyue LegA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('1003c4df', 'Banyue.LegA.LightMap.2048')),
    ],
    '1125ccff': [
        (log,                           ('2.4: Banyue LegA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('8b0fcc7b', 'Banyue.LegA.MaterialMap.1024')),
    ],
    '8b0fcc7b': [
        (log,                           ('2.4: Banyue LegA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('1125ccff', 'Banyue.LegA.MaterialMap.2048')),
    ],

    # MARK: Belle铃
    #IB
    #3.0版本铃的模型发生了较大变化，3.0版本之前的mod将无法通过简单的hash替换来适配3.0之后的版本，故取消更新
    '3acf9aea': [(log, ('3.0: Belle Hair IB Hash',)), (add_ib_check_if_missing,)],
    'c2b4ce3a': [(log, ('3.0: Belle Body IB Hash',)), (add_ib_check_if_missing,)],
    '9a9780a7': [(log, ('1.0: Belle Face IB Hash',)), (add_ib_check_if_missing,)],
    #VB
    
    #铃与皮肤之间一个含有1de8fc08一个含有ccc76aea互相冲突，故取消更新
    #'73a1352f': [(log, ('1.7 -> 2.0: Belle Face LightMap Texcoord Hash',)), (update_hash, ('1de8fc08',))],    
    #'ccc76aea': [(log, ('1.7 -> 2.0: Belle Face LightMap Texcoord Hash',)), (update_hash, ('1de8fc08',))],
    #Remap
    'caf95576': [
        (log,                         ('1.0 -> 1.1: Belle Body Texcoord Hash',)),
        (update_hash,                 ('801edbf4',)),
        (log,                         ('1.0 -> 1.1: Belle Body Blend Remap',)),
        (update_buffer_blend_indices, (
            'd2844c01',
            (3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 58, 59, 60, 61, 62, 63, 64, 65, 66, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 126, 127),
            (6, 7, 3, 5, 4, 18, 9, 10, 11, 12, 13, 14, 15, 16, 17, 21, 25, 24, 20, 22, 23, 38, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 47, 48, 53, 56, 45, 46, 49, 50, 51, 52, 54, 55, 60, 61, 66, 58, 59, 62, 63, 64, 65, 104, 95, 96, 97, 98, 99, 100, 101, 102, 103, 127, 126),
        ))
    ],

    #Texture纹理
    # Face脸部
    '75ec3614': [
        (log,                           ('1.0: Belle FaceA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('9a9780a7', 'Belle.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('77eef7e8', 'Belle.FaceA.Diffuse.1024')),
    ],
    '77eef7e8': [
        (log,                           ('1.0: Belle FaceA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('9a9780a7', 'Belle.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('75ec3614', 'Belle.FaceA.Diffuse.2048')),
    ],

    # Hair头发
    '1ce58567': [
        (log,                           ('1.0: Belle HairA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('bea4a483', 'Belle.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('08f04d95', 'Belle.HairA.Diffuse.1024')),
    ],
    '08f04d95': [
        (log,                           ('1.0: Belle HairA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('bea4a483', 'Belle.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('1ce58567', 'Belle.HairA.Diffuse.2048')),
    ],
    'f1ee2105': [(log, ('1.7 -> 2.0: Belle HairA LightMap 2048p Hash',)), (update_hash, ('7d562f53',))],
    '7d562f53': [
        (log,                           ('1.0: Belle HairA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('bea4a483', 'Belle.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('f44f330b','2e656f2f'), 'Belle.HairA.LightMap.1024')),
    ],
    '2e656f2f': [(log, ('1.7 -> 2.0: Belle HairA LightMap 1024p Hash',)), (update_hash, ('f44f330b',))],
    'f44f330b': [
        (log,                           ('1.0: Belle HairA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('bea4a483', 'Belle.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('7d562f53','f1ee2105'), 'Belle.HairA.LightMap.2048')),
    ],
    '24c47ca5': [(log, ('1.4 -> 1.5: Belle HairA MaterialMap 2048p Hash',)), (update_hash, ('34bdb036',))],
    '34bdb036': [
        (log,                           ('1.5: Belle HairA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        ('bea4a483', 'Belle.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('7542ef4b', '4b6ef993'), 'Belle.HairA.MaterialMap.1024')),
    ],
    '4b6ef993': [(log, ('1.4 -> 1.5: Belle HairA MaterialMap 1024p Hash',)), (update_hash, ('7542ef4b',))],
    '7542ef4b': [
        (log,                           ('1.5: Belle HairA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        ('bea4a483', 'Belle.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('34bdb036', '24c47ca5'), 'Belle.HairA.MaterialMap.2048')),
    ],

    # Body身体    
    'd2960560': [(log, ('1.4 -> 1.5: Belle BodyA Diffuse 2048p Hash',)), (update_hash, ('24639b77',))],
    '24639b77': [
        (log,                           ('1.5: Belle BodyA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('1817f3ca', 'Belle.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('b9c7f71b', '4454fb58'), 'Belle.BodyA.Diffuse.1024')),
    ],
    '4454fb58': [(log, ('1.4 -> 1.5: Belle BodyA Diffuse 1024p Hash',)), (update_hash, ('b9c7f71b',))],
    'b9c7f71b': [
        (log,                           ('1.5: Belle BodyA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('1817f3ca', 'Belle.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('24639b77', 'd2960560'), 'Belle.BodyA.Diffuse.2048')),
    ],
    'bf286c84': [(log, ('1.4 -> 1.5: Belle BodyA LightMap 2048p Hash',)), (update_hash, ('7947679c',))],
    '7947679c': [
        (log,                           ('1.5: Belle BodyA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('1817f3ca', 'Belle.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('a4d3687d', '2ed82c57'), 'Belle.BodyA.LightMap.1024')),
    ],
    '2ed82c57': [(log, ('1.4 -> 1.5: Belle BodyA LightMap 1024p Hash',)), (update_hash, ('a4d3687d',))],
    'a4d3687d': [
        (log,                           ('1.5: Belle BodyA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('1817f3ca', 'Belle.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('7947679c', 'bf286c84'), 'Belle.BodyA.LightMap.2048')),
    ],
    '33f28c6d': [
        (log,                           ('1.0: Belle BodyA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        ('1817f3ca', 'Belle.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('b1abe877', 'Belle.BodyA.MaterialMap.1024')),
    ],
    'b1abe877': [
        (log,                           ('1.0: Belle BodyA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        ('1817f3ca', 'Belle.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('33f28c6d', 'Belle.BodyA.MaterialMap.2048')),
    ],

    # MARK: BelleSchoolUniform铃校服
    #IB
    'feb1c4cd': [(log, ('3.0: BelleSchoolUniform Body IB Hash',)), (add_ib_check_if_missing,)],
    '62711f82': [(log, ('3.0: BelleSchoolUniform Earrings IB Hash',)), (add_ib_check_if_missing,)],
    '0a843a8f': [(log, ('3.0: BelleSchoolUniform Hat IB Hash',)), (add_ib_check_if_missing,)],
    'a318b3c6': [(log, ('3.0: BelleSchoolUniform Player IB Hash',)), (add_ib_check_if_missing,)],
    'b946c37f': [(log, ('3.0: BelleSchoolUniform Tie IB Hash',)), (add_ib_check_if_missing,)],
    #VB

    #'d3000b22': [(log, ('3.1: BelleSchoolUniform Face-脸部 texcoord_vb Hash',)), (update_hash, ('228f5a8b',))],
    #Texture纹理
    # Body身体

    'a292d07d': [(log, ('3.0 -> 3.1: BelleSchoolUniform BodyA Diffuse 2048p Hash',)), (update_hash, ('fd906f9b',))],
    'fd906f9b': [
        (log,                           ('3.1: BelleSchoolUniform BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   (('639ad374','d9dc65da'), 'BelleSchoolUniform.BodyA.Diffuse.1024')),
    ],
    '639ad374': [(log, ('3.0 -> 3.1: BelleSchoolUniform BodyA Diffuse 1024p Hash',)), (update_hash, ('d9dc65da',))],
    'd9dc65da': [
        (log,                           ('3.1: BelleSchoolUniform BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   (('a292d07d','fd906f9b'), 'BelleSchoolUniform.BodyA.Diffuse.2048')),
    ],
    '42310c0e': [
        (log,                           ('3.0: BelleSchoolUniform BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('e1f357ec', 'BelleSchoolUniform.BodyA.LightMap.1024')),
    ],
    'e1f357ec': [
        (log,                           ('3.0: BelleSchoolUniform BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('42310c0e', 'BelleSchoolUniform.BodyA.LightMap.2048')),
    ],
    '5724e531': [
        (log,                           ('3.0: BelleSchoolUniform BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('7c1fb5f6', 'BelleSchoolUniform.BodyA.MaterialMap.1024')),
    ],
    '7c1fb5f6': [
        (log,                           ('3.0: BelleSchoolUniform BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('5724e531', 'BelleSchoolUniform.BodyA.MaterialMap.2048')),
    ],
    
    # Hat帽子
    '8c0ea559': [
        (log,                           ('3.0: BelleSchoolUniform HatA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('269a82f9', 'BelleSchoolUniform.HatA.Diffuse.1024')),
    ],
    '269a82f9': [
        (log,                           ('3.0: BelleSchoolUniform HatA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('8c0ea559', 'BelleSchoolUniform.HatA.Diffuse.2048')),
    ],
    'dcb8ba2e': [
        (log,                           ('3.0: BelleSchoolUniform HatA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('a21dde78', 'BelleSchoolUniform.HatA.LightMap.1024')),
    ],
    'a21dde78': [
        (log,                           ('3.0: BelleSchoolUniform HatA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('dcb8ba2e', 'BelleSchoolUniform.HatA.LightMap.2048')),
    ],
    '57130f7c': [
        (log,                           ('3.0: BelleSchoolUniform HatA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('08453671', 'BelleSchoolUniform.HatA.MaterialMap.1024')),
    ],
    '08453671': [
        (log,                           ('3.0: BelleSchoolUniform HatA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('57130f7c', 'BelleSchoolUniform.HatA.MaterialMap.2048')),
    ],
        


    # MARK: BelleSkin铃·皮肤
    #IB
    'aa9ffb85': [(log, ('2.0: BelleSkin Hair IB Hash',)), (add_ib_check_if_missing,)],
    'd509bdd4': [(log, ('2.0: BelleSkin Body IB Hash',)), (add_ib_check_if_missing,)],
    'bcc9e4e1': [(log, ('2.0: BelleSkin Leg IB Hash',)), (add_ib_check_if_missing,)],  
    #VB

    '02c9dc4b': [(log, ('2.4 -> 2.5: BelleSkin Body Draw Hash',)),     (update_hash, ('19e5f486',)),],
    '0b3c5e7c': [(log, ('2.4 -> 2.5: BelleSkin Body Position Hash',)), (update_hash, ('8a4e97cd',)),],
    '01b0c8b': [(log, ('2.4 -> 2.5: BelleSkin Body Blend Hash',)),    (update_hash, ('f3dedb50',)),],
    'f3dedb50': [(log, ('2.8 -> 3.0: BelleSkin Body Blend Hash',)),    (update_hash, ('4d74d5e9',)),],
    '862dc27a': [(log, ('2.4 -> 2.5: BelleSkin Body Texcoord Hash',)), (update_hash, ('d761e076',)),],
    '860e1558': [(log, ('2.4 -> 2.5: BelleSkin Body IB Hash',)),       (update_hash, ('d509bdd4',)),],

    '39ac6700': [(log, ('2.8 -> 3.0: BelleSkin Hair Blend Hash',)),    (update_hash, ('8f7ae834',)),],
    'db7add33': [(log, ('2.8 -> 3.0: BelleSkin Facewear Blend Hash',)),    (update_hash, ('f18dd23f',)),],

    'f53b2eba': [(log, ('2.8 -> 3.0: BelleSkin Leg Blend Hash',)),    (update_hash, ('922a7db6',)),],

    #Texture纹理
    # Body身体
    'cac9fd5d': [(log, ('2.0 -> 2.1: BelleSkin BodyA Diffuse 2048p Hash',)), (update_hash, ('da2bfe2f',))],
    'da2bfe2f': [
        (log,                           ('2.0: BelleSkin BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   (('59218fac','fdf0b49e'), 'BelleSkin.BodyA.Diffuse.1024')),
    ],
    '59218fac': [(log, ('2.0 -> 2.1: BelleSkin BodyA Diffuse 1024p Hash',)), (update_hash, ('fdf0b49e',))],
    'fdf0b49e': [
        (log,                           ('2.0: BelleSkin BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   (('da2bfe2f','cac9fd5d'), 'BelleSkin.BodyA.Diffuse.2048')),
    ],
    '74f2fae3': [
        (log,                           ('2.0: BelleSkin BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('93d94f22', 'BelleSkin.BodyA.LightMap.1024')),
    ],
    '93d94f22': [
        (log,                           ('2.0: BelleSkin BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('74f2fae3', 'BelleSkin.BodyA.LightMap.2048')),
    ],
    '657402d0': [
        (log,                           ('2.0: BelleSkin BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('b95c08fb', 'BelleSkin.BodyA.MaterialMap.1024')),
    ],
    'b95c08fb': [
        (log,                           ('2.0: BelleSkin BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('657402d0', 'BelleSkin.BodyA.MaterialMap.2048')),
    ],

    # MARK: BellesWimwear铃·泳装
    #IB
    #3.0版本铃·泳装的模型发生了较大变化，3.0版本之前的mod将无法通过简单的hash替换来适配3.0之后的版本，故取消更新
    'a7683988': [(log, ('3.0: BellesWimwear Hair IB Hash',)), (add_ib_check_if_missing,)],
    '619c5c94': [(log, ('3.0: BellesWimwear Body IB Hash',)), (add_ib_check_if_missing,)],
    '69148073': [(log, ('2.0: BellesWimwear Tshirt IB Hash',)), (add_ib_check_if_missing,)],

    '6af00597': [(log, ('2.1 -> 2.2: BellesWimwear Body Blend',)), (update_hash, ('4f3ddd5c',))],
    '65481194': [(log, ('2.1 -> 2.2: BellesWimwear Tshirt Blend',)), (update_hash, ('0139f7e8',))],
    '0139f7e8': [(log, ('2.8 -> 3.0: BellesWimwear Tshirt Blend',)), (update_hash, ('0a00d846',))],
    '881514bf': [(log, ('2.8 -> 3.0: BellesWimwear Tshirt Texcoord',)), (update_hash, ('325b4a1c',))],
    #Texture纹理
    # Hair头发 Body身体
    '20954729': [
        (log,                           ('2.0: BellesWimwear BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('afe23695', 'BellesWimwear.BodyA.Diffuse.1024')),
    ],
    'afe23695': [
        (log,                           ('2.0: BellesWimwear BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('20954729', 'BellesWimwear.BodyA.Diffuse.2048')),
    ],
    'e0a86379': [(log, ('2.8 -> 3.0: BellesWimwear BodyA LightMap 2048p Hash',)), (update_hash, ('60250d24',))],
    '60250d24': [
        (log,                           ('2.0: BellesWimwear BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   (('a189eccd','5978a2ca'), 'BellesWimwear.BodyA.LightMap.1024')),
    ],
    'a189eccd': [(log, ('2.8 -> 3.0: BellesWimwear BodyA LightMap 1024p Hash',)), (update_hash, ('5978a2ca',))],
    '5978a2ca': [
        (log,                           ('2.0: BellesWimwear BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   (('e0a86379','60250d24'), 'BellesWimwear.BodyA.LightMap.2048')),
    ],
    '0298fba2': [
        (log,                           ('2.0: BellesWimwear BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('fbaaeb92', 'BellesWimwear.BodyA.MaterialMap.1024')),
    ],
    'fbaaeb92': [
        (log,                           ('2.0: BellesWimwear BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('0298fba2', 'BellesWimwear.BodyA.MaterialMap.2048')),
    ],

    # MARK: Ben本
    #IB
    '9c4f1a9a': [(log, ('1.0: Ben Hair IB Hash',)), (add_ib_check_if_missing,)],
    '94288cca': [(log, ('1.0: Ben Body IB Hash',)), (add_ib_check_if_missing,)],
    #VB

    'a2f79d33': [(log, ('1.7 -> 2.0: Ben Body Blend',)), (update_hash, ('21dd67a7',))],

    # Hair头发
    '00002f2c': [
        (log,                           ('1.0: Ben HairA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('9c4f1a9a', 'Ben.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('8d83daba', 'Ben.HairA.Diffuse.1024')),
    ],
    '8d83daba': [
        (log,                           ('1.0: Ben HairA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('9c4f1a9a', 'Ben.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('00002f2c', 'Ben.HairA.Diffuse.2048')),
    ],
    'cc195dc5': [(log, ('1.7 -> 2.0: Ben HairA LightMap 2048p Hash',)), (update_hash, ('2fa5ffa7',))],
    '2fa5ffa7': [
        (log,                           ('1.0: Ben HairA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('9c4f1a9a', 'Ben.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('9372e123','1439d2b9'), 'Ben.HairA.LightMap.1024')),
    ],
    '1439d2b9': [(log, ('1.7 -> 2.0: Ben HairA LightMap 1024p Hash',)), (update_hash, ('9372e123',))],
    '9372e123': [
        (log,                           ('1.0: Ben HairA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('9c4f1a9a', 'Ben.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('2fa5ffa7','cc195dc5'), 'Ben.HairA.LightMap.2048')),
    ],
    '0bbceea0': [(log, ('1.7 -> 2.0: Ben HairA MaterialMap 2048p Hash',)), (update_hash, ('12e5120e',))],
    '12e5120e': [
        (log,                           ('1.0: Ben HairA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        ('9c4f1a9a', 'Ben.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('dd8c0b3a','d665246d'), 'Ben.HairA.MaterialMap.1024')),
    ],
    'd665246d': [(log, ('1.7 -> 2.0: Ben HairA MaterialMap 1024p Hash',)), (update_hash, ('dd8c0b3a',))],
    'dd8c0b3a': [
        (log,                           ('1.0: Ben HairA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        ('9c4f1a9a', 'Ben.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('0bbceea0','12e5120e'), 'Ben.HairA.MaterialMap.2048')),
    ],

    # Body身体
    '0313ed95': [
        (log,                           ('1.0: Ben BodyA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('94288cca', 'Ben.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('d8dc4645', 'Ben.BodyA.Diffuse.1024')),
    ],
    'd8dc4645': [
        (log,                           ('1.0: Ben BodyA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('94288cca', 'Ben.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('0313ed95', 'Ben.BodyA.Diffuse.2048')),
    ],
    'cb84ed5e': [(log, ('1.7 -> 2.0: Ben BodyA LightMap 2048p Hash',)), (update_hash, ('d27a8f6b',))],
    'd27a8f6b': [
        (log,                           ('1.0: Ben BodyA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('94288cca', 'Ben.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('9a724295','6a80c2d8'), 'Ben.BodyA.LightMap.1024')),
    ],
    '6a80c2d8': [(log, ('1.7 -> 2.0: Ben BodyA LightMap 1024p Hash',)), (update_hash, ('9a724295',))],
    '9a724295': [
        (log,                           ('1.0: Ben BodyA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('94288cca', 'Ben.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('d27a8f6b','cb84ed5e'), 'Ben.BodyA.LightMap.2048')),
    ],
    '3f4f6bc0': [(log, ('1.7 -> 2.0: Ben BodyA MaterialMap 2048p Hash',)), (update_hash, ('2edd6f62',))],
    '2edd6f62': [
        (log,                           ('1.0: Ben BodyA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        ('94288cca', 'Ben.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('3678fad4','decc28c5'), 'Ben.BodyA.MaterialMap.1024')),
    ],
    'decc28c5': [(log, ('1.7 -> 2.0: Ben BodyA MaterialMap 1024p Hash',)), (update_hash, ('3678fad4',))],
    '3678fad4': [
        (log,                           ('1.0: Ben BodyA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        ('94288cca', 'Ben.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('2edd6f62','3f4f6bc0'), 'Ben.BodyA.MaterialMap.2048')),
    ],

    # MARK: Billy比利
    #IB
    '21e98aeb': [(log, ('1.0: Billy Hair IB Hash',)), (add_ib_check_if_missing,)],
    '3371580a': [(log, ('1.0: Billy Body IB Hash',)), (add_ib_check_if_missing,)],
    'dc7978f3': [(log, ('1.0: Billy Face IB Hash',)), (add_ib_check_if_missing,)],
    #VB

    #Texture纹理
    # Face脸部
    '6f8a9cdb': [
        (log,                           ('1.0: Billy FaceA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('dc7978f3', 'Billy.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('a1d68c9e', 'Billy.FaceA.Diffuse.1024')),
    ],
    'a1d68c9e': [
        (log,                           ('1.0: Billy FaceA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('dc7978f3', 'Billy.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('6f8a9cdb', 'Billy.FaceA.Diffuse.2048')),
    ],
    '9f02ef2b': [(log, ('1.7 -> 2.0: Billy FaceA LightMap 2048p Hash',)), (update_hash, ('cf4769ce',))],
    'cf4769ce': [
        (log,                           ('1.0: Billy FaceA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('dc7978f3', 'Billy.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('f5a507da','877e1a0d'), 'Billy.FaceA.LightMap.1024')),
    ],
    '877e1a0d': [(log, ('1.7 -> 2.0: Billy FaceA LightMap 1024p Hash',)), (update_hash, ('f5a507da',))],
    'f5a507da': [
        (log,                           ('1.0: Billy FaceA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('dc7978f3', 'Billy.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('cf4769ce','9f02ef2b'), 'Billy.FaceA.LightMap.2048')),
    ],
    'd166c3e5': [(log, ('1.7 -> 2.0: Billy FaceA MaterialMap 2048p Hash',)), (update_hash, ('3a7d88a1',))],
    '3a7d88a1': [
        (log,                           ('1.0: Billy FaceA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        ('dc7978f3', 'Billy.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('e534abc0','dc2f2dd2'), 'Billy.FaceA.MaterialMap.1024')),
    ],
    'dc2f2dd2': [(log, ('1.7 -> 2.0: Billy FaceA MaterialMap 1024p Hash',)), (update_hash, ('e534abc0',))],
    'e534abc0': [
        (log,                           ('1.0: Billy FaceA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        ('dc7978f3', 'Billy.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('3a7d88a1','d166c3e5'), 'Billy.FaceA.MaterialMap.2048')),
    ],

    # Hair头发
    '0475db07': [(log, ('1.7 -> 2.0: Billy HairA Diffuse 2048p Hash',)), (update_hash, ('ff939fb7',))],
    'ff939fb7': [
        (log,                           ('1.0: Billy HairA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('21e98aeb', 'Billy.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('c0360c81','6a6a1c79'), 'Billy.HairA.Diffuse.1024')),
    ],
    'c0360c81': [(log, ('1.7 -> 2.0: Billy HairA Diffuse 1024p Hash',)), (update_hash, ('6a6a1c79',))],
    '6a6a1c79': [
        (log,                           ('1.0: Billy HairA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('21e98aeb', 'Billy.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('ff939fb7','0475db07'), 'Billy.HairA.Diffuse.2048')),
    ],
    '4817b1bc': [(log, ('1.7 -> 2.0: Billy HairA LightMap 2048p Hash',)), (update_hash, ('b6e1da4b',))],
    'b6e1da4b': [
        (log,                           ('1.0: Billy HairA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('21e98aeb', 'Billy.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('2edbc842','f6749665','d269a0a1'), 'Billy.HairA.LightMap.1024')),
    ],
    'f6749665': [(log, ('1.7 -> 2.0: Billy HairA LightMap 1024p Hash',)), (update_hash, ('2edbc842',))],
    'd269a0a1': [(log, ('1.0 -> 1.7: Billy HairA LightMap 1024p Hash',)), (update_hash, ('f6749665',))],
    '2edbc842': [
        (log,                           ('1.0: Billy HairA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('21e98aeb', 'Billy.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('b6e1da4b','4817b1bc'), 'Billy.HairA.LightMap.2048')),
    ],

    # Body身体
    '399d9865': [
        (log,                           ('1.0: Billy BodyA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('3371580a', 'Billy.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('af07a583', 'Billy.BodyA.Diffuse.1024')),
    ],
    'af07a583': [
        (log,                           ('1.0: Billy BodyA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('3371580a', 'Billy.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('399d9865', 'Billy.BodyA.Diffuse.2048')),
    ],
    '789b054e': [(log, ('1.7 -> 2.0: Billy BodyA LightMap 2048p Hash',)), (update_hash, ('6305a7f4',))],
    '6305a7f4': [
        (log,                           ('1.0: Billy BodyA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('3371580a', 'Billy.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('adc2ec7c','0d5d374f'), 'Billy.BodyA.LightMap.1024')),
    ],
    '0d5d374f': [(log, ('1.7 -> 2.0: Billy BodyA LightMap 1024p Hash',)), (update_hash, ('adc2ec7c',))],
    'adc2ec7c': [
        (log,                           ('1.0: Billy BodyA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('3371580a', 'Billy.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('6305a7f4','789b054e'), 'Billy.BodyA.LightMap.2048')),
    ],
    '9cb20fa9': [
        (log,                           ('1.0: Billy BodyA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        ('3371580a', 'Billy.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('b3cabf65', 'Billy.BodyA.MaterialMap.1024')),
    ],
    'b3cabf65': [
        (log,                           ('1.0: Billy BodyA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        ('3371580a', 'Billy.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('9cb20fa9', 'Billy.BodyA.MaterialMap.2048')),
    ],

    # MARK: Burnice伯妮斯
    #IB
    'f779fb81': [(log, ('1.2: Burnice Hair IB Hash',)), (add_ib_check_if_missing,)],
    'af63e974': [(log, ('1.2: Burnice Body IB Hash',)), (add_ib_check_if_missing,)],
    'b3f6fcb3': [(log, ('1.2: Burnice Face IB Hash',)), (add_ib_check_if_missing,)],
    #VB

    #Texture纹理
    # Face脸部
    'c9c87bb1': [(log, ('1.3 -> 1.4: Burnice FaceA Diffuse 1024p Hash',)), (update_hash, ('68f0fb19',)),],
    '68f0fb19': [
        (log,                           ('1.4: Burnice FaceA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('b3f6fcb3', 'Burnice.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('c4b6bb10', 'e338bb82'), 'Burnice.FaceA.Diffuse.2048')),
    ],
    'e338bb82': [(log, ('1.3 -> 1.4: Burnice FaceA Diffuse 2048p Hash',)), (update_hash, ('c4b6bb10',)),],
    'c4b6bb10': [
        (log,                           ('1.4: Burnice FaceA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('b3f6fcb3', 'Burnice.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('68f0fb19', 'c9c87bb1'), 'Burnice.FaceA.Diffuse.1024')),
    ],

    # Hair头发
    '609b50a9': [
        (log,                           ('1.2: Burnice HairA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('f779fb81', 'Burnice.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('4568c6b3', 'Burnice.HairA.Diffuse.1024')),
    ],
    '4568c6b3': [
        (log,                           ('1.2: Burnice HairA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('f779fb81', 'Burnice.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('609b50a9', 'Burnice.HairA.Diffuse.2048')),
    ],
    'bf0042b9': [
        (log,                           ('1.2: Burnice HairA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('f779fb81', 'Burnice.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('08770e8c', 'Burnice.HairA.LightMap.1024')),
    ],
    '08770e8c': [
        (log,                           ('1.2: Burnice HairA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('f779fb81', 'Burnice.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('bf0042b9', 'Burnice.HairA.LightMap.2048')),
    ],
    '5f2840f1': [
        (log,                           ('1.2: Burnice HairA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        ('f779fb81', 'Burnice.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('3ae3ea20', 'Burnice.HairA.MaterialMap.1024')),
    ],
    '3ae3ea20': [
        (log,                           ('1.2: Burnice HairA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        ('f779fb81', 'Burnice.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('5f2840f1', 'Burnice.HairA.MaterialMap.2048')),
    ],

    # Body身体
    '50bf6521': [
        (log,                           ('1.2: Burnice BodyA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('af63e974', 'Burnice.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('f0e67001', 'Burnice.BodyA.Diffuse.1024')),
    ],
    'f0e67001': [
        (log,                           ('1.2: Burnice BodyA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('af63e974', 'Burnice.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('50bf6521', 'Burnice.BodyA.Diffuse.2048')),
    ],
    'f4e05ee7': [
        (log,                           ('1.2: Burnice BodyA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('af63e974', 'Burnice.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('0a3ba8ac', 'Burnice.BodyA.LightMap.1024')),
    ],
    '0a3ba8ac': [
        (log,                           ('1.2: Burnice BodyA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('af63e974', 'Burnice.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('f4e05ee7', 'Burnice.BodyA.LightMap.2048')),
    ],
    'c321481d': [
        (log,                           ('1.2: Burnice BodyA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        ('af63e974', 'Burnice.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('e37e7622', 'Burnice.BodyA.MaterialMap.1024')),
    ],
    'e37e7622': [
        (log,                           ('1.2: Burnice BodyA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        ('af63e974', 'Burnice.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('c321481d', 'Burnice.BodyA.MaterialMap.2048')),
    ],

    # MARK: Caesar凯撒
    #IB
    '7a8fa826': [(log, ('1.2: Caesar Hair IB Hash',)), (add_ib_check_if_missing,)],
    '92061e5e': [(log, ('1.2: Caesar Body IB Hash',)), (add_ib_check_if_missing,)],
    '6caaeb53': [(log, ('1.2: Caesar Face IB Hash',)), (add_ib_check_if_missing,)],
    #VB

    #Remap
    'af291513': [
        (log,            ('1.2 -> 1.3: Caesar Hair Texcoord Hash',)),
        (update_hash,    ('72537fa3',)),
        (log,            ('+ Remapping texcoord buffer',)),
        (zzz_13_remap_texcoord, (
            '13_Caesar_hair',
            ('4B','2e','2f','2e'),
            ('4B','2f','2f','2f')
        )),
    ],
    '3b2a70a5': [
        (log,            ('1.2 -> 1.3: Caesar Body Texcoord Hash',)),
        (update_hash,    ('0ca81129',)),
        (log,            ('+ Remapping texcoord buffer',)),
        (zzz_13_remap_texcoord, (
            '13_Caesar_body',
            ('4B','2e','2f','2e', '2e'),
            ('4B','2f','2f','2f', '2f')
        )),
    ],

    #Texture纹理
    # Face脸部
    '13098244': [
        (log,                           ('1.2: Caesar FaceA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('6caaeb53', 'Caesar.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('84d53514', 'Caesar.FaceA.Diffuse.1024')),
    ],
    '84d53514': [
        (log,                           ('1.2: Caesar FaceA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('6caaeb53', 'Caesar.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('13098244', 'Caesar.FaceA.Diffuse.2048')),
    ],

    # Hair头发
    '9ce3e80c': [
        (log,                           ('1.2: Caesar HairA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('7a8fa826', 'Caesar.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('b004ab49', 'Caesar.HairA.Diffuse.1024')),
    ],
    'b004ab49': [
        (log,                           ('1.2: Caesar HairA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('7a8fa826', 'Caesar.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('9ce3e80c', 'Caesar.HairA.Diffuse.2048')),
    ],
    'bf19954f': [(log, ('1.7 -> 2.0: Caesar HairA LightMap 2048p Hash',)), (update_hash, ('d5d3585b',))],
    'd5d3585b': [
        (log,                           ('1.2: Caesar HairA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('7a8fa826', 'Caesar.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('89b2d3b3','c7115c4b'), 'Caesar.HairA.LightMap.1024')),
    ],
    'c7115c4b': [(log, ('1.7 -> 2.0: Caesar HairA LightMap 1024p Hash',)), (update_hash, ('89b2d3b3',))],
    '89b2d3b3': [
        (log,                           ('1.2: Caesar HairA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('7a8fa826', 'Caesar.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('d5d3585b','bf19954f'), 'Caesar.HairA.LightMap.2048')),
    ],
    '350b827e': [
        (log,                           ('1.2: Caesar HairA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        ('7a8fa826', 'Caesar.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('2204f89a', 'Caesar.HairA.MaterialMap.1024')),
    ],
    '2204f89a': [
        (log,                           ('1.2: Caesar HairA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        ('7a8fa826', 'Caesar.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('350b827e', 'Caesar.HairA.MaterialMap.2048')),
    ],

    # Body身体
    '5e2cea1a': [
        (log,                           ('1.2: Caesar BodyA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('92061e5e', 'Caesar.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('f4b78da0', 'Caesar.BodyA.Diffuse.1024')),
    ],
    'f4b78da0': [
        (log,                           ('1.2: Caesar BodyA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('92061e5e', 'Caesar.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('5e2cea1a', 'Caesar.BodyA.Diffuse.2048')),
    ],
    '6296d481': [
        (log,                           ('1.2: Caesar BodyA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('92061e5e', 'Caesar.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('a9e24ba0', 'Caesar.BodyA.LightMap.1024')),
    ],
    'a9e24ba0': [
        (log,                           ('1.2: Caesar BodyA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('92061e5e', 'Caesar.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('6296d481', 'Caesar.BodyA.LightMap.2048')),
    ],
    'd5d89d5b': [
        (log,                           ('1.2: Caesar BodyA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        ('92061e5e', 'Caesar.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('328bc108', 'Caesar.BodyA.MaterialMap.1024')),
    ],
    '328bc108': [
        (log,                           ('1.2: Caesar BodyA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        ('92061e5e', 'Caesar.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('d5d89d5b', 'Caesar.BodyA.MaterialMap.2048')),
    ],

    # MARK: Chinatsu千夏
    #IB
    '904ecd0f': [(log, ('2.6: Chinatsu Hair IB Hash',)), (add_ib_check_if_missing,)],
    'b3c6ea5a': [(log, ('2.6: Chinatsu Body IB Hash',)), (add_ib_check_if_missing,)],
    '1a2c8573': [(log, ('2.6: Chinatsu Face IB Hash',)), (add_ib_check_if_missing,)],
    '337a62c1': [(log, ('2.6: Chinatsu BagCharm IB Hash',)), (add_ib_check_if_missing,)],
    'e7a17172': [(log, ('2.6: Chinatsu Paopao IB Hash',)), (add_ib_check_if_missing,)],
    '07a82c9c': [(log, ('2.6: Chinatsu PaopaoA IB Hash',)), (add_ib_check_if_missing,)],
    #VB

    #Texture纹理
    # Face脸部
    'c9b5c6ce': [
        (log,                           ('2.6: Chinatsu FaceA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('1ef66a60', 'Chinatsu.FaceA.Diffuse.1024')),
    ],
    '1ef66a60': [
        (log,                           ('2.6: Chinatsu FaceA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('c9b5c6ce', 'Chinatsu.FaceA.Diffuse.2048')),
    ],

    # Hair头发
    '2fcfee64': [
        (log,                           ('2.6: Chinatsu HairA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('e85201e7', 'Chinatsu.HairA.Diffuse.1024')),
    ],
    'e85201e7': [
        (log,                           ('2.6: Chinatsu HairA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('2fcfee64', 'Chinatsu.HairA.Diffuse.2048')),
    ],
    '8cd786f7': [
        (log,                           ('2.6: Chinatsu HairA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('a2b36369', 'Chinatsu.HairA.LightMap.1024')),
    ],
    'a2b36369': [
        (log,                           ('2.6: Chinatsu HairA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('8cd786f7', 'Chinatsu.HairA.LightMap.2048')),
    ],
    '3f11dfd9': [
        (log,                           ('2.6: Chinatsu HairA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('ab3c12c0', 'Chinatsu.HairA.MaterialMap.1024')),
    ],
    'ab3c12c0': [
        (log,                           ('2.6: Chinatsu HairA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('3f11dfd9', 'Chinatsu.HairA.MaterialMap.2048')),
    ],

    # Body身体
    'f051c211': [
        (log,                           ('2.6: Chinatsu BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('aa0f48fe', 'Chinatsu.BodyA.Diffuse.1024')),
    ],
    'aa0f48fe': [
        (log,                           ('2.6: Chinatsu BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('f051c211', 'Chinatsu.BodyA.Diffuse.2048')),
    ],
    '4aca364a': [
        (log,                           ('2.6: Chinatsu BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('3987c8c2', 'Chinatsu.BodyA.LightMap.1024')),
    ],
    '3987c8c2': [
        (log,                           ('2.6: Chinatsu BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('4aca364a', 'Chinatsu.BodyA.LightMap.2048')),
    ],
    'f3f8895c': [
        (log,                           ('2.6: Chinatsu BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('1d459d73', 'Chinatsu.BodyA.MaterialMap.1024')),
    ],
    '1d459d73': [
        (log,                           ('2.6: Chinatsu BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('f3f8895c', 'Chinatsu.BodyA.MaterialMap.2048')),
    ],

    # BagCharm
    '6c04b56d': [
        (log,                           ('2.6: Chinatsu BagCharmA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('bde1bdad', 'Chinatsu.BagCharmA.Diffuse.1024')),
    ],
    'bde1bdad': [
        (log,                           ('2.6: Chinatsu BagCharmA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('6c04b56d', 'Chinatsu.BagCharmA.Diffuse.2048')),
    ],
    '39dac70b': [
        (log,                           ('2.6: Chinatsu BagCharmA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('9368a6f9', 'Chinatsu.BagCharmA.LightMap.1024')),
    ],
    '9368a6f9': [
        (log,                           ('2.6: Chinatsu BagCharmA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('39dac70b', 'Chinatsu.BagCharmA.LightMap.2048')),
    ],
    '95070f7f': [
        (log,                           ('2.6: Chinatsu BagCharmA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('508c297c', 'Chinatsu.BagCharmA.MaterialMap.1024')),
    ],
    '508c297c': [
        (log,                           ('2.6: Chinatsu BagCharmA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('95070f7f', 'Chinatsu.BagCharmA.MaterialMap.2048')),
    ],

    #Paopao
    '7d8ac131': [
        (log,                           ('2.6: Chinatsu PaopaoA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('be5cd451', 'Chinatsu.PaopaoA.Diffuse.1024')),
    ],
    'be5cd451': [
        (log,                           ('2.6: Chinatsu PaopaoA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('7d8ac131', 'Chinatsu.PaopaoA.Diffuse.2048')),
    ],
    '5c5b6aad': [
        (log,                           ('2.6: Chinatsu PaopaoA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('945afd67', 'Chinatsu.PaopaoA.LightMap.1024')),
    ],
    '945afd67': [
        (log,                           ('2.6: Chinatsu PaopaoA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('5c5b6aad', 'Chinatsu.PaopaoA.LightMap.2048')),
    ],
    '3c4378db': [
        (log,                           ('2.6: Chinatsu PaopaoA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('e9783f84', 'Chinatsu.PaopaoA.MaterialMap.1024')),
    ],
    'e9783f84': [
        (log,                           ('2.6: Chinatsu PaopaoA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('3c4378db', 'Chinatsu.PaopaoA.MaterialMap.2048')),
    ],

    # MARK: ChinatsuSkin千夏皮肤
    #IB
    'a6d82ba5': [(log, ('2.7: ChinatsuSkin Hair IB Hash',)), (add_ib_check_if_missing,)],
    'ee17c9a2': [(log, ('2.6: ChinatsuSkin Body IB Hash',)), (add_ib_check_if_missing,)],
    #VB

    '6cc4d486': [(log, ('2.6 -> 2.7: ChinatsuSkin Hair IB Hash',)),       (update_hash, ('a6d82ba5',))],
    '22c82346': [(log, ('2.6 -> 2.7: ChinatsuSkin Hair Draw Hash',)),     (update_hash, ('74cc56df',))],
    '327644ee': [(log, ('2.6 -> 2.7: ChinatsuSkin Hair Position Hash',)), (update_hash, ('4b93d8eb',))],
    '5e70dde6': [(log, ('2.6 -> 2.7: ChinatsuSkin Hair Texcoord Hash',)), (update_hash, ('b9030f86',))],
    '79de92c7': [(log, ('2.6 -> 2.7: ChinatsuSkin Hair Blend Hash',)),    (update_hash, ('4a795f2a',))],

    'c77b3235': [(log, ('2.6 -> 2.7: ChinatsuSkin Body Position Hash',)), (update_hash, ('25cf6bf7',))],
    '0c6b95ca': [(log, ('2.6 -> 2.7: ChinatsuSkin Body Texcoord Hash',)), (update_hash, ('7a31eb8b',))],
    #Texture纹理
    # Hair头发
    'e5acd978': [
        (log,                           ('2.6: ChinatsuSkin HairA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('8de1219d', 'ChinatsuSkin.HairA.Diffuse.1024')),
    ],
    '8de1219d': [
        (log,                           ('2.6: ChinatsuSkin HairA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('e5acd978', 'ChinatsuSkin.HairA.Diffuse.2048')),
    ],
    '87ce81a5': [
        (log,                           ('2.6: ChinatsuSkin HairA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('9795e08f', 'ChinatsuSkin.HairA.LightMap.1024')),
    ],
    '9795e08f': [
        (log,                           ('2.6: ChinatsuSkin HairA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('87ce81a5', 'ChinatsuSkin.HairA.LightMap.2048')),
    ],
    '5ae5a95b': [
        (log,                           ('2.6: ChinatsuSkin HairA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('f240844c', 'ChinatsuSkin.HairA.MaterialMap.1024')),
    ],
    'f240844c': [
        (log,                           ('2.6: ChinatsuSkin HairA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('5ae5a95b', 'ChinatsuSkin.HairA.MaterialMap.2048')),
    ],

    # Body身体
    'db757608': [
        (log,                           ('2.6: ChinatsuSkin BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('5715ebbe', 'ChinatsuSkin.BodyA.Diffuse.1024')),
    ],
    '5715ebbe': [
        (log,                           ('2.6: ChinatsuSkin BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('db757608', 'ChinatsuSkin.BodyA.Diffuse.2048')),
    ],
    'c9724602': [
        (log,                           ('2.6: ChinatsuSkin BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('335f4f3e', 'ChinatsuSkin.BodyA.LightMap.1024')),
    ],
    '335f4f3e': [
        (log,                           ('2.6: ChinatsuSkin BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('c9724602', 'ChinatsuSkin.BodyA.LightMap.2048')),
    ],
    '719036d1': [
        (log,                           ('2.6: ChinatsuSkin BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('68807c0b', 'ChinatsuSkin.BodyA.MaterialMap.1024')),
    ],
    '68807c0b': [
        (log,                           ('2.6: ChinatsuSkin BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('719036d1', 'ChinatsuSkin.BodyA.MaterialMap.2048')),
    ],

    # MARK: Cissia希希芙
    #IB
    'e4785f80': [(log, ('2.7: Cissia Hair IB Hash',)), (add_ib_check_if_missing,)],
    'ff2ec4d6': [(log, ('2.7: Cissia Body IB Hash',)), (add_ib_check_if_missing,)],
    '4c11c155': [(log, ('2.7: Cissia Tail IB Hash',)), (add_ib_check_if_missing,)],
    'd1a31f0b': [(log, ('2.7: Cissia Face IB Hash',)), (add_ib_check_if_missing,)],
    #VB

    #Texture纹理
    # Face脸部
    '8f55186a': [
        (log,                           ('2.7: Cissia FaceA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('d1a31f0b', 'Cissia.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('c72539cd', 'Cissia.FaceA.Diffuse.1024')),
    ],
    'c72539cd': [
        (log,                           ('2.7: Cissia FaceA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('d1a31f0b', 'Cissia.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('8f55186a', 'Cissia.FaceA.Diffuse.2048')),
    ],

    # Body身体
    'fcfeb117': [
        (log,                           ('2.7: Cissia BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('2638fa23', 'Cissia.BodyA.Diffuse.1024')),
    ],
    '2638fa23': [
        (log,                           ('2.7: Cissia BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('fcfeb117', 'Cissia.BodyA.Diffuse.2048')),
    ],
    '2b6d5c26': [
        (log,                           ('2.7: Cissia BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('4862ab5d', 'Cissia.BodyA.LightMap.1024')),
    ],
    '4862ab5d': [
        (log,                           ('2.7: Cissia BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('2b6d5c26', 'Cissia.BodyA.LightMap.2048')),
    ],
    'e5edf7dd': [
        (log,                           ('2.7: Cissia BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('b0a060f2', 'Cissia.BodyA.MaterialMap.1024')),
    ],
    'b0a060f2': [
        (log,                           ('2.7: Cissia BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('e5edf7dd', 'Cissia.BodyA.MaterialMap.2048')),
    ],
    'b39896c4': [
        (log,                           ('2.7: Cissia BodyB Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('9aa301f1', 'Cissia.BodyB.Diffuse.1024')),
    ],
    '9aa301f1': [
        (log,                           ('2.7: Cissia BodyB Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('b39896c4', 'Cissia.BodyB.Diffuse.2048')),
    ],
    '31674c56': [
        (log,                           ('2.7: Cissia BodyB LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('0c2d5ee2', 'Cissia.BodyB.LightMap.1024')),
    ],
    '0c2d5ee2': [
        (log,                           ('2.7: Cissia BodyB LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('31674c56', 'Cissia.BodyB.LightMap.2048')),
    ],
    'abb852a0': [
        (log,                           ('2.7: Cissia BodyB MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('64a85915', 'Cissia.BodyB.MaterialMap.1024')),
    ],
    '64a85915': [
        (log,                           ('2.7: Cissia BodyB MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('abb852a0', 'Cissia.BodyB.MaterialMap.2048')),
    ],
    'f8739729': [(log,('2.7: -> 2.8: Cissia BodyC Diffuse 2048p Hash',)),(update_hash,('ec85e98d',)),],
    'ec85e98d': [
        (log,                           ('2.7: Cissia BodyC Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   (('f5ecd616','6d861173'), 'Cissia.BodyC.Diffuse.1024')),
    ],
    'f5ecd616': [(log,('2.7: -> 2.8: Cissia BodyC Diffuse 1024p Hash',)),(update_hash,('6d861173',)),],
    '6d861173': [
        (log,                           ('2.7: Cissia BodyC Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   (('f8739729','ec85e98d'), 'Cissia.BodyC.Diffuse.2048')),
    ],
    '6fadb6f5': [
        (log,                           ('2.7: Cissia BodyC LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('090684bd', 'Cissia.BodyC.LightMap.1024')),
    ],
    '090684bd': [
        (log,                           ('2.7: Cissia BodyC LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('6fadb6f5', 'Cissia.BodyC.LightMap.2048')),
    ],
    '1d5d53cd': [
        (log,                           ('2.7: Cissia BodyC MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('d59dc29c', 'Cissia.BodyC.MaterialMap.1024')),
    ],
    'd59dc29c': [
        (log,                           ('2.7: Cissia BodyC MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('1d5d53cd', 'Cissia.BodyC.MaterialMap.2048')),
    ],

    # MARK: Claret
    #IB
    'd942b3a7': [(log, ('3.2: Claret Body IB Hash',)), (add_ib_check_if_missing,)],
    '6467d6c6': [(log, ('3.2: Claret Face IB Hash',)), (add_ib_check_if_missing,)],
    '13596d7b': [(log, ('3.2: Claret Hair IB Hash',)), (add_ib_check_if_missing,)],
    '480eeade': [(log, ('3.2: Claret Headwear IB Hash',)), (add_ib_check_if_missing,)],
    '98ece166': [(log, ('3.2: Claret Leg IB Hash',)), (add_ib_check_if_missing,)],
    '7e1354ab': [(log, ('3.2: Claret weapon IB Hash',)), (add_ib_check_if_missing,)],
    #VB

    #Texture纹理
    # Face脸部
    '05b25205': [
        (log,                           ('3.2: Claret FaceA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('3caf81d7', 'Claret.FaceA.Diffuse.1024')),
    ],
    '3caf81d7': [
        (log,                           ('3.2: Claret FaceA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('05b25205', 'Claret.FaceA.Diffuse.2048')),
    ],
    
    # Hair
    '27ff9425': [
        (log,                           ('3.2: Claret HairA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('539c1df5', 'Claret.HairA.Diffuse.1024')),
    ],
    '539c1df5': [
        (log,                           ('3.2: Claret HairA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('27ff9425', 'Claret.HairA.Diffuse.2048')),
    ],
    '54af7ec2': [
        (log,                           ('3.2: Claret HairA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('ad8c918e', 'Claret.HairA.LightMap.1024')),
    ],
    'ad8c918e': [
        (log,                           ('3.2: Claret HairA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('54af7ec2', 'Claret.HairA.LightMap.2048')),
    ],
    'f328bcde': [
        (log,                           ('3.2: Claret HairA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('d32fb365', 'Claret.HairA.MaterialMap.1024')),
    ],
    'd32fb365': [
        (log,                           ('3.2: Claret HairA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('f328bcde', 'Claret.HairA.MaterialMap.2048')),
    ],
    
    # Body
    '49f33d8f': [
        (log,                           ('3.2: Claret BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('e2cd795e', 'Claret.BodyA.Diffuse.1024')),
    ],
    'e2cd795e': [
        (log,                           ('3.2: Claret BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('49f33d8f', 'Claret.BodyA.Diffuse.2048')),
    ],
    '3327e83f': [
        (log,                           ('3.2: Claret BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('6411f51e', 'Claret.BodyA.LightMap.1024')),
    ],
    '6411f51e': [
        (log,                           ('3.2: Claret BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('3327e83f', 'Claret.BodyA.LightMap.2048')),
    ],
    '875e4282': [
        (log,                           ('3.2: Claret BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('38cb42d1', 'Claret.BodyA.MaterialMap.1024')),
    ],
    '38cb42d1': [
        (log,                           ('3.2: Claret BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('875e4282', 'Claret.BodyA.MaterialMap.2048')),
    ],
        
    # Leg
    '54b5a00b': [
        (log,                           ('3.2: Claret LegA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('76b905e9', 'Claret.LegA.Diffuse.1024')),
    ],
    '76b905e9': [
        (log,                           ('3.2: Claret LegA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('54b5a00b', 'Claret.LegA.Diffuse.2048')),
    ],
    '83d81888': [
        (log,                           ('3.2: Claret LegA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('7a3a0d91', 'Claret.LegA.LightMap.1024')),
    ],
    '7a3a0d91': [
        (log,                           ('3.2: Claret LegA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('83d81888', 'Claret.LegA.LightMap.2048')),
    ],
    '6c63f8ce': [
        (log,                           ('3.2: Claret LegA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('55d77a3a', 'Claret.LegA.MaterialMap.1024')),
    ],
    '55d77a3a': [
        (log,                           ('3.2: Claret LegA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('6c63f8ce', 'Claret.LegA.MaterialMap.2048')),
    ],
    
    # weapon
    '9ff6afae': [
        (log,                           ('3.2: Claret weaponA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('98c65984', 'Claret.weaponA.Diffuse.1024')),
    ],
    '98c65984': [
        (log,                           ('3.2: Claret weaponA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('9ff6afae', 'Claret.weaponA.Diffuse.2048')),
    ],
    'a3fe0a37': [
        (log,                           ('3.2: Claret weaponA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('d6dd0d4e', 'Claret.weaponA.LightMap.1024')),
    ],
    'd6dd0d4e': [
        (log,                           ('3.2: Claret weaponA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('a3fe0a37', 'Claret.weaponA.LightMap.2048')),
    ],
    '7786fad6': [
        (log,                           ('3.2: Claret weaponA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('a8aebda0', 'Claret.weaponA.MaterialMap.1024')),
    ],
    'a8aebda0': [
        (log,                           ('3.2: Claret weaponA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('7786fad6', 'Claret.weaponA.MaterialMap.2048')),
    ],


    # MARK: Corin可琳
    #IB
    '5a839fb2': [(log, ('1.0: Corin Hair IB Hash',)), (add_ib_check_if_missing,)],
    'e74620b5': [(log, ('1.0: Corin Body IB Hash',)), (add_ib_check_if_missing,)],
    '5f803336': [(log, ('1.0: Corin Bear IB Hash',)), (add_ib_check_if_missing,)],
    'a0c80593': [(log, ('1.0: Corin Face IB Hash',)), (add_ib_check_if_missing,)],
    #VB


    '8d999156': [(log, ('1.3 -> 1.4: Corin Hair Blend Hash',)),    (update_hash, ('5fa50113',)),],
    '2cf242f4': [(log, ('1.3 -> 1.4: Corin Hair Texcoord Hash',)), (update_hash, ('abc95b03',)),],

    #Texture纹理
    # Face脸部
    '6d662824': [
        (log,                           ('1.0: Corin FaceA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('a0c80593', 'Corin.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('97022d3c', 'Corin.FaceA.Diffuse.1024')),
    ],
    '97022d3c': [
        (log,                           ('1.0: Corin FaceA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('a0c80593', 'Corin.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('6d662824', 'Corin.FaceA.Diffuse.2048')),
    ],

    # Hair头发
    '60526444': [
        (log,                           ('1.0: Corin HairA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('5a839fb2', 'Corin.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('651e96f8', 'Corin.HairA.Diffuse.1024')),
    ],
    '651e96f8': [
        (log,                           ('1.0: Corin HairA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('5a839fb2', 'Corin.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('60526444', 'Corin.HairA.Diffuse.2048')),
    ],
    '929aca42': [(log, ('1.7 -> 2.0: Corin HairA LightMap 2048p Hash',)), (update_hash, ('74d66671',))],
    '74d66671': [
        (log,                           ('1.0: Corin HairA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('5a839fb2', 'Corin.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('0f300531','edff2372'), 'Corin.HairA.LightMap.1024')),
    ],
    'edff2372': [(log, ('1.7 -> 2.0: Corin HairA LightMap 1024p Hash',)), (update_hash, ('0f300531',))],
    '0f300531': [
        (log,                           ('1.0: Corin HairA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('5a839fb2', 'Corin.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('74d66671','929aca42'), 'Corin.HairA.LightMap.2048')),
    ],
    # '23b4c60d': [
    #     (log,                           ('1.0: Corin HairA MaterialMap 2048p Hash',)),
    #     (add_section_if_missing,        ('5a839fb2', 'Corin.Hair.IB', 'match_priority = 0\n')),
    #     (multiply_section_if_missing,   ('1b88e01e', 'Corin.HairA.MaterialMap.1024')),
    # ],
    # '1b88e01e': [
    #     (log,                           ('1.0: Corin HairA MaterialMap 1024p Hash',)),
    #     (add_section_if_missing,        ('5a839fb2', 'Corin.Hair.IB', 'match_priority = 0\n')),
    #     (multiply_section_if_missing,   ('23b4c60d', 'Corin.HairA.MaterialMap.2048')),
    # ],

    # Body身体 
    'af9d845a': [
        (log,                           ('1.0: Corin BodyA, BearA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('681f5162', 'Corin.BodyA.Diffuse.1024')),
    ],
    '681f5162': [
        (log,                           ('1.0: Corin BodyA, BearA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('af9d845a', 'Corin.BodyA.Diffuse.2048')),
    ],
    '75e05cdc': [(log, ('1.7 -> 2.0: Corin BodyA, BearA LightMap 2048p Hash',)), (update_hash, ('e1c1718f',))],
    'e1c1718f': [
        (log,                           ('1.0: Corin BodyA, BearA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   (('068be251','af7eda82'), 'Corin.BodyA.LightMap.1024')),
    ],
    'af7eda82': [(log, ('1.7 -> 2.0: Corin BodyA, BearA LightMap 1024p Hash',)), (update_hash, ('068be251',))],
    '068be251': [
        (log,                           ('1.0: Corin BodyA, BearA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   (('e1c1718f','75e05cdc'), 'Corin.BodyA.LightMap.2048')),
    ],
    '50a0faea': [(log, ('1.7 -> 2.0: Corin BodyA, BearA MaterialMap 2048p Hash',)), (update_hash, ('e58d9767',))],
    'e58d9767': [
        (log,                           ('1.0: Corin BodyA, BearA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   (('50ed6c50','9dc9c0f6'), 'Corin.BodyA.MaterialMap.1024')),
    ],
    '9dc9c0f6': [(log, ('1.7 -> 2.0: Corin BodyA, BearA MaterialMap 1024p Hash',)), (update_hash, ('50ed6c50',))],
    '50ed6c50': [
        (log,                           ('1.0: Corin BodyA, BearA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   (('e58d9767','50a0faea'), 'Corin.BodyA.MaterialMap.2048')),
    ],

    # MARK: Dialyn琉音
    #IB
    '68f00074': [(log, ('2.4: Dialyn Hair IB Hash',)), (add_ib_check_if_missing,)],
    'af39a873': [(log, ('2.4: Dialyn Body IB Hash',)), (add_ib_check_if_missing,)],
    'facb2461': [(log, ('2.4: Dialyn Face IB Hash',)), (add_ib_check_if_missing,)],
    #VB
    #不再提供对脸部vb的修复，不建议对脸部模型进行修改，可能会导致脸部贴图错位
    #'d90368ed': [(log, ('3.1 -> 3.2: Dialyn Eyebrow-眉毛 texcoord_vb Hash',)), (update_hash, ('27fd9193',))],
    #'f6c5296e': [(log, ('3.1 -> 3.2: Dialyn Face-脸部 texcoord_vb Hash',)), (update_hash, ('dafc9647',))],
    #Remap
    '6ff0e4ad': [
        (log,                         ('2.4 -> 2.5: Dialyn Body Blend Remap',)),
        (update_buffer_blend_indices, (
            '6ff0e4ad',
            (18, 19, 20, 54, 55, 56, 57, 58, 59, 60, 61, 62, 69, 70, 71, 72, 91, 92, 93, 94, 95, 96, 97, 98, 113, 114, 128, 129, 130, 131, 132, 188, 189),
            (20, 18, 19, 62, 54, 55, 56, 57, 58, 59, 60, 61, 71, 72, 70, 69, 98, 91, 92, 93, 94, 95, 96, 97, 114, 113, 129, 128, 132, 130, 131, 189, 188),
        )),
        (update_hash,                 ('3d7e53cf',)),
    ],
    

    #Texture纹理
    # Face脸部
    'ad65abbf': [
        (log,                           ('2.4: Dialyn FaceA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('facb2461', 'Dialyn.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('56bc2921', 'Dialyn.FaceA.Diffuse.1024')),
    ],
    '56bc2921': [
        (log,                           ('2.4: Dialyn FaceA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('facb2461', 'Dialyn.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('ad65abbf', 'Dialyn.FaceA.Diffuse.2048')),
    ],

    # Hair头发
    '4f8d9492': [
        (log,                           ('2.4: Dialyn HairA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('4dfbd393', 'Dialyn.HairA.Diffuse.1024')),
    ],
    '4dfbd393': [
        (log,                           ('2.4: Dialyn HairA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('4f8d9492', 'Dialyn.HairA.Diffuse.2048')),
    ],
    'a3f74f7d': [
        (log,                           ('2.4: Dialyn HairA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('df9b8ecd', 'Dialyn.HairA.LightMap.1024')),
    ],
    'df9b8ecd': [
        (log,                           ('2.4: Dialyn HairA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('a3f74f7d', 'Dialyn.HairA.LightMap.2048')),
    ],
    '17aadaf6': [
        (log,                           ('2.4: Dialyn HairA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('5e6d6607', 'Dialyn.HairA.MaterialMap.1024')),
    ],
    '5e6d6607': [
        (log,                           ('2.4: Dialyn HairA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('17aadaf6', 'Dialyn.HairA.MaterialMap.2048')),
    ],

    # Body身体
    '52ea588e': [
        (log,                           ('2.4: Dialyn BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('76ca930e', 'Dialyn.BodyA.Diffuse.1024')),
    ],
    '76ca930e': [
        (log,                           ('2.4: Dialyn BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('52ea588e', 'Dialyn.BodyA.Diffuse.2048')),
    ],
    '5cc175fe': [
        (log,                           ('2.4: Dialyn BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('8c2fea9f', 'Dialyn.BodyA.LightMap.1024')),
    ],
    '8c2fea9f': [
        (log,                           ('2.4: Dialyn BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('5cc175fe', 'Dialyn.BodyA.LightMap.2048')),
    ],
    '28a10401': [
        (log,                           ('2.4: Dialyn BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('a2425ea0', 'Dialyn.BodyA.MaterialMap.1024')),
    ],
    'a2425ea0': [
        (log,                           ('2.4: Dialyn BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('28a10401', 'Dialyn.BodyA.MaterialMap.2048')),
    ],

    # MARK: Ellen艾莲
    #IB
    'd44a8015': [(log, ('1.1: Ellen Hair IB Hash',)), (add_ib_check_if_missing,)],
    'e30fae03': [(log, ('1.1: Ellen Body IB Hash',)), (add_ib_check_if_missing,)],
    'f6ef8f3a': [(log, ('1.1: Ellen Face IB Hash',)), (add_ib_check_if_missing,)],
    #VB
    '9c7fac5a': [(log, ('1.0 -> 1.1: Ellen Face IB Hash',)),       (update_hash, ('f6ef8f3a',))],
    '7f89a2b3': [(log, ('1.0 -> 1.1: Ellen Hair IB Hash',)),       (update_hash, ('d44a8015',))],
    'a72cfb34': [(log, ('1.0 -> 1.1: Ellen Body IB Hash',)),       (update_hash, ('e30fae03',))],

    #不再提供对脸部vb的修复，不建议对脸部模型进行修改，可能会导致脸部贴图错位
    #'83dfd744': [(log, ('1.0 -> 1.1: Ellen Face Texcoord Hash',)), (update_hash, ('8744badf',))],


    'd59a5fec': [(log, ('1.0 -> 1.1: Ellen Hair Draw Hash',)),     (update_hash, ('77ac5f85',))],
    'a5448398': [(log, ('1.0 -> 1.1: Ellen Hair Position Hash',)), (update_hash, ('ba0fe600',))],
    #Remap
    '9cddb082': [
        (log, ('1.0 -> 1.1: Ellen Hair Texcoord Hash',)),
        (update_hash, ('5c33833e',)),
        (log, ('+ Remapping texcoord buffer from stride 24 to 36',)),
        (zzz_13_remap_texcoord, ('11_Ellen_Hair', ('4B', '2e', '2f', '2e', '2e'), ('4f', '2e', '2f', '2e', '2e'))), # attention
    ],

    '5c33833e': [
        (log, ('1.1 -> 1.2: Ellen Hair Texcoord Hash',)),
        (update_hash, ('a27a8e1a',)),
        (log, ('+ Remapping texcoord buffer from stride 36 to 24',)),
        (zzz_12_shrink_texcoord_color, ('1.2',))
    ],
    '52188576': [
        (log,                         ('1.3 -> 1.4: Ellen Hair Blend Remap',)),
        (update_buffer_blend_indices, (
            '52188576',
            (34, 35, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 49, 50),
            (39, 34, 40, 35, 38, 42, 43, 44, 45, 46, 47, 41, 50, 49),
        )),
        (update_hash,                 ('e91c93e0',)),
    ],


    '7bd3f8c2': [(log, ('1.0 -> 1.1: Ellen Body Draw Hash',)),     (update_hash, ('cdce1fc2',))],
    '89d5fba4': [(log, ('1.0 -> 1.1: Ellen Body Position Hash',)), (update_hash, ('b78f3616',))],
    '26966844': [(log, ('1.0 -> 1.1: Ellen Body Texcoord Hash',)), (update_hash, ('5ac6d5ee',))],
    '89589539': [(log, ('1.5 -> 1.6: Ellen Body Blend Hash',)),    (update_hash, ('ed9cb852',))],

    #Texture纹理
    # Face脸部
    '09d55bce': [(log, ('1.0 -> 1.1: Ellen FaceA Diffuse 2048p Hash',)), (update_hash, ('465a66eb',))],
    '465a66eb': [
        (log,                           ('1.1: Ellen FaceA Diffuse 2048p Hash',)),
        (add_section_if_missing,        (('f6ef8f3a', '9c7fac5a'), 'Ellen.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('4808d050', 'e6b27e31'), 'Ellen.FaceA.Diffuse.1024')),
    ],
    'e6b27e31': [(log, ('1.0 -> 1.1: Ellen FaceA Diffuse 1024p Hash',)), (update_hash, ('4808d050',))],
    '4808d050': [
        (log,                           ('1.1: Ellen FaceA Diffuse 1024p Hash',)),
        (add_section_if_missing,        (('f6ef8f3a', '9c7fac5a'), 'Ellen.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('465a66eb', '09d55bce'), 'Ellen.FaceA.Diffuse.2048')),
    ],

    # Hair头发
    '81ccd2e2': [
        (log,                           ('1.0: Ellen HairA Diffuse 2048p Hash',)),
        (add_section_if_missing,        (('d44a8015', '7f89a2b3'), 'Ellen.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('1440e534', 'Ellen.HairA.Diffuse.1024')),
    ],
    '1440e534': [
        (log,                           ('1.0: Ellen HairA Diffuse 1024p Hash',)),
        (add_section_if_missing,        (('d44a8015', '7f89a2b3'), 'Ellen.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('81ccd2e2', 'Ellen.HairA.Diffuse.2048')),
    ],
    'dc9d8b6e': [
        (log,                           ('1.0: Ellen HairA LightMap 2048p Hash',)),
        (add_section_if_missing,        (('d44a8015', '7f89a2b3'), 'Ellen.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('8c835faa', 'Ellen.HairA.LightMap.1024')),
    ],
    '8c835faa': [
        (log,                           ('1.0: Ellen HairA LightMap 1024p Hash',)),
        (add_section_if_missing,        (('d44a8015', '7f89a2b3'), 'Ellen.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('dc9d8b6e', 'Ellen.HairA.LightMap.2048')),
    ],
    '01bb8189': [
        (log,                           ('1.0: Ellen HairA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        (('d44a8015', '7f89a2b3'), 'Ellen.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('b21b8370', 'Ellen.HairA.MaterialMap.1024')),
    ],
    'b21b8370': [
        (log,                           ('1.0: Ellen HairA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        (('d44a8015', '7f89a2b3'), 'Ellen.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('01bb8189', 'Ellen.HairA.MaterialMap.2048')),
    ],

    # Body身体
    'cf5f5fed': [
        (log,                           ('1.0: -> 1.1: Ellen BodyA Diffuse 2048p Hash',)),
        (update_hash,                   ('163e2559',)),
    ],
    '163e2559': [
        (log,                           ('1.1: Ellen BodyA Diffuse 2048p Hash',)),
        (add_section_if_missing,        (('e30fae03', 'a72cfb34'), 'Ellen.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('22fa0cd6', '94c15986'), 'Ellen.BodyA.Diffuse.1024')),
    ],
    '94c15986': [
        (log,                           ('1.0: -> 1.1: Ellen BodyA Diffuse 1024p Hash',)),
        (update_hash,                   ('22fa0cd6',)),
    ],
    '22fa0cd6': [
        (log,                           ('1.1: Ellen BodyA Diffuse 1024p Hash',)),
        (add_section_if_missing,        (('e30fae03', 'a72cfb34'), 'Ellen.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('163e2559', 'cf5f5fed'), 'Ellen.BodyA.Diffuse.2048')),
    ],
    'ff26fb83': [
        (log,                           ('1.0: Ellen BodyA LightMap 2048p Hash',)),
        (add_section_if_missing,        (('e30fae03', 'a72cfb34'), 'Ellen.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('cea7516a', 'Ellen.BodyA.LightMap.1024')),
    ],
    'cea7516a': [
        (log,                           ('1.0: Ellen BodyA LightMap 1024p Hash',)),
        (add_section_if_missing,        (('e30fae03', 'a72cfb34'), 'Ellen.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('ff26fb83', 'Ellen.BodyA.LightMap.2048')),
    ],
    'f4487235': [
        (log,                           ('1.0: Ellen BodyA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        (('e30fae03', 'a72cfb34'), 'Ellen.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('30dc14d7', 'Ellen.BodyA.MaterialMap.1024')),
    ],
    '30dc14d7': [
        (log,                           ('1.0: Ellen BodyA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        (('e30fae03', 'a72cfb34'), 'Ellen.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('f4487235', 'Ellen.BodyA.MaterialMap.2048')),
    ],

    # MARK: EllenSkin艾莲皮肤
    #IB
    'f601f643': [(log, ('1.5: EllenSkin Hair Leg IB Hash',)), (add_ib_check_if_missing,)],
    '4a938c0a': [(log, ('1.5: EllenSkin Body IB Hash',)), (add_ib_check_if_missing,)],
    'fafcfe36': [(log, ('1.5: EllenSkin Tail IB Hash',)), (add_ib_check_if_missing,)],
    #VB
    #Texture纹理
    # Hair头发 Leg
    '6e15911b': [
        (log,                           ('1.5: EllenSkin HairA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('37eefb17', 'EllenSkin.HairA.Diffuse.1024')),
    ],
    '37eefb17': [
        (log,                           ('1.5: EllenSkin HairA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('6e15911b', 'EllenSkin.HairA.Diffuse.2048')),
    ],
    '48fd827b': [
        (log,                           ('1.5: EllenSkin HairA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('aa77b3ff', 'EllenSkin.HairA.LightMap.1024')),
    ],
    'aa77b3ff': [
        (log,                           ('1.5: EllenSkin HairA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('48fd827b', 'EllenSkin.HairA.LightMap.2048')),
    ],
    '0de025b4': [(log, ('1.7 -> 2.0: EllenSkin HairA MaterialMap 2048p Hash',)), (update_hash, ('8740602f',))],
    '8740602f': [
        (log,                           ('1.5: EllenSkin HairA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   (('0ab940d8', '0cf3cd79'), 'EllenSkin.HairA.MaterialMap.1024')),
    ],
    '0cf3cd79': [(log, ('1.5 -> 2.0: EllenSkin HairA MaterialMap 1024p Hash',)), (update_hash, ('0ab940d8',))],
    '0ab940d8': [
        (log,                           ('1.5: EllenSkin HairA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   (('8740602f','0de025b4'), 'EllenSkin.HairA.MaterialMap.2048')),
    ],
    # Body身体
    '76f42184': [
        (log,                           ('1.5: EllenSkin BodyA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('4a938c0a', 'EllenSkin.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('61beec5c', 'EllenSkin.BodyA.Diffuse.1024')),
    ],
    '61beec5c': [
        (log,                           ('1.5: EllenSkin BodyA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('4a938c0a', 'EllenSkin.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('76f42184', 'EllenSkin.BodyA.Diffuse.2048')),
    ],
    'e6c9a6e1': [
        (log,                           ('1.5: EllenSkin BodyA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('4a938c0a', 'EllenSkin.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('d13c6700', 'EllenSkin.BodyA.LightMap.1024')),
    ],
    'd13c6700': [
        (log,                           ('1.5: EllenSkin BodyA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('4a938c0a', 'EllenSkin.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('e6c9a6e1', 'EllenSkin.BodyA.LightMap.2048')),
    ],
    'd08f1a54': [(log, ('1.7 -> 2.0: EllenSkin BodyA MaterialMap 2048p Hash',)), (update_hash, ('1d7b458d',))],
    '1d7b458d': [
        (log,                           ('1.5: EllenSkin BodyA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        ('4a938c0a', 'EllenSkin.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('ae919d9f', 'a4b66af3'), 'EllenSkin.BodyA.MaterialMap.1024')),
    ],
    'a4b66af3': [(log, ('1.5 -> 2.0: EllenSkin BodyA MaterialMap 1024p Hash',)), (update_hash, ('ae919d9f',))],
    'ae919d9f': [
        (log,                           ('1.5: EllenSkin BodyA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        ('4a938c0a', 'EllenSkin.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('1d7b458d','d08f1a54'), 'EllenSkin.BodyA.MaterialMap.2048')),
    ],
    # Tail
    '0e474202': [
        (log,                           ('1.5: EllenSkin TailA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('fafcfe36', 'EllenSkin.Tail.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('8df52d2a', 'EllenSkin.TailA.Diffuse.1024')),
    ],
    '8df52d2a': [
        (log,                           ('1.5: EllenSkin TailA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('fafcfe36', 'EllenSkin.Tail.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('0e474202', 'EllenSkin.TailA.Diffuse.2048')),
    ],
    '8f2cb44d': [
        (log,                           ('1.5: EllenSkin TailA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('fafcfe36', 'EllenSkin.Tail.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('a2f7a7db', 'EllenSkin.TailA.LightMap.1024')),
    ],
    'a2f7a7db': [
        (log,                           ('1.5: EllenSkin TailA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('fafcfe36', 'EllenSkin.Tail.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('8f2cb44d', 'EllenSkin.TailA.LightMap.2048')),
    ],
    'abb51170': [(log, ('1.7 -> 2.0: EllenSkin TailA MaterialMap 2048p Hash',)), (update_hash, ('51cc39d5',))],
    '51cc39d5': [
        (log,                           ('1.5: EllenSkin TailA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        ('fafcfe36', 'EllenSkin.Tail.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('cf37068c', 'beb3f207'), 'EllenSkin.TailA.MaterialMap.1024')),
    ],
    'beb3f207': [(log, ('1.5 -> 2.0: EllenSkin TailA MaterialMap 1024p Hash',)), (update_hash, ('cf37068c',))],
    'cf37068c': [
        (log,                           ('1.5: EllenSkin TailA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        ('fafcfe36', 'EllenSkin.Tail.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('51cc39d5','abb51170'), 'EllenSkin.TailA.MaterialMap.2048')),
    ],

    # MARK: Evelyn伊芙琳
    #IB
    '10a5bde2': [(log, ('1.5: Evelyn Hair IB Hash',)),      (add_ib_check_if_missing,)],
    '04b53ecd': [(log, ('1.5: Evelyn Body IB Hash',)),      (add_ib_check_if_missing,)],
    'bb6d1023': [(log, ('1.5: Evelyn Jacket IB Hash',)),    (add_ib_check_if_missing,)],
    'b3eaedb0': [(log, ('1.5: Evelyn Shoulders IB Hash',)), (add_ib_check_if_missing,)],
    'ddf4efa6': [(log, ('1.5: Evelyn Face IB Hash',)),      (add_ib_check_if_missing,)],
    #VB

    #Texture纹理
    # Face脸部
    '8e1d1a6f': [
        (log,                           ('1.5: Evelyn FaceA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('ddf4efa6', 'Evelyn.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('bc090438', 'Evelyn.FaceA.Diffuse.1024')),
    ],
    'bc090438': [
        (log,                           ('1.5: Evelyn FaceA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('ddf4efa6', 'Evelyn.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('8e1d1a6f', 'Evelyn.FaceA.Diffuse.2048')),
    ],

    # Hair头发
    '0e5c3c97': [
        (log,                           ('1.5: Evelyn Hair, Jacket Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('65a7592d', 'Evelyn.Hair.Diffuse.1024')),
    ],
    '65a7592d': [
        (log,                           ('1.5: Evelyn Hair, Jacket Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('0e5c3c97', 'Evelyn.Hair.Diffuse.2048')),
    ],
    'e1434e0d': [
        (log,                           ('1.5: Evelyn Hair, Jacket LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('eb414a98', 'Evelyn.Hair.LightMap.1024')),
    ],
    'eb414a98': [
        (log,                           ('1.5: Evelyn Hair, Jacket LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('e1434e0d', 'Evelyn.Hair.LightMap.2048')),
    ],
    'b2718585': [
        (log,                           ('1.5: Evelyn Hair, Jacket MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('e680f0c7', 'Evelyn.Hair.MaterialMap.1024')),
    ],
    'e680f0c7': [
        (log,                           ('1.5: Evelyn Hair, Jacket MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('b2718585', 'Evelyn.Hair.MaterialMap.2048')),
    ],

    # Body身体
    'a59b14c0': [
        (log,                           ('1.5: Evelyn Body, Shoulder Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('93033898', 'Evelyn.Body.Diffuse.1024')),
    ],
    '93033898': [
        (log,                           ('1.5: Evelyn Body, Shoulder Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('a59b14c0', 'Evelyn.Body.Diffuse.2048')),
    ],
    'd022d32c': [
        (log,                           ('1.5: Evelyn Body, Shoulder LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('16aab2ab', 'Evelyn.Body.LightMap.1024')),
    ],
    '16aab2ab': [
        (log,                           ('1.5: Evelyn Body, Shoulder LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('d022d32c', 'Evelyn.Body.LightMap.2048')),
    ],
    '8624e4e4': [
        (log,                           ('1.5: Evelyn Body, Shoulder MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('716561f0', 'Evelyn.Body.MaterialMap.1024')),
    ],
    '716561f0': [
        (log,                           ('1.5: Evelyn Body, Shoulder MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('8624e4e4', 'Evelyn.Body.MaterialMap.2048')),
    ],

    # MARK: Grace格莉丝
    #IB
    '89299f56': [(log, ('1.0: Grace Hair IB Hash',)), (add_ib_check_if_missing,)],
    '8b240678': [(log, ('1.2: Grace Body IB Hash',)), (add_ib_check_if_missing,)],
    '4d60568b': [(log, ('1.0: Grace Face IB Hash',)), (add_ib_check_if_missing,)],
    #VB
    'e5e04f6f': [(log, ('1.1 -> 1.2: Grace Body Draw Hash',)),     (update_hash, ('f1cba806',))],
    'e536af35': [(log, ('1.1 -> 1.2: Grace Body Texcoord Hash',)), (update_hash, ('4bb45448',))],
    '0f82a13e': [
        (log, ('1.1 -> 1.2: Grace Body IB Hash',)),
        (update_hash, ('8b240678',)),
        (transfer_indexed_sections, {
            'src_indices': ['0', '42885'],
            'trg_indices': ['0', '42927'],
        })
    ],

    #Remap
    # reverted in 1.2
    # '89d903ba': [
    #     (log, ('1.0: -> 1.1: Grace Hair Texcoord Hash',)),
    #     (update_hash, ('d21f32ad',)),
    #     (log, ('+ Remapping texcoord buffer from stride 20 to 32',)),
    #     (update_buffer_element_width, (('BBBB', 'ee', 'ff', 'ee'), ('ffff', 'ee', 'ff', 'ee'), '1.1')),
    #     (log, ('+ Setting texcoord vcolor alpha to 1',)),
    #     (update_buffer_element_value, (('ffff', 'ee', 'ff', 'ee'), ('xxx1', 'xx', 'xx', 'xx'), '1.1'))
    # ],

    'd21f32ad': [
        (log, ('1.1 -> 1.2: Grace Hair Texcoord Hash',)),
        (update_hash, ('89d903ba',)),
        (log, ('+ Remapping texcoord buffer',)),
        (zzz_12_shrink_texcoord_color, ('1.2',))
    ],

    '26ffa186': [
        (log, ('1.1 -> 1.2: Grace Body Position Hash',)),
        (update_hash, ('8855c5cf',)),
        (log, ('1.1 -> 1.2: Grace Body Blend Remap',)),
        (update_buffer_blend_indices, (
            '8855c5cf',
            (35, 34, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67,  68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89),
            (34, 35, 80, 85, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 51, 47, 48, 49, 50, 52, 54, 53, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 66,  65, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 89, 78, 79, 81, 82, 83, 84, 86, 87, 88),
        ))
    ],

    #Texture纹理
    # Face脸部
    '7459ecf4': [
        (log,                           ('1.0: Grace FaceA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('4d60568b', 'Grace.FaceA.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('e75590cb', 'Grace.FaceA.Diffuse.1024')),
    ],
    'e75590cb': [
        (log,                           ('1.0: Grace FaceA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('4d60568b', 'Grace.FaceA.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('7459ecf4', 'Grace.FaceA.Diffuse.2048')),
    ],

    # Hair头发
    'a87d2822': [
        (log,                           ('1.0: Grace HairA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('89299f56', 'Grace.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('94d04401', 'Grace.HairA.Diffuse.1024')),
    ],
    '94d04401': [
        (log,                           ('1.0: Grace HairA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('89299f56', 'Grace.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('a87d2822', 'Grace.HairA.Diffuse.2048')),
    ],
    '8eddd041': [(log, ('1.7 -> 2.0: Grace HairA LightMap 2048p Hash',)), (update_hash, ('a22d2c2c',))],
    'a22d2c2c': [
        (log,                           ('1.0: Grace HairA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('89299f56', 'Grace.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('48c17612','26bf1588'), 'Grace.HairA.LightMap.1024')),
    ],
    '26bf1588': [(log, ('1.7 -> 2.0: Grace HairA LightMap 1024p Hash',)), (update_hash, ('48c17612',))],
    '48c17612': [
        (log,                           ('1.0: Grace HairA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('89299f56', 'Grace.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('a22d2c2c','8eddd041'), 'Grace.HairA.LightMap.2048')),
    ],
    '3a38f6f9': [(log, ('1.7 -> 2.0: Grace HairA MaterialMap 2048p Hash',)), (update_hash, ('7bb81a4f',))],
    '7bb81a4f': [
        (log,                           ('1.0: Grace HairA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        ('89299f56', 'Grace.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('381930fe','e1cb3739'), 'Grace.HairA.MaterialMap.1024')),
    ],
    'e1cb3739': [(log, ('1.7 -> 2.0: Grace HairA MaterialMap 1024p Hash',)), (update_hash, ('381930fe',))],
    '381930fe': [
        (log,                           ('1.0: Grace HairA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        ('89299f56', 'Grace.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('7bb81a4f','3a38f6f9'), 'Grace.HairA.MaterialMap.2048')),
    ],

    # Body身体
    '6d6ac4f4': [
        (log,                           ('1.0: Grace BodyA Diffuse 2048p Hash',)),
        (add_section_if_missing,        (('8b240678', '0f82a13e'), 'Grace.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('397a8aed', 'Grace.BodyA.Diffuse.1024')),
    ],
    '397a8aed': [
        (log,                           ('1.0: Grace BodyA Diffuse 1024p Hash',)),
        (add_section_if_missing,        (('8b240678', '0f82a13e'), 'Grace.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('6d6ac4f4', 'Grace.BodyA.Diffuse.2048')),
    ],
    '993fe3e1': [(log, ('1.7 -> 2.0: Grace BodyA LightMap 2048p Hash',)), (update_hash, ('895fa458',))],
    '895fa458': [
        (log,                           ('1.0: Grace BodyA LightMap 2048p Hash',)),
        (add_section_if_missing,        (('8b240678', '0f82a13e'), 'Grace.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('7e2e15b3','59dd8899'), 'Grace.BodyA.LightMap.1024')),
    ],
    '59dd8899': [(log, ('1.7 -> 2.0: Grace BodyA LightMap 1024p Hash',)), (update_hash, ('7e2e15b3',))],
    '7e2e15b3': [
        (log,                           ('1.0: Grace BodyA LightMap 1024p Hash',)),
        (add_section_if_missing,        (('8b240678', '0f82a13e'), 'Grace.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('895fa458','993fe3e1'), 'Grace.BodyA.LightMap.2048')),
    ],
    'e8345f2c': [
        (log,                           ('1.0: Grace BodyA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        (('8b240678', '0f82a13e'), 'Grace.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('a6c8c203', 'Grace.BodyA.MaterialMap.1024')),
    ],
    'a6c8c203': [
        (log,                           ('1.0: Grace BodyA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        (('8b240678', '0f82a13e'), 'Grace.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('e8345f2c', 'Grace.BodyA.MaterialMap.2048')),
    ],
    '210b3ebf': [(log, ('1.3 -> 1.4: Grace BodyB Diffuse 2048p Hash',)), (update_hash, ('9c7057e8',))],
    '9c7057e8': [
        (log,                           ('1.4: Grace BodyB Diffuse 2048p Hash',)),
        (add_section_if_missing,        (('8b240678', '0f82a13e'), 'Grace.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('ac361185', '21794bd6'), 'Grace.BodyB.Diffuse.1024')),
    ],
    '21794bd6': [(log, ('1.3 -> 1.4: Grace BodyB Diffuse 1024p Hash',)), (update_hash, ('ac361185',))],
    'ac361185': [
        (log,                           ('1.4: Grace BodyB Diffuse 1024p Hash',)),
        (add_section_if_missing,        (('8b240678', '0f82a13e'), 'Grace.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('9c7057e8', '210b3ebf'), 'Grace.BodyB.Diffuse.2048')),
    ],
    '08082f5f': [
        (log,                           ('1.0: Grace BodyB LightMap 2048p Hash',)),
        (add_section_if_missing,        (('8b240678', '0f82a13e'), 'Grace.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('a60162a0', 'Grace.BodyB.LightMap.1024')),
    ],
    'a60162a0': [
        (log,                           ('1.0: Grace BodyB LightMap 1024p Hash',)),
        (add_section_if_missing,        (('8b240678', '0f82a13e'), 'Grace.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('08082f5f', 'Grace.BodyB.LightMap.2048')),
    ],
    'f176398a': [
        (log,                           ('1.0: Grace BodyB MaterialMap 2048p Hash',)),
        (add_section_if_missing,        (('8b240678', '0f82a13e'), 'Grace.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('b5b88a3f', 'Grace.BodyB.MaterialMap.1024')),
    ],
    'b5b88a3f': [
        (log,                           ('1.0: Grace BodyB MaterialMap 1024p Hash',)),
        (add_section_if_missing,        (('8b240678', '0f82a13e'), 'Grace.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('f176398a', 'Grace.BodyB.MaterialMap.2048')),
    ],

    # MARK: Harumasa浅羽悠真   
    #IB
    '6324de38': [(log, ('1.4: Harumasa Hair IB Hash',)), (add_ib_check_if_missing,)],
    'aa7ba2dc': [(log, ('1.4: Harumasa Legs IB Hash',)), (add_ib_check_if_missing,)],
    '79679a10': [(log, ('1.4: Harumasa Body IB Hash',)), (add_ib_check_if_missing,)],
    'b0688334': [(log, ('1.4: Harumasa Face IB Hash',)), (add_ib_check_if_missing,)],
    #VB

    '78bea30d': [(log, ('1.4 -> 1.5: Harumasa Body IB Hash',)), (update_hash, ('79679a10',))],

    'cafffd37': [(log, ('1.4 -> 1.5: Harumasa Body Draw Hash',)),     (update_hash, ('1fb92e46',))],
    '3fa41462': [(log, ('1.4 -> 1.5: Harumasa Body Position Hash',)), (update_hash, ('0899751e',))],
    'c0b32d17': [(log, ('1.4 -> 1.5: Harumasa Body Blend Hash',)),    (update_hash, ('347a0e9d',))],
    '95ee1030': [(log, ('1.4 -> 1.5: Harumasa Body Texcoord Hash',)), (update_hash, ('e14fbc30',))],

    #Texture纹理
    # Face脸部
    '4394c0b2': [
        (log,                           ('1.4: Harumasa FaceA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('b0688334', 'Harumasa.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('c5596262', 'Harumasa.FaceA.Diffuse.1024')),
    ],
    'c5596262': [
        (log,                           ('1.4: Harumasa FaceA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('b0688334', 'Harumasa.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('4394c0b2', 'Harumasa.FaceA.Diffuse.2048')),
    ],

    # Hair头发
    'b8f268ee': [
        (log,                           ('1.4: Harumasa HairA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('6324de38', 'Harumasa.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('5700ced5', 'Harumasa.HairA.Diffuse.1024')),
    ],
    '5700ced5': [
        (log,                           ('1.4: Harumasa HairA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('6324de38', 'Harumasa.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('b8f268ee', 'Harumasa.HairA.Diffuse.2048')),
    ],
    'd4838b9d': [(log, ('1.7 -> 2.0: Harumasa HairA LightMap 2048p Hash',)), (update_hash, ('11041778',))],
    '11041778': [
        (log,                           ('1.4: Harumasa HairA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('6324de38', 'Harumasa.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('54cc6a9a','a1310b4f'), 'Harumasa.HairA.LightMap.1024')),
    ],
    'a1310b4f': [(log, ('1.7 -> 2.0: Harumasa HairA LightMap 1024p Hash',)), (update_hash, ('54cc6a9a',))],
    '54cc6a9a': [
        (log,                           ('1.4: Harumasa HairA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('6324de38', 'Harumasa.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('11041778','d4838b9d'), 'Harumasa.HairA.LightMap.2048')),
    ],
    '7217c146': [
        (log,                           ('1.4: Harumasa HairA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        ('6324de38', 'Harumasa.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('c2c9ad2d', 'Harumasa.HairA.MaterialMap.1024')),
    ],
    'c2c9ad2d': [
        (log,                           ('1.4: Harumasa HairA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        ('6324de38', 'Harumasa.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('7217c146', 'Harumasa.HairA.MaterialMap.2048')),
    ],

    # Body身体
    'ba52ac92': [(log, ('1.4 -> 1.5: Harumasa BodyA Diffuse 2048p Hash',)), (update_hash, ('49f8aaf6',))],
    '49f8aaf6': [
        (log,                           ('1.4: Harumasa BodyA Diffuse 2048p Hash',)),
        (add_section_if_missing,        (('79679a10', '78bea30d'), 'Harumasa.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('999ec526', 'e0b0c6eb'), 'Harumasa.BodyA.Diffuse.1024')),
    ],
    'e0b0c6eb': [(log, ('1.4 -> 1.5: Harumasa BodyA Diffuse 1024p Hash',)), (update_hash, ('999ec526',))],
    '999ec526': [
        (log,                           ('1.4: Harumasa BodyA Diffuse 1024p Hash',)),
        (add_section_if_missing,        (('79679a10', '78bea30d'), 'Harumasa.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('49f8aaf6', 'ba52ac92'), 'Harumasa.BodyA.Diffuse.2048')),
    ],
    'cc51476a': [
        (log,                           ('1.4: Harumasa BodyA LightMap 2048p Hash',)),
        (add_section_if_missing,        (('79679a10', '78bea30d'), 'Harumasa.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('2b1230cf', 'Harumasa.BodyA.LightMap.1024')),
    ],
    '2b1230cf': [
        (log,                           ('1.4: Harumasa BodyA LightMap 1024p Hash',)),
        (add_section_if_missing,        (('79679a10', '78bea30d'), 'Harumasa.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('cc51476a', 'Harumasa.BodyA.LightMap.2048')),
    ],
    'cd1e0187': [(log, ('1.4 -> 1.5: Harumasa BodyA MaterialMap 2048p Hash',)), (update_hash, ('6d105f7e',))],
    '6d105f7e': [
        (log,                           ('1.4: Harumasa BodyA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        (('79679a10', '78bea30d'), 'Harumasa.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('c90264db', '2b0017d5'), 'Harumasa.BodyA.MaterialMap.1024')),
    ],
    '2b0017d5': [(log, ('1.4 -> 1.5: Harumasa BodyA MaterialMap 1024p Hash',)), (update_hash, ('c90264db',))],
    'c90264db': [
        (log,                           ('1.4: Harumasa BodyA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        (('79679a10', '78bea30d'), 'Harumasa.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('6d105f7e', 'cd1e0187'), 'Harumasa.BodyA.MaterialMap.2048')),
    ],

    # Legs腿部
    '44d74a1a': [
        (log,                           ('1.4: Harumasa LegsA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('aa7ba2dc', 'Harumasa.Legs.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('897c74d5', 'Harumasa.LegsA.Diffuse.1024')),
    ],
    '897c74d5': [
        (log,                           ('1.4: Harumasa LegsA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('aa7ba2dc', 'Harumasa.Legs.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('44d74a1a', 'Harumasa.LegsA.Diffuse.2048')),
    ],
    '4b4d0ff6': [
        (log,                           ('1.4: Harumasa LegsA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('aa7ba2dc', 'Harumasa.Legs.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('822ec07f', 'Harumasa.LegsA.LightMap.1024')),
    ],
    '822ec07f': [
        (log,                           ('1.4: Harumasa LegsA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('aa7ba2dc', 'Harumasa.Legs.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('4b4d0ff6', 'Harumasa.LegsA.LightMap.2048')),
    ],
    'ba8e396b': [(log, ('1.7 -> 2.0: Harumasa LegsA MaterialMap 2048p Hash',)), (update_hash, ('72885950',))],
    '72885950': [
        (log,                           ('1.4: Harumasa LegsA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        ('aa7ba2dc', 'Harumasa.Legs.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('b84027c8','bdbf66a1'), 'Harumasa.LegsA.MaterialMap.1024')),
    ],
    'bdbf66a1': [(log, ('1.7 -> 2.0: Harumasa LegsA MaterialMap 1024p Hash',)), (update_hash, ('b84027c8',))],
    'b84027c8': [
        (log,                           ('1.4: Harumasa LegsA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        ('aa7ba2dc', 'Harumasa.Legs.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('72885950','ba8e396b'), 'Harumasa.LegsA.MaterialMap.2048')),
    ],

    # MARK: Hugo雨果
    #IB
    '45ae7079': [(log, ('1.7: Hugo Hair IB Hash',)), (add_ib_check_if_missing,)],
    'b4765894': [(log, ('1.7: Hugo Body IB Hash',)), (add_ib_check_if_missing,)],
    'ed26c53d': [(log, ('1.7: Hugo Coat IB Hash',)), (add_ib_check_if_missing,)],
    '5db95af3': [(log, ('1.7: Hugo Badge IB Hash',)), (add_ib_check_if_missing,)],
    '66b936fc': [(log, ('1.7: Hugo Face IB Hash',)), (add_ib_check_if_missing,)],
    #VB

    #Texture纹理
    # Face脸部
    'a3064b0e': [
        (log,                           ('1.7: Hugo FaceA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('66b936fc', 'Hugo.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('0f344a22', 'Hugo.FaceA.Diffuse.1024')),
    ],
    '0f344a22': [
        (log,                           ('1.7: Hugo FaceA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('66b936fc', 'Hugo.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('a3064b0e', 'Hugo.FaceA.Diffuse.2048')),
    ],

    # Hair头发
    'f50ebb37': [
        (log,                           ('1.7: Hugo HairA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('bab642c6', 'Hugo.HairA.Diffuse.1024')),
    ],
    'bab642c6': [
        (log,                           ('1.7: Hugo HairA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('f50ebb37', 'Hugo.HairA.Diffuse.2048')),
    ],
    '94daa8f7': [
        (log,                           ('1.7: Hugo HairA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('dcf7c209', 'Hugo.HairA.LightMap.1024')),
    ],
    'dcf7c209': [
        (log,                           ('1.7: Hugo HairA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('94daa8f7', 'Hugo.HairA.LightMap.2048')),
    ],
    '9614f191': [
        (log,                           ('1.7: Hugo HairA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('144c15d0', 'Hugo.HairA.MaterialMap.1024')),
    ],
    '144c15d0': [
        (log,                           ('1.7: Hugo HairA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('9614f191', 'Hugo.HairA.MaterialMap.2048')),
    ],

    # Body身体
    '7fa5eb2e': [
        (log,                           ('1.7: Hugo BodyA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('b4765894', 'Hugo.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('2841b582', 'Hugo.BodyA.Diffuse.1024')),
    ],
    '2841b582': [
        (log,                           ('1.7: Hugo BodyA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('b4765894', 'Hugo.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('7fa5eb2e', 'Hugo.BodyA.Diffuse.2048')),
    ],
    'f9911f83': [
        (log,                           ('1.7: Hugo BodyA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('b4765894', 'Hugo.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('9fd99d99', 'Hugo.BodyA.LightMap.1024')),
    ],
    '9fd99d99': [
        (log,                           ('1.7: Hugo BodyA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('b4765894', 'Hugo.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('f9911f83', 'Hugo.BodyA.LightMap.2048')),
    ],
    'c6fa84c9': [
        (log,                           ('1.7: Hugo BodyA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        ('b4765894', 'Hugo.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('e2333ede', 'Hugo.BodyA.MaterialMap.1024')),
    ],
    'e2333ede': [
        (log,                           ('1.7: Hugo BodyA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        ('b4765894', 'Hugo.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('c6fa84c9', 'Hugo.BodyA.MaterialMap.2048')),
    ],

    # Coat
    '348bc40f': [
        (log,                           ('1.7: Hugo CoatA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('ed26c53d', 'Hugo.Coat.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('481e8fe0', 'Hugo.CoatA.Diffuse.1024')),
    ],
    '481e8fe0': [
        (log,                           ('1.7: Hugo CoatA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('ed26c53d', 'Hugo.Coat.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('348bc40f', 'Hugo.CoatA.Diffuse.2048')),
    ],
    '0db80414': [
        (log,                           ('1.7: Hugo CoatA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('ed26c53d', 'Hugo.Coat.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('a951a0cf', 'Hugo.CoatA.LightMap.1024')),
    ],
    'a951a0cf': [
        (log,                           ('1.7: Hugo CoatA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('ed26c53d', 'Hugo.Coat.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('0db80414', 'Hugo.CoatA.LightMap.2048')),
    ],
    '25b33389': [
        (log,                           ('1.7: Hugo CoatA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        ('ed26c53d', 'Hugo.Coat.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('ec648dcb', 'Hugo.CoatA.MaterialMap.1024')),
    ],
    'ec648dcb': [
        (log,                           ('1.7: Hugo CoatA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        ('ed26c53d', 'Hugo.Coat.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('25b33389', 'Hugo.CoatA.MaterialMap.2048')),
    ],

    # MARK: Jane Doe简
    #IB
    #2.5版本简的模型发生了较大变化，2.5版本之前的mod将无法通过简单的hash替换来适配2.5之后的版本，故取消更新
    '3275b812': [(log, ('3.0: Jane Hair IB Hash',)), (add_ib_check_if_missing,)],
    'ba4255a5': [(log, ('1.4: Jane Body IB Hash',)), (add_ib_check_if_missing,)],
    'ef86fc9f': [(log, ('1.1: Jane Face IB Hash',)), (add_ib_check_if_missing,)],
    #VB
    '5721e4e7': [(log, ('1.3 -> 1.4: Jane Hair Draw Hash',)),     (update_hash, ('2d06e785',)),],
    '24323bf9': [(log, ('1.3 -> 1.4: Jane Hair Position Hash',)), (update_hash, ('e7a3b7dc',)),],
    '0a10c747': [(log, ('1.3 -> 1.4: Jane Hair Blend Hash',)),    (update_hash, ('8721477f',)),],
    '257a90d6': [(log, ('1.3 -> 1.4: Jane Hair Texcoord Hash',)), (update_hash, ('acec29f8',)),],
    '7b16a708': [(log, ('1.3 -> 1.4: Jane Hair IB Hash',)),       (update_hash, ('9268a5af',)),],
    'd1aa4b85': [(log, ('1.3 -> 1.4: Jane Body Draw Hash',)),     (update_hash, ('0e1c6740',)),],
    '06f9bc49': [(log, ('1.3 -> 1.4: Jane Body Position Hash',)), (update_hash, ('10050266',)),],
    '9727a184': [(log, ('1.3 -> 1.4: Jane Body Blend Hash',)),    (update_hash, ('e27f398e',)),],
    '8b85c03e': [(log, ('1.3 -> 1.4: Jane Body Texcoord Hash',)), (update_hash, ('949549de',)),],
    'e2c0144e': [(log, ('1.3 -> 1.4: Jane Body IB Hash',)),       (update_hash, ('ba4255a5',)),],
    #不再提供对脸部vb的修复，不建议对脸部模型进行修改，可能会导致脸部贴图错位
    #'9f2f7c53': [(log, ('2.4 -> 2.5: Jane Face Texcoord Hash',)), (update_hash, ('1fa404c1',)),],
    #'1fa404c1': [(log, ('2.5 -> 3.1: Jane Face-脸 texcoord_vb Hash',)), (update_hash, ('3c32a411',))],
    #Remap
    'c8ad344e': [
        (log, ('1.1 -> 1.2: Jane Hair Texcoord Hash',)),
        (update_hash, ('257a90d6',)),
        (log, ('+ Remapping texcoord buffer',)),
        (zzz_12_shrink_texcoord_color, ('1.2',))
    ],

    #Texture纹理
    # Face脸部
    '8974fb74': [(log, ('1.3 -> 1.4: Jane FaceA Diffuse 2048p Hash',)), (update_hash, ('3b75aa2c',)),],
    '3b75aa2c': [
        (log,                           ('1.1: Jane FaceA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('ef86fc9f', 'Jane.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('d823ac80', '689639a5'), 'Jane.FaceA.Diffuse.1024')),
    ],
    '689639a5': [(log, ('1.3 -> 1.4: Jane FaceA Diffuse 1024p Hash',)), (update_hash, ('d823ac80',)),],
    'd823ac80': [
        (log,                           ('1.1: Jane FaceA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('ef86fc9f', 'Jane.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('3b75aa2c', '8974fb74'), 'Jane.FaceA.Diffuse.2048')),
    ],

    # Hair头发
    'f7ef1a53': [
        (log,                           ('1.1: Jane HairA Diffuse 2048p Hash',)),
        (add_section_if_missing,        (('9268a5af', '7b16a708'), 'Jane.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('b33a9770', 'Jane.HairA.Diffuse.1024')),
    ],
    'b33a9770': [
        (log,                           ('1.1: Jane HairA Diffuse 1024p Hash',)),
        (add_section_if_missing,        (('9268a5af', '7b16a708'), 'Jane.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('f7ef1a53', 'Jane.HairA.Diffuse.2048')),
    ],
    '9ec4cd4f': [
        (log,                           ('1.1: Jane HairA LightMap 2048p Hash',)),
        (add_section_if_missing,        (('9268a5af', '7b16a708'), 'Jane.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('5e12acc1', 'Jane.HairA.LightMap.1024')),
    ],
    '5e12acc1': [
        (log,                           ('1.1: Jane HairA LightMap 1024p Hash',)),
        (add_section_if_missing,        (('9268a5af', '7b16a708'), 'Jane.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('9ec4cd4f', 'Jane.HairA.LightMap.2048')),
    ],
    '5e34e275': [
        (log,                           ('1.1: Jane HairA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        (('9268a5af', '7b16a708'), 'Jane.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('40fca454', 'Jane.HairA.MaterialMap.1024')),
    ],
    '40fca454': [
        (log,                           ('1.1: Jane HairA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        (('9268a5af', '7b16a708'), 'Jane.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('5e34e275', 'Jane.HairA.MaterialMap.2048')),
    ],

    # Body身体
    'd1f56c7d': [
        (log,                           ('1.1: Jane BodyA Diffuse 2048p Hash',)),
        (add_section_if_missing,        (('ba4255a5', 'e2c0144e'), 'Jane.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('e62ae3b5', 'Jane.BodyA.Diffuse.1024')),
    ],
    'e62ae3b5': [
        (log,                           ('1.1: Jane BodyA Diffuse 1024p Hash',)),
        (add_section_if_missing,        (('ba4255a5', 'e2c0144e'), 'Jane.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('d1f56c7d', 'Jane.BodyA.Diffuse.2048')),
    ],
    '3087f82a': [
        (log,                           ('1.1: Jane BodyA LightMap 2048p Hash',)),
        (add_section_if_missing,        (('ba4255a5', 'e2c0144e'), 'Jane.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('52fa9861', 'Jane.BodyA.LightMap.1024')),
    ],
    '52fa9861': [
        (log,                           ('1.1: Jane BodyA LightMap 1024p Hash',)),
        (add_section_if_missing,        (('ba4255a5', 'e2c0144e'), 'Jane.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('3087f82a', 'Jane.BodyA.LightMap.2048')),
    ],
    '99eae42e': [
        (log,                           ('1.1: Jane BodyA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        (('ba4255a5', 'e2c0144e'), 'Jane.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('5dce2408', 'Jane.BodyA.MaterialMap.1024')),
    ],
    '5dce2408': [
        (log,                           ('1.1: Jane BodyA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        (('ba4255a5', 'e2c0144e'), 'Jane.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('99eae42e', 'Jane.BodyA.MaterialMap.2048')),
    ],

    # MARK: JaneDoeSkin简皮肤
    #IB
    'ac900322': [(log, ('2.5: JaneSkin Body IB Hash',)), (add_ib_check_if_missing,)],
    #VB
    #Texture纹理
    # Body身体
    'a47bf989': [
        (log,                           ('2.5: JaneSkin BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('be442045', 'JaneSkin.BodyA.Diffuse.1024')),
    ],
    'be442045': [
        (log,                           ('2.5: JaneSkin BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('a47bf989', 'JaneSkin.BodyA.Diffuse.2048')),
    ],
    'dd1b5520': [
        (log,                           ('2.5: JaneSkin BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('f655d62e', 'JaneSkin.BodyA.LightMap.1024')),
    ],
    'f655d62e': [
        (log,                           ('2.5: JaneSkin BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('dd1b5520', 'JaneSkin.BodyA.LightMap.2048')),
    ],
    '389d9c67': [
        (log,                           ('2.5: JaneSkin BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('13eafbbd', 'JaneSkin.BodyA.MaterialMap.1024')),
    ],
    '13eafbbd': [
        (log,                           ('2.5: JaneSkin BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('389d9c67', 'JaneSkin.BodyA.MaterialMap.2048')),
    ],

    # MARK: JuFufu橘福福
    #IB
    'a4fd9113': [(log, ('2.0: JuFufu Hair IB Hash',)), (add_ib_check_if_missing,)],
    'de303163': [(log, ('2.0: JuFufu Body IB Hash',)), (add_ib_check_if_missing,)],
    'f8ab3141': [(log, ('2.0: JuFufu Tail IB Hash',)), (add_ib_check_if_missing,)],
    '321768df': [(log, ('2.0: JuFufu Face IB Hash',)), (add_ib_check_if_missing,)],
    #VB

    #Texture纹理
    # Face脸部
    '37b277db': [
        (log,                           ('2.0: JuFufu FaceA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('321768df', 'JuFufu.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('134fbe43', 'JuFufu.FaceA.Diffuse.1024')),
    ],
    '134fbe43': [
        (log,                           ('2.0: JuFufu FaceA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('321768df', 'JuFufu.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('37b277db', 'JuFufu.FaceA.Diffuse.2048')),
    ],

    # Hair头发
    'db3bdffa': [
        (log,                           ('2.0: JuFufu HairA TailA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('521f60ae', 'JuFufu.HairA.Diffuse.1024')),
    ],
    '521f60ae': [
        (log,                           ('2.0: JuFufu HairA TailA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('db3bdffa', 'JuFufu.HairA.Diffuse.2048')),
    ],
    '5c948f7b': [
        (log,                           ('2.0: JuFufu HairA TailA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('29bb13b7', 'JuFufu.HairA.LightMap.1024')),
    ],
    '29bb13b7': [
        (log,                           ('2.0: JuFufu HairA TailA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('5c948f7b', 'JuFufu.HairA.LightMap.2048')),
    ],
    '9f4d4f72': [
        (log,                           ('2.0: JuFufu HairA TailA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('9355dcea', 'JuFufu.HairA.MaterialMap.1024')),
    ],
    '9355dcea': [
        (log,                           ('2.0: JuFufu HairA TailA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('9f4d4f72', 'JuFufu.HairA.MaterialMap.2048')),
    ],

    # Body身体
    '16e4cac1': [
        (log,                           ('2.0: JuFufu BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('3b372932', 'JuFufu.BodyA.Diffuse.1024')),
    ],
    '3b372932': [
        (log,                           ('2.0: JuFufu BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('16e4cac1', 'JuFufu.BodyA.Diffuse.2048')),
    ],
    'c952431f': [
        (log,                           ('2.0: JuFufu BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('9d1ab7c4', 'JuFufu.BodyA.LightMap.1024')),
    ],
    '9d1ab7c4': [
        (log,                           ('2.0: JuFufu BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('c952431f', 'JuFufu.BodyA.LightMap.2048')),
    ],
    'd555b4f8': [
        (log,                           ('2.0: JuFufu BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('f72af17c', 'JuFufu.BodyA.MaterialMap.1024')),
    ],
    'f72af17c': [
        (log,                           ('2.0: JuFufu BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('d555b4f8', 'JuFufu.BodyA.MaterialMap.2048')),
    ],

    # MARK: Koleda珂蕾妲
    #IB
    '242a8d48': [(log, ('1.0: Koleda Hair IB Hash',)), (add_ib_check_if_missing,)],
    '3afb3865': [(log, ('1.0: Koleda Body IB Hash',)), (add_ib_check_if_missing,)],
    '0e74656e': [(log, ('1.0: Koleda Face IB Hash',)), (add_ib_check_if_missing,)],
    #VB  
    #不再提供对脸部vb的修复，不建议对脸部模型进行修改，可能会导致脸部贴图错位
    #'a5539a26': [(log, ('1.2 -> 1.3: Koleda Face Texcoord Hash',)), (update_hash, ('f41b27e6',))],
    #'f41b27e6': [(log, ('3.1 -> 3.2: Koleda Face-脸 texcoord_vb Hash',)), (update_hash, ('57994826',))],
    #Remap
    '1a9b182a': [
        (log,            ('1.2 -> 1.3: Koleda Hair Texcoord Hash',)),
        (update_hash,    ('e35571a9',)),
        (log,            ('+ Remapping texcoord buffer',)),
        (zzz_13_remap_texcoord, (
            '13_koleda_hair',
            ('4B','2e','2f','2e'),
            ('4B','2f','2f','2f')
        )),
    ],
    'e3021a32': [
        (log,            ('1.2 -> 1.3: Koleda Body Texcoord Hash',)),
        (update_hash,    ('38b31082',)),
        (log,            ('+ Remapping texcoord buffer',)),
        (zzz_13_remap_texcoord, (
            '13_koleda_body',
            ('4B','2e','2f','2e'),
            ('4B','2f','2f','2f')
        )),
    ],

    #Texture纹理
    # Face脸部
    '200db5c4': [
        (log,                           ('1.0: Koleda FaceA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('0e74656e', 'Koleda.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('f1045670', 'Koleda.FaceA.Diffuse.1024')),
    ],
    'f1045670': [
        (log,                           ('1.0: Koleda FaceA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('0e74656e', 'Koleda.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('200db5c4', 'Koleda.FaceA.Diffuse.2048')),
    ],

    # Hair头发
    'e8e89f00': [
        (log,                           ('1.0: Koleda HairA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('242a8d48', 'Koleda.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('b0046e5a', 'Koleda.HairA.Diffuse.1024')),
    ],
    'b0046e5a': [
        (log,                           ('1.0: Koleda HairA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('242a8d48', 'Koleda.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('e8e89f00', 'Koleda.HairA.Diffuse.2048')),
    ],
    '8042506d': [(log, ('1.7 -> 2.0: Koleda HairA LightMap 2048p Hash',)), (update_hash, ('a451ca03',))],
    'a451ca03': [
        (log,                           ('1.0: Koleda HairA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('242a8d48', 'Koleda.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('1b33709a','144ab293'), 'Koleda.HairA.LightMap.1024')),
    ],
    '144ab293': [(log, ('1.7 -> 2.0: Koleda HairA LightMap 1024p Hash',)), (update_hash, ('1b33709a',))],
    '1b33709a': [
        (log,                           ('1.0: Koleda HairA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('242a8d48', 'Koleda.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('a451ca03','8042506d'), 'Koleda.HairA.LightMap.2048')),
    ],

    # Body身体
    '337fd6a2': [
        (log,                           ('1.0: Koleda BodyA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('3afb3865', 'Koleda.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('ce10237d', 'Koleda.BodyA.Diffuse.1024')),
    ],
    'ce10237d': [
        (log,                           ('1.0: Koleda BodyA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('3afb3865', 'Koleda.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('337fd6a2', 'Koleda.BodyA.Diffuse.2048')),
    ],
    '78e0f9f5': [(log, ('1.7 -> 2.0: Koleda BodyA LightMap 2048p Hash',)), (update_hash, ('7c1bce32',))],
    '7c1bce32': [
        (log,                           ('1.0: Koleda BodyA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('3afb3865', 'Koleda.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('a1087d61','db58787e'), 'Koleda.BodyA.LightMap.1024')),
    ],
    'db58787e': [(log, ('1.7 -> 2.0: Koleda BodyA LightMap 1024p Hash',)), (update_hash, ('a1087d61',))],
    'a1087d61': [
        (log,                           ('1.0: Koleda BodyA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('3afb3865', 'Koleda.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('7c1bce32','78e0f9f5'), 'Koleda.BodyA.LightMap.2048')),
    ],
    '6f34885f': [(log, ('1.7 -> 2.0: Koleda BodyA MaterialMap 2048p Hash',)), (update_hash, ('b60ace0c',))],
    'b60ace0c': [
        (log,                           ('1.0: Koleda BodyA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        ('3afb3865', 'Koleda.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('1c162e9c','02e6cb95'), 'Koleda.BodyA.MaterialMap.1024')),
    ],
    '02e6cb95': [(log, ('1.7 -> 2.0: Koleda BodyA MaterialMap 1024p Hash',)), (update_hash, ('1c162e9c',))],
    '1c162e9c': [
        (log,                           ('1.0: Koleda BodyA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        ('3afb3865', 'Koleda.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('b60ace0c','6f34885f'), 'Koleda.BodyA.MaterialMap.2048')),
    ],

    # MARK: Lighter莱特
    #IB
    '542b8aa9': [(log, ('1.3: Lighter Hair IB Hash',)),    (add_ib_check_if_missing,)],
    '8899e0fd': [(log, ('1.3: Lighter Body IB Hash',)),    (add_ib_check_if_missing,)],
    '018b03f0': [(log, ('1.3: Lighter Arm IB Hash',)),     (add_ib_check_if_missing,)],
    'dcc7bb78': [(log, ('1.4: Lighter Face IB Hash',)),        (add_ib_check_if_missing,)],
    #VB

    '039f30cf': [(log, ('1.3 -> 1.4: Lighter Face IB Hash',)), (update_hash, ('dcc7bb78',))],
    #不再提供对脸部vb的修复，不建议对脸部模型进行修改，可能会导致脸部贴图错位
    #'7bbe9c75': [(log, ('1.6 -> 2.0: Lighter Face Position Hash',)),  (update_hash, ('90653c42',))],
    #'af14829b': [(log, ('1.3 -> 3.1: Lighter Face-脸 texcoord_vb Hash',)), (update_hash, ('04cc2dfd',))],

    '0baec6b7': [(log, ('1.3 -> 1.4: Lighter Body Position Hash',)), (update_hash, ('5e461440',))],
    '5e461440': [(log, ('1.4 -> 1.6: Lighter Body Position Hash',)),  (update_hash, ('f6bbabb5',))],
    '710bca71': [(log, ('1.3 -> 1.4: Lighter Body Texcoord Hash',)), (update_hash, ('25ad7289',))],
    '25ad7289': [(log, ('1.4 -> 1.6: Lighter Body Texcoord Hash',)),  (update_hash, ('e1ae7f38',))],

    'af2e48a6': [(log, ('1.3 -> 1.4: Lighter Arm Texcoord Hash',)),  (update_hash, ('88aecee2',))],

    #Texture纹理
    # Face脸部
    '8ec33dd0': [
        (log,                           ('1.3: Lighter FaceA Diffuse 1024p Hash',)),
        (add_section_if_missing,        (('dcc7bb78', '039f30cf'), 'Lighter.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('4524e91a', 'Lighter.FaceA.Diffuse.2048')),
    ],
    '4524e91a': [
        (log,                           ('1.3: Lighter FaceA Diffuse 2048p Hash',)),
        (add_section_if_missing,        (('dcc7bb78', '039f30cf'), 'Lighter.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('8ec33dd0', 'Lighter.FaceA.Diffuse.1024')),
    ],

    # Hair头发
    'c5d60a1d': [(log,('2.7: -> 2.8: Lighter HairA Diffuse 2048p Hash',)),(update_hash,('4e088042',)),],
    '4e088042': [
        (log,                           ('1.3: Lighter HairA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('542b8aa9', 'Lighter.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('1cd2d442', '0ee07935'), 'Lighter.HairA.Diffuse.1024')),
    ],
    '1cd2d442': [(log,('2.7: -> 2.8: Lighter HairA Diffuse 1024p Hash',)),(update_hash,('0ee07935',)),],
    '0ee07935': [
        (log,                           ('1.3: Lighter HairA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('542b8aa9', 'Lighter.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('c5d60a1d', '4e088042'), 'Lighter.HairA.Diffuse.2048')),
    ],
    '6d3f91bc': [
        (log,                           ('1.3: Lighter HairA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('542b8aa9', 'Lighter.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('62ec7f01', 'Lighter.HairA.LightMap.1024')),
    ],
    '62ec7f01': [
        (log,                           ('1.3: Lighter HairA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('542b8aa9', 'Lighter.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('6d3f91bc', 'Lighter.HairA.LightMap.2048')),
    ],
    'd5ba9ea6': [(log,('2.7: -> 2.8: Lighter HairA MaterialMap 2048p Hash',)),(update_hash,('d331b850',)),],
    'd331b850': [
        (log,                           ('1.3: Lighter HairA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        ('542b8aa9', 'Lighter.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('8687f7b8', '99ad14f1'), 'Lighter.HairA.MaterialMap.1024')),
    ],
    '8687f7b8': [(log,('2.7: -> 2.8: Lighter HairA MaterialMap 1024p Hash',)),(update_hash,('99ad14f1',)),],
    '99ad14f1': [
        (log,                           ('1.3: Lighter HairA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        ('542b8aa9', 'Lighter.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('d5ba9ea6', 'd331b850'), 'Lighter.HairA.MaterialMap.2048')),
    ],

    # Body身体
    '5ed96bf2': [
        (log,                           ('1.3: Lighter BodyA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('8899e0fd', 'Lighter.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('be46890b', 'Lighter.BodyA.Diffuse.1024')),
    ],
    'be46890b': [
        (log,                           ('1.3: Lighter BodyA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('8899e0fd', 'Lighter.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('5ed96bf2', 'Lighter.BodyA.Diffuse.2048')),
    ],
    'da6f4dc0': [
        (log,                           ('1.3: Lighter BodyA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('8899e0fd', 'Lighter.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('5b828635', 'Lighter.BodyA.LightMap.1024')),
    ],
    '5b828635': [
        (log,                           ('1.3: Lighter BodyA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('8899e0fd', 'Lighter.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('da6f4dc0', 'Lighter.BodyA.LightMap.2048')),
    ],
    '94aebd7e': [
        (log,                           ('1.3: Lighter BodyA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        ('8899e0fd', 'Lighter.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('65f3bb7c', 'Lighter.BodyA.MaterialMap.1024')),
    ],
    '65f3bb7c': [
        (log,                           ('1.3: Lighter BodyA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        ('8899e0fd', 'Lighter.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('94aebd7e', 'Lighter.BodyA.MaterialMap.2048')),
    ],

    # ArmA手臂
    '8b854866': [
        (log,                           ('1.3: Lighter ArmA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('018b03f0', 'Lighter.Arm.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('6506987b', 'Lighter.ArmA.Diffuse.1024')),
    ],
    '6506987b': [
        (log,                           ('1.3: Lighter ArmA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('018b03f0', 'Lighter.Arm.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('8b854866', 'Lighter.ArmA.Diffuse.2048')),
    ],
    '547cbcd8': [
        (log,                           ('1.3: Lighter ArmA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('018b03f0', 'Lighter.Arm.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('939a2e18', 'Lighter.ArmA.LightMap.1024')),
    ],
    '939a2e18': [
        (log,                           ('1.3: Lighter ArmA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('018b03f0', 'Lighter.Arm.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('547cbcd8', 'Lighter.ArmA.LightMap.2048')),
    ],
    '3617c303': [
        (log,                           ('1.3: Lighter ArmA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        ('018b03f0', 'Lighter.Arm.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('1684d3e4', 'Lighter.ArmA.MaterialMap.1024')),
    ],
    '1684d3e4': [
        (log,                           ('1.3: Lighter ArmA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        ('018b03f0', 'Lighter.Arm.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('3617c303', 'Lighter.ArmA.MaterialMap.2048')),
    ],

    # MARK: Lucia 卢西娅
    #IB
    '340fc999': [(log, ('2.3: Lucia Hair IB Hash',)),         (add_ib_check_if_missing,)],
    'd39c304d': [(log, ('2.3: Lucia Body IB Hash',)),         (add_ib_check_if_missing,)],
    '6986f28e': [(log, ('2.3: Lucia Face IB Hash',)),         (add_ib_check_if_missing,)],
    #VB

    #Texture纹理
    # Face脸部
    '20a6224d': [
        (log,                           ('2.3: Lucia FaceA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('6986f28e', 'Lucia.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('12ec6e26', 'Lucia.FaceA.Diffuse.1024')),
    ],
    '12ec6e26': [
        (log,                           ('2.3: Lucia FaceA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('6986f28e', 'Lucia.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('20a6224d', 'Lucia.FaceA.Diffuse.2048')),
    ],

    # Hair头发
    '5b0b47c9': [
        (log,                           ('2.3: Lucia HairA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('ab461f68', 'Lucia.HairA.Diffuse.1024')),
    ],
    'ab461f68': [
        (log,                           ('2.3: Lucia HairA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('5b0b47c9', 'Lucia.HairA.Diffuse.2048')),
    ],
    '243feee8': [
        (log,                           ('2.3: Lucia HairA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('dda3939e', 'Lucia.HairA.LightMap.1024')),
    ],
    'dda3939e': [
        (log,                           ('2.3: Lucia HairA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('243feee8', 'Lucia.HairA.LightMap.2048')),
    ],
    '211a5700': [
        (log,                           ('2.3: Lucia HairA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('c09e5350', 'Lucia.HairA.MaterialMap.1024')),
    ],
    'c09e5350': [
        (log,                           ('2.3: Lucia HairA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('211a5700', 'Lucia.HairA.MaterialMap.2048')),
    ],

    # Body身体
    '2ca45943': [
        (log,                           ('2.3: Lucia BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('614c9ad5', 'Lucia.BodyA.Diffuse.1024')),
    ],
    '614c9ad5': [
        (log,                           ('2.3: Lucia BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('2ca45943', 'Lucia.BodyA.Diffuse.2048')),
    ],
    'f117c868': [
        (log,                           ('2.3: Lucia BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('30b94be9', 'Lucia.BodyA.LightMap.1024')),
    ],
    '30b94be9': [
        (log,                           ('2.3: Lucia BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('f117c868', 'Lucia.BodyA.LightMap.2048')),
    ],
    'a16861d2': [
        (log,                           ('2.3: Lucia BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('c0fe7e43', 'Lucia.BodyA.MaterialMap.1024')),
    ],
    'c0fe7e43': [
        (log,                           ('2.3: Lucia BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('a16861d2', 'Lucia.BodyA.MaterialMap.2048')),
    ],

    # MARK: Lucy露西
    #IB
    '69ad9d08': [(log, ('1.3: Lucy Hair IB Hash',)),     (add_ib_check_if_missing,)],
    '272dd7f6': [(log, ('1.0: Lucy Snout IB Hash',)),    (add_ib_check_if_missing,)],
    '9b6370f6': [(log, ('1.0: Lucy Belt IB Hash',)),     (add_ib_check_if_missing,)],
    'be5f4c7d': [(log, ('1.3: Lucy Body IB Hash',)),     (add_ib_check_if_missing,)],
    '1fe6e084': [(log, ('1.0: Lucy RedCloth IB Hash',)), (add_ib_check_if_missing,)],
    'a0ed04de': [(log, ('1.0: Lucy Helmet IB Hash',)),   (add_ib_check_if_missing,)],
    'df3e3965': [(log, ('1.3: Lucy Face IB Hash',)),     (add_ib_check_if_missing,)],
    #VB

    '9b4dfd86': [(log, ('1.3 -> 2.0: Lucy HairWallpaper Position Hash',)), (update_hash, ('39cfd24c',))],
    '5315f036': [(log, ('1.2 -> 1.3: Lucy Hair Blend Hash',)),             (update_hash, ('a37c7537',))],
    '751e21a5': [(log, ('1.2 -> 1.3: Lucy Hair Texcoord Hash',)),          (update_hash, ('c8810832',))],
    '198e99d7': [
        (log, ('1.2 -> 1.3: Lucy Hair IB Hash',)),
        (update_hash, ('69ad9d08',)),
        (transfer_indexed_sections, {
            'src_indices': ['0', '-1'],
            'trg_indices': ['0', '5253'],
        })
    ],

    '5da9dafc': [(log, ('1.2 -> 1.3: Lucy Body Position Hash',)), (update_hash, ('246b93e2',))],
    'b94b02e8': [(log, ('1.2 -> 1.3: Lucy Body Blend Hash',)),    (update_hash, ('66948a0f',))],
    '00f11ea6': [(log, ('1.2 -> 1.3: Lucy Body Texcoord Hash',)), (update_hash, ('f60dbb9e',))],
    'e0ad50ed': [(log, ('1.2 -> 1.3: Lucy Body IB Hash',)),       (update_hash, ('be5f4c7d',))],

    'fca15ccb': [(log, ('1.2 -> 1.3: Lucy Face IB Hash',)),       (update_hash, ('df3e3965',))],

    #不再提供对脸部vb的修复，不建议对脸部模型进行修改，可能会导致脸部贴图错位
    #'6275f052': [(log, ('1.2 -> 1.3: Lucy Face Texcoord Hash',)), (update_hash, ('1ca0ae1a',))],
    #'1ca0ae1a': [(log, ('1.3 -> 3.1: Lucy Face-脸 texcoord_vb Hash',)), (update_hash, ('e78a4ee2',))],
    #'80efa5cb': [(log, ('1.2 -> 1.3: Lucy Face Blend Hash',)),    (update_hash, ('a2054778',))],

    #Texture纹理
    # Face脸部
    '2a6df536': [(log, ('1.2 -> 1.3: Lucy FaceA Diffuse 2048p Hash',)), (update_hash, ('4e2d5baa',))],
    '4e2d5baa': [
        (log,                           ('1.3: Lucy FaceA Diffuse 2048p Hash',)),
        (add_section_if_missing,        (('df3e3965', 'fca15ccb'), 'Lucy.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('2578d35b', '483b418a'), 'Lucy.FaceA.Diffuse.1024')),
    ],
    '483b418a': [(log, ('1.2 -> 1.3: Lucy FaceA Diffuse 1024p Hash',)), (update_hash, ('2578d35b',))],
    '2578d35b': [
        (log,                           ('1.3: Lucy FaceA Diffuse 1024p Hash',)),
        (add_section_if_missing,        (('df3e3965', 'fca15ccb'), 'Lucy.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('4e2d5baa', '2a6df536'), 'Lucy.FaceA.Diffuse.2048')),
    ],

    # Hair头发
    'aa513afa': [(log, ('1.2 -> 1.3: Lucy HairA, SnoutA, BeltA Diffuse 2048p Hash',)),     (update_hash, ('0fa60fe1',))],
    '0fa60fe1': [
        (log,                           ('1.3: Lucy HairA, SnoutA, BeltA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   (('753baa45', 'b50eb71c'), 'Lucy.HairA.Diffuse.1024')),
    ],
    'b50eb71c': [(log, ('1.2 -> 1.3: Lucy HairA, SnoutA, BeltA Diffuse 1024p Hash',)),     (update_hash, ('753baa45',))],
    '753baa45': [
        (log,                           ('1.3: Lucy HairA, SnoutA, BeltA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   (('0fa60fe1', 'aa513afa'), 'Lucy.HairA.Diffuse.2048')),
    ],
    '1a3b30ba': [
        (log,                           ('1.0: Lucy HairA, SnoutA, BeltA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('810c0878', 'Lucy.HairA.LightMap.1024')),
    ],
    '810c0878': [
        (log,                           ('1.0: Lucy HairA, SnoutA, BeltA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('1a3b30ba', 'Lucy.HairA.LightMap.2048')),
    ],
    '919b608c': [(log, ('1.2 -> 1.3: Lucy HairA, SnoutA, BeltA MaterialMap 2048p Hash',)), (update_hash, ('068aba7f',))],
    '068aba7f': [
        (log,                           ('1.3: Lucy HairA, SnoutA, BeltA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   (('368f931c', 'd1241cfc'), 'Lucy.HairA.MaterialMap.1024')),
    ],
    'd1241cfc': [(log, ('1.2 -> 1.3: Lucy HairA, SnoutA, BeltA MaterialMap 1024p Hash',)), (update_hash, ('368f931c',))],
    '368f931c': [
        (log,                           ('1.3: Lucy HairA, SnoutA, BeltA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   (('068aba7f', '919b608c'), 'Lucy.HairA.MaterialMap.2048')),
    ],

    # Body身体
    '474c7aa2': [
        (log,                           ('1.0: Lucy BodyA, RedClothA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('f810e7ac', 'Lucy.BodyA.Diffuse.1024')),
    ],
    'f810e7ac': [
        (log,                           ('1.0: Lucy BodyA, RedClothA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('474c7aa2', 'Lucy.BodyA.Diffuse.2048')),
    ],
    '855d9fa3': [
        (log,                           ('1.0: Lucy BodyA, RedClothA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('e89f7814', 'Lucy.BodyA.LightMap.1024')),
    ],
    'e89f7814': [
        (log,                           ('1.0: Lucy BodyA, RedClothA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('855d9fa3', 'Lucy.BodyA.LightMap.2048')),
    ],
    '1fd24fd8': [
        (log,                           ('1.0: Lucy BodyA, RedClothA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('86ca6cfd', 'Lucy.BodyA.MaterialMap.1024')),
    ],
    '86ca6cfd': [
        (log,                           ('1.0: Lucy BodyA, RedClothA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('1fd24fd8', 'Lucy.BodyA.MaterialMap.2048')),
    ],

    # Helmet头盔
    'a0be0ed3': [
        (log,                           ('1.0: Lucy HelmetA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('a0ed04de', 'Lucy.Helmet.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('919ab7e5', 'Lucy.HelmetA.Diffuse.1024')),
    ],
    '919ab7e5': [
        (log,                           ('1.0: Lucy HelmetA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('a0ed04de', 'Lucy.Helmet.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('a0be0ed3', 'Lucy.HelmetA.Diffuse.2048')),
    ],
    '8d9a16c7': [
        (log,                           ('1.0: Lucy HelmetA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('a0ed04de', 'Lucy.Helmet.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('6a8fca92', 'Lucy.HelmetA.LightMap.1024')),
    ],
    '6a8fca92': [
        (log,                           ('1.0: Lucy HelmetA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('a0ed04de', 'Lucy.Helmet.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('8d9a16c7', 'Lucy.HelmetA.LightMap.2048')),
    ],
    'b3013a33': [(log, ('1.7 -> 2.0: Lucy HelmetA MaterialMap 2048p Hash',)), (update_hash, ('0a99d9d5',))],
    '0a99d9d5': [
        (log,                           ('1.0: Lucy HelmetA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        ('a0ed04de', 'Lucy.Helmet.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('2243086f','4227db77'), 'Lucy.HelmetA.MaterialMap.1024')),
    ],
    '4227db77': [(log, ('1.7 -> 2.0: Lucy HelmetA MaterialMap 1024p Hash',)), (update_hash, ('2243086f',))],
    '2243086f': [
        (log,                           ('1.0: Lucy HelmetA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        ('a0ed04de', 'Lucy.Helmet.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('0a99d9d5','b3013a33'), 'Lucy.HelmetA.MaterialMap.2048')),
    ],

    # MARK: LucySkin露西皮肤
    '30abbad1': [(log, ('3.1: LucySkin Body IB Hash',)), (add_ib_check_if_missing,)],
    'ba402095': [(log, ('3.1: LucySkin Hair IB Hash',)), (add_ib_check_if_missing,)],
    '7cec7c94': [(log, ('3.1: LucySkin Hat IB Hash',)), (add_ib_check_if_missing,)],
    
    # Body
    '2cac44c0': [
        (log,                           ('3.1: LucySkin BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('4901de52', 'LucySkin.BodyA.Diffuse.1024')),
    ],
    '4901de52': [
        (log,                           ('3.1: LucySkin BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('2cac44c0', 'LucySkin.BodyA.Diffuse.2048')),
    ],
    '8d155fc7': [
        (log,                           ('3.1: LucySkin BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('ca69aa34', 'LucySkin.BodyA.LightMap.1024')),
    ],
    'ca69aa34': [
        (log,                           ('3.1: LucySkin BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('8d155fc7', 'LucySkin.BodyA.LightMap.2048')),
    ],
    'e96ce933': [
        (log,                           ('3.1: LucySkin BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('fdf85374', 'LucySkin.BodyA.MaterialMap.1024')),
    ],
    'fdf85374': [
        (log,                           ('3.1: LucySkin BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('e96ce933', 'LucySkin.BodyA.MaterialMap.2048')),
    ],

        

    # MARK: Lycaon莱卡恩
    #IB
    '060bc1ad': [(log, ('1.0: Lycaon Hair IB Hash',)),              (add_ib_check_if_missing,)],    
    '6749b6e7': [(log, ('1.4: Lycaon Body IB Hash',)),        (add_ib_check_if_missing,)],    
    '5e710f36': [(log, ('1.0: Lycaon Mask IB Hash',)), (add_ib_check_if_missing,)],
    '22a1347b': [(log, ('1.0: Lycaon Legs IB Hash',)), (add_ib_check_if_missing,)],
    '6ffdfccb': [(log, ('1.6: Lycaon Face IB Hash',)), (add_ib_check_if_missing,)],
    #VB
    '395572dc': [(log, ('1.3 -> 1.4: Lycaon Hair Texcoord Hash',)), (update_hash, ('b092c043',))],
    '25196b7a': [(log, ('1.3 -> 1.4: Lycaon Body IB Hash',)), (update_hash, ('6749b6e7',))],
    '2a340ed5': [(log, ('1.3 -> 1.4: Lycaon Body Draw Hash',)),     (update_hash, ('25418598',))],
    '949e688a': [(log, ('1.3 -> 1.4: Lycaon Body Texcoord Hash',)), (update_hash, ('b950fda5',))],

    #不再提供对脸部vb的修复，不建议对脸部模型进行修改，可能会导致脸部贴图错位
    #'7074f97e': [(log, ('1.5 -> 1.6: Lycaon Face Draw Hash',)),     (update_hash, ('44277f65',))],
    #'4a666a39': [(log, ('1.5 -> 1.6: Lycaon Face Position Hash',)), (update_hash, ('7e35ec22',))],
    #'c862a611': [(log, ('1.5 -> 1.6: Lycaon Face Blend Hash',)),    (update_hash, ('e2d4c532',))],
    #'6902f441': [(log, ('1.? -> 1.?: Lycaon Face Texcoord Hash',)), (update_hash, ('b1edaf35',))],
    #'b1edaf35': [(log, ('1.? -> 1.6: Lycaon Face Texcoord Hash',)), (update_hash, ('3adaebb3',))],
    '7341e07b': [(log, ('1.5 -> 1.6: Lycaon Face IB Hash',)),       (update_hash, ('6ffdfccb',))],

    #Remap
    'b68056b4': [
        (log, ('1.3 -> 1.4: Lycaon Body Position Hash',)),
        (update_hash, ('8c7775ae',)),
        (log, ('1.3 -> 1.4: Lycaon Body Blend Remap',)),
        (update_buffer_blend_indices, (
            '8c7775ae',
            (50, 51, 89, 90,  98,  99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110),
            (51, 50, 90, 89, 669, 669, 669, 669, 669, 669, 669, 669, 669,  98,  99, 100, 101)
        ))
    ],
    'a485180e': [
        (log,                         ('1.3 -> 1.4: Lycaon Body Blend Remap',)),
        (update_hash,                 ('f2d1a929',)),
        (update_buffer_blend_indices, (
            'f2d1a929',
            (50, 51, 89, 90,  98,  99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110),
            (51, 50, 90, 89, 669, 669, 669, 669, 669, 669, 669, 669, 669,  98,  99, 100, 101)
        )),
    ],

    #Texture纹理
    # Face脸部
    'd14f3284': [(log, ('1.5 -> 1.6: Lycaon FaceA Diffuse 2048p Hash',)), (update_hash, ('7077ebb1',))],
    '7077ebb1': [
        (log,                           ('1.6: Lycaon FaceA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   (('2cc208a7', '4f098897'), 'Lycaon.FaceA.Diffuse.1024')),
    ],
    '4f098897': [(log, ('1.5 -> 1.6: Lycaon FaceA Diffuse 1024p Hash',)), (update_hash, ('2cc208a7',))],
    '2cc208a7': [
        (log,                           ('1.6: Lycaon FaceA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   (('7077ebb1', 'd14f3284'), 'Lycaon.FaceA.Diffuse.2048')),
    ],

    # Hair头发
    '61aaace5': [
        (log,                           ('1.0: Lycaon HairA, MaskA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('3bd1b7e6', 'Lycaon.HairA.Diffuse.1024')),
    ],
    '3bd1b7e6': [
        (log,                           ('1.0: Lycaon HairA, MaskA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('61aaace5', 'Lycaon.HairA.Diffuse.2048')),
    ],
    '04d061fe': [(log, ('1.7 -> 2.0: Lycaon HairA, MaskA LightMap 2048p Hash',)), (update_hash, ('f7daa6d9',))],
    '3d6eb388': [(log, ('1.3 -> 1.4: Lycaon HairA, MaskA LightMap 2048p Hash',)), (update_hash, ('04d061fe',))],
    'f7daa6d9': [
        (log,                           ('1.4: Lycaon HairA, MaskA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   (('4d878953', '4d4e8986','7c129f48'), 'Lycaon.HairA.LightMap.1024')),
    ],
    '4d878953': [(log, ('1.7 -> 2.0: Lycaon HairA, MaskA LightMap 1024p Hash',)), (update_hash, ('7c129f48',))],
    '4d4e8986': [(log, ('1.3 -> 1.4: Lycaon HairA, MaskA LightMap 1024p Hash',)), (update_hash, ('4d878953',))],
    '7c129f48': [
        (log,                           ('1.4: Lycaon HairA, MaskA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   (('04d061fe', '3d6eb388','f7daa6d9'), 'Lycaon.HairA.LightMap.2048')),
    ],
    '02bfcc69': [
        (log,                           ('1.0: Lycaon HairA, MaskA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('ba0f8320', 'Lycaon.HairA.MaterialMap.1024')),
    ],
    'ba0f8320': [
        (log,                           ('1.0: Lycaon HairA, MaskA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('02bfcc69', 'Lycaon.HairA.MaterialMap.2048')),
    ],

    # Body身体
    '7169ec86': [(log, ('2.4 -> 2.5: Lycaon BodyA Diffuse 2048p Hash',)), (update_hash, ('4cb6928e',))],
    '4cb6928e': [
        (log,                           ('1.0: Lycaon BodyA Diffuse 2048p Hash',)),
        (add_section_if_missing,        (('6749b6e7', '25196b7a'), 'Lycaon.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('82ad0c28', '7a22ad61'), 'Lycaon.BodyA.Diffuse.1024')),
    ],
    '82ad0c28': [(log, ('2.4 -> 2.5: Lycaon BodyA Diffuse 1024p Hash',)), (update_hash, ('7a22ad61',))],
    '7a22ad61': [
        (log,                           ('1.0: Lycaon BodyA Diffuse 1024p Hash',)),
        (add_section_if_missing,        (('6749b6e7', '25196b7a'), 'Lycaon.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('4cb6928e', '7169ec86'), 'Lycaon.BodyA.Diffuse.2048')),
    ],
    '814db5bf': [(log, ('1.7 -> 2.0: Lycaon BodyA LightMap 2048p Hash',)), (update_hash, ('fbf5a9b5',))],
    '565aa8be': [(log, ('1.3 -> 1.4: Lycaon BodyA LightMap 2048p Hash',)), (update_hash, ('814db5bf',))],
    'fbf5a9b5': [
        (log,                           ('1.0: Lycaon BodyA LightMap 2048p Hash',)),
        (add_section_if_missing,        (('6749b6e7', '25196b7a'), 'Lycaon.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('122c655e', '7ea75154','391855b7'), 'Lycaon.BodyA.LightMap.1024')),
    ],
    '122c655e': [(log, ('1.7 -> 2.0: Lycaon BodyA LightMap 1024p Hash',)), (update_hash, ('391855b7',))],
    '7ea75154': [(log, ('1.3 -> 1.4: Lycaon BodyA LightMap 1024p Hash',)), (update_hash, ('122c655e',))],
    '391855b7': [
        (log,                           ('1.0: Lycaon BodyA LightMap 1024p Hash',)),
        (add_section_if_missing,        (('6749b6e7', '25196b7a'), 'Lycaon.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('814db5bf', '565aa8be','fbf5a9b5'), 'Lycaon.BodyA.LightMap.2048')),
    ],
    '5a321eae': [
        (log,                           ('1.0: Lycaon BodyA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        (('6749b6e7', '25196b7a'), 'Lycaon.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('7cca7d7e', 'Lycaon.BodyA.MaterialMap.1024')),
    ],
    '7cca7d7e': [
        (log,                           ('1.0: Lycaon BodyA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        (('6749b6e7', '25196b7a'), 'Lycaon.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('5a321eae', 'Lycaon.BodyA.MaterialMap.2048')),
    ],

    # Legs腿部
    'd947066b': [
        (log,                           ('1.0: Lycaon LegsA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('22a1347b', 'Lycaon.Legs.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('89bd4d58', 'Lycaon.LegsA.Diffuse.1024')),
    ],
    '89bd4d58': [
        (log,                           ('1.0: Lycaon LegsA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('22a1347b', 'Lycaon.Legs.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('d947066b', 'Lycaon.LegsA.Diffuse.2048')),
    ],
    '072e6786': [(log, ('1.7 -> 2.0: Lycaon LegsA LightMap 2048p Hash',)), (update_hash, ('57b175c5',))],
    '57b175c5': [
        (log,                           ('1.0: Lycaon LegsA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('22a1347b', 'Lycaon.Legs.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('9bcd5f77','3dfdab95'), 'Lycaon.LegsA.LightMap.1024')),
    ],
    '3dfdab95': [(log, ('1.7 -> 2.0: Lycaon LegsA LightMap 1024p Hash',)), (update_hash, ('9bcd5f77',))],
    '9bcd5f77': [
        (log,                           ('1.0: Lycaon LegsA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('22a1347b', 'Lycaon.Legs.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('57b175c5','072e6786'), 'Lycaon.LegsA.LightMap.2048')),
    ],
    '4a4ea6dc': [(log, ('1.7 -> 2.0: Lycaon LegsA MaterialMap 2048p Hash',)), (update_hash, ('4b18f890',))],
    '4b18f890': [
        (log,                           ('1.0: Lycaon LegsA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        ('22a1347b', 'Lycaon.Legs.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('b4e95c1d','288e7fbd'), 'Lycaon.LegsA.MaterialMap.1024')),
    ],
    '288e7fbd': [(log, ('1.7 -> 2.0: Lycaon LegsA MaterialMap 1024p Hash',)), (update_hash, ('b4e95c1d',))],
    'b4e95c1d': [
        (log,                           ('1.0: Lycaon LegsA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        ('22a1347b', 'Lycaon.Legs.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('4b18f890','4a4ea6dc'), 'Lycaon.LegsA.MaterialMap.2048')),
    ],

    # MARK: Manato 狛野真斗
    #IB
    'de57398c': [(log, ('2.3: Manato Hair IB Hash',)),   (add_ib_check_if_missing,)],
    'f4c1c6d9': [(log, ('2.3: Manato Body IB Hash',)),   (add_ib_check_if_missing,)],
    'c0425328': [(log, ('2.3: Manato Legs IB Hash',)),   (add_ib_check_if_missing,)],
    'f987f156': [(log, ('2.3: Manato Face IB Hash',)),   (add_ib_check_if_missing,)],
    #VB

    #Texture纹理
    # Face脸部
    '6d1343ec': [
        (log,                           ('2.3: Manato FaceA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('f987f156', 'Manato.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('8de251ee', 'Manato.FaceA.Diffuse.1024')),
    ],
    '8de251ee': [
        (log,                           ('2.3: Manato FaceA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('f987f156', 'Manato.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('6d1343ec', 'Manato.FaceA.Diffuse.2048')),
    ],

    # Hair头发
    '81a04fa6': [
        (log,                           ('2.3: Manato HairA, LegsA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('07353b33', 'Manato.HairA.Diffuse.1024')),
    ],
    '07353b33': [
        (log,                           ('2.3: Manato HairA, LegsA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('81a04fa6', 'Manato.HairA.Diffuse.2048')),
    ],
    '2bfdcb76': [
        (log,                           ('2.3: Manato HairA, LegsA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('20447316', 'Manato.HairA.LightMap.1024')),
    ],
    '20447316': [
        (log,                           ('2.3: Manato HairA, LegsA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('2bfdcb76', 'Manato.HairA.LightMap.2048')),
    ],
    'b9654ab9': [
        (log,                           ('2.3: Manato HairA, LegsA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('b8091cf0', 'Manato.HairA.MaterialMap.1024')),
    ],
    'b8091cf0': [
        (log,                           ('2.3: Manato HairA, LegsA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('b9654ab9', 'Manato.HairA.MaterialMap.2048')),
    ],

    # Body身体
    '9e78d2c7': [
        (log,                           ('2.3: Manato BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('9c659f1a', 'Manato.BodyA.Diffuse.1024')),
    ],
    '9c659f1a': [
        (log,                           ('2.3: Manato BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('9e78d2c7', 'Manato.BodyA.Diffuse.2048')),
    ],
    '53c85c6a': [
        (log,                           ('2.3: Manato BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('a15d0289', 'Manato.BodyA.LightMap.1024')),
    ],
    'a15d0289': [
        (log,                           ('2.3: Manato BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('53c85c6a', 'Manato.BodyA.LightMap.2048')),
    ],
    'fdc49789': [
        (log,                           ('2.3: Manato BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('92336a2f', 'Manato.BodyA.MaterialMap.1024')),
    ],
    '92336a2f': [
        (log,                           ('2.3: Manato BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('fdc49789', 'Manato.BodyA.MaterialMap.2048')),
    ],

    # MARK: Miyabi星见雅
    #IB
    '4faabaac': [(log, ('1.4: Miyabi Hair IB Hash',)),   (add_ib_check_if_missing,)],
    '981c1a1e': [(log, ('1.4: Miyabi Body IB Hash',)),   (add_ib_check_if_missing,)],
    'd8003df3': [(log, ('1.4: Miyabi Legs IB Hash',)),   (add_ib_check_if_missing,)],
    'dbd59d30': [(log, ('1.4: Miyabi Face IB Hash',)),   (add_ib_check_if_missing,)],
    #VB

    #Texture纹理
    # Face脸部
    '1d487fd5': [
        (log,                           ('1.4: Miyabi FaceA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('dbd59d30', 'Miyabi.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('92599e94', 'Miyabi.FaceA.Diffuse.1024')),
    ],
    '92599e94': [
        (log,                           ('1.4: Miyabi FaceA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('dbd59d30', 'Miyabi.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('1d487fd5', 'Miyabi.FaceA.Diffuse.2048')),
    ],

    # Hair头发
    '012e84e9': [
        (log,                           ('1.4: Miyabi HairA, LegsA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('ed6b94f7', 'Miyabi.HairA.Diffuse.1024')),
    ],
    'ed6b94f7': [
        (log,                           ('1.4: Miyabi HairA, LegsA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('012e84e9', 'Miyabi.HairA.Diffuse.2048')),
    ],
    'a6ea6d83': [
        (log,                           ('1.4: Miyabi HairA, LegsA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('8b5708f4', 'Miyabi.HairA.LightMap.1024')),
    ],
    '8b5708f4': [
        (log,                           ('1.4: Miyabi HairA, LegsA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('a6ea6d83', 'Miyabi.HairA.LightMap.2048')),
    ],
    'd5462e37': [
        (log,                           ('1.4: Miyabi HairA, LegsA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('a84d9003', 'Miyabi.HairA.MaterialMap.1024')),
    ],
    'a84d9003': [
        (log,                           ('1.4: Miyabi HairA, LegsA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('d5462e37', 'Miyabi.HairA.MaterialMap.2048')),
    ],

    # Body身体
    '09a2bbd1': [
        (log,                           ('1.4: Miyabi BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('1a3644e7', 'Miyabi.BodyA.Diffuse.1024')),
    ],
    '1a3644e7': [
        (log,                           ('1.4: Miyabi BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('09a2bbd1', 'Miyabi.BodyA.Diffuse.2048')),
    ],
    'fd289380': [
        (log,                           ('1.4: Miyabi BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('0492f64a', 'Miyabi.BodyA.LightMap.1024')),
    ],
    '0492f64a': [
        (log,                           ('1.4: Miyabi BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('fd289380', 'Miyabi.BodyA.LightMap.2048')),
    ],
    '450770fd': [
        (log,                           ('1.4: Miyabi BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('168b1df9', 'Miyabi.BodyA.MaterialMap.1024')),
    ],
    '168b1df9': [
        (log,                           ('1.4: Miyabi BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('450770fd', 'Miyabi.BodyA.MaterialMap.2048')),
    ],

    # MARK: MiyabiSkin星见雅皮肤
    #IB
    'ecaf558f': [(log, ('2.8: MiyabiSkin Hair IB Hash',)), (add_ib_check_if_missing,)],
    'a913e9a9': [(log, ('2.8: MiyabiSkin Body IB Hash',)), (add_ib_check_if_missing,)],
    'fbb18630': [(log, ('2.8: MiyabiSkin Clothes IB Hash',)), (add_ib_check_if_missing,)],
    #VB

    'f2f19cb2': [(log, ('2.8 -> 2.81: MiyabiSkin Body Blend Hash',)),   (update_hash, ('5121459b',)),],
    #Texture纹理
    # Body身体
    '18299e4d': [
        (log,                           ('2.8: MiyabiSkin BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('7d420160', 'MiyabiSkin.BodyA.Diffuse.1024')),
    ],
    '7d420160': [
        (log,                           ('2.8: MiyabiSkin BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('18299e4d', 'MiyabiSkin.BodyA.Diffuse.2048')),
    ],
    '6b59bc2d': [
        (log,                           ('2.8: MiyabiSkin BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('d8ad1898', 'MiyabiSkin.BodyA.LightMap.1024')),
    ],
    'd8ad1898': [
        (log,                           ('2.8: MiyabiSkin BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('6b59bc2d', 'MiyabiSkin.BodyA.LightMap.2048')),
    ],
    '93d7173c': [
        (log,                           ('2.8: MiyabiSkin BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('417337f2', 'MiyabiSkin.BodyA.MaterialMap.1024')),
    ],
    '417337f2': [
        (log,                           ('2.8: MiyabiSkin BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('93d7173c', 'MiyabiSkin.BodyA.MaterialMap.2048')),
    ],

    # Clothes
    '66724f5a': [(log, ('2.8 -> 3.0: MiyabiSkin ClothesA Diffuse 2048p Hash',)), (update_hash, ('4e6c90bd',))],
    '4e6c90bd': [
        (log,                           ('2.8: MiyabiSkin ClothesA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   (('88e357af','7d80f565'), 'MiyabiSkin.ClothesA.Diffuse.1024')),
    ],
    '88e357af': [(log, ('2.8 -> 3.0: MiyabiSkin ClothesA Diffuse 1024p Hash',)), (update_hash, ('7d80f565',))],
    '7d80f565': [
        (log,                           ('2.8: MiyabiSkin ClothesA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   (('66724f5a','4e6c90bd'), 'MiyabiSkin.ClothesA.Diffuse.2048')),
    ],
    '7b8eb437': [
        (log,                           ('2.8: MiyabiSkin ClothesA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('93b264d9', 'MiyabiSkin.ClothesA.LightMap.1024')),
    ],
    '93b264d9': [
        (log,                           ('2.8: MiyabiSkin ClothesA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('7b8eb437', 'MiyabiSkin.ClothesA.LightMap.2048')),
    ],
    '1e1485e7': [(log, ('2.8 -> 3.0: MiyabiSkin ClothesA MaterialMap 2048p Hash',)), (update_hash, ('30590865',))],
    '30590865': [
        (log,                           ('2.8: MiyabiSkin ClothesA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   (('85aad660','2fbabf2e'), 'MiyabiSkin.ClothesA.MaterialMap.1024')),
    ],
    '85aad660': [(log, ('2.8 -> 3.0: MiyabiSkin ClothesA MaterialMap 1024p Hash',)), (update_hash, ('2fbabf2e',))],
    '2fbabf2e': [
        (log,                           ('2.8: MiyabiSkin ClothesA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   (('1e1485e7','30590865'), 'MiyabiSkin.ClothesA.MaterialMap.2048')),
    ],

    # MARK: NanGongYu南宫羽
    #IB
    '969152d4': [(log, ('2.7: NanGongYu Hair IB Hash',)), (add_ib_check_if_missing,)],
    '4586e530': [(log, ('2.7: NanGongYu Body IB Hash',)), (add_ib_check_if_missing,)],
    'd643e19a': [(log, ('2.7: NanGongYu Face IB Hash',)), (add_ib_check_if_missing,)],
    #VB

    #Texture纹理
    # Face脸部
    '1fd77103': [
        (log,                           ('2.7: NanGongYu FaceA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('d643e19a', 'NanGongYu.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('b6e87aef', 'NanGongYu.FaceA.Diffuse.1024')),
    ],
    'b6e87aef': [
        (log,                           ('2.7: NanGongYu FaceA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('d643e19a', 'NanGongYu.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('1fd77103', 'NanGongYu.FaceA.Diffuse.2048')),
    ],

    # Hair头发
    'df39b77c': [
        (log,                           ('2.7: NanGongYu HairA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('d2e23730', 'NanGongYu.HairA.Diffuse.1024')),
    ],
    'd2e23730': [
        (log,                           ('2.7: NanGongYu HairA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('df39b77c', 'NanGongYu.HairA.Diffuse.2048')),
    ],
    'd94a0c41': [
        (log,                           ('2.7: NanGongYu HairA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('e3573bc8', 'NanGongYu.HairA.LightMap.1024')),
    ],
    'e3573bc8': [
        (log,                           ('2.7: NanGongYu HairA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('d94a0c41', 'NanGongYu.HairA.LightMap.2048')),
    ],
    'a458a615': [
        (log,                           ('2.7: NanGongYu HairA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('687f57b8', 'NanGongYu.HairA.MaterialMap.1024')),
    ],
    '687f57b8': [
        (log,                           ('2.7: NanGongYu HairA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('a458a615', 'NanGongYu.HairA.MaterialMap.2048')),
    ],

    # Body身体
    '2d290490': [(log,('2.7: -> 2.8: NanGongYu BodyA Diffuse 2048p Hash',)),(update_hash,('11254966',)),],
    '11254966': [
        (log,                           ('2.7: NanGongYu BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   (('fe06152c','dc41fbbf'), 'NanGongYu.BodyA.Diffuse.1024')),
    ],
    'fe06152c': [(log,('2.7: -> 2.8: NanGongYu BodyA Diffuse 1024p Hash',)),(update_hash,('dc41fbbf',)),],
    'dc41fbbf': [
        (log,                           ('2.7: NanGongYu BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   (('2d290490','11254966'), 'NanGongYu.BodyA.Diffuse.2048')),
    ],
    'fee3d533': [
        (log,                           ('2.7: NanGongYu BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('ab51539c', 'NanGongYu.BodyA.LightMap.1024')),
    ],
    'ab51539c': [
        (log,                           ('2.7: NanGongYu BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('fee3d533', 'NanGongYu.BodyA.LightMap.2048')),
    ],
    'beb11b78': [
        (log,                           ('2.7: NanGongYu BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('958e389e', 'NanGongYu.BodyA.MaterialMap.1024')),
    ],
    '958e389e': [
        (log,                           ('2.7: NanGongYu BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('beb11b78', 'NanGongYu.BodyA.MaterialMap.2048')),
    ],

    # MARK: NanGongYuSkin南宫羽皮肤
    #IB
    '5f2741ff': [(log, ('2.7: NanGongYuSkin Body IB Hash',)), (add_ib_check_if_missing,)],
    #VB
    #Texture纹理
    # Hair头发
    '5a026445': [
        (log,                           ('2.7: NanGongYuSkin HairA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('4fa2f495', 'NanGongYuSkin.HairA.Diffuse.1024')),
    ],
    '4fa2f495': [
        (log,                           ('2.7: NanGongYuSkin HairA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('5a026445', 'NanGongYuSkin.HairA.Diffuse.2048')),
    ],

    # Body身体
    '46c73033': [
        (log,                           ('2.7: NanGongYuSkin BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('263aba53', 'NanGongYuSkin.BodyA.Diffuse.1024')),
    ],
    '263aba53': [
        (log,                           ('2.7: NanGongYuSkin BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('46c73033', 'NanGongYuSkin.BodyA.Diffuse.2048')),
    ],
    'c17bc21d': [
        (log,                           ('2.7: NanGongYuSkin BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('79423b33', 'NanGongYuSkin.BodyA.LightMap.1024')),
    ],
    '79423b33': [
        (log,                           ('2.7: NanGongYuSkin BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('c17bc21d', 'NanGongYuSkin.BodyA.LightMap.2048')),
    ],
    'e8200d09': [
        (log,                           ('2.7: NanGongYuSkin BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('1786d968', 'NanGongYuSkin.BodyA.MaterialMap.1024')),
    ],
    '1786d968': [
        (log,                           ('2.7: NanGongYuSkin BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('e8200d09', 'NanGongYuSkin.BodyA.MaterialMap.2048')),
    ],

    # MARK: Nekomata猫又
    #IB
    'da11fd85': [(log, ('1.0: Nekomata Hair IB Hash',)),   (add_ib_check_if_missing,)],
    '26a487ff': [(log, ('1.0: Nekomata Body IB Hash',)),   (add_ib_check_if_missing,)],
    '74688145': [(log, ('1.0: Nekomata Swords IB Hash',)), (add_ib_check_if_missing,)],
    '37119851': [(log, ('1.0: Nekomata Face IB Hash',)),   (add_ib_check_if_missing,)],
    #VB

    '2c317dda': [(log, ('1.0 -> 1.1: Nekomata Body Position Hash',)),  (update_hash, ('eaad1408',))],
    'b5a4c084': [(log, ('1.0 -> 1.1: Nekomata Body Texcoord Hash',)),  (update_hash, ('f589a51f',))],

    '6abb714e': [(log, ('1.0 -> 1.1: Nekomata Swords Position Hash',)), (update_hash, ('3c4015fd',))],
    '70f4875e': [(log, ('1.0 -> 1.1: Nekomata Swords Texcoord Hash',)), (update_hash, ('2a4f8c9e',))],

    #Texture纹理
    # Face脸部
    'fed3abbe': [(log, ('1.0 -> 1.1: Nekomata FaceA Diffuse 2048p Hash',)), (update_hash, ('ba411d22',))],
    'ba411d22': [
        (log,                           ('1.1: Nekomata FaceA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('37119851', 'Nekomata.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('0834f635', 'd9370c84'), 'Nekomata.FaceA.Diffuse.1024')),
    ],
    'd9370c84': [(log, ('1.0 -> 1.1: Nekomata FaceA Diffuse 1024p Hash',)), (update_hash, ('0834f635',))],
    '0834f635': [
        (log,                           ('1.1: Nekomata FaceA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('37119851', 'Nekomata.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('ba411d22', 'fed3abbe'), 'Nekomata.FaceA.Diffuse.2048')),
    ],

    # Hair头发
    '25f3ae9b': [
        (log,                           ('1.0: Nekomata HairA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('aed3d8bd', 'Nekomata.HairA.Diffuse.1024')),
    ],
    'aed3d8bd': [
        (log,                           ('1.0: Nekomata HairA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('25f3ae9b', 'Nekomata.HairA.Diffuse.2048')),
    ],
    '548c7f7d': [(log, ('1.7 -> 2.0: Nekomata HairA LightMap 2048p Hash',)), (update_hash, ('1c0193dc',))],
    '1c0193dc': [
        (log,                           ('1.0: Nekomata HairA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   (('0deeb9d2','f8accad8','362c205e'), 'Nekomata.HairA.LightMap.1024')),
    ],
    '0deeb9d2': [(log, ('1.7 -> 2.0: Nekomata HairA LightMap 1024p Hash',)), (update_hash, ('362c205e',))],
    'f8accad8': [(log, ('1.0 -> 1.7: Nekomata HairA LightMap 1024p Hash',)), (update_hash, ('0deeb9d2',))],
    '362c205e': [
        (log,                           ('1.0: Nekomata HairA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   (('1c0193dc','548c7f7d'), 'Nekomata.HairA.LightMap.2048')),
    ],
    '4ca5efc6': [(log, ('1.7 -> 2.0: Nekomata HairA MaterialMap 2048p Hash',)), (update_hash, ('3f73186f',))],
    '3f73186f': [
        (log,                           ('1.0: Nekomata HairA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   (('63687775','0c22352c','378b282c'), 'Nekomata.HairA.MaterialMap.1024')),
    ],
    '63687775': [(log, ('1.7 -> 2.0: Nekomata HairA MaterialMap 1024p Hash',)), (update_hash, ('378b282c',))],
    '0c22352c': [(log, ('1.0 -> 1.7: Nekomata HairA MaterialMap 1024p Hash',)), (update_hash, ('63687775',))],
    '378b282c': [
        (log,                           ('1.0: Nekomata HairA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   (('3f73186f','4ca5efc6'), 'Nekomata.HairA.MaterialMap.2048')),
    ],

    # Body身体
    'd3f67c0d': [(log,('1.0: -> 1.1: Nekomata HairB, BodyA, SwordsA Diffuse 2048p Hash',)),(update_hash,('207b8e63',)),],
    '207b8e63': [
        (log,                           ('1.0: Nekomata HairB, BodyA, SwordsA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   (('60687646', '37d3154d'), 'Nekomata.HairB.Diffuse.1024')),
    ],
    '37d3154d': [(log,('1.0: -> 1.1: Nekomata HairB, BodyA, SwordsA Diffuse 1024p Hash',)),(update_hash, ('60687646',)),],
    '60687646': [
        (log,                           ('1.1 Nekomata HairB, BodyA, SwordsA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   (('207b8e63', 'd3f67c0d'), 'Nekomata.HairB.Diffuse.2048')),
    ],
    'fc53fc6f': [(log, ('1.7 -> 2.0: Nekomata HairB LightMap 2048p Hash',)), (update_hash, ('25df29e7',))],
    '25df29e7': [
        (log,                           ('1.0: Nekomata HairB, BodyA, SwordsA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   (('4c09361d','4f3f7df0'), 'Nekomata.HairB.LightMap.1024')),
    ],
    '4f3f7df0': [(log, ('1.7 -> 2.0: Nekomata HairB, BodyA, SwordsA LightMap 1024p Hash',)), (update_hash, ('4c09361d',))],
    '4c09361d': [
        (log,                           ('1.0: Nekomata HairB, BodyA, SwordsA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   (('25df29e7','fc53fc6f'), 'Nekomata.HairB.LightMap.2048')),
    ],
    'f26828bd': [(log,('1.0: Nekomata HairB, BodyA, SwordsA MaterialMap 2048p Hash',)),(update_hash,('b3286755',)),],
    'b3286755': [
        (log,                           ('1.1: Nekomata HairB, BodyA, SwordsA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   (('a5529690', '424da647'), 'Nekomata.HairB.MaterialMap.1024')),
    ],
    '424da647': [(log,('1.0 -> 1.1: Nekomata HairB, BodyA, SwordsA MaterialMap 1024p Hash',)),(update_hash,('a5529690',)),],
    'a5529690': [
        (log,                           ('1.1: Nekomata HairB, BodyA, SwordsA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   (('b3286755', 'f26828bd'), 'Nekomata.HairB.MaterialMap.2048')),
    ],

    # MARK: Nicole妮可
    #IB
    '7dcfe907': [(log, ('3.01: Nicole Hair-头发 IB Hash',)), (add_ib_check_if_missing,)],
    'e53364dd': [(log, ('3.01: Nicole Body-身体 IB Hash',)), (add_ib_check_if_missing,)],
    '93b02078': [(log, ('3.01: Nicole Face-脸 IB Hash',)), (add_ib_check_if_missing,)],

    '5a4c1ef3': [(log, ('1.0 -> 3.01: Nicole Body-身体 IB Hash',)), (update_hash, ('e53364dd',))],
    '7435fc0e': [(log, ('1.0 -> 3.01: Nicole Face-脸 IB Hash',)), (update_hash, ('93b02078',))],
    '6847bbbd': [(log, ('1.0 -> 3.01: Nicole Hair-头发 IB Hash',)), (update_hash, ('7dcfe907',))],
    #VB
    '077c3500': [(log, ('2.4 -> 3.01: Nicole Amillion-艾米莉安 texcoord_vb Hash',)), (update_hash, ('f9f810ed',))],
    '7ecda89f': [(log, ('2.4 -> 3.01: Nicole Body-身体 blend_vb Hash',)), (update_hash, ('b793c804',))],
    '8cc1262b': [(log, ('2.4 -> 3.01: Nicole Body-身体 draw_vb Hash',)), (update_hash, ('b19da99e',))],
    '89df5a07': [(log, ('2.4 -> 3.01: Nicole Body-身体 position_vb Hash',)), (update_hash, ('4af0a4cd',))],
    '91c1b779': [(log, ('2.4 -> 3.01: Nicole Body-身体 texcoord_vb Hash',)), (update_hash, ('ed4c47a9',))],
    '347e4a48': [(log, ('2.4 -> 3.01: Nicole Hair-头发 blend_vb Hash',)), (update_hash, ('8171f5c9',))],
    'f6344432': [(log, ('2.4 -> 3.01: Nicole Hair-头发 draw_vb Hash',)), (update_hash, ('d9b8d61a',))],
    '199853eb': [(log, ('2.4 -> 3.01: Nicole Hair-头发 position_vb Hash',)), (update_hash, ('6f931ca7',))],
    '06e4fd79': [(log, ('2.4 -> 3.01: Nicole Hair-头发 texcoord_vb Hash',)), (update_hash, ('e04f4893',))],
    'b25ebcf6': [(log, ('2.4 -> 3.01: Nicole Face-脸 blend_vb Hash',)), (update_hash, ('292d1b1f',))],
    '9274e401': [(log, ('2.4 -> 3.01: Nicole Face-脸 draw_vb Hash',)), (update_hash, ('967c2f1c',))],
    'a8667746': [(log, ('2.4 -> 3.01: Nicole Face-脸 position_vb Hash',)), (update_hash, ('ac6ebc5b',))],
    '5714e5e6': [(log, ('2.4 -> 3.01: Nicole Face-脸 texcoord_vb Hash',)), (update_hash, ('d5958556',))],

    # Face脸部
    'd1e84a34': [
        (log,                           ('1.0: Nicole FaceA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('6abd3dd3', 'Nicole.FaceA.Diffuse.1024')),
    ],
    '6abd3dd3': [
        (log,                           ('1.0: Nicole FaceA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('d1e84a34', 'Nicole.FaceA.Diffuse.2048')),
    ],

    # Hair头发
    '6d3868f9': [
        (log,                           ('1.0: Nicole HairA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('7a45adcd', 'Nicole.HairA.Diffuse.1024')),
    ],
    '7a45adcd': [
        (log,                           ('1.0: Nicole HairA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('6d3868f9', 'Nicole.HairA.Diffuse.2048')),
    ],
    '1dfd9e16': [(log, ('1.7 -> 2.0: Nicole HairA LightMap 2048p Hash',)), (update_hash, ('8c9c25d5',))],
    '8c9c25d5': [
        (log,                           ('1.0: Nicole HairA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   (('f3c21e41','9adc04ed'), 'Nicole.HairA.LightMap.1024')),
    ],
    '9adc04ed': [(log, ('1.7 -> 2.0: Nicole HairA LightMap 1024p Hash',)), (update_hash, ('f3c21e41',))],
    'f3c21e41': [
        (log,                           ('1.0: Nicole HairA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   (('8c9c25d5','1dfd9e16'), 'Nicole.HairA.LightMap.2048')),
    ],

    # Body
    'f86ffe2c': [
        (log,                           ('1.0: Nicole BodyA, BangbooA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('9ee9b402', 'Nicole.BodyA.Diffuse.1024')),
    ],
    '9ee9b402': [
        (log,                           ('1.0: Nicole BodyA, BangbooA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('f86ffe2c', 'Nicole.BodyA.Diffuse.2048')),
    ],    
    '80855e0f': [
        (log,                           ('1.0: Nicole BodyA, BangbooA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('2b5aa784', 'Nicole.BodyA.LightMap.1024')),
    ],
    '2b5aa784': [
        (log,                           ('1.0: Nicole BodyA, BangbooA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('80855e0f', 'Nicole.BodyA.LightMap.2048')),
    ],
    '95cabef3': [
        (log,                           ('1.0: Nicole BodyA, BangbooA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('bb33129d', 'Nicole.BodyA.MaterialMap.1024')),
    ],
    'bb33129d': [
        (log,                           ('1.0: Nicole BodyA, BangbooA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('95cabef3', 'Nicole.BodyA.MaterialMap.2048')),
    ],

    # MARK: NicoleSkin妮可皮肤
    #IB
    '776f5703': [(log, ('2.0: NicoleSkin Hair IB Hash',)),    (add_ib_check_if_missing,)],
    '52842f31': [(log, ('2.0: NicoleSkin Body IB Hash',)),    (add_ib_check_if_missing,)],
    #VB
    #Texture纹理
    # Hair头发
    'cdaa9ab5': [
        (log,                           ('2.0: NicoleSkin HairA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('0e55f39d', 'NicoleSkin.HairA.Diffuse.1024')),
    ],
    '0e55f39d': [
        (log,                           ('2.0: NicoleSkin HairA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('cdaa9ab5', 'NicoleSkin.HairA.Diffuse.2048')),
    ],
    '4c8b0bce': [
        (log,                           ('2.0: NicoleSkin HairA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('b3ef7388', 'NicoleSkin.HairA.LightMap.1024')),
    ],
    'b3ef7388': [
        (log,                           ('2.0: NicoleSkin HairA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('4c8b0bce', 'NicoleSkin.HairA.LightMap.2048')),
    ],

    # Body身体
    '4af0010c': [
        (log,                           ('2.0: NicoleSkin BodyA, BangbooA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('b2bd144b', 'NicoleSkin.BodyA.Diffuse.1024')),
    ],
    'b2bd144b': [
        (log,                           ('2.0: NicoleSkin BodyA, BangbooA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('4af0010c', 'NicoleSkin.BodyA.Diffuse.2048')),
    ],    
    'c45a93a3': [
        (log,                           ('2.0: NicoleSkin BodyA, BangbooA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('5fcde3a6', 'NicoleSkin.BodyA.LightMap.1024')),
    ],
    '5fcde3a6': [
        (log,                           ('2.0: NicoleSkin BodyA, BangbooA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('c45a93a3', 'NicoleSkin.BodyA.LightMap.2048')),
    ],
    '592cee08': [
        (log,                           ('2.0: NicoleSkin BodyA, BangbooA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('76774ee7', 'NicoleSkin.BodyA.MaterialMap.1024')),
    ],
    '76774ee7': [
        (log,                           ('2.0: NicoleSkin BodyA, BangbooA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('592cee08', 'NicoleSkin.BodyA.MaterialMap.2048')),
    ],

    # MARK: Norma诺姆
    #IB
    '773f390c': [(log, ('3.0: Norma Body IB Hash',)), (add_ib_check_if_missing,)],
    '4fafb136': [(log, ('3.0: Norma Face IB Hash',)), (add_ib_check_if_missing,)],
    'a2150d3b': [(log, ('3.0: Norma Hair IB Hash',)), (add_ib_check_if_missing,)],
    'bcc7e369': [(log, ('3.0: Norma Hat IB Hash',)), (add_ib_check_if_missing,)],
    '85361021': [(log, ('3.1: Norma Shell IB Hash',)), (add_ib_check_if_missing,)],
    'ca38d6a1': [(log, ('3.1: Norma Weapon IB Hash',)), (add_ib_check_if_missing,)],
    #VB
    'fc98a89c': [(log, ('3.1: Norma Hat-帽子 NormalMap Hash',)), (update_hash, ('ebac056e',))],
    'dc5bc6d9': [(log, ('3.1: Norma Hat-帽子 NormalMap Hash',)), (update_hash, ('798adba3',))],
    '37da98f5': [(log, ('3.1: Norma Body-身体 NormalMap Hash',)), (update_hash, ('ebac056e',))],
    '02cbd89d': [(log, ('3.1: Norma Body-身体 NormalMap Hash',)), (update_hash, ('798adba3',))],
    '4050da0a': [(log, ('3.1: Norma Weapon-武器 NormalMap Hash',)), (update_hash, ('ebac056e',))],
    '0139f54e': [(log, ('3.1: Norma Weapon-武器 NormalMap Hash',)), (update_hash, ('798adba3',))],

    '38e511a4': [(log, ('3.0 -> 3.1: Norma Weapon Position Hash',)), (update_hash, ('07e51b64',)),],
    'd3a66db9': [(log, ('3.0 -> 3.1: Norma Weapon Blend Hash',)),    (update_hash, ('aa195b0b',)),],
    '89a25f1a': [(log, ('3.0 -> 3.1: Norma Weapon Texcoord Hash',)), (update_hash, ('c4173b6e',)),],

    'e2a92567': [(log, ('3.0 -> 3.1: Norma Shell Position Hash',)), (update_hash, ('e3fafeeb',)),],
    '1d67e673': [(log, ('3.0 -> 3.1: Norma Shell Texcoord Hash',)), (update_hash, ('44991f30',)),],
    #Texture纹理
    # Face脸部
    '007dc9ec': [
        (log,                           ('3.0: Norma FaceA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('c18a1af1', 'Norma.FaceA.Diffuse.1024')),
    ],
    'c18a1af1': [
        (log,                           ('3.0: Norma FaceA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('007dc9ec', 'Norma.FaceA.Diffuse.2048')),
    ],

    # Body身体
    '8dbb873b': [
        (log,                           ('3.0: Norma BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('ab235f8c', 'Norma.BodyA.Diffuse.1024')),
    ],
    'ab235f8c': [
        (log,                           ('3.0: Norma BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('8dbb873b', 'Norma.BodyA.Diffuse.2048')),
    ],
    '13e85378': [
        (log,                           ('3.0: Norma BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('becdc27c', 'Norma.BodyA.LightMap.1024')),
    ],
    'becdc27c': [
        (log,                           ('3.0: Norma BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('13e85378', 'Norma.BodyA.LightMap.2048')),
    ],
    'fcb3bd07': [
        (log,                           ('3.0: Norma BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('0e22ca8e', 'Norma.BodyA.MaterialMap.1024')),
    ],
    '0e22ca8e': [
        (log,                           ('3.0: Norma BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('fcb3bd07', 'Norma.BodyA.MaterialMap.2048')),
    ],
       
    # Hair头发
    '9593fbbd': [
        (log,                           ('3.0: Norma HairA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('a86b749d', 'Norma.HairA.Diffuse.1024')),
    ],
    'a86b749d': [
        (log,                           ('3.0: Norma HairA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('9593fbbd', 'Norma.HairA.Diffuse.2048')),
    ],
    'a0010ed7': [
        (log,                           ('3.0: Norma HairA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('541008f2', 'Norma.HairA.LightMap.1024')),
    ],
    '541008f2': [
        (log,                           ('3.0: Norma HairA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('a0010ed7', 'Norma.HairA.LightMap.2048')),
    ],
    '6493d4d4': [
        (log,                           ('3.0: Norma HairA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('60152e0e', 'Norma.HairA.MaterialMap.1024')),
    ],
    '60152e0e': [
        (log,                           ('3.0: Norma HairA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('6493d4d4', 'Norma.HairA.MaterialMap.2048')),
    ],

    # Weapon武器
    '23ba50e2': [
        (log,                           ('3.1: Norma WeaponA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('ff0137ae', 'Norma.WeaponA.Diffuse.1024')),
    ],
    'ff0137ae': [
        (log,                           ('3.1: Norma WeaponA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('23ba50e2', 'Norma.WeaponA.Diffuse.2048')),
    ],
    '00b13a4d': [
        (log,                           ('3.1: Norma WeaponA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('9bb6a4c1', 'Norma.WeaponA.LightMap.1024')),
    ],
    '9bb6a4c1': [
        (log,                           ('3.1: Norma WeaponA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('00b13a4d', 'Norma.WeaponA.LightMap.2048')),
    ],
    '7ae5f4d6': [(log, ('3.0 -> 3.1: Norma WeaponA MaterialMap 2048p Hash',)), (update_hash, ('79a583ad',))],
    '79a583ad': [
        (log,                           ('3.1: Norma WeaponA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   (('1db67ade','b70b6037'), 'Norma.WeaponA.MaterialMap.1024')),
    ],
    '1db67ade': [(log, ('3.0 -> 3.1: Norma WeaponA MaterialMap 2048p Hash',)), (update_hash, ('b70b6037',))],
    'b70b6037': [
        (log,                           ('3.1: Norma WeaponA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   (('7ae5f4d6','79a583ad'), 'Norma.WeaponA.MaterialMap.2048')),
    ],

    # MARK: Orphie 奥菲丝
    #IB
    '6988bfcd': [(log, ('2.1: Orphie Hair IB Hash',)),         (add_ib_check_if_missing,)],
    'a5eac582': [(log, ('2.1: Orphie Body IB Hash',)),         (add_ib_check_if_missing,)],
    '80017921': [(log, ('2.1: Orphie Leg IB Hash',)),  (add_ib_check_if_missing,)],    
    'ed85f33b': [(log, ('2.1: Orphie Face IB Hash',)),         (add_ib_check_if_missing,)],
    #VB

    #Texture纹理
    # Face脸部
    '0df52ae7': [
        (log,                           ('2.1: Orphie FaceA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('ed85f33b', 'Orphie.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('66efca96', 'Orphie.FaceA.Diffuse.1024')),
    ],
    '66efca96': [
        (log,                           ('2.1: Orphie FaceA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('ed85f33b', 'Orphie.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('0df52ae7', 'Orphie.FaceA.Diffuse.2048')),
    ],

    # Hair头发
    'ce52779f': [
        (log,                           ('2.1: Orphie HairA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('78d4038b', 'Orphie.HairA.Diffuse.1024')),
    ],
    '78d4038b': [
        (log,                           ('2.1: Orphie HairA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('ce52779f', 'Orphie.HairA.Diffuse.2048')),
    ],
    '77abe83b': [
        (log,                           ('2.1: Orphie HairA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('643268b4', 'Orphie.HairA.LightMap.1024')),
    ],
    '643268b4': [
        (log,                           ('2.1: Orphie HairA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('77abe83b', 'Orphie.HairA.LightMap.2048')),
    ],
    '94ed2491': [
        (log,                           ('2.1: Orphie HairA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('ef6e3a3b', 'Orphie.HairA.MaterialMap.1024')),
    ],
    'ef6e3a3b': [
        (log,                           ('2.1: Orphie HairA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('94ed2491', 'Orphie.HairA.MaterialMap.2048')),
    ],

    # Body身体
    'c9bea5d7': [
        (log,                           ('2.1: Orphie BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('ca89cd72', 'Orphie.BodyA.Diffuse.1024')),
    ],
    'ca89cd72': [
        (log,                           ('2.1: Orphie BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('c9bea5d7', 'Orphie.BodyA.Diffuse.2048')),
    ],
    '9a0406fe': [
        (log,                           ('2.1: Orphie BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('c797a191', 'Orphie.BodyA.LightMap.1024')),
    ],
    'c797a191': [
        (log,                           ('2.1: Orphie BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('9a0406fe', 'Orphie.BodyA.LightMap.2048')),
    ],
    '1daf926d': [
        (log,                           ('2.1: Orphie BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('7f6aa298', 'Orphie.BodyA.MaterialMap.1024')),
    ],
    '7f6aa298': [
        (log,                           ('2.1: Orphie BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('1daf926d', 'Orphie.BodyA.MaterialMap.2048')),
    ],

    # Leg
    'dd4120db': [
        (log,                           ('2.1: Orphie HoverboardA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('aaeb5f0f', 'Orphie.HoverboardA.Diffuse.1024')),
    ],
    'aaeb5f0f': [
        (log,                           ('2.1: Orphie HoverboardA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('dd4120db', 'Orphie.HoverboardA.Diffuse.2048')),
    ],
    'a9ae84df': [
        (log,                           ('2.1: Orphie HoverboardA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('ec3855fa', 'Orphie.HoverboardA.LightMap.1024')),
    ],
    'ec3855fa': [
        (log,                           ('2.1: Orphie HoverboardA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('a9ae84df', 'Orphie.HoverboardA.LightMap.2048')),
    ],
    '867ceb5b': [
        (log,                           ('2.1: Orphie HoverboardA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('70ff1eca', 'Orphie.HoverboardA.MaterialMap.1024')),
    ],
    '70ff1eca': [
        (log,                           ('2.1: Orphie HoverboardA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('867ceb5b', 'Orphie.HoverboardA.MaterialMap.2048')),
    ],

    # MARK: PanYinhu潘引壶
    #IB
    'cb1a6db9': [(log, ('2.0: PanYinhu Body IB Hash',)),    (add_ib_check_if_missing,)],
    'ebb6a59b': [(log, ('2.0: PanYinhu Face IB Hash',)),    (add_ib_check_if_missing,)],
    'ff7e9b40': [(log, ('2.0: PanYinhu Hat IB Hash',)),    (add_ib_check_if_missing,)],
    #VB

    #Texture纹理
    # Face脸部
    'ed361b8f': [
        (log,                           ('2.0: PanYinhu FaceA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('452a0918', 'PanYinhu.FaceA.Diffuse.1024')),
    ],
    '452a0918': [
        (log,                           ('2.0: PanYinhu FaceA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('ed361b8f', 'PanYinhu.FaceA.Diffuse.2048')),
    ],
    '96280008': [
        (log,                           ('2.0: PanYinhu FaceA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('3744882e', 'PanYinhu.FaceA.LightMap.1024')),
    ],
    '3744882e': [
        (log,                           ('2.0: PanYinhu FaceA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('96280008', 'PanYinhu.FaceA.LightMap.2048')),
    ],
    '57446a22': [
        (log,                           ('2.0: PanYinhu FaceA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('18dd19bf', 'PanYinhu.FaceA.MaterialMap.1024')),
    ],
    '18dd19bf': [
        (log,                           ('2.0: PanYinhu FaceA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('57446a22', 'PanYinhu.FaceA.MaterialMap.2048')),
    ],


    # Body身体
    'c0928025': [
        (log,                           ('2.0: PanYinhu BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('b20c7e8b', 'PanYinhu.BodyA.Diffuse.1024')),
    ],
    'b20c7e8b': [
        (log,                           ('2.0: PanYinhu BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('c0928025', 'PanYinhu.BodyA.Diffuse.2048')),
    ],
    '7d3c4c3d': [
        (log,                           ('2.0: PanYinhu BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('7967c15f', 'PanYinhu.BodyA.LightMap.1024')),
    ],
    '7967c15f': [
        (log,                           ('2.0: PanYinhu BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('7d3c4c3d', 'PanYinhu.BodyA.LightMap.2048')),
    ],
    '42fc25f0': [
        (log,                           ('2.0: PanYinhu BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('2daeed33', 'PanYinhu.BodyA.MaterialMap.1024')),
    ],
    '2daeed33': [
        (log,                           ('2.0: PanYinhu BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('42fc25f0', 'PanYinhu.BodyA.MaterialMap.2048')),
    ],


    #Hat
    'f2433e17': [
        (log,                           ('2.0: PanYinhu HatA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('ff7e9b40', 'PanYinhu.Hat.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('cf6afa84', 'PanYinhu.HatA.Diffuse.1024')),
    ],
    'cf6afa84': [
        (log,                           ('2.0: PanYinhu HatA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('ff7e9b40', 'PanYinhu.Hat.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('f2433e17', 'PanYinhu.HatA.Diffuse.2048')),
    ],
    'ddeaa4c3': [
        (log,                           ('2.0: PanYinhu HatA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('ff7e9b40', 'PanYinhu.Hat.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('26454e30', 'PanYinhu.HatA.LightMap.1024')),
    ],
    '26454e30': [
        (log,                           ('2.0: PanYinhu HatA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('ff7e9b40', 'PanYinhu.Hat.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('ddeaa4c3', 'PanYinhu.HatA.LightMap.2048')),
    ],
    'de553410': [
        (log,                           ('2.0: PanYinhu HatA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        ('ff7e9b40', 'PanYinhu.Hat.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('e0433c18', 'PanYinhu.HatA.MaterialMap.1024')),
    ],
    'e0433c18': [
        (log,                           ('2.0: PanYinhu HatA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        ('ff7e9b40', 'PanYinhu.Hat.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('de553410', 'PanYinhu.HatA.MaterialMap.2048')),
    ],

    # MARK: PanYinhuSkin潘引壶皮肤
    #IB
    'b518e540': [(log, ('2.6: PanYinhuSkin Body IB Hash',)),    (add_ib_check_if_missing,)],
    #VB
    #Texture纹理
    # Body身体
    'e9a912e7': [
        (log,                           ('2.6: PanYinhuSkin BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('0cab7a7b', 'PanYinhuSkin.BodyA.Diffuse.1024')),
    ],
    '0cab7a7b': [
        (log,                           ('2.6: PanYinhuSkin BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('e9a912e7', 'PanYinhuSkin.BodyA.Diffuse.2048')),
    ],
    '54c0f79a': [
        (log,                           ('2.6: PanYinhuSkin BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('91bfe5cd', 'PanYinhuSkin.BodyA.LightMap.1024')),
    ],
    '91bfe5cd': [
        (log,                           ('2.6: PanYinhuSkin BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('54c0f79a', 'PanYinhuSkin.BodyA.LightMap.2048')),
    ],
    '7498bd49': [
        (log,                           ('2.6: PanYinhuSkin BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('78cbb2e4', 'PanYinhuSkin.BodyA.MaterialMap.1024')),
    ],
    '78cbb2e4': [
        (log,                           ('2.6: PanYinhuSkin BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('7498bd49', 'PanYinhuSkin.BodyA.MaterialMap.2048')),
    ],
    '8459c5e8': [
        (log,                           ('2.6: PanYinhuSkin BodyB Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('b3775104', 'PanYinhuSkin.BodyB.Diffuse.1024')),
    ],
    'b3775104': [
        (log,                           ('2.6: PanYinhuSkin BodyB Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('8459c5e8', 'PanYinhuSkin.BodyB.Diffuse.2048')),
    ],
    'c7bdc86b': [
        (log,                           ('2.6: PanYinhuSkin BodyB LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('240da72f', 'PanYinhuSkin.BodyB.LightMap.1024')),
    ],
    '240da72f': [
        (log,                           ('2.6: PanYinhuSkin BodyB LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('c7bdc86b', 'PanYinhuSkin.BodyB.LightMap.2048')),
    ],
    'c50582f7': [
        (log,                           ('2.6: PanYinhuSkin BodyB MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('bf25d6f7', 'PanYinhuSkin.BodyB.MaterialMap.1024')),
    ],
    'bf25d6f7': [
        (log,                           ('2.6: PanYinhuSkin BodyB MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('c50582f7', 'PanYinhuSkin.BodyB.MaterialMap.2048')),
    ],
    '10e8bc53': [
        (log,                           ('2.6: PanYinhuSkin BodyC Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('48c0fbcc', 'PanYinhuSkin.BodyC.Diffuse.1024')),
    ],
    '48c0fbcc': [
        (log,                           ('2.6: PanYinhuSkin BodyC Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('10e8bc53', 'PanYinhuSkin.BodyC.Diffuse.2048')),
    ],
    '1da6b5bf': [
        (log,                           ('2.6: PanYinhuSkin BodyC LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('eceb77a3', 'PanYinhuSkin.BodyC.LightMap.1024')),
    ],
    'eceb77a3': [
        (log,                           ('2.6: PanYinhuSkin BodyC LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('1da6b5bf', 'PanYinhuSkin.BodyC.LightMap.2048')),
    ],
    'eb5755d6': [
        (log,                           ('2.6: PanYinhuSkin BodyC MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('40dea057', 'PanYinhuSkin.BodyC.MaterialMap.1024')),
    ],
    '40dea057': [
        (log,                           ('2.6: PanYinhuSkin BodyC MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('eb5755d6', 'PanYinhuSkin.BodyC.MaterialMap.2048')),
    ],

    # MARK: Piper派派
    #IB
    '940454ef': [(log, ('1.0: Piper Hair IB Hash',)), (add_ib_check_if_missing,)],
    '585da98b': [(log, ('1.0: Piper Body IB Hash',)), (add_ib_check_if_missing,)],
    'e11baad9': [(log, ('1.0: Piper Face IB Hash',)), (add_ib_check_if_missing,)],
    #VB
    '8b6b17f8': [(log, ('1.3 -> 1.4: Piper Hair Texcoord Hash',)), (update_hash, ('1c6d41af',)),],
    'b2f3e6aa': [(log, ('1.1 -> 1.2: Piper Body Position Hash',)), (update_hash, ('ffe8fea7',)),],
    'a0d146b3': [(log, ('1.1 -> 1.2: Piper Body Texcoord Hash',)), (update_hash, ('a011f94e',)),],
    'a011f94e': [(log, ('1.2 -> 1.3: Piper Body Texcoord Hash',)), (update_hash, ('6357b120',)),],
    '764276de': [(log, ('1.2 -> 1.3: Piper Body Blend Hash',)),    (update_hash, ('3d329807',)),],    

    #Remap
    # Reverted in 1.2
    # '8b6b17f8': [
    #     (log, ('1.0: -> 1.1: Piper Hair Texcoord Hash',)),
    #     (update_hash, ('fd1b9c29',)),
    #     (log, ('+ Remapping texcoord buffer from stride 20 to 32',)),
    #     (update_buffer_element_width, (('BBBB', 'ee', 'ff', 'ee'), ('ffff', 'ee', 'ff', 'ee'), '1.1')),
    #     (log, ('+ Setting texcoord vcolor alpha to 1',)),
    #     (update_buffer_element_value, (('ffff', 'ee', 'ff', 'ee'), ('xxx1', 'xx', 'xx', 'xx'), '1.1'))
    # ],

    'fd1b9c29': [
        (log, ('1.1 -> 1.2: Piper Hair Texcoord Hash',)),
        (update_hash, ('8b6b17f8',)),
        (log, ('+ Remapping texcoord buffer',)),
        (zzz_12_shrink_texcoord_color, ('1.2',))
    ],
    #Texture纹理
    # Face脸部
    '97a7862e': [(log, ('1.1 -> 1.2: Piper FaceA Diffuse 2048p Hash',)),   (update_hash, ('3b2eb1d9',))],
    '3b2eb1d9': [
        (log,                           ('1.2: Piper FaceA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('e11baad9', 'Piper.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('f1c8f946', '4b06ffe6'), 'Piper.FaceA.Diffuse.1024')),
    ],
    '4b06ffe6': [(log, ('1.1 -> 1.2: Piper FaceA Diffuse 1024p Hash',)),   (update_hash, ('f1c8f946',))],
    'f1c8f946': [
        (log,                           ('1.2: Piper FaceA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('e11baad9', 'Piper.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('3b2eb1d9', '97a7862e'), 'Piper.FaceA.Diffuse.2048')),
    ],
    # Hair头发
    '69ed4d11': [
        (log,                           ('1.0: Piper HairA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('940454ef', 'Piper.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('9b743eab', 'Piper.HairA.Diffuse.1024')),
    ],
    '9b743eab': [
        (log,                           ('1.0: Piper HairA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('940454ef', 'Piper.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('69ed4d11', 'Piper.HairA.Diffuse.2048')),
    ],
    '79953d32': [(log, ('1.7 -> 2.0: Piper HairA LightMap 2048p Hash',)), (update_hash, ('1146c5c3',))],
    '1146c5c3': [
        (log,                           ('1.0: Piper HairA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('940454ef', 'Piper.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('6bd15459','92acb4d4'), 'Piper.HairA.LightMap.1024')),
    ],
    '92acb4d4': [(log, ('1.7 -> 2.0: Piper HairA LightMap 1024p Hash',)), (update_hash, ('6bd15459',))],
    '6bd15459': [
        (log,                           ('1.0: Piper HairA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('940454ef', 'Piper.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('1146c5c3','79953d32'), 'Piper.HairA.LightMap.2048')),
    ],
    'b3034dff': [
        (log,                           ('1.0: Piper HairA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        ('940454ef', 'Piper.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('78c42c66', 'Piper.HairA.MaterialMap.1024')),
    ],
    '78c42c66': [
        (log,                           ('1.0: Piper HairA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        ('940454ef', 'Piper.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('b3034dff', 'Piper.HairA.MaterialMap.2048')),
    ],

    # Body身体
    'b4b74e7e': [(log, ('1.2 -> 1.3: Piper BodyA Diffuse 2048p Hash',)), (update_hash, ('fed40302',))],
    'fed40302': [
        (log,                           ('1.3: Piper BodyA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('585da98b', 'Piper.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('b450949d', '621564e5'), 'Piper.BodyA.Diffuse.1024')),
    ],
    '621564e5': [(log, ('1.2 -> 1.3: Piper BodyA Diffuse 1024p Hash',)), (update_hash, ('b450949d',))],
    'b450949d': [
        (log,                           ('1.3: Piper BodyA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('585da98b', 'Piper.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('fed40302', 'b4b74e7e'), 'Piper.BodyA.Diffuse.2048')),
    ],
    '9cc2aaa0': [(log, ('1.7 -> 2.0: Piper BodyA LightMap 2048p Hash',)), (update_hash, ('a32c39b9',))],
    'a32c39b9': [
        (log,                           ('1.0: Piper BodyA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('585da98b', 'Piper.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('7a281673','db9c7abf'), 'Piper.BodyA.LightMap.1024')),
    ],
    'db9c7abf': [(log, ('1.7 -> 2.0: Piper BodyA LightMap 1024p Hash',)), (update_hash, ('7a281673',))],
    '7a281673': [
        (log,                           ('1.0: Piper BodyA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('585da98b', 'Piper.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('a32c39b9','9cc2aaa0'), 'Piper.BodyA.LightMap.2048')),
    ],
    '7fdee30d': [
        (log,                           ('1.0: Piper BodyA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        ('585da98b', 'Piper.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('73e72a1e', 'Piper.BodyA.MaterialMap.1024')),
    ],
    '73e72a1e': [
        (log,                           ('1.0: Piper BodyA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        ('585da98b', 'Piper.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('7fdee30d', 'Piper.BodyA.MaterialMap.2048')),
    ],

    # MARK: Promeia普罗米娅
    #IB
    '31178971': [(log, ('2.81: Promeia Hair IB Hash',)), (add_ib_check_if_missing,)],
    'b386901d': [(log, ('3.0: Promeia Pinioned IB Hash',)), (add_ib_check_if_missing,)],
    '10c77d62': [(log, ('3.0: Promeia Torso IB Hash',)), (add_ib_check_if_missing,)],
    '0ae14c24': [(log, ('3.0: Promeia Clothes IB Hash',)), (add_ib_check_if_missing,)],
    'ec003379': [(log, ('3.0: Promeia Leg IB Hash',)), (add_ib_check_if_missing,)],
    'ef3c4506': [(log, ('3.0: Promeia Face IB Hash',)), (add_ib_check_if_missing,)],
    #VB
    '6cca89ab': [(log, ('2.8 -> 2.81: Promeia Hair IB Hash',)),      (update_hash, ('31178971',)),],
    '35096cb6': [(log, ('2.8 -> 2.81: Promeia Hair Position Hash',)),(update_hash, ('681aceaa',)),],
    '9c0aad96': [(log, ('2.8 -> 2.81: Promeia Hair Texcoord Hash',)),(update_hash, ('84d40d91',)),],
    '5a263750': [(log, ('2.8 -> 2.81: Promeia Hair Blend Hash',)),   (update_hash, ('3d4a4881',)),],

    'a633d5b7': [(log, ('2.8 -> 2.81: Promeia Pinioned IB Hash',)),      (update_hash, ('36e794ea',)),],
    #'dd86f5ae': [(log, ('2.8 -> 2.81: Promeia Pinioned Draw Hash',)),    (update_hash, ('19ad87f6',)),],
    'a7769c93': [(log, ('2.8 -> 2.81: Promeia Pinioned Position Hash',)),(update_hash, ('ffaa183a',)),],
    'bfcfb2f7': [(log, ('2.8 -> 2.81: Promeia Pinioned Texcoord Hash',)),(update_hash, ('2a9842a1',)),],
    '61c399b6': [(log, ('2.8 -> 2.81: Promeia Pinioned Blend Hash',)),   (update_hash, ('dae4abd0',)),],
    '36e794ea': [(log, ('2.81 -> 3.0: Promeia Pinioned IB Hash',)),      (update_hash, ('b386901d',)),],
    '19ad87f6': [(log, ('2.81 -> 3.0: Promeia Pinioned Draw Hash',)),    (update_hash, ('dd86f5ae',)),],
    'ffaa183a': [(log, ('2.81 -> 3.0: Promeia Pinioned Position Hash',)),(update_hash, ('68e2baef',)),],
    '2a9842a1': [(log, ('2.81 -> 3.0: Promeia Pinioned Texcoord Hash',)),(update_hash, ('6fe5f8c1',)),],
    'dae4abd0': [(log, ('2.81 -> 3.0: Promeia Pinioned Blend Hash',)),   (update_hash, ('112582ea',)),],

    '6abaa60a': [(log, ('2.8 -> 2.81: Promeia Torso IB Hash',)),      (update_hash, ('62a6b4bd',)),],
    '62a6b4bd': [(log, ('2.81 -> 3.0: Promeia Torso IB Hash',)),      (update_hash, ('10c77d62',)),],
    'b1ec331c': [(log, ('2.8 -> 2.81: Promeia Torso Texcoord Hash',)),(update_hash, ('d99d21e0',)),],
    'bca960d0': [(log, ('2.8 -> 2.81: Promeia Torso Blend Hash',)),   (update_hash, ('575d8b1b',)),],
    'd99d21e0': [(log, ('2.81 -> 3.0: Promeia Torso Texcoord Hash',)),(update_hash, ('1fc95f5b',)),],
    '575d8b1b': [(log, ('2.81 -> 3.0: Promeia Torso Blend Hash',)),   (update_hash, ('ee35cc06',)),],
    'bf938187': [(log, ('2.81 -> 3.0: Promeia Torso Position Hash',)),(update_hash, ('2dbfe8c9',)),],

    '68f34958': [(log, ('2.8 -> 2.81: Promeia Clothes IB Hash',)),      (update_hash, ('93f1f568',)),],
    '93f1f568': [(log, ('2.81 -> 3.0: Promeia Clothes IB Hash',)),      (update_hash, ('0ae14c24',)),],
    'd43597aa': [(log, ('2.8 -> 2.81: Promeia Clothes Position Hash',)),(update_hash, ('1d63183b',)),],
    '9f083955': [(log, ('2.8 -> 2.81: Promeia Clothes Texcoord Hash',)),(update_hash, ('826446a7',)),],
    '870f56b5': [(log, ('2.8 -> 2.81: Promeia Clothes Blend Hash',)),   (update_hash, ('58f42be3',)),],
    '1d63183b': [(log, ('2.81 -> 3.0: Promeia Clothes Position Hash',)),(update_hash, ('f6cc27b6',)),],
    '826446a7': [(log, ('2.81 -> 3.0: Promeia Clothes Texcoord Hash',)),(update_hash, ('bf00cc95',)),],
    '58f42be3': [(log, ('2.81 -> 3.0: Promeia Clothes Blend Hash',)),   (update_hash, ('4b0d6867',)),],

    '21871660': [(log, ('2.8 -> 2.81: Promeia Leg IB Hash',)),      (update_hash, ('fd054d1d',)),],
    'fd054d1d': [(log, ('2.81 -> 3.0: Promeia Leg IB Hash',)),      (update_hash, ('ec003379',)),],
    '595bd76e': [(log, ('2.8 -> 2.81: Promeia Leg Position Hash',)),(update_hash, ('0b822797',)),],
    '2918714e': [(log, ('2.8 -> 2.81: Promeia Leg Texcoord Hash',)),(update_hash, ('f5fd0e92',)),],
    'fd3c3d9f': [(log, ('2.8 -> 2.81: Promeia Leg Blend Hash',)),   (update_hash, ('9839b071',)),],
    '0b822797': [(log, ('2.81 -> 3.0: Promeia Leg Position Hash',)),(update_hash, ('4c1d0a70',)),],
    'f5fd0e92': [(log, ('2.81 -> 3.0: Promeia Leg Texcoord Hash',)),(update_hash, ('03d6f933',)),],
    '9839b071': [(log, ('2.81 -> 3.0: Promeia Leg Blend Hash',)),   (update_hash, ('65bba179',)),],

    'cb9d17fc': [(log, ('2.8 -> 2.81: Promeia Eyebrow IB Hash',)),      (update_hash, ('e032287a',)),],
    '3a00aa76': [(log, ('2.8 -> 2.81: Promeia Eyebrow Texcoord Hash',)),(update_hash, ('d3d65ca5',)),],

    '5ea47a32': [(log, ('2.8 -> 2.81: Promeia Face IB Hash',)),      (update_hash, ('ef3c4506',)),],
    #不再提供对脸部vb的修复，不建议对脸部模型进行修改，可能会导致脸部贴图错位
    #'b7a6479f': [(log, ('2.8 -> 2.81: Promeia Face Texcoord Hash',)),(update_hash, ('dcd61276',)),],
    #'5ff41c34': [(log, ('2.8 -> 2.81: Promeia Face Blend Hash',)),   (update_hash, ('bf5b785d',)),],

    '947ceb88': [(log, ('2.8 -> 2.81: Promeia Weapon IB Hash',)),      (update_hash, ('8995db58',)),],
    '7d76d686': [(log, ('2.8 -> 2.81: Promeia Weapon Draw Hash',)),    (update_hash, ('0a06059e',)),],
    '2f3a560d': [(log, ('2.8 -> 2.81: Promeia Weapon Position Hash',)),(update_hash, ('d242b77a',)),],
    '23587131': [(log, ('2.8 -> 2.81: Promeia Weapon Texcoord Hash',)),(update_hash, ('f2f5bd28',)),],
    '21ac80fa': [(log, ('2.8 -> 2.81: Promeia Weapon Blend Hash',)),   (update_hash, ('a864dc82',)),],
    '35ecba91': [(log, ('2.81 -> 3.0: Promeia Weapon Position Hash',)),(update_hash, ('d242b77a',)),],
    '064658e2': [(log, ('2.81 -> 3.0: Promeia Weapon Texcoord Hash',)),(update_hash, ('f2f5bd28',)),],

    'de6eb63b': [(log, ('2.8 -> 2.81: Promeia Shadow IB Hash',)),      (update_hash, ('ff223b2c',)),],

    #Texture纹理
    # Face脸部
    '9b293811': [
        (log,                           ('2.8: Promeia FaceA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('328fa0cf', 'Promeia.FaceA.Diffuse.1024')),
    ],
    '328fa0cf': [
        (log,                           ('2.8: Promeia FaceA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('9b293811', 'Promeia.FaceA.Diffuse.2048')),
    ],

    # Hair头发
    'c96de436': [
        (log,                           ('2.8: Promeia HairA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('a0add414', 'Promeia.HairA.Diffuse.1024')),
    ],
    'a0add414': [
        (log,                           ('2.8: Promeia HairA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('c96de436', 'Promeia.HairA.Diffuse.2048')),
    ],
    'e34356a6': [
        (log,                           ('2.8: Promeia HairA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('5c509f54', 'Promeia.HairA.LightMap.1024')),
    ],
    '5c509f54': [
        (log,                           ('2.8: Promeia HairA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('e34356a6', 'Promeia.HairA.LightMap.2048')),
    ],
    '6bed1450': [
        (log,                           ('2.8: Promeia HairA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('1f96c5d7', 'Promeia.HairA.MaterialMap.1024')),
    ],
    '1f96c5d7': [
        (log,                           ('2.8: Promeia HairA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('6bed1450', 'Promeia.HairA.MaterialMap.2048')),
    ],

    # Body身体
    'ae109401': [
        (log,                           ('2.8: Promeia BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('7d2d3a9e', 'Promeia.BodyA.Diffuse.1024')),
    ],
    '7d2d3a9e': [
        (log,                           ('2.8: Promeia BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('ae109401', 'Promeia.BodyA.Diffuse.2048')),
    ],
    '3864f20c': [
        (log,                           ('2.8: Promeia BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('70ca6de8', 'Promeia.BodyA.LightMap.1024')),
    ],
    '70ca6de8': [
        (log,                           ('2.8: Promeia BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('3864f20c', 'Promeia.BodyA.LightMap.2048')),
    ],
    'd57df6aa': [
        (log,                           ('2.8: Promeia BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('af976ad8', 'Promeia.BodyA.MaterialMap.1024')),
    ],
    'af976ad8': [
        (log,                           ('2.8: Promeia BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('d57df6aa', 'Promeia.BodyA.MaterialMap.2048')),
    ],

    # Clothes
    'b9367016': [(log, ('2.8 -> 3.0: Promeia ClothesA Diffuse 2048p Hash',)), (update_hash, ('e1492a53',))],
    'e1492a53': [
        (log,                           ('2.8: Promeia ClothesA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   (('406b1373','47d294f4'), 'Promeia.ClothesA.Diffuse.1024')),
    ],
    '406b1373': [(log, ('2.8 -> 3.0: Promeia ClothesA Diffuse 1024p Hash',)), (update_hash, ('47d294f4',))],
    '47d294f4': [
        (log,                           ('2.8: Promeia ClothesA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   (('b9367016','e1492a53'), 'Promeia.ClothesA.Diffuse.2048')),
    ],
    'd743acd0': [(log, ('2.8 -> 3.0: Promeia ClothesA LightMap 2048p Hash',)), (update_hash, ('9bf7f5cc',))],
    '9bf7f5cc': [
        (log,                           ('2.8: Promeia ClothesA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   (('044d2d39','562616d5'), 'Promeia.ClothesA.LightMap.1024')),
    ],
    '044d2d39': [(log, ('2.8 -> 3.0: Promeia ClothesA LightMap 1024p Hash',)), (update_hash, ('562616d5',))],
    '562616d5': [
        (log,                           ('2.8: Promeia ClothesA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   (('d743acd0','9bf7f5cc'), 'Promeia.ClothesA.LightMap.2048')),
    ],
    '31d7cbad': [(log, ('2.8 -> 3.0: Promeia ClothesA MaterialMap 2048p Hash',)), (update_hash, ('d37b40a9',))],
    'd37b40a9': [
        (log,                           ('2.8: Promeia ClothesA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   (('01a5ba27','73aaae54'), 'Promeia.ClothesA.MaterialMap.1024')),
    ],
    '01a5ba27': [(log, ('2.8 -> 3.0: Promeia ClothesA MaterialMap 1024p Hash',)), (update_hash, ('73aaae54',))],
    '73aaae54': [
        (log,                           ('2.8: Promeia ClothesA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   (('31d7cbad','d37b40a9'), 'Promeia.ClothesA.MaterialMap.2048')),
    ],

    # Weapon
    'd1399215': [(log, ('2.8 -> 3.0: Promeia WeaponA Diffuse 2048p Hash',)), (update_hash, ('328135c5',))],
    '328135c5': [
        (log,                           ('2.8: Promeia WeaponA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   (('138bcaa1','7750fc88'), 'Promeia.WeaponA.Diffuse.1024')),
    ],
    '138bcaa1': [(log, ('2.8 -> 3.0: Promeia WeaponA Diffuse 1024p Hash',)), (update_hash, ('7750fc88',))],
    '7750fc88': [
        (log,                           ('2.8: Promeia WeaponA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   (('d1399215','328135c5'), 'Promeia.WeaponA.Diffuse.2048')),
    ],
    '369f0efd': [(log, ('2.8 -> 3.0: Promeia WeaponA LightMap 2048p Hash',)), (update_hash, ('82f4146a',))],
    '82f4146a': [
        (log,                           ('2.8: Promeia WeaponA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   (('5e59380e','a1988612'), 'Promeia.WeaponA.LightMap.1024')),
    ],
    '5e59380e': [(log, ('2.8 -> 3.0: Promeia WeaponA LightMap 1024p Hash',)), (update_hash, ('a1988612',))],
    'a1988612': [
        (log,                           ('2.8: Promeia WeaponA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   (('369f0efd','82f4146a'), 'Promeia.WeaponA.LightMap.2048')),
    ],
    'a179a69c': [(log, ('2.8 -> 3.0: Promeia WeaponA MaterialMap 2048p Hash',)), (update_hash, ('d672b87c',))],
    'd672b87c': [
        (log,                           ('2.8: Promeia WeaponA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   (('09271c02','7559d574'), 'Promeia.WeaponA.MaterialMap.1024')),
    ],
    '09271c02': [(log, ('2.8 -> 3.0: Promeia WeaponA MaterialMap 1024p Hash',)), (update_hash, ('7559d574',))],
    '7559d574': [
        (log,                           ('2.8: Promeia WeaponA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   (('a179a69c','d672b87c'), 'Promeia.WeaponA.MaterialMap.2048')),
    ],

    # MARK: Pulchra波可娜
    #IB
    'bd385763': [(log, ('1.6: Pulchra Hair Body IB Hash',)), (add_ib_check_if_missing,)],
    '5b30f4da': [(log, ('1.6: Pulchra Mask IB Hash',)), (add_ib_check_if_missing,)],
    '62de5837': [(log, ('1.6: Pulchra Face IB Hash',)), (add_ib_check_if_missing,)],
    #VB
    #Texture纹理
    # Face脸部
    '1626aafe': [
        (log,                           ('1.6: Pulchra FaceA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('62de5837', 'Pulchra.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('32f923f1', 'Pulchra.FaceA.Diffuse.1024')),
    ],
    '32f923f1': [
        (log,                           ('1.6: Pulchra FaceA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('62de5837', 'Pulchra.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('1626aafe', 'Pulchra.FaceA.Diffuse.2048')),
    ],

    # Mask
    '320a1179': [(log, ('1.7 -> 2.0: Pulchra MaskA MaterialMap 2048p Hash',)), (update_hash, ('6b141146',))],
    '6b141146': [
        (log,                           ('1.6: Pulchra MaskA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   (('820ded20', 'f1ee6734'), 'Pulchra.MaskA.MaterialMap.1024')),
    ],
    '820ded20': [(log, ('1.7 -> 2.0: Pulchra MaskA MaterialMap 1024p Hash',)), (update_hash, ('f1ee6734',))],
    'f1ee6734': [
        (log,                           ('1.6: Pulchra MaskA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   (('320a1179', '6b141146'), 'Pulchra.MaskA.MaterialMap.2048')),
    ],

    # Hair头发
    '57be79d6': [
        (log,                           ('1.6: Pulchra HairA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('fb0a816a', 'Pulchra.HairA.Diffuse.1024')),
    ],
    'fb0a816a': [
        (log,                           ('1.6: Pulchra HairA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('57be79d6', 'Pulchra.HairA.Diffuse.2048')),
    ],
    '12c44063': [
        (log,                           ('1.6: Pulchra HairA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('f475e822', 'Pulchra.HairA.LightMap.1024')),
    ],
    'f475e822': [
        (log,                           ('1.6: Pulchra HairA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('12c44063', 'Pulchra.HairA.LightMap.2048')),
    ],
    'a553df20': [
        (log,                           ('1.6: Pulchra HairA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('64d75415', 'Pulchra.HairA.MaterialMap.1024')),
    ],
    '64d75415': [
        (log,                           ('1.6: Pulchra HairA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('a553df20', 'Pulchra.HairA.MaterialMap.2048')),
    ],

    # Body身体
    '7fc03353': [
        (log,                           ('1.6: Pulchra BodyA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('bd385763', 'Pulchra.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('bf7eba0f', 'Pulchra.BodyA.Diffuse.1024')),
    ],
    'bf7eba0f': [
        (log,                           ('1.6: Pulchra BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('7fc03353', 'Pulchra.BodyA.Diffuse.2048')),
    ],
    'd8462af0': [
        (log,                           ('1.6: Pulchra BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('47040200', 'Pulchra.BodyA.LightMap.1024')),
    ],
    '47040200': [
        (log,                           ('1.6: Pulchra BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('d8462af0', 'Pulchra.BodyA.LightMap.2048')),
    ],
    'd404b789': [
        (log,                           ('1.6: Pulchra BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('a66a11d0', 'Pulchra.BodyA.MaterialMap.1024')),
    ],
    'a66a11d0': [
        (log,                           ('1.6: Pulchra BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('d404b789', 'Pulchra.BodyA.MaterialMap.2048')),
    ],

    # MARK: Pyrois佩洛伊斯
    #IB
    '0a7c1023': [(log, ('3.0: Pyrois Arm IB Hash',)), (add_ib_check_if_missing,)],
    'd347d859': [(log, ('3.0: Pyrois Body IB Hash',)), (add_ib_check_if_missing,)],
    'd98c8923': [(log, ('3.0: Pyrois Hair IB Hash',)), (add_ib_check_if_missing,)],
    #VB
    #Texture纹理
    # Body身体
    'ef11e537': [
        (log,                           ('3.0: Pyrois BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('1331e7ee', 'Pyrois.BodyA.Diffuse.1024')),
    ],
    '1331e7ee': [
        (log,                           ('3.0: Pyrois BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('ef11e537', 'Pyrois.BodyA.Diffuse.2048')),
    ],
    'c7a6063b': [
        (log,                           ('3.0: Pyrois BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('3ed5431d', 'Pyrois.BodyA.LightMap.1024')),
    ],
    '3ed5431d': [
        (log,                           ('3.0: Pyrois BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('c7a6063b', 'Pyrois.BodyA.LightMap.2048')),
    ],
    'd81be7b3': [
        (log,                           ('3.0: Pyrois BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('17c1a8e2', 'Pyrois.BodyA.MaterialMap.1024')),
    ],
    '17c1a8e2': [
        (log,                           ('3.0: Pyrois BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('d81be7b3', 'Pyrois.BodyA.MaterialMap.2048')),
    ],
    
    # Hair头发
    '28b3c245': [
        (log,                           ('3.0: Pyrois HairA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('bee6766b', 'Pyrois.HairA.Diffuse.1024')),
    ],
    'bee6766b': [
        (log,                           ('3.0: Pyrois HairA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('28b3c245', 'Pyrois.HairA.Diffuse.2048')),
    ],
    '0d24e396': [
        (log,                           ('3.0: Pyrois HairA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('6bec1d56', 'Pyrois.HairA.LightMap.1024')),
    ],
    '6bec1d56': [
        (log,                           ('3.0: Pyrois HairA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('0d24e396', 'Pyrois.HairA.LightMap.2048')),
    ],
    'bd5b0984': [
        (log,                           ('3.0: Pyrois HairA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('7405e2d5', 'Pyrois.HairA.MaterialMap.1024')),
    ],
    '7405e2d5': [
        (log,                           ('3.0: Pyrois HairA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('bd5b0984', 'Pyrois.HairA.MaterialMap.2048')),
    ],
    


    # MARK: Qingyi青衣
    '3cacba0a': [(log, ('1.1: Qingyi Hair IB Hash',)), (add_ib_check_if_missing,)],
    '195857d8': [(log, ('1.1: Qingyi Body IB Hash',)), (add_ib_check_if_missing,)],
    'f6e96452': [(log, ('1.1: Qingyi Face IB Hash',)), (add_ib_check_if_missing,)],
    #VB
    #不再提供对脸部vb的修复，不建议对脸部模型进行修改，可能会导致脸部贴图错位
    #Face VB取消更新，因为与零号安比冲突
    #'6a492df0': [(log, ('3.1: Qingyi Face-脸 texcoord_vb Hash',)), (update_hash, ('db1f2dfa',))],
    #Remap
    '0643440c': [
        (log, ('1.1 -> 1.2: Qingyi Hair Texcoord Hash',)),
        (update_hash, ('53a2b66e',)),
        (log, ('+ Remapping texcoord buffer',)),
        (zzz_12_shrink_texcoord_color, ('1.2',))
    ],

    #Texture纹理
    # Face脸部
    '0b75cd32': [
        (log,                           ('1.1: Qingyi FaceA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('f6e96452', 'Qingyi.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('a58b5444', 'Qingyi.FaceA.Diffuse.1024')),
    ],
    'a58b5444': [
        (log,                           ('1.1: Qingyi FaceA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('f6e96452', 'Qingyi.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('0b75cd32', 'Qingyi.FaceA.Diffuse.2048')),
    ],

    # Hair头发
    '3212a0ca': [
        (log,                           ('1.1: Qingyi HairA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('3cacba0a', 'Qingyi.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('a472db9a', 'Qingyi.HairA.Diffuse.1024')),
    ],
    'a472db9a': [
        (log,                           ('1.1: Qingyi HairA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('3cacba0a', 'Qingyi.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('3212a0ca', 'Qingyi.HairA.Diffuse.2048')),
    ],
    '6e3ac847': [
        (log,                           ('1.1: Qingyi HairA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('3cacba0a', 'Qingyi.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('683414c1', 'Qingyi.HairA.LightMap.1024')),
    ],
    '683414c1': [
        (log,                           ('1.1: Qingyi HairA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('3cacba0a', 'Qingyi.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('6e3ac847', 'Qingyi.HairA.LightMap.2048')),
    ],
    '4a77fd3b': [
        (log,                           ('1.1: Qingyi HairA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        ('3cacba0a', 'Qingyi.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('bfefa200', 'Qingyi.HairA.MaterialMap.1024')),
    ],
    'bfefa200': [
        (log,                           ('1.1: Qingyi HairA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        ('3cacba0a', 'Qingyi.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('4a77fd3b', 'Qingyi.HairA.MaterialMap.2048')),
    ],

    # Body身体
    '1fa7e18e': [
        (log,                           ('1.1: Qingyi BodyA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('195857d8', 'Qingyi.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('aa3c1147', 'Qingyi.BodyA.Diffuse.1024')),
    ],
    'aa3c1147': [
        (log,                           ('1.1: Qingyi BodyA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('195857d8', 'Qingyi.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('1fa7e18e', 'Qingyi.BodyA.Diffuse.2048')),
    ],
    '35c2a022': [
        (log,                           ('1.1: Qingyi BodyA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('195857d8', 'Qingyi.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('4a484257', 'Qingyi.BodyA.LightMap.1024')),
    ],
    '4a484257': [
        (log,                           ('1.1: Qingyi BodyA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('195857d8', 'Qingyi.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('35c2a022', 'Qingyi.BodyA.LightMap.2048')),
    ],
    '41054bb6': [
        (log,                           ('1.1: Qingyi BodyA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        ('195857d8', 'Qingyi.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('4e561ee5', 'Qingyi.BodyA.MaterialMap.1024')),
    ],
    '4e561ee5': [
        (log,                           ('1.1: Qingyi BodyA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        ('195857d8', 'Qingyi.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('41054bb6', 'Qingyi.BodyA.MaterialMap.2048')),
    ],

    # MARK: Remielle蕾米埃尔
    '28e05a59': [(log, ('3.2: Remielle Body-身体 IB Hash',)), (add_ib_check_if_missing,)],
    '7fbbcf0d': [(log, ('3.1: Remielle Face IB Hash',)), (add_ib_check_if_missing,)],
    '789ae812': [(log, ('3.1: Remielle Hair IB Hash',)), (add_ib_check_if_missing,)],
    'fe9fc31a': [(log, ('3.1: Remielle Leg IB Hash',)), (add_ib_check_if_missing,)],
    '9004a39a': [(log, ('3.1: Remielle Wings IB Hash',)), (add_ib_check_if_missing,)],
    #VB
    '7a92a10a': [(log, ('3.2: Remielle Body-身体 draw_vb Hash',)), (update_hash, ('97664f2f',))],
    '679a1bd8': [(log, ('3.2: Remielle Body-身体 position_vb Hash',)), (update_hash, ('d16f6790',))],
    '9e33a8b6': [(log, ('3.2: Remielle Body-身体 texcoord_vb Hash',)), (update_hash, ('b943ec9e',))],
    '9e8a27ae': [(log, ('3.2: Remielle Body-身体 blend_vb Hash',)), (update_hash, ('da54a57a',))],
    '785b21f5': [
        (log, ('3.1 -> 3.2: Remielle Body IB Hash',)),
        (update_hash, ('28e05a59',)),
        (transfer_indexed_sections, {
            'src_indices': ['0', '57612'],
            'trg_indices': ['0', '59094'],
        })],
    #Texture纹理
    'baf9e1be': [
        (log,                           ('3.1: Remielle Face-脸 Diffuse Hash',)),
        (multiply_section_if_missing,   ('5bc2bbdd', 'Remielle.FaceA.Diffuse.2048')),
    ],
    '5bc2bbdd': [
        (log,                           ('3.1: Remielle Face-脸 Diffuse Hash',)),
        (multiply_section_if_missing,   ('baf9e1be', 'Remielle.FaceA.Diffuse.1024')),
    ],
    # Body
    'e51be5d1': [
        (log,                           ('3.1: Remielle BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('d770d330', 'Remielle.BodyA.Diffuse.1024')),
    ],
    'd770d330': [
        (log,                           ('3.1: Remielle BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('e51be5d1', 'Remielle.BodyA.Diffuse.2048')),
    ],
    '380d7bcf': [
        (log,                           ('3.1: Remielle BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('b95031e2', 'Remielle.BodyA.LightMap.1024')),
    ],
    'b95031e2': [
        (log,                           ('3.1: Remielle BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('380d7bcf', 'Remielle.BodyA.LightMap.2048')),
    ],
    '61c42d63': [
        (log,                           ('3.1: Remielle BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('ed6ca67a', 'Remielle.BodyA.MaterialMap.1024')),
    ],
    'ed6ca67a': [
        (log,                           ('3.1: Remielle BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('61c42d63', 'Remielle.BodyA.MaterialMap.2048')),
    ],
        
    # Hair
    '578239d7': [
        (log,                           ('3.1: Remielle HairA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('8a619774', 'Remielle.HairA.Diffuse.1024')),
    ],
    '8a619774': [
        (log,                           ('3.1: Remielle HairA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('578239d7', 'Remielle.HairA.Diffuse.2048')),
    ],
    '6f826e7d': [
        (log,                           ('3.1: Remielle HairA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('45bb8a18', 'Remielle.HairA.LightMap.1024')),
    ],
    '45bb8a18': [
        (log,                           ('3.1: Remielle HairA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('6f826e7d', 'Remielle.HairA.LightMap.2048')),
    ],
    'b5a12580': [
        (log,                           ('3.1: Remielle HairA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('8b8df55e', 'Remielle.HairA.MaterialMap.1024')),
    ],
    '8b8df55e': [
        (log,                           ('3.1: Remielle HairA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('b5a12580', 'Remielle.HairA.MaterialMap.2048')),
    ],
    
    # Leg
    '6538d30d': [
        (log,                           ('3.1: Remielle LegA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('49ac9d9e', 'Remielle.LegA.Diffuse.1024')),
    ],
    '49ac9d9e': [
        (log,                           ('3.1: Remielle LegA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('6538d30d', 'Remielle.LegA.Diffuse.2048')),
    ],
    '4049331b': [
        (log,                           ('3.1: Remielle LegA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('95db220c', 'Remielle.LegA.LightMap.1024')),
    ],
    '95db220c': [
        (log,                           ('3.1: Remielle LegA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('4049331b', 'Remielle.LegA.LightMap.2048')),
    ],
    'cdc2accb': [
        (log,                           ('3.1: Remielle LegA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('1c782fe7', 'Remielle.LegA.MaterialMap.1024')),
    ],
    '1c782fe7': [
        (log,                           ('3.1: Remielle LegA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('cdc2accb', 'Remielle.LegA.MaterialMap.2048')),
    ],
    
    # Wings
    '80ad86c3': [
        (log,                           ('3.1: Remielle WingsA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('cdc91dce', 'Remielle.WingsA.Diffuse.1024')),
    ],
    'cdc91dce': [
        (log,                           ('3.1: Remielle WingsA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('80ad86c3', 'Remielle.WingsA.Diffuse.2048')),
    ],
    '04497af6': [
        (log,                           ('3.1: Remielle WingsA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('128e607f', 'Remielle.WingsA.LightMap.1024')),
    ],
    '128e607f': [
        (log,                           ('3.1: Remielle WingsA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('04497af6', 'Remielle.WingsA.LightMap.2048')),
    ],
    '0ec88318': [
        (log,                           ('3.1: Remielle WingsA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('c23e467e', 'Remielle.WingsA.MaterialMap.1024')),
    ],
    'c23e467e': [
        (log,                           ('3.1: Remielle WingsA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('0ec88318', 'Remielle.WingsA.MaterialMap.2048')),
    ],

    # MARK: RemielleSkinBlack蕾米埃尔黑皮肤
    '92cb56c9': [(log, ('3.2: RemielleSkinBlack Body-身体 IB Hash',)), (add_ib_check_if_missing,)],
    '24a512cb': [(log, ('3.2: RemielleSkinBlack Leg-腿部 IB Hash',)), (add_ib_check_if_missing,)],
    #VB
    '22ec622c': [(log, ('3.1 -> 3.2: RemielleSkinBlack Body-身体 draw_vb Hash',)), (update_hash, ('6a0d36f2',))],
    '554d46cf': [(log, ('3.1 -> 3.2: RemielleSkinBlack Body-身体 position_vb Hash',)), (update_hash, ('0929171b',))],
    '5dcc6ee1': [(log, ('3.1 -> 3.2: RemielleSkinBlack Body-身体 texcoord_vb Hash',)), (update_hash, ('c24cc6a1',))],
    '7f6fe876': [(log, ('3.1 -> 3.2: RemielleSkinBlack Body-身体 blend_vb Hash',)), (update_hash, ('93b69961',))],
    'f57f3e40': [
        (log, ('3.1 -> 3.2: RemielleSkinBlack Body IB Hash',)),
        (update_hash, ('92cb56c9',)),
        (transfer_indexed_sections, {
            'src_indices': ['0', '64092'],
            'trg_indices': ['0', '64626'],
        })],

    '96dc0a8e': [(log, ('3.1 -> 3.2: RemielleSkinBlack Leg-腿部 draw_vb Hash',)), (update_hash, ('ea50e1d1',))],
    'fa9635bc': [(log, ('3.1 -> 3.2: RemielleSkinBlack Leg-腿部 position_vb Hash',)), (update_hash, ('11fbd4a3',))],
    '7c0db158': [(log, ('3.1 -> 3.2: RemielleSkinBlack Leg-腿部 texcoord_vb Hash',)), (update_hash, ('14ab0adc',))],
    'ff05e5f9': [(log, ('3.1 -> 3.2: RemielleSkinBlack Leg-腿部 blend_vb Hash',)), (update_hash, ('3841a909',))],
    '09a51ed3': [
        (log, ('3.1 -> 3.2: RemielleSkinBlack Leg IB Hash',)),
        (update_hash, ('24a512cb',)),
        (transfer_indexed_sections, {
            'src_indices': ['0', '15618'],
            'trg_indices': ['0', '15546'],
        })],
    #Texture纹理
    # Body
    '0e408177': [(log, ('3.1 -> 3.2: RemielleSkinBlack BodyA Diffuse 2048p Hash',)), (update_hash, ('bb0f08b9',))],
    'bb0f08b9': [
        (log,                           ('3.2: RemielleSkinBlack BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   (('abb0d69d','578353ea'), 'RemielleSkinBlack.BodyA.Diffuse.1024')),
    ],
    'abb0d69d': [(log, ('3.1 -> 3.2: RemielleSkinBlack BodyA Diffuse 1024p Hash',)), (update_hash, ('578353ea',))],
    '578353ea': [
        (log,                           ('3.2: RemielleSkinBlack BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   (('0e408177','bb0f08b9'), 'RemielleSkinBlack.BodyA.Diffuse.2048')),
    ],
    '6102ae18': [(log, ('3.1 -> 3.2: RemielleSkinBlack BodyA LightMap 2048p Hash',)), (update_hash, ('0e9d14dc',))],
    '0e9d14dc': [
        (log,                           ('3.2: RemielleSkinBlack BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   (('2aab9aa7','312bbc0c'), 'RemielleSkinBlack.BodyA.LightMap.1024')),
    ],
    '2aab9aa7': [(log, ('3.1 -> 3.2: RemielleSkinBlack BodyA LightMap 1024p Hash',)), (update_hash, ('312bbc0c',))],
    '312bbc0c': [
        (log,                           ('3.2: RemielleSkinBlack BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   (('6102ae18','0e9d14dc'), 'RemielleSkinBlack.BodyA.LightMap.2048')),
    ],
    'cccb8109': [(log, ('3.1 -> 3.2: RemielleSkinBlack BodyA MaterialMap 2048p Hash',)), (update_hash, ('8240c688',))],
    '8240c688': [
        (log,                           ('3.2: RemielleSkinBlack BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   (('e9f33a20','2367a92b'), 'RemielleSkinBlack.BodyA.MaterialMap.1024')),
    ],
    'e9f33a20': [(log, ('3.1 -> 3.2: RemielleSkinBlack BodyA MaterialMap 1024p Hash',)), (update_hash, ('2367a92b',))],
    '2367a92b': [
        (log,                           ('3.2: RemielleSkinBlack BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   (('cccb8109','8240c688'), 'RemielleSkinBlack.BodyA.MaterialMap.2048')),
    ],
    
    # Leg
    '877b0ce6': [(log, ('3.1 -> 3.2: RemielleSkinBlack LegA Diffuse 2048p Hash',)), (update_hash, ('017c13e4',))],
    '017c13e4': [
        (log,                           ('3.2: RemielleSkinBlack LegA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   (('4c49a23c','d0eb079f'), 'RemielleSkinBlack.LegA.Diffuse.1024')),
    ],
    '4c49a23c': [(log, ('3.1 -> 3.2: RemielleSkinBlack LegA Diffuse 1024p Hash',)), (update_hash, ('d0eb079f',))],
    'd0eb079f': [
        (log,                           ('3.2: RemielleSkinBlack LegA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   (('877b0ce6','017c13e4'), 'RemielleSkinBlack.LegA.Diffuse.2048')),
    ],
    'baeb2662': [(log, ('3.1 -> 3.2: RemielleSkinBlack LegA LightMap 2048p Hash',)), (update_hash, ('0a902460',))],
    '0a902460': [
        (log,                           ('3.2: RemielleSkinBlack LegA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   (('17b9c313','b9a73372'), 'RemielleSkinBlack.LegA.LightMap.1024')),
    ],
    '17b9c313': [(log, ('3.1 -> 3.2: RemielleSkinBlack LegA LightMap 1024p Hash',)), (update_hash, ('b9a73372',))],
    'b9a73372': [
        (log,                           ('3.2: RemielleSkinBlack LegA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   (('baeb2662','0a902460'), 'RemielleSkinBlack.LegA.LightMap.2048')),
    ],
    '3b0c9e0a': [(log, ('3.1 -> 3.2: RemielleSkinBlack LegA MaterialMap 2048p Hash',)), (update_hash, ('fb096287',))],
    'fb096287': [
        (log,                           ('3.2: RemielleSkinBlack LegA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   (('2dce69bd','0b54d931'), 'RemielleSkinBlack.LegA.MaterialMap.1024')),
    ],
    '2dce69bd': [(log, ('3.1 -> 3.2: RemielleSkinBlack LegA MaterialMap 1024p Hash',)), (update_hash, ('0b54d931',))],
    '0b54d931': [
        (log,                           ('3.2: RemielleSkinBlack LegA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   (('3b0c9e0a','fb096287'), 'RemielleSkinBlack.LegA.MaterialMap.2048')),
    ],
    
    # Wings
    '677ec0d0': [
        (log,                           ('3.1: RemielleSkinBlack WingsA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('b8574ee2', 'RemielleSkinBlack.WingsA.Diffuse.1024')),
    ],
    'b8574ee2': [
        (log,                           ('3.1: RemielleSkinBlack WingsA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('677ec0d0', 'RemielleSkinBlack.WingsA.Diffuse.2048')),
    ],

    # MARK: RemielleSkinWhite蕾米埃尔白皮肤
    '2cd6516a': [(log, ('3.2: RemielleSkinWhite Body-身体 IB Hash',)), (add_ib_check_if_missing,)],
    'b1870eee': [(log, ('3.1: RemielleSkinWhite Leg IB Hash',)), (add_ib_check_if_missing,)],
    #VB
    '48288582': [(log, ('3.1 -> 3.2: RemielleSkinWhite Body-身体 draw_vb Hash',)), (update_hash, ('df41c403',))],
    '13c77c3a': [(log, ('3.1 -> 3.2: RemielleSkinWhite Body-身体 position_vb Hash',)), (update_hash, ('22d04ad5',))],
    'c55c57ce': [(log, ('3.1 -> 3.2: RemielleSkinWhite Body-身体 texcoord_vb Hash',)), (update_hash, ('d637a74d',))],
    '9bca83d8': [(log, ('3.1 -> 3.2: RemielleSkinWhite Body-身体 blend_vb Hash',)), (update_hash, ('5ec5e567',))],
    '241deac5': [
        (log, ('3.1 -> 3.2: RemielleSkinWhite Body IB Hash',)),
        (update_hash, ('2cd6516a',)),
        (transfer_indexed_sections, {
            'src_indices': ['0', '56376'],
            'trg_indices': ['0', '56736'],
        })],
    #Texture纹理
    # Body
    '686a0805': [
        (log,                           ('3.1: RemielleSkinWhite BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('fb0f2f5d', 'RemielleSkinWhite.BodyA.Diffuse.1024')),
    ],
    'fb0f2f5d': [
        (log,                           ('3.1: RemielleSkinWhite BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('686a0805', 'RemielleSkinWhite.BodyA.Diffuse.2048')),
    ],
    'a255803d': [
        (log,                           ('3.1: RemielleSkinWhite BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('c4d1c25b', 'RemielleSkinWhite.BodyA.LightMap.1024')),
    ],
    'c4d1c25b': [
        (log,                           ('3.1: RemielleSkinWhite BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('a255803d', 'RemielleSkinWhite.BodyA.LightMap.2048')),
    ],
    'fb91abe9': [
        (log,                           ('3.1: RemielleSkinWhite BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('d52ee692', 'RemielleSkinWhite.BodyA.MaterialMap.1024')),
    ],
    'd52ee692': [
        (log,                           ('3.1: RemielleSkinWhite BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('fb91abe9', 'RemielleSkinWhite.BodyA.MaterialMap.2048')),
    ],
    
    # Leg
    '517d9d7c': [
        (log,                           ('3.1: RemielleSkinWhite LegA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('1fb64395', 'RemielleSkinWhite.LegA.Diffuse.1024')),
    ],
    '1fb64395': [
        (log,                           ('3.1: RemielleSkinWhite LegA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('517d9d7c', 'RemielleSkinWhite.LegA.Diffuse.2048')),
    ],
    '6a673bda': [
        (log,                           ('3.1: RemielleSkinWhite LegA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('63ef7922', 'RemielleSkinWhite.LegA.LightMap.1024')),
    ],
    '63ef7922': [
        (log,                           ('3.1: RemielleSkinWhite LegA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('6a673bda', 'RemielleSkinWhite.LegA.LightMap.2048')),
    ],
    'f87f83d9': [
        (log,                           ('3.1: RemielleSkinWhite LegA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('ac5220b6', 'RemielleSkinWhite.LegA.MaterialMap.1024')),
    ],
    'ac5220b6': [
        (log,                           ('3.1: RemielleSkinWhite LegA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('f87f83d9', 'RemielleSkinWhite.LegA.MaterialMap.2048')),
    ],
    


    # MARK: Rina丽娜
    #IB
    'cdb2cc7d': [(log, ('1.0: Rina Hair IB Hash',)), (add_ib_check_if_missing,)],
    '2825da1e': [(log, ('1.0: Rina Body IB Hash',)), (add_ib_check_if_missing,)],
    '9f90cfaa': [(log, ('1.0: Rina Face IB Hash',)), (add_ib_check_if_missing,)],
    #VB

    #Texture纹理
    # Face脸部
    '802a3281': [
        (log,                           ('1.0: Rina FaceA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('9f90cfaa', 'Rina.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('7ecc44ce', 'Rina.FaceA.Diffuse.1024')),
    ],
    '7ecc44ce': [
        (log,                           ('1.0: Rina FaceA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('9f90cfaa', 'Rina.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('802a3281', 'Rina.FaceA.Diffuse.2048')),
    ],

    # Hair头发
    'eb5d9d1c': [
        (log,                           ('1.0: Rina HairA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('cdb2cc7d', 'Rina.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('4b005a79', 'Rina.HairA.Diffuse.1024')),
    ],
    '4b005a79': [
        (log,                           ('1.0: Rina HairA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('cdb2cc7d', 'Rina.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('eb5d9d1c', 'Rina.HairA.Diffuse.2048')),
    ],
    '1145d2b8': [
        (log,                           ('1.0: Rina HairA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('cdb2cc7d', 'Rina.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('fb61499f', 'Rina.HairA.LightMap.1024')),
    ],
    'fb61499f': [
        (log,                           ('1.0: Rina HairA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('cdb2cc7d', 'Rina.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('1145d2b8', 'Rina.HairA.LightMap.2048')),
    ],
    '82153e28': [
        (log,                           ('1.0: Rina HairA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        ('cdb2cc7d', 'Rina.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('ea08fd96', 'Rina.HairA.MaterialMap.1024')),
    ],
    'ea08fd96': [
        (log,                           ('1.0: Rina HairA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        ('cdb2cc7d', 'Rina.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('82153e28', 'Rina.HairA.MaterialMap.2048')),
    ],

    # Body身体
    'bf44bf67': [
        (log,                           ('1.0: Rina BodyA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('2825da1e', 'Rina.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('a23e2e14', 'Rina.BodyA.Diffuse.1024')),
    ],
    'a23e2e14': [
        (log,                           ('1.0: Rina BodyA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('2825da1e', 'Rina.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('bf44bf67', 'Rina.BodyA.Diffuse.2048')),
    ],
    '95f4e9c8': [
        (log,                           ('1.0: Rina BodyA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('2825da1e', 'Rina.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('fad76987', 'Rina.BodyA.LightMap.1024')),
    ],
    'fad76987': [
        (log,                           ('1.0: Rina BodyA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('2825da1e', 'Rina.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('95f4e9c8', 'Rina.BodyA.LightMap.2048')),
    ],
    'ed47722f': [
        (log,                           ('1.0: Rina BodyA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        ('2825da1e', 'Rina.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('9fa6dfd3', 'Rina.BodyA.MaterialMap.1024')),
    ],
    '9fa6dfd3': [
        (log,                           ('1.0: Rina BodyA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        ('2825da1e', 'Rina.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('ed47722f', 'Rina.BodyA.MaterialMap.2048')),
    ],

    # MARK: Seed 席德
    #IB
    '6cb35165': [(log, ('2.1: Seed Hair IB Hash',)),         (add_ib_check_if_missing,)],
    '634ac589': [(log, ('2.1: Seed Body IB Hash',)),         (add_ib_check_if_missing,)],
    '651f4fd5': [(log, ('2.1: Seed Hoverboard IB Hash',)),  (add_ib_check_if_missing,)],    
    '09d9dca7': [(log, ('2.1: Seed Face IB Hash',)),         (add_ib_check_if_missing,)],
    #VB

    #Texture纹理
    # Face脸部
    'f02ebff3': [
        (log,                           ('2.1: Seed FaceA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('09d9dca7', 'Seed.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('a7e3da19', 'Seed.FaceA.Diffuse.1024')),
    ],
    'a7e3da19': [
        (log,                           ('2.1: Seed FaceA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('09d9dca7', 'Seed.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('f02ebff3', 'Seed.FaceA.Diffuse.2048')),
    ],

    # Hair头发
    '2fff22a7': [
        (log,                           ('2.1: Seed HairA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('9d4019f4', 'Seed.HairA.Diffuse.1024')),
    ],
    '9d4019f4': [
        (log,                           ('2.1: Seed HairA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('2fff22a7', 'Seed.HairA.Diffuse.2048')),
    ],
    'bf2c273a': [
        (log,                           ('2.1: Seed HairA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('e7efee45', 'Seed.HairA.LightMap.1024')),
    ],
    'e7efee45': [
        (log,                           ('2.1: Seed HairA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('bf2c273a', 'Seed.HairA.LightMap.2048')),
    ],
    'a1658bbd': [
        (log,                           ('2.1: Seed HairA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('bfcfcdc6', 'Seed.HairA.MaterialMap.1024')),
    ],
    'bfcfcdc6': [
        (log,                           ('2.1: Seed HairA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('a1658bbd', 'Seed.HairA.MaterialMap.2048')),
    ],

    # Body身体
    '7c7c2622': [
        (log,                           ('2.1: Seed BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('684d2bd5', 'Seed.BodyA.Diffuse.1024')),
    ],
    '684d2bd5': [
        (log,                           ('2.1: Seed BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('7c7c2622', 'Seed.BodyA.Diffuse.2048')),
    ],
    'b14c9c6f': [
        (log,                           ('2.1: Seed BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('522ee460', 'Seed.BodyA.LightMap.1024')),
    ],
    '522ee460': [
        (log,                           ('2.1: Seed BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('b14c9c6f', 'Seed.BodyA.LightMap.2048')),
    ],
    'da2deeaa': [
        (log,                           ('2.1: Seed BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('be9dd4c2', 'Seed.BodyA.MaterialMap.1024')),
    ],
    'be9dd4c2': [
        (log,                           ('2.1: Seed BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('da2deeaa', 'Seed.BodyA.MaterialMap.2048')),
    ],

    # Hoverboard
    '91d18cf9': [
        (log,                           ('2.1: Seed HoverboardA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('74b9c4c8', 'Seed.HoverboardA.Diffuse.1024')),
    ],
    '74b9c4c8': [
        (log,                           ('2.1: Seed HoverboardA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('91d18cf9', 'Seed.HoverboardA.Diffuse.2048')),
    ],
    'a6726612': [
        (log,                           ('2.1: Seed HoverboardA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('bd0f0925', 'Seed.HoverboardA.LightMap.1024')),
    ],
    'bd0f0925': [
        (log,                           ('2.1: Seed HoverboardA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('a6726612', 'Seed.HoverboardA.LightMap.2048')),
    ],
    '9896a7c2': [
        (log,                           ('2.1: Seed HoverboardA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('7f7b60c9', 'Seed.HoverboardA.MaterialMap.1024')),
    ],
    '7f7b60c9': [
        (log,                           ('2.1: Seed HoverboardA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('9896a7c2', 'Seed.HoverboardA.MaterialMap.2048')),
    ],

    # MARK: Seth赛斯
    #IB
    '35cf83ad': [(log, ('1.1: Seth Hair IB Hash',)), (add_ib_check_if_missing,)],
    '00172ec3': [(log, ('1.1: Seth Body IB Hash',)), (add_ib_check_if_missing,)],
    '52f5aa74': [(log, ('1.1: Seth Face IB Hash',)), (add_ib_check_if_missing,)],
    #VB

   #'bff3e0b3': [(log, ('1.1 -> 3.1: Seth Face texcoord_vb Hash',)), (update_hash, ('b3f6842f',))],
    #Remap
    # Reversed in v1.4
    # 'a91eeef2': [
    #     (log,            ('1.2 -> 1.3: Seth Hair Texcoord Hash',)),
    #     (update_hash,    ('a72f760f',)),
    #     (log,            ('+ Remapping texcoord buffer',)),
    #     (zzz_13_remap_texcoord, (
    #         '13_Seth_Hair',
    #         ('4B','2e','2f','2e'),
    #         ('4f','2e','2f','2e')
    #     )),
    # ],
    'a72f760f': [
        (log,            ('1.3 -> 1.4: Seth Hair Texcoord Hash',)),
        (update_hash,    ('a91eeef2',)),
        (log,            ('+ Remapping texcoord buffer',)),
        (zzz_13_remap_texcoord, (
            '14_Seth_Hair',
            ('4f','2e','2f','2e'),
            ('4B','2e','2f','2e')
        )),
    ],

    #Texture纹理
    # Face脸部
    '09981aff': [
        (log,                           ('1.1: Seth FaceA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('52f5aa74', 'Seth.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('fe5b7534', 'Seth.FaceA.Diffuse.1024')),
    ],
    'fe5b7534': [
        (log,                           ('1.1: Seth FaceA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('52f5aa74', 'Seth.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('09981aff', 'Seth.FaceA.Diffuse.2048')),
    ],

    # Hair头发
    'dc8e244d': [
        (log,                           ('1.1: Seth HairA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('35cf83ad', 'Seth.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('d3756c37', 'Seth.HairA.Diffuse.1024')),
    ],
    'd3756c37': [
        (log,                           ('1.1: Seth HairA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('35cf83ad', 'Seth.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('dc8e244d', 'Seth.HairA.Diffuse.2048')),
    ],
    'd4de9ec1': [(log, ('1.7 -> 2.0: Seth HairA LightMap 2048p Hash',)), (update_hash, ('a855884d',))],
    'a855884d': [
        (log,                           ('1.1: Seth HairA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('35cf83ad', 'Seth.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('ca070fa7','c01dbf6c'), 'Seth.HairA.LightMap.1024')),
    ],
    'c01dbf6c': [(log, ('1.7 -> 2.0: Seth HairA LightMap 1024p Hash',)), (update_hash, ('ca070fa7',))],
    'ca070fa7': [
        (log,                           ('1.1: Seth HairA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('35cf83ad', 'Seth.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('a855884d','d4de9ec1'), 'Seth.HairA.LightMap.2048')),
    ],
    '3c256565': [
        (log,                           ('1.1: Seth HairA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        ('35cf83ad', 'Seth.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('833e9405', 'Seth.HairA.MaterialMap.1024')),
    ],
    '833e9405': [
        (log,                           ('1.1: Seth HairA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        ('35cf83ad', 'Seth.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('3c256565', 'Seth.HairA.MaterialMap.2048')),
    ],

    # Body身体
    '7f8416ab': [
        (log,                           ('1.1: Seth BodyA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('00172ec3', 'Seth.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('dbc90150', 'Seth.BodyA.Diffuse.1024')),
    ],
    'dbc90150': [
        (log,                           ('1.1: Seth BodyA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('00172ec3', 'Seth.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('7f8416ab', 'Seth.BodyA.Diffuse.2048')),
    ],
    '3d97c2ef': [(log, ('1.7 -> 2.0: Seth BodyA LightMap 2048p Hash',)), (update_hash, ('5b205468',))],
    '5b205468': [
        (log,                           ('1.1: Seth BodyA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('00172ec3', 'Seth.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('57cf813c','9436aa83'), 'Seth.BodyA.LightMap.1024')),
    ],
    '9436aa83': [(log, ('1.7 -> 2.0: Seth BodyA LightMap 1024p Hash',)), (update_hash, ('57cf813c',))],
    '57cf813c': [
        (log,                           ('1.1: Seth BodyA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('00172ec3', 'Seth.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('5b205468','3d97c2ef'), 'Seth.BodyA.LightMap.2048')),
    ],
    '732d3f81': [
        (log,                           ('1.1: Seth BodyA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        ('00172ec3', 'Seth.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('56775fcb', 'Seth.BodyA.MaterialMap.1024')),
    ],
    '56775fcb': [
        (log,                           ('1.1: Seth BodyA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        ('00172ec3', 'Seth.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('732d3f81', 'Seth.BodyA.MaterialMap.2048')),
    ],


    # MARK: Sigrid希格莉德
    '38daef11': [(log, ('3.11: Sigrid Body IB Hash',)), (add_ib_check_if_missing,)],
    '48625d6d': [(log, ('3.1: Sigrid Face IB Hash',)), (add_ib_check_if_missing,)],
    '84618ee0': [(log, ('3.1: Sigrid Hair IB Hash',)), (add_ib_check_if_missing,)],
    'b20f90ea': [(log, ('3.1: Sigrid Leg IB Hash',)), (add_ib_check_if_missing,)],
    'b30db54e': [(log, ('3.1: Sigrid Tail IB Hash',)), (add_ib_check_if_missing,)],
    #VB
    'a23aa8a3': [
        (log, ('3.1 -> 3.11: Sigrid Body IB Hash',)), 
        (update_hash, ('38daef11',)),
        (transfer_indexed_sections, {
            'src_indices': ['0', '42759'],
            'trg_indices': ['0', '42963'],
        })],
    '8c0622d7': [(log, ('3.11: Sigrid Body-身体 blend_vb Hash',)), (update_hash, ('018ea72c',))],
    '01b35c45': [(log, ('3.11: Sigrid Body-身体 draw_vb Hash',)), (update_hash, ('d0bf0e87',))],
    '08c15b45': [(log, ('3.11: Sigrid Body-身体 position_vb Hash',)), (update_hash, ('e2a28287',))],
    'f6474154': [(log, ('3.11: Sigrid Body-身体 texcoord_vb Hash',)), (update_hash, ('08ddaed3',))],
    #Texture纹理
    # Face脸部
    '18b20f06': [
        (log,                           ('3.1: Sigrid FaceA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('f178a6f2', 'Sigrid.FaceA.Diffuse.1024')),
    ],
    'f178a6f2': [
        (log,                           ('3.1: Sigrid FaceA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('18b20f06', 'Sigrid.FaceA.Diffuse.2048')),
    ],

    # Body身体
    '5b733af8': [
        (log,                           ('3.1: Sigrid BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('037f456b', 'Sigrid.BodyA.Diffuse.1024')),
    ],
    '037f456b': [
        (log,                           ('3.1: Sigrid BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('5b733af8', 'Sigrid.BodyA.Diffuse.2048')),
    ],
    '13775170': [
        (log,                           ('3.1: Sigrid BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('a73e5eea', 'Sigrid.BodyA.LightMap.1024')),
    ],
    'a73e5eea': [
        (log,                           ('3.1: Sigrid BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('13775170', 'Sigrid.BodyA.LightMap.2048')),
    ],
    'af950416': [
        (log,                           ('3.1: Sigrid BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('764b45ad', 'Sigrid.BodyA.MaterialMap.1024')),
    ],
    '764b45ad': [
        (log,                           ('3.1: Sigrid BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('af950416', 'Sigrid.BodyA.MaterialMap.2048')),
    ],
        
    # Hair头发
    '0c4bea0f': [
        (log,                           ('3.1: Sigrid HairA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('66dbe05f', 'Sigrid.HairA.Diffuse.1024')),
    ],
    '66dbe05f': [
        (log,                           ('3.1: Sigrid HairA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('0c4bea0f', 'Sigrid.HairA.Diffuse.2048')),
    ],
    'da6a6f0b': [
        (log,                           ('3.1: Sigrid HairA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('bc582555', 'Sigrid.HairA.LightMap.1024')),
    ],
    'bc582555': [
        (log,                           ('3.1: Sigrid HairA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('da6a6f0b', 'Sigrid.HairA.LightMap.2048')),
    ],
    'f5da0fcd': [
        (log,                           ('3.1: Sigrid HairA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('d055f8e9', 'Sigrid.HairA.MaterialMap.1024')),
    ],
    'd055f8e9': [
        (log,                           ('3.1: Sigrid HairA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('f5da0fcd', 'Sigrid.HairA.MaterialMap.2048')),
    ],
    


    # MARK: SigridSkin希格莉德皮肤
    'd9e49957': [(log, ('3.1: SigridSkin Body IB Hash',)), (add_ib_check_if_missing,)],
    'd892c658': [(log, ('3.1: SigridSkin Rotor IB Hash',)), (add_ib_check_if_missing,)],
    'b4f608f5': [(log, ('3.1: SigridSkin RotorBearing IB Hash',)), (add_ib_check_if_missing,)],
    '285aa61f': [(log, ('3.1: SigridSkin Spear IB Hash',)), (add_ib_check_if_missing,)],
    
    # Body
    'b07c43ef': [(log, ('3.1 -> 3.1B: SigridSkin BodyA Diffuse 2048p Hash',)), (update_hash, ('8874c184',))],
    '8874c184': [
        (log,                           ('3.1B: SigridSkin BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   (('82a7f32e','3a0cfbd4'), 'SigridSkin.BodyA.Diffuse.1024')),
    ],
    '82a7f32e': [(log, ('3.1 -> 3.1B: SigridSkin BodyA Diffuse 1024p Hash',)), (update_hash, ('3a0cfbd4',))],
    '3a0cfbd4': [
        (log,                           ('3.1B: SigridSkin BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   (('b07c43ef','8874c184'), 'SigridSkin.BodyA.Diffuse.2048')),
    ],
    '5e907c41': [(log, ('3.1 -> 3.1B: SigridSkin BodyA LightMap 2048p Hash',)), (update_hash, ('2772f644',))],
    '2772f644': [
        (log,                           ('3.1B: SigridSkin BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   (('1b4edd7b','cfc4ac8a'), 'SigridSkin.BodyA.LightMap.1024')),
    ],
    '1b4edd7b': [(log, ('3.1 -> 3.1B: SigridSkin BodyA LightMap 1024p Hash',)), (update_hash, ('cfc4ac8a',))],
    'cfc4ac8a': [
        (log,                           ('3.1B: SigridSkin BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   (('5e907c41','2772f644'), 'SigridSkin.BodyA.LightMap.2048')),
    ],
    'e104d477': [
        (log,                           ('3.1: SigridSkin BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('aa626489', 'SigridSkin.BodyA.MaterialMap.1024')),
    ],
    'aa626489': [
        (log,                           ('3.1: SigridSkin BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('e104d477', 'SigridSkin.BodyA.MaterialMap.2048')),
    ],

    # MARK: Soldier0零号安比
    #IB
    '217ec790': [(log, ('1.6: Soldier0 Hair IB Hash',)), (add_ib_check_if_missing,)],
    '53d3f4e5': [(log, ('1.6: Soldier0 Body IB Hash',)), (add_ib_check_if_missing,)],
    'e30ca87f': [(log, ('1.6: Soldier0 Face IB Hash',)), (add_ib_check_if_missing,)],
    #VB

    'f2f539b8': [
        (log, ('1.6 -> 2.0: Soldier0 Face IB Hash',)), 
        (update_hash, ('e30ca87f',)),
        (transfer_indexed_sections, {
            'src_indices': ['0', '690', '8442'],
            'trg_indices': ['0', '984', '8442'],
        })],
    #不再提供对脸部vb的修复，不建议对脸部模型进行修改，可能会导致脸部贴图错位
    #Face VB取消更新，因为与青衣冲突
    #'6a492df0': [(log, ('1.7 -> 2.0: Soldier0 Face Texcoord Hash',)), (update_hash, ('fc66ecd0',))],
    #'57c9f0a3': [(log, ('1.7 -> 2.0: Soldier0 Face Blend Hash',)), (update_hash, ('df6b6f84',))],
    #Texture纹理
    # Hair头发
    'aa3d57ff': [
        (log,                           ('1.6: Soldier0 HairA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('217ec790', 'Soldier0.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('8cb4086a', 'Soldier0.HairA.Diffuse.1024')),
    ],
    '8cb4086a': [
        (log,                           ('1.6: Soldier0 HairA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('217ec790', 'Soldier0.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('aa3d57ff', 'Soldier0.HairA.Diffuse.2048')),
    ],
    '8d42a55b': [
        (log,                           ('1.6: Soldier0 HairA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('217ec790', 'Soldier0.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('96a28554', 'Soldier0.HairA.LightMap.1024')),
    ],
    '96a28554': [
        (log,                           ('1.6: Soldier0 HairA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('217ec790', 'Soldier0.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('8d42a55b', 'Soldier0.HairA.LightMap.2048')),
    ],
    '464847b3': [(log, ('1.7 -> 2.0: Soldier0 HairA MaterialMap 2048p Hash',)), (update_hash, ('0b059f91',))],
    '0b059f91': [
        (log,                           ('1.6: Soldier0 HairA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        ('217ec790', 'Soldier0.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('bb979f59','ce3e73be'), 'Soldier0.HairA.MaterialMap.1024')),
    ],
    'ce3e73be': [(log, ('1.7 -> 2.0: Soldier0 HairA MaterialMap 1024p Hash',)), (update_hash, ('bb979f59',))],
    'bb979f59': [
        (log,                           ('1.6: Soldier0 HairA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        ('217ec790', 'Soldier0.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('0b059f91','464847b3'), 'Soldier0.HairA.MaterialMap.2048')),
    ],

    # Body身体
    '627baf3f': [
        (log,                           ('1.6: Soldier0 BodyA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('53d3f4e5', 'Soldier0.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('0acef326', 'Soldier0.BodyA.Diffuse.1024')),
    ],
    '0acef326': [
        (log,                           ('1.6: Soldier0 BodyA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('53d3f4e5', 'Soldier0.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('627baf3f', 'Soldier0.BodyA.Diffuse.2048')),
    ],
    '3a56b70b': [
        (log,                           ('1.6: Soldier0 BodyA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('53d3f4e5', 'Soldier0.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('625ad0eb', 'Soldier0.BodyA.LightMap.1024')),
    ],
    '625ad0eb': [
        (log,                           ('1.6: Soldier0 BodyA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('53d3f4e5', 'Soldier0.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('3a56b70b', 'Soldier0.BodyA.LightMap.2048')),
    ],
    '7cfa12b6': [
        (log,                           ('1.6: Soldier0 BodyA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        ('53d3f4e5', 'Soldier0.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('dea3c5a0', 'Soldier0.BodyA.MaterialMap.1024')),
    ],
    'dea3c5a0': [
        (log,                           ('1.6: Soldier0 BodyA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        ('53d3f4e5', 'Soldier0.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('7cfa12b6', 'Soldier0.BodyA.MaterialMap.2048')),
    ],

    # MARK: Soldier11十一号
    #IB
    '2fa74e2f': [(log, ('1.0: Soldier11 Hair IB Hash',)), (add_ib_check_if_missing,)],
    'e3ee72d9': [(log, ('1.0: Soldier11 Body IB Hash',)), (add_ib_check_if_missing,)],
    'bb315c43': [(log, ('1.0: Soldier11 Face IB Hash',)), (add_ib_check_if_missing,)],
    #VB

    #Texture纹理
    # Face脸部
    '3c8697e8': [
        (log,                           ('1.0: Soldier11 FaceA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('bb315c43', 'Soldier11.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('67821d9d', 'Soldier11.FaceA.Diffuse.2048')),
    ],
    '67821d9d': [
        (log,                           ('1.0: Soldier11 FaceA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('bb315c43', 'Soldier11.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('3c8697e8', 'Soldier11.FaceA.Diffuse.1024')),
    ],

    # Hair头发
    'b41b671a': [
        (log,                           ('1.0: Soldier11 HairA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('2fa74e2f', 'Soldier11.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('15f933dc', 'Soldier11.HairA.Diffuse.1024')),
    ],
    '15f933dc': [
        (log,                           ('1.0: Soldier11 HairA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('2fa74e2f', 'Soldier11.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('b41b671a', 'Soldier11.HairA.Diffuse.2048')),
    ],
    '787659b9': [(log, ('1.7 -> 2.0: Soldier11 HairA LightMap 2048p Hash',)), (update_hash, ('71993491',))],
    '71993491': [
        (log,                           ('1.0: Soldier11 HairA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('2fa74e2f', 'Soldier11.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('17e75c76','baa3c836'), 'Soldier11.HairA.LightMap.1024')),
    ],
    'baa3c836': [(log, ('1.7 -> 2.0: Soldier11 HairA LightMap 1024p Hash',)), (update_hash, ('17e75c76',))],
    '17e75c76': [
        (log,                           ('1.0: Soldier11 HairA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('2fa74e2f', 'Soldier11.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('71993491','787659b9'), 'Soldier11.HairA.LightMap.2048')),
    ],

    # Body身体
    '640a8c01': [
        (log,                           ('1.0: Soldier11 BodyA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('e3ee72d9', 'Soldier11.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('d7f2269b', 'Soldier11.BodyA.Diffuse.1024')),
    ],
    'd7f2269b': [
        (log,                           ('1.0: Soldier11 BodyA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('e3ee72d9', 'Soldier11.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('640a8c01', 'Soldier11.BodyA.Diffuse.2048')),
    ],
    '2f88092e': [(log, ('1.7 -> 2.0: Soldier11 BodyA LightMap 2048p Hash',)), (update_hash, ('33e8af55',))],
    '33e8af55': [
        (log,                           ('1.0: Soldier11 BodyA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('e3ee72d9', 'Soldier11.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('744e39e9','ce581269'), 'Soldier11.BodyA.LightMap.1024')),
    ],
    'ce581269': [(log, ('1.7 -> 2.0: Soldier11 BodyA LightMap 1024p Hash',)), (update_hash, ('744e39e9',))],
    '744e39e9': [
        (log,                           ('1.0: Soldier11 BodyA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('e3ee72d9', 'Soldier11.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('2f88092e','33e8af55'), 'Soldier11.BodyA.LightMap.2048')),
    ],
    '81db8cbe': [(log, ('1.7 -> 2.0: Soldier11 BodyA MaterialMap 2048p Hash',)), (update_hash, ('8ab5b59d',))],
    '8ab5b59d': [
        (log,                           ('1.0: Soldier11 BodyA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        ('e3ee72d9', 'Soldier11.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('9d09159b','874f9f68'), 'Soldier11.BodyA.MaterialMap.1024')),
    ],
    '874f9f68': [(log, ('1.7 -> 2.0: Soldier11 BodyA MaterialMap 1024p Hash',)), (update_hash, ('9d09159b',))],
    '9d09159b': [
        (log,                           ('1.0: Soldier11 BodyA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        ('e3ee72d9', 'Soldier11.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('8ab5b59d','81db8cbe'), 'Soldier11.BodyA.MaterialMap.2048')),
    ],


    # MARK: Soukaku苍角
    #IB
    'fe70c7a3': [(log, ('1.0: Soukaku Hair IB Hash',)), (add_ib_check_if_missing,)],
    'ced49ff8': [(log, ('1.0: Soukaku Body IB Hash',)), (add_ib_check_if_missing,)],
    '1315178e': [(log, ('1.1: Soukaku Mask IB Hash',)), (add_ib_check_if_missing,)],
    '020f9ac6': [(log, ('1.1: Soukaku Face IB Hash',)), (add_ib_check_if_missing,)],
    #VB

    '01f7369e': [(log, ('1.0 - 1.1: Soukaku Face IB Hash',)), (update_hash, ('020f9ac6',))],
    #不再提供对脸部vb的修复，不建议对脸部模型进行修改，可能会导致脸部贴图错位
    #'ad41e2f6': [(log, ('1.0 - 1.1: Soukaku Face Texcoord Hash',)), (update_hash, ('c2db08f0',))],

    #Texture纹理
    # Face脸部
    '427b39a4': [
        (log,                           ('1.0: Soukaku FaceA Diffuse 2048p Hash',)),
        (add_section_if_missing,        (('020f9ac6', '01f7369e'), 'Soukaku.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('2ceacde6', 'Soukaku.FaceA.Diffuse.1024')),
    ],
    '2ceacde6': [
        (log,                           ('1.0: Soukaku FaceA Diffuse 1024p Hash',)),
        (add_section_if_missing,        (('020f9ac6', '01f7369e'), 'Soukaku.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('427b39a4', 'Soukaku.FaceA.Diffuse.2048')),
    ],
    '17110d01': [
        (log,                           ('1.0: Soukaku FaceA LightMap 2048p Hash',)),
        (add_section_if_missing,        (('020f9ac6', '01f7369e'), 'Soukaku.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('c20a8c82', 'Soukaku.FaceA.Diffuse.1024')),
    ],
    'c20a8c82': [
        (log,                           ('1.0: Soukaku FaceA LightMap 1024p Hash',)),
        (add_section_if_missing,        (('020f9ac6', '01f7369e'), 'Soukaku.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('17110d01', 'Soukaku.FaceA.Diffuse.2048')),
    ],

    # Hair头发
    '32ea0d00': [
        (log,                           ('1.0: Soukaku HairA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('fe70c7a3', 'Soukaku.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('34a3ff5b', 'Soukaku.HairA.Diffuse.1024')),
    ],
    '34a3ff5b': [
        (log,                           ('1.0: Soukaku HairA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('fe70c7a3', 'Soukaku.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('32ea0d00', 'Soukaku.HairA.Diffuse.2048')),
    ],
    '04654e94': [(log, ('1.7 -> 2.0: Soukaku HairA LightMap 2048p Hash',)), (update_hash, ('a70e24a2',))],
    'a70e24a2': [
        (log,                           ('1.0: Soukaku HairA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('fe70c7a3', 'Soukaku.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('5966c5e3','7bbb3d02'), 'Soukaku.HairA.LightMap.1024')),
    ],
    '7bbb3d02': [(log, ('1.7 -> 2.0: Soukaku HairA LightMap 1024p Hash',)), (update_hash, ('5966c5e3',))],
    '5966c5e3': [
        (log,                           ('1.0: Soukaku HairA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('fe70c7a3', 'Soukaku.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('a70e24a2','04654e94'), 'Soukaku.HairA.LightMap.2048')),
    ],
    'd1444c52': [
        (log,                           ('1.0: Soukaku HairA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        ('fe70c7a3', 'Soukaku.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('218689cf', 'Soukaku.HairA.MaterialMap.1024')),
    ],
    '218689cf': [
        (log,                           ('1.0: Soukaku HairA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        ('fe70c7a3', 'Soukaku.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('d1444c52', 'Soukaku.HairA.MaterialMap.2048')),
    ],

    # Body身体
    'ee31954b': [
        (log,                           ('1.0: Soukaku BodyA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('ced49ff8', 'Soukaku.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('6f5d31fc', 'Soukaku.BodyA.Diffuse.1024')),
    ],
    '6f5d31fc': [
        (log,                           ('1.0: Soukaku BodyA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('ced49ff8', 'Soukaku.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('ee31954b', 'Soukaku.BodyA.Diffuse.2048')),
    ],
    '112a36a4': [
        (log,                           ('1.0: Soukaku BodyA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('ced49ff8', 'Soukaku.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('c0f0bb74', 'Soukaku.BodyA.LightMap.1024')),
    ],
    'c0f0bb74': [
        (log,                           ('1.0: Soukaku BodyA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('ced49ff8', 'Soukaku.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('112a36a4', 'Soukaku.BodyA.LightMap.2048')),
    ],
    'd638ddf9': [
        (log,                           ('1.0: Soukaku BodyA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        ('ced49ff8', 'Soukaku.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('1ec28297', 'Soukaku.BodyA.MaterialMap.1024')),
    ],
    '1ec28297': [
        (log,                           ('1.0: Soukaku BodyA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        ('ced49ff8', 'Soukaku.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('d638ddf9', 'Soukaku.BodyA.MaterialMap.2048')),
    ],

    # MARK: StarlightBilly星徽比例
    #IB
    'b126d40d': [(log, ('2.8: StarlightBilly Hair IB Hash',)), (add_ib_check_if_missing,)],
    '099cc55b': [(log, ('2.8: StarlightBilly Body IB Hash',)), (add_ib_check_if_missing,)],
    'b602e4de': [(log, ('2.8: StarlightBilly Torso IB Hash',)), (add_ib_check_if_missing,)],
    '85ec4f39': [(log, ('2.8: StarlightBilly LeftArm IB Hash',)), (add_ib_check_if_missing,)],
    'fed4432c': [(log, ('2.8: StarlightBilly Collar IB Hash',)), (add_ib_check_if_missing,)],
    '26d71d07': [(log, ('2.8: StarlightBilly Motorcycle IB Hash',)), (add_ib_check_if_missing,)],
    '47be3135': [(log, ('2.8: StarlightBilly Face IB Hash',)), (add_ib_check_if_missing,)],
    #VB

    #Texture纹理
    # Face脸部
    'f55b5dbb': [
        (log,                           ('2.8: StarlightBilly FaceA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('e706ba29', 'StarlightBilly.FaceA.Diffuse.1024')),
    ],
    'e706ba29': [
        (log,                           ('2.8: StarlightBilly FaceA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('f55b5dbb', 'StarlightBilly.FaceA.Diffuse.2048')),
    ],
    'ba8a1e40': [
        (log,                           ('2.8: StarlightBilly FaceA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('4784f14a', 'StarlightBilly.FaceA.LightMap.1024')),
    ],
    '4784f14a': [
        (log,                           ('2.8: StarlightBilly FaceA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('ba8a1e40', 'StarlightBilly.FaceA.LightMap.2048')),
    ],
    'bdc617ad': [
        (log,                           ('2.8: StarlightBilly FaceA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('d08a92b4', 'StarlightBilly.FaceA.MaterialMap.1024')),
    ],
    'd08a92b4': [
        (log,                           ('2.8: StarlightBilly FaceA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('bdc617ad', 'StarlightBilly.FaceA.MaterialMap.2048')),
    ],

    # Body身体
    '30b6b9c7': [
        (log,                           ('2.8: StarlightBilly BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('be5165ce', 'StarlightBilly.BodyA.Diffuse.1024')),
    ],
    'be5165ce': [
        (log,                           ('2.8: StarlightBilly BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('30b6b9c7', 'StarlightBilly.BodyA.Diffuse.2048')),
    ],
    'da2181cf': [
        (log,                           ('2.8: StarlightBilly BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('7ac1a66a', 'StarlightBilly.BodyA.LightMap.1024')),
    ],
    '7ac1a66a': [
        (log,                           ('2.8: StarlightBilly BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('da2181cf', 'StarlightBilly.BodyA.LightMap.2048')),
    ],
    'd85dec5d': [
        (log,                           ('2.8: StarlightBilly BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('150df321', 'StarlightBilly.BodyA.MaterialMap.1024')),
    ],
    '150df321': [
        (log,                           ('2.8: StarlightBilly BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('d85dec5d', 'StarlightBilly.BodyA.MaterialMap.2048')),
    ],

    # Torso
    'd82e8cd7': [
        (log,                           ('2.8: StarlightBilly TorsoA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('a6ef0c74', 'StarlightBilly.TorsoA.Diffuse.1024')),
    ],
    'a6ef0c74': [
        (log,                           ('2.8: StarlightBilly TorsoA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('d82e8cd7', 'StarlightBilly.TorsoA.Diffuse.2048')),
    ],
    'a28930f3': [
        (log,                           ('2.8: StarlightBilly TorsoA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('6effa144', 'StarlightBilly.TorsoA.LightMap.1024')),
    ],
    '6effa144': [
        (log,                           ('2.8: StarlightBilly TorsoA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('a28930f3', 'StarlightBilly.TorsoA.LightMap.2048')),
    ],
    'f8f7fdbe': [
        (log,                           ('2.8: StarlightBilly TorsoA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('744b53d4', 'StarlightBilly.TorsoA.MaterialMap.1024')),
    ],
    '744b53d4': [
        (log,                           ('2.8: StarlightBilly TorsoA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('f8f7fdbe', 'StarlightBilly.TorsoA.MaterialMap.2048')),
    ],

    # LeftArm左臂
    '6fe50be9': [
        (log,                           ('2.8: StarlightBilly LeftArmA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('1d5dcd0a', 'StarlightBilly.LeftArmA.Diffuse.1024')),
    ],
    '1d5dcd0a': [
        (log,                           ('2.8: StarlightBilly LeftArmA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('6fe50be9', 'StarlightBilly.LeftArmA.Diffuse.2048')),
    ],
    'c0a681c1': [
        (log,                           ('2.8: StarlightBilly LeftArmA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('16d85b96', 'StarlightBilly.LeftArmA.LightMap.1024')),
    ],
    '16d85b96': [
        (log,                           ('2.8: StarlightBilly LeftArmA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('c0a681c1', 'StarlightBilly.LeftArmA.LightMap.2048')),
    ],
    '95454832': [
        (log,                           ('2.8: StarlightBilly LeftArmA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('02ac888a', 'StarlightBilly.LeftArmA.MaterialMap.1024')),
    ],
    '02ac888a': [
        (log,                           ('2.8: StarlightBilly LeftArmA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('95454832', 'StarlightBilly.LeftArmA.MaterialMap.2048')),
    ],

    # Motorcycle
    'ed4bde0d': [
        (log,                           ('2.8: StarlightBilly MotorcycleA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('d4aabf11', 'StarlightBilly.MotorcycleA.Diffuse.1024')),
    ],
    'd4aabf11': [
        (log,                           ('2.8: StarlightBilly MotorcycleA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('ed4bde0d', 'StarlightBilly.MotorcycleA.Diffuse.2048')),
    ],
    '573e87e3': [
        (log,                           ('2.8: StarlightBilly MotorcycleA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('5dc62b0b', 'StarlightBilly.MotorcycleA.LightMap.1024')),
    ],
    '5dc62b0b': [
        (log,                           ('2.8: StarlightBilly MotorcycleA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('573e87e3', 'StarlightBilly.MotorcycleA.LightMap.2048')),
    ],
    '6b61b30c': [
        (log,                           ('2.8: StarlightBilly MotorcycleA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('81cd8366', 'StarlightBilly.MotorcycleA.MaterialMap.1024')),
    ],
    '81cd8366': [
        (log,                           ('2.8: StarlightBilly MotorcycleA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('6b61b30c', 'StarlightBilly.MotorcycleA.MaterialMap.2048')),
    ],

    # MARK: Trigger扳机
    #IB
    '8e98ef9a': [(log, ('1.6: Trigger Hair IB Hash',)), (add_ib_check_if_missing,)],
    '7f32eeae': [(log, ('1.6: Trigger Body IB Hash',)), (add_ib_check_if_missing,)],
    '40cd4182': [(log, ('1.6: Trigger Face IB Hash',)), (add_ib_check_if_missing,)],
    #VB
    #不再提供对脸部vb的修复，不建议对脸部模型进行修改，可能会导致脸部贴图错位
    #'dfc69ad0': [(log, ('1.7 -> 2.0: Trigger Face Position',)), (update_hash, ('ba455625',))],
    #'b9f0d595': [(log, ('2.2 -> 2.3: Trigger Face Texcoord',)), (update_hash, ('d4a12ab7',))],

    #Texture纹理
    # Face脸部
    '88728785': [
        (log,                           ('1.6: Trigger FaceA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('40cd4182', 'Trigger.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('cffc4b09', 'Trigger.FaceA.Diffuse.1024')),
    ],
    'cffc4b09': [
        (log,                           ('1.6: Trigger FaceA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('40cd4182', 'Trigger.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('88728785', 'Trigger.FaceA.Diffuse.2048')),
    ],

    # Hair头发
    'e826a564': [
        (log,                           ('1.6: Trigger HairA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('8e98ef9a', 'Trigger.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('984e7896', 'Trigger.HairA.Diffuse.1024')),
    ],
    '984e7896': [
        (log,                           ('1.6: Trigger HairA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('8e98ef9a', 'Trigger.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('e826a564', 'Trigger.HairA.Diffuse.2048')),
    ],
    '23f2a4cf': [
        (log,                           ('1.6: Trigger HairA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('8e98ef9a', 'Trigger.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('c321345c', 'Trigger.HairA.LightMap.1024')),
    ],
    'c321345c': [
        (log,                           ('1.6: Trigger HairA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('8e98ef9a', 'Trigger.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('23f2a4cf', 'Trigger.HairA.LightMap.2048')),
    ],
    'b24f1752': [
        (log,                           ('1.6: Trigger HairA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        ('8e98ef9a', 'Trigger.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('4ee3c3fe', 'Trigger.HairA.MaterialMap.1024')),
    ],
    '4ee3c3fe': [
        (log,                           ('1.6: Trigger HairA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        ('8e98ef9a', 'Trigger.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('b24f1752', 'Trigger.HairA.MaterialMap.2048')),
    ],

    # Body身体
    '6631eadc': [
        (log,                           ('1.6: Trigger BodyA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('7f32eeae', 'Trigger.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('8cffa733', 'Trigger.BodyA.Diffuse.1024')),
    ],
    '8cffa733': [
        (log,                           ('1.6: Trigger BodyA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('7f32eeae', 'Trigger.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('6631eadc', 'Trigger.BodyA.Diffuse.2048')),
    ],
    '05250215': [
        (log,                           ('1.6: Trigger BodyA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('7f32eeae', 'Trigger.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('2c72b961', 'Trigger.BodyA.LightMap.1024')),
    ],
    '2c72b961': [
        (log,                           ('1.6: Trigger BodyA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('7f32eeae', 'Trigger.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('05250215', 'Trigger.BodyA.LightMap.2048')),
    ],
    '985c5f52': [
        (log,                           ('1.6: Trigger BodyA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        ('7f32eeae', 'Trigger.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('cd507047', 'Trigger.BodyA.MaterialMap.1024')),
    ],
    'cd507047': [
        (log,                           ('1.6: Trigger BodyA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        ('7f32eeae', 'Trigger.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('985c5f52', 'Trigger.BodyA.MaterialMap.2048')),
    ],

    # MARK: Velina维琳娜
    #IB
    '1300e048': [(log, ('3.0: Velina Body IB Hash',)), (add_ib_check_if_missing,)],
    '2414f4b9': [(log, ('3.1: Velina Face-脸部 IB Hash',)), (add_ib_check_if_missing,)],
    '9fbf4911': [(log, ('3.0: Velina Fan IB Hash',)), (add_ib_check_if_missing,)],
    '5eb66b57': [(log, ('3.0: Velina Hair IB Hash',)), (add_ib_check_if_missing,)],
    '6c0b932e': [(log, ('3.0: Velina HairClip IB Hash',)), (add_ib_check_if_missing,)],
    '6b25e6d8': [(log, ('3.0: Velina Leg IB Hash',)), (add_ib_check_if_missing,)],
    #VB
    '6cfb2498': [
        (log, ('3.0 -> 3.1: Velina Face IB Hash',)), 
        (update_hash, ('2414f4b9',)),
        (transfer_indexed_sections, {
            'src_indices': ['0', '7182', '9888'],
            'trg_indices': ['0', '7398', '9888'],
        })],
    #不再提供对脸部vb的修复，不建议对脸部模型进行修改，可能会导致脸部贴图错位
    #'98ecf569': [(log, ('3.1: Velina Face-脸部 blend_vb Hash',)), (update_hash, ('76fe8eed',))],
    #'19ead1b7': [(log, ('3.1: Velina Face-脸部 draw_vb Hash',)), (update_hash, ('bfa3b361',))],
    #'23f842f0': [(log, ('3.1: Velina Face-脸部 position_vb Hash',)), (update_hash, ('85b12026',))],
    #'641bedfb': [(log, ('3.1: Velina Face-脸部 texcoord_vb Hash',)), (update_hash, ('69304ff6',))],
    #Texture纹理
    # Face脸部
    '93ce2562': [
        (log,                           ('3.0: Velina FaceA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('e5409177', 'Velina.FaceA.Diffuse.1024')),
    ],
    'e5409177': [
        (log,                           ('3.0: Velina FaceA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('93ce2562', 'Velina.FaceA.Diffuse.2048')),
    ],

    # Body身体
    '93c61891': [
        (log,                           ('3.0: Velina BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('f9a8e3ba', 'Velina.BodyA.Diffuse.1024')),
    ],
    'f9a8e3ba': [
        (log,                           ('3.0: Velina BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('93c61891', 'Velina.BodyA.Diffuse.2048')),
    ],
    '9a16d70e': [
        (log,                           ('3.0: Velina BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('5562351c', 'Velina.BodyA.LightMap.1024')),
    ],
    '5562351c': [
        (log,                           ('3.0: Velina BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('9a16d70e', 'Velina.BodyA.LightMap.2048')),
    ],
    'bb1d0172': [
        (log,                           ('3.0: Velina BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('531320a5', 'Velina.BodyA.MaterialMap.1024')),
    ],
    '531320a5': [
        (log,                           ('3.0: Velina BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('bb1d0172', 'Velina.BodyA.MaterialMap.2048')),
    ],
            
    # Hair头发
    'dc6853c3': [
        (log,                           ('3.0: Velina HairA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('673e5da6', 'Velina.HairA.Diffuse.1024')),
    ],
    '673e5da6': [
        (log,                           ('3.0: Velina HairA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('dc6853c3', 'Velina.HairA.Diffuse.2048')),
    ],
    'f06d3a26': [
        (log,                           ('3.0: Velina HairA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('54fc678e', 'Velina.HairA.LightMap.1024')),
    ],
    '54fc678e': [
        (log,                           ('3.0: Velina HairA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('f06d3a26', 'Velina.HairA.LightMap.2048')),
    ],
    '4951b2a2': [
        (log,                           ('3.0: Velina HairA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('ccbcd045', 'Velina.HairA.MaterialMap.1024')),
    ],
    'ccbcd045': [
        (log,                           ('3.0: Velina HairA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('4951b2a2', 'Velina.HairA.MaterialMap.2048')),
    ],
    
    # Leg腿部
    'febbf3b1': [
        (log,                           ('3.0: Velina LegA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('afa5c7de', 'Velina.LegA.Diffuse.1024')),
    ],
    'afa5c7de': [
        (log,                           ('3.0: Velina LegA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('febbf3b1', 'Velina.LegA.Diffuse.2048')),
    ],
    '5908c0bf': [
        (log,                           ('3.0: Velina LegA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('b9fb90ca', 'Velina.LegA.LightMap.1024')),
    ],
    'b9fb90ca': [
        (log,                           ('3.0: Velina LegA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('5908c0bf', 'Velina.LegA.LightMap.2048')),
    ],
    '6b291f4d': [
        (log,                           ('3.0: Velina LegA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('ba191269', 'Velina.LegA.MaterialMap.1024')),
    ],
    'ba191269': [
        (log,                           ('3.0: Velina LegA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('6b291f4d', 'Velina.LegA.MaterialMap.2048')),
    ],

    # MARK: VelinaSkin维琳娜-皮肤
    #IB
    '0479bb8f': [(log, ('3.0: VelinaSkin Body IB Hash',)), (add_ib_check_if_missing,)],
    '1914d1e4': [(log, ('3.0: VelinaSkin Eyebrow IB Hash',)), (add_ib_check_if_missing,)],
    '73685503': [(log, ('3.0: VelinaSkin HairClip IB Hash',)), (add_ib_check_if_missing,)],
    '2f94c7e8': [(log, ('3.0: VelinaSkin Leg IB Hash',)), (add_ib_check_if_missing,)],
    '8ac40392': [(log, ('3.0: VelinaSkin Weapon IB Hash',)), (add_ib_check_if_missing,)],
    #VB
    #Texture纹理
    # Body身体
    '988ded22': [
        (log,                           ('3.0: VelinaSkin BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('3f573933', 'VelinaSkin.BodyA.Diffuse.1024')),
    ],
    '3f573933': [
        (log,                           ('3.0: VelinaSkin BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('988ded22', 'VelinaSkin.BodyA.Diffuse.2048')),
    ],
    '48ece6e8': [
        (log,                           ('3.0: VelinaSkin BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('22b4f8ab', 'VelinaSkin.BodyA.LightMap.1024')),
    ],
    '22b4f8ab': [
        (log,                           ('3.0: VelinaSkin BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('48ece6e8', 'VelinaSkin.BodyA.LightMap.2048')),
    ],
    'ed40f87e': [
        (log,                           ('3.0: VelinaSkin BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('ca53350a', 'VelinaSkin.BodyA.MaterialMap.1024')),
    ],
    'ca53350a': [
        (log,                           ('3.0: VelinaSkin BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('ed40f87e', 'VelinaSkin.BodyA.MaterialMap.2048')),
    ],
    '2ca3f765': [
        (log,                           ('3.0: VelinaSkin BodyB Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('b3f5f0a6', 'VelinaSkin.BodyB.Diffuse.1024')),
    ],
    'b3f5f0a6': [
        (log,                           ('3.0: VelinaSkin BodyB Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('2ca3f765', 'VelinaSkin.BodyB.Diffuse.2048')),
    ],
    '64b2da48': [
        (log,                           ('3.0: VelinaSkin BodyB LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('a8072c81', 'VelinaSkin.BodyB.LightMap.1024')),
    ],
    'a8072c81': [
        (log,                           ('3.0: VelinaSkin BodyB LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('64b2da48', 'VelinaSkin.BodyB.LightMap.2048')),
    ],
    '7c2d3cdb': [
        (log,                           ('3.0: VelinaSkin BodyB MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('05e20bdc', 'VelinaSkin.BodyB.MaterialMap.1024')),
    ],
    '05e20bdc': [
        (log,                           ('3.0: VelinaSkin BodyB MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('7c2d3cdb', 'VelinaSkin.BodyB.MaterialMap.2048')),
    ],
        
    # Hair头发
    '5e6e492c': [
        (log,                           ('3.0: VelinaSkin HairA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('03002967', 'VelinaSkin.HairA.Diffuse.1024')),
    ],
    '03002967': [
        (log,                           ('3.0: VelinaSkin HairA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('5e6e492c', 'VelinaSkin.HairA.Diffuse.2048')),
    ],
    '6b7dcb1b': [
        (log,                           ('3.0: VelinaSkin HairA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('b9c5d317', 'VelinaSkin.HairA.LightMap.1024')),
    ],
    'b9c5d317': [
        (log,                           ('3.0: VelinaSkin HairA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('6b7dcb1b', 'VelinaSkin.HairA.LightMap.2048')),
    ],
    '18018e7a': [
        (log,                           ('3.0: VelinaSkin HairA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('ccf82282', 'VelinaSkin.HairA.MaterialMap.1024')),
    ],
    'ccf82282': [
        (log,                           ('3.0: VelinaSkin HairA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('18018e7a', 'VelinaSkin.HairA.MaterialMap.2048')),
    ],
    
    # Leg腿部
    'f786f1ab': [
        (log,                           ('3.0: VelinaSkin LegA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('6eaed274', 'VelinaSkin.LegA.Diffuse.1024')),
    ],
    '6eaed274': [
        (log,                           ('3.0: VelinaSkin LegA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('f786f1ab', 'VelinaSkin.LegA.Diffuse.2048')),
    ],
    'bd0acdee': [
        (log,                           ('3.0: VelinaSkin LegA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('301301ff', 'VelinaSkin.LegA.LightMap.1024')),
    ],
    '301301ff': [
        (log,                           ('3.0: VelinaSkin LegA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('bd0acdee', 'VelinaSkin.LegA.LightMap.2048')),
    ],
    'ea9152d8': [
        (log,                           ('3.0: VelinaSkin LegA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('966cf15e', 'VelinaSkin.LegA.MaterialMap.1024')),
    ],
    '966cf15e': [
        (log,                           ('3.0: VelinaSkin LegA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('ea9152d8', 'VelinaSkin.LegA.MaterialMap.2048')),
    ],

    # MARK: Vivian薇薇安
    'c4eb6168': [(log, ('1.7: Vivian Hair IB Hash',)), (add_ib_check_if_missing,)],
    'cd609d98': [(log, ('1.7: Vivian Body IB Hash',)), (add_ib_check_if_missing,)],
    '39944f20': [(log, ('1.7: Vivian Face IB Hash',)), (add_ib_check_if_missing,)],
    #VB
    #不再提供对脸部vb的修复，不建议对脸部模型进行修改，可能会导致脸部贴图错位
    #'0afe5a44': [(log, ('3.1 -> 3.2: Vivian Face-脸 texcoord_vb Hash',)), (update_hash, ('50c5d703',))],

    #Texture纹理
    # Face脸部
    '7b262ab6': [
        (log,                           ('1.7: Vivian FaceA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('39944f20', 'Vivian.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('66b5da8e', 'Vivian.FaceA.Diffuse.1024')),
    ],
    '66b5da8e': [
        (log,                           ('1.7: Vivian FaceA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('39944f20', 'Vivian.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('7b262ab6', 'Vivian.FaceA.Diffuse.2048')),
    ],

    # Hair头发
    'a84d933f': [
        (log,                           ('1.7: Vivian HairA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('c4eb6168', 'Vivian.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('2df6f7b5', 'Vivian.HairA.Diffuse.1024')),
    ],
    '2df6f7b5': [
        (log,                           ('1.7: Vivian HairA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('c4eb6168', 'Vivian.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('a84d933f', 'Vivian.HairA.Diffuse.2048')),
    ],
    '8e3a20ea': [
        (log,                           ('1.7: Vivian HairA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('c4eb6168', 'Vivian.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('36b80366', 'Vivian.HairA.LightMap.1024')),
    ],
    '36b80366': [
        (log,                           ('1.7: Vivian HairA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('c4eb6168', 'Vivian.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('8e3a20ea', 'Vivian.HairA.LightMap.2048')),
    ],
    '2af66072': [
        (log,                           ('1.7: Vivian HairA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        ('c4eb6168', 'Vivian.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('2d5b1412', 'Vivian.HairA.MaterialMap.1024')),
    ],
    '2d5b1412': [
        (log,                           ('1.7: Vivian HairA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        ('c4eb6168', 'Vivian.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('2af66072', 'Vivian.HairA.MaterialMap.2048')),
    ],

    # Body身体
    '0635e2dd': [
        (log,                           ('1.7: Vivian BodyA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('cd609d98', 'Vivian.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('da41fbd6', 'Vivian.BodyA.Diffuse.1024')),
    ],
    'da41fbd6': [
        (log,                           ('1.7: Vivian BodyA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('cd609d98', 'Vivian.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('0635e2dd', 'Vivian.BodyA.Diffuse.2048')),
    ],
    'e21c3a6b': [
        (log,                           ('1.7: Vivian BodyA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('cd609d98', 'Vivian.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('4a86e169', 'Vivian.BodyA.LightMap.1024')),
    ],
    '4a86e169': [
        (log,                           ('1.7: Vivian BodyA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('cd609d98', 'Vivian.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('e21c3a6b', 'Vivian.BodyA.LightMap.2048')),
    ],
    '81f7d37c': [
        (log,                           ('1.7: Vivian BodyA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        ('cd609d98', 'Vivian.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('fa650e6c', 'Vivian.BodyA.MaterialMap.1024')),
    ],
    'fa650e6c': [
        (log,                           ('1.7: Vivian BodyA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        ('cd609d98', 'Vivian.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('81f7d37c', 'Vivian.BodyA.MaterialMap.2048')),
    ],

    # MARK: VivianSkin薇薇安皮肤
    #IB
    '4108c0da': [(log, ('2.3: VivianSkin Hair IB Hash',)), (add_ib_check_if_missing,)],
    '3060793b': [(log, ('2.3: VivianSkin Body IB Hash',)), (add_ib_check_if_missing,)],
    #VB

    'f32eec8a': [(log, ('2.3 -> 2.4: VivianSkin Body Blend Hash',)), (update_hash, ('723bccec',))],
    #Texture纹理
    # Hair头发
    '15dcce65': [
        (log,                           ('2.3: VivianSkin HairA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('427be7bd', 'VivianSkin.HairA.Diffuse.1024')),
    ],
    '427be7bd': [
        (log,                           ('2.3: VivianSkin HairA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('15dcce65', 'VivianSkin.HairA.Diffuse.2048')),
    ],
    '8a82d289': [
        (log,                           ('2.3: VivianSkin HairA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('45b67c0b', 'VivianSkin.HairA.LightMap.1024')),
    ],
    '45b67c0b': [
        (log,                           ('2.3: VivianSkin HairA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('8a82d289', 'VivianSkin.HairA.LightMap.2048')),
    ],
    'c23ddbea': [
        (log,                           ('2.3: VivianSkin HairA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('cdb06288', 'VivianSkin.HairA.MaterialMap.1024')),
    ],
    'cdb06288': [
        (log,                           ('2.3: VivianSkin HairA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('c23ddbea', 'VivianSkin.HairA.MaterialMap.2048')),
    ],

    # Body身体
    '136b3e29': [
        (log,                           ('2.3: VivianSkin BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('1ea05046', 'VivianSkin.BodyA.Diffuse.1024')),
    ],
    '1ea05046': [
        (log,                           ('2.3: VivianSkin BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('136b3e29', 'VivianSkin.BodyA.Diffuse.2048')),
    ],
    '69a6a15f': [
        (log,                           ('2.3: VivianSkin BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('e8bb6a0f', 'VivianSkin.BodyA.LightMap.1024')),
    ],
    'e8bb6a0f': [
        (log,                           ('2.3: VivianSkin BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('69a6a15f', 'VivianSkin.BodyA.LightMap.2048')),
    ],
    '527c3676': [
        (log,                           ('2.3: VivianSkin BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('909ea74d', 'VivianSkin.BodyA.MaterialMap.1024')),
    ],
    '909ea74d': [
        (log,                           ('2.3: VivianSkin BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('527c3676', 'VivianSkin.BodyA.MaterialMap.2048')),
    ],

    # MARK: Wise哲
    #IB
    'd5ca0411': [(log, ('2.1: Wise Hair IB Hash',)), (add_ib_check_if_missing,)],
    'b1df5d22': [(log, ('1.0: Wise Bag IB Hash',)),  (add_ib_check_if_missing,)],
    '8d6acf4e': [(log, ('1.1: Wise Body IB Hash',)), (add_ib_check_if_missing,)],
    '1fdaf388': [(log, ('1.6: Wise Face IB Hash',)), (add_ib_check_if_missing,)],
    #VB

    'f6cac296': [(log, ('2.0 -> 2.1: Wise Hair IB Hash',)),       (update_hash, ('d5ca0411',))],
    'ba59bf09': [(log, ('2.0 -> 2.1: Wise Hair Draw Hash',)), (update_hash, ('ef9c0510',))],
    '6235fa7f': [(log, ('2.0 -> 2.1: Wise Hair Position Hash',)), (update_hash, ('e8df7ff3',))],
    'fe89498c': [(log, ('2.0 -> 2.1: Wise Hair Texcoord Hash',)), (update_hash, ('774071dd',))],
    '1273c7b0': [(log, ('2.0 -> 2.1: Wise Hair Blend Hash',)), (update_hash, ('edfd1666',))],
    'edfd1666': [(log, ('2.8 -> 3.0: Wise Hair Blend Hash',)), (update_hash, ('68e4f572',))],
    '83e07a1b': [(log, ('2.0 -> 2.1: Wise HairShadow IB Hash',)),  (update_hash, ('8d08b190',))],

    '4894246e': [(log, ('1.5 -> 1.6: Wise Face IB Hash',)),       (update_hash, ('1fdaf388',))],
    #不再提供对脸部vb的修复，不建议对脸部模型进行修改，可能会导致脸部贴图错位
    #'b300256d': [(log, ('1.7 -> 2.0: Wise Face Texcoord Hash',)), (update_hash, ('ebe9f31b',))],
    #'ebe9f31b': [(log, ('2.0 -> 2.1: Wise Face Texcoord Hash',)), (update_hash, ('c83b6cbf',))],

    '054ea752': [(log, ('1.0 -> 1.1: Wise Body IB Hash',)),       (update_hash, ('8d6acf4e',))],
    '73c48816': [(log, ('1.0 -> 1.1: Wise Body Draw Hash',)),     (update_hash, ('b581dc0a',))],
    '9581de22': [(log, ('1.0 -> 1.1: Wise Body Position Hash',)), (update_hash, ('67f21c9f',))],
    'a012c752': [(log, ('1.0 -> 1.1: Wise Body Texcoord Hash',)), (update_hash, ('f425bd04',))],
    '1d55bd87': [(log, ('1.7 -> 2.0: Wise Body Blend Hash',)), (update_hash, ('46462bd8',))],
    '46462bd8': [(log, ('2.8 -> 3.0: Wise Body Blend Hash',)), (update_hash, ('03dadd2a',))],

    # Reversed in v1.6
    # '67f21c9f': [(log, ('1.2 -> 1.3: Wise Body Position Hash',)), (update_hash, ('f6c5b9f3',))],
    # 'f425bd04': [(log, ('1.2 -> 1.3: Wise Body Texcoord Hash',)), (update_hash, ('a9d5b70d',))],

    'f6c5b9f3': [(log, ('1.5 -> 1.6: Wise Body Position Hash',)),   (update_hash, ('67f21c9f',))],
    'a9d5b70d': [(log, ('1.5 -> 1.6: Wise Body Texcoord Hash',)),   (update_hash, ('f425bd04',))],
    'f425bd04': [(log, ('2.0 -> 2.1: Wise Body Texcoord Hash',)), (update_hash, ('91fbd2fa',))],

    'cb22cb95': [(log, ('1.2 -> 1.3: Wise Bag Texcoord Hash',)),    (update_hash, ('2ae08ae7',))],
    '2ae08ae7': [(log, ('2.0 -> 2.1: Wise Bag Texcoord Hash',)),    (update_hash, ('8d825ff1',))],

    #Texture纹理
    # Face脸部
    '5d75fddc': [
        (log,                           ('2.0: Wiseswimwear FaceA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   (('6c4ae8ce', '588d7d2d'), 'Wiseswimwear.FaceA.Diffuse.1024')),
    ],
    '6c4ae8ce': [(log, ('1.0 -> 1.1: Wise FaceA Diffuse 1024p Hash',)), (update_hash, ('588d7d2d',))],
    '588d7d2d': [
        (log,                           ('2.0: Wiseswimwear FaceA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('5d75fddc', 'Wiseswimwear.FaceA.Diffuse.2048')),
    ],

    # Hair头发
    '28005a5b': [
        (log,                           ('1.0: Wise HairA, BagA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('cb0d0c22', 'Wise.HairA.Diffuse.1024')),
    ],
    'cb0d0c22': [
        (log,                           ('1.0: Wise HairA, BagA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('28005a5b', 'Wise.HairA.Diffuse.2048')),
    ],
    '1f21c633': [(log, ('1.7 -> 2.0: Wise HairA, BagA LightMap 2048p Hash',)), (update_hash, ('8d8269f8',))],
    '8d8269f8': [
        (log,                           ('1.0: Wise HairA, BagA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   (('33368e12', '6fcc4ad4'), 'Wise.HairA.LightMap.1024')),
    ],
    '6fcc4ad4': [(log, ('1.7 -> 2.0: Wise HairA, BagA LightMap 1024p Hash',)), (update_hash, ('33368e12',))],
    '33368e12': [
        (log,                           ('1.0: Wise HairA, BagA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   (('8d8269f8', '1f21c633'), 'Wise.HairA.LightMap.2048')),
    ],
    '473f816d': [(log, ('1.7 -> 2.0: Wise HairA, BagA MaterialMap 2048p Hash',)), (update_hash, ('f1b20f3d',))],
    'f1b20f3d': [
        (log,                           ('1.0: Wise HairA, BagA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   (('d9383a15', '7c8b0713'), 'Wise.HairA.MaterialMap.1024')),
    ],
    '7c8b0713': [(log, ('1.7 -> 2.0: Wise HairA, BagA MaterialMap 1024p Hash',)), (update_hash, ('d9383a15',))],
    'd9383a15': [
        (log,                           ('1.0: Wise HairA, BagA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   (('f1b20f3d', '473f816d'), 'Wise.HairA.MaterialMap.2048')),
    ],

    # Body身体
    '84529dab': [(log, ('1.0 -> 1.1: Wise BodyA Diffuse 2048p Hash',)), (update_hash, ('868709f2',))],
    '868709f2': [(log, ('2.6 -> 2.7: Wise BodyA Diffuse 2048p Hash',)), (update_hash, ('f2fb7a37',))],
    'f2fb7a37': [(log, ('2.8 -> 3.0: Wise BodyA Diffuse 2048p Hash',)), (update_hash, ('a9652fa4',))],
    'a9652fa4': [
        (log,                           ('1.1: Wise BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   (('3d7a53b0', 'ef76b675', 'dea7a8ca', '53b3623f'), 'Wise.BodyA.Diffuse.1024')),
    ],
    'ef76b675': [(log, ('1.0 -> 1.1: Wise BodyA Diffuse 1024p Hash',)), (update_hash, ('3d7a53b0',))],
    '3d7a53b0': [(log, ('2.6 -> 2.7: Wise BodyA Diffuse 1024p Hash',)), (update_hash, ('dea7a8ca',))],
    'dea7a8ca': [(log, ('2.8 -> 3.0: Wise BodyA Diffuse 1024p Hash',)), (update_hash, ('53b3623f',))],
    '53b3623f': [
        (log,                           ('1.1: Wise BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   (('868709f2', '84529dab', 'f2fb7a37', 'a9652fa4'), 'Wise.BodyA.Diffuse.2048')),
    ],
    '088718a9': [
        (log,                           ('1.0: Wise BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('9f46182a', 'Wise.BodyA.LightMap.1024')),
    ],
    '9f46182a': [
        (log,                           ('1.0: Wise BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('088718a9', 'Wise.BodyA.LightMap.2048')),
    ],
    'a5fdb5e7': [
        (log,                           ('1.0: Wise BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('148283b7', 'Wise.BodyA.MaterialMap.1024')),
    ],
    '148283b7': [
        (log,                           ('1.0: Wise BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('a5fdb5e7', 'Wise.BodyA.MaterialMap.2048')),
    ],


    # MARK: WiseSchoolUniform哲校服
    #IB
    '22fe3236': [(log, ('3.0: WiseSchoolUniform Body IB Hash',)), (add_ib_check_if_missing,)],
    '8a1ec07e': [(log, ('3.0: WiseSchoolUniform Neck IB Hash',)), (add_ib_check_if_missing,)],
    'f21a2bac': [(log, ('3.0: WiseSchoolUniform Tie IB Hash',)), (add_ib_check_if_missing,)],
    #VB
    #Texture纹理
    # Body身体
    'b9dcce2e': [
        (log,                           ('3.0: WiseSchoolUniform BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('a0a4c84e', 'WiseSchoolUniform.BodyA.Diffuse.1024')),
    ],
    'a0a4c84e': [
        (log,                           ('3.0: WiseSchoolUniform BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('b9dcce2e', 'WiseSchoolUniform.BodyA.Diffuse.2048')),
    ],
    'bd86c7c4': [
        (log,                           ('3.0: WiseSchoolUniform BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('8d09dc95', 'WiseSchoolUniform.BodyA.LightMap.1024')),
    ],
    '8d09dc95': [
        (log,                           ('3.0: WiseSchoolUniform BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('bd86c7c4', 'WiseSchoolUniform.BodyA.LightMap.2048')),
    ],
    '4d7473b1': [
        (log,                           ('3.0: WiseSchoolUniform BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('31707abe', 'WiseSchoolUniform.BodyA.MaterialMap.1024')),
    ],
    '31707abe': [
        (log,                           ('3.0: WiseSchoolUniform BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('4d7473b1', 'WiseSchoolUniform.BodyA.MaterialMap.2048')),
    ],
            
    # Tie领带
    '1024352b': [
        (log,                           ('3.0: WiseSchoolUniform TieA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('dd08a467', 'WiseSchoolUniform.TieA.Diffuse.1024')),
    ],
    'dd08a467': [
        (log,                           ('3.0: WiseSchoolUniform TieA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('1024352b', 'WiseSchoolUniform.TieA.Diffuse.2048')),
    ],
    'e550cd81': [
        (log,                           ('3.0: WiseSchoolUniform TieA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('4f211318', 'WiseSchoolUniform.TieA.LightMap.1024')),
    ],
    '4f211318': [
        (log,                           ('3.0: WiseSchoolUniform TieA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('e550cd81', 'WiseSchoolUniform.TieA.LightMap.2048')),
    ],
    '6649f407': [
        (log,                           ('3.0: WiseSchoolUniform TieA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('ba59a4d0', 'WiseSchoolUniform.TieA.MaterialMap.1024')),
    ],
    'ba59a4d0': [
        (log,                           ('3.0: WiseSchoolUniform TieA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('6649f407', 'WiseSchoolUniform.TieA.MaterialMap.2048')),
    ],

    # MARK: WiseSkin哲皮肤
    #IB
    '1eca2097': [(log, ('2.0: WiseSkin Body IB Hash',)), (add_ib_check_if_missing,)],
    #VB
    '6acc1eb8': [(log, ('2.4 -> 2.5: Wise Body IB Hash',)),       (update_hash, ('1eca2097',))],
    '4fa228f9': [(log, ('2.4 -> 2.5: Wise Body Draw Hash',)),     (update_hash, ('ca02f614',))],
    'ae59eabb': [(log, ('2.4 -> 2.5: Wise Body Position Hash',)), (update_hash, ('a388eb6b',))],
    'a83ada4e': [(log, ('2.4 -> 2.5: Wise Body Texcoord Hash',)), (update_hash, ('b39870e1',))],
    '177ad7e8': [(log, ('2.4 -> 2.5: Wise Body Blend Hash',)), (update_hash, ('8612559a',))],
    '8612559a': [(log, ('2.8 -> 3.0: Wise Body Blend Hash',)), (update_hash, ('f28a6363',))],
    '458bbde3': [(log, ('2.8 -> 3.0: Wise Neck Blend Hash',)), (update_hash, ('e0b1e734',))],
    #Texture纹理
    # Body身体
    '81406abe': [(log, ('2.8 -> 3.0: WiseSkin BodyA Diffuse 2048p Hash',)), (update_hash, ('669191ec',))],    
    '669191ec': [
        (log,                           ('3.0: WiseSkin BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   (('9fc3646e','23876240'), 'WiseSkin.BodyA.Diffuse.1024')),
    ],
    '9fc3646e': [(log, ('2.8 -> 3.0: WiseSkin BodyA Diffuse 1024p Hash',)), (update_hash, ('23876240',))],    
    '23876240': [
        (log,                           ('3.0: WiseSkin BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   (('81406abe','669191ec'), 'WiseSkin.BodyA.Diffuse.2048')),
    ],
    '05b25d35': [
        (log,                           ('2.0: WiseSkin BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('dd79b44b', 'WiseSkin.BodyA.LightMap.1024')),
    ],
    'dd79b44b': [
        (log,                           ('2.0: WiseSkin BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('05b25d35', 'WiseSkin.BodyA.LightMap.2048')),
    ],
    '24af1f48': [
        (log,                           ('2.0: WiseSkin BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('aa712fb9', 'WiseSkin.BodyA.MaterialMap.1024')),
    ],
    'aa712fb9': [
        (log,                           ('2.0: WiseSkin BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('24af1f48', 'WiseSkin.BodyA.MaterialMap.2048')),
    ],


    # MARK: Wiseswimwear哲·泳装
    #IB
    #3.0版本哲·泳装的模型发生了较大变化，3.0版本之前的mod将无法通过简单的hash替换来适配3.0之后的版本，故取消更新
    '0ec31440': [(log, ('3.0: Wiseswimwear Face IB Hash',)), (add_ib_check_if_missing,)],
    '19a3f02e': [(log, ('3.0: Wiseswimwear Body IB Hash',)), (add_ib_check_if_missing,)],
    #VB

    #'c83b6cbf': [(log, ('3.1: WiseSwimwear Face-脸 texcoord_vb Hash',)), (update_hash, ('2b320847',))],
    '9741e2f0': [(log, ('2.1 -> 2.2: Wiseswimwear Body Blend Hash',)), (update_hash, ('d4147320',))],
    #Texture纹理
    # Body身体
    'd476035d': [
        (log,                           ('2.0: Wiseswimwear BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('5907afda', 'Wiseswimwear.BodyA.Diffuse.1024')),
    ],
    '5907afda': [
        (log,                           ('2.0: Wiseswimwear BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('d476035d', 'Wiseswimwear.BodyA.Diffuse.2048')),
    ],
    '0fa8f99c': [
        (log,                           ('2.0: Wiseswimwear BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('7a142a7d', 'Wiseswimwear.BodyA.LightMap.1024')),
    ],
    '7a142a7d': [
        (log,                           ('2.0: Wiseswimwear BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('0fa8f99c', 'Wiseswimwear.BodyA.LightMap.2048')),
    ],
    'c2c8606e': [
        (log,                           ('2.0: Wiseswimwear BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('d6996446', 'Wiseswimwear.BodyA.MaterialMap.1024')),
    ],
    'd6996446': [
        (log,                           ('2.0: Wiseswimwear BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('c2c8606e', 'Wiseswimwear.BodyA.MaterialMap.2048')),
    ],


    # MARK: Yanagi月城柳
    #IB
    '9e12899f': [(log, ('1.3: Yanagi Hair IB Hash',)),    (add_ib_check_if_missing,)],
    'f478ee4c': [(log, ('1.3: Yanagi Body IB Hash',)),    (add_ib_check_if_missing,)],
    # '27d49f0b': [(log, ('1.3: Yanagi Sheathe IB Hash',)), (add_ib_check_if_missing,)],
    # '2d7f2223': [(log, ('1.3: Yanagi Weapon IB Hash',)),  (add_ib_check_if_missing,)],
    '0817204c': [(log, ('1.3: Yanagi Face IB Hash',)),    (add_ib_check_if_missing,)],
    #VB

    'fd363c76': [(log, ('2.3 -> 2.4: Yanagi Body Blend Hash',)), (update_hash, ('b558d482',))],

    #Texture纹理
    # Face脸部
    '95d9e92e': [
        (log,                           ('1.3: Yanagi FaceA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('0817204c', 'Yanagi.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('cfe7ab46', 'Yanagi.FaceA.Diffuse.1024')),
    ],
    'cfe7ab46': [
        (log,                           ('1.3: Yanagi FaceA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('0817204c', 'Yanagi.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('95d9e92e', 'Yanagi.FaceA.Diffuse.2048')),
    ],

    # Hair头发
    'ac5f6d76': [
        (log,                           ('1.3: Yanagi HairA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('9e12899f', 'Yanagi.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('4edb5c79', 'Yanagi.HairA.Diffuse.1024')),
    ],
    '4edb5c79': [
        (log,                           ('1.3: Yanagi HairA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('9e12899f', 'Yanagi.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('ac5f6d76', 'Yanagi.HairA.Diffuse.2048')),
    ],
    '99cfa935': [
        (log,                           ('1.3: Yanagi HairA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('9e12899f', 'Yanagi.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('5a43d985', 'Yanagi.HairA.LightMap.1024')),
    ],
    '5a43d985': [
        (log,                           ('1.3: Yanagi HairA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('9e12899f', 'Yanagi.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('99cfa935', 'Yanagi.HairA.LightMap.2048')),
    ],
    'f80b57f0': [
        (log,                           ('1.3: Yanagi HairA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        ('9e12899f', 'Yanagi.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('486e3c42', 'Yanagi.HairA.MaterialMap.1024')),
    ],
    '486e3c42': [
        (log,                           ('1.3: Yanagi HairA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        ('9e12899f', 'Yanagi.Hair.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('f80b57f0', 'Yanagi.HairA.MaterialMap.2048')),
    ],

    # Body身体
    'c7c4f5c5': [
        (log,                           ('1.3: Yanagi BodyA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('f478ee4c', 'Yanagi.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('c119dbd7', 'Yanagi.BodyA.Diffuse.1024')),
    ],
    'c119dbd7': [
        (log,                           ('1.3: Yanagi BodyA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('f478ee4c', 'Yanagi.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('c7c4f5c5', 'Yanagi.BodyA.Diffuse.2048')),
    ],
    '08933e28': [(log, ('1.7 -> 2.0: Yanagi BodyA LightMap 2048p Hash',)), (update_hash, ('616200aa',))],
    '616200aa': [
        (log,                           ('1.3: Yanagi BodyA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('f478ee4c', 'Yanagi.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('3ffcef9e','f60602ec'), 'Yanagi.BodyA.LightMap.1024')),
    ],
    'f60602ec': [(log, ('1.0 - 1.1: Yanagi BodyA LightMap 1024p Hash',)), (update_hash, ('3ffcef9e',))],
    '3ffcef9e': [
        (log,                           ('1.3: Yanagi BodyA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('f478ee4c', 'Yanagi.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('616200aa','08933e28'), 'Yanagi.BodyA.LightMap.2048')),
    ],
    'c2ae5d2b': [
        (log,                           ('1.3: Yanagi BodyA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        ('f478ee4c', 'Yanagi.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('b29f0188', 'Yanagi.BodyA.MaterialMap.1024')),
    ],
    'b29f0188': [
        (log,                           ('1.3: Yanagi BodyA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        ('f478ee4c', 'Yanagi.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('c2ae5d2b', 'Yanagi.BodyA.MaterialMap.2048')),
    ],


    # 'aaccff06': [
    #     (log,                           ('1.3: Yanagi WeaponA, SheatheA Diffuse 1024p Hash',)),
    #     (add_section_if_missing,        ('2d7f2223', 'Yanagi.Weapon.IB', 'match_priority = 0\n')),
    #     (add_section_if_missing,        ('27d49f0b', 'Yanagi.Sheathe.IB', 'match_priority = 0\n')),
    #     # (multiply_section_if_missing,   ('a1eabb9f', 'Yanagi.WeaponA.Diffuse.2048')),
    # ],
    # '8ef68839': [
    #     (log,                           ('1.3: Yanagi WeaponA, SheatheA LightMap 1024p Hash',)),
    #     (add_section_if_missing,        ('2d7f2223', 'Yanagi.Weapon.IB', 'match_priority = 0\n')),
    #     (add_section_if_missing,        ('27d49f0b', 'Yanagi.Sheathe.IB', 'match_priority = 0\n')),
    #     # (multiply_section_if_missing,   ('a1eabb9f', 'Yanagi.WeaponA.LightMap.2048')),
    # ],
    # 'ecd8605e': [
    #     (log,                           ('1.3: Yanagi WeaponA, SheatheA MaterialMap 1024p Hash',)),
    #     (add_section_if_missing,        ('2d7f2223', 'Yanagi.Weapon.IB', 'match_priority = 0\n')),
    #     (add_section_if_missing,        ('27d49f0b', 'Yanagi.Sheathe.IB', 'match_priority = 0\n')),
    #     # (multiply_section_if_missing,   ('a1eabb9f', 'Yanagi.WeaponA.MaterialMap.2048')),
    # ],

    # MARK: YeShunguang叶瞬光
    #IB
    '01ef4403': [(log, ('2.5: YeShunguang Hair IB Hash',)), (add_ib_check_if_missing,)],
    'c209c22b': [(log, ('2.5: YeShunguang Body IB Hash',)), (add_ib_check_if_missing,)],
    '4a178546': [(log, ('2.5: YeShunguang Leg IB Hash',)), (add_ib_check_if_missing,)],
    '869976a3': [(log, ('2.5: YeShunguang Tail IB Hash',)), (add_ib_check_if_missing,)],
    'c28e6303': [(log, ('2.5: YeShunguang Face IB Hash',)), (add_ib_check_if_missing,)],
    #VB

    'd1ffd339': [(log, ('2.5 -> 2.5: YeShunguang Texcoord Hash',)), (update_hash, ('dbb027eb',))],

    #Texture纹理
    # Face脸部
    '6ed0c951': [
        (log,                           ('2.5: YeShunguang FaceA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('c28e6303', 'YeShunguang.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('50f2ead2', 'YeShunguang.FaceA.Diffuse.1024')),
    ],
    '50f2ead2': [
        (log,                           ('2.5: YeShunguang FaceA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('c28e6303', 'YeShunguang.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('6ed0c951', 'YeShunguang.FaceA.Diffuse.2048')),
    ],

    # Hair头发
    '79f6acd7': [
        (log,                           ('2.5: YeShunguang HairA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('3359b263', 'YeShunguang.HairA.Diffuse.1024')),
    ],
    '3359b263': [
        (log,                           ('2.5: YeShunguang HairA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('79f6acd7', 'YeShunguang.HairA.Diffuse.2048')),
    ],
    '88269532': [
        (log,                           ('2.5: YeShunguang HairA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('3c140ab4', 'YeShunguang.HairA.LightMap.1024')),
    ],
    '3c140ab4': [
        (log,                           ('2.5: YeShunguang HairA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('88269532', 'YeShunguang.HairA.LightMap.2048')),
    ],
    '825fbf26': [
        (log,                           ('2.5: YeShunguang HairA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('c009d7c9', 'YeShunguang.HairA.MaterialMap.1024')),
    ],
    'c009d7c9': [
        (log,                           ('2.5: YeShunguang HairA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('825fbf26', 'YeShunguang.HairA.MaterialMap.2048')),
    ],

    # Hair头发Write
    'e8a8ac0b': [
        (log,                           ('2.5: YeShunguangWrite HairA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('b79da949', 'YeShunguangWrite.HairA.Diffuse.1024')),
    ],
    'b79da949': [
        (log,                           ('2.5: YeShunguangWrite HairA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('e8a8ac0b', 'YeShunguangWrite.HairA.Diffuse.2048')),
    ],
    '9f7defbc': [
        (log,                           ('2.5: YeShunguangWrite HairA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('d8ce86a1', 'YeShunguangWrite.HairA.LightMap.1024')),
    ],
    'd8ce86a1': [
        (log,                           ('2.5: YeShunguangWrite HairA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('9f7defbc', 'YeShunguangWrite.HairA.LightMap.2048')),
    ],
    'c74f9710': [
        (log,                           ('2.5: YeShunguangWrite HairA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('d864cc64', 'YeShunguangWrite.HairA.MaterialMap.1024')),
    ],
    'd864cc64': [
        (log,                           ('2.5: YeShunguangWrite HairA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('c74f9710', 'YeShunguangWrite.HairA.MaterialMap.2048')),
    ],

    # Hair头发WriteB
    '652e15a3': [
        (log,                           ('2.5: YeShunguangWrite HairB Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('22ad0434', 'YeShunguangWrite.HairB.Diffuse.1024')),
    ],
    '22ad0434': [
        (log,                           ('2.5: YeShunguangWrite HairB Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('652e15a3', 'YeShunguangWrite.HairB.Diffuse.2048')),
    ],

    # Body身体
    '5bd7d31b': [
        (log,                           ('2.5: YeShunguang BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('9758a5db', 'YeShunguang.BodyA.Diffuse.1024')),
    ],
    '9758a5db': [
        (log,                           ('2.5: YeShunguang BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('5bd7d31b', 'YeShunguang.BodyA.Diffuse.2048')),
    ],
    '72c1cf72': [
        (log,                           ('2.5: YeShunguang BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('b35315ee', 'YeShunguang.BodyA.LightMap.1024')),
    ],
    'b35315ee': [
        (log,                           ('2.5: YeShunguang BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('72c1cf72', 'YeShunguang.BodyA.LightMap.2048')),
    ],
    'a5872c6e': [
        (log,                           ('2.5: YeShunguang BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('96fc91f0', 'YeShunguang.BodyA.MaterialMap.1024')),
    ],
    '96fc91f0': [
        (log,                           ('2.5: YeShunguang BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('a5872c6e', 'YeShunguang.BodyA.MaterialMap.2048')),
    ],

    # Body身体Write
    '43ca3d50': [
        (log,                           ('2.5: YeShunguangWrite BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('34097193', 'YeShunguangWrite.BodyA.Diffuse.1024')),
    ],
    '34097193': [
        (log,                           ('2.5: YeShunguangWrite BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('43ca3d50', 'YeShunguangWrite.BodyA.Diffuse.2048')),
    ],
    '369a2106': [
        (log,                           ('2.5: YeShunguangWrite BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('1fb42fdf', 'YeShunguangWrite.BodyA.LightMap.1024')),
    ],
    '1fb42fdf': [
        (log,                           ('2.5: YeShunguangWrite BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('369a2106', 'YeShunguangWrite.BodyA.LightMap.2048')),
    ],
    'e41b12be': [
        (log,                           ('2.5: YeShunguangWrite BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('0e921a23', 'YeShunguangWrite.BodyA.MaterialMap.1024')),
    ],
    '0e921a23': [
        (log,                           ('2.5: YeShunguangWrite BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('e41b12be', 'YeShunguangWrite.BodyA.MaterialMap.2048')),
    ],

    # Leg
    '727d3454': [
        (log,                           ('2.5: YeShunguang LegA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('40985c98', 'YeShunguang.LegA.Diffuse.1024')),
    ],
    '40985c98': [
        (log,                           ('2.5: YeShunguang LegA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('727d3454', 'YeShunguang.LegA.Diffuse.2048')),
    ],
    '4eb5aae2': [
        (log,                           ('2.5: YeShunguang LegA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('7d5bc57f', 'YeShunguang.LegA.LightMap.1024')),
    ],
    '7d5bc57f': [
        (log,                           ('2.5: YeShunguang LegA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('4eb5aae2', 'YeShunguang.LegA.LightMap.2048')),
    ],
    '7f5f0193': [
        (log,                           ('2.5: YeShunguang LegA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('1d6a9266', 'YeShunguang.LegA.MaterialMap.1024')),
    ],
    '1d6a9266': [
        (log,                           ('2.5: YeShunguang LegA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('7f5f0193', 'YeShunguang.LegA.MaterialMap.2048')),
    ],

    # LegWrite
    '0b7c1487': [
        (log,                           ('2.5: YeShunguangWrite LegA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('60aa1cca', 'YeShunguangWrite.LegA.Diffuse.1024')),
    ],
    '60aa1cca': [
        (log,                           ('2.5: YeShunguangWrite LegA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('0b7c1487', 'YeShunguangWrite.LegA.Diffuse.2048')),
    ],
    'afbdd8a1': [
        (log,                           ('2.5: YeShunguangWrite LegA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('2cd88b0d', 'YeShunguangWrite.LegA.LightMap.1024')),
    ],
    '2cd88b0d': [
        (log,                           ('2.5: YeShunguangWrite LegA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('afbdd8a1', 'YeShunguangWrite.LegA.LightMap.2048')),
    ],
    '263992f5': [
        (log,                           ('2.5: YeShunguangWrite LegA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('6261eabc', 'YeShunguangWrite.LegA.MaterialMap.1024')),
    ],
    '6261eabc': [
        (log,                           ('2.5: YeShunguangWrite LegA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('263992f5', 'YeShunguangWrite.LegA.MaterialMap.2048')),
    ],

    # MARK: YeShunguangSkin叶瞬光皮肤
    #IB
    '8e7f72d5': [(log, ('2.5: YeShunguangSkin Body IB Hash',)), (add_ib_check_if_missing,)],
    '4df52aae': [(log, ('2.5: YeShunguangSkin Leg IB Hash',)), (add_ib_check_if_missing,)],
    'bafd232d': [(log, ('2.5: YeShunguangSkin Skirt IB Hash',)), (add_ib_check_if_missing,)],
    #VB
    #Texture纹理
    # Body身体
    '956bcfbd': [
        (log,                           ('2.5: YeShunguangSkin BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('cc360f56', 'YeShunguangSkin.BodyA.Diffuse.1024')),
    ],
    'cc360f56': [
        (log,                           ('2.5: YeShunguangSkin BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('956bcfbd', 'YeShunguangSkin.BodyA.Diffuse.2048')),
    ],
    '8e815da2': [
        (log,                           ('2.5: YeShunguangSkin BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('8617f478', 'YeShunguangSkin.BodyA.LightMap.1024')),
    ],
    '8617f478': [
        (log,                           ('2.5: YeShunguangSkin BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('8e815da2', 'YeShunguangSkin.BodyA.LightMap.2048')),
    ],
    '2f2c27b5': [
        (log,                           ('2.5: YeShunguangSkin BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('b2efbac8', 'YeShunguangSkin.BodyA.MaterialMap.1024')),
    ],
    'b2efbac8': [
        (log,                           ('2.5: YeShunguangSkin BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('2f2c27b5', 'YeShunguangSkin.BodyA.MaterialMap.2048')),
    ],

    # Leg
    '37c5aae5': [
        (log,                           ('2.5: YeShunguangSkin LegA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('03ed5c91', 'YeShunguangSkin.LegA.Diffuse.1024')),
    ],
    '03ed5c91': [
        (log,                           ('2.5: YeShunguangSkin LegA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('37c5aae5', 'YeShunguangSkin.LegA.Diffuse.2048')),
    ],
    '01e54e40': [
        (log,                           ('2.5: YeShunguangSkin LegA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('4de697cf', 'YeShunguangSkin.LegA.LightMap.1024')),
    ],
    '4de697cf': [
        (log,                           ('2.5: YeShunguangSkin LegA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('01e54e40', 'YeShunguangSkin.LegA.LightMap.2048')),
    ],
    '18370cad': [
        (log,                           ('2.5: YeShunguangSkin LegA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('a7140533', 'YeShunguangSkin.LegA.MaterialMap.1024')),
    ],
    'a7140533': [
        (log,                           ('2.5: YeShunguangSkin LegA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('18370cad', 'YeShunguangSkin.LegA.MaterialMap.2048')),
    ],

    # Skirt
    'f6d35967': [
        (log,                           ('2.5: YeShunguangSkin SkirtA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('c87c6d8a', 'YeShunguangSkin.SkirtA.Diffuse.1024')),
    ],
    'c87c6d8a': [
        (log,                           ('2.5: YeShunguangSkin SkirtA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('f6d35967', 'YeShunguangSkin.SkirtA.Diffuse.2048')),
    ],
    '405fa4b6': [
        (log,                           ('2.5: YeShunguangSkin SkirtA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('043b86d0', 'YeShunguangSkin.SkirtA.LightMap.1024')),
    ],
    '043b86d0': [
        (log,                           ('2.5: YeShunguangSkin SkirtA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('405fa4b6', 'YeShunguangSkin.SkirtA.LightMap.2048')),
    ],
    'e67e5577': [
        (log,                           ('2.5: YeShunguangSkin SkirtA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('a2ae050f', 'YeShunguangSkin.SkirtA.MaterialMap.1024')),
    ],
    'a2ae050f': [
        (log,                           ('2.5: YeShunguangSkin SkirtA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('e67e5577', 'YeShunguangSkin.SkirtA.MaterialMap.2048')),
    ],

    # MARK: Yidhair伊德海莉
    #IB
    '2022936e': [(log, ('2.3: Yidhair Hair IB Hash',)), (add_ib_check_if_missing,)],
    '12251f42': [(log, ('2.3: Yidhair Body IB Hash',)), (add_ib_check_if_missing,)],
    '4cb99618': [(log, ('2.3: Yidhair Tail IB Hash',)), (add_ib_check_if_missing,)],
    'a2406060': [(log, ('2.3: Yidhair Face IB Hash',)), (add_ib_check_if_missing,)],
    #VB

    #Texture纹理
    # Face脸部
    'c6e0cfbe': [
        (log,                           ('2.3: Yidhair FaceA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('a2406060', 'Yidhair.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('4753db8f', 'Yidhair.FaceA.Diffuse.1024')),
    ],
    '4753db8f': [
        (log,                           ('2.3: Yidhair FaceA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('a2406060', 'Yidhair.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('c6e0cfbe', 'Yidhair.FaceA.Diffuse.2048')),
    ],

    # Hair头发
    'd0587bc2': [
        (log,                           ('2.3: Yidhair HairA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('aefe5860', 'Yidhair.HairA.Diffuse.1024')),
    ],
    'aefe5860': [
        (log,                           ('2.3: Yidhair HairA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('d0587bc2', 'Yidhair.HairA.Diffuse.2048')),
    ],
    '42ef8882': [
        (log,                           ('2.3: Yidhair HairA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('222b6f58', 'Yidhair.HairA.LightMap.1024')),
    ],
    '222b6f58': [
        (log,                           ('2.3: Yidhair HairA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('42ef8882', 'Yidhair.HairA.LightMap.2048')),
    ],
    'bc5d6f24': [
        (log,                           ('2.3: Yidhair HairA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('527ac41b', 'Yidhair.HairA.MaterialMap.1024')),
    ],
    '527ac41b': [
        (log,                           ('2.3: Yidhair HairA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('bc5d6f24', 'Yidhair.HairA.MaterialMap.2048')),
    ],

    # Body身体
    'ca51f269': [
        (log,                           ('2.3: Yidhair BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('89bec19d', 'Yidhair.BodyA.Diffuse.1024')),
    ],
    '89bec19d': [
        (log,                           ('2.3: Yidhair BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('ca51f269', 'Yidhair.BodyA.Diffuse.2048')),
    ],
    '2ae9bee8': [(log, ('2.3 -> 2.4: Yidhair BodyA LightMap 2048p Hash',)), (update_hash, ('5b985a6f',))],
    '5b985a6f': [
        (log,                           ('2.3: Yidhair BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   (('9ad20501','381e8e5a'), 'Yidhair.BodyA.LightMap.1024')),
    ],
    '9ad20501': [(log, ('2.3 -> 2.4: Yidhair BodyA LightMap 1024p Hash',)), (update_hash, ('381e8e5a',))],
    '381e8e5a': [
        (log,                           ('2.3: Yidhair BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   (('2ae9bee8','5b985a6f'), 'Yidhair.BodyA.LightMap.2048')),
    ],
    '0e91ed54': [
        (log,                           ('2.3: Yidhair BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('9af65de7', 'Yidhair.BodyA.MaterialMap.1024')),
    ],
    '9af65de7': [
        (log,                           ('2.3: Yidhair BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('0e91ed54', 'Yidhair.BodyA.MaterialMap.2048')),
    ],

    # Tail
    '2156a161': [
        (log,                           ('2.3: Yidhair TailA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('067b0a15', 'Yidhair.TailA.Diffuse.1024')),
    ],
    '067b0a15': [
        (log,                           ('2.3: Yidhair TailA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('2156a161', 'Yidhair.TailA.Diffuse.2048')),
    ],
    '8bf59f48': [
        (log,                           ('2.3: Yidhair TailA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('6b99432e', 'Yidhair.TailA.LightMap.1024')),
    ],
    '6b99432e': [
        (log,                           ('2.3: Yidhair TailA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('8bf59f48', 'Yidhair.TailA.LightMap.2048')),
    ],
    'e0bb4de9': [
        (log,                           ('2.3: Yidhair TailA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('0bf712a3', 'Yidhair.TailA.MaterialMap.1024')),
    ],
    '0bf712a3': [
        (log,                           ('2.3: Yidhair TailA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('e0bb4de9', 'Yidhair.TailA.MaterialMap.2048')),
    ],

    # MARK: YiXuan仪玄
    #IB
    'ac8e9ee3': [(log, ('2.0: YiXuan Hair IB Hash',)),         (add_ib_check_if_missing,)],
    '029c1f5a': [(log, ('2.0: YiXuan Body IB Hash',)),         (add_ib_check_if_missing,)],
    '8c2fc05e': [(log, ('2.0: YiXuan Coat IB Hash',)),         (add_ib_check_if_missing,)],
    '8b067f99': [(log, ('2.0: YiXuan Face IB Hash',)),         (add_ib_check_if_missing,)],
    #VB

    '0219df6e': [(log, ('2.0 -> 2.1: YiXuan Bottle IB Hash',)),       (update_hash, ('1630f2d0',))],
    'd000beae': [(log, ('2.0 -> 2.1: YiXuan Bottle Draw Hash',)),     (update_hash, ('05466ddf',))],
    'd0ff2c18': [(log, ('2.0 -> 2.1: YiXuan Bottle Position Hash',)), (update_hash, ('8555098d',))],
    'f05da93a': [(log, ('2.0 -> 2.1: YiXuan Bottle Texcoord Hash',)), (update_hash, ('ff4b112b',))],
    '55638d51': [(log, ('2.0 -> 2.1: YiXuan Bottle Blend Hash',)),    (update_hash, ('d89da8eb',))],


    #Texture纹理
    # Face脸部
    '7d9ee001': [
        (log,                           ('2.0: YiXuan FaceA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('8b067f99', 'YiXuan.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('9efd1605', 'YiXuan.FaceA.Diffuse.1024')),
    ],
    '9efd1605': [
        (log,                           ('2.0: YiXuan FaceA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('8b067f99', 'YiXuan.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('7d9ee001', 'YiXuan.FaceA.Diffuse.2048')),
    ],

    # Hair头发
    '7e38b38b': [
        (log,                           ('2.0: YiXuan HairA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('84fe943d', 'YiXuan.HairA.Diffuse.1024')),
    ],
    '84fe943d': [
        (log,                           ('2.0: YiXuan HairA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('7e38b38b', 'YiXuan.HairA.Diffuse.2048')),
    ],
    '086ac064': [
        (log,                           ('2.0: YiXuan HairA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('5574ca9f', 'YiXuan.HairA.LightMap.1024')),
    ],
    '5574ca9f': [
        (log,                           ('2.0: YiXuan HairA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('086ac064', 'YiXuan.HairA.LightMap.2048')),
    ],
    '83b02982': [
        (log,                           ('2.0: YiXuan HairA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('f4ac690c', 'YiXuan.HairA.MaterialMap.1024')),
    ],
    'f4ac690c': [
        (log,                           ('2.0: YiXuan HairA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('83b02982', 'YiXuan.HairA.MaterialMap.2048')),
    ],

    # Body身体
    '2a4f37a6': [
        (log,                           ('2.0: YiXuan BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('d7db2bc6', 'YiXuan.BodyA.Diffuse.1024')),
    ],
    'd7db2bc6': [
        (log,                           ('2.0: YiXuan BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('2a4f37a6', 'YiXuan.BodyA.Diffuse.2048')),
    ],
    '5a291e85': [
        (log,                           ('2.0: YiXuan BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('96f754a7', 'YiXuan.BodyA.LightMap.1024')),
    ],
    '96f754a7': [
        (log,                           ('2.0: YiXuan BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('5a291e85', 'YiXuan.BodyA.LightMap.2048')),
    ],
    'd28370ec': [
        (log,                           ('2.0: YiXuan BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('aa1056a5', 'YiXuan.BodyA.MaterialMap.1024')),
    ],
    'aa1056a5': [
        (log,                           ('2.0: YiXuan BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('d28370ec', 'YiXuan.BodyA.MaterialMap.2048')),
    ],

    # Coat
    'e6dca725': [
        (log,                           ('2.0: YiXuan CoatA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('8c2fc05e', 'YiXuan.Coat.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('1fcedcc3', 'YiXuan.CoatA.Diffuse.1024')),
    ],
    '1fcedcc3': [
        (log,                           ('2.0: YiXuan CoatA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('8c2fc05e', 'YiXuan.Coat.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('e6dca725', 'YiXuan.CoatA.Diffuse.2048')),
    ],
    '59b2daf9': [
        (log,                           ('2.0: YiXuan CoatA LightMap 2048p Hash',)),
        (add_section_if_missing,        ('8c2fc05e', 'YiXuan.Coat.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('c4d167c3', 'YiXuan.CoatA.LightMap.1024')),
    ],
    'c4d167c3': [
        (log,                           ('2.0: YiXuan CoatA LightMap 1024p Hash',)),
        (add_section_if_missing,        ('8c2fc05e', 'YiXuan.Coat.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('59b2daf9', 'YiXuan.CoatA.LightMap.2048')),
    ],
    'bb581f1e': [
        (log,                           ('2.0: YiXuan CoatA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        ('8c2fc05e', 'YiXuan.Coat.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('fd56fa4b', 'YiXuan.CoatA.MaterialMap.1024')),
    ],

    'fd56fa4b': [
        (log,                           ('2.0: YiXuan CoatA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        ('8c2fc05e', 'YiXuan.Coat.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('bb581f1e', 'YiXuan.CoatA.MaterialMap.2048')),
    ],


    # MARK: YiXuanSkin仪玄皮肤
    #IB
    '95de0d39': [(log, ('2.0: YiXuanSkin Body IB Hash',)),         (add_ib_check_if_missing,)],
    #VB
    #Texture纹理
    # Body身体
    'fe2cc6f3': [
        (log,                           ('2.0: YiXuanSkin BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('5460dbe4', 'YiXuanSkin.BodyA.Diffuse.1024')),
    ],
    '5460dbe4': [
        (log,                           ('2.0: YiXuanSkin BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('fe2cc6f3', 'YiXuanSkin.BodyA.Diffuse.2048')),
    ],
    '867e3b95': [
        (log,                           ('2.0: YiXuanSkin BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('7369431b', 'YiXuanSkin.BodyA.LightMap.1024')),
    ],
    '7369431b': [
        (log,                           ('2.0: YiXuanSkin BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('867e3b95', 'YiXuanSkin.BodyA.LightMap.2048')),
    ],
    'c72a2356': [
        (log,                           ('2.0: YiXuanSkin BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('2d535255', 'YiXuanSkin.BodyA.MaterialMap.1024')),
    ],
    '2d535255': [
        (log,                           ('2.0: YiXuanSkin BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('c72a2356', 'YiXuanSkin.BodyA.MaterialMap.2048')),
    ],

    '487db3e0': [(log, ('2.0 -> 2.1: YiXuanSkin BodyB Diffuse 2048p Hash',)), (update_hash, ('7683c132',))],
    '7683c132': [
        (log,                           ('2.0: YiXuanSkin BodyB Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   (('c13cac2c', '89509335'), 'YiXuanSkin.BodyB.Diffuse.1024')),
    ],
    'c13cac2c': [(log, ('2.0 -> 2.1: YiXuanSkin BodyB Diffuse 1024p Hash',)), (update_hash, ('89509335',))],
    '89509335': [
        (log,                           ('2.0: YiXuanSkin BodyB Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   (('487db3e0', '7683c132'), 'YiXuanSkin.BodyB.Diffuse.2048')),
    ],
    'a22695c9': [
        (log,                           ('2.0: YiXuanSkin BodyB LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('ed7abe1d', 'YiXuanSkin.BodyB.LightMap.1024')),
    ],
    'ed7abe1d': [
        (log,                           ('2.0: YiXuanSkin BodyB LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('a22695c9', 'YiXuanSkin.BodyB.LightMap.2048')),
    ],
    '16a1fb10': [(log, ('2.0 -> 2.1: YiXuanSkin BodyB MaterialMap 2048p Hash',)), (update_hash, ('7e6747ac',))],
    '7e6747ac': [
        (log,                           ('2.0: YiXuanSkin BodyB MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   (('9a79cf64', '229c5b0f'), 'YiXuanSkin.BodyB.MaterialMap.1024')),
    ],
    '9a79cf64': [(log, ('2.0 -> 2.1: YiXuanSkin BodyB MaterialMap 1024p Hash',)), (update_hash, ('229c5b0f',))],
    '229c5b0f': [
        (log,                           ('2.0: YiXuanSkin BodyB MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   (('16a1fb10', '7e6747ac'), 'YiXuanSkin.BodyB.MaterialMap.2048')),
    ],


    # MARK: Yuzuha浮波柚叶
    #IB
    '7a504287': [(log, ('2.1: Yuzuha Hair IB Hash',)),         (add_ib_check_if_missing,)],
    '5144c409': [(log, ('2.1: Yuzuha Body IB Hash',)),         (add_ib_check_if_missing,)],
    '73757570': [(log, ('2.1: Yuzuha Legs IB Hash',)),         (add_ib_check_if_missing,)],
    '507384ea': [(log, ('2.1: Yuzuha Face IB Hash',)),         (add_ib_check_if_missing,)],
    #VB

    #Texture纹理
    # Face脸部
    '59f9e66f': [
        (log,                           ('2.1: Yuzuha FaceA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('d394bc13', 'Yuzuha.FaceA.Diffuse.2048')),
    ],
    'd394bc13': [
        (log,                           ('2.1: Yuzuha FaceA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('59f9e66f', 'Yuzuha.FaceA.Diffuse.1024')),
    ],

    # Hair头发
    '521a3242': [
        (log,                           ('2.1: Yuzuha HairA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('c9115930', 'Yuzuha.HairA.Diffuse.1024')),
    ],
    'c9115930': [
        (log,                           ('2.1: Yuzuha HairA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('521a3242', 'Yuzuha.HairA.Diffuse.2048')),
    ],
    'c400f5b7': [
        (log,                           ('2.1: Yuzuha HairA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('a9730519', 'Yuzuha.HairA.LightMap.1024')),
    ],
    'a9730519': [
        (log,                           ('2.1: Yuzuha HairA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('c400f5b7', 'Yuzuha.HairA.LightMap.2048')),
    ],
    '3f70d124': [
        (log,                           ('2.1: Yuzuha HairA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('4f5639e2', 'Yuzuha.HairA.MaterialMap.1024')),
    ],
    '4f5639e2': [
        (log,                           ('2.1: Yuzuha HairA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('3f70d124', 'Yuzuha.HairA.MaterialMap.2048')),
    ],

    # Body身体
    'be85f061': [
        (log,                           ('2.1: Yuzuha BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('1fabf669', 'Yuzuha.BodyA.Diffuse.1024')),
    ],
    '1fabf669': [
        (log,                           ('2.1: Yuzuha BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('be85f061', 'Yuzuha.BodyA.Diffuse.2048')),
    ],
    'ef192425': [
        (log,                           ('2.1: Yuzuha BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('eff3b0b0', 'Yuzuha.BodyA.LightMap.1024')),
    ],
    'eff3b0b0': [
        (log,                           ('2.1: Yuzuha BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('ef192425', 'Yuzuha.BodyA.LightMap.2048')),
    ],
    '76e5c6b7': [
        (log,                           ('2.1: Yuzuha BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('2fb36ecb', 'Yuzuha.BodyA.MaterialMap.1024')),
    ],
    '2fb36ecb': [
        (log,                           ('2.1: Yuzuha BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('76e5c6b7', 'Yuzuha.BodyA.MaterialMap.2048')),
    ],


    # MARK: YuzuhaSkin浮波柚叶皮肤
    #IB
    'b298482d': [(log, ('2.1: YuzuhaSkin Body IB Hash',)),         (add_ib_check_if_missing,)],
    'a8de520e': [(log, ('2.1: YuzuhaSkin Acc IB Hash',)),         (add_ib_check_if_missing,)],
    '14ac0d52': [(log, ('2.1: YuzuhaSkin LeopardCat IB Hash',)),         (add_ib_check_if_missing,)],
    #VB

    'f34fdc84': [(log, ('2.1 -> 2.11: YuzuhaSkin Body IB Hash',)),       (update_hash, ('b298482d',))],
    'cf3319f6': [(log, ('2.1 -> 2.11: YuzuhaSkin Body Draw Hash',)), (update_hash, ('07437c27',))],
    'a3b56c9b': [(log, ('2.1 -> 2.11: YuzuhaSkin Body Position Hash',)), (update_hash, ('2a7b9144',))],
    '3d3199c5': [(log, ('2.1 -> 2.11: YuzuhaSkin Body Texcoord Hash',)), (update_hash, ('0c9062c5',))],
    'be70426a': [(log, ('2.1 -> 2.11: YuzuhaSkin Body Blend Hash',)), (update_hash, ('523cf99d',))],
    #Texture纹理
    # Body身体
    '4f4c2b65': [
        (log,                           ('2.1: YuzuhaSkin BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('7fc53810', 'YuzuhaSkin.BodyA.Diffuse.1024')),
    ],
    '7fc53810': [
        (log,                           ('2.1: YuzuhaSkin BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('4f4c2b65', 'YuzuhaSkin.BodyA.Diffuse.2048')),
    ],
    'c3e64779': [
        (log,                           ('2.1: YuzuhaSkin BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('ac06a4c8', 'YuzuhaSkin.BodyA.LightMap.1024')),
    ],
    'ac06a4c8': [
        (log,                           ('2.1: YuzuhaSkin BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('c3e64779', 'YuzuhaSkin.BodyA.LightMap.2048')),
    ],
    'ac2f3dcb': [
        (log,                           ('2.1: YuzuhaSkin BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('58fd94ec', 'YuzuhaSkin.BodyA.MaterialMap.1024')),
    ],
    '58fd94ec': [
        (log,                           ('2.1: YuzuhaSkin BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('ac2f3dcb', 'YuzuhaSkin.BodyA.MaterialMap.2048')),
    ],

    #Acc
    '54591ef6': [
        (log,                           ('2.1: YuzuhaSkin AccA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('9f387d35', 'YuzuhaSkin.AccA.Diffuse.1024')),
    ],
    '9f387d35': [
        (log,                           ('2.1: YuzuhaSkin AccA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('54591ef6', 'YuzuhaSkin.AccA.Diffuse.2048')),
    ],
    'a78340ed': [
        (log,                           ('2.1: YuzuhaSkin AccA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('00bcfe90', 'YuzuhaSkin.AccA.LightMap.1024')),
    ],
    '00bcfe90': [
        (log,                           ('2.1: YuzuhaSkin AccA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('a78340ed', 'YuzuhaSkin.AccA.LightMap.2048')),
    ],
    '1d0dabdb': [
        (log,                           ('2.1: YuzuhaSkin AccA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('c2c76575', 'YuzuhaSkin.AccA.MaterialMap.1024')),
    ],
    'c2c76575': [
        (log,                           ('2.1: YuzuhaSkin AccA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('1d0dabdb', 'YuzuhaSkin.AccA.MaterialMap.2048')),
    ],

    # MARK: Zhao照
    #IB
    '43c3c5a0': [(log, ('2.5: Zhao Face IB Hash',)), (add_ib_check_if_missing,)],
    '2d519056': [(log, ('2.5: Zhao Hair IB Hash',)), (add_ib_check_if_missing,)],
    '6a57d06b': [(log, ('2.5: Zhao Body IB Hash',)), (add_ib_check_if_missing,)],
    #VB

    #Texture纹理
    # Face脸部
    '6f06cdfa': [
        (log,                           ('2.5: Zhao FaceA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('43c3c5a0', 'Zhao.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('b9f4efa3', 'Zhao.FaceA.Diffuse.2048')),
    ],
    'b9f4efa3': [
        (log,                           ('2.5: Zhao FaceA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('43c3c5a0', 'Zhao.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('6f06cdfa', 'Zhao.FaceA.Diffuse.1024')),
    ],
    
    # Hair头发
    '3400d1fc': [
        (log,                           ('2.5: Zhao HairA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('738b6ad0', 'Zhao.HairA.Diffuse.1024')),
    ],
    '738b6ad0': [
        (log,                           ('2.5: Zhao HairA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('3400d1fc', 'Zhao.HairA.Diffuse.2048')),
    ],
    '4c988418': [
        (log,                           ('2.5: Zhao HairA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('39dab7f4', 'Zhao.HairA.LightMap.1024')),
    ],
    '39dab7f4': [
        (log,                           ('2.5: Zhao HairA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('4c988418', 'Zhao.HairA.LightMap.2048')),
    ],
    'bdc3666d': [
        (log,                           ('2.5: Zhao HairA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('06b8c2ae', 'Zhao.HairA.MaterialMap.1024')),
    ],
    '06b8c2ae': [
        (log,                           ('2.5: Zhao HairA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('bdc3666d', 'Zhao.HairA.MaterialMap.2048')),
    ],

    # Body身体
    '77dc1746': [
        (log,                           ('2.5: Zhao BodyA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('bebe4176', 'Zhao.BodyA.Diffuse.1024')),
    ],
    'bebe4176': [
        (log,                           ('2.5: Zhao BodyA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('77dc1746', 'Zhao.BodyA.Diffuse.2048')),
    ],
    '5ed57658': [
        (log,                           ('2.5: Zhao BodyA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('dd6cfe48', 'Zhao.BodyA.LightMap.1024')),
    ],
    'dd6cfe48': [
        (log,                           ('2.5: Zhao BodyA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('5ed57658', 'Zhao.BodyA.LightMap.2048')),
    ],
    'e98b7e9e': [
        (log,                           ('2.5: Zhao BodyA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('04383cb9', 'Zhao.BodyA.MaterialMap.1024')),
    ],
    '04383cb9': [
        (log,                           ('2.5: Zhao BodyA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('e98b7e9e', 'Zhao.BodyA.MaterialMap.2048')),
    ],

    # MARK: ZhuYuan朱鸢
    #IB
    '6619364f': [(log, ('1.1: ZhuYuan Body IB Hash',)),         (add_ib_check_if_missing,)],
    '9821017e': [(log, ('1.0: ZhuYuan Hair IB Hash',)),         (add_ib_check_if_missing,)],
    'fcac8411': [(log, ('1.0: ZhuYuan Extras IB Hash',)),       (add_ib_check_if_missing,)],
    '5e717358': [(log, ('1.0: ZhuYuan ShoulderAmmo IB Hash',)), (add_ib_check_if_missing,)],
    'a63028ae': [(log, ('1.0: ZhuYuan HipAmmo IB Hash',)),      (add_ib_check_if_missing,)],
    'f1c241b7': [(log, ('1.0: ZhuYuan Face IB Hash',)),         (add_ib_check_if_missing,)],
    #VB    
    'a4aeb1d5': [(log, ('1.0 -> 1.1: ZhuYuan Body IB Hash',)),  (update_hash, ('6619364f',))],
    'f3569f8d': [(log, ('1.0 -> 1.1: ZhuYuan Body Position Hash',)), (update_hash, ('f595d24d',))],
    '160872c0': [(log, ('1.0 -> 1.1: ZhuYuan Body Texcoord Hash',)), (update_hash, ('cb885260',))],
    #Remap
    # Reverted in 1.2
    # Comment out to prevent infinite loop :/
    # 'f3c092c5': [
    #     (log, ('1.0 -> 1.1: ZhuYuan Hair Texcoord Hash',)),
    #     (update_hash, ('fdc045fc',)),
    #     (log, ('+ Remapping texcoord buffer from stride 20 to 32',)),
    #     (update_buffer_element_width, (('BBBB', 'ee', 'ff', 'ee'), ('ffff', 'ee', 'ff', 'ee'), '1.1')),
    #     (log, ('+ Setting texcoord vcolor alpha to 1',)),
    #     (update_buffer_element_value, (('ffff', 'ee', 'ff', 'ee'), ('xxx1', 'xx', 'xx', 'xx'), '1.1'))
    # ],

    'fdc045fc': [
        (log, ('1.1 -> 1.2: ZhuYuan Hair Texcoord Hash',)),
        (update_hash, ('f3c092c5',)),
        (log, ('+ Reverting texcoord buffer remap',)),
        (zzz_12_shrink_texcoord_color, ('1.2',))
    ],

    #Texture纹理
    # Face脸部
    'a1eabb9f': [
        (log,                           ('1.0: ZhuYuan FaceA Diffuse 2048p Hash',)),
        (add_section_if_missing,        ('f1c241b7', 'ZhuYuan.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('138c7d76', 'ZhuYuan.FaceA.Diffuse.1024')),
    ],
    '138c7d76': [
        (log,                           ('1.0: ZhuYuan FaceA Diffuse 1024p Hash',)),
        (add_section_if_missing,        ('f1c241b7', 'ZhuYuan.Face.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   ('a1eabb9f', 'ZhuYuan.FaceA.Diffuse.2048')),
    ],
    # Hair头发
    '7f823598': [
        (log,                           ('1.0: ZhuYuan HairA, ExtrasA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('9b86c2f6', 'ZhuYuan.HairA.Diffuse.1024')),
    ],
    '9b86c2f6': [
        (log,                           ('1.0: ZhuYuan HairA, ExtrasA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('7f823598', 'ZhuYuan.HairA.Diffuse.2048')),
    ],
    'd4ee59c7': [
        (log,                           ('1.0: ZhuYuan HairA, ExtrasA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('8955095f', 'ZhuYuan.HairA.LightMap.1024')),
    ],
    '8955095f': [
        (log,                           ('1.0: ZhuYuan HairA, ExtrasA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('d4ee59c7', 'ZhuYuan.HairA.LightMap.2048')),
    ],
    '12a407b1': [
        (log,                           ('1.0: ZhuYuan HairA, ExtrasA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('7d884663', 'ZhuYuan.HairA.MaterialMap.1024')),
    ],
    '7d884663': [
        (log,                           ('1.0: ZhuYuan HairA, ExtrasA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('12a407b1', 'ZhuYuan.HairA.MaterialMap.2048')),
    ],

    # Body身体
    'c88e7660': [(log, ('1.0 -> 1.1: ZhuYuan BodyA Diffuse 2048p Hash',)),     (update_hash, ('3ef82f41',))],
    '3ef82f41': [(log, ('1.1 -> 1.2: ZhuYuan BodyA Diffuse 2048p Hash',)),     (update_hash, ('a271e894',))],
    'a271e894': [
        (log,                           ('1.2: ZhuYuan BodyA Diffuse 2048p Hash',)),
        (add_section_if_missing,        (('a4aeb1d5', '6619364f'), 'ZhuYuan.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('46af14f8', 'f6795718', 'b57a8744'), 'ZhuYuan.BodyA.Diffuse.1024')),
    ],
    'b57a8744': [(log, ('1.0 -> 1.1: ZhuYuan BodyA Diffuse 1024p Hash',)),     (update_hash, ('f6795718',))],
    'f6795718': [(log, ('1.1 -> 1.2: ZhuYuan BodyA Diffuse 1024p Hash',)),     (update_hash, ('46af14f8',))],
    '46af14f8': [
        (log,                           ('1.2: ZhuYuan BodyA Diffuse 1024p Hash',)),
        (add_section_if_missing,        (('a4aeb1d5', '6619364f'), 'ZhuYuan.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('a271e894', '3ef82f41', 'c88e7660'), 'ZhuYuan.BodyA.Diffuse.2048')),
    ],
    '13a38449': [(log, ('1.0 -> 1.1: ZhuYuan BodyA LightMap 2048p Hash',)),    (update_hash, ('80ebf536',))],
    '80ebf536': [(log, ('1.1 -> 1.2: ZhuYuan BodyA LightMap 2048p Hash',)),    (update_hash, ('d02bc66c',))],
    'd02bc66c': [
        (log,                           ('1.2: ZhuYuan BodyA LightMap 2048p Hash',)),
        (add_section_if_missing,        (('a4aeb1d5', '6619364f'), 'ZhuYuan.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('fb385169', '14b638b6', '18d00ac6'), 'ZhuYuan.BodyA.LightMap.1024')),
    ],
    '18d00ac6': [(log, ('1.0 -> 1.1: ZhuYuan BodyA LightMap 1024p Hash',)),    (update_hash, ('14b638b6',))],
    '14b638b6': [(log, ('1.1 -> 1.2: ZhuYuan BodyA LightMap 1024p Hash',)),    (update_hash, ('fb385169',))],
    'fb385169': [
        (log,                           ('1.2: ZhuYuan BodyA LightMap 1024p Hash',)),
        (add_section_if_missing,        (('a4aeb1d5', '6619364f'), 'ZhuYuan.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('d02bc66c', '80ebf536', '13a38449'), 'ZhuYuan.BodyA.LightMap.2048')),
    ],
    'b4e20235': [(log, ('1.0 -> 1.1: ZhuYuan BodyA MaterialMap 2048p Hash',)), (update_hash, ('10415de8',))],
    '10415de8': [(log, ('1.1 -> 1.2: ZhuYuan BodyA MaterialMap 2048p Hash',)), (update_hash, ('3e808ef6',))],
    '3e808ef6': [
        (log,                           ('1.2: ZhuYuan BodyA MaterialMap 2048p Hash',)),
        (add_section_if_missing,        (('a4aeb1d5', '6619364f'), 'ZhuYuan.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('29e2ebc5', 'cd4dee2c', '1daa379f'), 'ZhuYuan.BodyA.MaterialMap.1024')),
    ],
    '1daa379f': [(log, ('1.0 -> 1.1: ZhuYuan BodyA MaterialMap 1024p Hash',)), (update_hash, ('cd4dee2c',))],
    'cd4dee2c': [(log, ('1.1 -> 1.2: ZhuYuan BodyA MaterialMap 1024p Hash',)), (update_hash, ('29e2ebc5',))],
    '29e2ebc5': [
        (log,                           ('1.2: ZhuYuan BodyA MaterialMap 1024p Hash',)),
        (add_section_if_missing,        (('a4aeb1d5', '6619364f'), 'ZhuYuan.Body.IB', 'match_priority = 0\n')),
        (multiply_section_if_missing,   (('3e808ef6', '10415de8', 'b4e20235'), 'ZhuYuan.BodyA.MaterialMap.2048')),
    ],

    # Extras
    '6a33b25e': [
        (log,                           ('1.0: ZhuYuan ExtrasB, ShoulderAmmoA, HipAmmoA Diffuse 2048p Hash',)),
        (multiply_section_if_missing,   ('222ae5ee', 'ZhuYuan.ExtrasB.Diffuse.1024')),
    ],
    '222ae5ee': [
        (log,                           ('1.0: ZhuYuan ExtrasB, ShoulderAmmoA, HipAmmoA Diffuse 1024p Hash',)),
        (multiply_section_if_missing,   ('6a33b25e', 'ZhuYuan.ExtrasB.Diffuse.2048')),
    ],
    'e30f025b': [
        (log,                           ('1.0: ZhuYuan ExtrasB, ShoulderAmmoA, HipAmmoA LightMap 2048p Hash',)),
        (multiply_section_if_missing,   ('790183b4', 'ZhuYuan.ExtrasB.LightMap.1024')),
    ],
    '790183b4': [
        (log,                           ('1.0: ZhuYuan ExtrasB, ShoulderAmmoA, HipAmmoA LightMap 1024p Hash',)),
        (multiply_section_if_missing,   ('e30f025b', 'ZhuYuan.ExtrasB.LightMap.2048')),
    ],
    '58d5c840': [
        (log,                           ('1.0: ZhuYuan ExtrasB, ShoulderAmmoA, HipAmmoA MaterialMap 2048p Hash',)),
        (multiply_section_if_missing,   ('84842409', 'ZhuYuan.ExtrasB.MaterialMap.1024')),
    ],
    '84842409': [
        (log,                           ('1.0: ZhuYuan ExtrasB, ShoulderAmmoA, HipAmmoA MaterialMap 1024p Hash',)),
        (multiply_section_if_missing,   ('58d5c840', 'ZhuYuan.ExtrasB.MaterialMap.2048')),
    ],
}


# MARK: Regex
# 使用VERBOSE标志忽略空白
# https://docs.python.org/3/library/re.html#re.VERBOSE
def get_section_hash_pattern(hash) -> re.Pattern:
    return re.compile(
        r'''
            ^(
                [ \t]*?\[(?:Texture|Shader)Override.*\][ \t]*
                (?:\n
                    (?![ \t]*?(?:\[|hash\s*=))
                    .*$
                )*?
                (?:\n\s*hash\s*=\s*{}[ \t]*)
                (?:
                    (?:\n(?![ \t]*?\[).*$)*
                    (?:\n[\t ]*?[\$\w].*$)
                )?
            )\s*
        '''.format(hash),
        flags=re.VERBOSE|re.IGNORECASE|re.MULTILINE
    )


def get_section_title_pattern(title) -> re.Pattern:
    return re.compile(
        r'''
            ^(
                [ \t]*?\[{}\]
                (?:
                    (?:\n(?![ \t]*?\[).*$)*
                    (?:\n[\t ]*?[\$\w].*$)
                )?
            )\s*
        '''.format(title),
        flags=re.VERBOSE|re.IGNORECASE|re.MULTILINE
    )

# =====================================================================
# MARK: GUI
# =====================================================================
# 以下为图形界面部分（tkinter 标准库实现，无需额外安装）
ANSI_RE = re.compile(r'\033\[[0-9;]*m')

BG      = '#101216'   # 主背景
CARD    = '#1a1d25'   # 卡片
CARD2   = '#20242e'   # 输入/列表底色
LINE    = '#2b3140'   # 分隔线
TEXT    = '#e6e9f0'   # 正文
DIM     = '#8b93a3'   # 次要文字
ACCENT  = '#ffd83d'   # 霓虹黄
OK      = '#7ee0a3'   # 成功（暗色主题取值，日间在主题表内覆盖）
ERR     = '#ff6b6b'
WARN    = '#ffab52'
DANGER  = '#c23b2e'

FONT = 'Microsoft YaHei UI'

NL = chr(10)   # 换行符（显式拼接，避免转义歧义）
MAX_LINES = 8000   # 完整日志行数上限（超出丢最旧，同终端滚动）
MAX_OK_LINES = 3000   # 已更新日志上限
TICK_MAX = 300     # 每个刷新 tick 最多落屏行数

DARK_BTN   = '#2a2f3b'
DARK_BTN_H = '#3a4150'

# ---------- 日夜主题调色板 ----------
# 角色色在两种主题下都可变；状态色(ACENT/OK/ERR/WARN/DANGER)两主题通用不变
THEMES = {
    'dark': {
        'BG': BG, 'CARD': CARD, 'CARD2': CARD2, 'LINE': LINE,
        'TEXT': TEXT, 'DIM': DIM, 'BTN': DARK_BTN, 'BTN_H': DARK_BTN_H,
        'TAG_GRAY': '#5d6675', 'TAG_DIM': DIM,
        'TAG_ACCENT': ACCENT, 'TAG_OK': OK, 'TAG_ERR': ERR, 'TAG_WARN': WARN,
        'STAT_OK': OK, 'STAT_ERR': ERR, 'STAT_WARN': WARN,
    },
    'light': {
        'BG': '#eef1f6', 'CARD': '#ffffff', 'CARD2': '#dde5ee',
        'LINE': '#b6c2d1', 'TEXT': '#10151c', 'DIM': '#43516a',
        'BTN': '#d6dfea', 'BTN_H': '#c2cedd',
        'TAG_GRAY': '#55637a', 'TAG_DIM': '#43516a',
        # 白底可读的状态/强调色（深色系）
        'TAG_ACCENT': '#7a5c00', 'TAG_OK': '#117a4e',
        'TAG_ERR': '#b3261e', 'TAG_WARN': '#8a5a00',
        'STAT_OK': '#117a4e', 'STAT_ERR': '#b3261e', 'STAT_WARN': '#8a5a00',
    },
}
# 反向查找：widget 当前颜色 → 所属角色（任一主题的取值都算）
_THEME_ROLE_OF = {}
for _p in THEMES.values():
    for _role, _hex in _p.items():
        if _role.startswith('TAG_'):
            continue   # 日志标签色不进 widget 反查表，避免与 DIM 等角色撞色
        _THEME_ROLE_OF[_hex.lower()] = _role

# 配置文件（与脚本/exe 同目录）
def _config_path():
    if getattr(sys, 'frozen', False):
        d = os.path.dirname(os.path.abspath(sys.executable))
    else:
        d = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(d, 'zzz_fix_设置.json')


def _load_config():
    try:
        with open(_config_path(), encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def _save_config(cfg):
    try:
        with open(_config_path(), 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print('保存设置失败: {}'.format(e))


def _doc_text(fname, embedded):
    """读取随包文档：程序目录存在 fname 时优先读文件（便于作者直接改 txt 维护），
    打包后无 txt 时退回内嵌文本。"""
    try:
        if getattr(sys, 'frozen', False):
            d = os.path.dirname(os.path.abspath(sys.executable))
        else:
            d = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(d, fname), encoding='utf-8') as f:
            data = f.read()
            if data.strip():
                return data
    except Exception:
        pass
    return embedded


# ================= 自动更新核心（Gitee 优先，GitHub 兜底） =================
# 版本号格式：数字+可选字母后缀，如 3.1 / 3.1C / 3.10。比较按 (数字, 后缀) 逐段进行。
def _upd_repos():
    """(host, repo) 列表，按 Gitee→GitHub 顺序；设置文件可覆盖代码常量"""
    cfg = _load_config()
    pairs = (('gitee', cfg.get('update_gitee_repo') or GITEE_REPO),
             ('github', cfg.get('update_github_repo') or GITHUB_REPO))
    return [(h, r) for h, r in pairs if r]


def _upd_configured():
    return bool(_upd_repos())


def _ver_key(v):
    """版本串→可比较键。例：3.1C → 数字按位宽补零 + 小写后缀，字符串可直接比较"""
    m = re.search(r'(\d+(?:\.\d+)*[A-Za-z]*)', str(v))
    s = m.group(1) if m else re.sub(r'[^0-9A-Za-z.]', '', str(v))
    key = []
    for part in s.split('.'):
        mm = re.match(r'^(\d+)([A-Za-z]*)$', part)
        if mm:
            key.append('{:012d}{}'.format(int(mm.group(1)), mm.group(2).lower()))
        else:
            key.append(part.lower())
    return tuple(key)


def _version_greater(new_ver, cur_ver):
    """new 版本号严格大于 cur 才返回 True（3.1C > 3.1B；3.1 < 3.1A）"""
    return _ver_key(new_ver) > _ver_key(cur_ver)


def _release_url(host, repo, tag, fname):
    """按 Release 下载链接规则拼直链（两者同构）"""
    q = lambda s: urllib.parse.quote(s, safe='')
    base = 'https://github.com/{}' if host == 'github' else 'https://gitee.com/{}'
    return '{}/releases/download/{}/{}'.format(base.format(q(repo)), q(tag), q(fname))


def _http_open(url, timeout=8.0):
    """urllib 封装：统一 UA；证书校验失败时降级为不校验重试一次（无 ca 包的旧环境）"""
    req = urllib.request.Request(url, headers={
        'User-Agent': 'ZZZ-Fix-{}/1.0 (Windows)'.format(APP_VERSION),
        'Accept': 'application/json, */*'})
    try:
        return urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.URLError as e:
        if isinstance(getattr(e, 'reason', None), ssl.SSLError):
            req2 = urllib.request.Request(url, headers={
                'User-Agent': 'ZZZ-Fix-{}/1.0 (Windows)'.format(APP_VERSION),
                'Accept': 'application/json, */*'})
            return urllib.request.urlopen(req2, timeout=timeout,
                                          context=ssl._create_unverified_context())
        raise
    except ssl.SSLError:
        req2 = urllib.request.Request(url, headers={
            'User-Agent': 'ZZZ-Fix-{}/1.0 (Windows)'.format(APP_VERSION),
            'Accept': 'application/json, */*'})
        return urllib.request.urlopen(req2, timeout=timeout,
                                      context=ssl._create_unverified_context())


def _http_json(url):
    with _http_open(url) as r:
        data = r.read()
    return json.loads(data.decode('utf-8-sig', 'replace'))


def _list_releases():
    """按 Gitee→GitHub 顺序取 Release 列表；返回候选 [(tag, 资产[(名,直链)])...]，
    全部源都失败则抛错。仅从第一个成功返回的源取（Gitee 失败才轮到 GitHub）"""
    items = []
    errs = []
    for host, repo in _upd_repos():
        if host == 'gitee':
            api = 'https://gitee.com/api/v5/repos/{}/releases?per_page=8'.format(
                urllib.parse.quote(repo, safe='/'))
        else:
            api = 'https://api.github.com/repos/{}/releases?per_page=8'.format(
                urllib.parse.quote(repo, safe='/'))
        try:
            data = _http_json(api)
        except Exception as e:
            errs.append('{}: {}'.format(host, e))
            continue
        if not isinstance(data, list) or not data:
            errs.append('{}: 返回内容为空或异常'.format(host))
            continue
        ext = '.zip' if getattr(sys, 'frozen', False) else '.py'
        for it in data:
            if not isinstance(it, dict):
                continue
            tag = str(it.get('tag_name') or it.get('name') or '').strip()
            if not tag:
                continue
            if it.get('draft'):
                continue
            assets = []
            all_names = []
            for a in it.get('assets') or []:
                if not isinstance(a, dict):
                    continue
                nm = str(a.get('name') or '')
                if not nm:
                    nm = str(a.get('browser_download_url') or '').rsplit('/', 1)[-1]
                all_names.append(nm)
                if not nm.lower().endswith(ext):
                    continue
                url = a.get('browser_download_url') or _release_url(host, repo, tag, nm)
                assets.append((nm, url))
            # 预发布排最后：有正式版就只挑正式版
            items.append((tag, assets, bool(it.get('prerelease')), all_names))
        break
    if not items:
        raise RuntimeError('；'.join(errs) or '更新源均无数据')
    return items


def check_update_now():
    """查是否有更新。返回 (info, note)：
    info 非空 = 发现新版，含 new/old/host/repo/fname/url；
    info 为空且 note 非空 = 有说明（如仓库未配置资产）；均空 = 已是最新。异常直接抛。"""
    if not _upd_configured():
        return None, '尚未配置更新仓库：请填写代码顶部 GITEE_REPO / GITHUB_REPO，或设置文件 update_gitee_repo / update_github_repo'
    releases = _list_releases()
    # 先看正式版，再看预发布；同版本号靠前（Gitee）的优先
    stable = [r for r in releases if not r[2]]
    pool = stable or releases
    cand = None
    for tag, assets, _pre, _all in sorted(pool, key=lambda r: _ver_key(r[0]), reverse=True):
        if assets:
            cand = (tag, assets)
            break
    if cand is None:
        newest = max(pool, key=lambda r: _ver_key(r[0]))
        ext = '.zip' if getattr(sys, 'frozen', False) else '.py'
        names = (newest[3] or [])[:10]
        return None, ('最新版本 {} 的 Release 里没有本模式可用的资产（{}）。\n'
                      '该版本现有附件：{}').format(newest[0], ext,
                                                 '、'.join(names) or '无')
    tag, assets = cand
    tag, assets = cand
    if not _version_greater(tag, APP_VERSION):
        return None, ''
    fname, url = assets[0]
    return ({'new': tag, 'old': APP_VERSION, 'fname': fname, 'url': url,
             'kind': 'zip' if getattr(sys, 'frozen', False) else 'py'}, None)


def _program_target():
    """当前运行的程序本体路径（exe 或本 .py）"""
    if getattr(sys, 'frozen', False):
        return os.path.abspath(sys.executable)
    return os.path.abspath(__file__)


def _save_downloaded(tmp_path, preferred):
    """把下载好的 tmp 文件改名为最终名。同名旧文件被占用（资源管理器/杀软锁定）时
    自动加序号换名（xxx.zip → xxx(2).zip），保证一定能落盘；返回实际路径"""
    base, ext = os.path.splitext(preferred)
    for i in range(100):
        dest = preferred if i == 0 else '{}({}){}'.format(base, i + 1, ext)
        try:
            if os.path.exists(dest):
                os.remove(dest)
            os.rename(tmp_path, dest)
            return dest
        except OSError:
            continue
    raise RuntimeError('下载文件被占用，无法写入最终文件名')


def _download_file(url, tmp_path, pct_cb=None, cancel_cb=None):
    """流式下载到 tmp_path。取消回调返回 True 时中止；内容异常(HTML/过小)视为失败"""
    with _http_open(url, timeout=25.0) as r:
        total = None
        cl = r.headers.get('Content-Length')
        if cl and cl.isdigit():
            total = int(cl)
        done = 0
        with open(tmp_path, 'wb') as f:
            while True:
                if cancel_cb is not None and cancel_cb():
                    raise RuntimeError('已取消下载')
                chunk = r.read(65536)
                if not chunk:
                    break
                f.write(chunk)
                done += len(chunk)
                if pct_cb is not None and total:
                    pct_cb(max(0, min(99, done * 100 // total)))
    size = os.path.getsize(tmp_path)
    if size < 1024:
        raise RuntimeError('下载内容过小（{} 字节），链接可能失效'.format(size))
    with open(tmp_path, 'rb') as f:
        head = f.read(256).lower()
    if head.startswith(b'<!doctype') or head.startswith(b'<html') or b'not found' in head:
        raise RuntimeError('下载到的不是程序文件（可能地址错误或被网络拦截）')
    if pct_cb is not None:
        pct_cb(100)


def _apply_install(tmp_path):
    """原子替换程序本体：旧文件改名 .old → 新文件就位。失败自动回滚。返回新程序路径"""
    tgt = _program_target()
    old = tgt + '.old'
    try:
        if os.path.exists(old):
            try:
                os.remove(old)
            except OSError:
                pass
        if os.path.exists(tgt):
            try:
                os.rename(tgt, old)
            except OSError as e:
                raise RuntimeError('无法替换正在运行的程序：{}。请关闭其他实例后重试'.format(e))
        try:
            os.rename(tmp_path, tgt)
        except OSError as e:
            # 新文件放不进 → 还原旧文件
            try:
                if os.path.exists(old) and not os.path.exists(tgt):
                    os.rename(old, tgt)
            except OSError:
                pass
            raise RuntimeError('安装新版本失败：{}'.format(e))
    finally:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except OSError:
            pass
    return tgt


def _program_dir():
    """程序所在目录（exe 或本 .py 所在文件夹）"""
    return os.path.dirname(_program_target())


def _rmtree_retry(p, max_sec=60.0):
    """删目录树；杀软扫描锁定时轮询重试（最多 max_sec 秒），超时才放弃静默"""
    waited = 0.0
    while True:
        try:
            shutil.rmtree(p)
            return
        except OSError:
            if not os.path.exists(p):
                return
            if waited >= max_sec:
                return
            time.sleep(0.5)
            waited += 0.5


def _relaunch_command():
    """重启命令：exe 直接重跑；py 用原解释器带上原参数"""
    tgt = _program_target()
    if getattr(sys, 'frozen', False):
        return [tgt]
    return [sys.executable, tgt] + list(sys.argv[1:])


def _cleanup_stale_old():
    """下次启动时清理更新残留：.old（仅当新程序已就位才删，半途失败的留着可恢复）、
    安装器 cmd、下载 .part、未完成的 .upd_new 暂存"""
    tgt = _program_target()
    d = os.path.dirname(tgt)
    try:
        # 新本体已存在才删 .old；本体缺席说明上次替换没完成，保留 .old 供恢复
        if os.path.exists(tgt):
            old = tgt + '.old'
            if os.path.exists(old):
                os.remove(old)
            # 兼容清扫（曾用整目录改名方案）：残留的 F.old 新本体在时安全删
            old_dir = d + '.old'
            if os.path.isdir(old_dir):
                _rmtree_retry(old_dir)
    except OSError:
        pass
    for fn in ('.upd_apply.cmd', '.upd_extract.ps1', '.upd_new'):
        try:
            p = os.path.join(d, fn)
            if os.path.isdir(p):
                _rmtree_retry(p)
            elif os.path.exists(p):
                os.remove(p)
        except OSError:
            pass
    # 依赖目录已改名中文“依赖包勿删”（旧结构叫 _internal）：
    # 新版程序能跑起来 = 自己依赖目录在；残留的旧 _internal 确认后清理
    try:
        if getattr(sys, 'frozen', False):
            dep = os.path.join(d, DEP_DIR_NAME)
            if os.path.isdir(dep) and os.path.isdir(os.path.join(d, '_internal')):
                _rmtree_retry(os.path.join(d, '_internal'))
    except OSError:
        pass
    try:
        for fn in os.listdir(d):
            if fn.startswith('.update_') and fn.endswith('.part'):
                try:
                    os.remove(os.path.join(d, fn))
                except OSError:
                    pass
    except OSError:
        pass


UPD_CMD_NAME = '.upd_apply.cmd'
UPD_PS1_NAME = '.upd_extract.ps1'
UPD_FAIL_MARK = '.upd_fail.txt'
DEP_DIR_NAME = '依赖包勿删'   # onedir 依赖目录名（与 一键打包发布.bat 的 --contents-directory 同步维护）


def _cmd_escape(p):
    """路径嵌入 .cmd 的 set 引号内仍会展开的字符只有 %；含 % 返回 None，调用方走手动兜底"""
    return p if '%' not in p else None


def _build_update_cmd(zip_dest):
    """frozen 全自动更新：生成 .upd_apply.cmd（GBK，cmd 默认码页）+ .upd_extract.ps1。
    cmd 语义：等本进程(PID)退出 → PowerShell 原地解压 zip 覆盖程序目录（zip 保留不删）→
    启动新 exe。解压用 PowerShell（系统自带 tar.exe 实测被杀毒拦截，弃用）。
    任一失败写 .upd_fail.txt 并重启当前 exe。
    返回 .cmd 路径；非 frozen / 路径含 % / 写盘失败 → None（调用方走手动解压指引）"""
    if not getattr(sys, 'frozen', False):
        return None
    exe = _program_target()
    fdir = os.path.dirname(exe)            # 程序目录 F
    for s in (zip_dest, fdir, exe):
        if _cmd_escape(s) is None:
            return None
    exe_name = os.path.basename(exe)
    cmd_path = os.path.join(fdir, UPD_CMD_NAME)
    ps1_path = os.path.join(fdir, UPD_PS1_NAME)
    try:
        # PowerShell 备用解压脚本（tar 缺失时用）；单引号包裹、内含单引号翻倍
        ps1 = "Expand-Archive -LiteralPath '{0}' -DestinationPath '{1}' -Force".format(
            zip_dest.replace("'", "''"), fdir.replace("'", "''"))
        with open(ps1_path, 'w', encoding='utf-8-sig') as f:
            f.write(ps1)
        lines = [
            '@echo off',
            'chcp 936 >nul',
            'setlocal EnableExtensions',
            'set "PID={pid}"',
            'set "DIR={fdir}"',
            'set "EXE={fdir}\\{ename}"',
            'set "PS1={ps1}"',
            'set "FIND=%WINDIR%\\System32\\find.exe"',
            'set "REASON=UNKNOWN"',
            'set /a N=0',
            ':wait',
            'tasklist /fi "PID eq %PID%" /nh | "%FIND%" "%PID%" >nul',
            'if errorlevel 1 goto waited',
            'timeout /t 1 /nobreak >nul',
            'set /a N+=1',
            'if %N% lss 120 goto wait',
            'taskkill /f /pid %PID% >nul 2>&1',
            'timeout /t 1 /nobreak >nul',
            ':waited',
            'taskkill /f /im "{ename}" >nul 2>&1',
            'powershell -NoProfile -ExecutionPolicy Bypass -File "%PS1%" >nul 2>&1',
            'if errorlevel 1 goto fail_extract',
            'if not exist "%EXE%" goto fail_noexe',
            'if exist "%PS1%" del /q "%PS1%" >nul 2>&1',
            'cd /d "%DIR%"',
            'start "" "%EXE%"',
            'exit /b 0',
            ':fail_extract',
            'set "REASON=EXTRACT"',
            'goto fail',
            ':fail_noexe',
            'set "REASON=NOEXE"',
            'goto fail',
            ':fail',
            'echo UPD_FAIL:%REASON%> "%DIR%\\.upd_fail.txt"',
            'if exist "%PS1%" del /q "%PS1%" >nul 2>&1',
            'start "" "%EXE%"',
            'exit /b 1',
        ]
        text = '\r\n'.join(lines).format(pid=os.getpid(), fdir=fdir,
                                         ps1=ps1_path, ename=exe_name)
        with open(cmd_path, 'w', encoding='gbk') as f:
            f.write(text)
        return cmd_path
    except (OSError, UnicodeEncodeError, UnicodeDecodeError):
        for p in (cmd_path, ps1_path):
            try:
                os.remove(p)
            except OSError:
                pass
        return None


def _spawn_update_cmd(zip_dest):
    """frozen 全自动更新入口：生成并静默拉起 .upd_apply.cmd，随后本进程应立即退出，
    cmd 在进程结束后原地覆盖新程序并重启。返回 True=已接管；False=走手动解压指引"""
    cmd = None
    try:
        if not getattr(sys, 'frozen', False):
            return False
        cmd = _build_update_cmd(zip_dest)
        if not cmd or not os.path.exists(cmd):
            return False
        subprocess.Popen(['cmd.exe', '/c', cmd], cwd=os.path.dirname(cmd) or None,
                         creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000),
                         close_fds=True)
        return True
    except Exception:
        if cmd:
            try:
                os.remove(cmd)
            except OSError:
                pass
        return False


UPD_FAIL_REASONS = {
    'EXTRACT': '新版解压失败（压缩包损坏或被杀毒软件拦截）',
    'NOEXE':   '新版压缩包里缺少程序主文件',
    'UNKNOWN': '原因未知',
}


def _read_update_fail_marker():
    """上次全自动更新失败的标记（.upd_fail.txt，cmd 写 UPD_FAIL:原因码）。读到即删，
    返回原因码字符串；无标记/读取失败返回 None"""
    if not getattr(sys, 'frozen', False):
        return None
    p = os.path.join(os.path.dirname(_program_target()), UPD_FAIL_MARK)
    try:
        if os.path.exists(p):
            with open(p, 'r', encoding='ascii', errors='ignore') as f:
                data = f.read().strip()
            os.remove(p)
            if ':' in data:
                return data.rsplit(':', 1)[-1].strip()
            return 'UNKNOWN'
    except OSError:
        pass
    return None


def _update_fail_msg(code):
    """失败码 → 启动提示文案（zip 保留在程序目录可手动处理）"""
    code = code or 'UNKNOWN'
    return ('上次自动更新未完成（{}）。\n'
            '程序已恢复运行。新版压缩包保留在程序目录，\n'
            '可手动右键解压覆盖更新。').format(UPD_FAIL_REASONS.get(code, code))


def cli_check_update(manual=False):
    """命令行检查更新。交互询问，确认后下载并自替换，重启新进程。
    manual=False（启动自动）时静默：无更新/失败都不输出，仅发现新版才提示。
    返回 True 表示已更新并已启动新进程（调用方应直接退出）；False 表示无需更新/失败"""
    if not _upd_configured():
        if manual:
            print('尚未配置更新仓库：填写代码顶部 GITEE_REPO / GITHUB_REPO，'
                  '或设置文件 update_gitee_repo / update_github_repo')
        return False
    if manual:
        print('正在检查更新…')
    try:
        info, note = check_update_now()
    except Exception as e:
        if manual:
            print('检查更新失败: {}'.format(e))
        return False
    if info is None:
        if manual:
            if note:
                print(note)
            else:
                print('当前已是最新版本 {}'.format(APP_VERSION))
        return False
    print()
    print('发现新版本 {}（当前 {}）'.format(info['new'], APP_VERSION))
    print('来源: {}'.format(info['url']))
    auto_mode = False
    try:
        if info.get('kind') == 'zip':
            ans = input('选择更新方式：\n'
                        '  a - 自动更新（下载后自动覆盖并重启，约 5~10 秒）\n'
                        '  m - 手动更新（仅下载压缩包，自行解压替换）\n'
                        '  其他 - 取消\n> ').strip().lower()
            auto_mode = ans in ('a', 'auto', '自动')
            if not auto_mode and ans not in ('m', 'manual', '手动'):
                print('已取消更新')
                return False
        else:
            ans = input('是否下载并更新？完成后自动重启 (y/N): ').strip().lower()
            if ans not in ('y', 'yes', '是'):
                print('已取消更新')
                return False
    except (EOFError, KeyboardInterrupt):
        print()
        return False
    tgt_dir = os.path.dirname(_program_target())

    def pct(p):
        sys.stdout.write('\r下载中… {}%'.format(p))
        sys.stdout.flush()

    if info.get('kind') == 'zip':
        # 打包版更新：按用户选择走自动覆盖 或 手动解压指引
        dest = os.path.join(tgt_dir, info['fname'])
        tmp = dest + '.part'
        try:
            _download_file(info['url'], tmp, pct_cb=pct)
            dest = _save_downloaded(tmp, dest)
        except Exception as e:
            print()
            print('更新失败: {}'.format(e))
            return False
        print('\r新版压缩包已下载：{}'.format(dest))
        print()
        if auto_mode and _spawn_update_cmd(dest):
            print('自动更新中… 约需 5~10 秒，期间请勿手动打开程序，安装完成后自动重启')
            return True   # 退出进程，cmd 原地覆盖新版后启动
        print('手动更新步骤：')
        print('1. 右键压缩包，选“解压到当前文件夹”，提示覆盖时全部选“是/替换”')
        print('2. 重新打开程序')
        print('（程序即将自动退出）')
        return True   # 直接退出，释放旧程序文件占用
    tmp = os.path.join(tgt_dir, '.update_{}.part'.format(os.getpid()))
    try:
        _download_file(info['url'], tmp, pct_cb=pct)
    except Exception as e:
        print()
        print('更新失败: {}'.format(e))
        return False
    print('\r下载完成，正在替换程序…    ')
    try:
        _apply_install(tmp)
    except Exception as e:
        print()
        print('更新失败: {}'.format(e))
        return False
    print('已安装新版本 {}，正在重启…'.format(info['new']))
    try:
        subprocess.Popen(_relaunch_command(), cwd=tgt_dir or None, close_fds=True)
    except Exception as e:
        print('自动重启失败，请手动重新打开程序：{}'.format(e))
        return False
    time.sleep(1.0)   # 等新实例起来再退出，减少 onefile 解压/杀软扫描与旧进程清理撞车
    return True


# ---------- 输出重定向：脚本里的 print() 全部进入队列，由主线程写进日志框 ----------
class TextRedirector:
    def __init__(self, q):
        self.q = q

    def write(self, s):
        s = ANSI_RE.sub('', s)
        if s:
            self.q.put(('out', s))
        return len(s)

    def flush(self):
        pass


# ---------- 收集待修复文件（跳过规则与原脚本命令行模式一致） ----------
def collect_targets(paths):
    """返回 (待处理 ini 列表, 被跳过的 DISABLED ini 列表, 忽略项说明列表)"""
    plan, disabled, notes = [], [], []
    seen_dirs, seen_files = set(), set()

    def add_ini(fp):
        real = os.path.realpath(fp)
        if real in seen_files:
            return
        seen_files.add(real)
        plan.append(fp)

    def visit(p):
        p = os.path.abspath(p)
        if os.path.isdir(p):
            real = os.path.realpath(p)
            if real in seen_dirs:
                return
            seen_dirs.add(real)
            try:
                names = sorted(os.listdir(p))
            except OSError as e:
                notes.append('无法读取文件夹 {}: {}'.format(p, e))
                return
            for name in names:
                up = name.upper()
                if up.startswith('DESKTOP'):
                    continue
                fp = os.path.join(p, name)
                if os.path.isdir(fp):
                    visit(fp)
                elif name.lower().endswith('.ini'):
                    if up.startswith('DISABLED'):
                        disabled.append(fp)
                    else:
                        add_ini(fp)
        elif os.path.isfile(p):
            name = os.path.basename(p)
            if not name.lower().endswith('.ini'):
                notes.append('跳过非 .ini 文件: {}'.format(p))
            elif name.upper().startswith('DISABLED'):
                disabled.append(p)
            else:
                add_ini(p)
        else:
            notes.append('路径不存在: {}'.format(p))

    for p in paths:
        visit(p)
    return plan, disabled, notes


# ---------- 后台修复线程（逐文件处理，支持中途停止） ----------
def repair_worker(plan, q, cancel_event):
    total = len(plan)
    changed = nochange = failed = 0
    for idx, fp in enumerate(plan, 1):
        if cancel_event.is_set():
            q.put(('aborted',))
            return
        q.put(('prog', idx, total, fp, changed, nochange, failed))
        # 文件被实际更新时会先改名备份(DISABLED_BACKUP_*)再重写，mtime 必然变化
        try:
            m0 = os.stat(fp).st_mtime
        except OSError:
            m0 = None
        try:
            ok, hash_log = upgrade_ini(fp)
        except Exception:
            ok = False
        if ok:
            try:
                m1 = os.stat(fp).st_mtime
            except OSError:
                m1 = None
            if m0 is not None and m1 is not None and m1 != m0:
                if ok and m1 != m0 and m0 is not None:
                    q.put(('oklog', fp, hash_log))
                changed += 1
            else:
                nochange += 1
        else:
            failed += 1
    q.put(('done', changed, nochange, failed))


# ---------- 拖放支持（tkinterdnd2，已安装时可用；未安装则仅按钮选择） ----------
DROP_TOKEN = re.compile(r'\{([^{}]*)\}|([^\s{}]+)')


def split_drop_text(data):
    """解析拖放文本：带空格的路径用大括号包裹；
    括号外的空白字符（空格/制表/换行/回车）都是分隔符，兼容 tkdnd、uri-list 等不同来源布局"""
    tokens, cur, depth = [], [], 0
    for ch in data or '':
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
        if depth == 0 and ch.isspace():
            if cur:
                tokens.append(''.join(cur))
                cur = []
        else:
            cur.append(ch)
    if cur:
        tokens.append(''.join(cur))
    out = []
    for t in tokens:
        t = t.strip()
        if not t:
            continue
        if t.startswith('{') and t.endswith('}'):
            t = t[1:-1]
        t = t.strip(chr(34) + chr(39))
        if t:
            out.append(t)
    return out

def clean_gui_path(raw):
    """原命令行路径规范化 + URI 特有处理：仅当输入以 file:// 开头时做 URL 解码
    （%20 等还原为真实字符；普通输入里的 %20 是文件名的一部分，不误伤）"""
    c = _clean_path_token(raw)
    if not c:
        return None
    low = raw.strip().strip(chr(34) + chr(39)).lower()
    if low.startswith('file://') and '%' in c:
        try:
            from urllib.parse import unquote
            c = unquote(c)
        except Exception:
            pass
    return c

def resolve_spaced_tokens(tokens):
    """解析拖入片段为真实路径列表。依次尝试：
    原样存在 → URL 解码后存在 → 与后续片段按 1~4 空格拼接（含解码）后存在；
    都不行则原样保留，交由 collect 报告“路径不存在”。"""
    def exists(p):
        return os.path.isdir(p) or os.path.isfile(p)

    def decode_if_uri(p):
        low = p.strip().strip(chr(34) + chr(39)).lower()
        if low.startswith('file:') and chr(37) in p:  # %
            try:
                from urllib.parse import unquote
                return unquote(p)
            except Exception:
                return p
        return p

    out = []
    i = 0
    n = len(tokens)
    while i < n:
        tok = tokens[i]
        dec = decode_if_uri(tok)
        cand = dec if exists(dec) else tok
        if exists(cand):
            out.append(cand)
            i += 1
            continue
        joined = None
        j = i
        while j + 1 < n:
            j += 1
            for k in range(1, 5):
                seg = (chr(32) * k).join(tokens[i:j + 1])
                dseg = decode_if_uri(seg)
                if exists(dseg):
                    joined = dseg
                    break
            if joined:
                break
        if joined:
            out.append(joined)
            i = j + 1
        else:
            out.append(cand)
            i += 1
    return out

_HASH_TOKEN = re.compile(r'hash = [0-9a-f]+')   # 已更新日志中待染绿的 hash 值


def is_updated_line(line):
    """判定该日志行属于“已更新”流：实际修改了文件的证据行。
    注意 '\t保存: ' 带制表符前缀（修复器输出），无前缀的“xx已保存:”是 UI 提示，不算"""
    return ('已对该ini文件进行更新修复' in line
            or '已创建备份' in line
            or '已备份缓冲区' in line
            or '写入更新的缓冲区' in line
            or '\t保存: ' in line
            or ('更新修复' in line and '没有对' not in line))


def register_drop_targets(root, handler):
    """注册拖放：窗口及所有子控件都可接收文件/文件夹。返回成功与否"""
    try:
        from tkinterdnd2 import DND_FILES
    except Exception:
        return False
    n = 0
    stack = [root]
    while stack:
        w = stack.pop()
        try:
            w.drop_target_register(DND_FILES)
            w.dnd_bind('<<Drop>>', handler)
            n += 1
        except Exception:
            pass
        try:
            stack.extend(w.winfo_children())
        except Exception:
            pass
    return n > 0


# =====================================================================
# 主界面
# =====================================================================
class _LogNotebook:
    """手工叠页容器：替代 ttk.Notebook（Python 3.13 的 ttk 页签条无法隐藏，
    会画出系统页签条），页面切换由上方自绘两组按钮完成。
    接口兼容旧代码的 select()/tabs()/tab()/add() 调用方式。"""

    def __init__(self, host):
        self._host = host
        self._pages = []      # [(页面 widget, text)]
        self._cur = 0
        self.onselect = None  # 选中变化回调（原 <<NotebookTabChanged>>）

    def add(self, w, text):
        self._pages.append((w, text))
        w.place_forget()
        if len(self._pages) == 1:
            self._cur = 0
            self._show()

    def tabs(self):
        return ['page{}'.format(i) for i in range(len(self._pages))]

    def tab(self, tid, key):
        if key != 'text':
            return ''
        return self._pages[int(tid[4:])][1]

    def select(self, tgt=None):
        """tgt=None → 返回当前页 id；否则切页"""
        if tgt is None:
            return self.tabs()[self._cur]
        idx = int(tgt[4:])
        if 0 <= idx < len(self._pages) and idx != self._cur:
            self._cur = idx
            self._show()
            if self.onselect is not None:
                try:
                    self.onselect()
                except Exception:
                    pass
        return self.tabs()[self._cur]

    def _show(self):
        for i, (w, _t) in enumerate(self._pages):
            if i == self._cur:
                w.place(in_=self._host, x=0, y=0, relwidth=1, relheight=1)
            else:
                w.place_forget()


class App:
    def __init__(self, root, initial_paths=None):
        self.root = root
        self.q = queue.Queue()
        self.cancel_event = threading.Event()
        self.running = False
        self.auto_scroll = tk.BooleanVar(value=True)
        self.log_lines = 0
        self._pend = deque()
        self._pend_ok = deque()
        self._force_tag = None
        self._part = ''
        self.drop_engine = None
        self._real_stdout, self._real_stderr = sys.stdout, sys.stderr
        sys.stdout = TextRedirector(self.q)
        sys.stderr = TextRedirector(self.q)

        self._setup_styles()
        self._build_ui()

        cfg = _load_config()
        self.default_entry.delete(0, 'end')
        self.default_entry.insert(0, cfg.get('default_folder', ''))
        self.manual_entry.delete(0, 'end')   # 手动路径不跨启动保留
        cfg.pop('manual_paths', None)
        self.use_default.set(bool(cfg.get('use_default', True)))
        hour = time.localtime().tm_hour
        auto = 'light' if 7 <= hour < 19 else 'dark'
        self._chip_mode = None
        self._file_mode = None
        self.theme = str(cfg.get('theme') or auto)
        if self.theme not in THEMES:
            self.theme = auto
        self.apply_theme(self.theme)
        if cfg.get('default_folder'):
            self._log('已载入默认修复文件夹: {}'.format(cfg['default_folder']), 'accent')
            if not os.path.isdir(cfg['default_folder']):
                self._log('默认文件夹不存在（请重新选择）: {}'.format(cfg['default_folder']), 'warn')

        self.root._app = self
        if register_drop_targets(root, self._on_dnd_event):
            self._log('提示：可以直接把 .ini 文件或文件夹拖入窗口（拖入内容进入“手动路径”）。', 'gray')
        else:
            self._log('未检测到 tkinterdnd2，拖放不可用；可用“选择路径”按钮（可 pip install tkinterdnd2 开启拖放）。', 'warn')

        if initial_paths:
            self._append_manual([p for p in initial_paths if p and not p.startswith('-')])

        # ---- 自动更新状态（启动后自动静默检查：无更新零输出，有新版才提示） ----
        self._updating = False          # 更新流程进行中（查/下载/安装）
        self._update_tmp = None         # 下载中的临时文件
        self._upd_auto = False          # 用户在确认框的选择：True=自动更新，False=手动
        self._upd_pending = False       # 已发现新版待用户处理（按钮闪烁提醒）
        self._upd_info = None           # 待处理新版的信息（按钮点击时直接用，免重新查）
        self._upd_flash = False         # 按钮闪烁相位
        _cleanup_stale_old()            # 清理上次更新残留
        code = _read_update_fail_marker()
        if code:
            # 上次全自动更新失败：提示一次并删标记（zip 仍留在程序目录可手动解压）
            self.root.after(500, lambda: messagebox.showwarning(
                '更新未完成', _update_fail_msg(code), parent=self.root))
        if cfg.get('update_auto_start', True) and _upd_configured():
            self.root.after(2500, self._auto_update_check)

        self.root.protocol('WM_DELETE_WINDOW', self.on_close)
        self._poll_start()

    # ---------------- 样式 / 布局 ----------------
    # ---------------- 日夜主题 ----------------
    def _theme_walk(self):
        stack = [self.root]
        while stack:
            w = stack.pop()
            yield w
            try:
                stack.extend(w.winfo_children())
            except Exception:
                pass

    def apply_theme(self, name):
        """整窗按主题重漆：只换装饰角色色（BG/CARD/CARD2/LINE/TEXT/DIM/BTN），
        状态色（黄/绿/红/橙）两种主题通用不动"""
        p = THEMES[name]
        opts = {
            'bg': ('BG', 'CARD', 'CARD2', 'BTN'),
            'fg': ('TEXT', 'DIM'),
            'activebackground': ('BTN_H', 'CARD2'),
            'activeforeground': ('TEXT',),
            'highlightbackground': ('LINE',),
            'selectcolor': ('CARD2',),
            'insertbackground': ('TEXT',),
        }
        for w in self._theme_walk():
            for opt, roles in opts.items():
                try:
                    val = w.cget(opt)
                except Exception:
                    continue
                if not isinstance(val, str) or not val:
                    continue
                role = _THEME_ROLE_OF.get(val.lower())
                if role is not None and role in roles:
                    try:
                        w.configure(**{opt: p[role]})
                    except Exception:
                        pass
        # 日志标签按主题重配（正文两档 + 状态/强调色深浅自适应）
        try:
            self.log_ok.tag_configure('ok', foreground=p['TAG_OK'])
            self.log_ok.tag_configure('warn', foreground=p['TAG_WARN'])
            self.log_ok.tag_configure('hash', foreground=p['TAG_OK'])
            self.log.tag_configure('dim', foreground=p['TAG_DIM'])
            self.log.tag_configure('gray', foreground=p['TAG_GRAY'])
            self.log.tag_configure('accent', foreground=p['TAG_ACCENT'])
            self.log.tag_configure('ok', foreground=p['TAG_OK'])
            self.log.tag_configure('err', foreground=p['TAG_ERR'])
            self.log.tag_configure('warn', foreground=p['TAG_WARN'])
        except Exception:
            pass
        # 状态控件按记忆的模式重设（保证切主题后 已完成/失败 等提示色同步）
        try:
            if self._chip_mode == 'ok':
                self.chip.config(bg=p['STAT_OK'], fg='#101216')
            elif self._chip_mode == 'err':
                self.chip.config(bg=p['STAT_ERR'], fg='white')
            elif self._chip_mode == 'warn':
                self.chip.config(bg=p['STAT_WARN'], fg='#191c22')
            if self._file_mode == 'ok':
                self.file_label.config(fg=p['STAT_OK'])
            elif self._file_mode == 'err':
                self.file_label.config(fg=p['STAT_ERR'])
            elif self._file_mode == 'warn':
                self.file_label.config(fg=p['STAT_WARN'])
            elif self._file_mode == 'busy':
                self.file_label.config(fg=ACCENT)
        except Exception:
            pass
        try:
            st = ttk.Style(self.root)
            st.configure('TProgressbar', troughcolor=p['CARD2'],
                         bordercolor=p['CARD2'])
            try:
                st.configure('TNotebook', background=p['BG'], borderwidth=0)
                st.configure('TNotebook.Tab', background=p['CARD'],
                             foreground=p['TEXT'], padding=(14, 5))
                st.map('TNotebook.Tab',
                       background=[('selected', ACCENT)],
                       foreground=[('selected', '#191c22')])
            except Exception:
                pass
        except Exception:
            pass
        self.theme = name
        try:
            self.btn_theme.config(text='🌙 夜间主题' if name == 'dark' else '☀️ 日间主题')
        except Exception:
            pass
        try:
            self._tabbar_sync()
        except Exception:
            pass

    def toggle_theme(self):
        name = 'light' if self.theme == 'dark' else 'dark'
        self.apply_theme(name)
        cfg = _load_config()
        cfg['theme'] = name
        _save_config(cfg)
        self._log('已切换到{}主题。'.format('日间' if name == 'light' else '夜间'), 'gray')

    def _setup_styles(self):
        self.root.configure(bg=BG)
        st = ttk.Style(self.root)
        st.theme_use('clam')
        st.configure('TProgressbar', background=ACCENT, troughcolor=CARD2,
                     bordercolor=CARD2, lightcolor=ACCENT, darkcolor=ACCENT,
                     thickness=10)

    def _build_ui(self):
        root = self.root
        root.title('绝区零 Mod 修复工具 {}'.format(APP_VERSION))
        root.geometry('980x660')
        root.minsize(720, 540)

        # ---- 标题 ----
        header = tk.Frame(root, bg=CARD)
        header.pack(fill='x', padx=12, pady=(12, 0))
        tk.Frame(header, bg=ACCENT, width=5).pack(side='left', fill='y')
        tb = tk.Frame(header, bg=CARD)
        tb.pack(side='left', padx=14, pady=8)
        tk.Label(tb, text='绝区零 ZZZ · Mod 修复工具', bg=CARD, fg=TEXT,
                 font=(FONT, 16, 'bold')).pack(anchor='w')
        tk.Label(tb, text='{} 中文版 · GreenLzz / 绿林小子 · 批量修复旧版 .ini 与缓冲区'.format(APP_VERSION),
                 bg=CARD, fg=DIM, font=(FONT, 9)).pack(anchor='w', pady=(2, 0))
        self.btn_theme = tk.Button(header, text='', command=self.toggle_theme,
                                 bg=CARD, fg=DIM, relief='flat',
                                 font=(FONT, 9), padx=8, pady=4, cursor='hand2',
                                 activebackground=CARD2, activeforeground=TEXT,
                                 highlightthickness=0)
        self.btn_theme.pack(side='right', padx=(0, 6), pady=6)
        self.chip = tk.Label(header, text='就绪', bg=CARD2, fg=DIM,
                             font=(FONT, 9, 'bold'), padx=12, pady=6)
        self.chip.pack(side='right', padx=(0, 14))
        self.btn_update = tk.Button(header, text='检查更新', command=self.manual_update_check,
                                    bg=CARD2, fg=TEXT, relief='flat', cursor='hand2',
                                    font=(FONT, 9), padx=10, pady=4,
                                    activebackground=ACCENT, activeforeground='#191c22',
                                    highlightthickness=0)
        self.btn_update.pack(side='right', padx=(0, 8), pady=6)

        # ---- 路径卡片 ----
        card = tk.Frame(root, bg=CARD)
        card.pack(fill='x', padx=12, pady=(10, 0))
        for c in range(4):
            card.columnconfigure(c, weight=1 if c == 1 else 0)
        # 默认路径行
        tk.Label(card, text='默认修复路径', bg=CARD, fg=TEXT,
                 font=(FONT, 9)).grid(row=0, column=0, padx=(14, 8), pady=(8, 3), sticky='w')
        self.default_entry = self._entry(card)
        self.default_entry.grid(row=0, column=1, pady=(8, 3), sticky='ew')
        self.btn_def_pick = self._btn(card, '选择路径', self.pick_default)
        self.btn_def_pick.grid(row=0, column=2, padx=(8, 4), pady=(8, 3))
        self.btn_def_clear = self._btn(card, '清除', self.clear_default)
        self.btn_def_clear.grid(row=0, column=3, padx=(0, 14), pady=(8, 3))
        # 手动路径行
        tk.Label(card, text='手动修复路径', bg=CARD, fg=TEXT,
                 font=(FONT, 9)).grid(row=1, column=0, padx=(14, 8), pady=(0, 3), sticky='w')
        self.manual_entry = self._entry(card)
        self.manual_entry.grid(row=1, column=1, pady=(0, 3), sticky='ew')
        self.btn_man_pick = self._btn(card, '选择路径', self.pick_manual)
        self.btn_man_pick.grid(row=1, column=2, padx=(8, 4), pady=(0, 3))
        self.btn_man_clear = self._btn(card, '清空', self.clear_manual)
        self.btn_man_clear.grid(row=1, column=3, padx=(0, 14), pady=(0, 3))

        # 勾选：是否把默认修复路径纳入修复
        self.use_default = tk.BooleanVar(value=True)
        self.chk_default = tk.Checkbutton(card, text='✔ 修复时包含“默认修复路径”',
                                          variable=self.use_default, bg=CARD, fg=TEXT,
                                          activebackground=CARD, activeforeground=TEXT,
                                          selectcolor=CARD2, font=(FONT, 9),
                                          highlightthickness=0, cursor='hand2',
                                          command=self._on_use_default_toggle)
        self.chk_default.grid(row=2, column=0, columnspan=4, padx=14, pady=(0, 0), sticky='w')

        tk.Label(card,
                 text='选择路径自动保存；可填文件夹或 .ini 文件；多个路径用 ; 分隔；修复直接处理两栏路径。',
                 bg=CARD, fg=DIM, font=(FONT, 8), justify='left').grid(
            row=3, column=0, columnspan=4, padx=14, pady=(0, 8), sticky='w')

        # ---- 日志（单窗页签：点击页签切换 已更新 / 完整 内容） ----
        lbar = tk.Frame(root, bg=BG)
        lbar.pack(fill='x', padx=18, pady=(10, 0))
        self._mini_btn(lbar, '清空当前日志', self.clear_current_log).pack(side='right', padx=(0, 4))
        tk.Checkbutton(lbar, text='自动滚动', variable=self.auto_scroll, bg=BG,
                       fg=DIM, activebackground=BG, activeforeground=TEXT,
                       selectcolor=CARD2, font=(FONT, 8),
                       highlightthickness=0).pack(side='right')
        # ---- 日志页签组（自绘）：左=运行（完整/已更新），右=文档（版本更新/Hash变动），互不相连 ----
        tabbar = tk.Frame(root, bg=BG)
        tabbar.pack(fill='x', padx=12, pady=(6, 0))
        run_grp = tk.Frame(tabbar, bg=BG)
        run_grp.pack(side='left')
        doc_grp = tk.Frame(tabbar, bg=BG)
        doc_grp.pack(side='right')
        # 手工叠页容器（无系统页签条），页面由上方两组按钮切换
        nb_host = tk.Frame(root, bg=CARD2, highlightthickness=1,
                           highlightbackground=LINE)
        nb_host.pack(fill='both', expand=True, padx=12, pady=(6, 8))
        nb = _LogNotebook(nb_host)

        # 页1：已更新日志
        f_ok = tk.Frame(nb_host, bg=CARD2)
        self.log_ok = tk.Text(f_ok, bg=CARD2, fg=TEXT, relief='flat',
                              highlightthickness=1, highlightbackground=LINE,
                              font=('Consolas', 9), wrap='word', state='disabled',
                              padx=8, pady=6, height=6)
        oksb = tk.Scrollbar(f_ok, orient='vertical', command=self.log_ok.yview)
        self.log_ok.configure(yscrollcommand=oksb.set)
        oksb.pack(side='right', fill='y')
        self.log_ok.pack(side='left', fill='both', expand=True)
        # 已更新日志：默认整体正常字色；备份/更新修复证据行与完整日志同款色；
        # 更新行里的 hash = 值单独染绿
        self.log_ok.tag_configure('ok', foreground=OK, font=(FONT, 9))
        self.log_ok.tag_configure('warn', foreground=WARN, font=(FONT, 9))
        self.log_ok.tag_configure('hash', foreground=OK, font=(FONT, 9))

        # 完整日志排在首（默认选中页）
        f_full = tk.Frame(nb_host, bg=CARD2)
        self.log = tk.Text(f_full, bg=CARD2, fg=TEXT, relief='flat',
                           highlightthickness=1, highlightbackground=LINE,
                           font=('Consolas', 9), wrap='none', state='disabled',
                           padx=8, pady=6, height=6)
        lsb = tk.Scrollbar(f_full, orient='vertical', command=self.log.yview)
        self.log.configure(yscrollcommand=lsb.set)
        lsb.pack(side='right', fill='y')
        self.log.pack(side='left', fill='both', expand=True)
        for tag, color, bold in (('ok', OK, False), ('err', ERR, True), ('warn', WARN, False),
                                 ('accent', ACCENT, True), ('dim', DIM, False),
                                 ('gray', '#5d6675', False)):
            self.log.tag_configure(tag, foreground=color,
                                   font=(FONT, 9, 'bold') if bold else (FONT, 9))
        nb.add(f_full, text='  完整日志  ')
        nb.add(f_ok, text='   已更新日志  ')
        # 页3：版本更新日志（同目录 txt 优先，无则用内嵌文本）
        f_hist = tk.Frame(nb_host, bg=CARD2)
        self.log_hist = tk.Text(f_hist, bg=CARD2, fg=TEXT, relief='flat',
                                highlightthickness=1, highlightbackground=LINE,
                                font=('Consolas', 9), wrap='word', state='disabled',
                                padx=10, pady=6, height=6)
        hsb = tk.Scrollbar(f_hist, orient='vertical', command=self.log_hist.yview)
        self.log_hist.configure(yscrollcommand=hsb.set)
        hsb.pack(side='right', fill='y')
        self.log_hist.pack(side='left', fill='both', expand=True)
        self.log_hist.configure(state='normal')
        self.log_hist.insert('1.0', _doc_text('zzz_fix更新日志.txt', CHANGELOG_TEXT))
        self.log_hist.configure(state='disabled')
        nb.add(f_hist, text='   版本更新日志  ')
        # 页4：Hash 变动日志（同目录 Hash变动日志.txt 优先，无则用内嵌文本）
        f_hash = tk.Frame(nb_host, bg=CARD2)
        self.log_hash = tk.Text(f_hash, bg=CARD2, fg=TEXT, relief='flat',
                                highlightthickness=1, highlightbackground=LINE,
                                font=('Consolas', 9), wrap='word', state='disabled',
                                padx=10, pady=6, height=6)
        hash_sb = tk.Scrollbar(f_hash, orient='vertical', command=self.log_hash.yview)
        self.log_hash.configure(yscrollcommand=hash_sb.set)
        hash_sb.pack(side='right', fill='y')
        self.log_hash.pack(side='left', fill='both', expand=True)
        self.log_hash.configure(state='normal')
        self.log_hash.insert('1.0', _doc_text('Hash变动日志.txt', HASHLOG_TEXT))
        self.log_hash.configure(state='disabled')
        nb.add(f_hash, text='   Hash变动日志  ')
        self.nb = nb
        # ---- 自绘页签按钮：左组=运行页（完整/已更新），右组=文档页（版本更新/Hash变动） ----
        self._page_btns = []   # (按钮, nb 页 text)
        for grp, label in ((run_grp, '完整日志'), (run_grp, '已更新日志'),
                           (doc_grp, '版本更新日志'), (doc_grp, 'Hash变动日志')):
            b = tk.Button(grp, text=label, relief='flat', cursor='hand2',
                          font=(FONT, 9), padx=12, pady=4, highlightthickness=0,
                          bg=CARD, fg=TEXT, activebackground=CARD2, activeforeground=TEXT)
            b.pack(side='left')
            b.configure(command=lambda l=label: self._goto_log_page(l))
            self._page_btns.append((b, label))
        nb.onselect = self._tabbar_sync
        self._tabbar_sync()
        # 记下已更新页签 id：有更新时自动跳过去
        self._tab_ok = next((t for t in nb.tabs()
                             if '已更新' in nb.tab(t, 'text')), nb.tabs()[0])

        # ---- 底部 ----
        bottom = tk.Frame(root, bg=CARD)
        bottom.pack(fill='x', padx=12, pady=(0, 12))
        tr = tk.Frame(bottom, bg=CARD)
        tr.pack(fill='x', padx=14, pady=(6, 2))
        self.progress = ttk.Progressbar(tr, maximum=100)
        self.progress.pack(side='left', fill='x', expand=True)
        self.prog_label = tk.Label(tr, text='', bg=CARD, fg=DIM,
                                   font=(FONT, 9), width=10, anchor='e')
        self.prog_label.pack(side='right', padx=(10, 0))
        # 状态行（独占一行，窄窗口自动换行，不挤压按钮）
        self.file_label = tk.Label(bottom, text='就绪。填入路径后点击“开始修复”。', bg=CARD,
                                   fg=DIM, font=(FONT, 9), anchor='w', justify='left')
        self.file_label.pack(fill='x', padx=14, pady=(1, 0))
        # 按钮行：右侧只放按钮
        ar = tk.Frame(bottom, bg=CARD)
        ar.pack(fill='x', padx=14, pady=(3, 8))
        self.btn_run = self._btn(ar, '▶ 开始修复', self.start_repair, accent=True)
        self.btn_run.pack(side='right')
        # 链接按钮：mod指南 / 更多修复工具（网址见文件顶部 URL_MOD_GUIDE / URL_MORE_TOOLS）
        b1 = self._btn(ar, 'Mod 指南', lambda: self._open_url(URL_MOD_GUIDE))
        b1.pack(side='left', padx=(0, 6))
        b2 = self._btn(ar, '更多修复工具', lambda: self._open_url(URL_MORE_TOOLS))
        b2.pack(side='left')
        # 窗口变宽/变窄时给两行状态文字设自动换行宽度
        def _wrap(ev=None):
            w = bottom.winfo_width() - 28
            if w > 60:
                self.file_label.config(wraplength=w)
        bottom.bind('<Configure>', _wrap)

    def _open_url(self, url):
        """在默认浏览器中打开网址（放线程防卡界面）"""
        threading.Thread(target=lambda: webbrowser.open(url), daemon=True).start()

    def _entry(self, parent):
        return tk.Entry(parent, bg=CARD2, fg=TEXT, insertbackground=TEXT, relief='flat',
                        highlightthickness=1, highlightbackground=LINE,
                        highlightcolor=ACCENT, font=(FONT, 9))

    def _btn(self, parent, text, cmd, accent=False):
        bg, fg = DARK_BTN, TEXT
        if accent:
            bg, fg = ACCENT, '#191c22'
        b = tk.Button(parent, text=text, command=cmd, bg=bg, fg=fg, relief='flat',
                      font=(FONT, 11, 'bold') if accent else (FONT, 9),
                      padx=22 if accent else 8, pady=6 if accent else 4,
                      cursor='hand2', highlightthickness=0)
        if accent:
            b.configure(activebackground='#ffcf00', activeforeground='#191c22')
        else:
            b.configure(activebackground=DARK_BTN_H, activeforeground=TEXT)
        return b

    def _mini_btn(self, parent, text, cmd):
        return tk.Button(parent, text=text, command=cmd, bg=BG, fg=DIM, relief='flat',
                         font=(FONT, 8), padx=6, cursor='hand2',
                         activebackground=CARD2, activeforeground=TEXT, highlightthickness=0)

    def _on_use_default_toggle(self):
        """勾选状态即时保存到配置"""
        cfg = _load_config()
        if self.use_default.get():
            cfg['use_default'] = True
        else:
            cfg['use_default'] = False
        _save_config(cfg)
        if self.use_default.get():
            self._log('已启用默认修复路径：本次同时修复“默认修复路径”与“手动修复路径”。', 'ok')
        else:
            self._log('已停用默认修复路径：本次只修复“手动修复路径”中的文件。', 'warn')
        self._show_full_log()   # 勾选反馈只在完整日志页可见

    # ---------------- 路径操作 ----------------
    def _goto_log_page(self, label):
        """点自绘页签按钮 → 切到对应 Notebook 页（按文字定位）"""
        try:
            for t in self.nb.tabs():
                if label in self.nb.tab(t, 'text'):
                    if self.nb.select() != t:
                        self.nb.select(t)
                    break
        except Exception:
            pass

    def _tabbar_sync(self, ev=None):
        """Notebook 选中页变化 → 高亮自绘页签按钮（左组/右组只亮一个）。
        颜色按当前日夜主题取：选中态 夜=霓虹黄黑字 / 昼=蓝底白字，未选中用各主题按钮底色"""
        try:
            cur = self.nb.tab(self.nb.select(), 'text')
            p = THEMES.get(getattr(self, 'theme', None) or 'dark', THEMES['dark'])
            on_bg, on_fg = ((ACCENT, '#191c22') if p is THEMES['dark']
                            else ('#1976d2', '#ffffff'))
            for b, label in self._page_btns:
                on = label in cur
                b.configure(bg=on_bg if on else p['BTN'],
                            fg=on_fg if on else p['TEXT'],
                            activebackground=p['BTN_H'])
        except Exception:
            pass

    def _show_full_log(self):
        """切到“完整日志”页签（按文字定位，不赌页签顺序），路径操作反馈只在完整日志可见"""
        try:
            full = next((t for t in self.nb.tabs()
                         if '完整日志' in self.nb.tab(t, 'text')), None)
            target = full if full is not None else self.nb.tabs()[0]
            # 延迟一帧再切，避免被同批次积压的“已更新日志”跳转覆盖
            def _go():
                try:
                    if self.nb.select() != target:
                        self.nb.select(target)
                except Exception:
                    pass
            self.root.after(1, _go)
        except Exception:
            pass

    def pick_default(self):
        d = filedialog.askdirectory(parent=self.root, title='选择默认修复文件夹（会自动保存）')
        if d:
            d = os.path.abspath(d)
            self.default_entry.delete(0, 'end')
            self.default_entry.insert(0, d)
            self._save_paths()
            self._log('默认修复文件夹已保存: {}'.format(d), 'accent')
            self._show_full_log()   # 让反馈落在完整日志页可见，不留在更新页签

    def pick_manual(self):
        d = filedialog.askdirectory(parent=self.root, title='选择手动修复文件夹')
        if d:
            self._append_manual([os.path.abspath(d)])
            self._log('已添加手动修复路径: {}'.format(os.path.abspath(d)), 'gray')
            self._show_full_log()

    def clear_default(self):
        self.default_entry.delete(0, 'end')
        self._save_paths()
        self._log('已清除默认修复文件夹', 'gray')
        self._show_full_log()

    def clear_manual(self):
        self.manual_entry.delete(0, 'end')
        self._save_paths()
        self._log('已清空手动修复路径', 'gray')
        self._show_full_log()

    def _append_manual(self, paths):
        # 栏内文本是我们自己用 '; ' 拼出来的规范格式：只按分号拆，
        # 绝不用空格拆分 —— 否则含空格的目录（如 Zenless Zone Zero）会被切成碎片再拼错
        cur = [t.strip() for t in re.split(r'[;；]', self.manual_entry.get() or '')]
        parts = [t for t in cur if t]
        have = {os.path.normcase(os.path.realpath(x)) for x in parts}
        for p in paths:
            clean = clean_gui_path(p)
            if not clean:
                continue
            key = os.path.normcase(os.path.realpath(clean))
            if key not in have:
                parts.append(clean)
                have.add(key)
        self.manual_entry.delete(0, 'end')
        self.manual_entry.insert(0, '; '.join(parts))
        self._save_paths()

    def _entry_paths(self):
        """拆出两栏全部路径，并用原命令行逻辑规范化
        （去首尾引号、剥离 file:/// 前缀、正斜杠转反斜杠）"""
        out = []
        for raw in (self.default_entry.get(), self.manual_entry.get()):
            for t in re.split(r'[;；]', raw or ''):
                t = t.strip()
                if not t:
                    continue
                clean = clean_gui_path(t)
                if clean:
                    out.append(clean)
        return out

    def _save_paths(self):
        cfg = _load_config()
        d = self.default_entry.get().strip()
        if d:
            cfg['default_folder'] = d
        else:
            cfg.pop('default_folder', None)
        # 手动路径只在本次运行有效，不持久化（重启窗口后自动清空）
        cfg.pop('manual_paths', None)
        _save_config(cfg)

    def _on_dnd_event(self, event):
        paths = split_drop_text(getattr(event, 'data', ''))
        if not paths:
            return
        # 带空格的文件名可能被空格拆开：用原命令行拼接逻辑恢复
        recovered = resolve_spaced_tokens(paths)
        if recovered != paths:
            self._log('检测到空格路径片段，已自动拼接恢复。', 'gray')
        paths = recovered
        if self.running:
            self._log('修复进行中，已忽略拖入的文件。', 'warn')
            return
        self._log('收到拖入: {}'.format(
            '、'.join(os.path.basename(p.rstrip(chr(47) + chr(92))) or p for p in paths)), 'accent')
        self._append_manual(paths)

    # ---------------- 日志（命令行式流式输出：有界队列 + 定量落屏，永不多跑一步） ----------------
    def _classify(self, line):
        if ('发生错误' in line or '致命错误' in line or '未修复' in line
                or '失败' in line or '无法读取' in line or '路径不存在' in line
                or 'Traceback' in line):
            return 'err'
        if '已创建备份' in line or '已备份缓冲区' in line or '已保存默认' in line:
            return 'warn'
        if '更新修复' in line and '没有' not in line:
            return 'ok'
        if '没有对该' in line or '已是最新' in line:
            return 'gray'
        if line.startswith('=') or line.startswith('-'):
            return 'gray'
        return 'dim'

    def _enqueue(self, text, tag=None):
        """把原始输出追加进有界行队列（超出 MAX_LINES 丢最旧，行为同终端滚动）。
        tag 指定时这些行按固定配色入队（逐行打包，不与其他批次串扰）"""
        if not text:
            return
        self._part += text
        q = self._pend
        while True:
            i = self._part.find(NL)
            if i < 0:
                break
            line = self._part[:i] + NL
            q.append((line, tag) if tag else line)
            if is_updated_line(line):
                # 与完整日志同款判定：备份/缓冲保存=warn，更新修复完成=ok
                self._pend_ok.append((line, self._classify(line)))
                over = len(self._pend_ok) - MAX_OK_LINES
                if over > 0:
                    for _ in range(over):
                        self._pend_ok.popleft()
            self._part = self._part[i + 1:]
        over = len(q) - MAX_LINES
        if over > 0:
            for _ in range(over):
                q.popleft()

    def _log(self, text, tag=None):
        """控制消息入待显示队列；tag 指定整段固定配色。自动补换行，防止滞留半行缓冲"""
        if text and not text.endswith(NL):
            text += NL
        self._enqueue(text, tag)

    def _insert_tick(self):
        """每 tick 定量落屏；返回是否还有剩余待显示内容"""
        q = self._pend
        if not q:
            return False
        take = TICK_MAX if len(q) > TICK_MAX else len(q)
        chunks = []
        for _ in range(take):
            chunks.append(q.popleft())
        # 逐行配色（python 侧，廉价），相邻同色合并后一次 insert
        args = []
        last_tag = None
        buf = []
        def push():
            args.append(''.join(buf))
            args.append(last_tag)
        for item in chunks:
            if isinstance(item, tuple):
                ln, tag = item
            else:
                ln, tag = item, self._classify(item)
            if tag != last_tag and buf:
                push()
                buf = []
            last_tag = tag
            buf.append(ln)
        if buf:
            push()
        flat = []
        for i in range(0, len(args), 2):
            flat.append(args[i])
            flat.append(args[i + 1])
        self.log.configure(state="normal")
        self.log.insert("end", *flat)
        self.log_lines += take
        self.log.configure(state="disabled")
        if self.log_lines > MAX_LINES:
            # 顶部按行号删除（"N.0" 是合法索引；"N lines" 相对索引非法）
            remove = self.log_lines - MAX_LINES
            self.log.configure(state="normal")
            self.log.delete("1.0", "%d.0" % (remove + 1))
            self.log.configure(state="disabled")
            self.log_lines = MAX_LINES
        if self.auto_scroll.get():
            self.log.see("end")
        return bool(q)

    def clear_current_log(self):
        """清空当前页签日志；按页签文字路由，与页签顺序无关"""
        try:
            if getattr(self, 'nb', None) is not None:
                if '已更新' in self.nb.tab(self.nb.select(), 'text'):
                    self.clear_log_ok()
                    return
        except Exception:
            pass
        self.clear_log()

    def clear_log_ok(self):
        try:
            self.log_ok.configure(state='normal')
            self.log_ok.delete('1.0', 'end')
            self.log_ok.configure(state='disabled')
        except Exception:
            pass
        self._pend_ok.clear()

    def clear_log(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")
        self.log_lines = 0
        self._pend.clear()
        self._part = ""
        self.clear_log_ok()

    # ---------------- 消息泵（每次回调：清空队列入有界缓存 → 定量落屏） ----------------
    def poll_queue(self):
        while True:
            try:
                ev = self.q.get_nowait()
            except queue.Empty:
                break
            if ev[0] == "upd_msg":
                _, tag, txt = ev
                self._log(txt, tag)
            elif ev[0] == "upd_prog":
                p = ev[1]
                self.progress.configure(maximum=100, value=p)
                self.prog_label.config(text='{}%'.format(p))
                self.btn_update.config(text='下载 {}%'.format(p))
            elif ev[0] == "upd_prompt":
                self._upd_show_prompt(ev[1])
            elif ev[0] == "upd_pending":
                # 启动自动检查发现新版：不弹窗打扰，按钮改"可更新"并闪烁提醒
                info = ev[1]
                self._upd_info = info
                self._upd_pending = True
                self._upd_flash = False
                try:
                    self.btn_update.config(
                        text='发现新版 {}! 点此更新'.format(info['new']), state='normal')
                except Exception:
                    pass
                self.root.after(0, self._flash_update_btn)
            elif ev[0] == "upd_stale":
                # 已被忽略的版本：只静态显示有更新，不闪烁不弹窗
                self._upd_btn_static(ev[1])
            elif ev[0] == "upd_done":
                self._upd_finish(ev[1])
            elif ev[0] == "upd_fail":
                _, msg = ev
                self._upd_reset()
                self._log(msg, 'err')
                messagebox.showerror('更新失败', msg, parent=self.root)
            elif ev[0] == "out":
                self._enqueue(ev[1])
            elif ev[0] == "oklog":
                _, fp, hlog = ev
                blk = ['▍ {}'.format(os.path.basename(fp))]
                acts = {}      # act -> 有序 hash 列表
                order = []
                for h, t in hlog:
                    ts = t.strip()
                    if not ts.startswith('+'):
                        continue   # 跳过/版本标题等非实际变更行不显示，只留真实更新
                    act = ts[1:].strip()
                    if act not in acts:
                        acts[act] = []
                        order.append(act)
                    acts[act].append(h or '?')
                for act in order:
                    hs = acts[act]
                    if act.startswith('添加'):
                        # 添加 run 的多个 hash 合并为一行
                        note = act.replace('`', '')
                        if note.startswith('添加'):
                            note = '添加了' + note[2:]
                        blk.append('  hash = {} {}'.format('、'.join(hs), note))
                    else:
                        for h in hs:
                            blk.append('  hash {}: {}'.format(h, act))
                blk.append('')
                for _line in blk:
                    # 文件名头行绿，内容行默认正常字色
                    tag = 'ok' if _line.startswith('▍') else None
                    self._pend_ok.append((_line, tag))
                over = len(self._pend_ok) - MAX_OK_LINES
                if over > 0:
                    for _ in range(over):
                        self._pend_ok.popleft()
            elif ev[0] == "prog":
                _, idx, total, fp, c, n, f = ev
                self.progress.configure(maximum=max(total, 1), value=idx)
                self.prog_label.config(text="{}/{}".format(idx, total))
                name = os.path.basename(fp)
                if len(name) > 56:
                    name = name[:27] + "…" + name[-28:]
                # 实时计数常驻状态行：滚动再快也一眼看清本次进度与结果
                self.file_label.config(
                    text="处理 {name} ｜ 已更新 {c} · 无需更新 {n} · 失败 {f}".format(
                        name=name[:40], c=c, n=n, f=f),
                    fg=THEMES[self.theme]['STAT_ERR'] if f else ACCENT)
                self._file_mode = 'err' if f else 'busy'
            elif ev[0] == "done":
                self._finish_run(ev[1], ev[2], ev[3])
            elif ev[0] == "aborted":
                self._log("已停止（用户取消）" + NL, "warn")
                self._finish_run(None, None, None, aborted=True)
        # 待显示内容越多、单 tick 落屏越多：保证旧任务结束后队列快速清零，绝不长阻塞
        if self._pend:
            for _ in range(4):
                if not self._insert_tick():
                    break
        # 已更新流（量小，一次刷完；默认正常色，证据行单独着 ok/warn）
        if self._pend_ok:
            jumped = False
            self.log_ok.configure(state='normal')
            while self._pend_ok:
                line, tag = self._pend_ok.popleft()
                if not jumped and line.strip():
                    jumped = True
                # 更新行（hash xxx: ... 更新为 ...）中 hash = 的值染绿，
                # 其余分段正常色；整行分行插入，无索引算术
                if tag is None and '更新为' in line:
                    i = 0
                    for m in _HASH_TOKEN.finditer(line):
                        a, b = m.start() + 7, m.end()   # 跳过 'hash = ' 前缀
                        self.log_ok.insert('end', line[i:a], tag or None)
                        self.log_ok.insert('end', line[a:b], 'hash')
                        i = b
                    line = line[i:]                     # 剩余尾部照常色
                if line:
                    self.log_ok.insert('end', line if line.endswith(NL) else line + NL, tag or None)
            self.log_ok.configure(state='disabled')
            self.log_ok.see('end')
            if jumped:
                try:
                    if self.nb.select() != self._tab_ok:
                        self.nb.select(self._tab_ok)   # 有新更新内容 → 跳转到更新页
                except Exception:
                    pass

    def _poll_safe(self):
        """poll_queue 的异常保险壳：任何意外都不允许中断刷新链"""
        try:
            self.poll_queue()
        except Exception:
            try:
                self._enqueue("内部显示错误（不影响修复）" + NL)
            except Exception:
                pass
        self.root.after(25, self._poll_safe)

    # ---------- 消息泵入口 ----------
    def _poll_start(self):
        self.root.after(25, self._poll_safe)

    # ---------------- 修复流程 ----------------
    def start_repair(self):
        if getattr(self, '_updating', False):
            messagebox.showinfo('提示', '正在检查/下载更新，请稍候再开始修复。', parent=self.root)
            return
        if self.running:
            self.cancel_event.set()
            self.chip.config(text='正在停止…',
                             bg=THEMES[self.theme]['STAT_WARN'], fg='#191c22')
            self._chip_mode = 'warn'
            self.btn_run.config(state='disabled')
            return
        self._save_paths()
        if self.use_default.get():
            raw_paths = self._entry_paths()
        else:
            raw_paths = [t for t in self._entry_paths()
                         if os.path.normcase(os.path.realpath(t)) != os.path.normcase(os.path.realpath(self.default_entry.get().strip()))]
        plan, disabled, notes = collect_targets(raw_paths)
        if notes:
            self._log(chr(10).join('  · ' + n for n in notes))
        if disabled:
            names = '、'.join(os.path.basename(d) for d in disabled[:5])
            if len(disabled) > 5:
                names += ' 等'
            self._log('跳过 {} 个已禁用文件（DISABLED_*.ini）：{}'.format(len(disabled), names))
        if not plan:
            messagebox.showinfo('提示', '请先在顶部填入有效的文件夹或 .ini 路径。'
                                        '（可用“选择路径”按钮或直接把文件拖入窗口）', parent=self.root)
            return
        self.running = True
        self.cancel_event = threading.Event()
        self.btn_run.config(text='■ 停止修复', bg=DANGER, fg='white',
                            activebackground='#a52f23', activeforeground='white')
        self._set_edit_enabled(False)
        self.progress.configure(value=0, maximum=max(len(plan), 1))
        self.prog_label.config(text='0/{}'.format(len(plan)))
        self.chip.config(text='修复中', bg=ACCENT, fg='#191c22')
        self._chip_mode = None
        self.file_label.config(text='', fg=DIM)
        self._file_mode = None
        self._log('=' * 62, 'gray')
        self._log('开始修复：共 {} 个 .ini 文件'.format(len(plan)), 'accent')
        self._log('=' * 62, 'gray')
        threading.Thread(target=repair_worker,
                         args=(list(plan), self.q, self.cancel_event),
                         daemon=True).start()

    def _finish_run(self, changed, nochange, failed, aborted=False):
        self.running = False
        self.btn_run.config(text='▶ 开始修复', bg=ACCENT, fg='#191c22',
                            activebackground='#ffcf00', state='normal')
        self._set_edit_enabled(True)
        if aborted:
            self.chip.config(text='已停止',
                             bg=THEMES[self.theme]['STAT_WARN'], fg='#191c22')
            self._chip_mode = 'warn'
            self.file_label.config(text='已停止。',
                                   fg=THEMES[self.theme]['STAT_WARN'])
            self._file_mode = 'warn'
            return
        self._log('-' * 62, 'gray')
        if failed:
            msg = '修复完成（有失败项）：更新 {} · 无需更新 {} · 失败 {}'.format(changed, nochange, failed)
            self.chip.config(text='部分失败',
                             bg=THEMES[self.theme]['STAT_ERR'], fg='white')
            self._chip_mode = 'err'
            self.file_label.config(
                text='完成：{} 已更新 · {} 无需更新 · {} 失败（详见日志）'.format(changed, nochange, failed),
                fg=THEMES[self.theme]['STAT_ERR'])
            self._file_mode = 'err'
        else:
            msg = '修复完成：全部成功 ✔'
            self.chip.config(text='完成 ✔',
                             bg=THEMES[self.theme]['STAT_OK'], fg='#101216')
            self._chip_mode = 'ok'
            self.file_label.config(
                text='完成：{} 个已更新 · {} 个已是最新（备份 DISABLED_BACKUP_*）'.format(changed, nochange),
                fg=THEMES[self.theme]['STAT_OK'])
            self._file_mode = 'ok'
        self._log(msg, 'accent')
        # 结束页签跳转：有实际修复内容 → 已更新日志；无 → 完整日志
        try:
            if changed:
                target = self._tab_ok
            else:
                target = next((t for t in self.nb.tabs()
                               if '完整日志' in self.nb.tab(t, 'text')), self.nb.tabs()[0])
            if self.nb.select() != target:
                self.nb.select(target)
        except Exception:
            pass

    def _set_edit_enabled(self, en):
        st = 'normal' if en else 'disabled'
        for b in (self.btn_def_pick, self.btn_def_clear, self.btn_man_pick,
                  self.btn_man_clear):
            b.config(state=st)

    # ---------------- 自动更新 ----------------
    def _upd_reset(self):
        """恢复按钮/进度条到空闲态（同时清除待处理新版标记，停闪烁）"""
        self._updating = False
        self._update_tmp = None
        self._upd_pending = False
        self._upd_info = None
        try:
            p = THEMES[self.theme]
            self.btn_update.config(text='检查更新', state='normal',
                                   background=p['BTN'], foreground=p['TEXT'])
        except Exception:
            pass
        self.progress.configure(maximum=100, value=0)
        self.prog_label.config(text='')

    def _flash_update_btn(self):
        """按钮提醒闪烁：有新版待处理时每 500ms 在 警告黄底/主题按钮色 间交替（两主题均清晰）"""
        if not self._upd_pending or self._updating:
            return
        self._upd_flash = not self._upd_flash
        try:
            p = THEMES[self.theme]
            if self._upd_flash:
                self.btn_update.config(background=p['STAT_WARN'], foreground='#191c22')
            else:
                self.btn_update.config(background=p['BTN'], foreground=p['TEXT'])
        except Exception:
            pass
        self.root.after(500, self._flash_update_btn)

    def _upd_btn_static(self, newver):
        """忽略后的静态提醒：按钮显示有更新但不闪烁，点开仍可手动查看"""
        try:
            p = THEMES[self.theme]
            self.btn_update.config(text='有新版 {}'.format(newver), state='normal',
                                   background=p['BTN'], foreground=p['TEXT'])
        except Exception:
            pass

    def _upd_show_prompt(self, info):
        """主线程：新版选择框。是=自动更新；否=手动更新；取消=忽略该版本（不再自动提醒）"""
        auto_txt = ('当前版本：{}\n最新版本：{}\n\n'
                    '选择更新方式：\n\n'
                    '  是(Y) - 自动更新：下载后自动覆盖并重启，约需 5~10 秒\n'
                    '  否(N) - 手动更新：仅下载压缩包，自行解压替换\n'
                    '  取消 - 忽略此版本，不再提醒（可点“检查更新”手动查看）'
                    ).format(APP_VERSION, info['new'])
        ask = messagebox.askyesnocancel(
            '发现新版本 {}'.format(info['new']), auto_txt, parent=self.root)
        if ask is None:
            # 取消 = 记入忽略列表：下次启动不再闪烁/弹窗，仅按钮静态提示有更新
            try:
                cfg = _load_config()
                cfg['update_ignored'] = info['new']
                _save_config(cfg)
            except Exception:
                pass
            self._log('已忽略版本 {}，之后仅按钮提示，不闪烁不弹窗'.format(info['new']), 'gray')
            self._upd_reset()
            self._upd_btn_static(info['new'])
            return
        self._upd_auto = bool(ask)     # 是=自动更新；否=手动
        self._upd_pending = False
        self._upd_info = None
        self._upd_begin_download(info)

    def manual_update_check(self):
        if self._updating:
            return
        if self.running:
            messagebox.showinfo('提示', '修复正在进行，请结束后再检查更新。', parent=self.root)
            return
        if self._upd_pending and self._upd_info:
            self._upd_show_prompt(self._upd_info)   # 已有待处理新版：直接弹选择框
            return
        threading.Thread(target=self._upd_check_worker, args=(True,), daemon=True).start()

    def _auto_update_check(self):
        """启动后自动静默检查：只有发现新版才提示，其余情况零输出"""
        if self._updating or self.running:
            return
        threading.Thread(target=self._upd_check_worker, args=(False,), daemon=True).start()

    def _upd_check_worker(self, manual=False):
        """后台线程：查版本。结果经队列回到主线程，避免跨线程碰 tkinter。
        manual=True = 点按钮检查：逐步写日志给反馈；
        manual=False = 启动自动：无更新/出错都静默，仅发现新版时提示"""
        if not _upd_configured():
            if manual:
                self.q.put(('upd_msg', 'warn',
                            '尚未配置更新仓库：填写代码顶部 GITEE_REPO / GITHUB_REPO，'
                            '或设置文件 update_gitee_repo / update_github_repo'))
            return   # 未配置：不置 busy、不打扰
        self._updating = True
        if manual:
            self.q.put(('upd_msg', 'gray', '正在检查更新（Gitee 优先，GitHub 兜底）…'))
            self.q.put(('upd_msg', 'gray', '当前版本 {}'.format(APP_VERSION)))
        try:
            info, note = check_update_now()
        except Exception as e:
            if manual:
                self.q.put(('upd_msg', 'warn', '检查更新失败：{}'.format(e)))
                self.q.put(('upd_done', None))
            else:
                self._updating = False   # 自动检查失败：静默复位，不打扰
            return
        if info is None:
            if manual:
                self.q.put(('upd_done', None))
                if note:
                    self.q.put(('upd_msg', 'warn', note))
                else:
                    self.q.put(('upd_msg', 'gray', '已是最新版本 {}'.format(APP_VERSION)))
            else:
                self._updating = False   # 自动检查已是最新：静默复位
            return
        self.q.put(('upd_done', None))
        self.q.put(('upd_msg', 'accent',
                    '发现新版本 {}（来源文件 {}）'.format(info['new'], info['fname'])))
        if manual:
            self.q.put(('upd_prompt', info))   # 用户主动点按钮：直接弹选择框
            return
        # 启动自动检查：已被用户忽略的版本不再提醒，其余交给按钮闪烁提示
        try:
            ignored = (_load_config() or {}).get('update_ignored')
        except Exception:
            ignored = None
        if ignored == info['new']:
            # 已忽略：不再闪烁打扰，按钮静态显示有更新，点开仍可手动查看
            self.q.put(('upd_stale', info['new']))
            return
        self.q.put(('upd_pending', info))

    def _upd_begin_download(self, info):
        """主线程：用户确认后开始下载"""
        if self._updating:
            self._upd_reset()
        self._updating = True
        self.btn_update.config(text='下载中…', state='disabled')
        self.progress.configure(maximum=100, value=0)
        self.prog_label.config(text='')
        threading.Thread(target=self._upd_download_worker, args=(info,),
                         daemon=True).start()

    def _upd_download_worker(self, info):
        """后台线程：下载。zip 模式直接存为最终压缩包名；py 模式存临时文件待自替换"""
        self._update_tmp = None
        try:
            zdir = os.path.dirname(_program_target())
            if info.get('kind') == 'zip':
                # 手动更新模式：下成正式名字的 zip，用户自行解压替换
                dest = os.path.join(zdir, info['fname'])
                tmp = dest + '.part'
                try:
                    os.remove(tmp)
                except OSError:
                    pass
                _download_file(info['url'], tmp,
                               pct_cb=lambda p: self.q.put(('upd_prog', p)))
                dest = _save_downloaded(tmp, dest)
                self._update_tmp = dest
            else:
                tmp = os.path.join(zdir, '.update_{}.part'.format(os.getpid()))
                try:
                    os.remove(tmp)
                except OSError:
                    pass
                _download_file(info['url'], tmp,
                               pct_cb=lambda p: self.q.put(('upd_prog', p)))
                self._update_tmp = tmp
            self.q.put(('upd_done', info))
        except Exception as e:
            self.q.put(('upd_fail', '下载新版本失败：{}'.format(e)))

    def _upd_finish(self, info):
        """主线程。info 为空 = 本次只是检查（无动作）。
        kind=zip（打包版）：优先自动更新（cmd 原地覆盖+重启），能力缺失时引导手动解压；
        kind=py（源码模式）：当前进程内直接自替换重启"""
        if info is None:
            self._upd_reset()
            return
        if info.get('kind') == 'zip':
            dest = self._update_tmp
            self._update_tmp = None
            self._upd_reset()
            if dest and os.path.exists(dest):
                self._log('新版压缩包已下载：{}'.format(dest), 'accent')
                # 自动更新：拉起 .upd_apply.cmd 后本进程立即退出，cmd 等进程结束
                # 原地覆盖新程序并重启；失败退回手动解压指引
                if self._upd_auto and _spawn_update_cmd(dest):
                    self._log('自动更新中，程序即将退出，安装完成后自动重启。', 'accent')
                    try:
                        sys.stdout, sys.stderr = self._real_stdout, self._real_stderr
                    except Exception:
                        pass
                    # 更新提示窗：bat 在等本进程退出，此时主窗口还开着；
                    # 点确定才关闭并开始更新，避免黑屏空档里用户误以为失败而手动重开
                    messagebox.showinfo(
                        '自动更新中',
                        '新版已下载。\n\n'
                        '点【确定】后程序将退出并开始自动更新，\n'
                        '约需 5~10 秒，完成后自动重启。\n'
                        '期间请勿手动打开程序。',
                        parent=self.root)
                    self._upd_exit()
                    return
                guide = ('新版压缩包已下载到：\n{}\n\n手动更新步骤（请手动操作）：\n'
                         '1. 右键压缩包，选“解压到当前文件夹”，\n'
                         '   提示覆盖时全部选“是/替换”\n'
                         '2. 重新打开程序\n\n'
                         '点【确定】后本窗口关闭（程序退出），按上述步骤手动更新。').format(dest)
                try:
                    # 打开文件夹并选中压缩包，方便用户操作
                    subprocess.Popen(['explorer.exe', '/select,', dest])
                except Exception:
                    pass
                messagebox.showinfo('新版本已下载', guide, parent=self.root)
                # 确认后直接退出：旧程序不再占用文件，用户解压覆盖无阻碍
                self._log('程序即将退出，请按提示解压更新。', 'gray')
                try:
                    sys.stdout, sys.stderr = self._real_stdout, self._real_stderr
                except Exception:
                    pass
                self._upd_exit()
            return
        tmp = self._update_tmp
        self._update_tmp = None
        try:
            tgt = _apply_install(tmp)
        except Exception as e:
            self._upd_reset()
            msg = '安装新版本失败：{}'.format(e)
            self._log(msg, 'err')
            messagebox.showerror('更新失败', msg, parent=self.root)
            return
        self._log('已安装新版本 {}，正在重启…'.format(info['new']), 'accent')
        try:
            subprocess.Popen(_relaunch_command(), cwd=os.path.dirname(tgt) or None,
                             close_fds=True)
        except Exception as e:
            self._log('自动重启失败，请手动重新打开程序：{}'.format(e), 'warn')
            self._upd_reset()
            return
        # 给新实例 1 秒启动时间再退出旧的：onefile exe 引导进程解压/杀软扫描
        # 都在这个窗口里，等它过了再让旧进程退出清理，减少 _MEI 临时目录删除失败
        time.sleep(1.0)
        # 旧进程退出前把 stdout 恢复，避免新进程继承重定向器
        try:
            sys.stdout, sys.stderr = self._real_stdout, self._real_stderr
        except Exception:
            pass
        self._upd_exit()

    def _upd_exit(self):
        """更新流程收尾退出：quit 停 mainloop + destroy 清资源。
        个别环境 destroy 半途异常会被轮询层吞掉导致进程残留，故 quit 先行兜底"""
        try:
            self.root.quit()
        except Exception:
            pass
        try:
            self.root.destroy()
        except Exception:
            os._exit(0)   # 兜底：窗口销毁失败也确保进程结束（更新需释放文件占用）

    # ---------------- 退出 ----------------
    def on_close(self):
        if self.running and not messagebox.askokcancel(
                '退出', '修复仍在进行，确定要停止并退出吗？', parent=self.root):
            return
        if self.running:
            self.cancel_event.set()
        try:
            self._save_paths()
        except Exception:
            pass
        sys.stdout, sys.stderr = self._real_stdout, self._real_stderr
        self.root.destroy()


def gui_main():
    """GUI 入口。argv 中的路径（拖到脚本/exe 上打开）会预加入手动路径。"""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    try:
        from tkinterdnd2 import Tk as DnDTk
    except Exception:
        DnDTk = None

    if DnDTk is not None:
        try:
            root = DnDTk()
        except Exception:
            stale_root = getattr(tk, '_default_root', None)
            if stale_root is not None:
                try:
                    stale_root.destroy()
                except Exception:
                    pass
                tk._default_root = None
            root = tk.Tk()
    else:
        root = tk.Tk()
    # 窗口左上角 + 任务栏图标：打包时经 --add-data 内置，源码头旁需存在 Fairy2.ico
    try:
        if getattr(sys, 'frozen', False):
            base = getattr(sys, '_MEIPASS', None) or os.path.dirname(os.path.abspath(sys.executable))
        else:
            base = os.path.dirname(os.path.abspath(__file__))
        ico = os.path.join(base, 'Fairy2.ico')
        if os.path.isfile(ico):
            root.iconbitmap(ico)
    except Exception:
        pass
    paths = [a for a in sys.argv[1:] if a not in ('--cli', '-c', '--console')]
    App(root, initial_paths=paths or None)
    root.mainloop()


# MARK: 运行
def _run_cli():
    _enable_ansi()
    _cleanup_stale_old()          # 与 GUI 一致：启动时清理更新残留(.upd_apply.cmd/.upd_extract.ps1 等)
    code = _read_update_fail_marker()
    if code:
        print('警告：{}'.format(_update_fail_msg(code)))
    # 启动静默检查：无更新零输出；发现新版才提示（也可在拖放循环输入 update 手动更新）
    direct = [a for a in sys.argv[1:] if a not in ('--cli', '-c', '--console')]
    if not direct and _upd_configured():
        try:
            if cli_check_update():
                return
        except Exception:
            pass   # 自动检查出错静默，不影响正常使用
    try:
        main()
    except Exception as x:
        print('\n发生错误: {}\n'.format(x))
        print(traceback.format_exc())
        input('\n按 "Enter" 退出...\n')


if __name__ == '__main__':
    if any(a in ('--cli', '-c', '--console') for a in sys.argv[1:]):
        _run_cli()
    else:
        try:
            gui_main()
        except tk.TclError as e:
            print('图形界面不可用（{}），切换为命令行模式。'.format(e))
            _run_cli()