# -*- coding: utf-8 -*-
r"""
    索引与顶点修复工具

名字里的两样东西：
    索引 = blend.buf 里的骨骼索引（VGX）
    顶点 = texcoord.buf 里的顶点格式

先选这次用哪一组参照（一组 = dump\ 里的一个文件夹，不按角色合并），
再把那个 mod 的文件夹拖进来，两类问题一起查、一起修：

    一、骨骼索引（VGX）
        blend.buf 里的骨骼索引被写错了
        症状：模型变形（腿弯、塌陷、扭曲），贴图正常
        做法：按角色表把索引逐个换成正确的

    二、顶点格式（texcoord）
        游戏更新改了顶点格式，老 mod 的 buf 布局对不上
        症状：贴图整体错乱，模型形状完全正常
        做法：按目标表重排每个顶点的字节，并同步改 ini 里的 stride

    两类互相独立，哪个命中修哪个；都没命中就什么都不做。

两套模式（启动时选；拖放界面输 m 可以换）
    1 = 索引与顶点修复（默认）
        就是上面说的这两样：VGX 按角色表，texcoord 按 TEXCOORD_TARGETS
        或 dump 参照。要选一组参照。

    2 = 通用脸部修复
        3.1 -> 3.2 更新里 texcoord 变过的那批网格，只有一种变化，写死在
        代码里，不用填格式，也不需要参照：
            texcoord 里最前面那块顶点 COLOR 4 字节（R8G8B8A8_UNORM）
            -> 4 个 float，每顶点多 12 字节（旧 36 -> 新 48 字节/顶点）
        只认 UNIVERSAL_HASHES 那张名单（53 个网格 / 46 个角色，输 3 看名单）。
        这个模式只动 texcoord buf 和 ini 里的 stride，骨骼索引（VGX）不碰。

用法
    双击 本脚本：
        第一步  选这次用哪组参照（dump\ 里有几个文件夹就列几组）
        第二步  把【那个 mod 的文件夹】拖进窗口，按 Enter，
                再选 1 = 修复 / 2 = 还原 / 回车 = 跳过 / q = 退出

    修复时会先把两类问题都列出来，输入 queren 确认后一起写；
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
    贴图格式：json 里的 hash / 当前格式，旧格式按 buf 实际大小倒推
    VGX    ：同一个网格文件夹里再放 -*Blend.buf 和 -*Position.buf，
             工具按位置配对逐顶点投票，自己推出索引映射
两张表（TEXCOORD_TARGETS / VGX_CHARACTERS）里已有的都能用，
跟 dump 撞上时会问一次用哪个。
"""

import os
import re
from array import array
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
MODE_NAMES = {'normal': '索引与顶点修复', 'universal': '通用脸部修复'}
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
        for line in resource_match.group(1).splitlines():
            if line_match := line_pattern.match(line):
                paths.append(ini_filepath.parent / line_match.group(1).strip())
                break
    return paths


def vgx_remap(buffer: bytes, table: dict) -> bytes:
    """按映射表重写 blend.buf 的骨骼索引，权重不动"""
    out = bytearray()
    stride = 32
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
        order_d = sorted(range(4), key=lambda k: -dump_w[k])
        for _d2, i in found:
            mod_w, mod_i = mod_blend[i]
            order_m = sorted(range(4), key=lambda k: -mod_w[k])
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


def buf_by_slot(ini_path: Path, text: str, hash_value, slots):
    """按 hash 找节，再顺着 vb0 / vb2 找缓冲文件"""
    body = section_by_hash(text, hash_value)
    if body is None:
        return None
    for slot in slots:
        for resource in follow_slot_resources(text, body, slot):
            definition = find_resource_definition(text, resource)
            if not definition:
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
        blend_path = buf_by_slot(ini_path, text, hash_value, ('vb2',))
        if blend_path:
            break
    if not blend_path:
        return None

    # position：同名前缀的先试，再看 ini 里 vb0 指到哪
    stem = blend_path.name[:-4].replace('Blend', 'Position').replace('blend', 'position')
    pos_path = blend_path.with_name(stem + '.buf')
    if not pos_path.exists():
        pos_path = None
        for hash_value in (info.get('position_hash'), info.get('blend_hash')):
            pos_path = buf_by_slot(ini_path, text, hash_value, ('vb0',))
            if pos_path:
                break
    if not pos_path:
        return None

    return blend_path, pos_path


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

    hits = {}
    for ini_filepath in ini_filepaths:
        try:
            ini_content = ini_filepath.read_text(encoding='utf-8', errors='replace')
        except Exception:
            traceback.print_exc()
            return [], 0, '读取失败 "{}"'.format(ini_filepath)

        for character in VGX_CHARACTERS:
            for position_hash in character.get('hashes', []):
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

        # 这几行先攒着不打印：如果用户等下选了"用 dump 自动推"，这几行就过期了
        planned.append({
            'buf': blend_path, 'table': tables[0], 'label': label,
            'lines': ['- [VGX] "{}"  [{}]'.format(blend_path, label),
                      '        骨骼索引重映射（用表）'],
        })

    return planned, skipped, None


