#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZZZ 不同角色 Mod 冲突自动修复工具（XXMI 新格式）
作者：踩蘑菇网 绿林小子
    不同角色mod产生冲突的原因，基本上是 mod 使用了 position 的 hash 制作（该 hash 被多个
    角色共享，如露西头发 position hash 6c733c84）。XXMI 的新格式使用角色专属的
    blend hash（如露西头发 a37c7537 / 5315f036），并把 position 节的绘制内容移入
    blend 节、用 "if DRAW_TYPE == 1" 包裹，即可避免角色间的冲突。

定位方式：
    只处理 vb.txt 中列出的哈希（position_vb / position_wallpaper_vb / blend_vb）。
    结构信息（节名 *Position/*Blend、资源名 ResourceXXXPosition/Blend）用于
    辅助匹配对应 blend 节；哈希全部变动时，程序会提示把新哈希追加到 vb.txt，
    更新后重新运行即可正常修复。

用法：
    1. 把本程序放在 Mod 文件夹中直接运行 → 自动修复当前目录下所有 Mod；
    2. 将文件夹或 ini 文件拖到程序图标上 → 修复拖入的路径。
    （程序会把工作目录固定为自身所在目录，双击或右键"用 Python 打开"
    行为一致，均以程序所在目录为基准；拖入的路径使用绝对路径不受影响）
    （递归处理所有 .ini，跳过 DISABLED* 文件，自动备份为 *.bak）
    可选参数：
    --dry-run        只预览不修改
    --vb <文件>      指定哈希表文件（默认自动查找当前目录或程序目录下的 vb.txt）

    只处理 vb.txt 中列出的哈希（正常 position 迁移、背景/变体节保留 hash 行、
    blend 哈希定位）；未列出的哈希一律忽略。
    文件内 blend hash 与 vb.txt 不一致时仅提示（在 vb.txt 中追加新哈希即可）。
    迁移失败（找不到对应 blend 节）时保持原配置，不删除内容。
"""

import os
import re
import sys
import argparse
import shutil

# ---------------- 控制台 UTF-8（避免 Windows 控制台中文乱码） ----------------
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

if getattr(sys, 'frozen', False):
    # PyInstaller 打包后 __file__ 指向临时解包目录（_MEIxxxx），
    # 程序目录应为 exe 所在目录。
    SCRIPT_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_VB = os.path.join(SCRIPT_DIR, 'vb.txt')

# 内置默认哈希表：程序可单独运行。
# 以后哈希更新或想添加新哈希/新角色时，把更新后的 vb.txt 放到本程序
# 同目录，程序会优先读取外部 vb.txt 覆盖内置默认值。
DEFAULT_VB_CONTENT = '''露西
position_vb: 6c733c84
position_wallpaper_vb: 39cfd24c,9b4dfd86
blend_vb: a37c7537,5315f036

青衣
position_vb: a5783704
blend_vb: 57c9f0a3
'''


def find_vb():
    """定位 vb.txt：当前工作目录优先（程序与 vb.txt 放同一文件夹直接运行），
    其次脚本所在目录；均不存在时使用内置默认哈希表。"""
    for cand in (os.path.join(os.getcwd(), 'vb.txt'),
                 os.path.join(SCRIPT_DIR, 'vb.txt')):
        if os.path.exists(cand):
            return cand
    return None

POSITION_RE = re.compile(r'Resource\s*(\w+?)\s*Position\b', re.I)
BLEND_RE = re.compile(r'Resource\s*(\w+?)\s*Blend\b', re.I)
HASH_RE = re.compile(r'[0-9a-fA-F]{8}')
# 宽松匹配：Resource 与 Position/Blend 字样之间允许少量乱码字符
# （文件编码异常、字节损坏时仍能识别），如 vb0 = Resourc锟斤拷e198e99d7Position
POSITION_RE_LOOSE = re.compile(r'Resource.{0,4}?(\w+?)Position\b', re.I | re.S)
BLEND_RE_LOOSE = re.compile(r'Resource.{0,4}?(\w+?)Blend\b', re.I | re.S)


# ---------------- vb.txt 解析 ----------------
def parse_vb(text, label):
    """从文本解析哈希表，格式示例：
        露西
        position_vb: 6c733c84
        blend_vb: a37c7537,5315f036

        青衣
        position_vb: a5783704
        blend_vb: 57c9f0a3
    返回 [(角色名, {key: [哈希,...]}), issues]；label 用于错误提示（文件路径或"内置默认"）。
    """
    chars = []
    issues = []
    cur = None
    for lineno, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if not s or s.startswith('#') or s.startswith(';'):
            continue
        mm = re.match(r'^([^:=]+?)\s*:\s*(.+?)\s*$', s)
        if mm and mm.group(1).strip().lower().endswith('_vb'):
            key = mm.group(1).strip().lower()
            if cur is None:
                issues.append('{} 第{}行: "{}" 出现在角色名之前，已忽略'.format(label, lineno, key))
                continue
            vals = [v.strip() for v in re.split(r'[,，]', mm.group(2)) if v.strip()]
            for v in vals:
                if not HASH_RE.fullmatch(v):
                    issues.append('{} 第{}行: "{}" 不是 8 位十六进制哈希，已忽略'.format(label, lineno, v))
                    continue
                v = v.lower()
                if v not in cur[1].setdefault(key, []):
                    cur[1][key].append(v)
        elif mm and ':' in s:
            # 形如 "xxx: yyy" 但不是 _vb 结尾 → 字段名可能拼写错误，提示后忽略
            issues.append('{} 第{}行: "{}" 不是 _vb 字段，已忽略'.format(label, lineno, s))
        else:
            cur = (s, {})
            chars.append(cur)
    return chars, issues


def load_vb(path):
    """读取 vb.txt 文件；路径为空或文件不存在时返回 (None, [])。"""
    if not path or not os.path.exists(path):
        return None, []
    with open(path, 'r', encoding='utf-8-sig') as f:
        return parse_vb(f.read(), path)


def merge_chars(inner, outer):
    """合并两组角色哈希表：内置默认（inner）始终生效，外部（outer）追加新角色、
    同名角色合并哈希（内置与外部并集）。"""
    merged = []
    outer_by_name = {name: d for name, d in outer}
    for name, d in inner:
        if name in outer_by_name:
            od = outer_by_name.pop(name)
            nd = {}
            for k in set(d) | set(od):
                nd[k] = list(dict.fromkeys(d.get(k, []) + od.get(k, [])))
            merged.append((name, nd))
        else:
            merged.append((name, d))
    merged.extend(outer_by_name.items())
    return merged


# ---------------- INI 解析 ----------------
def parse_ini(text):
    """按行解析 ini，返回 (行列表, 节列表)。
    节: {'name','start','end','body'}，body 为节头之后、下一节头之前的所有行。"""
    lines = text.split('\n')
    headers = [i for i, l in enumerate(lines)
               if l.lstrip().startswith('[') and ']' in l]
    sections = []
    for j, idx in enumerate(headers):
        end = headers[j + 1] if j + 1 < len(headers) else len(lines)
        name = lines[idx][lines[idx].find('[') + 1: lines[idx].find(']')].strip()
        sections.append({'name': name, 'start': idx, 'end': end,
                         'body': lines[idx + 1: end]})
    return lines, sections


def analyze_body(body):
    """
    提取节的顶层键与条件状态。
    返回 ([(key_lower, key_orig, value), ...], has_top_if)
    has_top_if：节体内是否包含顶层 if 块（旧方法修复的特征）。
    """
    keys = []
    depth = 0
    has_top_if = False
    for line in body:
        s = line.strip()
        if not s or s.startswith(';'):
            continue
        low = s.lower()
        if low == 'endif':
            depth = max(0, depth - 1)
            continue
        if low.startswith('else'):
            continue
        if low == 'if' or low.startswith('if '):
            if depth == 0:
                has_top_if = True
            depth += 1
            continue
        if depth > 0:
            continue
        if '=' in s:
            k, v = s.split('=', 1)
            keys.append((k.strip().lower(), k.strip(), v.strip()))
    return keys, has_top_if


def extract_all_keys(body):
    """提取节内全部键（忽略 if/else/endif 结构，用于旧方法节转换）。"""
    keys = []
    seen = set()
    for line in body:
        s = line.strip()
        if not s or s.startswith(';'):
            continue
        low = s.lower()
        if low == 'endif' or low.startswith('else') or low == 'if' or low.startswith('if '):
            continue
        if '=' in s:
            k, v = s.split('=', 1)
            kl = k.strip().lower()
            if kl not in seen:
                seen.add(kl)
                keys.append((kl, k.strip(), v.strip()))
    return keys


def get_hash(keys):
    for k, ko, v in keys:
        if k == 'hash':
            return v.lower()
    return None


def get_hashes(body):
    """提取节的哈希：返回 (当前 hash, [注释掉的 hash 列表])。
    注释 hash（`; hash = xxxxxxxx`）是作者留下的有效历史/备选值，
    定位时同样考虑——只要任一在 vb.txt 中，该节即可按已知处理。"""
    active = None
    commented = []
    for line in body:
        s = line.strip()
        m = re.match(r'^hash\s*=\s*([0-9a-fA-F]{8})', s)
        if m:
            active = m.group(1).lower()
            continue
        m2 = re.match(r'^;\s*hash\s*=\s*([0-9a-fA-F]{8})', s)
        if m2:
            commented.append(m2.group(1).lower())
    return active, commented


def hash_matches(body, hash_set):
    """节的哈希是否在 hash_set 中。
    无论 hash 行是注释的（`; hash = xxx`）还是实际的，只要任一在
    hash_set 中即判定为已知（注释行是作者保留的有效备选/历史值）。"""
    active, commented = get_hashes(body)
    if active is not None and active in hash_set:
        return True
    return any(c in hash_set for c in commented)


def bind_resource(keys, regex, loose_regex=None):
    """从键值中提取资源前缀，如 vb0 = Resource198e99d7Position → 198e99d7。
    先精确匹配；失败时用宽松匹配（容忍 Resource 字样间少量乱码字符）。"""
    for _, _, v in keys:
        m = regex.search(v)
        if m:
            return m.group(1)
    if loose_regex is not None:
        for _, _, v in keys:
            m = loose_regex.search(v)
            if m:
                return m.group(1)
    return None


def sec_role(sec_name):
    """从节名提取角色关键字：Position / Blend（如 TextureOverride198e99d7Position2 → 'position'）。"""
    m = re.search(r'(Position|Blend)\w*', sec_name, re.I)
    return m.group(1).lower() if m else None


def prefix_from_name(sec_name, keyword):
    """兜底：从节名提取资源前缀与角色。
    如 [TextureOverride198e99d7Position] / [TextureOverride198e99d7Position2] → 198e99d7。
    仅当资源匹配完全失败（vb0 值整段乱码）时使用。"""
    m = re.match(r'TextureOverride\+?(\w+?)' + keyword, sec_name, re.I)
    if m:
        return m.group(1)
    return None


def get_prefix(keys, sec_name, allow_blend=False):
    """提取节前缀：先资源名匹配，再节名兜底（Position；blend 类节允许 Blend）。"""
    p = bind_resource(keys, POSITION_RE, POSITION_RE_LOOSE)
    if p is None:
        p = prefix_from_name(sec_name, 'Position')
    if p is None and allow_blend:
        p = prefix_from_name(sec_name, 'Blend')
    return p


def role_of(body, char_sets):
    """节命中哪个角色的哪类哈希；返回 (角色索引, 'pos'/'wall'/'blend') 或 (None, None)。"""
    for i, (_, cs) in enumerate(char_sets):
        for k in ('pos', 'wall', 'blend'):
            if hash_matches(body, cs[k]):
                return i, k
    return None, None


def similarity_warning(h, role, prefix, found_similar, fallback):
    """按节名相似性生成"可能变动"提示：同前缀同角色的在案节存在时给出具体
    提示；否则返回笼统提示 fallback。"""
    match = None
    if role:
        for (p, r), names in found_similar.items():
            if r == role and p == prefix:
                match = names[0]
                break
    if match:
        return 'hash {} 可能是变动的{}哈希（节名与 [{}] 相似），请在 vb.txt 中追加'.format(
            h, role, match)
    return fallback


# ---------------- 修复逻辑 ----------------
def build_merged_block(target_keys_lists):
    """
    把 position 节的内容组装成新格式块（对齐参考修复文件）：
        handling = skip
        vb2 = ResourceXXXBlend
        if DRAW_TYPE == 1
        vb0 = ResourceXXXPosition
        draw = 15613, 0
        endif
    match_priority 等节级属性放 endif 之后。

    每个来源节独立生成一个块：正常 position 与满信赖背景等变体 position
    （draw 值可能不同）会各自成块保留；内容完全相同的块自动合并去重，
    不会产生重复的迁移。
    返回块列表（每块为行列表）。
    """
    blocks = []
    for keys in target_keys_lists:
        pre, inner, post = [], [], []
        for k, ko, v in keys:
            if k == 'hash':
                continue
            if k == 'match_priority':
                if not any(p[0] == k for p in post):
                    post.append((k, ko, v))
            elif k in ('handling', 'vb2'):
                if not any(p[0] == k for p in pre):
                    pre.append((k, ko, v))
            else:
                if not any(p[0] == k for p in inner):
                    inner.append((k, ko, v))
        # handling 在前、vb2 在后（对齐参考修复文件的顺序）
        pre.sort(key=lambda t: 0 if t[0] == 'handling' else 1)
        lines = ['{} = {}'.format(ko, v) for _, ko, v in pre]
        if inner:
            lines.append('if DRAW_TYPE == 1')
            lines += ['{} = {}'.format(ko, v) for _, ko, v in inner]
            lines.append('endif')
        lines += ['{} = {}'.format(ko, v) for _, ko, v in post]
        blocks.append(lines)
    # 内容完全相同的块合并（保持顺序）
    seen = set()
    out = []
    for b in blocks:
        key = tuple(b)
        if key not in seen:
            seen.add(key)
            out.append(b)
    return out


def find_blend_section(sections, prefix, blend_hashes):
    """
    为资源前缀 prefix 寻找目标 blend 节（优先名字匹配，其次哈希匹配，其次 vb2 绑定）。
    绑定 vb0（position 角色）的节一律排除。
    返回 (section, score) 或 None。
    """
    best, best_score = None, -1.0
    for sec in sections:
        if not sec['name'].lower().startswith('textureoverride'):
            continue
        keys, _ = analyze_body(sec['body'])
        if not keys:
            continue                    # 纯注释节（无实际 hash 行）不作为 blend 目标
        name_low = sec['name'].lower()
        if bind_resource(keys, POSITION_RE, POSITION_RE_LOOSE):          # 绑定 position 缓冲 → 不是 blend 节
            continue
        binds_blend = bind_resource(keys, BLEND_RE, BLEND_RE_LOOSE)
        score = 0.0
        if prefix and 'blend' in name_low and prefix.lower() in name_low:
            score += 2.0
        if hash_matches(sec['body'], blend_hashes):     # 含注释掉的 blend hash
            score += 1.0
        if binds_blend:
            score += 0.5
        if score <= 0:
            continue
        # 同名多节时优先"空节"（只有 hash），即典型的待填充 blend 节
        if score == best_score and best is not None:
            _, best_keys = analyze_body(best['body'])
            _, cur_keys = analyze_body(sec['body'])
            if len(cur_keys) < len(best_keys):
                best = sec
            continue
        if score > best_score:
            best, best_score = sec, score
    return best


def keep_hash_only(body):
    """position 节空壳化：只保留 hash 行与注释行，其余内容（vb2/vb0/draw 等）
    已迁移至 blend 节，原节仅作为 hash 占位保留。"""
    keep = []
    for line in body:
        s = line.strip()
        if not s or s.startswith(';'):
            keep.append(line)
            continue
        if s.lower().startswith('hash'):
            keep.append(line)
    return keep


def split_if_blocks(body):
    """
    把节体拆分为 (保留行, if块列表)。
    保留行：hash 行、注释、空行等顶层行（非条件块内）；
    if块：从顶层 if 到匹配 endif 的完整行序列（含原条件，原样保留）。
    有嵌套或不闭合时按最近匹配处理，不闭合的块也照常迁移。
    """
    keep = []
    blocks = []
    depth = 0
    cur = None
    for line in body:
        s = line.strip().lower()
        if s == 'endif':
            if cur is not None:
                cur.append(line)
                depth -= 1
                if depth == 0:
                    blocks.append(cur)
                    cur = None
            continue
        if s == 'if' or s.startswith('if '):
            if depth == 0:
                cur = [line]
                depth = 1
            elif cur is not None:
                cur.append(line)
                depth += 1
            continue
        if s.startswith('else') and cur is not None:
            cur.append(line)
            continue
        if cur is not None:
            cur.append(line)
            continue
        keep.append(line)
    if cur:                                    # 未闭合的 if 块，仍迁移
        blocks.append(cur)
    return keep, blocks


def _is_draw_type_block(blk):
    """块的第一行是否为 if DRAW_TYPE == 1（顶层判断）。"""
    return bool(blk and blk[0].strip().lower().startswith('if')
                and 'draw_type' in blk[0].strip().lower())


def _vb0_wrapped_correctly(blk):
    """vb0 绘制行的直接外层 if 是否为 DRAW_TYPE（正确格式的标志）。
    用 if 栈扫描块结构。"""
    stack = []
    for line in blk:
        s = line.strip().lower()
        if s == 'if' or s.startswith('if '):
            stack.append('draw_type' in s)
        elif s == 'endif':
            if stack:
                stack.pop()
        elif re.match(r'^\s*vb0\s*=', s, re.I):
            if not stack or not stack[-1]:
                return False
    return True


def _needs_draw_type(blk):
    """判断旧方法 if 块是否需要规范化（vb0 未被 DRAW_TYPE 直接包裹）：
    1) 平铺旧方法块：if $hairActive > 0 / vb2 / vb0 … → 需补
    2) 旧版整体套的错误格式：if DRAW_TYPE == 1 / if $cond / vb0 … → 需拆
    3) 正确格式：外层条件 + if DRAW_TYPE == 1 直接包 vb0 → 不动"""
    if not any(re.match(r'^\s*vb0\s*=', l, re.I) for l in blk):
        return False
    return not _vb0_wrapped_correctly(blk)


def normalize_block(blk):
    """把 blend 节中的 position 块规范化为目标格式：
    if DRAW_TYPE == 1 只包住 vb0 / draw（不再套在最外层条件上）。"""
    if not blk:
        return []
    if _is_draw_type_block(blk):
        inner = blk[1:-1]
        if not inner:
            return blk
        if inner[0].strip().lower().startswith('if'):
            return wrap_vb0_with_draw_type(inner)   # 拆掉外层，处理内层条件块
        return blk                                  # 已是目标格式
    return wrap_vb0_with_draw_type(blk)             # 平铺旧方法块


def wrap_vb0_with_draw_type(blk):
    """在旧方法 if 块内部，用 if DRAW_TYPE == 1 包住 vb0 / draw 绘制行，
    对齐参考修复格式：handling / vb2 等键排在 DRAW_TYPE 判断之外。
    仅处理平铺的旧方法块（if … endif，无深层嵌套）；原块条件与内容保留。"""
    if not blk:
        return []
    out = [blk[0]]                    # 外层 if 行（原条件，如 $hairActive > 0）
    outer = []                        # 顶层非绘制键（handling / vb2 / 其它）
    inner = []                        # 顶层绘制键（vb0 / draw）
    wrapped = False
    depth = 0
    for line in blk[1:]:
        s = line.strip()
        low = s.lower()
        if low == 'if' or low.startswith('if '):
            depth += 1
            (inner if wrapped else outer).append(line)
            continue
        if low == 'endif':
            if depth > 0:
                depth -= 1
                (inner if wrapped else outer).append(line)
                continue
            break                       # 外层块的 endif
        if depth == 0 and re.match(r'^\s*(vb0|draw)\s*=', s, re.I):
            wrapped = True
            inner.append(line)
        elif depth == 0:
            outer.append(line)              # 顶层非绘制键（handling/vb2）始终在外层
        else:
            (inner if wrapped else outer).append(line)
    out.extend(outer)
    if wrapped:
        out.append('if DRAW_TYPE == 1')
        out.extend(inner)
        out.append('endif')
    out.append(blk[-1])               # 外层块的 endif
    return out


def build_new_blend_body(blend, blk):
    """构造新的 blend 节体：保留原注释 / hash 行 / 其它键，追加新格式块 blk。
    原节内的 if 条件块（含嵌套、多个块）整体原样保留；若是旧方法迁移遗留的
    position 绘制块（缺 DRAW_TYPE），自动补上新方法的 if DRAW_TYPE == 1。
    注意：原键一律保留（含 handling/vb2 等，即使与 blk 重复也无害，
    值相同且保证对已修复文件二次处理时不会丢键）。"""
    keep, blocks = split_if_blocks(blend['body'])
    new_body = list(keep)
    new_body.extend(blk)
    for blk0 in blocks:
        if _needs_draw_type(blk0):
            # 升级遗留块：规范化为新方法格式（DRAW_TYPE 只包 vb0）
            new_body.extend(normalize_block(blk0))
        else:
            new_body.extend(blk0)                   # 原 if 块整体保留
    # 原节体以空行结尾时，保留一个空行作为节间分隔
    if blk and blend['body'] and not blend['body'][-1].strip():
        new_body.append('')
    return new_body


def find_upgrade_targets(sections, blend_hashes):
    """寻找需升级的 blend 节：节内存在旧方法迁移遗留的 position 绘制块
    （缺新方法 if DRAW_TYPE == 1）。此类文件 position 节已空壳，没有可迁移
    内容，但 blend 节需要补上新方法的判断。"""
    targets = []
    for sec in sections:
        if not sec['name'].lower().startswith('textureoverride'):
            continue
        if 'blend' not in sec['name'].lower():
            continue
        keys, _ = analyze_body(sec['body'])
        if not keys:
            continue                    # 纯注释节（无实际 hash 行）不升级
        binds_blend = bind_resource(keys, BLEND_RE, BLEND_RE_LOOSE)
        if not hash_matches(sec['body'], blend_hashes) and not binds_blend:
            continue
        _, blocks = split_if_blocks(sec['body'])
        if any(_needs_draw_type(b) for b in blocks):
            targets.append(sec)
    return targets


def fix_file(path, chars, args):
    """
    修复单个 ini。返回 (modified, [描述行], [警告行], skipped)。
    """
    report = []
    warns = []
    with open(path, 'rb') as f:
        raw_bytes = f.read()
    has_bom = raw_bytes.startswith(b'\xef\xbb\xbf')
    raw = raw_bytes.decode('utf-8-sig', errors='replace')
    eol = '\r\n' if '\r\n' in raw else '\n'
    text = raw.replace('\r\n', '\n').replace('\r', '\n')
    lines, sections = parse_ini(text)

    # 哈希集合（按角色独立判定）：
    #   每个角色一组 {pos, wall, blend}，节的哈希命中哪个角色的哪类集合，
    #   该节即归属该角色；blend 节查找与一致性检查只用该角色的 blend 集合，
    #   避免跨角色误匹配。同时保留全局并集用于升级/未修复等整体判定。
    char_sets = []
    for name, d in chars:
        cs = {'pos': set(), 'wall': set(), 'blend': set()}
        for key, hs in d.items():
            if 'blend' in key:
                cs['blend'].update(hs)
            elif key == 'position_vb':
                cs['pos'].update(hs)
            else:
                cs['wall'].update(hs)
        char_sets.append((name, cs))
    pos_hashes = set().union(*(cs['pos'] for _, cs in char_sets))
    wallpaper_hashes = set().union(*(cs['wall'] for _, cs in char_sets))
    blend_hashes = set().union(*(cs['blend'] for _, cs in char_sets))

    all_sets = pos_hashes | wallpaper_hashes | blend_hashes

    # ---- 预解析：一次扫描缓存每个节的解析结果，供后续检查复用 ----
    info = {}
    for sec in sections:
        if not sec['name'].lower().startswith('textureoverride'):
            continue
        keys, has_top_if = analyze_body(sec['body'])
        all_keys = extract_all_keys(sec['body'])
        active, commented = get_hashes(sec['body'])
        info[id(sec)] = {
            'keys': keys, 'all_keys': all_keys, 'has_top_if': has_top_if,
            'active': active, 'commented': commented,
            'h': active or (commented[0] if commented else None),
            'has_vb0': (any(k == 'vb0' for k, _, _ in keys)
                        or any(k == 'vb0' for k, _, _ in all_keys)),
            'has_vb2': (any(k == 'vb2' for k, _, _ in keys)
                        or any(k == 'vb2' for k, _, _ in all_keys)),
        }

    # 在案节（任一哈希在 vb.txt 中）的 (前缀, 角色) → 节名，供相似性提示
    found_similar = {}
    for sec in sections:
        iv = info.get(id(sec))
        if iv is None or not hash_matches(sec['body'], all_sets):
            continue
        role = sec_role(sec['name'])
        p = get_prefix(iv['all_keys'], sec['name'], allow_blend=True)
        if role and p:
            found_similar.setdefault((p, role), []).append(sec['name'])

    # ---- 互补检查：只找到 position 或 blend 哈希之一时，按节名相似性提示 ----
    sec_view = []
    for sec in sections:
        iv = info.get(id(sec))
        if iv is None or not iv['h']:
            continue
        role = sec_role(sec['name'])
        if role not in ('position', 'blend'):
            continue
        sec_view.append((get_prefix(iv['all_keys'], sec['name'], allow_blend=True),
                         role, iv['h'], sec['name'], sec['body']))

    # 互补检查按角色独立进行：每个角色单独判定 position / blend 是否单边缺失
    for _, cs in char_sets:
        pos_ok = [v for v in sec_view if v[1] == 'position'
                  and hash_matches(v[4], cs['pos'] | cs['wall'])]
        blend_ok = [v for v in sec_view if v[1] == 'blend' and hash_matches(v[4], cs['blend'])]

        if pos_ok and not blend_ok:
            for p, role, h, name, body in sec_view:
                if role == 'blend' and not hash_matches(body, cs['blend']):
                    base = next((v[3] for v in pos_ok if v[0] == p), None)
                    if base:
                        warns.append('找到 position 哈希但未找到对应 blend 哈希：hash {}（节名与 [{}] 相似）可能已变动，请在 vb.txt 中追加'.format(h, base))
                        break
        elif blend_ok and not pos_ok:
            for p, role, h, name, body in sec_view:
                if role == 'position' and not hash_matches(body, cs['pos'] | cs['wall']):
                    base = next((v[3] for v in blend_ok if v[0] == p), None)
                    if base:
                        warns.append('找到 blend 哈希但未找到对应 position 哈希：hash {}（节名与 [{}] 相似）可能已变动，请在 vb.txt 中追加'.format(h, base))
                        break

    # 文件是否"未修复"：存在 hash 在 vb.txt 中的裸 position 节（该修未修）。
    # 只有未修复的文件才会提示"存在不在 vb.txt 中的哈希"。
    has_unfixed = False
    for sec, iv in ((s, info.get(id(s))) for s in sections):
        if (iv is None or 'blend' in sec['name'].lower()
                or iv['has_top_if'] or not iv['has_vb0']):
            continue
        if hash_matches(sec['body'], all_sets):
            has_unfixed = True
            break

    # ---- 按节分类：只处理 vb.txt 中列出的哈希，未列出的节一律忽略 ----
    fix_targets = {}      # prefix -> [(section, keys)] 精确层 L1 + 退化层 L2
    wall_sections = []    # (section, prefix, keys) 背景/变体节（仅空壳化）
    old_fixed = []        # 旧方法 if 包裹的正常 position 节
    noticed = False       # 本文件是否已提示"存在不在 vb.txt 中的哈希"（每文件提示一次）

    for sec in sections:
        iv = info.get(id(sec))
        if iv is None:
            continue
        keys, has_top_if = iv['keys'], iv['has_top_if']
        all_keys, h = iv['all_keys'], iv['h']
        if not keys and not all_keys:
            continue
        # 乱码通常出现在值中（vb0 = 乱码），键名 vb0 本身是 ASCII 不受影响，
        # 因此用"vb0 键是否存在"判断 position 角色；hash 定位为主，资源名
        # 提取失败不影响处理（blend 节查找会回退到 hash 匹配）。
        prefix = get_prefix(keys, sec['name'])
        ci, ck = role_of(sec['body'], char_sets)   # 归属角色与类型（按角色独立判定）
        if not iv['has_vb0']:
            # blend 类节（绑定 vb2 缓冲）：hash 不在案且文件未修复 → 提示可能变动
            if (iv['has_vb2'] and h and not noticed and has_unfixed
                    and ci is None):
                noticed = True
                warns.append(similarity_warning(
                    h, sec_role(sec['name']),
                    get_prefix(keys, sec['name'], allow_blend=True),
                    found_similar,
                    '存在不在 vb.txt 中的哈希（可能已变动），未处理；请在 vb.txt 中追加'))
            continue                                # 非 position 角色节
        if has_top_if:
            # 旧方法修复的节：vb2/vb0 等键都在 if 块内，只按 hash 判定
            if ck == 'wall':
                # 背景/变体节：即使旧方法 if 包裹，也只保留 hash 行（默认执行）
                wall_sections.append((sec, prefix, all_keys, ci))
            elif ck == 'pos':
                old_fixed.append((sec, h, ci))
            elif ck == 'blend':
                pass                            # 已修复 blend 节（含迁移的 vb0 + if 块）→ 跳过
            # 已修复（if 包裹）的节不在 vb.txt 中 → 不提示
            continue
        key = (ci, prefix)                      # 分组键：角色 + 前缀
        if ck == 'pos':
            fix_targets.setdefault(key, []).append((sec, keys))             # 精确层 L1
        elif ck == 'wall':
            wall_sections.append((sec, prefix, keys, ci))                   # 背景/变体：仅空壳化
        elif ck == 'blend':
            if 'blend' in sec['name'].lower():
                pass                        # blend 节本身（作者手写的扁平格式）→ 跳过
            else:
                # 退化节 L2（blend 哈希但绑定 position 缓冲）
                fix_targets.setdefault(key, []).append((sec, keys))
        elif (h and not noticed and has_unfixed
              and ci is None):
            # 未修复文件里存在不在 vb.txt 中的哈希（可能已变动）：不修复，提示用户更新。
            noticed = True
            warns.append(similarity_warning(
                h, sec_role(sec['name']), prefix, found_similar,
                '存在不在 vb.txt 中的哈希（可能已变动），未处理；请在 vb.txt 中追加'))

    # 没有任何 position 节需要迁移时，仍可能需升级遗留状态
    # （blend 节已有旧方法迁移块，缺新方法 if DRAW_TYPE == 1）
    upgrade_targets = []
    if not fix_targets and not wall_sections and not old_fixed:
        upgrade_targets = find_upgrade_targets(sections, blend_hashes)
        if not upgrade_targets:
            return False, report, warns, old_fixed

    # ---- 第二遍：按（角色, 资源前缀）合并所有待迁移内容，统一修复 ----
    # 同一角色的同一前缀下的裸 position 节与旧方法 if 块会全部合并进
    # 同一个 blend 节，互不排斥；不同角色即使前缀相同也不合并。
    pending = {}    # (角色索引, prefix) -> {'keysets': [...], 'blocks': [...], 'sections': [(sec, 来源)]}

    def _add_pending(key, keys=None, blocks=None, sec=None, source=''):
        p = pending.setdefault(key, {'keysets': [], 'blocks': [], 'sections': []})
        if keys is not None:
            p['keysets'].append(keys)
        if blocks:
            p['blocks'].extend(blocks)
        if sec is not None:
            p['sections'].append((sec, source))

    # 精确层 L1 / 退化层 L2
    for key, tgts in fix_targets.items():
        for sec, keys in tgts:
            _add_pending(key, keys=keys, sec=sec)
    # 旧方法节（if 块包裹的正常 position）：无论是否使用旧方法，都整体迁移
    # —— 整个 if 块（含原条件，如 $hairActive > 0，支持嵌套 / 多个块）
    # 带着旧方法的内容原样迁移到 blend 节，块内用新方法 if DRAW_TYPE == 1
    # 包住 vb0 绘制行（handling / vb2 保持在判断之外，对齐参考修复格式）
    for sec, h, ci in old_fixed:
        prefix = get_prefix(info[id(sec)]['all_keys'], sec['name'])
        if prefix is None:
            continue
        _, blocks = split_if_blocks(sec['body'])
        if not blocks:
            continue
        _add_pending((ci, prefix),
                     blocks=[normalize_block(b) for b in blocks],
                     sec=sec, source='[旧方法] ')

    if not pending and not wall_sections and not upgrade_targets:
        return False, report, warns, old_fixed

    replacements = {}          # 节 start 行 -> 新体行列表
    converted_names = set()

    # ---- 升级遗留状态：blend 节内旧方法迁移的 if 块补上新方法 DRAW_TYPE 判断 ----
    for sec in upgrade_targets:
        replacements[sec['start']] = build_new_blend_body(sec, [])
        report.append('  升级 [{}]：为旧方法迁移的 if 块补上新方法 if DRAW_TYPE == 1'.format(
            sec['name']))
    failed_prefixes = set()
    for (ci, prefix), p in pending.items():
        blend_set = char_sets[ci][1]['blend']        # 该角色的 blend 哈希集合
        blend = find_blend_section(sections, prefix, blend_set)
        if blend is None:
            warns.append('前缀 {}：未找到对应 Blend 节，迁移未执行，保持原配置'.format(prefix))
            failed_prefixes.add((ci, prefix))
            continue
        # blend hash 与 vb.txt 不一致时：迁移无法确认有效，不执行，
        # 保持原配置（在 vb.txt 中追加新哈希后即可正常迁移）。
        # 注释掉的 blend hash 与实际 hash 同时存在且命中 vb.txt 时视为已知。
        orig_keys, _ = analyze_body(blend['body'])
        blend_hash = get_hash(orig_keys)
        if not hash_matches(blend['body'], blend_set):
            warns.append('Blend hash {} 与 vb.txt 不一致，迁移未执行，保持原配置（请在 vb.txt 中追加该哈希）'.format(blend_hash))
            failed_prefixes.add((ci, prefix))
            continue
        # 新格式块（裸节内容，draw 不同各自成块、相同自动合并）+ 原样保留的 if 块
        new_body = build_new_blend_body(blend, [])
        for blk in (build_merged_block(p['keysets']) if p['keysets'] else []):
            new_body.extend(blk)
        for blk0 in p['blocks']:
            new_body.extend(blk0)
        # position 节只保留 hash 行（空壳占位），并输出报告
        for sec, source in p['sections']:
            replacements[sec['start']] = keep_hash_only(sec['body'])
            converted_names.add(sec['name'])
            _a, _c = get_hashes(sec['body'])
            h = _a or (_c[0] if _c else None)
            if source.startswith('[旧方法]'):
                report.append('  [旧方法] 将 [{}] 的 if 块迁移至 [{}]，原节仅保留 hash'.format(
                    sec['name'], blend['name']))
            else:
                report.append('  将 [{}] hash={} 的内容移入 [{}]，原节仅保留 hash'.format(
                    sec['name'], h, blend['name']))
        replacements[blend['start']] = new_body

    old_fixed = [(s, h, ci) for s, h, ci in old_fixed if s['name'] not in converted_names]

    # ---- 背景/变体 position 节：仅空壳化，内容不迁移 ----
    # 背景节（如满信赖背景 39cfd24c）与正常 position 并存时，只迁移正常
    # position，背景节保留 hash 行即可解除对 position hash 的占用，避免
    # blend 节出现重复的迁移块。
    # 迁移失败的前缀：保持原配置，不删除内容。
    for sec, prefix, keys, ci in wall_sections:
        if (ci, prefix) in failed_prefixes:
            warns.append('前缀 {} 迁移失败，[{}] 保持原配置'.format(prefix, sec['name']))
            continue
        replacements[sec['start']] = keep_hash_only(sec['body'])
        report.append('  背景/变体节 [{}] hash={}：仅保留 hash（内容不迁移）'.format(
            sec['name'], get_hash(keys)))

    if not replacements:
        return False, report, warns, old_fixed

    # ---- 重建文件 ----
    out = []
    i = 0
    n = len(lines)
    while i < n:
        if i in replacements:
            out.append(lines[i])               # 保留节头行
            out.extend(replacements[i])        # 新节体
            # 跳过该节原体
            i = next((s['end'] for s in sections if s['start'] == i), i + 1)
            continue
        out.append(lines[i])
        i += 1
    new_text = eol.join(out)

    if new_text == text:
        return False, report, warns, old_fixed

    if args.apply:
        bak = path + '.bak'
        k = 1
        while os.path.exists(bak):
            bak = path + '.bak{}'.format(k)
            k += 1
        shutil.copy2(path, bak)
        with open(path, 'w', encoding='utf-8-sig' if has_bom else 'utf-8', newline='') as f:
            f.write(new_text)
        report.insert(0, '已修复并备份为 {}'.format(os.path.basename(bak)))
    else:
        report.insert(0, '（预览）需要修改，未写入文件（去掉 --dry-run 即直接修复）')
    return True, report, warns, old_fixed


def process_path(path, chars, args, stats):
    if os.path.isdir(path):
        for root, dirs, files in os.walk(path):
            for fn in sorted(files):
                if not fn.lower().endswith('.ini'):
                    continue
                if fn.upper().startswith('DISABLED') or fn.lower().startswith('disabled'):
                    continue
                process_path(os.path.join(root, fn), chars, args, stats)
    elif path.lower().endswith('.ini'):
        fn = os.path.basename(path)
        if fn.upper().startswith('DISABLED') or fn.lower().startswith('disabled'):
            return
        modified, report, warns, old_fixed = fix_file(path, chars, args)
        stats['files'] += 1
        if modified:
            stats['fixed'] += 1
            print('【修复】{}'.format(path))
        elif report or warns or old_fixed:
            stats['noticed'] += 1
            print('【查看】{}'.format(path))
        else:
            print('【跳过】{}'.format(path))
            return
        for ln in report:
            print('  ' + ln)
        for ln in warns:
            print('  ⚠ ' + ln)
        for sec, h, _ci in old_fixed:
            print('  ℹ 旧方法已修复节（未改动）: [{}] hash={}'.format(sec['name'], h or '?'))
        print()


def main():
    # 工作目录固定为程序所在目录：双击运行正常，但右键"用 Python 打开"时
    # CWD 可能落在别处（如 Python 安装目录），导致无参数时处理 "./xxx"
    # 相对路径找不到文件。切回程序目录后，两种启动方式行为一致。
    os.chdir(SCRIPT_DIR)
    ap = argparse.ArgumentParser(
        prog='脸部冲突修复.py',
        description='ZZZ 角色 Mod 冲突自动修复工具（XXMI 新格式，vb.txt 哈希定位）')
    ap.add_argument('paths', nargs='*',
                    help='拖拽到程序图标上的文件夹 / ini 文件（不填则处理当前目录）')
    ap.add_argument('--dry-run', action='store_true', help='只预览不修改（默认直接修复并自动备份 *.bak）')
    ap.add_argument('--vb', default=None, help='指定哈希表文件（默认自动查找当前目录或程序目录下的 vb.txt）')
    args = ap.parse_args()
    args.apply = not args.dry_run   # 默认直接修复

    # ---- 启动横幅（含作者信息） ----
    print('=' * 60)
    print('ZZZ 角色 Mod 冲突修复工具（XXMI 新格式）')
    print('作者：踩蘑菇网 绿林小子')
    print('=' * 60)
    print()

    vb_path = args.vb or find_vb()
    chars, vb_issues = load_vb(vb_path)
    inner, inner_issues = parse_vb(DEFAULT_VB_CONTENT, '内置默认')
    if chars is None:
        # 无外部 vb.txt → 使用内置默认哈希表（程序可单独运行）
        chars, vb_issues = inner, inner_issues
        print('⚠ 未找到外部 vb.txt，使用内置默认哈希表')
        print('  哈希更新或添加新角色时，请将 vb.txt 放到本程序同目录')
    else:
        # 外部 vb.txt 存在 → 与内置默认合并（内置始终生效）
        chars = merge_chars(inner, chars)
        vb_issues = vb_issues + inner_issues
        print('使用哈希表: {}（已合并内置默认）'.format(vb_path))
    for name, d in chars:
        parts = ['{}={}'.format(k, ','.join(v)) for k, v in d.items()]
        print('vb.txt: {}  {}'.format(name, '  '.join(parts)))
    for msg in vb_issues:
        print('⚠ ' + msg)
    print()

    # 拖拽到程序图标上的路径优先处理；无拖拽（双击）时处理当前目录
    stats = {'files': 0, 'fixed': 0, 'noticed': 0}
    if args.paths:
        for p in args.paths:
            if not os.path.exists(p):
                print('⚠ 路径不存在，跳过: {}'.format(p))
                continue
            process_path(p, chars, args, stats)
    else:
        process_path('.', chars, args, stats)
    print('=' * 60)
    print('共检查 {} 个 ini，修复 {} 个，有发现未修复 {} 个{}'.format(
        stats['files'], stats['fixed'], stats['noticed'],
        '（--dry-run 预览模式，未写入）' if not args.apply else ''))

    # 修复完成后保持窗口：可拖放文件/文件夹到窗口继续修复，输入 q 结束
    if sys.stdin and sys.stdin.isatty():
        while True:
            try:
                cmd = input('\n可拖放文件或文件夹到窗口继续修复，或输入 q 结束: ').strip()
            except EOFError:
                break
            if not cmd:
                continue
            if cmd.lower() == 'q':
                break
            # 先试整行：可能是含空格的单个路径（如 C:\My Mods\hair）
            whole = cmd.strip().strip('"')
            if os.path.exists(whole):
                process_path(whole, chars, args, stats)
                continue
            # 整行不是有效路径 → 解析多个路径：
            #   1) 引号包裹的路径优先；2) 无引号的多个含空格路径按"最长匹配"
            #   贪心合并（先试最长的连续组合是否是不存在的路径）。
            quoted = re.findall(r'"([^"]*)"', cmd)
            tokens = re.sub(r'"([^"]*)"', ' ', cmd).split()
            parts = list(quoted)
            i = 0
            while i < len(tokens):
                best, best_len = None, 0
                for j in range(len(tokens), i, -1):
                    cand = ' '.join(tokens[i:j])
                    if os.path.exists(cand):
                        best, best_len = cand, j - i
                        break
                if best is not None:
                    parts.append(best)
                    i += best_len
                else:
                    parts.append(tokens[i])
                    i += 1
            for p in parts:
                if os.path.exists(p):
                    process_path(p, chars, args, stats)
                else:
                    print('⚠ 路径不存在: {}'.format(p))
        print('程序结束，感谢使用。作者：踩蘑菇网 绿林小子')


if __name__ == '__main__':
    main()
