# -*- coding: utf-8 -*-
r"""
    索引与顶点修复工具

名字里的两样东西：
    索引 = blend.buf 里的骨骼索引（VGX）
    顶点 = texcoord.buf 里的顶点格式

先选这次用哪一组参照（一组 = dump\ 里的一个文件夹，不按角色合并），
再把那个 mod 的文件夹拖进来，三类问题一起查、一起修：

    一、骨骼索引（VGX）
        blend.buf 里的骨骼索引被写错了
        症状：模型变形（腿弯、塌陷、扭曲），贴图正常
        做法：按角色表把索引逐个换成正确的

    二、顶点格式（texcoord）
        游戏更新改了顶点格式，老 mod 的 buf 布局对不上
        症状：贴图整体错乱，模型形状完全正常
        做法：按目标表重排每个顶点的字节，并同步改 ini 里的 stride

    三、顶点上限（VertexLimitRaise）
        症状：模型炸开、顶点被拉到天上、顶点缓冲溢出（贴图和形状本身看着正常）
        做法：照这个网格的 buf 算真实顶点数，补上或改正 override_vertex_count；
              旧写法（92 / 96 / 76）的 override_byte_stride 一律改回 40
        只动 ini，不动 buf

    四、网格拆分修复（选 3 号模式）
        症状：模型/头发/腿整块不动，或者归位了但形状对不上
        做法：按参照 dump 的各分量把老的一条网格按位置切开，每件绑自己的 hash

    五、掐掉多余的那几笔（跟索引与顶点修复一起跑）
        症状：同一块地方画两遍（耳坠、发夹这种小件最容易看出来）、某处糊成一团
        做法：mod 的 ini 里没认、却被 mod 的网格盖住了的分量 -> 出一节 handling = skip；
              mod 认了、但 dump 里它还有第 2 段起没人 match 的索引段 -> 也出一节 skip
        只动 ini（备份 .texfmt.bak）

    五类互相独立，哪个命中修哪个；都没命中就什么都不做。

三套模式（启动时选；拖放界面输 m 可以换）
    1 = 索引与顶点修复（默认）
        就是上面说的这两样：VGX 按角色表，texcoord 按 TEXCOORD_TARGETS
        或 dump 参照。要选一组参照。

    2 = 通用脸部修复
    3 = 网格拆分修复
        3.1 -> 3.2 更新里 texcoord 变过的那批网格，只有一种变化，写死在
        代码里，不用填格式，也不需要参照：
            texcoord 里最前面那块顶点 COLOR 4 字节（R8G8B8A8_UNORM）
            -> 4 个 float，每顶点多 12 字节（旧 36 -> 新 48 字节/顶点）
        只认 UNIVERSAL_HASHES 那张名单（53 个网格 / 46 个角色，输 3 看名单）。
        这个模式只动 texcoord buf 和 ini 里的 stride，骨骼索引（VGX）不碰。

        老 mod 的 texcoord 比游戏少几块时（2024 年那批只有 2 条 UV，现在 4 条），
        buf 大小对不上 36 —— 只要 dump\ 里正好有这个网格，就按 dump 的元素表
        + buf 实际字节推出每块落在哪，缺的块补 0（推不出就说跳过，不乱修；
        跳过时会把卡在哪说清：dump 缺 -*Texcoord.buf / 值域对不上 / 形状不对）。
        推出来时，如果 dump 里这个网格绑了不止一张贴图，会多提醒一句 ——
        那种网格补 0 会让那层贴图失效。

用法
    双击 本脚本：
        第一步  选这次用哪组参照（dump\ 里有几个文件夹就列几组）
        第二步  把【那个 mod 的文件夹】拖进窗口，按 Enter，
                再选 1 = 修复 / 2 = 还原 / 回车 = 跳过 / q = 退出

    修复时会先把三类问题都列出来，输入 queren 确认后一起写；
    写前都会自动备份。

    命令行：python 索引与顶点修复工具.py [universal] [restore] <mod文件夹>

    拖放界面输 c 可以换参照组（重选参照），输 m 换模式，输 3 看通用脸部修复的名单。

注意
    - 一次只拖一个 mod 的文件夹（它自己的 ini 和 Buffer），
      不要把整个 Mods 目录拖进来 —— 会扫到别的 mod
    - 不要在同一个 mod 上跑两次（有备份/标记的会自动跳过）
    - 拖进来的 mod 必须属于本次选的那组参照：ini 里一个参照 hash 都没命中，
      整包都不处理 —— 选了哪组就只能修哪组，免得跨组修错
      （没读 dump、只用表的时候不做这个限制）

加新角色 / 新网格看下面两张表
    VGX_CHARACTERS     —— VGX 骨骼索引重映射，用 查找VGX映射工具 生成
    TEXCOORD_TARGETS   —— texcoord 顶点格式重排，用 查找Texcoord映射工具 生成

texcoord 顶点格式和 VGX 骨骼索引都可以不填表：把游戏内抓的 dump 放进本程序目录下的
dump\ 文件夹，启动时自动读；也可以运行时把 dump 文件夹拖进窗口。
    贴图格式：json 里的 hash / 当前格式，旧格式按 buf 实际大小倒推；
             元素个数变过的那种（老 mod 少几块）按 dump 的 texcoord buf 逐块对值域推
    VGX    ：同一个网格文件夹里再放 -*Blend.buf 和 -*Position.buf，
             工具按位置配对逐顶点投票，自己推出索引映射
两张表（TEXCOORD_TARGETS / VGX_CHARACTERS）里已有的都能用，
跟 dump 撞上时会问一次用哪个。
"""

import os
import re
from array import array
from collections import deque
from math import floor
import sys
import json
import shlex
import struct
import traceback
from pathlib import Path

# 打包成 exe 时 __file__ 指向临时解压目录（_MEIPASS），dump\ 会建到那儿、退出就没，
# 所以 frozen 时用 exe 所在目录
SCRIPT_DIR = (Path(sys.executable).resolve().parent
              if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent)

# dump\ 从哪找：程序目录优先，再把上一级也带上 ——
# 脚本放在 py代码\ 这类子目录里时，dump\ 通常和 exe 一起放在外面。
APP_DIRS = [SCRIPT_DIR]
if SCRIPT_DIR.parent not in APP_DIRS:
    APP_DIRS.append(SCRIPT_DIR.parent)

CONFIRM_WORD = 'queren'
EXIT_WORDS = ('exit', 'quit', 'q', '退出')

if sys.platform == 'win32':
    os.system('')   # 打开终端 ANSI 支持


# ------------------------------------------------------------------ 终端样式

class Style:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    GREEN = '\033[1;32m'
    RED = '\033[1;31m'
    YELLOW = '\033[1;33m'
    CYAN = '\033[1;36m'
    GRAY = '\033[90m'


def c(text, color):
    return '{}{}{}'.format(color, text, Style.RESET)


# ------------------------------------------------------------------ 提问接口
# 修复前要问用户几件事（表与 dump 撞车用哪套、写不写、还原确认）。
# 独立脚本一律走下面这套命令行问答；把 IV_ASKER 换成别的提问器，
# 同一处问话就能改成别的问法 —— 两边决定的东西完全一样。

IV_ASKER = None      # 换了就是别的提问器；None = 命令行问答


class IvConsoleAsker:
    """命令行提问：独立脚本默认用这套"""

    def source_choice(self, kind, detail, count, prefer_dump):
        """表 / dump 撞车：返回 'table' 或 'dump'"""
        if kind == 'vgx':
            print('表里和 dump 里都能修{}这个网格：{}'.format(
                '' if count == 1 else ' {} 个'.format(count), detail))
            print('  用哪个的数据修？')
            print('    {}1 = 用表里的（推荐，人手填过）{}'.format(Style.GREEN, Style.RESET))
            print('    {}2 = 用 dump 自动推的{}'.format(Style.GREEN, Style.RESET))
            return 'dump' if ask('  选 1 / 2（直接回车 = 表）: ').strip() == '2' else 'table'
        print('表里和 dump 里都有{}这个网格：{}'.format(
            '' if count == 1 else ' {} 个'.format(count), detail))
        print('  这次用哪个的数据修？')
        print('    {}1 = 用表里的{}'.format(Style.GREEN, Style.RESET))
        print('    {}2 = 用 dump 里的{}'.format(Style.GREEN, Style.RESET))
        answer = ask('  选 1 / 2（直接回车 = {}）: '.format('dump' if prefer_dump else '表')).strip()
        if answer == '1':
            return 'table'
        if answer == '2':
            return 'dump'
        return 'dump' if prefer_dump else 'table'

    def auto_vgx_choice(self, paths):
        """表里没有、dump 能推：返回 True = 用 dump 推的修"""
        print('表里没有这些网格的条目，但 dump 能自动推：')
        for path in paths:
            print('  - {}'.format(path))
        print('  要不要用 dump 推出来的映射来修？')
        print('    {}1 = 要{}'.format(Style.GREEN, Style.RESET))
        print('    {}2 = 不要，这次不动它{}'.format(Style.GREEN, Style.RESET))
        return ask('  选 1 / 2（直接回车 = 要）: ').strip() != '2'

    def confirm(self, summary):
        """写文件前的总确认：返回 True = 动手"""
        print(c('不要对不需要修复的 mod 运行本工具!!!', Style.RED))
        print(c('不要在同一个 buf 上运行两次!!!', Style.RED))
        print('输入 {}{}{} 回车应用（改前都会备份，想反悔可以选 2 还原）'.format(
            Style.GREEN, CONFIRM_WORD, Style.RESET))
        return ask().lower() == CONFIRM_WORD

    def confirm_restore(self, lines):
        """还原确认：返回 True = 动手（明细行由调用方打印）"""
        print('输入 {}{}{} 回车执行还原。'.format(Style.GREEN, CONFIRM_WORD, Style.RESET))
        return ask().lower() == CONFIRM_WORD

    def progress(self, done, total, text):
        """命令行不画进度条，什么都不做"""
        pass


def iv_asker():
    """当前提问器：换了 IV_ASKER 就用换的那个，否则命令行那套"""
    return IV_ASKER if IV_ASKER is not None else _IV_CONSOLE_ASKER


_IV_CONSOLE_ASKER = IvConsoleAsker()


def iv_progress(done, total, text):
    """写文件进度（换个提问器就能刷进度条；命令行忽略）"""
    if IV_ASKER is not None:
        try:
            IV_ASKER.progress(done, total, text)
        except Exception:
            pass


def active_ref_hashes():
    """本次这组参照的 dump 里出现过的全部 hash：texcoord + blend + position。

    表（VGX_CHARACTERS / TEXCOORD_TARGETS）里的条目也要过这一关：
    条目上的 hash 不在里面 = 这个网格不属于本次选的这组，一律不修 ——
    免得选了 A 组的参照，拖进来 B 组的 mod，靠表跨组给修了。

    返回 None = 没有 dump 参照（DUMP_MESHES 空），此时不做限制，
    只有表的模式照旧能用。
    """
    if not DUMP_MESHES:
        return None
    allowed = set()
    for tex_hash, info in DUMP_MESHES.items():
        allowed.add(str(tex_hash).lower())
        for key in ('blend_hash', 'position_hash'):
            value = info.get(key)
            if value:
                allowed.add(str(value).lower())
    return allowed


def active_component_hashes():
    """本次参照里所有分量的 hash：texcoord + blend + position + draw + ib。

    和 active_ref_hashes() 的区别：那个只拿三个顶点 hash 判断 mod 属于哪组；
    这个给「顶点上限」这类按 hash 认分量的步骤用，draw/ib 也要算进来。
    返回 None = 没有 dump 参照，调用方保持原来的全局行为。
    """
    if not DUMP_MESHES:
        return None
    allowed = set()
    for tex_hash, info in DUMP_MESHES.items():
        allowed.add(str(tex_hash).lower())
        for key in ('position_hash', 'texcoord_hash', 'blend_hash', 'draw_hash', 'ib_hash'):
            value = info.get(key)
            if value:
                allowed.add(str(value).lower())
    return allowed


def ref_scope_text():
    """给提示文字用：本次参照是谁"""
    return describe_active_dumps()


def mod_ref_hit(target: Path, allowed):
    """这个 mod 是不是本次这组参照的：拿 ini 里的 hash 跟白名单对。

    每组的 hash 都不一样，所以【命中任意一个就够了】——
    命中一个 = 这个 mod 和参照 dump 是同一组。
    返回 (是否命中, 命中的那个 hash)。
    """
    if allowed is None:
        return True, None
    for ini_path in find_ini_files(target):
        try:
            text = ini_path.read_text(encoding='utf-8', errors='replace')
        except Exception:
            continue
        for match in HASH_LINE_RE.finditer(text):
            value = str(match.group(1)).lower()
            if value in allowed:
                return True, value
    return False, None


# ==========================================================================
#  表一：VGX 骨骼索引重映射
#
#  和琉音 2.5 / 艾莲 1.4A 一个思路：把一个写错的骨骼索引换成正确的。
#  hashes 填该角色【Position 节点】的 hash（ini 里带 vb2 = ResourcexxxBlend 的那节），
#  old / new 用 查找VGX映射工具 推出来。
#
#    {
#        'name':   '琉音 Dialyn 身体',
#        'hashes': ['ff36809b'],
#        'old':    [...],
#        'new':    [...],
#    },
# ==========================================================================

VGX_CHARACTERS = [
    {
        'name':   '琉音 Dialyn 身体',
        'hashes': ['ff36809b'],
        'old':    [18, 19, 20, 54, 55, 56, 57, 58, 59, 60, 61, 62, 69, 70, 71, 72,
                   91, 92, 93, 94, 95, 96, 97, 98, 113, 114, 128, 129, 130, 131, 132, 188, 189],
        'new':    [20, 18, 19, 62, 54, 55, 56, 57, 58, 59, 60, 61, 71, 72, 70, 69,
                   98, 91, 92, 93, 94, 95, 96, 97, 114, 113, 129, 128, 132, 130, 131, 189, 188],
    },
    {
        'name':   '艾莲 Ellen 腿部',
        'hashes': ['ba0fe600'],
        'old':    [34, 35, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 49, 50],
        'new':    [39, 34, 40, 35, 38, 42, 43, 44, 45, 46, 47, 41, 50, 49],
    },
    {
        'name':   '铃 腿（老头发槽）2.1->3.0',
        'hashes': ['ca81bde5'],
        'old':    [0, 1, 3, 7, 9, 10, 11, 12, 13, 14, 64, 65],
        'new':    [1, 3, 0, 9, 7, 11, 13, 14, 12, 10, 0, 0],
    },
    {
        'name':   '铃 头发 2.1->3.0',
        'hashes': ['71d2bf80'],
        'old':    [30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 66, 64, 65],
        'new':    [0, 33, 8, 9, 7, 10, 12, 13, 14, 15, 16, 17, 18, 11, 19, 20, 4, 22, 23, 24, 25, 21, 26, 27, 28, 2, 6, 3, 5, 29, 30, 31, 32, 34, 1, 0, 0],
    },
    {
        'name':   '铃 身体 2.1->3.0',
        'hashes': ['5838ad30'],
        'old':    [0, 1, 2, 3, 4, 12, 13, 14, 15, 16, 17, 18, 20, 21, 22, 23, 24, 25, 37, 39, 40, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 110, 111, 112, 113, 114, 115, 116, 117, 118, 128, 129],
        'new':    [1, 2, 0, 4, 3, 13, 14, 15, 16, 17, 18, 12, 22, 20, 23, 24, 25, 21, 39, 40, 37, 45, 46, 47, 48, 49, 50, 51, 52, 53, 44, 58, 60, 61, 59, 62, 63, 64, 65, 66, 57, 111, 112, 113, 114, 115, 116, 117, 118, 110, 129, 128],
    },
    # 铃-泳装（原 BelleSummer 皮肤）2.8 -> 3.0：表从已验证产物的
    # bellesummermix 和原 mod 的 blend 逐行回推（权重完全一致、只有索引变），
    # 无弱票。头发那张和我们按位置配对独立推的逐条一致。
    {
        'name':   '铃-泳装 头发 2.8->3.0',
        'hashes': ['d440bcc9', '4bb8fccc', 'b536d9e6', '898f40fc', 'a7683988'],
        'old':    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24],
        'new':    [0, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 24, 23, 25, 26],
    },
    {
        'name':   '铃-泳装 身体 2.8->3.0',
        'hashes': ['b95ddd01', 'b36f6834', '91cdde70', '051d5424', '619c5c94'],
        'old':    [0, 1, 2, 3, 6, 7, 8, 10, 12, 13, 14, 16, 17, 18, 19, 20, 21, 23, 24, 25, 26, 27, 28, 31, 33, 34, 36, 37, 38, 39, 40, 41, 42, 43, 45, 46, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 62, 64, 66, 69, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 105, 106, 111, 112, 113, 114, 121, 122, 123],
        'new':    [2, 0, 1, 3, 6, 7, 8, 10, 12, 11, 9, 15, 16, 18, 19, 21, 22, 25, 20, 26, 24, 27, 28, 31, 33, 34, 37, 36, 38, 39, 40, 41, 42, 43, 45, 46, 49, 48, 50, 51, 52, 53, 54, 55, 56, 57, 58, 62, 64, 66, 69, 71, 72, 73, 74, 75, 76, 78, 80, 82, 84, 86, 81, 85, 87, 83, 77, 88, 79, 89, 90, 91, 92, 94, 95, 99, 102, 93, 101, 103, 98, 97, 100, 96, 105, 106, 111, 112, 73, 73, 73, 73, 73],
    },
    {
        'name':   '铃-泳装 上衣(Shirt) 2.8->3.0',
        'hashes': ['324d9d21', '0a00d846', '325b4a1c', 'a1de68c0', '69148073'],
        'old':    [0, 1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28],
        'new':    [0, 1, 2, 5, 4, 9, 3, 8, 10, 11, 12, 13, 14, 16, 6, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28],
        # 整件替换：mod 上衣 6633 顶点 vs 游戏 Shirt 1296，一致率没有可比性。
        # 套表后一致率反而下降，但表本身是对的（已验证产物就是这么套的）。
        'ignore_dump_judge': True,
    },

]

VGX_BACKUP_SUFFIX = '.vgx_BACKUP.buf'
VGX_MARKER_SUFFIX = '.vgx_REMAP_APPLIED.empty'

# ==========================================================================
#  表二：texcoord 顶点格式重排
#
#  游戏更新把某些网格的顶点 COLOR 从 4 字节改成 float4，vb1 每顶点多了 12 字节。
#  hash 用【当前版本】的值（dump 的 CategoryHash.Texcoord），
#  old_format / new_format 用 查找Texcoord映射工具 生成。
#
#    {
#        'name':       '琉音 Dialyn 脸部',
#        'hash':       'dafc9647',
#        'old_format': ('4B', '2f', '2f', '2f', '2f'),   # 36 字节
#        'new_format': ('4f', '2f', '2f', '2f', '2f'),   # 48 字节
#        'blend_hash': '08923d3e',        # 选填，见下
#    },
#
#  记法：'4B'=4 字节  '2e'=2 个 half  '2f'=2 个 float  '4f'=4 个 float
#        '4I'=4 个 uint32  '3f'=3 个 float
#
#  element_map（选填）：只有新旧元素个数不一样时才要填 —— 旧第 i 块落在新布局的第几块，
#      比如旧 3 块（COLOR + 2 条 UV）-> 新 5 块，第二条 UV 落到 TEXCOORD2，就写 [0, 1, 3]；
#      没被写到的那些新块一律补 0（mod 里没有那份数据）。
#      一般不手填：dump\ 里有这个网格时，工具自己按 dump 的 texcoord buf 逐块对值域推，
#      推不出会明说跳过。
#
#  blend_hash（选填）：该网格【blend 节】的 hash —— dump 里的 CategoryHash.Blend。
#      修之前要先确认 buf 到底是不是旧格式，判断顺序：
#        1) 按 buf 大小：只能被旧步幅整除 = 旧格式，只能被新步幅整除 = 已修过
#        2) 大小有歧义时，反推顶点数 —— 先按 blend_hash 找 blend 缓冲（不依赖命名），
#           没填就按同名文件 xxxBlend.buf / xxxPosition.buf 推
#        3) 都判不出来 -> 只提示，不动文件
#      所以这个值只在第 2 步用得上，填了更稳，不填也能跑。
# ==========================================================================

TEXCOORD_TARGETS = [
    {
        'name': '琉音 Dialyn 脸部',
        'hash': 'dafc9647',
        'old_format': ('4B', '2f', '2f', '2f', '2f'),   # 36 字节
        'new_format': ('4f', '2f', '2f', '2f', '2f'),   # 48 字节
        'blend_hash': '08923d3e',                       # 脸部 blend 节
    },
]

TEX_BACKUP_SUFFIX = '.texfmt_BACKUP.buf'
TEX_MARKER_SUFFIX = '.texfmt_DONE.empty'
TEX_INI_BACKUP_SUFFIX = '.texfmt.bak'
TEX_LEGACY_BACKUP_SUFFIX = '.tex48_BACKUP.buf'    # 旧版工具留下的，还原时也认
TEX_LEGACY_INI_BACKUP_SUFFIX = '.tex48.bak'

# ==========================================================================
#  表三：通用脸部修复（3.1 -> 3.2 更新里 texcoord 变过的那批网格）
#
#  只有一种变化，写死在代码里，不用填 old_format / new_format：
#      texcoord buf 最前面那块顶点 COLOR：4 字节（R8G8B8A8_UNORM）-> 4 个 float
#      每顶点多 12 字节        旧 36 字节/顶点 -> 新 48 字节/顶点
#
#  hash 用【变动日志里"更新后"的 texcoord hash】（新 hash）。程序只认这张表，
#  不去读外面的日志文件。
#  加新角色 / 新网格：把日志里那行 "texcoord_vb: 旧 -> 新" 抄进来。
#
#      新 hash: (旧 hash, 是哪个网格)
#
#  和 TEXCOORD_TARGETS 的分工：那张表一条一条写 name / hash / 格式，什么形状
#  都能修；这张只认 36 -> 48 这一种，但一条只用写 hash 和一个名字。
#  「通用脸部修复」模式下只用这张表，不看 dump 参照（有 dump 也只是借它的
#  blend hash 反推顶点数）。
# ==========================================================================

UNIVERSAL_HASHES = {
    '014159dd': ('287c161c', '叶瞬光-皮肤YeShunguangSkin / IB 611df76d 眉毛'),
    '01b43c04': ('ffac76ac', '耀佳音Astra / IB 51831437 脸'),
    '02426764': ('2e04aac2', '仪玄-皮肤YixuanSkin、仪玄Yixuan / IB 8b067f99 脸'),
    '0749a6d7': ('7c9dbd4a', '爱丽丝-皮肤AliceSkin、爱丽丝Alice / IB b078ff22 脸部'),
    '0aacc89a': ('99d2733a', '雨果Hugo / IB 66b936fc 脸'),
    '1132301e': ('d4a12ab7', '扳机Trigger / IB 40cd4182 脸'),
    '20095c2e': ('48152e31', '浅羽悠真Harumasa / IB b0688334 脸'),
    '27fd9193': ('d90368ed', '琉音Dialyn / IB d860525e 眉毛'),
    '2bc69f3c': ('dfc76798', '希希芙Cissia / IB d1a31f0b 脸部'),
    '2bcb59f6': ('a0dfaf80', '席德seed / IB 09d9dca7 脸部'),
    '2fe49591': ('58468aba', '派派Piper / IB e11baad9 脸'),
    '31df6120': ('d5958556', '妮可-皮肤NicoleSkin、妮可Nicole / IB 93b02078 脸'),
    '325bb10f': ('0fd41a37', '狛野真斗Manato / IB f987f156 脸'),
    '37a09c33': ('9d0f7ef5', '浮波柚叶-皮肤YuzuhaSkin、浮波柚叶Yuzuha / IB 507384ea 脸'),
    '3e7815b5': ('f818271a', '安比Anby / IB 19df8e84 脸'),
    '40cdb80f': ('08316415', '伊德海莉Yidhair / IB a2406060 脸'),
    '43cb221f': ('9648c6d3', '卢西娅Lucia / IB 6986f28e 脸'),
    '50c5d703': ('0afe5a44', '薇薇安Vivian、薇薇安-皮肤VivianSkin / IB 39944f20 脸'),
    '558c7001': ('144828a7', '安东Anton / IB a0201907 脸'),
    '57994826': ('f41b27e6', '珂蕾妲Koleda / IB 0e74656e 脸'),
    '60732ab5': ('7a476f86', '星见雅-皮肤MiyabiSkin / IB dbd59d30 脸部'),
    '615a1f62': ('48191f72', '奥菲丝Orphie / IB ed85f33b 脸部'),
    '61782f72': ('14b70725', '柏妮思Burnice / IB b3f6fcb3 脸'),
    '63481380': ('c3b7516b', '格莉丝Grace / IB 4d60568b 脸'),
    '644e5029': ('d3d65ca5', '普罗米娅Promeia / IB e032287a 眉毛'),
    '68efc509': ('69c75b70', '月城柳Yanagi / IB 0817204c Face脸'),
    '6ca475b9': ('dcd61276', '普罗米娅Promeia / IB ef3c4506 脸部'),
    '75302f6a': ('2a29bb4e', '波可娜Pulchra / IB 62de5837 脸'),
    '768c9ec4': ('8267358b', '橘福福jufufu / IB 321768df 脸'),
    '8bbcb25d': ('aa036e70', '猫又Nekomata / IB 37119851 脸'),
    '9e121fda': ('05342ce9', '卢西娅Lucia / IB 84eaa4c6 眉毛'),
    'a79912e2': ('1866cf6a', '丽娜Rina / IB 9f90cfaa 脸'),
    'ac48fc8a': ('158fa3f3', '艾莲Ellen / IB f6ef8f3a Face脸'),
    'aeeeaa7f': ('b7d38cbb', '爱芮-皮肤ArieSkin、爱芮Arie / IB c0b0db5f 眉毛'),
    'b3136c51': ('aa2f560e', '伊芙琳Evelyn / IB ddf4efa6 脸'),
    'b3f1b714': ('c2db08f0', '苍角Soukaku / IB 020f9ac6 脸'),
    'b50b51c0': ('3adaebb3', '莱卡恩Lycaon / IB 6ffdfccb Face脸'),
    'b8af50ce': ('45910aef', '南宫羽-皮肤NanGongYuSkin、南宫羽NanGongYu / IB d643e19a 脸部'),
    'baf394c7': ('cf1a7297', '伊德海莉Yidhair / IB 02072970 眉毛'),
    'be99c90e': ('fc66ecd0', '零号安比Soldier0 / IB e30ca87f 脸'),
    'bf705014': ('a1353cc8', '叶瞬光-皮肤YeShunguangSkin、叶瞬光YeShunguang、叶瞬光白毛YeShunguangWrite / IB c28e6303 脸部'),
    'c1bd84e7': ('b1412ed9', '诺姆Norma / IB 4fafb136 脸部'),
    'c4618d41': ('76c4a041', '照Zhao / IB 43c3c5a0 Face脸'),
    'c493b91c': ('39d7123a', '爱芮-皮肤ArieSkin、爱芮Arie / IB 27966f80 脸部'),
    'cc9f6187': ('0c6f696b', '朱鸢ZhuYuan / IB f1c241b7 脸'),
    'd2e41266': ('7acc7619', '诺姆Norma / IB d3b2ed9a 眉毛'),
    'dafc9647': ('f6c5296e', '琉音Dialyn / IB facb2461 脸部'),
    'daff87b1': ('1c0725e4', '可琳Corin / IB a0c80593 Face脸'),
    'e56b3fdf': ('f87ddcae', '艾莲-皮肤EllenSkin / IB f6ef8f3a 脸'),
    'e619a2b8': ('9772ccda', '爱芮智能体-皮肤ArieAgentSkin、爱芮智能体ArieAgent / IB ffa703e8 脸部'),
    'f30b174b': ('39de00d5', '11号Soldier11 / IB bb315c43 Face 脸'),
    'f5ce8320': ('506dc9e1', '千夏-皮肤ChinatsuSkin、千夏Chinatsu / IB 1a2c8573 脸部'),
    'fd41220d': ('e3cc1981', '千夏-皮肤ChinatsuSkin、千夏Chinatsu / IB 30ea5791 眉毛'),
}

UNIVERSAL_OLD_FORMAT = ('4B', '2f', '2f', '2f', '2f')   # 36 字节/顶点
UNIVERSAL_NEW_FORMAT = ('4f', '2f', '2f', '2f', '2f')   # 48 字节/顶点

# 这次用哪套（启动时选，拖放界面输 m 可以换）
FIX_MODE = 'normal'                 # 'normal' = 索引与顶点修复
MODE_NAMES = {'normal': '索引与顶点修复', 'universal': '通用脸部修复',
              'split': '网格拆分修复'}
MODE_KEYS = ('universal', 'univ', 'tongyong', '通用', '-u')   # 命令行指定走通用模式

# ==========================================================================
#  可选：dump 文件夹
#
#  游戏内 F8 抓的 Frame Analysis dump 里有这个网格当前的所有信息：
#      CategoryHash.Texcoord   -> 该填什么 hash
#      CategoryHash.Blend      -> 反推顶点数用
#      元素表                   -> 当前是什么格式
#  所以 dump 不用手填表，放进来就行。
#
#  全部放进本程序目录下的 dump 文件夹，启动时自动读，拖 mod 进来就直接修：
#
#      索引与顶点修复工具\
#          dump\
#              琉音-脸\                    <- 一个参照一个子文件夹
#                  琉音-脸.json            （游戏内 F8 抓的）
#              艾莲-腿\
#                  d44a8015-24321-0.json
#
#  分组按【文件夹名】走，不按角色合并：一个文件夹 = 一组参照 = 一次修复的范围。
#  同一角色不同部位/不同 mod 各放一个文件夹（名字写成「角色-部位」），
#  合并了会把已经修过的那组一起带上，同一个网格修第二遍。
#
#  文件夹名（或直接放根目录时的文件名）只用来在输出里显示，叫什么都可以；
#  json 内容不依赖文件名，所以随便改。
#
#  也可以填别的绝对路径，或运行时把 dump 文件夹直接拖进窗口：
#      DUMP_DIRS = [r'D:\dump', r'E:\另一个dump']
#
#  只填 TEXCOORD_TARGETS 里没有的网格才会用 dump 里的；重名以表为准。
# ==========================================================================

DUMP_DIR_NAME = 'dump'      # 本程序目录下的 dump 文件夹，自动读
DUMP_DIRS = []              # 另外的 dump 路径（选填）

# 同一个网格，表里和 dump 里都有时，默认用哪个：
#     False = 用表里的（表是人手填的，可控）
#     True  = 用 dump 里的（dump 是游戏当前状态，最新）
# 运行时如果两边都有，工具会问一次用哪个，那次回答优先。
PREFER_DUMP = False

# DXGI 格式 -> 顶点格式记法
DXGI_CHUNK = {
    'R32G32B32A32_FLOAT': '4f', 'R32G32B32_FLOAT': '3f',
    'R32G32_FLOAT': '2f', 'R32_FLOAT': '1f',
    'R16G16B16A16_FLOAT': '4e', 'R16G16_FLOAT': '2e',
    'R32G32B32A32_UINT': '4I', 'R32G32_UINT': '2I', 'R16G16B16A16_UINT': '4H',
    'R8G8B8A8_UNORM': '4B', 'R8G8B8A8_UNORM_SRGB': '4B', 'R8G8B8A8_SNORM': '4B',
    'R10G10B10A2_UNORM': '4B', 'B8G8R8A8_UNORM': '4B',
}

DUMP_MESHES = {}     # 这次实际生效的（可能只是某个角色的）
ALL_DUMPS = {}       # dump\ 里读到的全部


# ==========================================================================
#  通用：ini 收集 / 节切分
# ==========================================================================

SECTION_RE = re.compile(r'(?m)^[ \t]*\[([^\]]+)\][ \t]*$')


def split_sections(text):
    """返回 [(节标题, 节起始, 节结束)]"""
    marks = [(m.start(), m.group(1)) for m in SECTION_RE.finditer(text)]
    result = []
    for i, (start, title) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(text)
        result.append((title, start, end))
    return result


def find_ini_files(folder: Path):
    """递归收集 ini（跳过 DISABLED / DESKTOP 开头的）"""
    hits = []
    for root, _dirs, files in os.walk(folder):
        for name in files:
            if not name.endswith('.ini'):
                continue
            if name.upper().startswith('DISABLED') or name.upper().startswith('DESKTOP'):
                continue
            hits.append(Path(root) / name)
    return sorted(hits)


_UNSUPPORTED_TIME_SWAP = re.compile(
    r'(?im)^\s*\$[A-Za-z_]\w*\s*=.*\btime\b')
UNSUPPORTED_FRAME_SETS = 8        # 同一网格 ≥ 这么多套编号缓冲 = 逐帧动画
ALLOW_UNSUPPORTED_TIME_SWAP = False   # 独立的逐帧脚本 import 后设 True 来放行


def _frame_variant_count(ini_path: Path, text: str) -> int:
    """同一网格最多有几套编号缓冲（.0/.1/... 且 position/blend 都指向不同文件）。

    不依赖变量名：动画 mod 可能把 $swapvar 换成 $frame 之类；结构上一定是
    同一网格几十套 position/blend/texcoord/head.N。普通 mod 最多 2~3 套。
    """
    sets = {}
    for title, start, end in split_sections(text):
        head = title.strip()
        num = re.search(r'\.(\d+)\s*$', head)
        if not num:
            continue
        body = text[start:end]
        fn = re.search(r'(?im)^\s*filename\s*=\s*([^\s;]+)', body)
        if not fn:
            continue
        stride = re.search(r'(?im)^\s*stride\s*=\s*(\d+)', body)
        stride = stride.group(1) if stride else ''
        low = head.lower()
        if 'position' in low and stride == '40':
            kind = 'position'
        elif 'blend' in low and stride == '32':
            kind = 'blend'
        elif 'texcoord' in low and stride:
            kind = 'texcoord'
        elif 'head' in low or low.endswith('ib'):
            kind = 'ib'
        else:
            continue
        path = ini_path.parent / fn.group(1).replace('\\', '/')
        try:
            if not path.exists():
                continue
        except OSError:
            continue
        base = re.sub(r'(position|texcoord|blend|head|ib)?\.\d+$', '', low)
        sets.setdefault(base, {}).setdefault(kind, set()).add(int(num.group(1)))
    best = 0
    for kinds in sets.values():
        if len(kinds) >= 2:
            best = max(best, max(len(nums) for nums in kinds.values()))
    return best


def unsupported_mod_reason(target) -> str:
    """是不是主工具不该碰的 mod（逐帧动态动画），是就返回原因。

    判据（不依赖变量名）：
      1) 任意一行 `$变量 = ... time ...`（动画时钟）
      2) 同一网格有 ≥ UNSUPPORTED_FRAME_SETS 套编号缓冲（逐帧网格）
    这种 mod 骨头/缓冲结构跟普通 mod 完全不同，索引修复/拆分不支持。
    """
    if ALLOW_UNSUPPORTED_TIME_SWAP:
        return ''
    try:
        inis = find_ini_files(Path(target))
    except OSError:
        return ''
    for ini_path in inis:
        try:
            text = ini_path.read_text(encoding='utf-8', errors='replace')
        except OSError:
            continue
        reason = ''
        if _UNSUPPORTED_TIME_SWAP.search(text):
            reason = '按时间逐帧切换'
        else:
            _sets = _frame_variant_count(ini_path, text)
            if _sets >= UNSUPPORTED_FRAME_SETS:
                reason = '同一网格有 {} 套编号缓冲'.format(_sets)
        if reason:
            return ('这是一个逐帧动态动画 mod（{}）：'
                    '索引与顶点修复/拆分不支持，这一步不改任何文件。'.format(reason))
    return ''


def find_backup_like(buf_path: Path):
    """同名文件里有没有备份 / 已修复标记（本工具的、旧工具的都认）"""
    stem = buf_path.name[:-4]
    try:
        names = os.listdir(buf_path.parent)
    except OSError:
        return None
    for name in names:
        if name == buf_path.name or not name.startswith(stem):
            continue
        upper = name.upper()
        if 'BACKUP' in upper or 'REMAP_APPLIED' in upper or '_DONE' in upper:
            return name
    return None


# ==========================================================================
#  一、VGX 骨骼索引
# ==========================================================================

def vgx_hash_pattern(hash) -> re.Pattern:
    return re.compile(r'^([ \t]*?\[(?:Texture|Shader)Override.*\][ \t]*(?:\n(?![ \t]*?\[).*?$)*?(?:\n\s*hash\s*=\s*{}[ \t]*)(?:(?:\n(?![ \t]*?\[).*?$)*(?:\n[\t ]*?[\$\w].*?$))?)\s*'.format(hash), flags=re.VERBOSE | re.IGNORECASE | re.MULTILINE)


def vgx_section_pattern(title) -> re.Pattern:
    return re.compile(r'^([ \t]*?\[{}\](?:(?:\n(?![ \t]*?\[).*?$)*(?:\n[\t ]*?[\$\w].*?$))?)\s*'.format(title), flags=re.VERBOSE | re.IGNORECASE | re.MULTILINE)


def vgx_blend_resources(ini_content: str, section_text: str) -> list:
    """从节内容里收集 vb2 = xxx，遇到 run = CommandList 追进去"""
    line_pattern = re.compile(r'^\s*(run|vb2)\s*=\s*(.*)\s*$', flags=re.IGNORECASE)
    resources = []

    for line in section_text.splitlines():
        line_match = line_pattern.match(line)
        if not line_match:
            continue

        if line_match.group(1) == 'vb2':
            resources.append(line_match.group(2))
        elif line_match.group(1) == 'run':
            commandlist_match = vgx_section_pattern(line_match.group(2)).search(ini_content)
            if commandlist_match:
                resources.extend(vgx_blend_resources(ini_content, commandlist_match.group(1)))

    return resources


def vgx_blend_filepaths(ini_filepath: Path, ini_content: str, position_hash: str) -> list:
    position_match = vgx_hash_pattern(position_hash).search(ini_content)
    if not position_match:
        return []

    line_pattern = re.compile(r'^\s*filename\s*=\s*(.*)\s*$', flags=re.IGNORECASE)
    paths = []
    for resource in vgx_blend_resources(ini_content, position_match.group(1)):
        resource_match = vgx_section_pattern(resource).search(ini_content)
        if not resource_match:
            continue
        stride_match = re.search(r'(?im)^\s*stride\s*=\s*(\d+)',
                                 resource_match.group(1))
        if stride_match and int(stride_match.group(1)) != 32:
            continue
        for line in resource_match.group(1).splitlines():
            if line_match := line_pattern.match(line):
                paths.append(ini_filepath.parent / line_match.group(1).strip())
                break
    return paths


def vgx_remap(buffer: bytes, table: dict) -> bytes:
    """按映射表重写 blend.buf 的骨骼索引，权重不动"""
    stride = 32
    if len(buffer) % stride:
        raise ValueError('blend 缓冲区 {} 字节不是 32 的整数倍'.format(len(buffer)))
    out = bytearray()
    for i in range(len(buffer) // stride):
        weights = struct.unpack_from('<4f', buffer, i * stride + 0)
        indices = struct.unpack_from('<4I', buffer, i * stride + 16)
        out.extend(struct.pack('<4f4I', *weights, *[table.get(v, v) for v in indices]))
    return bytes(out)


def vgx_backup_of(buf: Path) -> Path:
    return buf.with_name(buf.stem + VGX_BACKUP_SUFFIX)


def vgx_marker_of(buf: Path) -> Path:
    return buf.with_name(buf.stem + VGX_MARKER_SUFFIX)


def validate_vgx() -> bool:
    ok = True
    seen = {}
    for character in VGX_CHARACTERS:
        name = character.get('name', '(没写 name)')
        old = character.get('old', [])
        new = character.get('new', [])
        hashes = character.get('hashes', [])

        if not hashes:
            print(c('[配置错误] {}: 没有填 hashes'.format(name), Style.RED))
            ok = False
        for position_hash in hashes:
            if not re.fullmatch(r'[0-9a-fA-F]{8}', str(position_hash)):
                print(c('[配置错误] {}: hash "{}" 不是 8 位十六进制'.format(name, position_hash), Style.RED))
                ok = False
            key = str(position_hash).lower()
            if key in seen:
                print(c('[配置警告] hash {} 被 "{}" 和 "{}" 同时使用'.format(key, seen[key], name), Style.YELLOW))
            seen[key] = name

        if len(old) != len(new):
            print(c('[配置错误] {}: old 有 {} 个，new 有 {} 个，必须一样长'.format(name, len(old), len(new)), Style.RED))
            ok = False
            continue
        if not old:
            print(c('[配置错误] {}: old/new 是空的'.format(name), Style.RED))
            ok = False
            continue
        duplicates = sorted({x for x in old if old.count(x) > 1})
        if duplicates:
            print(c('[配置错误] {}: old 里有重复值 {}'.format(name, duplicates), Style.RED))
            ok = False
    return ok


# ---- dump 驱动：按位置配对推映射（验证工具里那套，参数一样）-----------------

VGX_RADIUS = 0.010        # 位置配对半径（游戏单位）
VGX_MAX_K = 6             # 每个 dump 顶点最多取几个 mod 顶点
VGX_W_EPS = 0.050         # 权重被认为"一样"的容差
VGX_W_MIN = 0.010         # 小于这个权重的槽位不参与投票
VGX_LOW_VOTES = 20        # 少于这么多票的条目会被标出来


def load_blend_verts(path: Path):
    """blend.buf -> [(权重4, 索引4)]"""
    try:
        data = path.read_bytes()
    except Exception:
        return None
    if len(data) % 32:
        return None
    return [(struct.unpack_from('<4f', data, i * 32),
             struct.unpack_from('<4I', data, i * 32 + 16))
            for i in range(len(data) // 32)]


def load_positions(path: Path):
    """Position.buf -> [(x, y, z)]（只取每顶点开头 12 字节）"""
    try:
        data = path.read_bytes()
    except Exception:
        return None
    count = len(data) // 40
    flat = array('f')
    flat.frombytes(data[:count * 40])
    return list(zip(flat[0::10], flat[1::10], flat[2::10]))


# 邻格偏移：单元边长 == 半径，所以查 ±1 个格子就够
VGX_CELL_OFFSETS = tuple((dx, dy, dz)
                         for dx in (-1, 0, 1) for dy in (-1, 0, 1) for dz in (-1, 0, 1))


def derive_bone_map(mod_blend, mod_pos, dump_blend, dump_pos):
    """逐顶点按位置配对投票 -> {旧索引: {新索引: 票数}}, 统计

    格子用 floor 取整 —— 不能用 int()，那在负数上是截断，跨 0 那个格子会被撑成
    两倍宽，边界外一个半径内的顶点就会漏掉。
    """
    inv = 1.0 / VGX_RADIUS
    limit = VGX_RADIUS * VGX_RADIUS
    w_min = VGX_W_MIN
    w_eps = VGX_W_EPS
    max_k = VGX_MAX_K
    offsets = VGX_CELL_OFFSETS

    xs = [p[0] for p in mod_pos]
    ys = [p[1] for p in mod_pos]
    zs = [p[2] for p in mod_pos]

    # 每个顶点的权重排序只跟 blend 行有关，先算一遍；原来在候选配对内层
    # 每个 dump 顶点 × 最多 6 个候选都要重新 sorted(range(4))。
    mod_order = [sorted(range(4), key=lambda k: -row[0][k])
                 for row in mod_blend]
    dump_order = [sorted(range(4), key=lambda k: -row[0][k])
                  for row in dump_blend]

    grid = {}
    for i in range(len(xs)):
        key = (floor(xs[i] * inv), floor(ys[i] * inv), floor(zs[i] * inv))
        cell = grid.get(key)
        if cell is None:
            grid[key] = [i]
        else:
            cell.append(i)
    get_cell = grid.get

    votes = {}
    matched = 0
    distances = []

    for d, (px, py, pz) in enumerate(dump_pos):
        bx = floor(px * inv)
        by = floor(py * inv)
        bz = floor(pz * inv)
        found = []
        for dx, dy, dz in offsets:
            cell = get_cell((bx + dx, by + dy, bz + dz))
            if not cell:
                continue
            for i in cell:
                ax = xs[i] - px
                ay = ys[i] - py
                az = zs[i] - pz
                d2 = ax * ax + ay * ay + az * az
                if d2 <= limit:
                    found.append((d2, i))
        if not found:
            continue
        found.sort()
        if len(found) > max_k:
            found = found[:max_k]
        matched += 1
        distances.append(found[0][0] ** 0.5)

        dump_w, dump_i = dump_blend[d]
        order_d = dump_order[d]
        for _d2, i in found:
            mod_w, mod_i = mod_blend[i]
            order_m = mod_order[i]
            for a, b in zip(order_m, order_d):
                if mod_w[a] < w_min:
                    break
                if abs(mod_w[a] - dump_w[b]) <= w_eps:
                    counter = votes.get(mod_i[a])
                    if counter is None:
                        votes[mod_i[a]] = {dump_i[b]: 1}
                    else:
                        counter[dump_i[b]] = counter.get(dump_i[b], 0) + 1

    distances.sort()
    stats = {'matched': matched, 'total': len(dump_pos),
             'median': distances[len(distances) // 2] if distances else 0.0}
    return votes, stats


def resolve_bone_map(votes):
    """按票数贪心，保证一一对应 -> {旧: {'new': 新, 'votes': 票数}}"""
    flat = [((old, new), count)
            for old, counter in votes.items()
            for new, count in counter.items()]
    flat.sort(key=lambda item: -item[1])

    mapping = {}
    used_new = set()
    for (old, new), count in flat:
        if old in mapping or new in used_new:
            continue
        mapping[old] = {'new': new, 'votes': count}
        used_new.add(new)
    return mapping


def section_by_hash(text, hash_value):
    """节里 hash = xxx 的那个节的内容"""
    if not hash_value:
        return None
    for title, start, end in split_sections(text):
        body = text[start:end]
        m = HASH_LINE_RE.search(body)
        if m and m.group(1).lower() == str(hash_value).lower():
            return body
    return None


def buf_by_slot(ini_path: Path, text: str, hash_value, slots, expect_stride=None):
    """按 hash 找节，再顺着 vb0 / vb2 找缓冲文件"""
    body = section_by_hash(text, hash_value)
    if body is None:
        return None
    for slot in slots:
        for resource in follow_slot_resources(text, body, slot):
            definition = find_resource_definition(text, resource)
            if not definition:
                continue
            stride = definition.get('stride')
            if expect_stride and stride not in (None, expect_stride):
                continue
            path = ini_path.parent / definition['filename']
            if path.exists():
                return path
    return None


def vgx_auto_candidate(ini_path: Path, text: str, info: dict):
    """一个 dump 网格能不能对上一个 mod 缓冲（按 hash 定位）"""
    ref_blend = info.get('blend_buf')
    ref_pos = info.get('position_buf')
    if not ref_blend or not ref_pos:
        return None
    if not Path(ref_blend).exists() or not Path(ref_pos).exists():
        return None

    # blend 节：用 dump 的 blend hash 找；找不到再用 position hash
    # （有些作者把 vb2 写进 position 那一节里）
    blend_path = None
    for hash_value in (info.get('blend_hash'), info.get('position_hash')):
        blend_path = buf_by_slot(ini_path, text, hash_value, ('vb2',), expect_stride=32)
        if blend_path:
            break
    if not blend_path:
        return None
    try:
        if blend_path.stat().st_size % 32:
            return None
    except OSError:
        return None

    # position：同名前缀的先试，再看 ini 里 vb0 指到哪
    stem = blend_path.name[:-4].replace('Blend', 'Position').replace('blend', 'position')
    pos_path = blend_path.with_name(stem + '.buf')
    if not pos_path.exists() or pos_path.stat().st_size % 40:
        pos_path = None
        for hash_value in (info.get('position_hash'), info.get('blend_hash')):
            pos_path = buf_by_slot(ini_path, text, hash_value, ('vb0',), expect_stride=40)
            if pos_path:
                break
    if not pos_path:
        return None
    try:
        if pos_path.stat().st_size % 40:
            return None
    except OSError:
        return None

    return blend_path, pos_path


VGX_ALREADY_AGREE = 0.90   # （保留）与 dump 同位置主骨一致率参考线
VGX_TABLE_MARGIN = 0.02    # 套表后一致率至少要提高这么多，否则判定"已修/无需修"
VGX_MIN_PAIRS = 64         # 至少配上这么多顶点才敢下"已修"的结论
VGX_CHECK_SAMPLES = 4096   # 复核时最多抽这么多个 dump 顶点
VGX_CHECK_QUICK = 512      # 先抽 512 个粗判；差异不明显再补到 4096
VGX_CHECK_SURE = 0.05      # 快判差异超过这个就定案


def vgx_sibling_position(blend_path: Path):
    """同名的 Position 文件（Blend -> Position）"""
    name = blend_path.name
    for old, new in (('Blend', 'Position'), ('blend', 'position')):
        if old in name:
            candidate = blend_path.with_name(name.replace(old, new))
            if candidate.exists():
                return candidate
    return None


def vgx_position_grid(mod_pos):
    """mod 顶点位置格子（VGX_RADIUS 边长），配对和复核共用"""
    inv = 1.0 / VGX_RADIUS
    grid = {}
    for i, p in enumerate(mod_pos):
        key = (floor(p[0] * inv), floor(p[1] * inv), floor(p[2] * inv))
        grid.setdefault(key, []).append(i)
    return grid


def vgx_pair_dump_to_mod(mod_pos, dump_pos, samples=None, grid=None):
    """dump 每个（抽样后的）顶点在 mod 里最近的顶点 -> [(dump 下标, mod 下标)]

    抽样：dump 顶点多的时候按固定步长取，最多 VGX_CHECK_SAMPLES 个 ——
    "已修/没修"的判定几千个点足够，不用每个点都扫 27 个格子。
    套表前后复用同一份配对，只重算骨号，不重复找最近点。
    grid 可以不传；vgx_rows_improvement 会把粗判/复核共用的格子传进来。
    """
    if not mod_pos or not dump_pos:
        return []
    inv = 1.0 / VGX_RADIUS
    limit = VGX_RADIUS * VGX_RADIUS
    if grid is None:
        grid = vgx_position_grid(mod_pos)
    cap = int(samples or VGX_CHECK_SAMPLES)
    step = max(1, len(dump_pos) // cap) if len(dump_pos) > cap else 1
    pairs = []
    for d in range(0, len(dump_pos), step):
        px, py, pz = dump_pos[d]
        bx, by, bz = floor(px * inv), floor(py * inv), floor(pz * inv)
        best = None
        for dx, dy, dz in VGX_CELL_OFFSETS:
            for i in grid.get((bx + dx, by + dy, bz + dz), ()):
                q = mod_pos[i]
                ax = q[0] - px
                ay = q[1] - py
                az = q[2] - pz
                d2 = ax * ax + ay * ay + az * az
                if d2 <= limit and (best is None or d2 < best[0]):
                    best = (d2, i)
        if best is not None:
            pairs.append((d, best[1]))
    return pairs


def vgx_agreement_from_pairs(pairs, mod_rows, dump_rows):
    """按给定配对算"主骨"一致率 -> (一致率, 配对数) 或 None"""
    same = paired = 0
    for d, m in pairs:
        dw, di = dump_rows[d]
        slot_d = max(range(4), key=lambda k: dw[k])
        if dw[slot_d] < VGX_W_MIN:
            continue
        mw, mi = mod_rows[m]
        slot_m = max(range(4), key=lambda k: mw[k])
        if mw[slot_m] < VGX_W_MIN:
            continue
        paired += 1
        if int(mi[slot_m]) == int(di[slot_d]):
            same += 1
    if paired < VGX_MIN_PAIRS:
        return None
    return same / paired, paired


def vgx_rows_agreement(mod_rows, mod_pos, dump_rows, dump_pos):
    """mod 的"主骨"和 dump 同位置顶点的主骨一致率 -> (一致率, 配对数) 或 None"""
    if not (mod_rows and mod_pos and dump_rows and dump_pos):
        return None
    pairs = vgx_pair_dump_to_mod(mod_pos, dump_pos)
    return vgx_agreement_from_pairs(pairs, mod_rows, dump_rows)


def vgx_remap_rows(rows, table):
    """内存里按表换一遍骨号（不动文件）"""
    out = []
    for weights, bones in rows:
        out.append((weights, [table.get(int(value), int(value)) for value in bones]))
    return out


def vgx_rows_improvement(mod_rows, mod_pos, dump_rows, dump_pos, table):
    """套表前后主骨一致率 -> (before, after) 或 None

    先抽 512 个点粗判：差异明显就直接定案；差异不明显（可能影响判定）再补到
    4096 个点复核。已修/没修通常差得很开（88%->39% 这种），粗判就够。
    """
    grid = vgx_position_grid(mod_pos)
    pairs = vgx_pair_dump_to_mod(mod_pos, dump_pos, VGX_CHECK_QUICK, grid=grid)
    before = vgx_agreement_from_pairs(pairs, mod_rows, dump_rows)
    after = vgx_agreement_from_pairs(pairs, vgx_remap_rows(mod_rows, table), dump_rows)
    if before is None or after is None:
        return None
    if abs(after[0] - before[0]) <= VGX_CHECK_SURE and len(dump_pos) > VGX_CHECK_QUICK:
        pairs = vgx_pair_dump_to_mod(mod_pos, dump_pos, grid=grid)
        before = vgx_agreement_from_pairs(pairs, mod_rows, dump_rows)
        after = vgx_agreement_from_pairs(pairs, vgx_remap_rows(mod_rows, table), dump_rows)
        if before is None or after is None:
            return None
    return before, after


def vgx_augment_out_of_range(blend_path: Path, info: dict, table: dict):
    """固定表里没有、且超出目标骨盘范围的旧骨号，按 dump 位置配对补映射。

    超范围骨号在游戏里越界（会被 clamp / 丢弃），顶点塌在一起、拉成块
    （铃-动态：身体网格用到 135 / 140 / 142，新身体骨盘最大 129）。
    只补超范围的；表里已有一律不动。返回补了几条。
    """
    pos_path = vgx_sibling_position(blend_path)
    dump_blend_path = info.get('blend_buf')
    dump_pos_path = info.get('position_buf')
    if not (pos_path and dump_blend_path and dump_pos_path):
        return 0
    if not (blend_path.exists() and Path(dump_blend_path).exists()
            and Path(dump_pos_path).exists()):
        return 0
    mod_rows = load_blend_verts(blend_path)
    mod_pos = load_positions(pos_path)
    dump_rows = load_blend_verts(Path(dump_blend_path))
    dump_pos = load_positions(Path(dump_pos_path))
    if not (mod_rows and mod_pos and dump_rows and dump_pos):
        return 0
    palette_max = 0
    for weights, bones in dump_rows:
        for slot in range(4):
            if weights[slot] > 0.01 and int(bones[slot]) > palette_max:
                palette_max = int(bones[slot])
    missing = set()
    for weights, bones in mod_rows:
        for slot in range(4):
            if weights[slot] <= 0.001:
                continue
            old = int(bones[slot])
            if old not in table and old > palette_max:
                missing.add(old)
    if not missing:
        return 0
    votes, _stats = derive_bone_map(mod_rows, mod_pos, dump_rows, dump_pos)
    added = 0
    rest = set()
    for old in missing:
        counter = votes.get(old)
        if not counter:
            rest.add(old)
            continue
        total = sum(counter.values())
        best, count = max(counter.items(), key=lambda kv: kv[1])
        if count * 2 >= total:
            table[old] = best
            added += 1
        else:
            rest.add(old)
    # 权重对不上的（mod 自加的骨，比如 130~140 这种私处/布料骨）：
    # 按位置找最近的 dump 顶点，用它的主骨投票（半径 15cm）
    if rest:
        radius = 0.15
        inv = 1.0 / radius
        grid = {}
        for index, point in enumerate(dump_pos):
            key = (floor(point[0] * inv), floor(point[1] * inv), floor(point[2] * inv))
            grid.setdefault(key, []).append(index)
        votes2 = {}
        for k, (weights, bones) in enumerate(mod_rows):
            if not any(weights[s] > 0.001 and int(bones[s]) in rest
                       for s in range(4)):
                continue          # 这条顶点没有要补的骨号，不用找最近点
            point = mod_pos[k]
            key = (floor(point[0] * inv), floor(point[1] * inv), floor(point[2] * inv))
            best_index = None
            best_d2 = radius * radius
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        for index in grid.get((key[0] + dx, key[1] + dy,
                                               key[2] + dz), ()):
                            q = dump_pos[index]
                            d2 = ((q[0] - point[0]) ** 2 + (q[1] - point[1]) ** 2
                                  + (q[2] - point[2]) ** 2)
                            if d2 <= best_d2:
                                best_index, best_d2 = index, d2
            if best_index is None:
                continue
            dump_w, dump_b = dump_rows[best_index]
            slot_d = max(range(4), key=lambda s: dump_w[s])
            target = int(dump_b[slot_d])
            for slot in range(4):
                if weights[slot] <= 0.001:
                    continue
                old = int(bones[slot])
                if old in rest:
                    counter = votes2.setdefault(old, {})
                    counter[target] = counter.get(target, 0) + 1
        if votes2:
            # 这些是 mod 自加的骨（私处/布料等），3.0 骨盘里没有对应。
            # 分开映射会让整块几何被不同骨拉散 → 全部绑到同一个锚点骨，
            # 整块保持原形、只跟随一根骨。锚点 = 位置投票总票数最多的那个。
            anchor_votes = {}
            for counter in votes2.values():
                for target, count in counter.items():
                    anchor_votes[target] = anchor_votes.get(target, 0) + count
            anchor = max(anchor_votes.items(), key=lambda kv: kv[1])[0]
            for old in missing:
                table[old] = anchor       # 全部统一到锚点，整块不被拉散
                added += 1
    return added


def vgx_table_improvement(blend_path: Path, info: dict, table: dict):
    """套这张表之前 / 之后，与 dump 同位置主骨的一致率 -> (before, after) 或 None

    没标记的 buf 用这个判"是不是已经修过"：已经在新空间的，套表不会让一致率
    变高（甚至变低）；没修的，套表后会明显变高。配对只做一次，两遍都复用它。
    """
    pos_path = vgx_sibling_position(blend_path)
    dump_blend_path = info.get('blend_buf')
    dump_pos_path = info.get('position_buf')
    if not (pos_path and dump_blend_path and dump_pos_path):
        return None
    if not (blend_path.exists() and Path(dump_blend_path).exists()
            and Path(dump_pos_path).exists()):
        return None
    mod_rows = load_blend_verts(blend_path)
    mod_pos = load_positions(pos_path)
    dump_rows = load_blend_verts(Path(dump_blend_path))
    dump_pos = load_positions(Path(dump_pos_path))
    if not (mod_rows and mod_pos and dump_rows and dump_pos):
        return None
    return vgx_rows_improvement(mod_rows, mod_pos, dump_rows, dump_pos, table)


def vgx_auto_plan(target: Path, dump_meshes: dict):
    """dump 驱动：返回 [{buf, label, mapping, stats}]（还没做去重，交给调用方挑）"""
    ini_filepaths = find_ini_files(target)
    if not ini_filepaths:
        return []

    candidates = []
    seen = set()
    for ini_path in ini_filepaths:
        try:
            text = ini_path.read_text(encoding='utf-8', errors='replace')
        except Exception:
            continue
        for _tex_hash, info in sorted(dump_meshes.items()):
            hit = vgx_auto_candidate(ini_path, text, info)
            if not hit:
                continue
            blend_path, pos_path = hit
            key = str(blend_path.resolve())
            if key in seen:
                continue
            seen.add(key)
            # 已修过的 buf（含拆出来的件）不能再按 dump 推一遍 —— 二次套表骨索引
            # 会转两圈。固定表那条路有这层检查，dump 自动推这条以前漏了
            state = find_backup_like(blend_path)
            if state:
                print('- [VGX] "{}"  [{}]  {}'.format(
                    blend_path, '{}（dump）'.format(info.get('character') or info.get('mesh')),
                    c('已修过({})，跳过'.format(state), Style.YELLOW)))
                continue

            mod_blend = load_blend_verts(blend_path)
            mod_pos = load_positions(pos_path)
            dump_blend = load_blend_verts(Path(info['blend_buf']))
            dump_pos = load_positions(Path(info['position_buf']))
            if not mod_blend or not mod_pos or not dump_blend or not dump_pos:
                continue

            votes, stats = derive_bone_map(mod_blend, mod_pos, dump_blend, dump_pos)
            if not votes:
                print('- [VGX] "{}"  [{}]  {}'.format(
                    blend_path, '{}（dump）'.format(info.get('character') or info.get('mesh')),
                    c('和 dump 位置配不上（半径 {} 内没有顶点），跳过'.format(VGX_RADIUS), Style.YELLOW)))
                continue
            mapping = resolve_bone_map(votes)
            changed = {o: v for o, v in mapping.items() if v['new'] != o}
            if not changed:
                continue      # 全是恒等 = 这个网格已经不用修，不占提示
            # 没标记的 buf 也能判：套表前后各跟 dump 比一次主骨一致率 ——
            # 已经在新空间的，套表不会更好（甚至变差）；没修的会明显变好。
            plain_map = {o: v['new'] for o, v in mapping.items()}
            improvement = vgx_rows_improvement(mod_blend, mod_pos, dump_blend,
                                               dump_pos, plain_map)
            before, after = improvement if improvement else (None, None)
            if before and after and after[0] <= before[0] + VGX_TABLE_MARGIN:
                vgx_marker_of(blend_path).write_text('', encoding='utf-8')
                print('- [VGX] "{}"  [{}]  {}'.format(
                    blend_path, '{}（dump）'.format(info.get('character') or info.get('mesh')),
                    c('套表前后主骨一致率 {:.0%} -> {:.0%}，没有变好，判定已修，跳过'.format(
                        before[0], after[0]), Style.YELLOW)))
                continue

            matched_ratio = stats['matched'] / stats['total'] if stats['total'] else 0
            if matched_ratio < 0.05:
                print('- [VGX] "{}"  [{}]  {}'.format(
                    blend_path, '{}（dump）'.format(info.get('character') or info.get('mesh')),
                    c('和 dump 配得上的顶点只有 {:.1%}，不是同一套网格，跳过'.format(matched_ratio),
                      Style.YELLOW)))
                continue

            candidates.append({
                'buf': blend_path,
                'label': '{}（dump 自动推）'.format(info.get('character') or info.get('mesh') or '?'),
                'mapping': {o: v['new'] for o, v in mapping.items()},
                'detail': mapping,
                'stats': stats,
                'changed': changed,
                'matched_ratio': matched_ratio,
            })
    return candidates


def vgx_plan(target: Path):
    """返回 (待修列表, 已跳过的条数)"""
    ini_filepaths = find_ini_files(target)
    if not ini_filepaths:
        return [], 0, '没找到 ini 文件'

    # 只看本次参照组里的分量：选"铃通用-脸"就只修脸相关的表，
    # 别把身体/头发的骨骼也一起动了（用户明确要的是"参照限定在当前组"）
    active_hashes = {str(key).lower() for key in DUMP_MESHES}
    for info in DUMP_MESHES.values():
        for key in ('position_hash', 'texcoord_hash', 'blend_hash', 'draw_hash', 'ib_hash'):
            value = str(info.get(key) or '').lower()
            if value:
                active_hashes.add(value)

    hits = {}
    for ini_filepath in ini_filepaths:
        try:
            ini_content = ini_filepath.read_text(encoding='utf-8', errors='replace')
        except Exception:
            traceback.print_exc()
            return [], 0, '读取失败 "{}"'.format(ini_filepath)

        for character in VGX_CHARACTERS:
            entry_hashes = {str(value).lower() for value in character.get('hashes', [])}
            if active_hashes and not (entry_hashes & active_hashes):
                continue
            probe_hashes = set(character.get('hashes', []))
            # 有的 mod 不写 Position 覆盖节（vb0/vb2 全藏在 Blend 节里，铃-夏日休闲 这种），
            # 拿 dump 里对应分量的 blend hash 也能顺到那条 blend
            for _info in DUMP_MESHES.values():
                if str(_info.get('position_hash') or '').lower() in entry_hashes:
                    _bh = str(_info.get('blend_hash') or '').lower()
                    if _bh:
                        probe_hashes.add(_bh)
            for position_hash in probe_hashes:
                for blend_path in vgx_blend_filepaths(ini_filepath, ini_content, position_hash):
                    hits.setdefault(str(blend_path.resolve()), (blend_path, []))[1].append(character)

    planned = []
    skipped = 0
    for key in sorted(hits):
        blend_path, characters = hits[key]
        names = []
        for character in characters:
            if character['name'] not in names:
                names.append(character['name'])
        label = ' + '.join(names)

        state = find_backup_like(blend_path)
        if state:
            print('- [VGX] "{}"  [{}]  {}{}{}'.format(
                blend_path, label, Style.YELLOW, '已修过({})，跳过'.format(state), Style.RESET))
            skipped += 1
            continue
        if not blend_path.exists():
            print('- [VGX] "{}"  [{}]  {}'.format(blend_path, label, c('文件不存在，跳过', Style.YELLOW)))
            skipped += 1
            continue

        tables = []
        for character in characters:
            table = dict(zip(character['old'], character['new']))
            if table not in tables:
                tables.append(table)
        if len(tables) > 1:
            print('- [VGX] "{}"  [{}]  {}'.format(
                blend_path, label, c('被两条不同的表命中，无法确定用哪条，跳过', Style.YELLOW)))
            skipped += 1
            continue

        # 没标记的也对比一下：套表前后各跟 dump 比一次主骨一致率。已经在新空间的
        # buf（已有修复痕迹 / 备份标记丢了）套表不会更好，甚至变差 —— 二次映射必须拦住。
        compare_info = None
        character_hashes = {str(value).lower()
                            for character in characters
                            for value in character.get('hashes', ())}
        for _info in DUMP_MESHES.values():
            _vals = {str(_info.get(key) or '').lower() for key in
                     ('position_hash', 'texcoord_hash', 'blend_hash', 'draw_hash', 'ib_hash')}
            if character_hashes & _vals:
                compare_info = _info
                break
        # 参照 dump 跟这个 buf 不是同一条网格时（整件替换类 mod：泳装上衣 6633 顶点
        # vs 游戏 Shirt 1296），主骨一致率没有可比性 —— 套表后数字反而下降，
        # 但表本身是对的（已验证产物就是这么套的）。顶点数差到 5 倍时
        # 不直接撤掉裁判，而是把“变差”的判定阈值放宽；如果一致率还是明显下降，
        # 说明这个 buf 本来就在新空间（Dialyn Hakuhou：腿已经修好，套表反而坏），
        # 仍然按“已修”跳过。裁判本身算不出来（配对不够）时才只按表换。
        compare_suspect = False
        ignore_judge = any(c.get('ignore_dump_judge') for c in characters)
        if compare_info is not None and compare_info.get('position_buf'):
            _mod_verts = len(load_blend_verts(blend_path) or [])
            _dump_verts = len(load_positions(Path(compare_info['position_buf'])))
            if _mod_verts and _dump_verts and _dump_verts * 5 < _mod_verts:
                compare_suspect = True
        table = dict(tables[0])
        if compare_info is not None:
            _added = vgx_augment_out_of_range(blend_path, compare_info, table)
            if _added:
                label += '（超范围骨号按参照补 {} 条）'.format(_added)
        if compare_info is not None and tables:
            improvement = vgx_table_improvement(blend_path, compare_info, table)
            if improvement is not None:
                before, after = improvement
                # 正常网格：没提高 2 个点就算“已修”。
                # 顶点数差 5 倍以上的可疑参照：只有一致率明显下降（5 个点）才
                # 判“已修/不动”；轻微变差仍按老行为信表，避免误伤整件替换类 mod。
                if compare_suspect:
                    if ignore_judge:
                        not_improved = False      # 整件替换：信表，不看一致率
                    else:
                        not_improved = after[0] <= before[0] - VGX_CHECK_SURE
                else:
                    not_improved = after[0] <= before[0] + VGX_TABLE_MARGIN
                if not_improved:
                    vgx_marker_of(blend_path).write_text('', encoding='utf-8')
                    print('- [VGX] "{}"  [{}]  {}'.format(
                        blend_path, label,
                        c('套表前后主骨一致率 {:.0%} -> {:.0%}，没有变好，判定已修，跳过'.format(
                            before[0], after[0]), Style.YELLOW)))
                    skipped += 1
                    continue

        # 这几行先攒着不打印：如果用户等下选了"用 dump 自动推"，这几行就过期了
        planned.append({
            'buf': blend_path, 'table': table, 'label': label,
            'lines': ['- [VGX] "{}"  [{}]'.format(blend_path, label),
                      '        骨骼索引重映射（用表）'],
        })

    return planned, skipped, None


def vgx_apply(planned, total=None, done0=0):
    for index, item in enumerate(planned, 1):
        buf = item['buf']
        original = buf.read_bytes()
        if len(original) % 32:
            print(c('跳过 [VGX]: "{}" 不是 32 字节的整数倍（{} 字节）'.format(
                buf.name, len(original)), Style.YELLOW))
            continue
        vgx_backup_of(buf).write_bytes(original)
        buf.write_bytes(vgx_remap(original, item['table']))
        vgx_marker_of(buf).write_text('', encoding='utf-8')
        print(c('已修 [VGX]: "{}"  ({})'.format(buf.name, item['label']), Style.GREEN))
        iv_progress(done0 + index, total or len(planned), buf.name)


# ==========================================================================
#  二、texcoord 顶点格式
# ==========================================================================

def fmt_stride(fmt):
    return struct.calcsize('<' + ''.join(fmt))


def fmt_count(chunk):
    m = re.match(r'(\d+)', chunk)
    return int(m.group(1)) if m else 0


def target_formats(target):
    old_format = target.get('old_format')
    new_format = target.get('new_format')
    if not old_format or not new_format:
        return None, None
    return tuple(old_format), tuple(new_format)


def validate_texcoord() -> bool:
    ok = True
    for target in TEXCOORD_TARGETS:
        name = target.get('name', '(没写 name)')
        if not re.fullmatch(r'[0-9a-fA-F]{8}', str(target.get('hash', ''))):
            print(c('[配置错误] {}: hash "{}" 不是 8 位十六进制'.format(name, target.get('hash')), Style.RED))
            ok = False

        old_format, new_format = target_formats(target)
        if not old_format:
            print(c('[配置错误] {}: 必须填 old_format 和 new_format'.format(name), Style.RED))
            ok = False
            continue
        element_map = target.get('element_map')
        if element_map is None and len(old_format) != len(new_format):
            print(c('[配置错误] {}: old_format 有 {} 块，new_format 有 {} 块，必须一样多'
                    '（元素个数真的变了就填 element_map）'.format(
                        name, len(old_format), len(new_format)), Style.RED))
            ok = False
            continue
        if element_map is not None:
            if len(element_map) != len(old_format):
                print(c('[配置错误] {}: element_map 有 {} 个，old_format 有 {} 块，必须一样多'.format(
                    name, len(element_map), len(old_format)), Style.RED))
                ok = False
            elif len(set(element_map)) != len(element_map):
                print(c('[配置错误] {}: element_map 里有重复的落位'.format(name), Style.RED))
                ok = False
            elif any((not isinstance(index, int)) or index < 0 or index >= len(new_format)
                     for index in element_map):
                print(c('[配置错误] {}: element_map 里的落位要在 0 ~ {} 之间'.format(
                    name, len(new_format) - 1), Style.RED))
                ok = False
        for chunk in list(old_format) + list(new_format):
            if not re.fullmatch(r'\d+[BefIHi]?', str(chunk)):
                print(c('[配置错误] {}: 格式写法不对 "{}"（例：4B / 2e / 2f / 4f / 4I）'.format(name, chunk), Style.RED))
                ok = False
        if fmt_stride(old_format) == fmt_stride(new_format):
            print(c('[配置警告] {}: old/new 都是 {} 字节，转了等于没转'.format(
                name, fmt_stride(old_format)), Style.YELLOW))
    return ok


def validate_universal() -> bool:
    """通用脸部修复那张名单自查：hash 格式、格式元组是不是还写着 36 -> 48"""
    ok = True
    seen = {}
    for new_hash, (old_hash, label) in sorted(UNIVERSAL_HASHES.items()):
        for tag, value in (('新', new_hash), ('旧', old_hash)):
            if not re.fullmatch(r'[0-9a-fA-F]{8}', str(value)):
                print(c('[配置错误] 通用脸部修复 {}: {} hash "{}" 不是 8 位十六进制'.format(
                    label, tag, value), Style.RED))
                ok = False
        key = str(new_hash).lower()
        if key in seen:
            print(c('[配置警告] 通用脸部修复 hash {} 被 "{}" 和 "{}" 同时使用'.format(
                key, seen[key], label), Style.YELLOW))
        seen[key] = label

    old_stride = fmt_stride(UNIVERSAL_OLD_FORMAT)
    new_stride = fmt_stride(UNIVERSAL_NEW_FORMAT)
    if (old_stride, new_stride) != (36, 48):
        print(c('[配置错误] 通用脸部修复的格式元组算出 {} -> {} 字节/顶点，应该是 36 -> 48'.format(
            old_stride, new_stride), Style.RED))
        ok = False
    return ok


def universal_targets() -> list:
    """把 UNIVERSAL_HASHES 转成 TEXCOORD_TARGETS 那种条目（格式固定，不用填）

    有 dump 的话顺手借它的 blend hash 反推顶点数（不依赖文件命名），没有也能跑。
    """
    rows = []
    for new_hash, (old_hash, label) in sorted(UNIVERSAL_HASHES.items()):
        key = new_hash.lower()
        entry = {
            'name': '{}（通用脸部修复）'.format(label),
            'hash': key,
            'hash_note': '{} -> {}'.format(old_hash.lower(), key),
            'old_format': UNIVERSAL_OLD_FORMAT,
            'new_format': UNIVERSAL_NEW_FORMAT,
            'universal': True,
        }
        info = DUMP_MESHES.get(key)
        if info and info.get('blend_hash'):
            entry['blend_hash'] = info['blend_hash']
        rows.append(entry)
    return rows


def universal_old_map() -> dict:
    """旧 hash -> 新 hash（认"ini 里 hash 还是旧的"用）"""
    return {old_hash.lower(): new_hash.lower()
            for new_hash, (old_hash, _label) in UNIVERSAL_HASHES.items()}


def universal_old_hash_hits(target: Path):
    """通用模式：ini 里 hash 还是旧的那种 -> 提醒先跑版本修复工具

    返回 [(ini 路径, [命中的旧 hash, ...])]，一个 ini 只收一条（不逐节刷屏）。
    """
    old_map = universal_old_map()
    result = []
    for ini_path in find_ini_files(target):
        try:
            text = ini_path.read_text(encoding='utf-8', errors='replace')
        except Exception:
            continue
        found = []
        for match in HASH_LINE_RE.finditer(text):
            value = match.group(1).lower()
            if value in old_map and value not in found:
                found.append(value)
        if found:
            result.append((ini_path, found))
    return result


def universal_color_stats(buf: Path, count: int, stride: int):
    """颜色块小统计：多少顶点颜色全 0、多少个不同取值（只看，不拦）"""
    color_bytes = fmt_stride(UNIVERSAL_OLD_FORMAT[:1])
    data = buf.read_bytes()
    zero = 0
    kinds = set()
    for index in range(count):
        block = data[index * stride:index * stride + color_bytes]
        if not any(block):
            zero += 1
        kinds.add(block)
    return zero, len(kinds)


HASH_LINE_RE = re.compile(r'(?m)^[ \t]*hash[ \t]*=[ \t]*([0-9a-fA-F]{8})[ \t]*$')
VB_LINE_RE = re.compile(r'(?mi)^[ \t]*(vb0|vb1|vb2|run)[ \t]*=[ \t]*(.+?)[ \t]*$')


def find_hash_span(body, hash_value):
    """在节内容里找 hash = xxx（跳过被 ; 注释掉的）"""
    for m in HASH_LINE_RE.finditer(body):
        if m.group(1).lower() == str(hash_value).lower():
            return m.span(1)
    return None


def section_body_map(text):
    """节标题（小写） -> 节文本；同名节保留第一个，跟原来的顺序查找一致"""
    result = {}
    for title, start, end in split_sections(text):
        result.setdefault(title.strip().lower(), text[start:end])
    return result


def follow_slot_resources(text, body, slot, depth=0, section_map=None):
    """收集 slot = xxx（vb1/vb2）；遇到 run = CommandList 追进去"""
    if depth > 5:
        return []
    if section_map is None:
        section_map = section_body_map(text)
    resources = []
    for m in VB_LINE_RE.finditer(body):
        key, value = m.group(1).lower(), m.group(2).strip()
        if key == slot:
            resources.append(value)
        elif key == 'run':
            linked = section_map.get(value.lower())
            if linked is not None:
                resources.extend(follow_slot_resources(
                    text, linked, slot, depth + 1, section_map))
    return resources


def follow_vb1_resources(text, body, depth=0):
    return follow_slot_resources(text, body, 'vb1', depth)


def follow_vb2_resources(text, body, depth=0):
    return follow_slot_resources(text, body, 'vb2', depth)


def find_resource_definition(text, resource_name):
    for title, start, end in split_sections(text):
        if title.strip().lower() != resource_name.strip().lower():
            continue
        body = text[start:end]
        filename_match = re.search(r'(?m)^[ \t]*filename[ \t]*=[ \t]*(.+?)[ \t]*$', body, re.IGNORECASE)
        if not filename_match:
            return None
        stride_match = re.search(r'(?m)^[ \t]*stride[ \t]*=[ \t]*(\d+)', body, re.IGNORECASE)
        return {
            'section': title,
            'filename': filename_match.group(1).strip(),
            'stride': int(stride_match.group(1)) if stride_match else None,
            'stride_span': (start + stride_match.start(1), start + stride_match.end(1)) if stride_match else None,
        }
    return None


def tex_convert(data: bytes, count: int, old_format, new_format, element_map=None) -> bytes:
    """按元素块逐个转换（写法和版本修复工具 zzz_13_remap_texcoord 一致）

    element_map：旧第 i 块落到新布局的第几块。给了它就能处理【元素个数变了】的老 mod
    （常见：老 mod 的 texcoord 只有 2 条 UV，游戏现在是 4 条）——
    新布局里没被映射到的块一律补 0，因为 mod 里根本没有那份数据。
    不给就按老规矩：新旧元素个数必须一样，逐块对位。
    """
    if element_map is None:
        if len(old_format) != len(new_format):
            raise ValueError('old_format 和 new_format 的元素个数必须一样')
        element_map = list(range(len(old_format)))
    else:
        element_map = list(element_map)
        if len(element_map) != len(old_format):
            raise ValueError('element_map 的长度必须和 old_format 一样')
        if len(set(element_map)) != len(element_map):
            raise ValueError('element_map 里有重复的落位')
        if any((not isinstance(j, int)) or j < 0 or j >= len(new_format) for j in element_map):
            raise ValueError('element_map 里有超出 new_format 范围的下标')

    old_stride = fmt_stride(old_format)
    old_offsets = [0]
    for chunk in old_format:
        old_offsets.append(old_offsets[-1] + struct.calcsize('<' + chunk))

    source_of = {new_index: old_index for old_index, new_index in enumerate(element_map)}

    out = bytearray()
    for i in range(count):
        base = i * old_stride
        for j, new_chunk in enumerate(new_format):
            old_index = source_of.get(j)
            if old_index is None:                 # 新布局多出来的块，mod 里没有 -> 补 0
                out.extend(struct.pack('<' + new_chunk, *([0] * fmt_count(new_chunk))))
                continue
            old_chunk = old_format[old_index]
            start = base + old_offsets[old_index]
            end = base + old_offsets[old_index + 1]
            if old_chunk == new_chunk:            # 没变，原样搬
                out.extend(data[start:end])
                continue
            # 颜色块：字节 0-255 和 0.0-1.0 的浮点 / 半浮点互转（不是原样搬数值）
            if old_chunk == '4B' and new_chunk == '4f':
                out.extend(struct.pack('<4f', *[b / 255.0 for b in struct.unpack_from('<4B', data, start)]))
            elif old_chunk == '4f' and new_chunk == '4B':
                values = [min(255, max(0, int(round(f * 255)))) for f in struct.unpack_from('<4f', data, start)]
                out.extend(struct.pack('<4B', *values))
            elif old_chunk == '4B' and new_chunk == '4e':
                out.extend(struct.pack('<4e', *[b / 255.0 for b in struct.unpack_from('<4B', data, start)]))
            elif old_chunk == '4e' and new_chunk == '4B':
                values = [min(255, max(0, int(round(f * 255)))) for f in struct.unpack_from('<4e', data, start)]
                out.extend(struct.pack('<4B', *values))
            else:                                  # 其他块按格式重新打包
                out.extend(struct.pack('<' + new_chunk, *struct.unpack_from('<' + old_chunk, data, start)))
    return bytes(out)


def vertex_count_of(buf_path: Path):
    """用同名的 Blend(32) / Position(40) 反推顶点数"""
    stem = buf_path.name[:-4]
    for suffix, stride in (('Blend', 32), ('Position', 40)):
        for candidate in (buf_path.with_name(stem.replace('Texcoord', suffix) + '.buf'),
                          buf_path.with_name(stem.replace('texcoord', suffix) + '.buf')):
            if candidate.exists():
                size = candidate.stat().st_size
                if size % stride == 0:
                    return size // stride, candidate.name
    return None, None


def blend_buf_by_hash(ini_path: Path, text: str, blend_hash):
    """按 blend 节的 hash 找 blend 缓冲文件（不依赖文件命名）"""
    if not blend_hash:
        return None
    for title, start, end in split_sections(text):
        body = text[start:end]
        m = HASH_LINE_RE.search(body)
        if not m or m.group(1).lower() != str(blend_hash).lower():
            continue
        for resource in follow_vb2_resources(text, body):
            definition = find_resource_definition(text, resource)
            if not definition:
                continue
            path = ini_path.parent / definition['filename']
            if path.exists():
                return path
    return None


def vertex_count_by_hash(ini_path: Path, text: str, blend_hash):
    """按 blend 节的 hash 找 blend 缓冲 -> 顶点数"""
    path = blend_buf_by_hash(ini_path, text, blend_hash)
    if path and path.stat().st_size % 32 == 0:
        return path.stat().st_size // 32, path.name
    return None, None


def dxgi_chunk(fmt, width):
    """DXGI 格式名 -> 顶点格式记法（认不出来就按字节数猜一个等宽写法）"""
    if fmt in DXGI_CHUNK:
        return DXGI_CHUNK[fmt]
    if width % 4 == 0:
        return '{}f'.format(width // 4)
    if width % 2 == 0:
        return '{}e'.format(width // 2)
    return '{}B'.format(width)


def load_dump_folder(folder: Path):
    """读 dump 文件夹里的 json -> {texcoord hash: {mesh, new_format, blend_hash}}

    分组名（只影响输出显示，也决定一次修多少）：
        直接放在 dump 根目录 -> 文件名（不含 .json）
        放在子文件夹里       -> 一级子文件夹名
    """
    meshes = {}
    for json_path in sorted(folder.rglob('*.json')):
        try:
            data = json.loads(json_path.read_text(encoding='utf-8', errors='replace'))
        except Exception:
            continue

        hashes = {str(k).lower(): str(v).lower() for k, v in (data.get('CategoryHash') or {}).items()}
        tex_hash = hashes.get('texcoord')
        if not tex_hash:
            continue

        elements = None
        for category in data.get('CategoryBufferList', []):
            items = category.get('D3D11ElementList', [])
            if items and str(items[0].get('Category', '')).lower() == 'texcoord':
                elements = items
                break
        if not elements:
            continue

        relative = json_path.relative_to(folder)
        character = relative.parts[0] if len(relative.parts) > 1 else json_path.stem

        new_format = tuple(dxgi_chunk(str(e.get('Format', '')), int(e.get('ByteWidth', 0)))
                           for e in elements)
        new_stride = fmt_stride(new_format)
        # 元素名（COLOR0 / TEXCOORD0 …）：只拿来打印，好认是哪一块
        semantics = ['{}{}'.format(e.get('SemanticName', ''), e.get('SemanticIndex', ''))
                     for e in elements]

        # 同一个文件夹里 3DMigoto 还会 dump 出 -*Blend.buf / -*Position.buf / -*Texcoord.buf
        # blend + position（能被 32 / 40 整除）才能自动推 VGX 映射；
        # texcoord（能被 dump 的元素表算出的步幅整除）用来给"元素个数变了"的老 mod
        # 反推每块落在哪 —— 没有它也能跑，只是那种 buf 推不出来
        blend_buf = position_buf = texcoord_buf = None
        try:
            for candidate in sorted(json_path.parent.iterdir()):
                low = candidate.name.lower()
                if not candidate.is_file() or not low.endswith('.buf'):
                    continue
                if 'backup' in low:
                    continue
                size = candidate.stat().st_size
                if 'blend' in low and size and size % 32 == 0:
                    blend_buf = blend_buf or candidate
                elif 'position' in low and size and size % 40 == 0:
                    position_buf = position_buf or candidate
                elif 'texcoord' in low and size and new_stride and size % new_stride == 0:
                    texcoord_buf = texcoord_buf or candidate
        except OSError:
            pass

        # 索引段：目录名是 <ib hash>-<索引数>-<首个索引>；draw hash 在 json 的 VertexLimitVB
        seg_dir = json_path.parent.parent if json_path.parent.name.startswith('TYPE_') else json_path.parent
        segment = re.fullmatch(r'([0-9a-fA-F]{8})-(\d+)-(\d+)', seg_dir.name)
        ib_hash = ''
        first_index = index_count = None
        if segment:
            ib_hash = segment.group(1).lower()
            index_count, first_index = int(segment.group(2)), int(segment.group(3))
        else:
            stem_parts = json_path.stem.split('-')       # 用 stem，别带 .json
            if (len(stem_parts) >= 3 and re.fullmatch(r'[0-9a-fA-F]{8}', stem_parts[0])
                    and stem_parts[1].isdigit() and stem_parts[2].isdigit()):
                ib_hash = stem_parts[0].lower()
                index_count, first_index = int(stem_parts[1]), int(stem_parts[2])

        # 键带分组名：不同皮肤会共用 texcoord hash（铃-原皮/铃-泳装的耳坠
        # a2ee3518 就是），只按 tex_hash 存，后加载的那组会把前一组顶掉
        meshes[(character, tex_hash)] = {
            'mesh': json_path.name.split('-')[0],
            'character': character,
            'segment': seg_dir.name,
            'ib_hash': ib_hash,
            'first_index': first_index,
            'index_count': index_count,
            'draw_hash': str(data.get('VertexLimitVB') or '').lower(),
            'new_format': new_format,
            'semantics': semantics,
            'textures': [str(item.get('MarkName', '')) for item in (data.get('TextureMarkUpInfoList') or [])
                         if item.get('MarkName')],
            'blend_hash': hashes.get('blend'),
            'position_hash': hashes.get('position'),
            'blend_buf': blend_buf,
            'position_buf': position_buf,
            'texcoord_buf': texcoord_buf,
            'source': json_path.name,
        }
    return meshes


def dump_places() -> list:
    """dump\\ 能放的几个位置（程序目录 + 上一级），按优先级从低到高 ——
    两处有同名网格时，后面那份说了算。"""
    places = []
    for base in APP_DIRS:
        folder = base / DUMP_DIR_NAME
        if folder not in places:
            places.append(folder)
    return places


def dump_roots():
    r"""要自动扫描的 dump 根目录，按优先级从低到高（后面的覆盖前面的同名网格）：
    旧位置 索引与顶点修复工具\dump\（有就用，照顾老用户）
        -> 程序目录下的 dump\   <- 正式位置，以后就用它
        -> 上一级的 dump\（脚本放在 py代码\ 子目录时的位置）
        -> DUMP_DIRS 里配置的 / 运行时选的"""
    roots = []
    for folder in dump_places():
        legacy = folder.parent / '索引与顶点修复工具' / DUMP_DIR_NAME
        if legacy.is_dir() and legacy not in roots:
            roots.append(legacy)
        if folder not in roots:
            roots.append(folder)
    for raw in DUMP_DIRS:
        path = Path(raw)
        if path not in roots:
            roots.append(path)
    return roots


def refresh_dumps():
    r"""加载 dump：本程序目录下的 dump\ 里的 + DUMP_DIRS 里配置的

    读到的全放进 ALL_DUMPS，DUMP_MESHES 是这次实际生效的那一份
    （用户选了某一组就只留那一组的）。
    """
    ALL_DUMPS.clear()
    for folder in dump_roots():
        if folder.is_dir():
            for key, info in load_dump_folder(folder).items():
                ALL_DUMPS[key] = info
    set_active_dumps(None)


def character_of(info: dict) -> str:
    """参照分组名 —— 按 dump 里的【文件夹名】走，不做角色归类。

    子文件夹里的 json 取它所在的一级文件夹名；直接放 dump\\ 根目录的取文件名。
    文件名里带 '-' '_' 也不拆：一个文件夹 = 一组参照 = 一次修复的范围。
    拆了就会把已经修过的那组一起带上，同一个网格修两遍。
    """
    name = info.get('character') or info.get('mesh') or '?'
    return name


def dump_items(dumps: dict = None):
    """遍历 dump：ALL_DUMPS 的键是 (分组名, tex_hash)，DUMP_MESHES 的键只是 tex_hash"""
    for key, info in (ALL_DUMPS if dumps is None else dumps).items():
        tex_hash = key[1] if isinstance(key, tuple) else key
        yield tex_hash, info


def dump_info(tex_hash):
    """按 texcoord hash 找一条 dump（多组共用同一 tex 时任取一条）"""
    for tex, info in dump_items():
        if tex == tex_hash:
            return info
    return None


def character_groups(dumps: dict = None) -> dict:
    """按参照分组（dump 里的文件夹）-> {组名: [tex_hash, ...]}"""
    groups = {}
    for tex_hash, info in dump_items(dumps):
        groups.setdefault(character_of(info), []).append(tex_hash)
    return groups


def set_active_dumps(character):
    """把生效的 dump 限定到某一组参照；None = 全都用"""
    DUMP_MESHES.clear()
    if character is None:
        for tex_hash, info in dump_items():
            DUMP_MESHES[tex_hash] = info
        return
    for tex_hash, info in dump_items():
        if character_of(info) == character:
            DUMP_MESHES[tex_hash] = info


def dump_mesh_names(character) -> str:
    """这组参照下都有哪些网格（显示用）"""
    names = sorted({Path(info.get('source') or '').stem or '?'
                    for _tex, info in dump_items()
                    if character_of(info) == character})
    return '、'.join(names)


def describe_active_dumps() -> str:
    if not DUMP_MESHES:
        return '没有'
    groups = character_groups(DUMP_MESHES)
    return '、'.join('{}({})'.format(name, len(groups[name])) for name in sorted(groups))


def choose_character():
    """让用户选这次用哪组参照（dump 里的一个文件夹）；返回组名，None = 没有 dump

    只能选某一组（不提供"全都用"）—— 跨组匹配会把别的组的网格也扫进来。
    """
    if not ALL_DUMPS:
        return None

    groups = character_groups()
    if len(groups) == 1:
        only = next(iter(groups))
        set_active_dumps(only)
        print('dump\\ 里只有一组参照：{}（{}）'.format(only, dump_mesh_names(only)))
        print()
        return only

    print('dump\\ 里有这些参照（一组 = dump 里的一个文件夹）：')
    names = sorted(groups)
    for index, name in enumerate(names, 1):
        print('  {}. {:<10} {}'.format(index, name, dump_mesh_names(name)))
    print()

    while True:
        raw = ask('  这次用哪组参照？输序号（回车 = 1）: ').strip()
        if raw.lower() in EXIT_WORDS:
            print('退出。')
            sys.exit(0)
        if raw == '':
            index = 1
        elif raw.isdigit():
            index = int(raw)
        else:
            print(c('  输个序号。', Style.YELLOW))
            continue
        if 1 <= index <= len(names):
            name = names[index - 1]
            set_active_dumps(name)
            print('  这次只用【{}】的参照：{}'.format(name, dump_mesh_names(name)))
            print()
            return name
        print(c('  没有这个序号。', Style.YELLOW))


DUMP_README = r"""dump 文件夹 —— 各组参照的网格信息（贴图错乱修复用）
================================================

普通用户
    不用动这里，也不用自己做任何操作。这是作者放好的数据，
    程序启动时自动读 —— 你直接把 mod 文件夹拖进程序窗口就行。

    这个文件夹就在本程序目录（脚本旁边）；删了下次启动会自动重建一个空的。
    换新版程序时它跟着一起换，别在这里放自己的东西。

    里面缺哪个角色/哪个网格，反馈给作者补一份即可。
    （进游戏抓 dump 是作者的事，不需要你来做。）

    自己抓的 dump 想推 VGX 表（新旧两版同一个部位），用 查找工具\两版推VGX表，
    它出的是能直接贴进本工具 VGX_CHARACTERS 的代码块 —— 本工具不自己推，
    保持精简。

作者（维护这个文件夹的人）
    把 F8 抓的 Frame Analysis dump 的 json 丢进来，**一个参照一个子文件夹**：

        dump\
            琉音-脸\
                琉音-脸.json
            艾莲-腿\
                d44a8015-24321-0.json

    分组按【文件夹名】走，不按角色合并 —— 一个文件夹 = 一组参照 =
    一次修复的范围。所以同一角色的不同部位/不同 mod 各放一个文件夹，
    名字写成「角色-部位」，下拉里就是一组一条：
        琉音-脸、琉音-腿、艾莲-腿 ……  而不是合并成一个「琉音」。
    合并了的话，选「琉音」会把已经修过的「琉音-腿」一起带上，
    同一个网格会被修第二遍 —— 所以千万别按角色合到同一个文件夹里。

    文件夹名只用来在输出里显示，随便改，json 内容不依赖文件名。
    整个 3DMigoto 那种嵌套目录（<ib hash>-<n>-<i>\TYPE_...\xxx.json）
    直接拷过来也行，程序会递归找，一级文件夹名当组名。

    抓法：游戏里进到该角色的画面，按 F8 抓 Frame Analysis，在 3DMigoto 的
    FrameAnalysis 文件夹里找到该网格的 json（文件名形如
    <ib hash>-<索引数>-<首个索引>.json），复制过来。

    顺带也管骨骼索引（VGX，腿弯 / 塌陷 / 扭曲）：
    同一个网格文件夹里再放上它的 -*Blend.buf 和 -*Position.buf，工具就能拿
    dump 当参照自动推索引映射 —— mod 的网格通常是游戏原网格的细分版，
    位置对得上，于是逐顶点投票，把 mod 的旧索引对上 dump 的新索引。

        json          该网格的 CategoryHash（定位 mod 那边是哪个 buf）
        -*Blend.buf   新编号的骨骼索引（投票的目标）
        -*Position.buf 位置（配对用，缺了这个就推不了）
        -*Texcoord.buf 顶点数据（老 mod 的 buf 比游戏少几块时，靠它对各块的值域推落位）

    抓 dump 时这三样本来就在同一个 TYPE_ 目录里，整个文件夹拷过来即可。

    实测琉音身体：mod 351810 顶点 / 游戏 15715 顶点，位置最近距离中位
    0.0033（身高的约 0.3%），推出来的映射和已知的表比对 25/26 一致。

注意
    - json 要能看到这个网格的 texcoord，抓的时候别选错 draw
    - 前提仍然是 mod 的 ini 里 hash 已经是当前值（先跑版本修复工具），
      VGX 自动推也是靠 dump 的 CategoryHash 去 ini 里定位 buf 的
    - 表里和 dump 里都能修同一个网格时，程序会问一次用哪个
      （texcoord 默认表，由 PREFER_DUMP 决定；VGX 默认推荐表）
    - 表里没有、只有 dump 能推的网格，程序会问一次要不要用 dump 推的修
"""


def ensure_dump_dir():
    """本程序目录下的 dump\\ 不存在就建一个，附一份说明。
    这是 dump 的正式位置：以后新 dump 都往这里放。
    旧位置（索引与顶点修复工具\\dump\\）只是兼容，读到就用，不再往那边放东西。
    程序目录和上一级哪个已经有 dump\\ 了就不再多建一个 —— 建错地方会让人
    以为数据没放（脚本在 py代码\\、dump\\ 在外面时就是这种）。"""
    if any(folder.is_dir() for folder in dump_places()):
        return
    folder = SCRIPT_DIR / DUMP_DIR_NAME
    try:
        folder.mkdir(exist_ok=True)
        readme = folder / '说明.txt'
        if not readme.exists():
            readme.write_text(DUMP_README, encoding='utf-8')
    except Exception:
        pass


def load_dump_into_session(folder: Path):
    """运行时把 dump 文件夹拖进来，返回 (新增网格数, 共读到几个, 新增的分组名)"""
    found = load_dump_folder(folder)
    added = 0
    names = set()
    for key, info in found.items():
        tex_hash = key[1] if isinstance(key, tuple) else key
        if key not in ALL_DUMPS:
            added += 1
            names.add(character_of(info))
        ALL_DUMPS[key] = info
        DUMP_MESHES[tex_hash] = info
    return added, len(found), sorted(names)


def infer_old_formats(new_format, per_vertex) -> list:
    """从 new_format 倒推旧格式：把某个 float4 块缩成 4 字节 / half4，看哪个等宽

    返回所有凑得上每顶点字节数的候选，按位置从前往后。
    真实改法是顶点 COLOR 那块，在 texcoord 里排第一个，所以取第一个候选。
    """
    hits = []
    for index, chunk in enumerate(new_format):
        if chunk != '4f':
            continue
        for shrink in ('4B', '4e'):
            candidate = list(new_format)
            candidate[index] = shrink
            if fmt_stride(tuple(candidate)) == per_vertex:
                hits.append(tuple(candidate))
    return hits


# ---- 元素个数变了的推法（老 mod 比游戏少几块，比如只有 2 条 UV）----------------

LAYOUT_RANGE_EPS = 0.02    # 值域包含的容差（mod 是改过的网格，边界允许差一点）


def layout_candidates(new_format, per_vertex) -> list:
    """按字节数凑候选：保留 dump 元素表的一个子集，其中 4f 那块可以缩成 4B / 4e

    老 mod 的 texcoord 往往比游戏少几块（当年只有 2 条 UV，现在 4 条）。
    返回 [{'old_format', 'element_map', 'unmatched'}]：
        old_format   按保留顺序拼出来的旧布局（被缩的那块已经是 4B / 4e）
        element_map  旧第 i 块落在新布局的第几块（就是 dump 元素表里保留下来的下标）
        unmatched    保留下来的、既不是 2f、也不是被缩的那块的元素 —— 没法拿值域对，
                     只能在候选唯一时才敢用
    """
    sizes = [struct.calcsize('<' + chunk) for chunk in new_format]
    total = len(new_format)
    out = []
    seen = set()
    for mask in range(1, 1 << total):
        kept = [index for index in range(total) if mask >> index & 1]
        # 只认"前缀"：老 mod 的 texcoord 是当年那份布局，游戏后来把新元素排在后面；
        # 跳过中间某块、却保留它后面那块（色 + T0 + T3 这种）在作者那边不会发生，
        # 而且值域会撞车（铃-白泳果子足 的身体 UV1 会误配到 T3）。
        if kept != list(range(len(kept))):
            continue
        bytes_now = sum(sizes[index] for index in kept)
        choices = [(None, None)]                       # (被缩的新块下标, 缩成什么)
        for index in kept:
            if new_format[index] == '4f':
                choices += [(index, shrink) for shrink in ('4B', '4e')]
            elif new_format[index] == '2f':
                # 老 mod 那条 UV 可能是半精度（R16G16，4 字节）：按 2e 读、写时换成浮点
                # （铃-白泳果子足：老的 texcoord 12 字节 = 色 + 2 条半精度 UV，
                #   新的 20 字节 = 色 + 半精度UV + 浮点UV + 半精度UV）
                choices.append((index, '2e'))
        for shrunk, shrink_format in choices:
            got = bytes_now
            if shrunk is not None:
                got = bytes_now - sizes[shrunk] + struct.calcsize('<' + shrink_format)
            if got != per_vertex:
                continue
            old_format = tuple(shrink_format if index == shrunk else new_format[index]
                               for index in kept)
            key = (old_format, tuple(kept))
            if key in seen:
                continue
            seen.add(key)
            out.append({
                'old_format': old_format,
                'element_map': list(kept),
                'unmatched': [index for index in kept
                              if new_format[index] not in ('2f', '2e', '4B', '4ub', '4e', '4f')
                              and index != shrunk],
            })
    return out


def chunk_value_ranges(data: bytes, count: int, chunks) -> list:
    """每块里 float 的取值范围 [((最小, 最大)) 或 None]

    只认 UV 块（2f 浮点 / 2e 半精度）：两个分量一起取最值。别的块给 None（不参与对值）。
    NaN / inf 的顶点直接跳过（真 dump 里就有这种退化 UV）；有限值却大得离谱的，
    说明这个布局根本不是这么切的 —— 整块判 None。
    """
    offsets = [0]
    for chunk in chunks:
        offsets.append(offsets[-1] + struct.calcsize('<' + chunk))
    stride = offsets[-1]
    if stride:
        # dump 的 buf 顶点数可能远少于 mod 网格（耳坠 360 vs 头发 1 万多）：
        # 只按这份 buf 里实际装得下的顶点数读，别越界
        count = min(count, len(data) // stride)
    result = []
    for index, chunk in enumerate(chunks):
        if chunk not in ('2f', '2e'):
            result.append(None)
            continue
        low = high = None
        broken = False
        for i in range(count):
            u, v = struct.unpack_from('<' + chunk, data, i * stride + offsets[index])
            for value in (u, v):
                if value != value or value in (float('inf'), float('-inf')):
                    continue
                if abs(value) > 1e6:
                    broken = True
                    break
                if low is None or value < low:
                    low = value
                if high is None or value > high:
                    high = value
            if broken:
                break
        if low is not None and high is not None and max(abs(low), abs(high)) < 1e-4:
            # 全是 1e-5 以下的数：把颜色/别的块当 UV 读出来的退化值，不是真 UV
            result.append(None)
            continue
        result.append(None if broken or low is None else (low, high))
    return result


def dump_layout_ranges(info: dict):
    """dump 的 texcoord buf 按 dump 元素表算出来的各块取值范围；没带 buf 返回 None"""
    path = info.get('texcoord_buf')
    if not path:
        return None
    path = Path(path)
    new_format = tuple(info['new_format'])
    stride = fmt_stride(new_format)
    try:
        data = path.read_bytes()
    except Exception:
        return None
    if not stride or not data or len(data) % stride:
        return None
    return chunk_value_ranges(data, len(data) // stride, new_format)


def match_chunks_to_dump(mod_ranges, dump_ranges):
    """把 mod 的每块（2f）对到 dump 的某块上 -> {新块下标: 旧块下标}；对不出唯一返回 None

    规则：mod 那块的值域要落在 dump 那块的值域里，且取最紧的那个；
    两个 dump 块一样紧 = 说不清，直接放弃（宁可不修，不乱修）。
    """
    options = []
    for old_index, mod_range in enumerate(mod_ranges):
        if mod_range is None:
            continue
        hits = []
        for dump_index, dump_range in enumerate(dump_ranges):
            if dump_range is None:
                continue
            if (mod_range[0] >= dump_range[0] - LAYOUT_RANGE_EPS
                    and mod_range[1] <= dump_range[1] + LAYOUT_RANGE_EPS):
                hits.append((dump_range[1] - dump_range[0], dump_index))
        if not hits:
            return None
        hits.sort()
        if len(hits) > 1 and abs(hits[0][0] - hits[1][0]) < 1e-9:
            return None                    # 一样紧，认不出是哪块
        options.append((old_index, [item[1] for item in hits]))

    options.sort(key=lambda item: len(item[1]))       # 选择少的先定，挤掉其它候选的可能性
    used = set()
    assignment = {}
    for old_index, targets in options:
        for dump_index in targets:
            if dump_index in used:
                continue
            assignment[dump_index] = old_index
            used.add(dump_index)
            break
        else:
            return None
    return assignment


def derive_element_layout(buf: Path, count: int, per_vertex: int, info: dict):
    """buf 比 dump 少几块时，推【旧第几块 -> 新第几块】，缺的块补 0

        1. 按字节数凑候选（layout_candidates）
        2. 用 dump 的 texcoord buf 里各块的实际取值范围筛：mod 每块的值域必须落在 dump
           对应的那块里，且这个对应关系要和候选自己给的顺序一致
        3. dump 没带 texcoord buf（老 dump 只有 json）时，只有候选唯一才敢用

    返回 {'ok': True, 'old_format', 'element_map', 'note'}；
    推不出返回 {'ok': False, 'reason'}（reason 是给用户看的一句话，说清卡在哪）。
    """
    try:
        data = buf.read_bytes()
    except Exception:
        return {'ok': False, 'reason': 'buf 读不出来'}

    new_format = tuple(info['new_format'])
    candidates = layout_candidates(new_format, per_vertex)
    if not candidates:
        return {'ok': False, 'reason':
                '按每顶点 {} 字节凑不出 dump 元素表的子集 —— 形状不是"少几块"这种'.format(per_vertex)}

    dump_ranges = dump_layout_ranges(info)
    matched = []
    if dump_ranges is not None:
        for candidate in candidates:
            old_format = candidate['old_format']
            if candidate['unmatched']:
                continue
            mod_ranges = chunk_value_ranges(data, count, old_format)
            expected = {}
            broken = False
            for old_index, chunk in enumerate(old_format):
                if chunk != '2f':
                    continue
                if mod_ranges[old_index] is None:
                    broken = True        # 这么切出来不是像样的 UV，这个候选不对
                    break
                expected[candidate['element_map'][old_index]] = old_index
            if broken:
                continue
            if match_chunks_to_dump(mod_ranges, dump_ranges) == expected:
                matched.append(candidate)

    prefixes = [item for item in candidates
                if item['element_map'] == list(range(len(item['old_format'])))
                and item['old_format'] == new_format[:len(item['old_format'])]]
    if len(matched) == 1:
        candidate = matched[0]
        how = '（按 dump 各块的值域对出来的）'
    elif not matched and len(prefixes) == 1:
        # 老 mod 的 texcoord 就是当年那份布局，游戏后来加的元素排在后面；
        # 值域对不上多半是 mod 自己改过 UV，但"少的是最后几块"这件事只有一种切法
        candidate = prefixes[0]
        how = ('（老 mod 少的是排在最后的那几块，按前缀切、缺的补 0）')
    elif not matched and len(candidates) == 1 and not candidates[0]['unmatched']:
        candidate = candidates[0]
        how = '（只有这一种凑得上，dump 没带 texcoord buf，没别的佐证）'
    else:
        if dump_ranges is None:
            reason = ('dump 里没有这个网格的 texcoord buf，{} 种凑法分不出用哪个'
                      '（把 -*Texcoord.buf 跟 json 一起放进 dump\\）'.format(len(candidates)))
        elif all(candidate['unmatched'] for candidate in candidates):
            reason = '留下来的块里除颜色外还有对不了值的元素，认不出落位'
        else:
            reason = 'buf 里各块的值域和 dump 对不上（多半这份 mod 的 UV 自己改过），认不出落位'
        return {'ok': False, 'reason': reason}

    element_map = candidate['element_map']
    missing = [index for index in range(len(new_format)) if index not in set(element_map)]
    semantics = info.get('semantics') or []
    names = []
    for index in missing:
        names.append(semantics[index] if index < len(semantics) and semantics[index]
                     else '第 {} 块'.format(index + 1))
    note = '旧 {} 块 -> 新 {} 块：{}'.format(
        len(element_map), len(new_format),
        '、'.join('{}->{}'.format(i + 1, j + 1) for i, j in enumerate(element_map)))
    if missing:
        note += '，缺的 {} 补 0'.format('、'.join(names))
    note += how
    return {'ok': True, 'old_format': candidate['old_format'],
            'element_map': element_map, 'note': note}


def infer_layout_from_dump(buf: Path, count: int, per_vertex: int, info: dict):
    """buf 和 dump 的元素表对不上时，用 dump 的元素表 + buf 实际字节推一份能用的

    先按【元素个数不变、只缩一块】推（36 -> 48 那种）；推不出再按【少了几块】推。
    返回 {'ok': True, 'old_format', 'element_map', 'note', 'multi'}，
    或 {'ok': False, 'reason'}（说清卡在哪，用户自己能补数据 / 判断）；
    也已经是新格式时返回 None。
    element_map 为 None = 元素个数没变，multi = 同尺寸有多种凑法（取最靠前的那块 COLOR）。
    """
    new_format = tuple(info['new_format'])
    if per_vertex == fmt_stride(new_format):
        return None                     # 已经是新格式（调用方自己会判，这里只是保险）
    same = infer_old_formats(new_format, per_vertex)
    if same:
        return {'ok': True, 'old_format': same[0], 'element_map': None, 'multi': len(same) > 1,
                'note': '元素个数没变，按 buf 大小倒推：{}  ->  {}'.format(
                    ' + '.join(same[0]), ' + '.join(new_format))}
    return derive_element_layout(buf, count, per_vertex, info)


def tex_backup_of(buf: Path) -> Path:
    return buf.with_name(buf.stem + TEX_BACKUP_SUFFIX)


def tex_marker_of(buf: Path) -> Path:
    return buf.with_name(buf.stem + TEX_MARKER_SUFFIX)


def tex_inventory(target: Path):
    """按网格分组列出所有 texcoord buf：[(buf, 每顶点字节数)]"""
    groups = {}
    for path in sorted(target.rglob('*.buf')):
        name = path.name[:-4]
        low = name.lower()
        if 'backup' in low or '.bak' in low:
            continue
        for suffix in ('position', 'blend', 'texcoord'):
            if low.endswith(suffix):
                groups.setdefault(name[:-len(suffix)], {})[suffix] = path
                break

    rows = []
    for group in groups.values():
        count = None
        for suffix, stride in (('blend', 32), ('position', 40)):
            path = group.get(suffix)
            if path and path.exists() and path.stat().st_size % stride == 0:
                count = path.stat().st_size // stride
                break
        path = group.get('texcoord')
        if not path or not count or not path.exists():
            continue
        size = path.stat().st_size
        rows.append((path, size // count if size % count == 0 else size / count))
    return rows


def dump_old_strides() -> dict:
    """dump 里的网格倒推出来的旧步幅 -> {步幅: 分组名集合}"""
    result = {}
    for info in DUMP_MESHES.values():
        new_stride = fmt_stride(info['new_format'])
        who = info.get('character') or info.get('mesh') or '?'
        for delta in (12, 8):      # COLOR 块缩成 4B / half4
            for candidate in infer_old_formats(info['new_format'], new_stride - delta):
                result.setdefault(fmt_stride(candidate), set()).add(who)
    return result


def table_hashes():
    return {str(entry.get('hash', '')).lower() for entry in TEXCOORD_TARGETS}


def dump_entry(tex_hash: str, info: dict) -> dict:
    """把 dump 里的一个网格转成一条内部条目"""
    source = info['source']
    if info.get('character') and info['character'] != Path(source).stem:
        # 放在子文件夹里：带上文件夹名，好定位是哪个网格的 dump
        label = '{}（dump：{}\\{}）'.format(info['mesh'], info['character'], source)
    else:
        # 直接放在 dump\ 下：文件名就是分组名，不用再重复一遍
        label = '{}（dump）'.format(Path(source).stem)
    return {
        'name': label,
        'hash': tex_hash,
        'new_format': info['new_format'],
        'blend_hash': info['blend_hash'],
        'from_dump': True,
    }


def dump_conflicts():
    """表里和 dump 里都有的网格 hash（两边数据可能不一样，要用户挑一个）"""
    return sorted(set(DUMP_MESHES) & table_hashes())


def conflicts_differ():
    """两边都有的网格里，数据真的对不上的那些"""
    result = []
    for entry in TEXCOORD_TARGETS:
        info = DUMP_MESHES.get(str(entry.get('hash', '')).lower())
        if not info:
            continue
        _old, new_format = target_formats(entry)
        if not new_format:
            continue
        if tuple(new_format) != tuple(info['new_format']):
            result.append((entry, info))
    return result


def target_entries(use_dump_for_conflicts: bool = None) -> list:
    """常规模式这次能用的目标：表里的 + dump 里多出来的

    两边都有的网格：按 PREFER_DUMP（或用户当场选的）留一个。
    选了参照组时，表里的条目也要过参照组的 hash —— 选「琉音-腿」就只修腿相关的，
    不会顺手把脸也修了（用户报过：用腿修，脸也跟着变）。
    """
    if use_dump_for_conflicts is None:
        use_dump_for_conflicts = PREFER_DUMP
    active_hashes = set()
    for tex_hash, info in DUMP_MESHES.items():
        active_hashes.add(str(tex_hash).lower())
        for key in ('position_hash', 'texcoord_hash', 'blend_hash', 'draw_hash', 'ib_hash'):
            value = str(info.get(key) or '').lower()
            if value:
                active_hashes.add(value)
    skip_from_dump = set() if use_dump_for_conflicts else table_hashes()
    skip_from_table = table_hashes() if use_dump_for_conflicts else set()

    entries = []
    for entry in TEXCOORD_TARGETS:
        entry_hash = str(entry.get('hash', '')).lower()
        if entry_hash in skip_from_table:
            continue
        if (active_hashes and entry_hash not in active_hashes
                and str(entry.get('blend_hash') or '').lower() not in active_hashes):
            continue
        entries.append(entry)
    for tex_hash, info in sorted(DUMP_MESHES.items()):
        if tex_hash in skip_from_dump:
            continue
        entries.append(dump_entry(tex_hash, info))
    return entries


def tex_plan(target: Path, use_dump_for_conflicts: bool = None, entries: list = None):
    """按 hash 定位目标网格，返回 (待改列表, 已跳过条数, 错误)

    entries 给了就用它（通用脸部修复模式给的是 UNIVERSAL_HASHES 那张名单），
    没给就按常规模式自己拼（表 + dump）。
    """
    ini_filepaths = find_ini_files(target)
    if not ini_filepaths:
        return [], 0, '没找到 ini 文件'

    if entries is None:
        entries = target_entries(use_dump_for_conflicts)

    items = []
    seen = set()
    for ini_path in ini_filepaths:
        text = ini_path.read_text(encoding='utf-8', errors='replace')
        sections = split_sections(text)

        for target_entry in entries:
            for title, start, end in sections:
                body = text[start:end]
                span = find_hash_span(body, target_entry['hash'])
                if span is None:
                    continue

                for resource in follow_vb1_resources(text, body):
                    definition = find_resource_definition(text, resource)
                    if not definition:
                        continue
                    buf_path = ini_path.parent / definition['filename']
                    key = (str(ini_path.resolve()), str(buf_path.resolve()))
                    if key in seen:
                        continue
                    seen.add(key)
                    items.append({
                        'ini': ini_path,
                        'ini_text': text,
                        'target': target_entry,
                        'section': title,
                        'resource': definition['section'],
                        'buf': buf_path,
                        'stride': definition['stride'],
                        'stride_span': definition['stride_span'],
                    })

    planned = []
    skipped = 0
    for item in items:
        buf = item['buf']
        label = '{} / 节[{}]'.format(item['target']['name'], item['section'])

        if not buf.exists():
            print('- [格式] {}  "{}"  {}'.format(label, buf, c('文件不存在，跳过', Style.YELLOW)))
            skipped += 1
            continue
        if item['stride'] is None:
            print('- [格式] {}  "{}"  {}'.format(label, buf, c('资源节里没有 stride 行，跳过', Style.YELLOW)))
            skipped += 1
            continue
        state = find_backup_like(buf)
        if state:
            print('- [格式] {}  "{}"  {}'.format(
                label, buf, c('已处理过({})，跳过'.format(state), Style.YELLOW)))
            skipped += 1
            continue

        old_format, new_format = target_formats(item['target'])
        from_dump = bool(item['target'].get('from_dump'))
        if from_dump and not old_format:
            # dump 来的条目没写旧格式，等下按 buf 实际大小倒推
            new_format = tuple(item['target']['new_format'])
        old_stride = fmt_stride(old_format) if old_format else None
        new_stride = fmt_stride(new_format)
        size = buf.stat().st_size

        # 顶点数：先按 blend_hash 找 blend 节（不依赖命名），再按同名文件推，
        # 最后按 buf 大小直接判（只有一边能整除时不用知道顶点数）
        count, from_what = vertex_count_by_hash(item['ini'], item['ini_text'],
                                                item['target'].get('blend_hash'))
        if count:
            from_what = 'blend hash，{}'.format(from_what)
        else:
            count, from_what = vertex_count_of(buf)
            if count:
                from_what = '同名文件，{}'.format(from_what)
            else:
                # 文件名不可靠（UUID.assets 这种）：按 ini 资源组里同组的 blend 推
                count, from_what = ini_group_vertex_count(buf)
            if not count and old_format:
                if size % old_stride == 0 and size % new_stride != 0:
                    count, from_what = size // old_stride, '按 buf 大小'
                elif size % new_stride == 0 and size % old_stride != 0:
                    count, from_what = size // new_stride, '按 buf 大小'

        if not count:
            print('- [格式] {}  "{}"  {}'.format(
                label, buf, c('算不出顶点数，也判断不出格式，跳过', Style.YELLOW)))
            skipped += 1
            continue

        # 能整除就用整数，免得浮点比较出偏差
        per_vertex = size // count if size % count == 0 else size / count

        inferred = None            # 旧格式是推出来的（元素个数没变那条路，取最靠前的）
        element_map = item['target'].get('element_map') or None
        layout_note = None         # 元素个数变了时的说明（打给用户看）
        layout_reason = None       # 推不出时的原因（也打给用户看）
        hash_key = str(item['target'].get('hash', '')).lower()
        info = DUMP_MESHES.get(hash_key)

        if from_dump and not old_format:
            if per_vertex == new_stride:
                print('- [格式] {}  "{}"  {}'.format(
                    label, buf, c('已是新格式({})，跳过'.format(new_stride), Style.YELLOW)))
                skipped += 1
                continue
            got = infer_layout_from_dump(buf, count, per_vertex, info) if info else None
            if not got or not got.get('ok'):
                print('- [格式] {}  "{}"  {}'.format(
                    label, buf, c('每顶点 {} 字节，推不出对应的旧格式，跳过'.format(per_vertex), Style.YELLOW)))
                print('        （dump 给的当前格式是 {}）'.format(' + '.join(new_format)))
                if got and got.get('reason'):
                    print(c('        （{}）'.format(got['reason']), Style.YELLOW))
                skipped += 1
                continue
            old_format = got['old_format']
            element_map = got['element_map']
            layout_note = got['note']
            old_stride = fmt_stride(old_format)
            inferred = got.get('multi')
        elif (element_map is None and old_format
                and per_vertex != fmt_stride(old_format) and info):
            # 表里 / 名单里写了旧格式，但 buf 大小对不上 —— 元素个数变过的那种
            # （老 mod 只有 2 条 UV，游戏现在是 4 条）。有 dump 就按 dump 的元素表 + buf 推；
            # 推不出就照旧跳过（下面那条"和表里对不上"的提示 + 原因）
            got = infer_layout_from_dump(buf, count, per_vertex, info)
            if got and got.get('ok'):
                old_format = got['old_format']
                element_map = got['element_map']
                layout_note = got['note']
                old_stride = fmt_stride(old_format)
                inferred = got.get('multi')
            elif got:
                layout_reason = got.get('reason')

        do_buf = (per_vertex == old_stride)
        do_stride = (item['stride'] == old_stride)

        print('- [格式] {}  "{}"'.format(label, buf))
        if item['target'].get('hash_note'):
            print('        认得它：hash {}'.format(c(item['target']['hash_note'], Style.GREEN)))
        print('        格式 {} -> {} 字节/顶点   顶点数 {}（{}）'.format(
            old_stride, new_stride, count, from_what))
        if element_map:
            print(c('        {}'.format(layout_note), Style.GREEN))
            textures = info.get('textures') if info else None
            if textures and len(textures) > 1:
                print(c('        注意：dump 里这个网格绑了 {} 张贴图（{}）—— 补 0 的那几块 UV '
                        '在游戏里是有贴图的，那层细节补不回来'.format(
                            len(textures), '、'.join(textures)), Style.YELLOW))
        elif inferred is not None:
            print('        按 buf 大小倒推：{}  ->  {}'.format(
                ' + '.join(old_format), ' + '.join(new_format)))
            if inferred:
                print(c('        （有多个位置都能凑上，取最靠前的，也就是顶点 COLOR 那块）', Style.YELLOW))
        if do_buf:
            print('        buf {} 字节 -> {} 字节'.format(size, count * new_stride))
        elif per_vertex == new_stride:
            print('        buf 已是新格式，不用转')
        else:
            print('        {}'.format(c('buf 每顶点 {} 字节，和表里的 {} 对不上，跳过'.format(
                per_vertex, old_stride), Style.YELLOW)))
            if layout_reason:
                print(c('        （{}）'.format(layout_reason), Style.YELLOW))
            skipped += 1
            continue
        if do_stride:
            print('        ini 里 stride {} -> {}'.format(old_stride, new_stride))

        if do_buf or do_stride:
            planned.append({
                'buf': buf, 'ini': item['ini'], 'count': count,
                'old_format': old_format, 'new_format': new_format,
                'element_map': element_map,
                'old_stride': old_stride, 'new_stride': new_stride,
                'stride_span': item['stride_span'], 'do_buf': do_buf, 'do_stride': do_stride,
            })

    return planned, skipped, None


def apply_stride_edits(text, edits):
    """按原文偏移从后往前改 stride。

    edits = [(start, end, old_stride, new_stride)]，span 都是基于原始
    ini 文本算的。同一份 ini 有多个 stride 时，从后往前改，前面的偏移
    才不会被顶掉；同 span 的重复项只改一次。
    """
    unique = list(dict.fromkeys(
        (start, end, str(old), str(new)) for start, end, old, new in edits))
    for start, end, old, new in sorted(unique, key=lambda e: e[0], reverse=True):
        if text[start:end] == old:
            text = text[:start] + new + text[end:]
    return text


def tex_apply(planned, total=None, done0=0):
    ini_texts = {}
    ini_backed = set()
    stride_edits = {}

    def load_ini(ini_path: Path):
        key = str(ini_path)
        if key not in ini_texts:
            ini_texts[key] = ini_path.read_text(encoding='utf-8', errors='replace')
        return ini_texts[key]

    def ensure_ini_backup(ini_path: Path):
        key = str(ini_path)
        if key in ini_backed:
            return
        ini_backup = Path(key + TEX_INI_BACKUP_SUFFIX)
        if not ini_backup.exists():
            ini_backup.write_bytes(ini_path.read_bytes())
        ini_backed.add(key)

    for index, item in enumerate(planned, 1):
        buf = item['buf']
        ini_path = item['ini']
        changes = []

        if item['do_buf']:
            original = buf.read_bytes()
            tex_backup_of(buf).write_bytes(original)
            buf.write_bytes(tex_convert(original, item['count'], item['old_format'],
                                        item['new_format'], item.get('element_map')))
            tex_marker_of(buf).write_text('', encoding='utf-8')
            changes.append('buf {} -> {} 字节'.format(len(original), buf.stat().st_size))

        if item['do_stride']:
            load_ini(ini_path)                 # 先缓存原文本，别在这里改
            start, end = item['stride_span']
            stride_edits.setdefault(str(ini_path), []).append(
                (start, end, item['old_stride'], item['new_stride']))
            changes.append('stride {} -> {}'.format(item['old_stride'], item['new_stride']))

        if changes:
            ensure_ini_backup(ini_path)
            print(c('已修 [格式]: "{}"  [{}]'.format(buf.name, ' ； '.join(changes)), Style.GREEN))
        iv_progress(done0 + index, total or len(planned), buf.name)

    for key, text in ini_texts.items():
        edits = stride_edits.get(key)
        if edits:
            text = apply_stride_edits(text, edits)
        Path(key).write_text(text, encoding='utf-8')


# ==========================================================================
#  三、顶点上限（VertexLimitRaise）
#
#  ZZMI 导出的 mod，一个网格一节：
#      [TextureOverrideXXX_40_32695_VertexLimitRaise]
#      hash = bea2b94e
#      override_vertex_count = 32695
#      override_byte_stride = 40
#  游戏靠这个数把顶点缓冲的上限抬上去。数填错 / 没填 / stride 还是旧写法（92/96/76），
#  进游戏就是模型炸开、顶点缓冲溢出、顶点被拉到天上。
#
#  这一项只动 ini —— 改前备份成 .texfmt.bak，跟"顶点格式"那项共用同一个还原。
# ==========================================================================

LIMIT_TITLE_RE = re.compile(r'VertexLimitRaise$', re.IGNORECASE)
LIMIT_MESH_RE = re.compile(r'^(.*?)_\d+_\d+_VertexLimitRaise$', re.IGNORECASE)
LEGACY_STRIDES = ('92', '96', '76')     # 旧版把三份缓冲写成一整条时的步幅
LIMIT_BIG_MESH = 25000                  # 顶点数超过这个又没写上限定数的，得补
LIMIT_FALLBACK_COUNT = 35000
DRAW_LINE_RE = re.compile(r'(?mi)^[ \t]*draw[ \t]*=[ \t]*(\d+)')
LIMIT_VC_LINE_RE = re.compile(r'(?mi)^([ \t]*)override_vertex_count[ \t]*=[ \t]*(\d*)[ \t]*$')
LIMIT_BS_LINE_RE = re.compile(r'(?mi)^([ \t]*)override_byte_stride[ \t]*=[ \t]*(\d*)[ \t]*$')


def _limit_mesh_of_title(title: str) -> str:
    """VertexLimitRaise 节标题里的网格名（去掉 TextureOverride / 数字 / 后缀）"""
    m = LIMIT_MESH_RE.match(title.strip())
    return (m.group(1) if m else LIMIT_TITLE_RE.sub('', title.strip())).replace(
        'TextureOverride', '').strip('_')


def _limit_buffer_section_of(title: str, mesh: str) -> bool:
    """这个节是不是 mesh 自己的 Position / Blend 缓冲节（精确匹配，不做子串）"""
    low = re.sub(r'\.\d+\s*$', '', title.strip().lower())
    mesh = mesh.strip().lower()
    for prefix in (mesh, 'textureoverride' + mesh):
        # 变体写法：Position2 / Position.0 / 0Dialyn00Position 这种
        if re.fullmatch(re.escape(prefix) + r'\d*(?:position|blend)\d*', low):
            return True
    return False


def _limit_draw_section_of(title: str, mesh: str) -> bool:
    """这个节是不是 mesh 自己的绘制节（允许 A/B/IB/Head 这类单字母/单后缀变体）"""
    low = re.sub(r'\.\d+\s*$', '', title.strip().lower())
    prefix = 'textureoverride' + mesh.strip().lower()
    if not low.startswith(prefix):
        return False
    suffix = low[len(prefix):]
    return bool(re.fullmatch(
        r'(?:[a-z]?\d*|ib|head|position|blend|vertexlimitraise)?', suffix))


def limit_real_count(target: Path, ini_path: Path, text: str, sections, title: str):
    """这一节对应的网格真实有多少顶点 —— 顺着同前缀的 Position 节找 buf 算。

    返回 (顶点数, 出处说明)；算不出来返回 (None, 原因)
    """
    mesh = _limit_mesh_of_title(title)
    if not mesh:
        return None, '节名里没看到网格名'
    best = None
    for t2, s2, e2 in sections:
        body2 = text[s2:e2]
        # 老 mod 的 vb0 在 Position 节；新 mod 没有 Position 节，vb0 藏在 Blend 节的
        # if DRAW_TYPE 块里 —— 两边都要找。只认这个网格自己的节，不能用子串匹配
        # （BelleBody 不能拿 BelleBodyA 的缓冲）。
        if _limit_buffer_section_of(t2, mesh):
            res = re.search(r'(?mi)^[ \t]*vb0[ \t]*=[ \t]*([^\s;]+)', body2)
            if res:
                definition = find_resource_definition(text, res.group(1).strip())
                if definition:
                    path = ini_path.parent / definition['filename']
                    stride = definition.get('stride') or 40
                    if path.exists() and stride and path.stat().st_size % stride == 0:
                        return path.stat().st_size // stride, 'buf {}（{} 字节 / stride {}）'.format(
                            path.name, path.stat().st_size, stride)
        if best is None and _limit_draw_section_of(t2, mesh):
            d = DRAW_LINE_RE.search(body2)
            if d:
                best = int(d.group(1))
    if best:
        return best, '同前缀节的 draw 数（没找到 buf，按 ini 里写的算）'
    return None, '没找到这个网格的 Position 节 / buf'


def limit_plan(target: Path, active_hashes=None):
    """扫 ini 的 VertexLimitRaise 节 -> [(ini, 改法)]（items, skipped, error）

    active_hashes 给了就只处理 hash 命中的节（本次参照组的分量）；
    None = 没选参照，保持原来的全局行为。
    """
    items, skipped = [], []
    active = None if active_hashes is None else {
        str(value).lower() for value in active_hashes if value}
    inis = find_ini_files(target)
    if not inis:
        return [], skipped, '这个文件夹里没找到 .ini'

    for ini_path in inis:
        try:
            text = ini_path.read_text(encoding='utf-8', errors='replace')
        except OSError as exc:
            skipped.append('{}（读不了：{}）'.format(ini_path.name, exc))
            continue
        sections = split_sections(text)
        if not sections:
            continue
        edits, lines = [], []

        for title, start, end in sections:
            body = text[start:end]
            if active is not None:
                hm = HASH_LINE_RE.search(body)
                if not hm or hm.group(1).lower() not in active:
                    continue
            vc = LIMIT_VC_LINE_RE.search(body)
            bs = LIMIT_BS_LINE_RE.search(body)
            is_limit = bool(LIMIT_TITLE_RE.search(title.strip()))

            if not is_limit:
                # 不是上限节，但万一把 stride 写在这儿了，也顺手纠
                if bs and bs.group(2).strip() in LEGACY_STRIDES:
                    edits.append(dict(ini=ini_path, span=(start + bs.start(2), start + bs.end(2)),
                                      text='40', title=title))
                    lines.append('- [上限] "{}"  [{}]  override_byte_stride {} -> 40（旧写法）'.format(
                        ini_path.name, title, bs.group(2).strip()))
                continue

            real, why = limit_real_count(target, ini_path, text, sections, title)
            if real == 0:
                continue          # buf 是 0 字节（拆分工具留下的空壳），没什么好抬的
            # 真实顶点数优先；算不出来就按这个网格自己的 draw，再不行用默认值
            wanted = real if real is not None else LIMIT_FALLBACK_COUNT
            cur_vc = vc.group(2).strip() if vc else None
            cur_bs = bs.group(2).strip() if bs else None
            content = [l for l in body.splitlines()
                       if l.strip() and not l.strip().startswith((';', '#', '['))]
            has_other = any(not l.strip().lower().startswith('hash') for l in content)
            todo, why_lines = [], []

            if cur_vc is None:
                if has_other or (real and real > LIMIT_BIG_MESH):
                    indent = ''
                    anchor = HASH_LINE_RE.search(body)
                    at = start + (anchor.end() if anchor else len(body.rstrip()))
                    edits.append(dict(ini=ini_path, span=(at, at),
                                      text='\n{}override_vertex_count = {}'.format(indent, wanted),
                                      title=title))
                    todo.append('补 override_vertex_count = {}'.format(wanted))
                    why_lines.append('这一节没写上限定数（{}）'.format(
                        why if real is not None else 'buf 数没算出来，按默认值'))
            elif cur_vc in ('', '0'):
                edits.append(dict(ini=ini_path, span=(start + vc.start(2), start + vc.end(2)),
                                  text=str(wanted), title=title))
                todo.append('override_vertex_count {} -> {}'.format(cur_vc or '空', wanted))
                why_lines.append(why)
            elif real is not None and int(cur_vc) != real:
                edits.append(dict(ini=ini_path, span=(start + vc.start(2), start + vc.end(2)),
                                  text=str(real), title=title))
                todo.append('override_vertex_count {} -> {}'.format(cur_vc, real))
                why_lines.append(why + '（跟 ini 里写的对不上）')

            if cur_bs is None and todo:
                anchor = HASH_LINE_RE.search(body)
                at = start + (anchor.end() if anchor else len(body.rstrip()))
                edits.append(dict(ini=ini_path, span=(at, at),
                                  text='\noverride_byte_stride = 40', title=title))
                todo.append('补 override_byte_stride = 40')
            elif cur_bs in LEGACY_STRIDES:
                edits.append(dict(ini=ini_path, span=(start + bs.start(2), start + bs.end(2)),
                                  text='40', title=title))
                todo.append('override_byte_stride {} -> 40（旧写法）'.format(cur_bs))

            if todo:
                lines.append('- [上限] "{}"  [{}]'.format(ini_path.name, title))
                for t in todo:
                    lines.append('        {}'.format(t))
                for w in dict.fromkeys(why_lines):
                    lines.append('        （{}）'.format(w))

        if edits:
            # 同一份 ini 里的多处改动：按位置从后往前改，前面的偏移才不会被顶掉
            edits.sort(key=lambda e: e['span'][0], reverse=True)
            items.append(dict(ini=ini_path, edits=edits, lines=lines))

    error = None
    return items, skipped, error


def limit_apply(planned, total=None, done0=0):
    ini_texts = {}
    ini_backed = set()

    for index, item in enumerate(planned, 1):
        ini_path = item['ini']
        key = str(ini_path)
        if key not in ini_texts:
            ini_texts[key] = ini_path.read_text(encoding='utf-8', errors='replace')
        if key not in ini_backed:
            ini_backup = Path(key + TEX_INI_BACKUP_SUFFIX)
            if not ini_backup.exists():
                ini_backup.write_bytes(ini_path.read_bytes())
            ini_backed.add(key)

        text = ini_texts[key]
        for edit in item['edits']:                 # 已按位置从后往前排
            s, e = edit['span']
            text = text[:s] + edit['text'] + text[e:]
        ini_texts[key] = text
        print(c('已修 [上限]: "{}"  {} 处'.format(ini_path.name, len(item['edits'])), Style.GREEN))
        iv_progress(done0 + index, total or len(planned), ini_path.name)

    for key, text in ini_texts.items():
        Path(key).write_text(text, encoding='utf-8')


# ==========================================================================
#  四、网格拆分修复（一条老网格 -> 按新版本的分量拆成几件）
#
#  游戏更新常把角色的一条网格拆成好几条分量（铃：上半身 c2b4ce3a / 耳环
#  c2b4ce3a 第二段 / 腿 e6afd8d1）。老 mod 的网格还是旧版的一条，光换 hash
#  也修不出来 —— 得按新分量拆开、每件绑自己的 hash 才认得出、才动得对。
#
#  参照 = 本次选的 dump（新版本各分量）：分量名 / ib hash / 索引段(首个,个数) /
#      draw hash(VertexLimitVB) / position·texcoord·blend 三个 hash /
#      Position.buf / Blend.buf / texcoord 元素表。
#
#  判定：mod 网格的顶点按位置分给最近的参照分量（同一位置多个顶点时用权重挑），
#       三角面按三个顶点的多数票归属。落在 2 个以上分量、且次多的占 10% 以上才拆。
#
#  每件：抽顶点、写自己的 Position/Texcoord/Blend/IB —— 权重行原样搬；骨索引按该
#       分量的表换；texcoord 按目标分量的元素表重排（复用"顶点格式"那套）；
#       ini 里一整节，其中 override_vertex_count = 该件自己的顶点数（缺了会炸开）。
#  目标分量没出件的不动它（游戏照原样画）；该掐的原版分量 / 多余索引段由
#  "五、掐掉多余的那几笔"那一步负责（要 mod 的 ini 里凡是没认的分量才掐）。
#
#  推不出来（配不上 / texcoord 布局推不出 / 骨索引推不出）就整单不写，
#  打印卡在哪 —— 宁可不修，不给半成品。写过的文件记进 split_created.json，
#  "还原"时照它删掉。
# ==========================================================================

SPLIT_SECOND_MIN = 0.10      # 次多分量占该网格三角面的比例，低于这个不拆
SPLIT_PART_MIN = 0.05        # 某分量分到的面不到目标分量面数的这个比例 -> 不出件
SPLIT_FAR = 0.05             # 顶点离所有参照都超过这么多米 -> 没归属
SPLIT_COVER_MIN = 0.30       # 整块网格配上的比例低于这个 -> 不是同一套，拒绝
SPLIT_W_MATCH = 0.25         # 判定归属时"权重像"的门槛（4 个权重绝对差之和）
SPLIT_VC_WARN = 65000        # 单件顶点数超过这个 -> 报告提醒
SPLIT_CREATED = 'split_created.json'    # 新写了哪些文件（还原时照它删）
SPLIT_SHADOW_COVER = 0.80    # 参考分量有这么多顶点跟别的分量重合 = 影子/贴花，不参与分件

# 只有这些参照组需要/允许做网格拆分。后期有新角色要拆，把组名加进来。
# 不在名单里的组，拆分步骤整段跳过（不做分析、不写件、也不跑拆分里的 auto 自检）。
SPLIT_REF_GROUPS = ('铃-原皮', '铃-泳装')


def split_allowed_groups():
    """本次生效的参照组里，允许拆分的那些"""
    return {character_of(info) for info in DUMP_MESHES.values()} & set(SPLIT_REF_GROUPS)


def split_refs(characters=None):
    """本次生效的参照 dump -> 每个分量一条；characters 给了就只收这些组"""
    refs = []
    for tex_hash, info in sorted(DUMP_MESHES.items()):
        if characters is not None and character_of(info) not in characters:
            continue
        if not info.get('position_buf') or not info.get('blend_buf'):
            continue
        pos = load_positions(Path(info['position_buf']))
        blend = load_blend_verts(Path(info['blend_buf']))
        if not pos or not blend or len(pos) != len(blend):
            continue
        refs.append({
            'tex_hash': str(tex_hash).lower(),
            'name': info.get('segment') or info.get('character') or info.get('mesh') or '?',
            'ib_hash': str(info.get('ib_hash') or '').lower(),
            'first': info.get('first_index'), 'count': info.get('index_count'),
            'draw_hash': str(info.get('draw_hash') or '').lower(),
            'pos_hash': str(info.get('position_hash') or '').lower(),
            'tex_vb_hash': str(info.get('texcoord_hash') or tex_hash).lower(),
            'blend_hash': str(info.get('blend_hash') or '').lower(),
            'texcoord_buf': info.get('texcoord_buf'),
            'pos': pos, 'blend': blend, 'info': info,
        })
    return _split_drop_shadow(refs)


def _split_drop_shadow(refs):
    """把"影子 / 贴花"分量从参照里去掉

    游戏里有些分量的位置跟另一个分量几乎重合（头发阴影就贴在头发上），
    留着它分件时会把本该判给主分量的顶点整片吸走。
    判定：它的顶点有 SPLIT_SHADOW_COVER 以上能在 1cm 内找到【顶点更多】的分量的顶点。
    """
    cell = 0.01
    grids = {}
    for r, ref in enumerate(refs):
        grid = {}
        for p in ref['pos']:
            key = (int(floor(p[0] / cell)), int(floor(p[1] / cell)), int(floor(p[2] / cell)))
            grid.setdefault(key, []).append(p)
        grids[r] = grid
    offsets = [(dx, dy, dz) for dx in (-1, 0, 1) for dy in (-1, 0, 1) for dz in (-1, 0, 1)]

    def covered(r, p):
        key = (int(floor(p[0] / cell)), int(floor(p[1] / cell)), int(floor(p[2] / cell)))
        for other, grid in grids.items():
            if other == r or len(refs[other]['pos']) <= len(refs[r]['pos']):
                continue
            for dx, dy, dz in offsets:
                for q in grid.get((key[0] + dx, key[1] + dy, key[2] + dz), ()):
                    if ((q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2 + (q[2] - p[2]) ** 2) <= cell * cell:
                        return True
        return False

    keep = []
    for r, ref in enumerate(refs):
        if len(ref['pos']) < 16:
            continue
        hit = sum(1 for p in ref['pos'] if covered(r, p))
        if hit >= len(ref['pos']) * SPLIT_SHADOW_COVER:
            continue
        keep.append(ref)
    return keep or refs


def split_pick(refs, cell=None):
    """权重先筛、再取最近 -> pick(p, weights) 返回 (参照下标, 距离)

    光看位置不行：长头发会盖在屁股上（位置最近的是头发，权重却完全不像）。
    所以把半径内的候选都算出来，先留下"权重分布跟这个顶点像的"（绝对差之和 <= SPLIT_W_MATCH），
    在这些里面取最近的；一个都不像就退回按最近。

    性能：邻域候选按距离排好，一路扫到"已经找到够像的、后面的都比它远"就停 ——
    并集参照（身体+脸）时邻域里动辄上百个候选，以前每个顶点都要把权重差全算一遍。
    """
    cell = cell or SPLIT_FAR
    grid = {}
    seen_entries = set()           # dump 里同位置同权重的重复顶点只留一条
    for r, ref in enumerate(refs):
        blend = ref['blend']
        for k, p in enumerate(ref['pos']):
            key = (int(floor(p[0] / cell)), int(floor(p[1] / cell)), int(floor(p[2] / cell)))
            rw = blend[k][0]
            entry = (r, rw[0], rw[1], rw[2], rw[3], p[0], p[1], p[2])
            if entry in seen_entries:
                continue
            seen_entries.add(entry)
            # 全摊平存（r, w0..w3, x, y, z）：内层循环少做两次下标查表
            grid.setdefault(key, []).append(entry)
    # 自己的格子先扫：一拿到"最近且像"的候选，远处整格就能按盒子距离跳过
    offsets = [(0, 0, 0)] + [(dx, dy, dz) for dx in (-1, 0, 1)
                             for dy in (-1, 0, 1) for dz in (-1, 0, 1)
                             if (dx, dy, dz) != (0, 0, 0)]
    w_match = SPLIT_W_MATCH
    _abs = abs
    _floor = floor
    _get = grid.get
    _sqrt = lambda v: v ** 0.5

    def pick(p, weights, limit=SPLIT_FAR):
        px, py, pz = p
        key = (int(_floor(px / cell)), int(_floor(py / cell)), int(_floor(pz / cell)))
        limit2 = limit * limit
        w0, w1, w2, w3 = weights
        # 用标量记录，省掉每个候选建 tuple / 比较 tuple
        like_d2 = like_wd = None
        like_r = -1
        any_d2 = any_wd = None
        any_r = -1
        for dx, dy, dz in offsets:
            kx, ky, kz = key[0] + dx, key[1] + dy, key[2] + dz
            items = _get((kx, ky, kz))
            if not items:
                continue
            if like_d2 is not None:
                # 这个格子离 p 的最近距离都已经超过已找到的 best_like -> 整格跳过
                bx, by, bz = kx * cell, ky * cell, kz * cell
                ddx = (bx - px) if px < bx else ((px - (bx + cell)) if px > bx + cell else 0.0)
                ddy = (by - py) if py < by else ((py - (by + cell)) if py > by + cell else 0.0)
                ddz = (bz - pz) if pz < bz else ((pz - (bz + cell)) if pz > bz + cell else 0.0)
                if ddx * ddx + ddy * ddy + ddz * ddz > like_d2:
                    continue
            for r, rw0, rw1, rw2, rw3, qx, qy, qz in items:
                ax = qx - px
                ay = qy - py
                az = qz - pz
                d2 = ax * ax + ay * ay + az * az
                if d2 > limit2:
                    continue
                if like_d2 is not None and d2 > like_d2:
                    continue              # 比已找到的"最近且像"还远，没必要算权重差
                wd = (_abs(w0 - rw0) + _abs(w1 - rw1)
                      + _abs(w2 - rw2) + _abs(w3 - rw3))
                if (any_d2 is None or d2 < any_d2
                        or (d2 == any_d2 and (wd < any_wd
                                              or (wd == any_wd and r < any_r)))):
                    any_d2, any_wd, any_r = d2, wd, r
                if wd <= w_match and (like_d2 is None or d2 < like_d2
                                      or (d2 == like_d2 and (wd < like_wd
                                                             or (wd == like_wd and r < like_r)))):
                    like_d2, like_wd, like_r = d2, wd, r
        if like_d2 is not None:
            return like_r, _sqrt(like_d2)
        if any_d2 is not None:
            return any_r, _sqrt(any_d2)
        return -1, limit

    return pick


def split_nearest(refs, cell=None):
    """参照分量的顶点建个位置格子 -> nearest(p) 返回 (参照下标, 距离)，找不到返回 (-1, limit)"""
    cell = cell or SPLIT_FAR
    grid = {}
    for r, ref in enumerate(refs):
        for k, p in enumerate(ref['pos']):
            key = (int(floor(p[0] / cell)), int(floor(p[1] / cell)), int(floor(p[2] / cell)))
            grid.setdefault(key, []).append((r, k, p))
    offsets = [(dx, dy, dz) for dx in (-1, 0, 1) for dy in (-1, 0, 1) for dz in (-1, 0, 1)]

    def nearest(p, limit=SPLIT_FAR):
        key = (int(floor(p[0] / cell)), int(floor(p[1] / cell)), int(floor(p[2] / cell)))
        best_r, best_d2 = -1, limit * limit
        for dx, dy, dz in offsets:
            items = grid.get((key[0] + dx, key[1] + dy, key[2] + dz))
            if not items:
                continue
            for r, _k, q in items:
                d2 = (q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2 + (q[2] - p[2]) ** 2
                if d2 < best_d2:
                    best_r, best_d2 = r, d2
        return best_r, (best_d2 ** 0.5 if best_r >= 0 else limit)

    return nearest


def split_tex_prefix(new_format, per_vertex: int):
    """老布局是不是正好等于新布局的前几块（缺的块补 0）—— 是就返回块表，不是返回 None

    自定义 UV 的 mod（值域跟游戏对不上）走这条：derive_element_layout 那套按值域核对
    会推不出来，但"老的就少后面几块"这种情况是确定的。
    """
    chunks, total = [], 0
    for chunk in new_format:
        size = fmt_stride((chunk,))
        if total + size > per_vertex:
            return None
        chunks.append(chunk)
        total += size
        if total == per_vertex:
            return tuple(chunks)
    return None


def split_mesh_files(blend_path: Path, ini_path: Path, text: str, ib_hash: str):
    """一个网格的四个文件：Position / Texcoord / Blend / 索引"""
    stem = blend_path.name[:-4]
    base = stem[:-5] if stem.lower().endswith('blend') else stem
    found = {'blend': blend_path}
    for key, suffix in (('position', 'Position'), ('texcoord', 'Texcoord')):
        for name in (base + suffix + '.buf', base + suffix.lower() + '.buf'):
            cand = blend_path.with_name(name)
            if cand.exists():
                found[key] = cand
                break
    for name in (base + 'Head.ib', base + '.ib', base + 'Index.ib',
                 base.lower() + '.ib', base + 'head.ib'):
        cand = blend_path.with_name(name)
        if cand.exists():
            found['ib'] = cand
            break
    if 'ib' not in found:
        # 老 mod 的索引文件名很随便（LingHairA.ib 这种）：按网格名前缀找一遍
        for cand in sorted(blend_path.parent.glob(base + '*.ib')):
            found['ib'] = cand
            break
        if 'ib' not in found:
            for cand in sorted(blend_path.parent.glob(base.lower() + '*.ib')):
                found['ib'] = cand
                break
    if 'ib' not in found and ib_hash:
        # 同 hash 的节可能不止一个（IB 跳过节、绘制节都写 hash）：逐个找带 ib= 的
        for title, start, end in split_sections(text):
            body = text[start:end]
            m = HASH_LINE_RE.search(body)
            if not m or m.group(1).lower() != str(ib_hash).lower():
                continue
            match = re.search(r'(?mi)^[ \t]*ib[ \t]*=[ \t]*(.+?)[ \t]*$', body)
            if not match:
                continue
            definition = find_resource_definition(text, match.group(1).strip())
            cand = (ini_path.parent / definition['filename']) if definition else None
            if cand and cand.exists():
                found['ib'] = cand
                break
    if not {'position', 'texcoord', 'ib'} <= set(found):
        # 文件名不可靠（UUID.assets / 乱起名）：按 ini 资源组补齐
        group = ini_buffer_group_of(blend_path)
        if group:
            for kind in ('position', 'texcoord', 'ib', 'blend'):
                if kind not in found and group.get(kind):
                    found[kind] = group[kind]['path']
    if {'position', 'texcoord', 'ib'} <= set(found):
        return found
    return None


def split_read_ib(path: Path):
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if not data or len(data) % 4:
        return None
    flat = array('I')
    flat.frombytes(data)
    if sys.byteorder != 'little':
        flat.byteswap()
    return list(flat)


def split_mesh_resources(ini_text: str, files):
    """这条网格自己的资源名（按资源定义里的 filename 指向哪个文件来认）

    节名可以乱起（`[TextureOverride_IB_25.3.7Ling_下半身_Component1]` 里根本没有
    网格名），但资源定义跑不掉：`[Resourcebea4a483Position]` 的
    `filename = Buffer/bea4a483-Position.buf` 指的就是这条网格的 Buffer 文件。
    """
    names = set()
    if not files:
        return names
    want = set()
    for key in ('position', 'texcoord', 'blend', 'ib'):
        path = files.get(key) if isinstance(files, dict) else None
        if path:
            want.add(Path(str(path)).name.lower())
    if not want:
        return names
    for title, start, end in split_sections(ini_text):
        head = title.strip().lower()
        if not head.startswith('resource'):
            continue
        match = re.search(r'(?im)^\s*filename\s*=\s*([^\s;]+)', ini_text[start:end])
        if not match:
            continue
        base = match.group(1).replace('\\', '/').rsplit('/', 1)[-1].lower()
        if base in want:
            names.add(head)
    return names


def split_mesh_resource_map(ini_text, files):
    """按资源定义里的 filename 反查这条网格各类资源名

    返回 {'position': {...}, 'texcoord': {...}, 'blend': {...}, 'ib': {...}}。
    认"绘制节"就靠它：`ib = Resource_bea4a483_Component1` 里的资源名对得上这条
    网格的 IB 文件，那一节才是这个网格真正用来画的那一节。
    """
    result = {}
    if not files:
        return result
    want = {}
    for key in ('position', 'texcoord', 'blend', 'ib'):
        path = files.get(key) if isinstance(files, dict) else None
        if path:
            want[Path(str(path)).name.lower()] = key
    if not want:
        return result
    for title, start, end in split_sections(ini_text):
        head = title.strip().lower()
        if not head.startswith('resource'):
            continue
        match = re.search(r'(?im)^\s*filename\s*=\s*([^\s;]+)', ini_text[start:end])
        if not match:
            continue
        base = match.group(1).replace('\\', '/').rsplit('/', 1)[-1].lower()
        key = want.get(base)
        if key:
            result.setdefault(key, set()).add(head)
    return result


def _buffer_kind(name, stride, fmt):
    """资源名 + stride/format -> position / texcoord / blend / ib（扩展名无关）"""
    low = name.lower()
    for suffix, kind in (('position', 'position'), ('texcoord', 'texcoord'),
                         ('blend', 'blend'), ('component', 'ib'), ('index', 'ib'),
                         ('head', 'ib'), ('aib', 'ib'), ('ib', 'ib')):
        if low.endswith(suffix):
            if kind != 'ib' or not stride:
                return kind
    if fmt and 'uint' in fmt.lower() and not stride:
        return 'ib'
    if stride == 40:
        return 'position'
    if stride == 32:
        return 'blend'
    if stride:
        return 'texcoord'
    return None


def _buffer_group_key(name):
    low = name.lower()
    for suffix in ('position', 'texcoord', 'blend', 'component', 'index',
                   'head', 'aib', 'ib'):
        if low.endswith(suffix):
            low = low[:-len(suffix)]
            break
    low = re.sub(r'\d+$', '', low)
    return re.sub(r'[^0-9a-z]', '', low)


def ini_resource_groups(ini_path, ini_text):
    """按资源名把 ini 里的 buffer 资源分组（不看扩展名：.buf/.assets/.bin 都认）

    返回 [{'ini': Path, 'name': key, 'position': {...}, 'texcoord': {...}, ...}]，
    每项 {'path', 'stride', 'format', 'name'}。用于：
      - 顶点格式：推顶点数（同组的 blend/position 大小）
      - 掐笔：找 mod 的 Position 缓冲
      - 拆分：找网格的四个文件（UUID.assets 这种命名也能认）
    """
    groups = {}
    for title, start, end in split_sections(ini_text):
        head = title.strip()
        if not head.lower().startswith('resource'):
            continue
        body = ini_text[start:end]
        filename = re.search(r'(?im)^\s*filename\s*=\s*([^\s;]+)', body)
        if not filename:
            continue
        stride_match = re.search(r'(?im)^\s*stride\s*=\s*(\d+)', body)
        format_match = re.search(r'(?im)^\s*format\s*=\s*(\S+)', body)
        stride = int(stride_match.group(1)) if stride_match else None
        fmt = format_match.group(1) if format_match else ''
        kind = _buffer_kind(head, stride, fmt)
        if kind is None:
            continue
        path = (ini_path.parent / filename.group(1).replace('\\', '/')).resolve()
        if not path.exists():
            continue
        key = _buffer_group_key(head)
        group = groups.setdefault(key, {'ini': ini_path, 'name': key})
        group.setdefault(kind, {'path': path, 'stride': stride,
                                'format': fmt, 'name': head})
    # 合并：ib 资源名常和位置组差一截（ResourceXComponent1 / ResourceX）
    for key in list(groups):
        group = groups.get(key)
        if not group:
            continue
        if any(name in group for name in ('position', 'blend', 'texcoord')):
            continue
        candidates = [other for other in groups
                      if other and other != key and key.startswith(other)
                      and any(name in groups[other] for name in ('position', 'blend'))]
        if not candidates:
            continue
        target = groups[max(candidates, key=len)]
        for name, value in group.items():
            if name not in ('ini', 'name'):
                target.setdefault(name, value)
        del groups[key]
    return [group for group in groups.values()
            if 'position' in group or 'blend' in group]


_INI_RESOURCE_GROUP_CACHE = {}


def ini_resource_groups_cached(ini_path, text=None):
    """按 ini 的 mtime/size 缓存资源组，避免每 buf 重扫重解析同一份 ini。"""
    ini_path = Path(ini_path)
    key = str(ini_path)
    try:
        stat = ini_path.stat()
        stamp = (stat.st_mtime_ns, stat.st_size)
    except OSError:
        return []
    cached = _INI_RESOURCE_GROUP_CACHE.get(key)
    if cached and cached[0] == stamp:
        return cached[1]
    if text is None:
        try:
            text = ini_path.read_text(encoding='utf-8', errors='replace')
        except OSError:
            return []
    groups = ini_resource_groups(ini_path, text)
    _INI_RESOURCE_GROUP_CACHE[key] = (stamp, groups)
    return groups


def ini_buffer_group_of(path: Path):
    """给一个 buffer 文件，找它所在的 ini 资源组（同组的 blend/position 可互推顶点数）"""
    try:
        target = path.resolve()
    except OSError:
        return None
    # buffer 常在 Buffer\ 子目录，ini 在上一层（偶像打歌服 这种）；
    # 先找同目录，再找上一级
    folders = [path.parent]
    if path.parent.parent != path.parent:
        folders.append(path.parent.parent)
    seen = set()
    for folder in folders:
        for ini_path in find_ini_files(folder):
            key = str(ini_path)
            if key in seen:
                continue
            seen.add(key)
            for group in ini_resource_groups_cached(ini_path):
                for kind, item in group.items():
                    if kind in ('ini', 'name'):
                        continue
                    if item['path'] == target:
                        return group
    return None


def ini_group_vertex_count(buf_path: Path):
    """同资源组的 blend/position 反推顶点数 -> (顶点数, 来源说明) 或 (None, None)"""
    group = ini_buffer_group_of(buf_path)
    if not group:
        return None, None
    for kind, stride in (('blend', 32), ('position', 40)):
        item = group.get(kind)
        if not item or (item.get('stride') not in (None, stride)):
            continue
        size = item['path'].stat().st_size
        if size % stride == 0:
            return size // stride, '同资源组 {}'.format(item['path'].name)
    return None, None


def split_find_commandlist(ini_text, name):
    """按 CommandList 名找节（大小写不敏感；也认只写末段的引用）"""
    want = name.strip().lower()
    tail = want.replace('\\', '/').rsplit('/', 1)[-1]
    for title, start, end in split_sections(ini_text):
        low = title.strip().lower()
        if low == want or low == tail or low.endswith('\\' + tail):
            return ini_text[start:end]
    return None


def split_inline_commandlists(ini_text, lines, depth=0, seen=None, notes=None,
                              limit=3):
    """把绘制节里的 `run = CommandList_xxx` 换成那个 CommandList 的内容

    已验证产物就是这么做的（注释里写 INLINED）。有些 mod
    （嗨丝逆兎）把分段 drawindexed 全放在 CommandList 里，节里只有一句 run ——
    不内联就看不到任何分段，件只能一笔画整件，鞋子/兔耳这些开关全失效。

    SkinTexture / SetTextures 这类必须留在件里当 run，不能内联；
    找不到对应节的行直接丢掉并记一条笔记 —— 留着会在件里把老网格整条重画。
    """
    if seen is None:
        seen = set()
    out = []
    for raw in lines:
        s = raw.strip()
        match = re.match(r'(?i)^run\s*=\s*(\S+)\s*$', s)
        if not match or depth >= limit:
            out.append(raw)
            continue
        name = match.group(1)
        low = name.lower()
        # 只内联真正的 CommandList；`run = CustomShaderTransparencyStocking` 这种是
        # CustomShader（自带 blend + drawindexed），内联进来会在件里再画一遍、
        # 还丢掉着色器切换 —— 原样留着
        if not low.startswith('commandlist'):
            out.append(raw)
            continue
        if 'skin' in low or 'settextures' in low:
            out.append(raw)
            continue
        body = split_find_commandlist(ini_text, name)
        if body is None:
            # 外部 CommandList（定义在别的 mod/ini 里，比如外部 mod）：
            # 照克隆的规矩保留原 run 行，别丢 —— 不然发光/着色效果就没了
            if notes is not None:
                notes.append('CommandList "{}" 没找到，保留原 run 行'.format(name))
            out.append(raw)
            continue
        if low in seen:
            continue
        seen.add(low)
        inner = [line for line in body.splitlines()
                 if not line.strip().startswith('[')]
        out.extend(split_inline_commandlists(ini_text, inner, depth + 1, seen,
                                             notes, limit))
    return out


def split_required_texture_binds(ini_text, body):
    """原绘制节里"必须出现在件里"的贴图绑定行（内联 CommandList 之后）。

    用于写盘前自检：ps-tN / Resource\\ZZMI\\… / run = CommandList\\ZZMI\\SetTextures
    这些是贴图绑定；件里少任何一类，进游戏就是颜色错/原版贴图。
    返回规范化后的行集合（小写、单空格）。
    """
    if not body:
        return set()
    lines = [line.rstrip() for line in body.splitlines()
             if not line.strip().startswith('[')]
    lines = split_inline_commandlists(ini_text, lines)
    required = set()
    for line in lines:
        text = ' '.join(line.split())
        low = text.lower()
        if re.match(r'(?i)^ps-t\d+\s*=', text):
            required.add(low)
        elif re.match(r'(?i)^resource\s*\\\s*zzmi\s*\\', text):
            required.add(low)
        elif low.startswith('run = ') and 'settextures' in low:
            required.add(low)
    return required


def split_filter_texture_lines(lines):
    """从内联出来的 CommandList 里只留 ps-tN / checktextureoverride，保留 if/else 分支

    GIMI 合并版 mod（彼岸浮华）把贴图绑定整段放在 `run = CommandListxxxHead` 里：
    不内联的话件里一个 ps 都不绑，游戏就用原版贴图 —— 头发/腿颜色全错。
    drawindexed / ib 不能带进来（会把老网格再画一遍），所以只挑这两类行；
    分支里没有任何保留行的整个 if/endif 组丢掉（空 if 会让 3dmigoto 截断整节）。
    """
    def parse(region, index):
        out = []
        while index < len(region):
            raw = region[index]
            text = raw.strip()
            low = text.lower()
            if low.startswith('endif') or low.startswith(('else if ', 'elseif ',
                                                          'elif ', 'else')):
                return out, index
            if low.startswith('if ') or low.startswith('if('):
                parts = []                 # [(条件行, 行列表), ...]
                cond = text
                index += 1
                body, index = parse(region, index)
                parts.append((cond, body))
                while index < len(region):
                    t = region[index].strip()
                    tl = t.lower()
                    if tl.startswith(('else if ', 'elseif ', 'elif ', 'else')):
                        cond = t
                        index += 1
                        body, index = parse(region, index)
                        parts.append((cond, body))
                        continue
                    if tl.startswith('endif'):
                        index += 1
                    break
                kept = [(c, b) for c, b in parts if b]
                if kept:
                    for c, b in kept:
                        out.append(c)
                        out.extend(b)
                    out.append('endif')
                continue
            if (re.match(r'(?i)^\s*(ps-t\d+|checktextureoverride)\s*=', raw)
                    or re.match(r'(?i)^\s*resource\s*\\\s*zzmi\s*\\', raw)
                    or ('settextures' in low and re.match(r'(?i)^\s*run\s*=', raw))):
                # ZZMI 的写法 `Resource\ZZMI\Diffuse = ref Resource_…` +
                # `run = CommandList\ZZMI\SetTextures` 也是贴图绑定，别只认 ps-tN
                out.append(text)
            index += 1
        return out, index

    result, _ = parse(list(lines), 0)
    return result


def split_find_draw_section(ini_text, files, res_map, mesh_tag, mesh_hashes):
    """这条网格真正用来画的那一节 —— 只挑一个，返回 (标题, 节文本) 或 None

    以前是按网格名把许多节的行拼起来：铃-内内裤袜 把 12 款换色的贴图节也拼进件，
    件里的 elif 没配对，3dmigoto 把整节剩下的命令全丢掉，身体就拉丝/豁口。
    已验证写法是只克隆"这一个绘制节"：ib 指向这条网格的 IB 资源，或者
    hash 是这个网格的 IB hash 且节里有绘制/贴图绑定。按分数挑最高的一个，平手取靠前的。
    """
    ib_names = set(res_map.get('ib') or ())
    all_names = set()
    for values in res_map.values():
        all_names |= values
    mesh_hashes = {str(value).lower() for value in (mesh_hashes or ()) if value}
    best, best_score = None, 0
    for title, start, end in split_sections(ini_text):
        head = title.strip().lower()
        if not head.startswith('textureoverride'):
            continue
        body = ini_text[start:end]
        low = body.lower()
        score = 0
        has_ib_res = False
        for line in body.splitlines():
            match = re.match(r'(?i)^ib\s*=\s*(\S+)\s*$', line.strip())
            if match and match.group(1).lower() in ib_names:
                has_ib_res = True
                break
        if has_ib_res:
            score += 100
        hashes = {match.group(1).lower()
                  for match in re.finditer(r'(?im)^\s*hash\s*=\s*(\w+)', body)}
        if hashes & mesh_hashes:
            score += 40
        if any(name in (head + low) for name in all_names):
            score += 20
        if mesh_tag and mesh_tag in (head + low):
            score += 10
        if re.search(r'(?im)^\s*drawindexed\s*=\s*\d', body):
            score += 30
        if re.search(r'(?im)^\s*run\s*=\s*commandlist', body):
            score += 15
        # 真正的绘制节：run 的 CommandList 里有 drawindexed / 贴图绑定。
        # GIMI 合并版（彼岸浮华）的 IB 节和 Head 节都只有一句 run，光看节本身
        # 分不出来 —— IB 那节里是 handling=skip，Head 那节里才是 drawindexed+ps。
        for _run in re.finditer(r'(?im)^\s*run\s*=\s*(\S+)\s*$', body):
            _cl = split_find_commandlist(ini_text, _run.group(1))
            if not _cl:
                continue
            # 数字分段才是真绘制；只有 drawindexed = auto 的多半是"掐原版"的 IB 节
            if re.search(r'(?im)^\s*drawindexed\s*=\s*\d', _cl):
                score += 30
            elif re.search(r'(?im)^\s*drawindexed\s*=', _cl):
                score += 5
            # 会换 ib 的才是件的模板（IB 跳过节只有 handling=skip + auto）
            if re.search(r'(?im)^\s*ib\s*=\s*resource', _cl):
                score += 25
            if re.search(r'(?im)^\s*ps-t\d+\s*=', _cl):
                score += 20
        if 'checktextureoverride' in low or 'resource\\zzmi\\' in low:
            score += 15
        if score > best_score:
            best, best_score = (title.strip(), body), score
    # 分数太低说明没一个是"带 ib/hash 的绘制节"—— 宁可交回老办法兜底，
    # 也别挑一个只设缓冲的 VB 节当模板
    if best_score < 40:
        return None
    return best


def split_section_lines(ini_text: str, mesh_name: str, files=None, hashes=None):
    """这个网格在 ini 里的旧节标题（要注释掉的那些）

    认节优先看【资源名】：节里引用本网格的 Buffer 资源（`ib = Resource_…`、
    `vb0 = Resource…` 这种）就算。节名可以乱起 —— 嗨丝逆兎 用
    `[TextureOverride_IB_25.3.7Ling_下半身_Component1]` 画老网格，标题里没有网格名，
    只有节里 `ib = Resource_bea4a483_Component1` 提到。不注释掉：拆完老网格还照原样
    画一遍，骨号又换过 —— 头发炸成一团。网格名/节名只当兜底。
    """
    names = []
    tag = mesh_name.lower()
    res_names = split_mesh_resources(ini_text, files)
    hashes = {str(value).lower() for value in (hashes or ()) if value}
    for title, start, end in split_sections(ini_text):
        head = title.strip().lower()
        body = ini_text[start:end]
        # 只在"有效行"里找名字：注释里常写别的网格名（`; bea4a483 ----` 这种），
        # 拿注释匹配会把别的网格的节也注释掉
        low_body = chr(10).join(line for line in body.splitlines()
                                if not line.strip().startswith((';', '#'))).lower()
        body_hashes = {m.group(1).lower()
                       for m in re.finditer(r'(?im)^\s*hash\s*=\s*(\w+)', body)}
        ours = (tag in head or tag in low_body
                or any(res in head or res in low_body for res in res_names)
                or bool(hashes & body_hashes))
        if not ours:
            continue
        # 资源定义（[ResourceLingHairAIB] 这种）绝对不能注释掉：还引用它的节会
        # 在游戏里报"资源找不到"（红字）。老 mod 那些节注释了，资源定义留着没坏处
        if head.startswith('resource'):
            continue
        # CommandList 节也别注释：已验证写法就是保留的。它只有被 run 才执行，
        # 放着不碍事；注释掉还可能连带影响仍引用它的别的节。
        if head.startswith('commandlist'):
            continue
        if (head.endswith('position') or head.endswith('texcoord') or head.endswith('blend')
                or head.endswith('ib') or head.endswith('head') or head.endswith('vertexlimitraise')):
            names.append(title.strip())
            continue
        # 还有种节叫 [TextureOverride<网格名>A] —— 拿原 IB 画整条老网格的就是它
        # （`ib = null` 的掐笔节不算：那是原版分量的抑制节，跟这条网格的拆分无关）
        draw_like = any(re.match(r'(?i)^\s*(drawindexed|draw)\s*=', line)
                        or (re.match(r'(?i)^\s*ib\s*=', line) and 'null' not in line.lower())
                        for line in body.splitlines())
        if not draw_like:
            # 绘制藏在 run = CommandList 里（GIMI 合并版）：CL 里换 ib / 有 drawindexed
            # 也说明这节在画这条网格，拆完必须注释掉，否则跟件的显式绘制重叠 → 炸
            for _run in re.finditer(r'(?im)^\s*run\s*=\s*(\S+)\s*$', body):
                _cl = split_find_commandlist(ini_text, _run.group(1))
                if not _cl:
                    continue
                if (re.search(r'(?im)^\s*drawindexed\s*=', _cl)
                        or re.search(r'(?im)^\s*ib\s*=\s*resource', _cl)):
                    draw_like = True
                    break
        if draw_like:
            names.append(title.strip())
    return names


SPLIT_PIECE_COVER = 0.30    # 面数够不上 10% 的小件：盖住那个分量这么多也算数（耳坠那种）
SPLIT_EARRING_ISLAND_MAX = 1000  # 骨号 27~30 的连通块，最多这么多顶点才整块判耳坠
SPLIT_GATE_MIN_RATIO = 0.50   # "次多分量很小但要拆"的门槛：件顶点数 ≥ 分量的这么多
SPLIT_PIECE_MIN_RATIO = 0.20  # 小件的顶点数至少要占该参照分量顶点数的这么多
                              # （铃-制服米塔阴影修复：头发网格里 22 个贴脸阴影顶点
                              #   "盖住" 31% 的脸 → 被当成脸件，hash=9a9780a7 的绘制节
                              #   把游戏的脸那一笔顶掉 → 没脸。22/2776=0.8%，不是件，是贴片）
# 骨索引不再跟 dump 校：每件套【它那个分量的表】一次（跟已验证产物一致）。
# 照 dump 改出来的那份进游戏腿会没 —— 见 今日进度 里 2026-10-16 那两条。


def vgx_table_for(ref):
    """这个分量的骨索引表（VGX_CHARACTERS 里按 position / texcoord / blend / draw / ib hash 认）"""
    hits = {str(ref.get(key) or '').lower()
            for key in ('pos_hash', 'tex_vb_hash', 'blend_hash', 'draw_hash', 'ib_hash')}
    hits.discard('')
    if not hits:
        return None
    for entry in VGX_CHARACTERS:
        if hits & {str(value).lower() for value in entry.get('hashes', [])}:
            return {'name': entry.get('name') or '表',
                    'table': dict(zip(entry['old'], entry['new']))}
    return None


def split_dominant_map(src_rows, src_pos, ref, radius=None):
    """没表的分量：按位置配对、**只看主骨**投票 -> ({旧主骨: 新主骨}, 配对率)

    不比权重 —— 老 mod 的耳坠是"权重 1.0 一骨到底"，游戏那边同一位置是混权
    （0.59/0.33/0.08），按权重对齐一颗票都收不到，表就缺条目。
    """
    ref_pos = ref.get('pos') or []
    ref_blend = ref.get('blend') or []
    if not ref_pos or not ref_blend or not src_pos:
        return {}, 0.0
    radius = radius or VGX_RADIUS
    inv = 1.0 / radius
    grid = {}
    for index, p in enumerate(ref_pos):
        grid.setdefault((int(floor(p[0] * inv)), int(floor(p[1] * inv)),
                         int(floor(p[2] * inv))), []).append(index)
    top = lambda w: max(range(4), key=lambda slot: w[slot])
    votes, hit = {}, 0
    for k, p in enumerate(src_pos):
        key = (int(floor(p[0] * inv)), int(floor(p[1] * inv)), int(floor(p[2] * inv)))
        best, best_d2 = -1, radius * radius
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for index in grid.get((key[0] + dx, key[1] + dy, key[2] + dz), ()):
                        q = ref_pos[index]
                        d2 = (q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2 + (q[2] - p[2]) ** 2
                        if d2 <= best_d2:
                            best, best_d2 = index, d2
        if best < 0:
            continue
        w, b = src_rows[k]
        dw, db = ref_blend[best]
        if w[top(w)] < VGX_W_MIN or dw[top(dw)] < VGX_W_MIN:
            continue
        hit += 1
        old, new = int(b[top(w)]), int(db[top(dw)])
        counter = votes.get(old)
        if counter is None:
            votes[old] = {new: 1}
        else:
            counter[new] = counter.get(new, 0) + 1
    table = {}
    for old, counter in votes.items():
        total = sum(counter.values())
        value, count = max(counter.items(), key=lambda kv: kv[1])
        if count * 2 >= total:                 # 多数才要（一半一半的那种别瞎定）
            table[old] = value
    return table, hit / len(src_pos)


def split_piece_cover(mod_pos, vset, ref):
    """这件盖住了参照分量的几成（0~1）：件里的顶点 1cm 内能找到的参照顶点比例

    耳坠那种小分量：件只占本网格 2% 的面，但这个分量的顶点它基本都盖住了 ——
    面数门槛拦不住它，得看这条。参照的顶点按位置去重（dump 里同位置常有好几行）。
    """
    ref_pos = ref.get('pos') or []
    if not ref_pos or not vset:
        return 0.0
    inv = 1.0 / SPLIT_COVER_NEAR
    cells = set()
    for k in vset:
        p = mod_pos[k]
        cells.add((int(floor(p[0] * inv)), int(floor(p[1] * inv)), int(floor(p[2] * inv))))
    seen = set()
    hit = 0
    for q in ref_pos:
        mark = (round(q[0] * 100000), round(q[1] * 100000), round(q[2] * 100000))
        if mark in seen:
            continue
        seen.add(mark)
        base = (int(floor(q[0] * inv)), int(floor(q[1] * inv)), int(floor(q[2] * inv)))
        found = False
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    if (base[0] + dx, base[1] + dy, base[2] + dz) in cells:
                        found = True
                        break
                if found:
                    break
            if found:
                break
        if found:
            hit += 1
    return hit / len(seen)


SPLIT_COVER_NEAR = 0.010       # "盖住多少"那步的格子大小（米）
SPLIT_DERIVE_MIN = 0.05         # 没表的分量按参照推骨索引：配对率低于这个就别用（宁可不改）



def split_rel_path(path: Path, base: Path) -> str:
    r"""写进 ini 的 filename：相对 ini 所在目录；同一个目录下就只写文件名"""
    try:
        rel = os.path.relpath(str(path), str(base))
    except ValueError:
        return path.name
    if rel.startswith('..'):
        return path.name
    if os.sep in rel:
        return ('.\\' if os.sep == '\\' else './') + rel
    return rel


_SPLIT_NS_GUARD = re.compile(
    r'(?im)^[ \t]*if[ \t]+\$(\\[^\\\s]+\\Master)\\swapvar[ \t]*==[ \t]*(\d+)[ \t]*$')


def split_namespace_guard(text):
    """命名空间合并类 mod（q333 合并脚本）的变体开关。

    返回 (guard 行, 变体号)，例如 ('if $\\q333\\Master\\swapvar==0', 0)；
    不是合并类返回 None。合并脚本给每个带 hash 的节都包了这一层 ——
    工具新写进去的节也要包，不然三个变体的同一 hash 会同时生效
    （铃-圣诞执行者 的贴图覆盖就是这么重复的）。
    """
    match = _SPLIT_NS_GUARD.search(text or '')
    if not match:
        return None
    return r'if ${0}\swapvar=={1}'.format(match.group(1), match.group(2)), int(match.group(2))


def split_wrap_namespace(lines, guard):
    """把新写的每个 TextureOverride 节按合并脚本的规矩包起来。

    hash 行后插 `match_priority = N` + `if $\\ns\\Master\\swapvar==N`，节尾补 endif，
    节里的行整体缩进。Resource 节不动。
    """
    if not guard:
        return lines
    expr, num = guard
    out, index = [], 0
    while index < len(lines):
        line = lines[index]
        if not line.startswith('[TextureOverride'):
            out.append(line)
            index += 1
            continue
        section = [line]
        index += 1
        while index < len(lines) and not lines[index].startswith('['):
            section.append(lines[index])
            index += 1
        body = section[1:]
        hash_at = next((k for k, item in enumerate(body)
                        if re.match(r'(?i)^\s*hash\s*=', item)), None)
        if hash_at is None:
            out.extend(section)
            continue
        wrapped = [section[0]]
        for k, item in enumerate(body):
            if re.match(r'(?i)^\s*match_priority\s*=', item):
                continue
            if k == hash_at:
                wrapped.append(item)
                wrapped.append('match_priority = {}'.format(num))
                wrapped.append(expr)
                continue
            wrapped.append(('\t' + item) if item.strip() else item)
        last = len(wrapped) - 1
        while last > 0 and (not wrapped[last].strip()
                            or wrapped[last].strip().startswith(';')):
            last -= 1
        wrapped.insert(last + 1, 'endif')
        out.extend(wrapped)
    return out


def split_variant_count(ini_path, text, files):
    """同一条网格有几个变体缓冲（`.0/.1/...` 资源各指向不同文件）。

    多帧动画合并 mod（铃-动态）就是 32 套，逐帧拆分要用独立脚本；
    普通工具按"一个网格一套缓冲"处理，遇到多套必须拒绝，否则只拆第 0 帧
    写出来的 ini 会把其它帧全画错。
    """
    base = files['blend'].stem
    if base.lower().endswith('blend'):
        base = base[:-5]
    base = base.strip('-_ .').lower()
    if not base:
        return 0
    sets = {}
    for title, start, end in split_sections(text):
        head = title.strip()
        if not head.lower().startswith('resource'):
            continue
        if base not in head.lower():
            continue
        num = re.search(r'\.(\d+)\s*$', head)
        if not num:
            continue
        body = text[start:end]
        fn = re.search(r'(?im)^\s*filename\s*=\s*([^\s;]+)', body)
        if not fn:
            continue
        path = (ini_path.parent / fn.group(1).replace('\\', '/'))
        try:
            path = path.resolve()
        except OSError:
            continue
        if path.exists():
            sets.setdefault(int(num.group(1)), set()).add(str(path))
    return sum(1 for paths in sets.values() if paths)


def split_position_variants(text, ini_path, files, verts, mesh_tag):
    """合并版 mod：同一条网格按 `$swapvar` 分支用不同的 Position 缓冲（.0/.1）。

    彼岸浮华 这种 GIMI 合并版：1/ 和 2/ 各一份 Position（形状不同），
    Texcoord/Blend/IB 共用。只拆一份的话，切到另一个变体形状就不对。
    返回 [{'num', 'path', 'title', 'primary'}]（按变体号排序）；不是这种结构返回 []。
    """
    if '$swapvar' not in text:
        return []
    main = files['position'].resolve()
    scaled = re.sub(r'[^0-9a-z]', '', mesh_tag.lower())
    found = {}
    for title, start, end in split_sections(text):
        head = title.strip()
        if not head.lower().startswith('resource'):
            continue
        num_match = re.search(r'\.(\d+)\s*$', head)
        if not num_match:
            continue
        body = text[start:end]
        stride = re.search(r'(?im)^\s*stride\s*=\s*(\d+)', body)
        if not stride or int(stride.group(1)) != 40:
            continue
        name = re.search(r'(?im)^\s*filename\s*=\s*([^\s;]+)', body)
        if not name:
            continue
        path = (ini_path.parent / name.group(1).replace('\\', '/')).resolve()
        if not path.exists() or path.stat().st_size != verts * 40:
            continue
        tag_scaled = re.sub(r'[^0-9a-z]', '', head.lower())
        if scaled and scaled not in tag_scaled:
            continue
        if not re.search(r'(?im)^\s*vb0\s*=\s*' + re.escape(head) + r'\s*$', text):
            continue
        found[str(path)] = {'num': int(num_match.group(1)), 'path': path,
                            'title': head, 'primary': path == main}
    if len(found) < 2 or not any(item['primary'] for item in found.values()):
        return []
    return sorted(found.values(), key=lambda item: (item['num'], str(item['path'])))


def split_drop_vb_runs(lines):
    """克隆 VB 节时去掉 `run = CommandList…`：那些 CommandList 会绑原网格的
    vb0/vb1/vb2（原顶点顺序），把件自己的绑定盖掉 → 顶点/UV 错位。
    皮肤/SetTextures 的 run 保留。"""
    out = []
    for line in lines:
        s = line.strip()
        if re.match(r'(?i)^run\s*=', s):
            low = s.lower()
            if 'skin' not in low and 'settextures' not in low:
                continue
        out.append(line)
    return out


def split_ensure_key(lines, key, value):
    if not any(re.match(r'(?i)^' + key + r'\s*=', line.strip()) for line in lines):
        lines.append(value)


def split_clone_section(lines, replace, drop=()):
    """按原节的行克隆：命中的键换成件的值，其它行（守卫/字段）原样保留"""
    out = []
    for raw in lines:
        text = raw.strip()
        if text.startswith('$'):
            continue          # 开关赋值由 assign_lines 统一补，克隆里不重复
        match = re.match(r'(?i)^([a-z_][\w\\-]*)\s*=', text)
        key = match.group(1).lower() if match else None
        if key and key in drop:
            continue
        if key and key in replace:
            out.append(replace[key])
            continue
        out.append(text)
    return out


def split_piece_block(prefix, ref, piece):
    """一件的一整套节（照已验证产物的形状）"""
    res_pos = 'Resource{}Position'.format(prefix)
    res_tex = 'Resource{}Texcoord'.format(prefix)
    res_blend = 'Resource{}Blend'.format(prefix)
    res_ib = 'Resource{}Head'.format(prefix)
    lines = ['']
    lines.append('; ===== 拆出来的一件：{}（原网格切给这个分量）====='.format(ref['name']))
    if piece.get('draw_in_blend'):
        # 新写法：原网格的 vb0/vb2/draw 都在 Blend 节里，件也照这个样子写；
        # 原来的 if 条件（DRAW_TYPE 这种）也保留，只把 vb0/draw 换成件自己的
        _src = piece.get('blend_lines')
        if _src:
            _body = split_clone_section(
                _src,
                {'hash': 'hash = {}'.format(ref['blend_hash']),
                 'vb2': 'vb2 = {}'.format(res_blend),
                 'vb0': 'vb0 = {}'.format(res_pos),
                 'draw': 'draw = {}, 0'.format(piece['verts'])},
                drop=('match_first_index', 'match_index_count',
                      'ib', 'resource_bak_ib0', 'drawindexed'))
            _body = split_drop_vb_runs(_body)
            split_ensure_key(_body, 'vb2', 'vb2 = {}'.format(res_blend))
            split_ensure_key(_body, 'vb0', 'vb0 = {}'.format(res_pos))
            split_ensure_key(_body, 'draw', 'draw = {}, 0'.format(piece['verts']))
            if not any('handling' in line.lower() for line in _body):
                _body.insert(1, 'handling = skip')
            lines += ['[TextureOverride{}Blend]'.format(prefix)] + _body
        else:
            lines += ['[TextureOverride{}Blend]'.format(prefix),
                      'hash = {}'.format(ref['blend_hash']),
                      'handling = skip',
                      'vb2 = {}'.format(res_blend)]
            if piece.get('draw_if'):
                lines += [piece['draw_if'],
                          '	vb0 = {}'.format(res_pos),
                          '	draw = {}, 0'.format(piece['verts']),
                          'endif']
            else:
                lines += ['vb0 = {}'.format(res_pos),
                          'draw = {}, 0'.format(piece['verts'])]
    else:
        pos_variants = piece.get('_pos_variants')
        _src = piece.get('pos_lines')
        if pos_variants:
            lines += ['[TextureOverride{}Position]'.format(prefix),
                      'hash = {}'.format(ref['pos_hash'])]
            for index, variant in enumerate(pos_variants):
                cond = ('if $swapvar == {}' if index == 0 else 'else if $swapvar == {}')
                lines += [cond.format(variant['num']),
                          '	vb0 = {}'.format(variant['res']),
                          '	vb2 = {}'.format(res_blend),
                          '	handling = skip',
                          '	draw = {}, 0'.format(piece['verts'])]
            lines += ['endif']
        elif _src:
            _body = split_clone_section(
                _src,
                {'hash': 'hash = {}'.format(ref['pos_hash']),
                 'vb0': 'vb0 = {}'.format(res_pos),
                 'vb2': 'vb2 = {}'.format(res_blend),
                 'draw': 'draw = {}, 0'.format(piece['verts'])},
                drop=('match_first_index', 'match_index_count',
                      'ib', 'resource_bak_ib0', 'drawindexed'))
            _body = split_drop_vb_runs(_body)
            split_ensure_key(_body, 'vb0', 'vb0 = {}'.format(res_pos))
            split_ensure_key(_body, 'vb2', 'vb2 = {}'.format(res_blend))
            split_ensure_key(_body, 'draw', 'draw = {}, 0'.format(piece['verts']))
            if not any('handling' in line.lower() for line in _body):
                _body.append('handling = skip')
            lines += ['[TextureOverride{}Position]'.format(prefix)] + _body
        else:
            lines += ['[TextureOverride{}Position]'.format(prefix),
                      'hash = {}'.format(ref['pos_hash']),
                      'vb0 = {}'.format(res_pos),
                      'vb2 = {}'.format(res_blend),
                      'handling = skip',
                      'draw = {}, 0'.format(piece['verts'])]
    # 原网格绘制节里的开关赋值（`$active = 1` 这种）照已验证写法写回件的绘制节：
    # 原节被注释掉以后就没人再置位，K/L 的 condition = $active == 1 会永远不成立
    lines += list(piece.get('assign_lines') or [])
    _tex_src = piece.get('tex_lines')
    if _tex_src:
        _body = split_clone_section(
            _tex_src,
            {'hash': 'hash = {}'.format(ref['tex_vb_hash']),
             'vb1': 'vb1 = {}'.format(res_tex)})
        _body = split_drop_vb_runs(_body)
        split_ensure_key(_body, 'vb1', 'vb1 = {}'.format(res_tex))
        lines += ['', '[TextureOverride{}Texcoord]'.format(prefix)] + _body
    else:
        lines += ['',
                  '[TextureOverride{}Texcoord]'.format(prefix),
                  'hash = {}'.format(ref['tex_vb_hash']),
                  'vb1 = {}'.format(res_tex)]
    if not piece.get('draw_in_blend'):
        _src_blend = piece.get('blend_lines')
        if _src_blend:
            _body = split_clone_section(
                _src_blend,
                {'hash': 'hash = {}'.format(ref['blend_hash']),
                 'vb2': 'vb2 = {}'.format(res_blend)},
                drop=('match_first_index', 'match_index_count',
                      'ib', 'resource_bak_ib0', 'drawindexed', 'draw'))
            _body = split_drop_vb_runs(_body)
            split_ensure_key(_body, 'vb2', 'vb2 = {}'.format(res_blend))
            lines += ['', '[TextureOverride{}Blend]'.format(prefix)] + _body
        else:
            lines += ['',
                      '[TextureOverride{}Blend]'.format(prefix),
                      'hash = {}'.format(ref['blend_hash'])]
    vlr = piece.get('vlr_lines')
    if vlr:
        # 原节整节克隆，只改 hash / 顶点数（filter_index 等字段原样保留）
        _vlr_body = []
        for _line in vlr:
            if re.match(r'(?i)^hash\s*=', _line):
                _vlr_body.append('hash = {}'.format(ref['draw_hash']))
            elif re.match(r'(?i)^override_vertex_count\s*=', _line):
                _vlr_body.append('override_vertex_count = {}'.format(piece['verts']))
            else:
                _vlr_body.append(_line)
        lines += ['',
                  '[TextureOverride{}_40_{}_VertexLimitRaise]'.format(
                      prefix, piece['verts'])] + _vlr_body + ['']
    else:
        lines += ['',
                  '[TextureOverride{}_40_{}_VertexLimitRaise]'.format(
                      prefix, piece['verts']),
                  'hash = {}'.format(ref['draw_hash'])] + \
                 (['filter_index = {}'.format(piece['filter_index'])]
                  if piece.get('filter_index') is not None else []) + [
                  'override_vertex_count = {}'.format(piece['verts']),
                  'override_byte_stride = 40',
                  '']
    _ib_src = piece.get('ib_lines')
    if _ib_src:
        _body = split_clone_section(
            _ib_src, {'hash': 'hash = {}'.format(ref['ib_hash'])},
            drop=('ib', 'match_first_index', 'match_index_count',
                  'resource_bak_ib0', 'drawindexed', 'draw'))
        # 原 IB 节的 `run = CommandList…` 会拿游戏原来那条 ib 画一次
        # （CL 里 `drawindexed = auto`）—— 件这时绑的是件自己的 vb0，
        # 整条 IB 配件的顶点就是越界绘制，游戏里整只炸开。
        # 节的 IB 只需要 hash + handling = skip 把原来那笔掐掉，run 一律不带。
        _body = split_drop_vb_runs(_body)
        if not any('handling' in line.lower() for line in _body):
            _body.append('handling = skip')
        lines += ['[TextureOverride{}IB]'.format(prefix)] + _body
    else:
        lines += [
                  '[TextureOverride{}IB]'.format(prefix),
                  'hash = {}'.format(ref['ib_hash']),
                  'handling = skip']
    lines += [
              '',
              '[TextureOverride{}Head]'.format(prefix),
              'hash = {}'.format(ref['ib_hash']),
              'handling = skip']
    if piece.get('segments'):
        # 这条网格原来是分段画的（部件开关就是靠这些段）：按原来的段和顺序重写，
        # 挪走的段注释掉不删 —— 开关才还能用
        lines += ['match_first_index = {}'.format(ref['first'] if ref['first'] is not None else 0),
                  'match_index_count = {}'.format(ref['count'] if ref['count'] else 0),
                  'Resource_Bak_IB0 = ref ib',
                  'ib = {}'.format(res_ib)]
        for item in piece['segments']:
            if item[0] == 'line':
                lines.append(item[1])
            elif item[1]:
                lines.append('drawindexed = {}, {}, 0'.format(item[1], item[2]))
            else:
                # 挪走的段留个注释（方便对着看），别删
                lines.append('; 这一段归别的分量了  ' + (item[3] if len(item) > 3 else ''))
        lines.append('ib = Resource_Bak_IB0')
    else:
        # 原节顺序照搬：match_first_index 紧跟 handling，ib 插回原来的位置
        # （已验证产物是 ib 在 `Resource\ZZMI\…` 之前）；Resource_Bak_IB0 要在
        # 件的 ib 赋值之前取，才存得下游戏原来那条 ib
        ps = piece.get('ps_lines', [])
        first = ref['first'] if ref['first'] is not None else 0
        count = ref['count'] if ref['count'] else 0
        if any('__PIECE_IB__' in line or '__PIECE_DRAW__' in line for line in ps):
            # 绘制 CommandList 是整段搬过来的（带 if/else 分支）：ib/drawindexed
            # 已经替换成占位符，这里换成件的值，分支结构原样保留
            lines += ['match_first_index = {}'.format(first),
                      'match_index_count = {}'.format(count),
                      'Resource_Bak_IB0 = ref ib']
            for line in ps:
                line = line.replace('__PIECE_IB__', res_ib)
                line = line.replace('__PIECE_DRAW__',
                                    '{}, 0, 0'.format(piece['indices']))
                lines.append(line)
            lines += ['ib = Resource_Bak_IB0']
        else:
            cut = piece.get('ps_ib_at')
            if cut is None or cut > len(ps):
                cut = len(ps)
            lines += ['match_first_index = {}'.format(first)]
            lines += ps[:cut]
            lines += ['Resource_Bak_IB0 = ref ib',
                      'ib = {}'.format(res_ib)]
            lines += ps[cut:]
            lines += ['match_index_count = {}'.format(count),
                      'drawindexed = {}, 0, 0'.format(piece['indices']),
                      'ib = Resource_Bak_IB0']
    # 件自己的四个资源定义 —— 这两支都得写。分段那支以前漏了：节里 vb0/vb1/vb2/ib
    # 引用的资源没人定义，游戏里就是一堆红字（资源找不到），件也画不出来
    lines += ['']
    pos_variants = piece.get('_pos_variants')
    if pos_variants:
        for variant in pos_variants:
            lines += ['[{}]'.format(variant['res']), 'type = Buffer', 'stride = 40',
                      'filename = {}'.format(variant['name']), '']
    else:
        lines += ['[{}]'.format(res_pos), 'type = Buffer', 'stride = 40',
                  'filename = {}'.format(piece['files_out']['position']), '']
    lines += ['[{}]'.format(res_tex), 'type = Buffer',
              'stride = {}'.format(piece['stride_tex']),
              'filename = {}'.format(piece['files_out']['texcoord']), '',
              '[{}]'.format(res_blend), 'type = Buffer', 'stride = 32',
              'filename = {}'.format(piece['files_out']['blend']), '',
              '[{}]'.format(res_ib), 'type = Buffer',
              'format = DXGI_FORMAT_R32_UINT',
              'filename = {}'.format(piece['files_out']['ib']), '']
    return lines


def split_block_conditionals_ok(lines):
    """一段节文本里 if/elif/else/endif 是否配对；配对返回 None，否则返回原因

    3dmigoto 遇到没配对的 elif / 没 if 的 else，会把这一节剩下的命令整个丢掉 ——
    看起来就是"件不画了 / 身体拉丝"。写盘前先自己查，别等游戏里炸。
    """
    depth = 0
    for line in lines:
        s = line.strip()
        if not s or s.startswith((';', '#', '[')):
            continue
        word = s.split()[0].lower()
        if word == 'if':
            depth += 1
        elif word in ('elif', 'elseif', 'else'):
            if depth == 0:
                return '出现没有 if 的 {}：{}'.format(word, s)
        elif word == 'endif':
            if depth == 0:
                return '多出一个 endif：{}'.format(s)
            depth -= 1
    if depth:
        return 'if 没有配对的 endif（差 {} 个）'.format(depth)
    return None


def split_validate(planned):
    """写盘前自检：件的数据 + 生成的节。返回问题列表（空 = 通过）

    宁可不写，不给半成品 —— 数据错、节结构错（孤立 elif / this=）、
    drawindexed 越界，都在这里拦下来，而不是进游戏看截图。
    """
    problems = []
    for item in planned:
        name = item['name']
        for title in item.get('old_sections') or ():
            if title.strip().lower().startswith('commandlist'):
                problems.append('【{}】：CommandList 节不该被注释（{}）'.format(name, title))
        seen_prefix = {}
        for piece in item['pieces']:
            prefix = piece.get('prefix')
            if prefix:
                if prefix in seen_prefix:
                    problems.append('【{}】：件前缀重复（{} / {}）—— 会互相覆盖'.format(
                        name, seen_prefix[prefix], prefix))
                seen_prefix[prefix] = piece.get('ref', {}).get('name') or prefix
        for piece in item['pieces']:
            verts = int(piece['verts'])
            ref_name = piece['ref']['name']
            where = '【{}】的件 {}'.format(name, ref_name)
            if len(piece['position']) != verts * 40:
                problems.append('{}：position {} 字节 ≠ {} 顶点 × 40'.format(
                    where, len(piece['position']), verts))
            if len(piece['blend']) != verts * 32:
                problems.append('{}：blend {} 字节 ≠ {} 顶点 × 32'.format(
                    where, len(piece['blend']), verts))
            if len(piece['texcoord']) != verts * int(piece['stride_tex']):
                problems.append('{}：texcoord {} 字节 ≠ {} 顶点 × {}'.format(
                    where, len(piece['texcoord']), verts, piece['stride_tex']))
            ib_size = len(piece['ib'])
            if ib_size % 12:
                problems.append('{}：ib {} 字节不是 3 个索引的整数倍'.format(where, ib_size))
            indices = ib_size // 4
            if indices:
                max_index = max(struct.unpack('<{}I'.format(indices), piece['ib']))
                if max_index >= verts:
                    problems.append('{}：索引最大 {} 超过顶点数 {}'.format(
                        where, max_index, verts))
            for seg in (piece.get('segments') or ()):
                if seg[0] != 'draw' or not seg[1]:
                    continue
                count, start = int(seg[1]), int(seg[2])
                if start + count > indices:
                    problems.append('{}：drawindexed {} 起 {} 超过件索引数 {}'.format(
                        where, count, start, indices))
            if 'files_out' not in piece:
                continue                    # 还没算文件名（理论上不会走到这里）
            block = split_wrap_namespace(
                split_piece_block(piece.get('prefix') or name, piece['ref'], piece),
                item.get('merge_guard'))
            piece['_block'] = block       # 写盘时直接复用，别重新生成一遍
            err = split_block_conditionals_ok(block)
            if err:
                problems.append('{}：{}'.format(where, err))
            if any(re.match(r'(?i)^\s*this\s*=', line) for line in block):
                problems.append('{}：绘制节里出现 this =（3dmigoto 会截断整节）'.format(where))
            missing = item.get('required_texture') or set()
            if missing:
                have = {' '.join(line.split()).lower() for line in block}
                lacking = sorted(missing - have)
                if lacking:
                    problems.append('{}：件的绘制节少了原节的贴图绑定（{}）'.format(
                        where, '；'.join(lacking[:4])))
    return problems


def split_tex_for(ref, raw_tex: bytes, verts: int, per_vertex: int, src_format=None):
    """按这个分量的元素表把 texcoord 重排 -> (新字节, 新步幅)；推不出返回 (None, 原因)

    src_format = **这条网格自己那个分量**的元素表（"顶点格式"那步已经把它换成这个样子了）。
    给了它就走"逐块对位 + 按块类型换算"：两边字节数一样但块不一样时（网格是
    `4B+半精度UV+浮点UV+半精度UV`、目标分量是 `4B+浮点UV×3`），光看字节数会以为
    "老的就是新的前几块"，按同样类型搬就整串错位 —— 耳坠那种 UV 全乱、采样到贴图别处、
    看着没颜色，就是这么来的。
    """
    new_format = tuple(ref['info']['new_format'])
    new_stride = fmt_stride(new_format)
    if src_format and fmt_stride(src_format) == per_vertex and tuple(src_format) != new_format:
        blocks = tuple(src_format)[:len(new_format)]
        return (tex_convert(raw_tex, verts, blocks, new_format, list(range(len(blocks)))),
                new_stride)
    if per_vertex == new_stride:
        return raw_tex, new_stride
    prefix = split_tex_prefix(new_format, per_vertex)
    if prefix:
        return tex_convert(raw_tex, verts, prefix, ref['info']['new_format'],
                           list(range(len(prefix)))), new_stride
    layout = derive_element_layout(ref.get('texcoord_buf'), verts, per_vertex, ref['info'])
    if layout.get('ok'):
        return tex_convert(raw_tex, verts, layout['old_format'], ref['info']['new_format'],
                           layout.get('element_map')), new_stride
    return None, ('texcoord 布局推不出（老的每顶点 {} 字节、目标 {} 字节，既不是少几块也不是'
                  '已知的旧格式：{}）'.format(per_vertex, new_stride, layout.get('reason')))


def split_analyse(ini_path: Path, text: str, files: dict, refs: list, nearest,
                  mod_pos: list, mod_blend: list, mod_ib: list, info: dict,
                  own_bufs=None):
    """分类一个网格 -> (计划 or None, 跳过原因 or None)

    own_bufs：这个网格的其它变体缓冲（多帧 mod）。判断"某个分量是不是别的网格的"
    时要一起算本网格，否则第 2 帧起会把 .0 资源当成别的网格，把头发分量排除掉。
    """
    # 多帧/多变体网格（同一网格 32 套缓冲）：普通工具只按一套拆会写坏其它帧，
    # 交给独立的逐帧修复脚本
    if own_bufs is None:
        variants = split_variant_count(ini_path, text, files)
        # 只有"按时间逐帧切换"的动画 mod 才拦；普通两变体（.0/.1）照常拆
        if variants > 1 and re.search(
                r'(?im)^\s*\$swapvar\s*=.*\btime\b', text):
            return None, ('{}（同一网格有 {} 套变体缓冲 —— 多帧动态 mod，'
                          '请用独立脚本《逐帧拆分修复》，主工具不拆）'
                          .format(files['blend'].name, variants))
    # 已经拆过的不再拆第二次：件节（[TextureOverride<网格名>_<ib>Head]）还在就说明
    # 上次已经写过了。重跑一次会把同样的件节再追加一遍、ini 越滚越长。
    name_now = files['blend'].stem
    if name_now.lower().endswith('blend'):
        name_now = name_now[:-5]
    name_now = name_now.strip('-_ .')
    existing_titles = {title.strip().lower() for title, _s, _e in split_sections(text)}
    for ref in refs:
        ib_hash = str(ref.get('ib_hash') or '').lower()
        if not ib_hash:
            continue
        if 'textureoverride{}_{}head'.format(name_now, ib_hash).lower() in existing_titles:
            return None, None            # 已拆过：静默跳过（不是普通 mod，也不用报错）
    # 这条网格自己就是本工具拆出来的"件"：件名是 "<原网格名>_<8 位 ib hash>"，
    # 且它的 [TextureOverride<件名>Head] 还在。注意别用 Resource_Bak_IB0 判断 ——
    # 新版 ZZMI/夏音 这种原 mod 自己就带 Resource_Bak_IB0，会误伤。
    if re.search(r'_[0-9a-f]{8}$', name_now.lower()) and \
            ('textureoverride' + name_now + 'head').lower() in existing_titles:
        return None, None
    # 跨 IB 渲染（铃-可爱睡衣 这类）：绘制节里存别的网格的顶点/中途换 ib 重画，
    # 段的索引偏移是相对【另一条 ib】的 —— 按本网格拆会把段当成本网格的段，必错。
    # 只认有把握的签名：copy vb0 / ref vb0 / ref so0 / ref vs-cb，或 ib = 换成
    # 不属于本网格的资源（Resource_Bak_IB0 这种还原变量除外）。
    _res_map = split_mesh_resource_map(text, files)
    _own = set()
    for _values in _res_map.values():
        _own |= _values
    _own_ib = set(_res_map.get('ib') or ())
    if _own:
        for _title, _s1, _e1 in split_sections(text):
            if not _title.strip().lower().startswith('textureoverride'):
                continue
            _body = text[_s1:_e1]
            if not any(_name in (_title + _body).lower() for _name in _own):
                continue
            for _line in _body.splitlines():
                _line = _line.strip()
                if not _line or _line.startswith((';', '#')):
                    continue
                if (re.search(r'(?i)=\s*copy[ _]?vb0\b', _line)
                        or re.search(r'(?i)=\s*ref\s+vb0\b', _line)
                        or re.search(r'(?i)=\s*ref\s+so0\b', _line)
                        or re.search(r'(?i)=\s*ref\s+vs-cb\w*', _line)):
                    return None, ('{}（绘制节用了跨 IB 渲染：{} —— 段索引属于别的网格，'
                                  '拆分不安全，跳过）'.format(files['blend'].name, _line))
                _m = re.match(r'(?i)^ib\s*=\s*(\S+)\s*$', _line)
                if (_m and _m.group(1).lower() not in _own_ib
                        and _m.group(1).lower() != 'null'
                        and not _m.group(1).lower().startswith('resource_bak')):
                    return None, ('{}（绘制节中途换用别的 ib：{} —— 跨 IB 渲染，'
                                  '拆分不安全，跳过）'.format(files['blend'].name, _m.group(1)))
    verts = len(mod_pos)
    tri = [(mod_ib[i], mod_ib[i + 1], mod_ib[i + 2]) for i in range(0, len(mod_ib) - 2, 3)]
    if not tri:
        return None, '{}（索引里没有三角面）'.format(files['ib'].name)
    if max(mod_ib) >= verts:
        return None, '{}（索引最大 {} 超过顶点数 {}，文件对不上）'.format(
            files['ib'].name, max(mod_ib), verts)

    # 超大网格先抽样判一次“值不值得拆”：只落一个分量、且次多分量很小又
    # 没盖住它的，直接跳过，不跑全量分类（Dialyn Hakuhou 134k 顶点：
    # 全量分类约 3 秒，抽样 4096 个点约 0.2 秒）。
    if verts >= 50000:
        sample_step = max(1, verts // 4096)
        sample = list(range(0, verts, sample_step))
        sample_cls = []
        for k in sample:
            r, _d = nearest(mod_pos[k], mod_blend[k][0])
            sample_cls.append((k, r))
        sample_n = len(sample_cls)
        sample_paired = sum(1 for _k, r in sample_cls if r >= 0)
        if sample_n and sample_paired < sample_n * SPLIT_COVER_MIN * 0.5:
            return None, '{}（抽样只配上 {:.0%} 的顶点，跟参照不是同一套，跳过）'.format(
                files['blend'].name, sample_paired / sample_n)
        sample_counts = {}
        for _k, r in sample_cls:
            if r >= 0:
                sample_counts[r] = sample_counts.get(r, 0) + 1
        ordered_sample = sorted(sample_counts.items(), key=lambda kv: -kv[1])
        second_share = (ordered_sample[1][1] / sample_n) if len(ordered_sample) > 1 else 0.0
        if second_share < SPLIT_SECOND_MIN * 0.25:
            ok_small = False
            uncertain = False
            for r, count in ordered_sample[1:]:
                vset = [_k for _k, rr in sample_cls if rr == r]
                cover = split_piece_cover(mod_pos, vset, refs[r])
                ref_verts = len(refs[r].get('pos') or ())
                est_ratio = (count / sample_n * verts / ref_verts) if ref_verts else 0.0
                if cover >= SPLIT_PIECE_COVER and est_ratio >= SPLIT_GATE_MIN_RATIO:
                    ok_small = True
                    break
                if cover >= SPLIT_PIECE_COVER * 0.2:
                    # 抽样盖住得不算少，可能是耳坠那种小而全的件：别省这一步，
                    # 交给全量分类判。
                    uncertain = True
            if not ok_small and not uncertain:
                return None, None

    cls = []
    cls_cache = {}                 # 同一位置+同一权重的重复顶点直接复用分类结果
    for k, p in enumerate(mod_pos):
        weights = mod_blend[k][0]
        cache_key = (p[0], p[1], p[2], weights)
        r = cls_cache.get(cache_key)
        if r is None:
            r, _d = nearest(p, weights)
            cls_cache[cache_key] = r
        cls.append(r)
    paired = sum(1 for c in cls if c >= 0)     # 扩散之前先记下来（"是不是同一套"要看它）

    # 参照里没有的地方（mod 自己加的尾巴 / 飘带这种，离所有参照都超过 SPLIT_FAR）
    # 别整块丢给主件 —— 按三角面连通性从最近的"已判定"邻居扩散标签，跟着自己接的那件走
    orphan = [k for k in range(verts) if cls[k] < 0]
    neighbours = {}
    for a, b, c in tri:
        for x, y in ((a, b), (b, c), (c, a)):
            neighbours.setdefault(x, []).append(y)
            neighbours.setdefault(y, []).append(x)

    # 一个连通块只能归一件 —— 长头发从头顶一直垂到胯上，光按顶点位置，下半截会判给腿、
    # 上半截判给头发，中间就撕开了。整块按多数票归一（票一样时取下标小的，结果稳定）
    # 耳坠件专属骨号（27~29）+ 头发根骨（30）：整块都在这组里且用了 27~29 = 耳坠挂件
    EARRING_BONES = {27, 28, 29, 30}
    earring_ref = None
    for _i, _ref in enumerate(refs):
        if str(_ref.get('ib_hash') or '').lower() == '07920753':
            earring_ref = _i
            break
    bone_rows = mod_blend
    _bone_backup = vgx_backup_of(files['blend'])
    if _bone_backup.exists():
        _raw = _bone_backup.read_bytes()
        if len(_raw) == len(files['blend'].read_bytes()):
            bone_rows = load_blend_verts(_bone_backup) or mod_blend

    earring_islands = set()                     # 按骨号判成耳坠的块（下面骨头纠正别再把它们拽走）
    seen = bytearray(verts)
    island_votes, island_todo = [], []          # 每块的票数 / 要处理的块（给下面合并用）
    island_members = []                         # 每块的顶点列表，后面算中心点直接用
    island_of = [-1] * verts
    island_pick = []
    island_mixed = set()                        # 票数没过半数的块（等知道哪几件成件了再定）
    for start in range(verts):
        if seen[start]:
            continue
        seen[start] = 1
        comp, queue = [start], deque([start])
        while queue:
            k = queue.popleft()
            for n in neighbours.get(k, ()):
                if not seen[n]:
                    seen[n] = 1
                    comp.append(n)
                    queue.append(n)
        island_index = len(island_votes)
        for k in comp:
            island_of[k] = island_index
        island_members.append(comp)
        island_votes.append(None)
        island_pick.append(-1)
        votes = {}
        for k in comp:
            if cls[k] >= 0:
                votes[cls[k]] = votes.get(cls[k], 0) + 1
        # 耳坠配件：整块主骨全落在 27~30（且用到了 27~29 —— 那是耳坠专属骨，
        # 头发表从 30 起）→ 整块归 07920753 那件。铃-夏日休闲 的耳坠挂件贴着头发长，
        # 光看位置会被判进头发件；同一条头发里只用 30 单骨的小块不算（透明猫咪右耳那簇）。
        if earring_ref is not None and comp:
            bones = set()
            for k in comp:
                wrow, brow = bone_rows[k]
                slot = max(range(4), key=lambda s: wrow[s])
                if wrow[slot] >= VGX_W_MIN:
                    bones.add(int(brow[slot]))
            # 只有【小】块才整块判耳坠：挂件链都是几十~几百顶点（夏日最大 150）。
            # 一整块头发要是只沾到几颗 27~29 也会满足骨号集合，但那是头发，
            # 不能整块搬去耳坠件（铃-动态：头发+发饰连成一块，3680 顶点）
            if (bones and bones <= EARRING_BONES and (bones & {27, 28, 29})
                    and len(comp) <= SPLIT_EARRING_ISLAND_MAX):
                votes = {earring_ref: len(comp)}
                earring_islands.add(island_index)
        island_votes[island_index] = votes
        if not votes:
            continue
        pick, top = max(((r, n) for r, n in votes.items()), key=lambda kv: (kv[1], -kv[0]))
        island_pick[island_index] = pick
        # 只有这块网格多数顶点都判给同一件时才整块归一 —— 像那条长头发，910 个顶点里
        # 只有 28 个位置碰巧落进身体分量，按多数票会把整块搬去身体（中间就撕开了）
        if top * 2 < len(comp):
            # 多数票不够：先记下来，等"哪几件成了件"算出来以后再看票里有没有它们
            # （夏音 腰那圈 147 个顶点：腿 73 票 / 身体 70 票，差一票没过半数 ——
            #   以前整块当"mod 自己加的地方"跟主件（头发），衣服带子绑到头发骨上，
            #   游戏里拉成一根黑刺）。见下面 island_target 那段
            island_mixed.add(island_index)
            for k in comp:
                cls[k] = -1
            continue
        for k in comp:
            cls[k] = pick

    tri_cls = []
    for a, b, c in tri:
        votes = {}
        for k in (a, b, c):
            if cls[k] >= 0:
                votes[cls[k]] = votes.get(cls[k], 0) + 1
        tri_cls.append(max(votes.items(), key=lambda kv: kv[1])[0] if votes else -1)

    counted = {}
    for r in tri_cls:
        counted[r] = counted.get(r, 0) + 1
    hit_parts = sorted((r for r in counted if r >= 0), key=lambda r: -counted[r])
    if not hit_parts:
        return None, '{}（跟参照一个点都对不上）'.format(files['blend'].name)
    if len(hit_parts) < 2 or counted[hit_parts[1]] < len(tri) * SPLIT_SECOND_MIN:
        # 次多分量不大，但如果它"小而全"（件盖住该分量 ≥30% 且顶点数 ≥50%），
        # 仍然要拆 —— 铃-动态 的衣服网格：头发部分只占 7% 三角，可是整个头发都在里面
        ok_small = False
        if len(hit_parts) >= 2:
            _sec = hit_parts[1]
            _vset = []
            _seen = set()
            for _t, _c in enumerate(tri_cls):
                if _c != _sec:
                    continue
                for _k in tri[_t]:
                    if _k not in _seen:
                        _seen.add(_k)
                        _vset.append(_k)
            _cover = split_piece_cover(mod_pos, _vset, refs[_sec])
            _ratio = (len(_vset) / len(refs[_sec]['pos'])
                      if refs[_sec].get('pos') else 0.0)
            ok_small = (_cover >= SPLIT_PIECE_COVER
                        and _ratio >= SPLIT_GATE_MIN_RATIO)
        if not ok_small:
            return None, None                  # 只落一个分量 = 普通 mod，不拆也不报

    if paired < verts * SPLIT_COVER_MIN:
        return None, '{}（只配上 {:.0%} 的顶点，跟参照不是同一套，跳过）'.format(
            files['blend'].name, paired / verts)

    # texcoord：每件按【自己那个分量】的元素表重排（件与件的目标格式可能不一样）
    raw_tex = files['texcoord'].read_bytes()
    if not raw_tex or len(raw_tex) % verts:
        return None, '{}（texcoord {} 字节 / {} 顶点 除不尽）'.format(
            files['texcoord'].name, len(raw_tex), verts)
    per_vertex = len(raw_tex) // verts
    tex_cache = {}

    # 贴图槽 / 皮肤着色命令都在 Head 那一节里，得按【这个网格】整个翻一遍再搬
    # 文件名和 ini 里的写法可能用不同分隔符（bea4a483-Blend.buf vs bea4a483_Position）——
    # 匹配词去掉首尾分隔符，两种都认；不去掉的话旧节一个都匹配不上，原网格会照旧画一遍
    mesh_tag = files['blend'].stem[:-5].lower().strip('-_ .')
    res_map = split_mesh_resource_map(text, files)     # 按资源 filename 反查各类资源名
    res_names = set()
    for _values in res_map.values():
        res_names |= _values
    if not res_names:                                  # 资源定义认不出来就按老办法兜底
        res_names = split_mesh_resources(text, files)
    mesh_hashes = {str(r['ib_hash']).lower() for r in refs if r['ib_hash']}
    mesh_blend_hashes = {str(r.get('blend_hash') or '').lower() for r in refs}
    seen_lines = set()

    # 这条网格真正用来画的那【一个】节 —— 已验证写法只克隆这一节，不按名字拼多节
    # （内内裤袜 的 elif 事故就是拼多节拼进来的）
    src_section = split_find_draw_section(text, files, res_map, mesh_tag, mesh_hashes)

    # 这条网格的 filter_index（ZZMI 的顶点数过滤变量）：件的 VertexLimitRaise
    # 也要写同一个值，件里 `if vb0 == N` 的守卫才成立（已验证产物就是这么带的）
    filter_index = None
    for _t, _s, _e in split_sections(text):
        _body = text[_s:_e]
        if 'filter_index' not in _body.lower():
            continue
        _low = (_t + _body).lower()
        if mesh_tag not in _low and not any(r in _low for r in res_names):
            continue
        _m = re.search(r'(?im)^\s*filter_index\s*=\s*(\d+)', _body)
        if _m:
            filter_index = int(_m.group(1))
            break
    if filter_index is None and src_section is not None:
        _m = re.search(r'(?im)^\s*if\s+vb0\s*==\s*(\d+)', src_section[1])
        if _m:
            filter_index = int(_m.group(1))

    # 原网格的 VertexLimitRaise 节整节克隆（filter_index 这种字段不能手写重建）
    def _section_lines(word):
        for _t, _s, _e in split_sections(text):
            _tl = _t.strip().lower()
            if not _tl.startswith('textureoverride') or word not in _tl:
                continue
            _body = text[_s:_e]
            _low = (_t + _body).lower()
            if mesh_tag not in _low and not any(r in _low for r in res_names):
                continue
            return [line.strip() for line in _body.splitlines()
                    if line.strip()
                    and not line.strip().startswith((';', '#', '['))]
        return None

    vlr_lines = _section_lines('vertexlimitraise')
    pos_lines = _section_lines('position')
    tex_lines = _section_lines('texcoord')
    blend_lines = _section_lines('blend')
    ib_lines = None
    for _t, _s, _e in split_sections(text):
        _tl = _t.strip().lower()
        if not _tl.startswith('textureoverride') or not _tl.endswith('ib'):
            continue
        _body = text[_s:_e]
        _low = (_t + _body).lower()
        if mesh_tag not in _low and not any(r in _low for r in res_names):
            continue
        ib_lines = [line.strip() for line in _body.splitlines()
                    if line.strip()
                    and not line.strip().startswith((';', '#', '['))]
        break

    def _is_draw_section(block):
        """只认"绘制/贴图绑定"节：带 ib =（不是 null）、ZZMI 的 Resource\\ZZMI\\ 引用
        或 checktextureoverride。

        Position/Texcoord/Blend 这种只设缓冲的节、贴图 swap 节（this= + if/elif 链）
        都不是绘制节。铃-内内裤袜：宽松匹配按网格名把 12 个 $swapvar 贴图节的
        `elif $swapvar==N`（if 被滤掉了、elif 没滤）和 Position 节的 `$active = 1`
        全收进件的 Head 里 —— 孤立 elif 让 3dmigoto 把整节剩下的命令全丢掉，
        件的 drawindexed 不执行、ib 也不还原，沾到后面别的绘制上，身体上就豁口/拉丝。
        """
        low = block.lower()
        if 'resource\\zzmi\\' in low or 'checktextureoverride' in low:
            return True
        for raw in block.splitlines():
            s = raw.strip()
            if re.match(r'(?i)^ib\s*=', s) and not re.search(r'(?i)\bnull\b', s):
                return True
        return False

    def _collect_ps(strict):
        """把绘制节里"每件要重写的那几个键"以外的行原样带出来（整节搬、改键）。

        strict = 只认【这条网格自己的节】；宽松那种会把别的网格的 run 也扫进来。
        以前是白名单（只收 ps-tN= 和 run=），漏过 ZZMI 的
        `Resource\\ZZMI\\Diffuse = ref Resource_…` + `run = CommandList\\ZZMI\\SetTextures`
        —— 件里没人绑贴图，整件采样游戏原版贴图 = "模型对、颜色不对"。

        返回 (行, ib 插回的位置)：行里剔掉了每件要重写的键，但记着原节里 `ib =`
        在第几行 —— 写件时把件的 ib 插回同一位置（已验证产物就是原节顺序照搬：
        ib 在 `Resource\\ZZMI\\…` 前面）。
        """
        out, ib_at = [], None
        if src_section is not None:
            # 只从挑出来的那一节搬（不再按网格名把别的节拼进来）
            sources = [(src_section[0], src_section[1])]
        else:
            sources = [(title, text[start:end]) for title, start, end in split_sections(text)]
        for title, block in sources:
            head = title.strip().lower()
            if not head.startswith('textureoverride'):
                continue                      # 资源定义节里是 type/stride/filename，不能搬
            low = (title + block).lower()
            if src_section is None:
                if strict:
                    if mesh_tag not in low and not any(r in low for r in res_names):
                        continue
                elif (mesh_tag not in low and not any(r in low for r in res_names)
                      and not any(h in low for h in mesh_hashes)):
                    continue
                if not _is_draw_section(block):
                    continue
            for raw in block.splitlines():
                s = raw.strip()
                if not s or s.startswith((';', '#', '[')):
                    continue
                if re.match(r'(?i)^ib\s*=', s):
                    if ib_at is None:
                        ib_at = len(out)
                    continue
                # 这几个键每件的值都不一样，写回时由 split_piece_block 重新生成
                if re.match(r'(?i)^(hash|handling|vb[012]|match_first_index|'
                            r'match_index_count|Resource_Bak_IB0|draw|drawindexed|'
                            r'override_\w+)\s*=', s):
                    continue
                if re.match(r'(?i)^this\s*=', s):
                    # `this = Resource…` 只在贴图 hash 命中的覆盖节里合法；搬进件的
                    # IB/VB 节会让 3dmigoto 报错并把整节截断 → 件不画（夏日 头发腿没了）
                    continue
                if s.split() and s.split()[0].lower() in ('if', 'else', 'elif', 'elseif', 'endif'):
                    # if/endif 不搬：它们包住的 vb0/draw 已被剔掉，搬过去只剩空壳
                    # （铃-夏日休闲 的 DRAW_TYPE 空 if 会把整节截断 —— 头发腿都不画）
                    continue
                if re.match(r'(?i)^run\s*=', s):
                    # 只带皮肤着色那条（CommandListSkinTexture）和 ZZMI 的贴图绑定
                    # 命令（SetTextures），mod 自己的部件级着色器
                    # （CustomShaderTransparencyStocking 这种）是按子绘制分段用的，
                    # 拆成一件后套整件会串色 —— 已验证写法也不带
                    low_s = s.lower()
                    if 'skin' not in low_s and 'settextures' not in low_s:
                        # 自定义 run（外部发光、CustomShader、外部 CommandList）：
                        # 照克隆的规矩原样保留 —— 原节里怎么写的，件里就怎么写
                        name_s = s.split('=', 1)[1].strip()
                        body_s = None
                        if name_s.lower().startswith('commandlist'):
                            body_s = split_find_commandlist(text, name_s)
                        inner = [line.strip() for line in body_s.splitlines()
                                 if line.strip() and not line.strip().startswith('[')] \
                            if body_s else []
                        if inner and any(re.match(r'(?i)^ib\s*=', line)
                                         for line in inner) \
                                and not any(re.match(r'(?i)^drawindexed\s*=',
                                                    line) for line in inner):
                            # 只换 ib 的 CommandList（老 mod 的 [TextureOverride…A]
                            # run = CommandList<网格>A 就是这种：按变体把 ib 换回
                            # 原网格那条）。件的绘制节要自己绑件的 ib —— 这条 run
                            # 带进去会把原网格整条 ib 绑上，画完还原后游戏下一笔
                            # 还拿着它配件的 vb0 → 越界，身上糊一片碎面。
                            # 只留它里面的贴图命令（skin / SetTextures / ps / ZZMI）。
                            for line in inner:
                                s_low = line.strip().lower()
                                if not s_low:
                                    continue
                                if s_low.startswith('run'):
                                    if 'skin' not in s_low and 'settextures' not in s_low:
                                        continue
                                elif not re.match(
                                        r'(?i)^(ps-t\d+|resource\\zzmi|checktextureoverride)',
                                        line.strip()):
                                    continue
                                if s_low not in seen_lines:
                                    seen_lines.add(s_low)
                                    out.append(line.strip())
                            continue
                        if inner and any(re.match(r'(?i)^drawindexed\s*=',
                                                  line) for line in inner):
                            # 这是真正绘制的那条 CommandList：整段搬（已验证写法），
                            # 保留 if/else、ps、checktextureoverride 和别的命令，
                            # 只把 ib 和 drawindexed 换成本件的
                            for line in inner:
                                if re.match(r'(?i)^drawindexed\s*=', line):
                                    out.append('drawindexed = __PIECE_DRAW__')
                                    continue
                                if re.match(r'(?i)^ib\s*=', line):
                                    out.append('ib = __PIECE_IB__')
                                    continue
                                if re.match(r'(?i)^(hash|handling|vb[012]|draw|'
                                            r'match_first_index|match_index_count|'
                                            r'Resource_Bak_IB0|override_\w+)\s*=', line):
                                    continue
                                out.append(line)
                            continue
                        if s.lower() not in seen_lines:
                            seen_lines.add(s.lower())
                            out.append(s)
                        continue
                if s.lower() in seen_lines:
                    continue
                seen_lines.add(s.lower())
                out.append(s)
        return out, ib_at

    # 这条网格原来的画法：老 mod 画在 Position 节；新 mod（铃-夏日休闲）画在 Blend 节
    # （hash = blend hash，vb2 + vb0 + draw 全在一个 Blend 节里）—— 件要照原来的节写
    draw_in_blend = False
    draw_if = None
    for _title, _s0, _e0 in split_sections(text):
        _head = _title.strip().lower()
        if not _head.startswith('textureoverride') or not _head.endswith('blend'):
            continue
        _body = text[_s0:_e0]
        _low_body = _body.lower()
        _bhashes = {match.group(1).lower()
                    for match in re.finditer(r'(?im)^\s*hash\s*=\s*(\w+)', _body)}
        # 只认【这条网格自己】的 Blend 节：别的网格的 Blend 节也带 vb2+draw，
        # 按先来先得会把写法判错
        if not (mesh_tag in (_head + _low_body)
                or any(r in _low_body for r in res_names)
                or (_bhashes & (mesh_hashes | mesh_blend_hashes))):
            continue
        if (re.search(r'(?im)^\s*vb2\s*=', _body)
                and re.search(r'(?im)^\s*draw\s*=', _body)):
            draw_in_blend = True
            _if = re.search(r'(?im)^[ \t]*if[ \t]+(.+?)[ \t]*$', _body)
            draw_if = 'if {}'.format(_if.group(1)) if _if else None
            break

    ps_lines, ps_ib_at = _collect_ps(True)
    if not ps_lines and src_section is None:
        ps_lines, ps_ib_at = _collect_ps(False)

    # 原网格绘制节里的开关赋值（`$active = 1` 这种）：原节被注释掉以后没人再置位，
    # KeySwap 的 condition = $active == 1 就永远不成立、K/L 切换全失效。
    # 照已验证写法写回件自己的绘制节（Position / Blend）。
    assign_lines = []
    for _title, _s1, _e1 in split_sections(text):
        _block = text[_s1:_e1]
        if not _title.strip().lower().startswith('textureoverride'):
            continue
        _low = (_title + _block).lower()
        if mesh_tag not in _low and not any(r in _low for r in res_names):
            continue
        for _raw in _block.splitlines():
            _s = _raw.strip()
            _m = re.match(r'(?i)^(\$[A-Za-z_]\w*)\s*=\s*(-?\d+)\s*$', _s)
            if _m:
                _line = '{} = {}'.format(_m.group(1), _m.group(2))
                if _line.lower() not in seen_lines:
                    seen_lines.add(_line.lower())
                    assign_lines.append(_line)

    # 有些 mod 写法把 $active 这些开关藏在 VB 的 CommandList 里（Position 节只剩
    # `run = CommandList_VB_…`）。VB 节引用的 CommandList 也要翻一遍，不然 K/L 切换失效。
    for _title, _s2, _e2 in split_sections(text):
        _block = text[_s2:_e2]
        if not _title.strip().lower().startswith('textureoverride'):
            continue
        _low = (_title + _block).lower()
        if mesh_tag not in _low and not any(r in _low for r in res_names):
            continue
        for _raw in _block.splitlines():
            _m = re.match(r'(?i)^\s*run\s*=\s*(\S+)\s*$', _raw)
            if not _m:
                continue
            _name = _m.group(1)
            if 'skin' in _name.lower() or 'settextures' in _name.lower():
                continue
            _cl = split_find_commandlist(text, _name)
            if not _cl:
                continue
            for _l2 in _cl.splitlines():
                _m2 = re.match(r'(?i)^\s*(\$[A-Za-z_]\w*)\s*=\s*(-?\d+)\s*$',
                               _l2.strip())
                if _m2:
                    _line = '{} = {}'.format(_m2.group(1), _m2.group(2))
                    if _line.lower() not in seen_lines:
                        seen_lines.add(_line.lower())
                        assign_lines.append(_line)

    # 原来这节是怎么画的：带数字的 drawindexed 分段 + 段之间的 if/变量开关 + 段间的 run
    # （铃-濛 那种只有一句 drawindexed = auto 的，走下面老路）
    inline_notes = []
    draw_lines = []
    if src_section is not None:
        # 只克隆这一节；`run = CommandList_xxx` 内联成它的内容（已验证写法的 INLINED 做法）
        raw_lines = [l.rstrip() for l in src_section[1].splitlines()
                     if not l.strip().startswith('[')]
        raw_lines = split_inline_commandlists(text, raw_lines, notes=inline_notes)
        for line in raw_lines:
            s = line.strip()
            if not s:
                continue
            if s.startswith(';'):
                if 'MARK:' in s:              # 分隔注释，带上没意义
                    continue
                draw_lines.append(s)          # 其余注释照参照那样保留
                continue
            if re.match(r'(?i)^(?:\$[A-Za-z_]\w*\s*=|hash|handling|vb[012]|ib|draw|'
                        r'match_first_index|match_index_count|Resource_Bak_IB0|'
                        r'override_\w+)\s*=', s):
                continue                      # 每件自己的键 / 开关赋值另行处理
            draw_lines.append(s)
        if not any(re.match(r'(?i)^drawindexed\s*=\s*\d', l) for l in draw_lines):
            draw_lines = []                   # 没有数字分段 -> 按老路一笔一件
    else:
        for title, start, end in split_sections(text):
            block = text[start:end]
            if mesh_tag not in (title + block).lower():
                continue
            lines = [l.strip() for l in block.splitlines()
                     if l.strip() and not l.strip().startswith((';', '#'))]
            if not any(re.match(r'(?i)^drawindexed\s*=\s*\d', l) for l in lines):
                continue
            for line in lines:
                if line.startswith('['):      # 节标题别一起收（收进去会在件里又开一个节）
                    continue
                if re.match(r'(?i)^(hash|handling|vb[012]|ib|match_first_index|match_index_count|'
                            r'Resource_Bak_IB0)\s*=', line):
                    continue
                draw_lines.append(line)
    if draw_lines and not any(re.match(r'(?i)^run\s*=', l) and 'skin' in l.lower()
                              for l in draw_lines):
        draw_lines.insert(0, 'run = CommandListSkinTexture')




    pos_raw = files['position'].read_bytes()
    blend_raw = files['blend'].read_bytes()
    stride_pos = len(pos_raw) // verts
    stride_blend = len(blend_raw) // verts
    # 骨索引从哪份行算：VGX 那步换过一次了，优先用之前的备份（换了就只换一次）
    src_blend_raw = blend_raw
    src_rows = None
    _backup = vgx_backup_of(files['blend'])
    if _backup.exists():
        _raw = _backup.read_bytes()
        if len(_raw) == len(blend_raw):
            src_blend_raw = _raw
            src_rows = load_blend_verts(_backup)

    pieces, dropped_tris, notes = [], 0, list(inline_notes)
    if hit_parts[0] < 0:
        return None, '{}（没归属）'.format(files['blend'].name)
    # 主件 = mod 这条网格的 IB hash 现在指向的那个分量（hash 修复之后的"接班人"，
    # 例：老头发槽 bea4a483 -> 头发 aa9ffb85）；没命中就取最大的那件
    primary = hit_parts[0]
    for r in hit_parts:
        if refs[r]['ib_hash'] and refs[r]['ib_hash'] == str(info.get('ib_hash') or '').lower():
            primary = r
            break
    # texcoord 的源布局 = 这条网格自己那个分量的格式（"顶点格式"那步换过的那份），
    # 件按它逐块对位换算（两边块不一样时不能光按字节数对）
    src_format = tuple(refs[primary]['info']['new_format'])
    # 够大的分量各成一件；小的、没归属的（mod 自己加的件、新版里没有的地方）并进最大的那件
    # "别的网格"的分量：它的 position/blend hash 在这份 ini 里绑着**另一条** buf
    # （比如身体网格的 BelleBodyBlend.buf）—— 这种分量不是本网格该拆出来的件，只当参照用。
    # 铃-夏日休闲：老头发槽里混着一段身体几何，按表会单独成 c2b4ce3a 件；参考产物是并进腿件。
    def _vb_buf_of(hash_value):
        pattern = re.compile(r'(?im)^[ 	]*hash[ 	]*=[ 	]*' + re.escape(hash_value) + r'[ 	]*$')
        for title, start, end in split_sections(text):
            body = text[start:end]
            if not pattern.search(body):
                continue
            vb = re.search(r'(?im)^[ 	]*(vb0|vb2)[ 	]*=[ 	]*(.+?)[ 	]*$', body)
            if not vb:
                # 有些 mod 写法：VB 绑定藏在 CommandList 里
                # （Position 节只剩 `run = CommandList_VB_…`）。不跟进去的话
                # 结构完全一样的分量会被当成"本网格该出的件"，跟另一条网格
                # 抢同一个 VB hash → 谁后写谁赢，另一条网格的绘制就散了
                # （铃-圣诞执行者：身体网格已经占着 c2b4ce3a，头发槽里那段
                #  身体几何又被拆成 c2b4ce3a 件，两条 Position 节同 hash 5838ad30）
                for _run in re.finditer(r'(?im)^[ \t]*run[ \t]*=[ \t]*(\S+)[ \t]*$', body):
                    _cl = split_find_commandlist(text, _run.group(1))
                    if not _cl:
                        continue
                    _vb = re.search(r'(?im)^[ 	]*(vb0|vb2)[ 	]*=[ 	]*(.+?)[ 	]*$', _cl)
                    if _vb:
                        vb = _vb
                        break
            if not vb:
                continue
            definition = find_resource_definition(text, vb.group(2).strip())
            if definition and definition.get('filename'):
                return ini_path.parent / definition['filename']
        return None

    my_bufs = {files['position'].resolve(), files['blend'].resolve()}
    for _extra in (own_bufs or ()):
        try:
            my_bufs.add(Path(_extra).resolve())
        except OSError:
            pass
    other_mesh_refs = set()
    for _ri, _ref in enumerate(refs):
        _bufs = []
        for _key in ('pos_hash', 'blend_hash'):
            _value = str(_ref.get(_key) or '').lower()
            if _value:
                _p = _vb_buf_of(_value)
                if _p is not None:
                    _bufs.append(_p)
        if _bufs and all(p.exists() and p.resolve() not in my_bufs for p in _bufs):
            other_mesh_refs.add(_ri)
    if other_mesh_refs:
        notes.append('{} 是别的网格的分量，只当参照、不单独出件'.format(
            '、'.join(refs[i]['name'] for i in sorted(other_mesh_refs))))

    kept = set()
    for r in hit_parts:
        if r in other_mesh_refs:
            continue
        if r == primary:
            kept.add(r)
            continue
        vset, seen_v = [], set()
        for t, c in enumerate(tri_cls):
            if c != r:
                continue
            for k in tri[t]:
                if k not in seen_v:
                    seen_v.add(k)
                    vset.append(k)
        if not vset:
            continue
        # 面数够（>= SPLIT_SECOND_MIN）就成件；不够的再看它是不是把这个分量整个盖住了
        # —— 耳坠那种：只占本网格 2% 的面，但它就是这个分量的全部，手工拆的 obj 里
        # 它就是单独一件。盖不住才是碎片（并进最大那件）
        if counted.get(r, 0) < len(tri) * SPLIT_SECOND_MIN:
            cover = split_piece_cover(mod_pos, vset, refs[r])
            ref_verts = len(refs[r].get('pos') or ())
            verts_ratio = len(vset) / ref_verts if ref_verts else 0.0
            if cover < SPLIT_PIECE_COVER or verts_ratio < SPLIT_PIECE_MIN_RATIO:
                notes.append('{} 那件只占 {:.0%}、盖住这个分量 {:.0%}（顶点只有它的 {:.1%}），'
                             '并进最近的那件里（不单独出件）'.format(
                                 refs[r]['name'], counted.get(r, 0) / len(tri),
                                 cover, verts_ratio))
                continue
        if split_tex_for(refs[r], raw_tex, verts, per_vertex, src_format)[0] is None:
            notes.append('{} 那件的 texcoord 转不出，并进最近的那件里（不单独出件）'.format(
                refs[r]['name']))
            continue
        kept.add(r)
    if orphan:
        notes.append('mod 自己加的地方有 {} 个顶点（参照里没有）：跟主件走（同一条网格的，别拆散）'.format(
            len(orphan)))

    # 没成件的分量（落到"身体"这种、只盖住一点点、或者 texcoord 转不出的）：
    # 一个面一个面看，它离【成了件的那几件】里哪一件的参照几何最近，就并进那一件。
    # 以前是一律并进"最大的那件"，玲-濛 的两鬓发绺因此并进了腿件、跟着腿动 → 头发断掉；
    # 按最近的来：那撮离头发 0.02~0.09m、离腿 0.28m -> 归头发 ✓；透明猫咪胸口那截离腿最近
    # -> 归腿 ✓ —— 两条都跟已验证产物对得上。
    # 没归属的（mod 自己加的地方，cls < 0）仍然跟主件 —— 这条是作者验证过的。
    kept_order = sorted(kept)
    kept_grid, kept_inv = {}, 1.0 / SPLIT_FAR
    if kept_order:
        for index, r in enumerate(kept_order):
            for p in refs[r]['pos']:
                kept_grid.setdefault(
                    (int(floor(p[0] * kept_inv)), int(floor(p[1] * kept_inv)),
                     int(floor(p[2] * kept_inv))), []).append((index, p))

    def _nearest_kept(cx, cy, cz):
        """离 (cx,cy,cz) 最近的成件那件（格子按半径一层层往外找，找不到给 None）

        主件（这条网格的 hash 指向的那件）跟最近的差不多近时（1.5 倍以内）就取主件 ——
        后脑勺那种"离头发和腿都差不多远"的小条，已验证产物是归头发的。
        """
        if not kept_grid:
            return None
        key = (int(floor(cx * kept_inv)), int(floor(cy * kept_inv)), int(floor(cz * kept_inv)))
        best, best_d2, primary_d2 = None, None, None
        for radius in (1, 2, 4, 8, 16):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    for dz in range(-radius, radius + 1):
                        for index, q in kept_grid.get(
                                (key[0] + dx, key[1] + dy, key[2] + dz), ()):
                            d2 = (q[0] - cx) ** 2 + (q[1] - cy) ** 2 + (q[2] - cz) ** 2
                            if best_d2 is None or d2 < best_d2:
                                best, best_d2 = index, d2
                            if kept_order[index] == primary and (
                                    primary_d2 is None or d2 < primary_d2):
                                primary_d2 = d2
            if best is not None:
                if primary_d2 is not None and primary_d2 <= best_d2 * 2.25:
                    return primary                     # 1.5 倍以内 -> 主件
                return kept_order[best]
        return None

    # 没成件的分量整块（连通块）一起决定去哪儿 —— 一条长头发从头顶垂到地板，按面算会
    # 上半截给头发、下半截给腿，中间就断成切面了。先看这块的票里有没有"成了件的那几件"
    # （有就投给票最多的那件 —— 玲-濛 的两鬓发绺：身体 117 票、头发 110 票，身体没成件，
    #   所以归头发 ✓）；一块票都没有成件的（透明猫咪胸口那截：票全在"身体"上）才按
    # 这块的中心点找最近的参照几何（那截离腿最近 -> 归腿 ✓）。
    # 块里"没成件"类的那部分也要跟着这块的多数走，不能一律掉到主件上 ——
    # 夏音 腰那圈整块是 腿 329 票 / 身体 295 票，身体那部分以前全跟主件（头发），
    # 衣服带子绑到头发骨上，游戏里拉成一根黑刺。
    island_target = {}
    for island_index, votes in enumerate(island_votes):
        pick = island_pick[island_index]
        options = [(r, n) for r, n in (votes or {}).items() if r in kept]
        if pick < 0 or island_index in island_mixed:
            # 票没过半数的块（夏音 腰那圈）：票里有成了件的就跟票最多的那件；
            # 一块票都没有（4 个点的脚踝小零碎那种）也按中心点找最近的成件件，
            # 别一律扔给主件 —— 主件是头发时脚踝那点会被拉到头上去
            if options:
                island_target[island_index] = max(options, key=lambda kv: kv[1])[0]
                continue
            members = island_members[island_index]
            cx = sum(mod_pos[k][0] for k in members) / len(members)
            cy = sum(mod_pos[k][1] for k in members) / len(members)
            cz = sum(mod_pos[k][2] for k in members) / len(members)
            island_target[island_index] = _nearest_kept(cx, cy, cz) or primary
            continue
        if options:
            island_target[island_index] = max(options, key=lambda kv: kv[1])[0]
            continue
        members = island_members[island_index]
        cx = sum(mod_pos[k][0] for k in members) / len(members)
        cy = sum(mod_pos[k][1] for k in members) / len(members)
        cz = sum(mod_pos[k][2] for k in members) / len(members)
        island_target[island_index] = _nearest_kept(cx, cy, cz) or primary

    # 位置撞在一起的，再按【骨索引的表】逐顶点校一次：某件的骨索引表没有权威数据
    # （只有按位置推出来的派生表），而某个顶点的主骨在另一件的权威表里 -> 跟那件走。
    # 夏音/透明猫咪/鲨鲨 的耳坠：旧骨号 27~29 才是耳坠，骨号 30 的是头发（头发表里有 30）。
    # 右耳那簇头发贴在耳坠位置上（距离 0.00mm），光看位置分不开；同一簇里还混着
    # 几个真耳坠的顶点（骨号 27~29），所以按顶点分、不能整块搬。
    piece_tables = {}
    for r in kept:
        entry = vgx_table_for(refs[r])
        piece_tables[r] = set(entry['table']) if entry else None
    bone_target = {}
    rows_src = src_rows or mod_blend           # 表的键是【换之前】的旧骨号
    for island_index in range(len(island_votes)):
        if island_index in earring_islands:
            continue                            # 耳坠块已经定死了，别再按头发表往回拽
        pick = island_pick[island_index]
        if pick not in kept or piece_tables.get(pick) is not None:
            continue
        for k in range(verts):
            if island_of[k] != island_index:
                continue
            weights, bone_ids = rows_src[k]
            slot = max(range(4), key=lambda s: weights[s])
            if weights[slot] < VGX_W_MIN:
                continue
            bone = int(bone_ids[slot])
            for r in kept:
                table = piece_tables.get(r)
                if r != pick and table and bone in table:
                    bone_target[k] = r
                    break

    # 骨号空间纠偏（2026-10-18，铃-制服米塔阴影修复）：
    # 长马尾垂到腿上，按位置会判给腿件，但它的主骨（旧骨号 30）只出现在【头发】
    # 那张旧骨表里。某顶点的主骨在 kept 各件里只被一张表认领 -> 那件才是真归属；
    # 三角里至少两个顶点这么说时以骨头为准（跟上面的 bone_target 同一个裁决处）。
    bone_owner = {}
    for r in kept:
        table = piece_tables.get(r)
        if not table:
            continue
        for bone in table:
            bone_owner.setdefault(bone, set()).add(r)
    for k in range(verts):
        if island_of[k] in earring_islands:
            continue                  # 耳坠块已经定死，别按头发表往回拽
        if earring_ref is not None and island_pick[island_of[k]] == earring_ref:
            continue                  # 归耳坠件的块也别动（夏日 那串骨号 30 的挂件链）
        weights, bone_ids = rows_src[k]
        slot = max(range(4), key=lambda s: weights[s])
        # 只认"这根骨头是主骨且权重够硬"的顶点：权重 0.5 的混权顶点大多挂在
        # 耳坠/挂件链上（夏日 那串），按骨号硬搬会把它们从耳坠件拽走
        if weights[slot] < 0.8:
            continue
        owners = bone_owner.get(int(bone_ids[slot]))
        if owners and len(owners) == 1:
            bone_target.setdefault(k, next(iter(owners)))

    def _final_of(t):
        moved = [bone_target[k] for k in tri[t] if k in bone_target]
        if len(moved) >= 2:
            for cand in moved:
                if moved.count(cand) >= 2:     # 三个顶点里至少两个说同一件
                    return cand
        isl = island_of[tri[t][0]]
        if isl in island_target:
            return island_target[isl]
        c = tri_cls[t]
        return c if c in kept else primary

    final_cls = [_final_of(t) for t in range(len(tri_cls))]

    for r in sorted(kept, key=lambda x: -counted.get(x, 0)):
        ref = refs[r]
        sel = [t for t, c in enumerate(final_cls) if c == r]
        if not sel:
            continue
        vset, seen_v = [], set()
        for t in sel:
            for k in tri[t]:
                if k not in seen_v:
                    seen_v.add(k)
                    vset.append(k)
        if not vset:
            continue
        idx_of = {v: i for i, v in enumerate(vset)}
        new_indices = [idx_of[k] for t in sel for k in tri[t]]

        # 本件在每个原分段里的（个数, 偏移）—— 一个段里这件一个面都没有就注释掉
        tri_off = {}
        _off = 0
        for t in sel:
            tri_off[t] = _off
            _off += 3
        segments = None
        if draw_lines:
            segments = []
            for line in draw_lines:
                match = re.match(r'(?i)^drawindexed\s*=\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*$', line)
                if not match:
                    segments.append(('line', line))
                    continue
                first = int(match.group(2)) // 3
                count = int(match.group(1)) // 3
                got = 0
                start = 0
                for t in range(first, min(first + count, len(tri))):
                    pos = tri_off.get(t)
                    if pos is None:
                        continue
                    if got == 0:
                        start = pos
                    got += 3
                segments.append(('draw', got, start, line))



        # 骨索引：这一件属于哪个分量，就套哪个分量的表，**只套一次**。
        # 行从 VGX 之前那份（.vgx_BACKUP.buf）拿 —— 拿现在这份再套一遍就是换两次了。
        # 这个分量没有表（耳坠 07920753 这种）就按参照 dump 推一张：把这一件的顶点跟
        # 那个分量的 dump 顶点按位置+权重配对，推老索引 -> 新索引。已验证产物
        # 耳坠就是这个值（跟游戏自己的耳坠数据一致）；不推的话骨号留在老空间里，
        # 在耳坠那一笔里是越界的，几何会拉成一个空壳。
        entry = vgx_table_for(ref)
        rows_raw = src_blend_raw
        if entry:
            table = dict(entry['table'])
            bone_how = '用表〔{}〕'.format(entry['name'])
            # 表里没有、又超出目标骨盘范围的旧骨号（布料/裙摆骨 87/90 这种）：
            # 统一 clamp 到一根骨会跟原地不动的骨混在一起，模型拉成扇形。
            # 这些骨按参照推一条给它们（铃-动态 的裙摆）
            _pmax = 0
            for _w, _b in (ref.get('blend') or []):
                for _s in range(4):
                    if _w[_s] > 0.01 and int(_b[_s]) > _pmax:
                        _pmax = int(_b[_s])
            _rows_t = src_rows or mod_blend
            _need = set()
            for k in vset:
                _w, _b = _rows_t[k]
                _s = max(range(4), key=lambda j: _w[j])
                _old = int(_b[_s])
                if _w[_s] >= VGX_W_MIN and _old not in table and _old > _pmax:
                    _need.add(_old)
            if _need:
                _derived, _ratio = split_dominant_map(
                    [_rows_t[k] for k in vset], [mod_pos[k] for k in vset], ref)
                if _derived and _ratio >= SPLIT_DERIVE_MIN:
                    _added = 0
                    for _old in _need:
                        if _old in _derived:
                            table[_old] = _derived[_old]
                            _added += 1
                    if _added:
                        bone_how += ' + 参照补{}条'.format(_added)
        else:
            _rows = src_rows or mod_blend
            derived, _ratio = split_dominant_map(
                [_rows[k] for k in vset], [mod_pos[k] for k in vset], ref)
            if derived and _ratio >= SPLIT_DERIVE_MIN:
                table = derived
                bone_how = '按参照推〔{} 条，配对 {:.0%}〕'.format(len(derived), _ratio)
            else:
                table = {}
                bone_how = '不动'
                rows_raw = blend_raw     # 没表也推不出来：用当前行（VGX 那步换过的）
        changed = {o: n for o, n in table.items() if o != n}
        cover = split_piece_cover(mod_pos, vset, ref)
        tex_new, stride_tex = split_tex_for(ref, raw_tex, verts, per_vertex, src_format)
        if tex_new is None:
            return None, '{}（切给"{}"那件：{}）'.format(
                files['texcoord'].name, ref['name'], stride_tex)

        pos_out = bytearray()
        blend_out = bytearray()
        # 这件骨盘里最大到几号：表里没映射到的旧骨号如果超出这个范围（耳坠件只有 0~3，
        # 挂件链上却是 30），游戏里就是越界骨号，顶点会塌成一团 —— 统一收到表里最常见的目标号
        palette_max = 0
        for weights_ref, bones_ref in (ref.get('blend') or []):
            for slot_ref in range(4):
                if weights_ref[slot_ref] > 0.01 and int(bones_ref[slot_ref]) > palette_max:
                    palette_max = int(bones_ref[slot_ref])
        clamp_to = None
        if table:
            counts = {}
            for vv in table.values():
                counts[vv] = counts.get(vv, 0) + 1
            clamp_to = max(counts, key=lambda kk: counts[kk])
        for k in vset:
            pos_out += pos_raw[k * stride_pos:(k + 1) * stride_pos]
            row = bytearray(rows_raw[k * stride_blend:(k + 1) * stride_blend])
            for slot in range(4):
                off = 16 + slot * 4
                value = struct.unpack_from('<I', row, off)[0]
                if value in table:
                    struct.pack_into('<I', row, off, table[value])
                elif clamp_to is not None and value > palette_max:
                    struct.pack_into('<I', row, off, clamp_to)
            blend_out += row
        tex_out = bytearray()
        for k in vset:
            tex_out += tex_new[k * stride_tex:(k + 1) * stride_tex]
        ib_out = struct.pack('<{}I'.format(len(new_indices)), *new_indices)

        pieces.append(dict(
            ref_i=r, ref=ref, verts=len(vset), indices=len(new_indices), tris=len(sel),
            position=bytes(pos_out), texcoord=bytes(tex_out), blend=bytes(blend_out),
            ib=ib_out, stride_tex=stride_tex, table=table, changed=changed, bone_how=bone_how,
            cover=cover, segments=segments, ps_lines=ps_lines, ps_ib_at=ps_ib_at,
            assign_lines=assign_lines, vset=list(vset),
            filter_index=filter_index, vlr_lines=vlr_lines,
            pos_lines=pos_lines, tex_lines=tex_lines,
            blend_lines=blend_lines, ib_lines=ib_lines,
            draw_in_blend=draw_in_blend, draw_if=draw_if))

    if not pieces:
        return None, '{}（切出来一件都不剩，跳过）'.format(files['blend'].name)

    name = files['blend'].stem
    if name.lower().endswith('blend'):
        name = name[:-5]
    name = name.strip('-_ .')                  # 分隔符去掉，件名统一（bea4a483- -> bea4a483）
    _hashes = [refs[primary].get(key) for key in
               ('pos_hash', 'tex_vb_hash', 'blend_hash', 'draw_hash', 'ib_hash')]
    return dict(ini=ini_path, files=files, refs=refs, pieces=pieces, name=name, notes=notes,
                merge_guard=split_namespace_guard(text),
                required_texture=split_required_texture_binds(
                    text, src_section[1] if src_section is not None else ''),
                pos_variants=split_position_variants(text, ini_path, files, verts, mesh_tag),
                verts=verts, tris=len(tri), dropped_tris=dropped_tris,
                far_verts=sum(1 for c in cls if c < 0), paired=paired,
                old_sections=split_section_lines(text, name, files, _hashes)), None


def split_plan(target: Path):
    """返回 (items, skipped, error)：每个要拆的网格一条（还没写盘）"""
    items, skipped = [], []
    ini_paths = find_ini_files(target)
    if not ini_paths:
        return [], skipped, '这个文件夹里没找到 .ini'
    if not DUMP_MESHES:
        return [], skipped, '没读进参照 dump —— 先在左边"选择 dump 文件夹"选一份新版本的抓包'
    allowed_groups = split_allowed_groups()
    if not allowed_groups:
        return [], skipped, '参照组不在拆分名单（只拆：{}），跳过拆分步骤'.format(
            '、'.join(SPLIT_REF_GROUPS))
    refs = split_refs(allowed_groups)
    if not refs:
        return [], skipped, '参照 dump 里缺 Position.buf / Blend.buf，拆不了'
    thin_refs = [info for info in DUMP_MESHES.values()
                 if character_of(info) in allowed_groups
                 and not (info.get('position_buf') and info.get('blend_buf'))]
    nearest = split_pick(refs)
    hit, _which = mod_ref_hit(target, active_ref_hashes())
    if not hit:
        return [], skipped, 'mod 的 ini 里没有一个 hash 属于本次参照【{}】'.format(ref_scope_text())

    # 跨 ini 去重：同一个网格的 blend 可能被主 ini + 菜单 ini 同时引用，
    # seen 放在 ini 循环里面会让它被拆两次。
    seen = set()
    for ini_path in ini_paths:
        try:
            text = ini_path.read_text(encoding='utf-8', errors='replace')
        except OSError:
            continue
        for info in DUMP_MESHES.values():
            if character_of(info) not in allowed_groups:
                continue
            cand = vgx_auto_candidate(ini_path, text, info)
            if not cand:
                continue
            blend_path, _pos_path = cand
            key = str(blend_path.resolve())
            if key in seen:
                continue
            files = split_mesh_files(blend_path, ini_path, text, str(info.get('ib_hash') or ''))
            if not files:
                skipped.append('{}（找不到配套的 Position/Texcoord/索引）'.format(blend_path.name))
                continue
            mod_pos = load_positions(files['position'])
            mod_blend = load_blend_verts(files['blend'])
            mod_ib = split_read_ib(files['ib'])
            if not mod_pos or not mod_blend or not mod_ib:
                skipped.append('{}（顶点或索引读不出来）'.format(blend_path.name))
                continue
            if len(mod_pos) != len(mod_blend):
                skipped.append('{}（Position {} 顶点 / Blend {} 顶点 对不上）'.format(
                    blend_path.name, len(mod_pos), len(mod_blend)))
                continue
            item, why = split_analyse(ini_path, text, files, refs, nearest,
                                      mod_pos, mod_blend, mod_ib, info)
            if why:
                skipped.append(why)
            elif item:
                items.append(item)
                seen.add(key)          # 真的出计划了才占坑，失败留给后面的 ini 重试

        # 文件名不是 .buf 结尾的 mod（UUID.assets 这种）：按 ini 资源组找网格。
        # 只认绘制节 hash 命中参照分量的 —— 皮肤专用分量（dump 里没有）不拆，
        # 否则会把整身皮肤按原皮分量切开。
        ref_ib_hashes = {str(r.get('ib_hash') or '').lower()
                         for r in refs if r.get('ib_hash')}
        for group in ini_resource_groups_cached(ini_path, text):
            if not all(kind in group for kind in ('position', 'blend', 'texcoord', 'ib')):
                continue
            ib_name = group['ib']['name']
            pattern = re.compile(r'(?im)^\s*ib\s*=\s*' + re.escape(ib_name) + r'\s*$')
            comp_hash = None
            for _title, _s0, _e0 in split_sections(text):
                _body = text[_s0:_e0]
                if not pattern.search(_body):
                    continue
                _m = HASH_LINE_RE.search(_body)
                if _m:
                    comp_hash = _m.group(1).lower()
                    break
            if not comp_hash or comp_hash not in ref_ib_hashes:
                continue
            files = {kind: group[kind]['path']
                     for kind in ('position', 'blend', 'texcoord', 'ib')}
            key = str(files['blend'].resolve())
            if key in seen:
                continue
            mod_pos = load_positions(files['position'])
            mod_blend = load_blend_verts(files['blend'])
            mod_ib = split_read_ib(files['ib'])
            if not mod_pos or not mod_blend or not mod_ib:
                skipped.append('{}（顶点或索引读不出来）'.format(files['blend'].name))
                continue
            if len(mod_pos) != len(mod_blend):
                skipped.append('{}（Position {} 顶点 / Blend {} 顶点 对不上）'.format(
                    files['blend'].name, len(mod_pos), len(mod_blend)))
                continue
            item, why = split_analyse(ini_path, text, files, refs, nearest,
                                      mod_pos, mod_blend, mod_ib, {'ib_hash': comp_hash})
            if why:
                skipped.append(why)
            elif item:
                items.append(item)
                seen.add(key)          # 同上：出计划才占坑

        # 这个 ini 一个网格都没配上？看看是不是 hash 指到了没有 Position/Blend 的分量
        if not any(str(x['ini']) == str(ini_path) for x in items) and thin_refs:
            for info in thin_refs:
                if vgx_auto_candidate(ini_path, text, info):
                    skipped.append('{}：ini 里的 hash 指到{}这个分量，但它没有 Position/Blend'
                                   '（多半是发夹/耳坠这类小件）—— hash 修错了，先把 hash 改对'
                                   '（头发应指 头发 那个分量）再拆'.format(
                                       ini_path.name, info.get('character')))
                    break

    error = None
    if not items and not skipped:
        error = ('没有需要拆的网格 —— 每个网格都只落在一个分量上；'
                 '或者是这个网格的 hash 还是旧的（先跑【版本Hash修复】）')
    return items, skipped, error


def split_report(item):
    """一条拆分计划的报告文字"""
    lines = ['- [拆分] "{}"  {} 顶点 / {} 三角'.format(item['files']['blend'], item['verts'], item['tris'])]
    for piece in item['pieces']:
        lines.append('        切给 {}：顶点 {} / 索引 {}（骨索引 {} → 改 {} 条；'
                     '盖住那个分量 {:.0%}）'.format(
                         piece['ref']['name'], piece['verts'], piece['indices'],
                         piece.get('bone_how', '?'), len(piece['changed']),
                         piece.get('cover', 0.0)))
        if piece['verts'] > SPLIT_VC_WARN:
            lines.append('          ! 这件顶点 {} 超过 {}，进游戏可能超出顶点上限'.format(
                piece['verts'], SPLIT_VC_WARN))
    for note in item.get('notes', []):
        lines.append('        {}'.format(note))
    return lines


def split_piece_prefixes(item):
    """给每个件算唯一前缀。

    正常情况保持原来的 `<网格名>_<ib hash>`，只有两个件撞同一个前缀时才加
    tex hash / 序号。这样已有产物名字不变，只有真正同 ib 不同 tex 的件才改名。
    """
    pieces = item['pieces']
    bases = []
    for piece in pieces:
        ref = piece.get('ref') or {}
        bases.append('{}_{}'.format(
            item['name'], ref.get('ib_hash') or ref.get('tex_hash') or 'part'))

    counts = {}
    for base in bases:
        counts[base] = counts.get(base, 0) + 1

    used = set()
    result = []
    for piece, base in zip(pieces, bases):
        if counts.get(base, 0) <= 1:
            prefix = base
            if prefix in used:
                number = 2
                while '{}__{}'.format(base, number) in used:
                    number += 1
                prefix = '{}__{}'.format(base, number)
        else:
            tex_hash = str((piece.get('ref') or {}).get('tex_hash') or '')
            candidate = '{}_{}'.format(base, tex_hash) if tex_hash else base
            prefix = candidate
            number = 2
            while prefix in used or prefix in counts:
                prefix = '{}__{}'.format(candidate, number)
                number += 1
        used.add(prefix)
        result.append(prefix)
    return result


def split_apply(planned, total=None, done0=0):
    # 先把每件的文件名算好（不写盘），再整体自检 —— 不过就一个文件都不写。
    # 数据不对 / 节结构不对（孤立 elif、this=、drawindexed 越界）在这里拦下来，
    # 而不是写进 mod 里再进游戏看截图。
    for item in planned:
        ini_path = item['ini']
        prefixes = split_piece_prefixes(item)
        for piece, prefix in zip(item['pieces'], prefixes):
            piece['prefix'] = prefix
            names, paths = {}, {}
            for kind, suffix in (('position', 'Position'), ('texcoord', 'Texcoord'),
                                 ('blend', 'Blend')):
                path = item['files'][kind].with_name(prefix + suffix + '.buf')
                paths[kind] = path
                # 按 ini 所在目录写相对路径：网格在子目录里（Mesh\xxx.buf）时只写文件名找不到
                names[kind] = split_rel_path(path, ini_path.parent)
            path = item['files']['ib'].with_name(prefix + 'Head.ib')
            paths['ib'] = path
            names['ib'] = split_rel_path(path, ini_path.parent)
            piece['prefix'] = prefix
            piece['files_out'] = names
            piece['_paths'] = paths
            # 合并版 mod：同一个件按变体各出一份 Position（.0/.1 形状不同）
            if item.get('pos_variants'):
                variants = []
                for variant in item['pos_variants']:
                    path = item['files']['position'].with_name(
                        '{}Position.v{}.buf'.format(prefix, variant['num']))
                    variants.append(dict(
                        num=variant['num'], path=path, src=variant['path'],
                        name=split_rel_path(path, ini_path.parent),
                        res='Resource{}Position.v{}'.format(prefix, variant['num'])))
                piece['_pos_variants'] = variants
    problems = split_validate(planned)
    if problems:
        for line in problems:
            print(c('  ! 自检不过：{}'.format(line), Style.RED))
        print(c('拆分已中止，没有写任何文件（请把这段报告发我）。', Style.RED))
        return False

    for index, item in enumerate(planned, 1):
        ini_path = item['ini']
        text = ini_path.read_text(encoding='utf-8', errors='replace')
        created = []

        for piece in item['pieces']:
            names = piece['files_out']
            paths = piece['_paths']
            for kind in ('position', 'texcoord', 'blend'):
                if kind == 'position' and piece.get('_pos_variants'):
                    continue          # 每个变体各写一份，见下
                paths[kind].write_bytes(piece[kind])
                created.append(names[kind])
            for variant in piece.get('_pos_variants') or ():
                source = variant['src'].read_bytes()
                data = bytearray()
                for k in piece['vset']:
                    data += source[k * 40:(k + 1) * 40]
                variant['path'].write_bytes(bytes(data))
                created.append(variant['name'])
            paths['ib'].write_bytes(piece['ib'])
            created.append(names['ib'])
            # 件里的骨索引/texcoord 切的时候已经一次到位（行取自 .vgx_BACKUP、按目标格式重排），
            # 放上"已修"标记 —— 以后再对同一个 mod 跑工具（比如换参照组补修脸），
            # 不会对着件再套一次表（骨索引二次映射会转两圈，模型就错位了）
            for kind, marker in (('blend', vgx_marker_of),
                                 ('texcoord', tex_marker_of)):
                marker_path = marker(paths[kind])
                marker_path.write_text('', encoding='utf-8')
                created.append(split_rel_path(marker_path, ini_path.parent))

        # 先把"新写了哪些文件"记下来 —— 万一后面 ini 那步出错，还原也删得掉
        manifest = ini_path.parent / SPLIT_CREATED
        try:
            data = json.loads(manifest.read_text(encoding='utf-8'))
            if not isinstance(data.get('files'), list):
                data['files'] = []
        except Exception:
            data = {'files': []}
        for name in created:
            if name not in data['files']:
                data['files'].append(name)
        manifest.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')

        # ini：旧节注释掉 + 末尾补新节
        out_lines = []
        title_now = None
        old = {t.lower() for t in item['old_sections']}
        # 掐笔那步先跑，会给"mod 盖住了"的分量各写一个 ModOff 掐笔节；
        # 这些分量现在拆成件了，件自己 handling = skip + 显式 drawindexed 就够 ——
        # 再留一个同 hash 的掐笔节就是重复（已验证产物里没有），一起注释掉
        piece_ib = {str(p['ref']['ib_hash'] or '').lower() for p in item['pieces']}
        piece_ib.discard('')
        drop_titles = set()
        for title, start, end in split_sections(text):
            low = title.strip().lower()
            if 'modoff' not in low:
                continue
            body = text[start:end]
            # 带 match_first_index 的是"只掐某一段"（多段分量），别动 ——
            # 件只画自己那一段，别的段还得靠它掐
            if re.search(r'(?im)^\s*match_first_index\s*=', body):
                continue
            for line in body.splitlines():
                m = re.match(r'(?i)^\s*hash\s*=\s*(\w+)', line)
                if m and m.group(1).lower() in piece_ib:
                    drop_titles.add(low)
                    break
        for line in text.splitlines():
            match = re.fullmatch(r'\s*\[(.+)\]\s*', line)
            if match:
                title_now = match.group(1).strip()
            if title_now and (title_now.lower() in old or title_now.lower() in drop_titles):
                out_lines.append('; ' + line)          # 注释掉旧节（不删，方便还原/对照）
            else:
                out_lines.append(line)
        # 件里靠 "Resource_Bak_IB0 = ref ib / ib = Resource_Bak_IB0" 存一下再还回来；
        # ini 里没有这个定义的话游戏里就是一堆红字（资源找不到）—— 没有就补一个
        if not re.search(r'(?im)^\s*\[\s*Resource_Bak_IB0\s*\]\s*$', text):
            out_lines += ['', '[Resource_Bak_IB0]']
        for piece in item['pieces']:
            prefix = piece['prefix']
            block = piece.get('_block')
            if block is None:
                block = split_wrap_namespace(
                    split_piece_block(prefix, piece['ref'], piece),
                    item.get('merge_guard'))
            out_lines += block
        # 没拆出东西的分量【不掐】——那些分量的顶点缓冲本工具没覆盖，
        # 游戏照自己原样画就是对的（掐了会出现"脸没了"这类事故）。
        ini_backup = Path(str(ini_path) + TEX_INI_BACKUP_SUFFIX)
        if not ini_backup.exists():
            ini_backup.write_bytes(ini_path.read_bytes())
        ini_path.write_text('\n'.join(out_lines) + '\n', encoding='utf-8')

        report = ini_path.parent / 'split报告.txt'
        report.write_text('\n'.join(split_report(item)), encoding='utf-8')
        print(c('已拆: "{}"  {} 件（{}）'.format(
            ini_path.name, len(item['pieces']),
            '、'.join(p['ref']['name'] for p in item['pieces'])), Style.GREEN))
        iv_progress(done0 + index, total or len(planned), ini_path.name)
    return True


def stale_auto_in_split(target: Path, verdict=True):
    """拆分模式里也做一遍 auto 自检（正常流程在修复那步已经做过，这里为空）"""
    auto_items, _skipped, auto_error = stale_auto_plan(target)
    if auto_error:
        print(c('（{}）'.format(auto_error), Style.YELLOW))
    if not auto_items:
        return 0
    print('===== 整条 auto 绘制（换成 mod 自己的 IB） =====')
    for item in auto_items:
        for line in item.get('lines', []):
            print(line)
    print()
    if not iv_asker().confirm('将改写 {} 个 ini 的 auto 绘制（改前备份）'.format(len(auto_items))):
        print(c('已跳过 auto 绘制改写。', Style.YELLOW))
        return 0
    stale_auto_apply(auto_items, len(auto_items))
    return len(auto_items)


def apply_split(target: Path, verdict=True):
    """网格拆分修复：计划 -> 打印 -> 确认 -> 写盘"""
    # 先看参照组在不在拆分名单里。不在就整段跳过，连拆分里的 auto 自检也不跑；
    # 正常流程前面 apply_fix 已经做过 auto 自检。
    allowed_groups = split_allowed_groups()
    if DUMP_MESHES and not allowed_groups:
        message = '参照组不在拆分名单（只拆：{}），跳过拆分步骤'.format(
            '、'.join(SPLIT_REF_GROUPS))
        print(c(message, Style.YELLOW))
        return dict(items=0, changed=False, cancelled=False, error=message)
    # 单独跑拆分模式时也要先过表校验；正常流程里 apply_fix 已经验过，
    # 这里再验一次只是多几毫秒，但能堵住“上一步中止、拆分照写”的漏洞。
    if not validate_vgx() or not validate_texcoord():
        print()
        print(c('表里有写错的地方，先改好再跑。已中止。', Style.RED))
        return dict(items=0, changed=False, cancelled=False,
                    aborted=True, error='表校验失败')
    print('===== 四、网格拆分修复 =====')
    items, skipped, error = split_plan(target)
    if error:
        print(c('（{}）'.format(error), Style.YELLOW))
    for line in skipped:
        print(c('  ! {}'.format(line), Style.YELLOW))
    if not items:
        printed = False
        if error and '没有需要拆的网格' not in error:
            print(c('（{}）'.format(error), Style.YELLOW))
            printed = True
        auto_done = stale_auto_in_split(target, verdict)
        if verdict and not printed:
            print(c('结论：这个 mod 不需要拆分（没有需要拆的网格）。', Style.YELLOW))
        return dict(items=0, changed=bool(auto_done), cancelled=False, error=error or '')
    for item in items:
        for line in split_report(item):
            print(line)
    print()
    summary = '将拆分 {} 个网格（新写的文件 + 改 ini，改前都备份）'.format(len(items))
    if not iv_asker().confirm(summary):
        print(c('已取消，没有改动任何文件。', Style.YELLOW))
        return dict(items=0, changed=False, cancelled=True, error='')
    print()
    print('拆分中...')
    if not split_apply(items, len(items), 0):
        return dict(items=0, changed=False, cancelled=False, error='自检没过，已中止')
    auto_done = stale_auto_in_split(target, verdict)
    print()
    if verdict:
        print(c('结论：已拆分 {} 个网格。'.format(len(items)), Style.GREEN))
        print(c('完成! 新文件就写在 mod 目录里；点"还原"会删掉它们并把 ini 退回去。', Style.GREEN))
    return dict(items=len(items), changed=True, cancelled=False, error='')


# ==========================================================================
#  五、掐掉多余的那几笔（原版分量 / 索引段）
#
#  游戏更新把老的一条网格拆成好几条分量后，老 mod 只认其中一条：剩下那些要么
#  原版照画（mod 的网格其实已经盖到它了 -> 同一块地方画两遍），要么是 mod 那条
#  IB 里多出来的索引段（第 2 段起没写 match_first_index -> 拿 mod 的顶点去画原版
#  那一笔，多半糊成一团）。已验证产物就是这么动的：给耳坠 07920753、发夹
#  3acf9aea 各出一节 handling = skip，给身体 IB 的第 2 段（31275）出一节点名
#  match_first_index = 31275 的 skip。
#
#  判定（只看本次参照 dump + mod 自己的 ini，不猜）：
#    A 原版分量：该分量的 position / texcoord / blend / 顶点上限 / IB 五个 hash
#       在 mod 的所有 ini 里一个都没出现，而它的顶点有 SUPPRESS_COVER 以上能在
#       SUPPRESS_NEAR 内被 mod 的某条网格盖上 -> mod 画的就是它，出
#       hash = 该分量 IB hash 的一节 handling = skip，免得原版那笔也画一遍
#    B 索引段：mod 认了这个分量（ini 里有一节带 match_first_index，是自己画的），
#       但 dump 里它还有别的段（首个索引 != 0），mod 的 ini 里没有任何一节的
#       match_first_index 指着它 -> 出 hash = 该分量 IB hash + match_first_index =
#       那一段 的一节 handling = skip
#
#  只动 ini（备份 .texfmt.bak，跟"顶点格式 / 顶点上限"共用同一份），
#  改哪个 ini、为什么都打在报告里；分量连位置 buf 都没有就整条跳过，宁可不掐。
# ==========================================================================

SUPPRESS_COVER = 0.30        # 分量被 mod 网格盖上的比例，超过这个才敢掐原版那一笔
SUPPRESS_NEAR = 0.010        # "盖上"的判定半径（米）
SUPPRESS_LIMIT = 12          # 一次最多掐几笔（再多多半是参照选错了，只报告不动手）


def suppress_refs():
    """掐笔只认位置：参照分量有位置 buf 就够（小分量的 blend 步幅不是 32，不让它卡住）"""
    refs = []
    for tex_hash, info in sorted(DUMP_MESHES.items()):
        if not info.get('position_buf'):
            continue
        pos = load_positions(Path(info['position_buf']))
        if not pos:
            continue
        refs.append({
            'name': info.get('segment') or info.get('character') or '?',
            'pos': pos,
            'ib_hash': str(info.get('ib_hash') or '').lower(),
            'first': info.get('first_index'), 'count': info.get('index_count'),
            'draw_hash': str(info.get('draw_hash') or '').lower(),
            'pos_hash': str(info.get('position_hash') or '').lower(),
            'tex_vb_hash': str(info.get('texcoord_hash') or tex_hash).lower(),
            'blend_hash': str(info.get('blend_hash') or '').lower(),
        })
    return refs


def suppress_sections(text):
    """带 hash / match_first_index 的节 -> [(title, body)]，只看真行"""
    out = []
    for title, start, end in split_sections(text):
        body = text[start:end]
        lines = [l.strip() for l in body.splitlines()
                 if l.strip() and not l.strip().startswith((';', '#', '['))]
        out.append((title, lines))
    return out


def suppress_mod_meshes(target: Path):
    """mod 里所有顶点缓冲 -> [(buf 路径, [(x,y,z)…])]（按文件名 + ini 资源节认）"""
    out = []
    seen = set()
    for path in sorted(target.rglob('*.buf')):
        low = path.name.lower()
        if 'backup' in low or '.bak' in low or not low.endswith('position.buf'):
            continue
        pos = load_positions(path)
        if pos:
            out.append((path, pos))
            seen.add(path.resolve())
    # 文件名不是 .buf 结尾的（UUID.assets 这种）：按 ini 资源节找 position 缓冲
    for ini_path in find_ini_files(target):
        try:
            text = ini_path.read_text(encoding='utf-8', errors='replace')
        except OSError:
            continue
        for group in ini_resource_groups_cached(ini_path, text):
            item = group.get('position')
            if not item:
                continue
            try:
                resolved = item['path'].resolve()
            except OSError:
                continue
            if resolved in seen:
                continue
            pos = load_positions(item['path'])
            if pos:
                out.append((item['path'], pos))
                seen.add(resolved)
    return out


def suppress_grid(meshes):
    """把所有 mod 网格的顶点建成格子索引 -> nearest(p) 返回 (网格下标, 距离)；没盖上返回 (-1, 距离)"""
    inv = 1.0 / SUPPRESS_NEAR
    grid = {}
    for mesh_index, (_path, pos) in enumerate(meshes):
        for p in pos:
            key = (int(floor(p[0] * inv)), int(floor(p[1] * inv)), int(floor(p[2] * inv)))
            cell = grid.get(key)
            if cell is None:
                grid[key] = [(mesh_index, p)]
            else:
                cell.append((mesh_index, p))
    offsets = [(dx, dy, dz) for dx in (-1, 0, 1) for dy in (-1, 0, 1) for dz in (-1, 0, 1)]

    def nearest(p, limit=SUPPRESS_NEAR):
        key = (int(floor(p[0] * inv)), int(floor(p[1] * inv)), int(floor(p[2] * inv)))
        best_mesh, best_d2 = -1, limit * limit
        for dx, dy, dz in offsets:
            items = grid.get((key[0] + dx, key[1] + dy, key[2] + dz))
            if not items:
                continue
            for mesh_index, q in items:
                d2 = ((q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2 + (q[2] - p[2]) ** 2)
                if d2 <= best_d2:
                    best_mesh, best_d2 = mesh_index, d2
        return best_mesh, best_d2 ** 0.5

    return nearest


def buf_ini_of(buf: Path, texts: dict, inis: list):
    """这份顶点缓冲是哪份 ini 里的（按 filename 行找；找不到就用同目录那份 ini）"""
    name = buf.name.lower()
    for ini_path, text in texts.items():
        for line in text.splitlines():
            s = line.strip()
            if s.startswith((';', '#')) or not s:
                continue
            match = re.match(r'(?i)^filename\s*=\s*(.+)$', s)
            if match and Path(match.group(1).strip().replace('\\', '/')).name.lower() == name:
                return ini_path
    same = [p for p in inis if p.parent == buf.parent]
    return same[0] if same else None


def suppress_plan(target: Path):
    """(items, skipped, error)：每个 ini 里要追加的掐笔节（只增不改）"""
    refs = suppress_refs()
    if not refs:
        return [], [], '没有可用的参照 dump（没选参照 / 参照里没有位置缓冲）'
    meshes = suppress_mod_meshes(target)
    if not meshes:
        return [], [], 'mod 里没找到 Position 顶点缓冲'
    nearest = suppress_grid(meshes)

    inis = find_ini_files(target)
    if not inis:
        return [], [], '这个文件夹里没找到 .ini'
    texts = {}
    for ini_path in inis:
        try:
            texts[ini_path] = ini_path.read_text(encoding='utf-8', errors='replace')
        except OSError:
            continue
    parsed = {path: suppress_sections(text) for path, text in texts.items()}

    def mentions(value):
        """这个 hash 在 mod 的某个 ini 里出现过吗 -> 那份 ini（只看真行）"""
        if not value:
            return None
        for ini_path, sections in parsed.items():
            for _title, lines in sections:
                for line in lines:
                    if re.match(r'(?i)^hash\s*=\s*' + re.escape(value) + r'$', line):
                        return ini_path
        return None

    def draw_claim(ib_hash):
        """mod 里有没有一节自己画这个分量（带 match_first_index 的节）"""
        if not ib_hash:
            return False
        for _ini_path, sections in parsed.items():
            for _title, lines in sections:
                if any(re.match(r'(?i)^hash\s*=\s*' + re.escape(ib_hash) + r'$', l) for l in lines) \
                        and any(re.match(r'(?i)^match_first_index\s*=', l) for l in lines):
                    return True
        return False

    def claimed(ib_hash, first):
        """这个分量的这一段，mod 的 ini 里有没有一节 match_first_index 指着它"""
        for _ini_path, sections in parsed.items():
            for _title, lines in sections:
                if any(re.match(r'(?i)^hash\s*=\s*' + re.escape(ib_hash) + r'$', l) for l in lines) \
                        and any(re.match(r'(?i)^match_first_index\s*=\s*' + str(first) + r'$', l)
                                for l in lines):
                    return True
        return False

    additions = []          # (ini, ib hash, 索引段起点或 None, 说明)
    skipped = []
    for ref in refs:
        ib = ref['ib_hash']
        if not ib or not ref['pos']:
            continue
        owner = None
        for value in (ref['pos_hash'], ref['tex_vb_hash'], ref['blend_hash'],
                      ref['draw_hash'], ib):
            owner = mentions(value)
            if owner:
                break

        if owner is not None:
            first = ref['first'] if ref['first'] is not None else 0
            if first == 0 or not draw_claim(ib) or claimed(ib, first):
                continue
            additions.append((owner, ib, first, '{}（mod 认了这条分量，但第 {} 个索引起点那一段没人管）'
                              .format(ref['name'], first)))
            continue

        counts = {}
        covered = 0
        for p in ref['pos']:
            mesh_index, _d = nearest(p)
            if mesh_index < 0:
                continue
            covered += 1
            counts[mesh_index] = counts.get(mesh_index, 0) + 1
        ratio = covered / len(ref['pos'])
        if ratio < SUPPRESS_COVER:
            skipped.append('{}（只有 {:.0%} 的顶点盖得住，不掐）'.format(ref['name'], ratio))
            continue
        mesh_index = max(counts, key=lambda k: counts[k])
        buf = meshes[mesh_index][0]
        ini_path = buf_ini_of(buf, texts, inis)
        if ini_path is None:
            skipped.append('{}（{} 归哪份 ini 认不出来，不掐）'.format(ref['name'], buf.name))
            continue
        additions.append((ini_path, ib, None,
                          '{}（mod 的网格"{}"盖住了它 {:.0%}，原版那一笔会画两遍）'
                          .format(ref['name'], buf.name, ratio)))

    if len(additions) > SUPPRESS_LIMIT:
        return [], skipped, ('要掐 {} 笔，太多了 —— 多半是参照 dump 选错了组，先看参照再重跑'
                             .format(len(additions)))

    items = []
    for ini_path, ib, first, why in additions:
        name = 'TextureOverrideModOff{}'.format(ib)
        if first is not None:
            name += 'At{}'.format(first)
        head = '' if first is None else 'match_first_index = {}\n'.format(first)
        text = ('\n; 掐掉多余的那一笔：{}\n[{}]\nhash = {}\n{}handling = skip\n'
                .format(why, name, ib, head))
        item = next((it for it in items if it['ini'] == ini_path), None)
        if item is None:
            item = dict(ini=ini_path, text='', lines=[])
            items.append(item)
        item['text'] += text
        item['lines'].append('- [掐笔] "{}"  {}'.format(ini_path.name, why))
    return items, skipped, None


def suppress_apply(planned, total=None, done0=0):
    for index, item in enumerate(planned, 1):
        ini_path = item['ini']
        ini_backup = Path(str(ini_path) + TEX_INI_BACKUP_SUFFIX)
        if not ini_backup.exists():
            ini_backup.write_bytes(ini_path.read_bytes())
        with ini_path.open('a', encoding='utf-8') as handle:
            handle.write(item['text'])
        print(c('已修 [掐笔]: "{}"  {} 笔'.format(ini_path.name, len(item['lines'])), Style.GREEN))
        iv_progress(done0 + index, total or len(planned), ini_path.name)
# ==========================================================================
#  六、还原
# ==========================================================================

def restore(target: Path):
    """把本工具改过的文件按备份退回（VGX + 格式 一起）"""
    buf_backups = []
    for suffix in (VGX_BACKUP_SUFFIX, TEX_BACKUP_SUFFIX, TEX_LEGACY_BACKUP_SUFFIX):
        buf_backups.extend(sorted(target.rglob('*' + suffix)))
    ini_backups = []
    for suffix in (TEX_INI_BACKUP_SUFFIX, TEX_LEGACY_INI_BACKUP_SUFFIX):
        ini_backups.extend(sorted(target.rglob('*' + suffix)))

    split_files, manifests = [], []
    for manifest in sorted(target.rglob(SPLIT_CREATED)):
        try:
            data = json.loads(manifest.read_text(encoding='utf-8'))
        except Exception:
            continue
        manifests.append(manifest)
        for name in (data.get('files') or []):
            path = manifest.parent / str(name)
            if path.exists():
                split_files.append(path)

    if not buf_backups and not ini_backups and not split_files:
        print(c('这个文件夹里没有本工具的备份，没什么可还原的。', Style.YELLOW))
        return

    def buf_target(backup: Path) -> Path:
        for suffix in (VGX_BACKUP_SUFFIX, TEX_BACKUP_SUFFIX, TEX_LEGACY_BACKUP_SUFFIX):
            if backup.name.endswith(suffix):
                return backup.with_name(backup.name[:-len(suffix)] + '.buf')
        return backup

    def ini_target(backup: Path) -> Path:
        text = str(backup)
        for suffix in (TEX_INI_BACKUP_SUFFIX, TEX_LEGACY_INI_BACKUP_SUFFIX):
            if text.endswith(suffix):
                return Path(text[:-len(suffix)])
        return backup

    lines = ['将要还原：']
    for backup in buf_backups:
        lines.append('  - "{}"'.format(buf_target(backup)))
    for backup in ini_backups:
        lines.append('  - "{}"'.format(ini_target(backup)))
    for path in split_files:
        lines.append('  - 删掉拆分写出来的 "{}"'.format(path))
    for line in lines:
        print(line)
    print()
    if not iv_asker().confirm_restore(lines):
        print(c('已取消。', Style.YELLOW))
        return

    for backup in buf_backups:
        buf = buf_target(backup)
        buf.write_bytes(backup.read_bytes())
        backup.unlink()
        for marker in (vgx_marker_of(buf), tex_marker_of(buf)):
            if marker.exists():
                marker.unlink()
        print(c('已还原: "{}"'.format(buf), Style.GREEN))

    for backup in ini_backups:
        ini_path = ini_target(backup)
        ini_path.write_bytes(backup.read_bytes())
        backup.unlink()
        print(c('已还原: "{}"'.format(ini_path), Style.GREEN))
    for path in split_files:
        try:
            path.unlink()
            print(c('已删掉拆分文件: "{}"'.format(path), Style.GREEN))
        except OSError:
            print(c('删不掉: "{}"'.format(path), Style.YELLOW))
    for manifest in manifests:
        for extra in (manifest.parent / 'split报告.txt', manifest):
            try:
                if extra.exists():
                    extra.unlink()
            except OSError:
                pass
    print(c('还原完成。', Style.GREEN))


# ==========================================================================
#  整条 auto 绘制自检（老 mod 换版本后身体糊成碎面）
#
#  老 mod 画整条网格的写法是 `handling = skip` + `drawindexed = auto`：
#  auto = 拿【游戏当前那条 ib】配 mod 自己的 vb0。老版本里两边顶点顺序一致，
#  所以对。游戏更新把这条分量换了之后，游戏 ib 的索引数 / 顶点数都变了
#  （例：铃-短款运动装 身体游戏 7430 顶点，mod 只有 4228）—— auto 一画就
#  越界，胸口/手臂糊一片碎面。件（拆分）没有这问题，因为件是显式 ib + 显式计数。
#
#  这里把这种节也改成显式：`ib = mod 自己的 IB` + `drawindexed = 它的索引数, 0, 0`。
#  只在能证明 auto 已经配不上时才动：
#    - 跑这条 CL 的 TextureOverride 的 hash = 本次参照里某个分量的 ib hash
#    - 同一个分量的 Position 节里 vb0 指的 mod 缓冲顶点数 < dump 里该分量顶点数
#    - mod 自己带 IB 资源（名字 = Position 资源名去掉 position、接 …IB[.N]），
#      且 IB 里的索引都 < mod 顶点数
#  三样缺一就不动（宁可不修，也别把本来对的 auto 改坏）。
# ==========================================================================

def ini_resource_files(ini_path, text):
    """[Resource…] 节名（小写） -> 解析后的文件路径（只收存在的）"""
    out = {}
    for title, start, end in split_sections(text):
        head = title.strip()
        if not head.lower().startswith('resource'):
            continue
        match = re.search(r'(?im)^\s*filename\s*=\s*([^\s;]+)', text[start:end])
        if not match:
            continue
        path = (ini_path.parent / match.group(1).replace('\\', '/'))
        try:
            path = path.resolve()
        except OSError:
            continue
        if path.exists():
            out[head.lower()] = path
    return out


def ib_max_index(path):
    """IB 文件里的最大索引；读不了返回 None"""
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if len(data) < 4 or len(data) % 4:
        return None
    values = struct.unpack('<{}I'.format(len(data) // 4), data)
    return max(values) if values else None


def stale_auto_plan(target: Path):
    """找"auto 已经配不上"的整条绘制（CL 或 IB 节都收）"""
    items = []
    if not DUMP_MESHES:
        return items, [], None
    # ib hash -> (该分量的参照信息, 游戏顶点数)；同一 hash 有多段时取顶点最多的
    by_ib = {}
    for info in DUMP_MESHES.values():
        key = str(info.get('ib_hash') or '').lower()
        if not key or not info.get('position_buf'):
            continue
        pos = load_positions(Path(info['position_buf']))
        if not pos:
            continue
        old = by_ib.get(key)
        if old is None or len(pos) > old[1]:
            by_ib[key] = (info, len(pos))
    if not by_ib:
        return items, [], None

    for ini_path in find_ini_files(target):
        try:
            text = ini_path.read_text(encoding='utf-8', errors='replace')
        except OSError:
            continue
        sections = [(title.strip(), text[start:end])
                    for title, start, end in split_sections(text)]
        commandlists = {head.lower(): (head, body) for head, body in sections
                        if head.lower().startswith('commandlist')}
        resources = ini_resource_files(ini_path, text)
        if not resources:
            continue
        resource_titles = {}
        for head, _body in sections:
            if head.lower().startswith('resource'):
                resource_titles.setdefault(head.lower(), head)
        # CommandList（小写） -> 直接 run 它的 TextureOverride [(标题, hash)]
        runners = {}
        for head, body in sections:
            if not head.lower().startswith('textureoverride'):
                continue
            match = re.search(r'(?im)^\s*hash\s*=\s*([0-9a-fA-F]{8})\s*$', body)
            if not match:
                continue
            for run in re.finditer(r'(?im)^\s*run\s*=\s*(\S+)\s*$', body):
                runners.setdefault(run.group(1).lower(), []).append(
                    (head, match.group(1).lower()))

        def analyse(hash_value):
            """同一个分量的 Position 节 -> mod 缓冲 -> mod 自己的 IB 资源"""
            info, game_verts = by_ib[hash_value]
            pos_hash = str(info.get('position_hash') or '').lower()
            if not pos_hash:
                return None
            def _find_vb0(body, depth=0, seen=None):
                """Position 节里的 vb0：先看直接写的，再跟 run=CommandList 递归找"""
                if depth > 5:
                    return None
                if seen is None:
                    seen = set()
                direct = re.search(r'(?im)^\s*vb0\s*=\s*([^\s;]+)', body)
                if direct:
                    return direct.group(1).lower()
                for run in re.finditer(r'(?im)^\s*run\s*=\s*(\S+)\s*$', body):
                    key = run.group(1).lower()
                    if key in seen:
                        continue
                    linked = commandlists.get(key)
                    if not linked:
                        continue
                    seen.add(key)
                    got = _find_vb0(linked[1], depth + 1, seen)
                    if got:
                        return got
                return None

            pos_res = None
            for head, body in sections:
                if not head.lower().startswith('textureoverride'):
                    continue
                match = re.search(r'(?im)^\s*hash\s*=\s*([0-9a-fA-F]{8})\s*$', body)
                if not match or match.group(1).lower() != pos_hash:
                    continue
                pos_res = _find_vb0(body)
                if pos_res:
                    break
            if not pos_res:
                return None
            pos_path = resources.get(pos_res)
            if not pos_path:
                return None
            try:
                mod_verts = pos_path.stat().st_size // 40
            except OSError:
                return None
            if mod_verts <= 0 or game_verts <= mod_verts:
                return None        # auto 配得上（或者推不出），不动
            base = re.sub(r'\.\d+$', '', pos_res)
            if not base.endswith('position'):
                return None
            base = base[:-len('position')]
            # mod 自己的 IB 资源：名字 = base + …IB[.N]
            candidates, counts = {}, {}
            for name, path in resources.items():
                match = re.fullmatch(
                    re.escape(base) + r'([a-z0-9_]*)ib(?:\.(\d+))?', name)
                if not match:
                    continue
                try:
                    count = path.stat().st_size // 4
                except OSError:
                    continue
                if count <= 0:
                    continue
                top = ib_max_index(path)
                if top is None or top >= mod_verts:
                    continue
                counts[name] = count
                number = int(match.group(2)) if match.group(2) is not None else None
                candidates.setdefault(number, []).append((name, count))
            if not candidates or any(len(group) > 1 for group in candidates.values()):
                return None        # 一个变体好几个 IB，说不清，别猜
            edits = {}
            for number, group in candidates.items():
                name, count = group[0]
                edits[number] = (resource_titles.get(name, name), count)
            return mod_verts, game_verts, edits

        def make_item(cl_title, owners, hash_value):
            result = analyse(hash_value)
            if result is None:
                return None
            mod_verts, game_verts, edits = result
            return {
                'ini': ini_path, 'cl': cl_title, 'edits': edits, 'owners': owners,
                'mod_verts': mod_verts, 'game_verts': game_verts,
                'lines': ['- [auto] "{}"  {}：原版整条 ib（{} 顶点）配 mod 的 {} 顶点，'
                          'auto 会越界 -> 改用 mod 自己的 IB（{}）'.format(
                              ini_path.name, cl_title, game_verts, mod_verts,
                              '/'.join(str(size) for size in sorted(
                                  {count for _name, count in edits.values()})) + ' 索引')],
            }

        taken = set()
        # 1) 老写法：skip + auto 藏在 CommandList 里，由带 hash 的节 run
        for cl_low, (cl_title, cl_body) in commandlists.items():
            if not (re.search(r'(?im)^\s*drawindexed\s*=\s*auto\s*$', cl_body)
                    and re.search(r'(?im)^\s*handling\s*=\s*skip\s*$', cl_body)):
                continue
            owner = None
            for head, hash_value in runners.get(cl_low, ()):
                if hash_value in by_ib:
                    owner = (head, hash_value)
                    break
            if owner is None:
                continue
            owner_body = next((body for head, body in sections
                               if head.lower() == owner[0].lower()), '')
            if re.search(r'(?im)^\s*drawindexed\s*=\s*auto\s*$', owner_body):
                continue        # 节自己也有 auto，交给下面按节处理
            owners = [name for name, value in runners.get(cl_low, ())
                      if value == owner[1]]
            item = make_item(cl_title, owners, owner[1])
            if item:
                # 绘制放哪：优先学验证过的手改版 —— 放到"绑 mod IB 的那个节"，
                # 那里 skin/贴图已经绑好再画；找不到才就地改
                names = {name for name, _count in item['edits'].values()}
                target = None
                for head, body in sections:
                    if not head.lower().startswith('textureoverride'):
                        continue
                    if head.lower() == owner[0].lower():
                        continue
                    for run in re.finditer(r'(?im)^\s*run\s*=\s*(\S+)\s*$', body):
                        linked = commandlists.get(run.group(1).lower())
                        if not linked:
                            continue
                        if any(re.search(
                                r'(?im)^\s*ib\s*=\s*' + re.escape(name) + r'\s*$',
                                linked[1]) for name in names):
                            target = head
                            break
                    if target:
                        break
                if target:
                    target_body = next(
                        (body for head, body in sections
                         if head.lower() == target.lower()), '')
                    if re.search(r'(?im)^\s*drawindexed\s*=', target_body):
                        item['mode'] = 'comment'
                    else:
                        item['mode'] = 'move'
                        item['target'] = target
                        # 目标节里那条"只绑 ib"的 run 也去掉：绘制块自己会绑 ib，
                        # 留着和验证过的手改版不一样（手改版是替换掉那三行的）
                        for run in re.finditer(
                                r'(?im)^\s*run\s*=\s*(\S+)\s*$', target_body):
                            linked = commandlists.get(run.group(1).lower())
                            if linked and any(re.search(
                                    r'(?im)^\s*ib\s*=\s*' + re.escape(name) + r'\s*$',
                                    linked[1]) for name in names):
                                item['target_run'] = run.group(1)
                                break
                else:
                    item['mode'] = 'inplace'
                taken.add(owner[0].lower())
                items.append(item)

        # 2) 新写法：drawindexed 直接写在带 ib hash 的节里
        for head, body in sections:
            if not head.lower().startswith('textureoverride'):
                continue
            if head.lower() in taken:
                continue
            match = re.search(r'(?im)^\s*hash\s*=\s*([0-9a-fA-F]{8})\s*$', body)
            if not match or match.group(1).lower() not in by_ib:
                continue
            if not re.search(r'(?im)^\s*drawindexed\s*=\s*auto\s*$', body):
                continue
            item = make_item(head, [head], match.group(1).lower())
            if item:
                # 同 hash 的另一个节已经把 mod 的 IB 绑上了（内内裤袜 gold：
                # BodyIB 里 auto，BodyA 里 ib = ResourceBelleBodyAIB）—— auto 用的
                # 就是那条 mod IB，不能再改成显式绘制，否则会改已验证的产物。
                names = {name.lower() for name, _count in item['edits'].values()}
                already_bound = False
                for other_head, other_body in sections:
                    if other_head.lower() != head.lower():
                        m2 = re.search(r'(?im)^\s*hash\s*=\s*([0-9a-fA-F]{8})\s*$',
                                       other_body)
                        if not m2 or m2.group(1).lower() != match.group(1).lower():
                            continue
                    for line in other_body.splitlines():
                        m3 = re.match(r'(?i)^\s*ib\s*=\s*([^\s;]+)\s*$', line.strip())
                        if m3 and m3.group(1).lower() in names:
                            already_bound = True
                            break
                    if already_bound:
                        break
                if already_bound:
                    continue
                item['mode'] = 'inplace'
                items.append(item)

    return items, [], None


def stale_auto_patch(text, item):
    """按计划改写：把 auto 换成显式绘制

    move    -> CL 里那句 auto 注释掉，绘制块追加到绑 mod IB 的那个节
               （和验证过的手改版一个形状：绘制发生在 skin/贴图绑定之后）
    comment -> 绑 mod IB 的节自己已有绘制，只把 CL 里那句注释掉
    inplace -> 找不到那样的节：就地换成 ib + 显式计数
    """
    mode = item.get('mode', 'inplace')
    target = (item.get('target') or '').lower()

    def variant_block(indent):
        numbered = sorted((number, value) for number, value
                          in item['edits'].items() if number is not None)
        single = item['edits'].get(None)
        if single is not None or len(numbered) <= 1:
            name, count = single if single is not None else numbered[0][1]
            return ['{}ib = {}'.format(indent, name),
                    '{}drawindexed = {}, 0, 0'.format(indent, count)]
        out = []
        for position, (number, (name, count)) in enumerate(numbered):
            out.append('{}{} $swapvar == {}'.format(
                indent, 'if' if position == 0 else 'else if', number))
            out.append('{}\tib = {}'.format(indent, name))
            out.append('{}\tdrawindexed = {}, 0, 0'.format(indent, count))
        out.append('{}endif'.format(indent))
        return out

    # inplace：绘制节没写 match_first_index 的补 0
    # move  ：目标节（绑 mod IB 的那节）没写 match_first_index 的补 0
    need_first = set()
    owners = {name.lower() for name in item.get('owners') or ()}
    for head, body in ((title.strip(), text[start:end])
                       for title, start, end in split_sections(text)):
        low = head.lower()
        watch = owners if mode == 'inplace' else ({target} if mode == 'move' else set())
        if low in watch and not re.search(r'(?im)^\s*match_first_index\s*=', body):
            need_first.add(low)

    out, title_now, branch = [], None, None
    pending, pending_target = None, False
    for line in text.splitlines():
        match = re.fullmatch(r'\s*\[(.+)\]\s*', line)
        if match:
            if pending:
                out.extend(pending)
                pending = None
            title_now, branch = match.group(1).strip(), None
            pending_target = mode == 'move' and title_now.lower() == target
            if pending_target:
                pending = variant_block('')
        if (pending_target and item.get('target_run')
                and re.match(r'(?i)^\s*run\s*=\s*'
                             + re.escape(item['target_run']) + r'\s*$', line)):
            out.append('; ' + line)
            continue
        low = title_now.lower() if title_now else ''
        if low in need_first and re.match(r'(?i)^\s*hash\s*=', line):
            out.append(line)
            out.append('match_first_index = 0')
            continue
        if title_now and title_now.lower() == item['cl'].lower():
            stripped = line.strip()
            cond = re.match(
                r'(?i)^(?:if|else\s+if|elseif|elif)\s+\$swapvar\s*==\s*(\d+)\s*$', stripped)
            if cond:
                branch = int(cond.group(1))
            elif re.match(r'(?i)^endif\s*$', stripped):
                branch = None
            elif re.match(r'(?i)^drawindexed\s*=\s*auto\s*$', stripped):
                indent = line[:len(line) - len(line.lstrip())]
                if mode == 'move':
                    out.append('; ' + line)
                    continue
                if mode == 'comment':
                    continue
                choice = item['edits'].get(branch)
                if choice is not None:
                    name, count = choice
                    out.append('{}ib = {}'.format(indent, name))
                    out.append('{}drawindexed = {}, 0, 0'.format(indent, count))
                    continue
                if branch is None:
                    out.extend(variant_block(indent))
                    continue
        out.append(line)
    if pending:
        out.extend(pending)
    return '\n'.join(out) + ('\n' if text.endswith('\n') else '')


def stale_auto_apply(planned, total=None, done0=0):
    for index, item in enumerate(planned, 1):
        ini_path = item['ini']
        try:
            text = ini_path.read_text(encoding='utf-8', errors='replace')
        except OSError:
            continue
        backup = Path(str(ini_path) + TEX_INI_BACKUP_SUFFIX)
        if not backup.exists():
            backup.write_bytes(ini_path.read_bytes())
        patched = stale_auto_patch(text, item)
        if patched != text:
            ini_path.write_text(patched, encoding='utf-8')
        print(c('已修 [auto]: "{}"  {}'.format(ini_path.name, item['cl']), Style.GREEN))
        iv_progress(done0 + index, total or len(planned), ini_path.name)


# ==========================================================================
#  四、修复主流程
# ==========================================================================

# 老版独立、3.0 起并进别的分量的绘制节：旧 ib hash -> 新分量 ib hash。
# 铃-泳装：2.8 帽子是单独部件（93f38bdd），3.0 并进了头发（a7683988）。
MERGED_DRAW = {
    '93f38bdd': 'a7683988',
}


def merged_draw_plan(target: Path):
    """找"整件并进别的分量"的绘制节 -> 改 hash + 自己绑 vb0/vb1/vb2

    并进去以后，新分量的 Blend/Texcoord 节绑的是大网格的缓冲，跟这件的顶点
    对不上；所以这节的 hash 换成新分量以外，还要把它自己的 Position/Texcoord/
    Blend 资源直接绑进本节（新分量那几节的 hash 已经匹配不上了）。
    """
    items = []
    for ini_path in find_ini_files(target):
        try:
            text = ini_path.read_text(encoding='utf-8', errors='replace')
        except OSError:
            continue
        sections = [(title.strip(), text[start:end])
                    for title, start, end in split_sections(text)]
        resources = {}
        for head, body in sections:
            if not head.lower().startswith('resource'):
                continue
            fn = re.search(r'(?im)^\s*filename\s*=\s*([^\s;]+)', body)
            if fn:
                resources[head.lower()] = Path(fn.group(1).replace('\\', '/')).name.lower()
        # 所有 vb0/vb1/vb2 绑定 -> 资源名
        binds = {'vb0': [], 'vb1': [], 'vb2': []}
        for head, body in sections:
            for line in body.splitlines():
                s = line.strip()
                if s.startswith((';', '#')):
                    continue
                m = re.match(r'(?i)^(vb[012])\s*=\s*(resource\S+)$', s)
                if m:
                    binds[m.group(1)].append(m.group(2))
        if not resources:
            continue

        def stem(name):
            return resources.get(name.lower(), '')

        def best(kind, ib_file):
            pick, pick_score = None, 0
            for name in binds[kind]:
                fn = stem(name)
                if not fn or not ib_file:
                    continue
                score = 0
                while (score < len(fn) and score < len(ib_file)
                       and fn[score] == ib_file[score]):
                    score += 1
                if score > pick_score:
                    pick, pick_score = name, score
            return pick if pick_score >= 8 else None

        for head, body in sections:
            if not head.lower().startswith('textureoverride'):
                continue
            match = re.search(r'(?im)^\s*hash\s*=\s*([0-9a-fA-F]{8})\s*$', body)
            if not match or match.group(1).lower() not in MERGED_DRAW:
                continue
            act = [line.strip() for line in body.splitlines()
                   if line.strip() and not line.strip().startswith((';', '#'))]
            if not any(re.match(r'(?i)^drawindexed\s*=', line) for line in act):
                continue
            ib_m = next((re.match(r'(?i)^ib\s*=\s*(resource\S+)$', line)
                         for line in act
                         if re.match(r'(?i)^ib\s*=\s*resource', line)), None)
            ib_res = ib_m.group(1) if ib_m else None
            ib_file = stem(ib_res) if ib_res else ''
            vb0 = best('vb0', ib_file)
            vb1 = best('vb1', ib_file)
            vb2 = best('vb2', ib_file)
            if not (vb0 and vb1 and vb2):
                continue        # 找不全就别动
            lines = ['- [合并件] "{}"  {}：hash {} -> {}，并自己绑 {} / {} / {}'.format(
                ini_path.name, head, match.group(1).lower(),
                MERGED_DRAW[match.group(1).lower()], vb0, vb1, vb2)]
            items.append({
                'ini': ini_path, 'section': head,
                'old': match.group(1).lower(), 'new': MERGED_DRAW[match.group(1).lower()],
                'vb0': vb0, 'vb1': vb1, 'vb2': vb2,
                'lines': lines,
            })
    return items


def merged_draw_apply(planned, total=None, done0=0):
    for index, item in enumerate(planned, 1):
        ini_path = item['ini']
        try:
            text = ini_path.read_text(encoding='utf-8', errors='replace')
        except OSError:
            continue
        backup = Path(str(ini_path) + TEX_INI_BACKUP_SUFFIX)
        if not backup.exists():
            backup.write_bytes(ini_path.read_bytes())
        out, inside, inserted = [], False, False
        for line in text.splitlines():
            m = re.fullmatch(r'\s*\[(.+)\]\s*', line)
            if m:
                inside = m.group(1).strip().lower() == item['section'].lower()
            if inside:
                if re.match(r'(?i)^\s*hash\s*=\s*[0-9a-fA-F]{8}\s*$', line):
                    indent = line[:len(line) - len(line.lstrip())]
                    out.append('{}hash = {}'.format(indent, item['new']))
                    out.append('{}; 旧 hash = {}（这件已并进上面的分量）'.format(
                        indent, item['old']))
                    continue
                if not inserted and re.match(
                        r'(?i)^\s*(ib\s*=|drawindexed\s*=)', line.strip()):
                    indent = line[:len(line) - len(line.lstrip())]
                    out.append('{}vb0 = {}'.format(indent, item['vb0']))
                    out.append('{}vb1 = {}'.format(indent, item['vb1']))
                    out.append('{}vb2 = {}'.format(indent, item['vb2']))
                    inserted = True
            out.append(line)
        if inserted:
            ini_path.write_text('\n'.join(out) + ('\n' if text.endswith('\n') else ''),
                                encoding='utf-8')
        print(c('已修 [合并件]: "{}"  {}'.format(ini_path.name, item['section']), Style.GREEN))
        if total:
            iv_progress(done0 + index, total, ini_path.name)


def apply_fix(target: Path, verdict=True):
    reason = unsupported_mod_reason(target)
    if reason:
        print(c(reason, Style.RED))
        return dict(vgx=0, tex=0, limit=0, off=0, auto=0, merge=0, changed=False,
                    cancelled=True, error=reason)
    print('目录: {}'.format(target))
    print('VGX 角色表 {} 条    格式目标表 {} 条'.format(len(VGX_CHARACTERS), len(TEXCOORD_TARGETS)))

    # 参照闸门：mod 的 ini 里命中本次这组参照的任意一个 hash = 同一组，整包放行；
    # 一个都没命中 = 不是这组的 mod，一个文件都不动（每组的 hash 都不一样）
    hit, which = mod_ref_hit(target, active_ref_hashes())
    if not hit:
        print()
        print(c('这个 mod 的 ini 里没有一个 hash 属于本次参照【{}】。'.format(ref_scope_text()),
                Style.YELLOW))
        print(c('不是这组参照的 mod，整包不处理 —— 想修它就把“参照文件夹”换成它对应的那组。',
                Style.YELLOW))
        return dict(vgx=0, tex=0, limit=0, off=0, auto=0, merge=0,
                    changed=False, cancelled=False, aborted=True,
                    error='不属于本次参照')
    if which:
        print('参照比对：ini 里的 hash {} 命中本次参照【{}】'.format(which, ref_scope_text()))
    print()

    if not validate_vgx() or not validate_texcoord():
        print()
        print(c('表里有写错的地方，先改好再跑。已中止。', Style.RED))
        return dict(vgx=0, tex=0, limit=0, off=0, auto=0, merge=0,
                    changed=False, cancelled=False, aborted=True,
                    error='表校验失败')

    print('===== 一、VGX 骨骼索引 =====')
    vgx_items, _vgx_skipped, vgx_error = vgx_plan(target)
    if vgx_error:
        print(c('（{}）'.format(vgx_error), Style.YELLOW))
    table_paths = {str(item['buf'].resolve()) for item in vgx_items}

    # dump 驱动：mod 的网格和 dump 按位置配得上，就自己推映射
    auto_items = vgx_auto_plan(target, DUMP_MESHES) if DUMP_MESHES else []
    both = [it for it in auto_items if str(it['buf'].resolve()) in table_paths]
    only_auto = [it for it in auto_items if str(it['buf'].resolve()) not in table_paths]

    approved = []

    if both:
        if iv_asker().source_choice('vgx', '、'.join(it['buf'].name for it in both),
                                    len(both), False) == 'dump':
            drop = {str(it['buf'].resolve()) for it in both}
            vgx_items = [it for it in vgx_items if str(it['buf'].resolve()) not in drop]
            approved += both          # 已经选过 dump 了，不再问一遍
        print()

    if only_auto:
        if iv_asker().auto_vgx_choice([str(it['buf']) for it in only_auto]):
            approved += only_auto
        print()

    # 决定完了才打印各条要做什么
    for item in vgx_items:
        for line in item.get('lines', []):
            print(line)
    for it in approved:
        changed = it['changed']
        low = [o for o in changed if changed[o]['votes'] < VGX_LOW_VOTES]
        print('- [VGX] "{}"  [{}]'.format(it['buf'], it['label']))
        print('        按位置配对推出来的骨骼索引映射（用 dump）')
        print('        配到 {}/{} 个 dump 顶点（{:.1%}），中位偏差 {:.5f}'.format(
            it['stats']['matched'], it['stats']['total'],
            it['matched_ratio'], it['stats']['median']))
        print('        要改 {} 条：{}'.format(
            len(changed),
            ', '.join('{}->{}'.format(o, changed[o]['new']) for o in sorted(changed)[:12])
            + (' ...' if len(changed) > 12 else '')))
        if low:
            print(c('        有 {} 条票数偏少，可能是配错顶点凑的，重点核对：{}'.format(
                len(low), ', '.join('{}->{}'.format(o, changed[o]['new']) for o in sorted(low)[:6])),
                Style.YELLOW))
        vgx_items.append({'buf': it['buf'], 'table': it['mapping'], 'label': it['label']})

    if not vgx_items:
        if not VGX_CHARACTERS and not DUMP_MESHES:
            print(c('（没得比 —— VGX_CHARACTERS 表是空的，dump\\ 里也没有 dump）', Style.YELLOW))
            print('  骨骼索引错位（腿弯、塌陷）要么填表（用 查找VGX映射工具），')
            print('  要么把该网格的 dump 放进 dump\\（json + -*Blend.buf + -*Position.buf）')
        elif not vgx_error:
            print('（没有命中的网格，或都已经修过了）')
    print()

    print('===== 二、texcoord 顶点格式 =====')
    use_dump = None
    conflicts = dump_conflicts()
    if conflicts:
        for entry, info in conflicts_differ():
            _old, new_format = target_formats(entry)
            print(c('  ! "{}" 两边给的格式不一样：表 {} / dump {}'.format(
                entry.get('name', '?'), ' + '.join(new_format), ' + '.join(info['new_format'])),
                Style.YELLOW))
        use_dump = (iv_asker().source_choice('tex', '、'.join(conflicts), len(conflicts),
                                             PREFER_DUMP) == 'dump')
        print('  -> 这次用 {} 里的数据'.format('dump' if use_dump else '表'))
        print()

    tex_items, _tex_skipped, tex_error = tex_plan(target, use_dump)
    if tex_error:
        print(c('（{}）'.format(tex_error), Style.YELLOW))
    elif not tex_items:
        if not TEXCOORD_TARGETS and not DUMP_MESHES:
            print(c('（没得比 —— TEXCOORD_TARGETS 表是空的，dump\\ 里也没有 dump）', Style.YELLOW))
            print('  贴图错乱要修，得先有这个网格的 dump —— 找作者要一份放进 dump\\')
        else:
            print('（没有命中的网格，或都已经处理过了）')
    print()

    # 漏网提醒：旧格式但没被处理到的 texcoord
    planned_paths = {str(item['buf'].resolve()) for item in tex_items}
    known_old = set()
    for entry in TEXCOORD_TARGETS:
        old_format, _new_format = target_formats(entry)
        if old_format:
            known_old.add(fmt_stride(old_format))
    dump_strides = dump_old_strides()          # dump 里网格能倒推出来的旧步幅
    known_old |= set(dump_strides)

    orphans = [(path, per) for path, per in tex_inventory(target)
               if per in known_old and str(path.resolve()) not in planned_paths]
    if orphans:
        print(c('注意：下面这些 texcoord 看着是旧格式，但没被处理，工具不会动：', Style.YELLOW))
        for path, per in orphans:
            print('  - "{}"   每顶点 {} 字节'.format(path, per))
            who = dump_strides.get(per)
            if who:
                print('      dump 里有 {} 的 {} 字节旧格式，但 mod 的 ini 里 hash 对不上 ——'
                      ' 先跑一遍版本修复工具把 hash 更新到最新。'.format('、'.join(sorted(who)), per))
        print('  两种原因：① mod 的 ini 里 hash 还是旧的（先跑版本修复工具）')
        print('            ② 这个网格作者还没提供 dump —— 反馈给作者补一份就行')
        print()

    print('===== 三、顶点上限（VertexLimitRaise） =====')
    limit_items, limit_skipped, limit_error = limit_plan(
        target, active_component_hashes())
    if limit_error:
        print(c('（{}）'.format(limit_error), Style.YELLOW))
    for name in limit_skipped:
        print(c('  ! {}'.format(name), Style.YELLOW))
    if not limit_items and not limit_error:
        print('（没有要补 / 要对不上的）')
    for item in limit_items:
        for line in item.get('lines', []):
            print(line)
    print()

    print('===== 五、掐掉多余的那几笔（原版分量 / 索引段） =====')
    off_items, off_skipped, off_error = suppress_plan(target)
    if off_error:
        print(c('（{}）'.format(off_error), Style.YELLOW))
    for name in off_skipped:
        print('  （{}）'.format(name))
    if not off_items and not off_error:
        print('（没有要掐的）')
    for item in off_items:
        for line in item.get('lines', []):
            print(line)
    print()

    print('===== 六、整条 auto 绘制（换成 mod 自己的 IB） =====')
    auto_items, _auto_skipped, auto_error = stale_auto_plan(target)
    if auto_error:
        print(c('（{}）'.format(auto_error), Style.YELLOW))
    if not auto_items and not auto_error:
        print('（没有要改的）')
    for item in auto_items:
        for line in item.get('lines', []):
            print(line)
    print()

    print('===== 七、并进别的部件的绘制（旧独立件） =====')
    merge_items = merged_draw_plan(target)
    if not merge_items:
        print('（没有要改的）')
    for item in merge_items:
        for line in item.get('lines', []):
            print(line)
    print()

    if (not vgx_items and not tex_items and not limit_items and not off_items
            and not auto_items and not merge_items):
        if verdict:
            print(c('结论：这个 mod 不需要修复（没有任何文件需要改）。', Style.YELLOW))
        return dict(vgx=0, tex=0, limit=0, off=0, auto=0, merge=0,
                    changed=False, cancelled=False)

    summary = ('将修改：VGX 骨骼索引 {} 个 buf、顶点格式 {} 个 buf、顶点上限 {} 个 ini、'
               '掐笔 {} 个 ini、整条 auto 绘制 {} 个 ini、并进部件 {} 个节（改前都会备份）'.format(
                   len(vgx_items), len(tex_items), len(limit_items), len(off_items),
                   len(auto_items), len(merge_items)))
    print(c('不要对不需要修复的 mod 运行本工具!!!', Style.RED))
    print(c('不要在同一个 buf 上运行两次!!!', Style.RED))
    if not iv_asker().confirm(summary):
        print(c('结论：已取消，这个 mod 没有任何改动。', Style.YELLOW))
        return dict(vgx=0, tex=0, limit=0, off=0, auto=0, merge=0,
                    changed=False, cancelled=True)

    total = (len(vgx_items) + len(tex_items) + len(limit_items) + len(off_items)
             + len(auto_items) + len(merge_items))
    print()
    if vgx_items:
        print('应用 VGX 重映射中...')
        vgx_apply(vgx_items, total, 0)
    if tex_items:
        print('应用格式重排中...')
        tex_apply(tex_items, total, len(vgx_items))
    if limit_items:
        print('应用顶点上限修正中...')
        limit_apply(limit_items, total, len(vgx_items) + len(tex_items))
    if off_items:
        print('追加掐笔中...')
        suppress_apply(off_items, total, len(vgx_items) + len(tex_items) + len(limit_items))
    if auto_items:
        print('改写 auto 绘制中...')
        stale_auto_apply(auto_items, total,
                         len(vgx_items) + len(tex_items) + len(limit_items) + len(off_items))
    if merge_items:
        print('并进部件的绘制节改写中...')
        merged_draw_apply(merge_items, total,
                          len(vgx_items) + len(tex_items) + len(limit_items)
                          + len(off_items) + len(auto_items))

    print()
    if verdict:
        print(c('结论：已修复这个 mod —— VGX {} 个 buf / 顶点格式 {} 个 buf / '
                '顶点上限 {} 个 ini / 掐笔 {} 个 ini / auto 绘制 {} 个 ini / '
                '并进部件 {} 个节。'.format(
                    len(vgx_items), len(tex_items), len(limit_items), len(off_items),
                    len(auto_items), len(merge_items)), Style.GREEN))
        print(c('完成!', Style.GREEN))
    print('备份后缀: {} / {}'.format(VGX_BACKUP_SUFFIX, TEX_BACKUP_SUFFIX))
    return dict(vgx=len(vgx_items), tex=len(tex_items), limit=len(limit_items),
                off=len(off_items), auto=len(auto_items), merge=len(merge_items),
                changed=True, cancelled=False)


def apply_universal(target: Path):
    """通用脸部修复：认内嵌名单的 hash，把 texcoord buf 从 36 改成 48 字节/顶点

    只动 texcoord buf（和 ini 里那行 stride）；骨骼索引（VGX）这次不碰。
    不看参照 —— 有 dump 也只是借它的 blend hash 反推顶点数。
    """
    print('目录: {}'.format(target))
    print('通用脸部修复名单 {} 个网格 / {} 个角色'.format(
        len(UNIVERSAL_HASHES), len({label.split(' / ')[0].strip() or label
                                    for _old, label in UNIVERSAL_HASHES.values()})))
    print('固定改法：顶点 COLOR 4 字节 -> 4 个 float，每顶点 {} -> {} 字节'.format(
        fmt_stride(UNIVERSAL_OLD_FORMAT), fmt_stride(UNIVERSAL_NEW_FORMAT)))
    print('（这个模式只动 texcoord buf；骨骼索引 VGX 不碰）')
    print()

    if not validate_universal():
        print()
        print(c('名单里有写错的地方，先改好再跑。已中止。', Style.RED))
        return

    # ini 里 hash 还是旧的那种 -> 先跑版本修复工具，不然按 hash 找不到节
    old_hits = universal_old_hash_hits(target)
    if old_hits:
        old_map = universal_old_map()
        print(c('注意：这些 ini 里的 hash 还是旧的 —— 先跑一遍版本修复工具把 hash 更新到最新：',
                Style.YELLOW))
        for ini_path, hashes in old_hits[:5]:
            try:
                where = str(ini_path.relative_to(target))
            except ValueError:
                where = str(ini_path)
            sample = '、'.join(c('{} -> {}'.format(h, old_map[h]), Style.GREEN)
                               for h in hashes[:3])
            print('  - {}: {} 个节的 hash 还是旧的（{}{}）'.format(
                where, len(hashes), sample, ' …' if len(hashes) > 3 else ''))
        if len(old_hits) > 5:
            print('  … 另有 {} 个 ini'.format(len(old_hits) - 5))
        print()

    print('===== texcoord 顶点格式（通用脸部修复） =====')
    tex_items, _tex_skipped, tex_error = tex_plan(target, entries=universal_targets())
    if tex_error:
        print(c('（{}）'.format(tex_error), Style.YELLOW))
    elif not tex_items:
        print('（没有命中的网格，或都已经处理过了）')
    print()

    # 漏网提醒：看着还是旧格式、但没认到名单里的 hash
    old_stride = fmt_stride(UNIVERSAL_OLD_FORMAT)
    planned_paths = {str(item['buf'].resolve()) for item in tex_items}
    others = [path for path, per in tex_inventory(target)
              if per == old_stride and str(path.resolve()) not in planned_paths]
    if others:
        print(c('注意：下面这些 texcoord 看着还是旧格式（{} 字节/顶点），但没认到名单里的 hash，'
                '工具不会动：'.format(old_stride), Style.YELLOW))
        for path in others[:8]:
            print('  - "{}"'.format(path))
        if len(others) > 8:
            print('  … 另有 {} 个'.format(len(others) - 8))
        print('  两种原因：① 这个网格不在这批通用修复里（或者 hash 又变了，表没跟上）')
        print('            ② mod 的 ini 里 hash 还是旧的 —— 先跑版本修复工具')
        print()

    if not tex_items:
        print(c('没有需要处理的文件。', Style.YELLOW))
        return

    print('颜色块小统计（只看，不拦）：')
    for item in tex_items:
        zero, kinds = universal_color_stats(item['buf'], item['count'], item['old_stride'])
        print('  {}: 全 0 的顶点 {} / {}，{} 种取值'.format(
            item['buf'].name, zero, item['count'], kinds))
    print()

    summary = '将修改：texcoord 顶点格式 {} 个 buf（改前都会备份）'.format(len(tex_items))
    print(c('不要对不需要修复的 mod 运行本工具!!!', Style.RED))
    print(c('不要在同一个 buf 上运行两次!!!', Style.RED))
    if not iv_asker().confirm(summary):
        print(c('已取消，没有改动任何文件。', Style.YELLOW))
        return

    print()
    print('应用格式重排中...')
    tex_apply(tex_items, len(tex_items), 0)

    print()
    print(c('完成!', Style.GREEN))
    print('备份后缀: {} / {} / {}'.format(
        TEX_BACKUP_SUFFIX, TEX_MARKER_SUFFIX, TEX_INI_BACKUP_SUFFIX))
    print('修坏了就在拖放界面输 2 还原。')


# ==========================================================================
#  五、界面
# ==========================================================================

def ask(prompt=''):
    """读一行输入。非交互运行（stdin 到头）时当空输入，不让它抛异常"""
    try:
        return input(prompt)
    except EOFError:
        return ''
    except KeyboardInterrupt:
        print()
        return ''


def clean_path(raw):
    raw = raw.strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in '"\'':
        raw = raw[1:-1]
    return raw.strip()


def is_dump_folder(folder: Path) -> bool:
    """有 json、没有 ini -> 当成 dump 文件夹"""
    if not folder.is_dir():
        return False
    return any(True for _ in folder.rglob('*.json')) and not any(True for _ in folder.rglob('*.ini'))


def take_dump_folder(folder: Path) -> bool:
    """是 dump 文件夹就读进来并返回 True"""
    if not is_dump_folder(folder):
        return False
    added, total, names = load_dump_into_session(folder)
    print(c('  识别为 dump 文件夹：读到 {} 个网格（新增 {}）'.format(total, added), Style.GREEN))
    print('  之后拖 mod 文件夹进来，贴图格式和骨骼索引都会自己对照，不用手填表。')
    if names:
        print('  刚读进来的参照：{}'.format('、'.join(names)))
        print('  想只用一组，输 {} 重选参照。'.format(c('c', Style.GREEN)))
    print()
    return True


def mode_text() -> str:
    """这次用哪套（显示用）"""
    if FIX_MODE == 'universal':
        return '通用脸部修复（{} 个网格，固定 {} -> {} 字节/顶点，不看参照）'.format(
            len(UNIVERSAL_HASHES),
            fmt_stride(UNIVERSAL_OLD_FORMAT), fmt_stride(UNIVERSAL_NEW_FORMAT))
    return '索引与顶点修复（VGX 骨骼索引 + texcoord 顶点格式）'


def choose_mode():
    """启动时选这次用哪套；拖放界面输 m 也能回来重选"""
    global FIX_MODE
    while True:
        print('这次用哪套？（拖放界面输 {} 可以换）'.format(c('m', Style.GREEN)))
        print('  {} = 索引与顶点修复  VGX 骨骼索引 + texcoord 格式，按表 / dump 参照走，'
              '要选一组参照{}'.format(c('1', Style.GREEN), Style.RESET))
        print('  {} = 通用脸部修复    3.1 -> 3.2 那批脸部，固定 {} -> {} 字节/顶点，'
              '只认 hash 名单，不需要参照{}'.format(
                  c('2', Style.GREEN),
                  fmt_stride(UNIVERSAL_OLD_FORMAT), fmt_stride(UNIVERSAL_NEW_FORMAT),
                  Style.RESET))
        print('  {} = 网格拆分修复    老 mod 的网格是一条、新版拆成好几条分量时用：'
              '按参照 dump 把那条网格按位置切开、各绑各的 hash，要选一组参照{}'.format(
                  c('3', Style.GREEN), Style.RESET))
        print('  {} = 看通用脸部修复能修哪些角色（看完回来接着选）{}'.format(
            c('4', Style.GREEN), Style.RESET))
        answer = ask('  选 1 / 2 / 3 / 4（回车 = 1）: ').strip().lower()
        if answer in ('4', '名单', 'list', 'l'):
            show_universal_list()
            continue
        if answer in ('3', '拆分', 'split', 's'):
            FIX_MODE = 'split'
        elif answer in ('2', '通用', 'universal', 'u'):
            FIX_MODE = 'universal'
        else:
            FIX_MODE = 'normal'
        print('  这次用：{}'.format(c(mode_text(), Style.GREEN)))
        show_mode_intro()
        ensure_reference()
        return


def universal_covered():
    """名单里的 (角色, IB 那句, 旧 hash, 新 hash)，按角色名排"""
    rows = []
    for new_hash, (old_hash, label) in UNIVERSAL_HASHES.items():
        parts = label.split(' / ', 1)
        rows.append((parts[0].strip() or label,
                     parts[1].strip() if len(parts) > 1 else '',
                     old_hash.lower(), new_hash.lower()))
    return sorted(rows)


def show_universal_list():
    """通用脸部修复能修哪些角色（菜单那步"看名单"打这个）"""
    rows = universal_covered()
    names = sorted({row[0] for row in rows})
    print()
    print('通用脸部修复能修的（3.1 -> 3.2 更新里 texcoord 变过的）:')
    print('  共 {} 个网格，{} 个角色'.format(len(rows), len(names)))
    print()
    for name, mesh, old_hash, new_hash in rows:
        print('  {:<22} {:<28} {} -> {}'.format(name, mesh, old_hash, new_hash))
    print()


def show_normal_intro():
    """选完/换到「索引与顶点修复」之后，把原来那份说明说一遍"""
    print()
    print('这个模式干什么')
    print('  一次拖一个 mod 文件夹进去，三类问题一起查、一起列、一次确认、一起修。')
    print()
    print('  一、骨骼索引（VGX）')
    print('      症状：模型变形 —— 腿弯、塌陷、扭曲，但贴图正常')
    print('      做法：按角色表把 blend.buf 里的骨骼索引逐个换成正确的')
    print()
    print('  二、顶点格式（texcoord）')
    print('      症状：贴图整体错乱，但模型形状完全正常')
    print('      做法：按目标表重排每个顶点的字节，并同步改 ini 里的 stride')
    print()
    print('  三、顶点上限（VertexLimitRaise）')
    print('      症状：模型炸开、顶点被拉到天上、顶点缓冲溢出（贴图和形状本身看着正常）')
    print('      做法：照这个网格的 buf 算真实顶点数，补上或改正 override_vertex_count；')
    print('            旧写法（92 / 96 / 76）的 override_byte_stride 一律改回 40')
    print('      只动 ini，不动 buf')
    print()
    print('  四、网格拆分修复（选 3 号模式）')
    print('      症状：模型/头发/腿整块不动，或者归位了但形状对不上')
    print('      做法：按参照 dump 的各分量把老的一条网格按位置切开，每件绑自己的 hash')
    print()
    print('  五、掐掉多余的那几笔（跟本模式一起跑）')
    print('      症状：同一块地方画两遍（耳坠、发夹这种小件最容易看出来）、某处糊成一团')
    print('      做法：mod 的 ini 里没认、却被 mod 的网格盖住了的分量 -> 出一节 handling = skip；')
    print('            mod 认了、但 dump 里它还有第 2 段起没人 match 的索引段 -> 也出一节 skip')
    print('      只动 ini（备份 .texfmt.bak）')
    print()
    print('  五类互相独立，哪个命中修哪个；都没命中就什么都不做。')
    print('  动手前要先选一组参照（dump\\ 里的一个文件夹），只按那组的 hash 认。')
    print()


def show_universal_intro():
    """选完/换到「通用脸部修复」之后，把原来那份说明说一遍"""
    rows = universal_covered()
    names = {row[0] for row in rows}
    print()
    print('这个模式干什么')
    print('  修复 3.1 -> 3.2 更新后，部分角色 mod 脸部损坏的问题。')
    print('  mod 的 texcoord buf 里，最前面那块顶点颜色从 4 字节（R8G8B8A8_UNORM）')
    print('  变成 4 个 float（每顶点 36 -> 48 字节），同时把 ini 里的 stride 一起改掉。')
    print('  只认 hash：ini 里某个节的 hash 命中名单里的某条，才动它 vb1 绑的那个 buf。')
    print()
    print('能修哪些')
    print('  只修 3.1 -> 3.2 这次更新里 texcoord 变过的角色：')
    print('  {} 个网格 / {} 个角色（输 3 看名单）。'.format(len(rows), len(names)))
    print('  别的角色、或者 hash 又变过的，认不出来就不动它。')
    print('  骨骼索引（VGX）不归这个模式管，那个换回索引与顶点修复模式。')
    print()
    print('一次拖一个 mod')
    print('  拖进来的文件夹里应当直接就是这个 mod 的 ini 和 buf。')
    print('  好几个 mod 堆在一个文件夹里也能扫，但一个一个来最稳 —— 出问题好认是哪个。')
    print()


def show_mode_intro():
    """当前模式的说明（选完模式、换完模式都过一遍）"""
    if FIX_MODE == 'universal':
        show_universal_intro()
    else:
        show_normal_intro()


def ensure_reference():
    """索引与顶点修复模式下，确保这次已经选好一组参照

    每次进这个模式都要重新问一遍 —— 从通用模式换回来时，参照是上一轮留下的
    （通用模式用的是全部 dump），不重选就会跨组匹配。
    通用模式不看参照，只把 dump 全都放着（借它的 blend hash 反推顶点数用）。
    """
    if FIX_MODE != 'normal':
        set_active_dumps(None)
        return
    if ALL_DUMPS:
        choose_character()
    else:
        set_active_dumps(None)


def ask_action(target: Path):
    """拖进来之后让用户选：修复 / 还原 / 跳过 / 退出"""
    print('  目标: {}'.format(target))
    while True:
        print('  {} = 修复     {} = 还原     回车 = 跳过     {} = 退出'.format(
            c('1', Style.GREEN), c('2', Style.GREEN), c('q', Style.GRAY)))
        try:
            choice = input(c('  选择: ', Style.CYAN)).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return 'quit'

        if choice == '':
            return None
        if choice in ('1', '修复', 'apply', 'fix'):
            return 'apply'
        if choice in ('2', '还原', 'restore', 'undo'):
            return 'restore'
        if choice in EXIT_WORDS:
            return 'quit'
        print(c('  请输入 1 / 2 / 回车 / q', Style.YELLOW))


def run_once(action, target: Path):
    if action == 'restore':
        restore(target)
        return
    reason = unsupported_mod_reason(target)
    if reason:
        print()
        print(c('结论：' + reason, Style.RED))
        return
    if FIX_MODE == 'universal':
        apply_universal(target)
    elif FIX_MODE == 'split':
        apply_split(target)
    else:
        # 索引与顶点修复 + 网格拆分合并成一步：拆分要用这一步换好的骨号/格式；
        # 不需要拆的网格（单分量 / hash 对不上参照）拆分那步自己会跳过。
        # 两步各自的"结论"行不单独出，最后合并成一行总结
        fix = apply_fix(target, verdict=False)
        if fix is None:
            print(c('结论：修复已中止，这个 mod 没有任何改动。', Style.YELLOW))
            return
        fix = fix or {}
        if fix.get('aborted'):
            print(c('结论：已中止，这个 mod 没有任何改动。', Style.YELLOW))
            return
        if fix.get('cancelled'):
            print(c('结论：已取消，这个 mod 没有任何改动。', Style.YELLOW))
            return
        split = apply_split(target, verdict=False) or {}
        if split.get('aborted'):
            print(c('结论：拆分已中止，没有写任何拆件文件。', Style.YELLOW))
            return
        if split.get('cancelled'):
            if fix.get('changed'):
                print(c('结论：索引与顶点已修；拆分被取消，没有写拆件文件。', Style.YELLOW))
            else:
                print(c('结论：已取消，这个 mod 没有任何改动。', Style.YELLOW))
            return
        parts = []
        if fix.get('changed'):
            parts.append('VGX {} 个 buf / 顶点格式 {} 个 buf / 顶点上限 {} 个 ini / 掐笔 {} 个 ini'.format(
                fix.get('vgx', 0), fix.get('tex', 0), fix.get('limit', 0), fix.get('off', 0)))
        if split.get('changed'):
            parts.append('拆分 {} 个网格'.format(split.get('items', 0)))
        print()
        if parts:
            print(c('结论：已修复这个 mod —— {}。'.format('；'.join(parts)), Style.GREEN))
        else:
            print(c('结论：这个 mod 不需要修复（索引与拆分都没有要改的）。', Style.YELLOW))


def drag_drop_loop():
    """跑完不退出，把 mod 文件夹拖进窗口就能接着处理下一个"""
    print()
    if FIX_MODE == 'normal' and DUMP_MESHES:
        print('这次生效的参照：{}'.format(c(describe_active_dumps(), Style.GREEN)))
    print(c('  注意：一次只拖一个 mod 的文件夹（它自己的 ini 和 Buffer）。', Style.RED))
    print(c('        不要把整个 Mods 目录拖进来 —— 会扫到别的 mod。', Style.RED))
    print()
    print(c('=' * 62, Style.GRAY))
    print('把 mod 文件夹拖到本窗口（或直接粘贴路径），按 Enter')
    print('然后再选要做什么')
    if ALL_DUMPS and FIX_MODE == 'normal':
        print('  输入 {}{}{} 换参照组（重选参照）'.format(Style.GREEN, 'c', Style.RESET))
    print('  输入 {}{}{} 换模式（索引与顶点修复 / 通用脸部修复 / 网格拆分修复）'.format(
        Style.GREEN, 'm', Style.RESET))
    print('  输入 {}{}{} 看通用脸部修复能修哪些角色'.format(Style.GREEN, '3', Style.RESET))
    print('  输入 {}{}{} 退出'.format(Style.GREEN, 'q', Style.RESET))
    print(c('=' * 62, Style.GRAY))
    print()

    while True:
        try:
            raw = input(c('拖放文件夹: ', Style.CYAN)).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not raw:
            continue
        if raw.lower() in EXIT_WORDS:
            print('退出。')
            break
        # 换模式：索引与顶点修复 / 通用脸部修复
        if raw.lower() in ('m', 'mode', '模式', '换模式'):
            choose_mode()
            continue
        # 看通用脸部修复的名单
        if raw.lower() in ('l', 'list', '名单', '3'):
            show_universal_list()
            continue
        # 换参照组：重新选参照（通用模式不看参照）
        if raw.lower() in ('c', 'juese', 'role', '角色', '换角色', '参照', '换参照'):
            if FIX_MODE == 'universal':
                print(c('  通用脸部修复不看参照（输 m 换回索引与顶点修复）。', Style.YELLOW))
            elif ALL_DUMPS:
                choose_character()
                print('当前参照：{}'.format(describe_active_dumps()))
                print()
            else:
                print(c('  dump\\ 里还没有 dump。', Style.YELLOW))
            continue

        # 一次拖多个文件夹时，控制台会把所有路径拼成一行（含空格的路径带引号）
        try:
            tokens = shlex.split(raw, posix=False)
        except ValueError:
            tokens = [raw]

        for token in tokens:
            path = clean_path(token)
            if not path:
                continue
            item = Path(path)
            if not item.exists():
                print(c('找不到: {}'.format(path), Style.RED))
                continue

            target = item.resolve() if item.is_dir() else item.resolve().parent

            # 拖进来的是 dump 文件夹（有 json、没 ini）-> 读进来存着，不修
            if take_dump_folder(target):
                continue

            action = ask_action(target)
            if action == 'quit':
                return
            if not action:
                continue

            print(c('-' * 62, Style.GRAY))
            run_once(action, target)
            print(c('-' * 62, Style.GRAY))
            print()


def main():
    global FIX_MODE
    argv = sys.argv[1:]
    action = 'apply'
    for arg in argv:
        low = arg.lower()
        if low in ('apply', 'restore'):
            action = low
        elif low in MODE_KEYS:
            FIX_MODE = 'universal'
    skip = ('apply', 'restore') + MODE_KEYS
    paths = [arg for arg in argv if arg.lower() not in skip]

    print(c('索引与顶点修复工具  ·  VGX 骨骼索引 + texcoord 顶点格式', Style.CYAN))
    print('（两套模式：索引与顶点修复 / 通用脸部修复，启动时选，拖放界面输 m 可以换）')
    print()

    ensure_dump_dir()
    refresh_dumps()

    if paths:
        set_active_dumps(None)          # 命令行调用不提问，有多少用多少
        print('这次用：{}'.format(c(mode_text(), Style.GREEN)))
        if FIX_MODE == 'normal' and DUMP_MESHES:
            print('这次生效的参照：{}'.format(describe_active_dumps()))
            print('（这些网格不用填表，拖 mod 进来直接修）')
        print()
    else:
        choose_mode()                   # 选模式 + 选参照（都在这一步问完），再拖 mod

    if paths:
        for raw in paths:
            item = Path(clean_path(raw))
            if not item.exists():
                print(c('找不到: {}'.format(raw), Style.RED))
                continue
            target = item.resolve() if item.is_dir() else item.resolve().parent
            if take_dump_folder(target):
                continue
            run_once(action, target)
    else:
        print('（没给路径，进入拖放模式）')

    drag_drop_loop()


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        # 出错了才停住等按键；正常退出（输入 q）直接关窗口
        print('\n出错了: {}\n'.format(error))
        print(traceback.format_exc())
        try:
            input('\n按 Enter 键退出...')
        except EOFError:
            pass