def vgx_apply(planned, total=None, done0=0):
    for index, item in enumerate(planned, 1):
        buf = item['buf']
        original = buf.read_bytes()
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
        if len(old_format) != len(new_format):
            print(c('[配置错误] {}: old_format 有 {} 块，new_format 有 {} 块，必须一样多'.format(
                name, len(old_format), len(new_format)), Style.RED))
            ok = False
            continue
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


def follow_slot_resources(text, body, slot, depth=0):
    """收集 slot = xxx（vb1/vb2）；遇到 run = CommandList 追进去"""
    if depth > 5:
        return []
    resources = []
    for m in VB_LINE_RE.finditer(body):
        key, value = m.group(1).lower(), m.group(2).strip()
        if key == slot:
            resources.append(value)
        elif key == 'run':
            for title, start, end in split_sections(text):
                if title.strip().lower() == value.lower():
                    resources.extend(follow_slot_resources(text, text[start:end], slot, depth + 1))
                    break
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


def tex_convert(data: bytes, count: int, old_format, new_format) -> bytes:
    """按元素块逐个转换（写法和版本修复工具 zzz_13_remap_texcoord 一致）"""
    if len(old_format) != len(new_format):
        raise ValueError('old_format 和 new_format 的元素个数必须一样')

    old_stride = fmt_stride(old_format)
    offsets = [0]
    for chunk in old_format:
        offsets.append(offsets[-1] + struct.calcsize('<' + chunk))

    out = bytearray()
    for i in range(count):
        base = i * old_stride
        for j, (old_chunk, new_chunk) in enumerate(zip(old_format, new_format)):
            if offsets[j] >= old_stride:          # 超出旧缓冲范围，补 0
                out.extend(struct.pack('<' + new_chunk, *([0] * fmt_count(new_chunk))))
                continue
            if old_chunk == new_chunk:            # 没变，原样搬
                out.extend(data[base + offsets[j]: base + offsets[j + 1]])
                continue
            # 颜色块：字节 0-255 和 0.0-1.0 的浮点 / 半浮点互转（不是原样搬数值）
            if old_chunk == '4B' and new_chunk == '4f':
                out.extend(struct.pack('<4f', *[b / 255.0 for b in struct.unpack_from('<4B', data, base + offsets[j])]))
            elif old_chunk == '4f' and new_chunk == '4B':
                values = [min(255, max(0, int(round(f * 255)))) for f in struct.unpack_from('<4f', data, base + offsets[j])]
                out.extend(struct.pack('<4B', *values))
            elif old_chunk == '4B' and new_chunk == '4e':
                out.extend(struct.pack('<4e', *[b / 255.0 for b in struct.unpack_from('<4B', data, base + offsets[j])]))
            elif old_chunk == '4e' and new_chunk == '4B':
                values = [min(255, max(0, int(round(f * 255)))) for f in struct.unpack_from('<4e', data, base + offsets[j])]
                out.extend(struct.pack('<4B', *values))
            else:                                  # 其他块按格式重新打包
                out.extend(struct.pack('<' + new_chunk, *struct.unpack_from('<' + old_chunk, data, base + offsets[j])))
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

        # 同一个文件夹里 3DMigoto 还会 dump 出 -*Blend.buf / -*Position.buf
        # 有这两个（且都能被 32 / 40 整除）才能自动推 VGX 映射
        blend_buf = position_buf = None
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
        except OSError:
            pass

        meshes[tex_hash] = {
            'mesh': json_path.name.split('-')[0],
            'character': character,
            'new_format': tuple(dxgi_chunk(str(e.get('Format', '')), int(e.get('ByteWidth', 0)))
                                for e in elements),
            'blend_hash': hashes.get('blend'),
            'position_hash': hashes.get('position'),
            'blend_buf': blend_buf,
            'position_buf': position_buf,
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
        if legacy.is_dir():
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
            ALL_DUMPS.update(load_dump_folder(folder))
    set_active_dumps(None)


def character_of(info: dict) -> str:
    """参照分组名 —— 按 dump 里的【文件夹名】走，不做角色归类。

    子文件夹里的 json 取它所在的一级文件夹名；直接放 dump\\ 根目录的取文件名。
    文件名里带 '-' '_' 也不拆：一个文件夹 = 一组参照 = 一次修复的范围。
    拆了就会把已经修过的那组一起带上，同一个网格修两遍。
    """
    name = info.get('character') or info.get('mesh') or '?'
    return name


def character_groups(dumps: dict = None) -> dict:
    """按参照分组（dump 里的文件夹）-> {组名: [tex_hash, ...]}"""
    groups = {}
    for tex_hash, info in (dumps or ALL_DUMPS).items():
        groups.setdefault(character_of(info), []).append(tex_hash)
    return groups


def set_active_dumps(character):
    """把生效的 dump 限定到某一组参照；None = 全都用"""
    DUMP_MESHES.clear()
    if character is None:
        DUMP_MESHES.update(ALL_DUMPS)
        return
    for tex_hash, info in ALL_DUMPS.items():
        if character_of(info) == character:
            DUMP_MESHES[tex_hash] = info


def dump_mesh_names(character) -> str:
    """这组参照下都有哪些网格（显示用）"""
    names = sorted({Path(ALL_DUMPS[h].get('source') or '').stem or '?'
                    for h in character_groups().get(character, [])})
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


def dump_hint():
    """没有 dump 时不建文件夹，只提示放哪儿

    原来这里是"没有就自动建一个空的 + 塞一份说明"，去掉了：
    自动建的位置一错（脚本在子目录、exe 在别处），用户看到的是"空 dump 已就绪"，
    会以为是作者没放数据。宁可什么都不建，把位置说清楚。
    """
    places = dump_places()
    print(c('dump\\ 里没有数据。', Style.YELLOW))
    print('  这个文件夹程序不自动建，自己放一份就行（两处都认，都有时后者优先）：')
    for folder in places:
        print('    {}'.format(folder))
    print('  一个参照一个子文件夹（名字写成「角色-部位」），里面放游戏内 F8 抓的 json；')
    print('  要推骨骼索引（VGX）就再放同一网格的 -*Blend.buf 和 -*Position.buf。')
    print('  没有它也能用：表里写死的那些网格照旧能修，只有靠 dump 推的认不出来。')
    print('  详细说明见程序目录的 使用说明.txt。')
    print()


def load_dump_into_session(folder: Path):
    """运行时把 dump 文件夹拖进来，返回 (新增网格数, 共读到几个, 新增的分组名)"""
    found = load_dump_folder(folder)
    added = 0
    names = set()
    for tex_hash, info in found.items():
        if tex_hash not in ALL_DUMPS:
            added += 1
            names.add(character_of(info))
        ALL_DUMPS[tex_hash] = info
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
    """
    if use_dump_for_conflicts is None:
        use_dump_for_conflicts = PREFER_DUMP
    skip_from_dump = set() if use_dump_for_conflicts else table_hashes()
    skip_from_table = table_hashes() if use_dump_for_conflicts else set()

    entries = [entry for entry in TEXCOORD_TARGETS
               if str(entry.get('hash', '')).lower() not in skip_from_table]
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
            elif old_format:
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

        inferred = None
        if from_dump and not old_format:
            if per_vertex == new_stride:
                print('- [格式] {}  "{}"  {}'.format(
                    label, buf, c('已是新格式({})，跳过'.format(new_stride), Style.YELLOW)))
                skipped += 1
                continue
            candidates = infer_old_formats(new_format, per_vertex)
            if not candidates:
                print('- [格式] {}  "{}"  {}'.format(
                    label, buf, c('每顶点 {} 字节，推不出对应的旧格式，跳过'.format(per_vertex), Style.YELLOW)))
                print('        （dump 给的当前格式是 {}）'.format(' + '.join(new_format)))
                skipped += 1
                continue
            old_format = candidates[0]
            old_stride = fmt_stride(old_format)
            inferred = len(candidates) > 1

        do_buf = (per_vertex == old_stride)
        do_stride = (item['stride'] == old_stride)

        print('- [格式] {}  "{}"'.format(label, buf))
        if item['target'].get('hash_note'):
            print('        认得它：hash {}'.format(c(item['target']['hash_note'], Style.GREEN)))
        print('        格式 {} -> {} 字节/顶点   顶点数 {}（{}）'.format(
            old_stride, new_stride, count, from_what))
        if inferred is not None:
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
            skipped += 1
            continue
        if do_stride:
            print('        ini 里 stride {} -> {}'.format(old_stride, new_stride))

        if do_buf or do_stride:
            planned.append({
                'buf': buf, 'ini': item['ini'], 'count': count,
                'old_format': old_format, 'new_format': new_format,
                'old_stride': old_stride, 'new_stride': new_stride,
                'stride_span': item['stride_span'], 'do_buf': do_buf, 'do_stride': do_stride,
            })

    return planned, skipped, None


def tex_apply(planned, total=None, done0=0):
    ini_texts = {}
    ini_backed = set()

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
            buf.write_bytes(tex_convert(original, item['count'], item['old_format'], item['new_format']))
            tex_marker_of(buf).write_text('', encoding='utf-8')
            changes.append('buf {} -> {} 字节'.format(len(original), buf.stat().st_size))

        if item['do_stride']:
            text = load_ini(ini_path)
            start, end = item['stride_span']
            if text[start:end] == str(item['old_stride']):
                text = text[:start] + str(item['new_stride']) + text[end:]
                ini_texts[str(ini_path)] = text
                changes.append('stride {} -> {}'.format(item['old_stride'], item['new_stride']))

        if changes:
            ensure_ini_backup(ini_path)
            print(c('已修 [格式]: "{}"  [{}]'.format(buf.name, ' ； '.join(changes)), Style.GREEN))
        iv_progress(done0 + index, total or len(planned), buf.name)

    for key, text in ini_texts.items():
        Path(key).write_text(text, encoding='utf-8')


# ==========================================================================
#  三、还原
# ==========================================================================

def restore(target: Path):
    """把本工具改过的文件按备份退回（VGX + 格式 一起）"""
    buf_backups = []
    for suffix in (VGX_BACKUP_SUFFIX, TEX_BACKUP_SUFFIX, TEX_LEGACY_BACKUP_SUFFIX):
        buf_backups.extend(sorted(target.rglob('*' + suffix)))
    ini_backups = []
    for suffix in (TEX_INI_BACKUP_SUFFIX, TEX_LEGACY_INI_BACKUP_SUFFIX):
        ini_backups.extend(sorted(target.rglob('*' + suffix)))

    if not buf_backups and not ini_backups:
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
    print(c('还原完成。', Style.GREEN))


# ==========================================================================
#  四、修复主流程
# ==========================================================================

def apply_fix(target: Path):
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
        return
    if which:
        print('参照比对：ini 里的 hash {} 命中本次参照【{}】'.format(which, ref_scope_text()))
    print()

    if not validate_vgx() or not validate_texcoord():
        print()
        print(c('表里有写错的地方，先改好再跑。已中止。', Style.RED))
        return

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

    if not vgx_items and not tex_items:
        print(c('没有需要处理的文件。', Style.YELLOW))
        return

    summary = '将修改：VGX 骨骼索引 {} 个 buf、顶点格式 {} 个 buf（改前都会备份）'.format(
        len(vgx_items), len(tex_items))
    print(c('不要对不需要修复的 mod 运行本工具!!!', Style.RED))
    print(c('不要在同一个 buf 上运行两次!!!', Style.RED))
    if not iv_asker().confirm(summary):
        print(c('已取消，没有改动任何文件。', Style.YELLOW))
        return

    total = len(vgx_items) + len(tex_items)
    print()
    if vgx_items:
        print('应用 VGX 重映射中...')
        vgx_apply(vgx_items, total, 0)
    if tex_items:
        print('应用格式重排中...')
        tex_apply(tex_items, total, len(vgx_items))

    print()
    print(c('完成!', Style.GREEN))
    print('备份后缀: {} / {}'.format(VGX_BACKUP_SUFFIX, TEX_BACKUP_SUFFIX))


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
        print('  {} = 看通用脸部修复能修哪些角色（看完回来接着选）{}'.format(
            c('3', Style.GREEN), Style.RESET))
        answer = ask('  选 1 / 2 / 3（回车 = 1）: ').strip().lower()
        if answer in ('3', '名单', 'list', 'l'):
            show_universal_list()
            continue
        FIX_MODE = 'universal' if answer in ('2', '通用', 'universal', 'u') else 'normal'
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
    print('  一次拖一个 mod 文件夹进去，两类问题一起查、一起列、一次确认、一起修。')
    print()
    print('  一、骨骼索引（VGX）')
    print('      症状：模型变形 —— 腿弯、塌陷、扭曲，但贴图正常')
    print('      做法：按角色表把 blend.buf 里的骨骼索引逐个换成正确的')
    print()
    print('  二、顶点格式（texcoord）')
    print('      症状：贴图整体错乱，但模型形状完全正常')
    print('      做法：按目标表重排每个顶点的字节，并同步改 ini 里的 stride')
    print()
    print('  两类互相独立，哪个命中修哪个；都没命中就什么都不做。')
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
    elif FIX_MODE == 'universal':
        apply_universal(target)
    else:
        apply_fix(target)


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
    print('  输入 {}{}{} 换模式（索引与顶点修复 / 通用脸部修复）'.format(Style.GREEN, 'm', Style.RESET))
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
                print(c('  dump\\ 里还没有数据（放哪儿见启动时的提示）。', Style.YELLOW))
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

    refresh_dumps()
    if not ALL_DUMPS:
        dump_hint()

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
