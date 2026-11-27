#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mod快捷键管理工具。

功能：
  * 扫描指定模组目录中的 ini 快捷键（名称、按键、中文说明、条件、选项等）
  * 可直接选择 Mods 文件夹，自动展开角色分类并逐个列出真实模组
  * 支持把模组文件夹、Mods 文件夹或 mod 的 ini 拖进窗口
  * 单击表格单元格直接编辑识别名/默认值；快捷键单元格按键捕获，禁止手输
  * 快捷键松开即自动保存；其他单元格 Enter、失焦或关闭窗口时自动保存
  * 撤销、按文件对照恢复原档；首次修改前创建唯一原档备份
  * 选中模组时自动生成“快捷键_<模组>.txt”表格（有备注用备注作名称）
  * 内部名固定不可改；可改按键和识别名（面板模组的按键锁定）
  * 编辑 ini 默认值（面板模组也允许）
  * 把保存的当前记忆恢复为默认值（写入 d3dx_user.ini）
  * 自动/手动刷新（自动检测 ini 与 d3dx_user.ini 变化）
  * 保存一套快捷键设置，之后选择恢复

“游戏当前值”读取自 3DMigoto 的 d3dx_user.ini；游戏运行中该文件可能不是实时值。
修改 ini / 恢复默认值 / 恢复状态前请先完全退出游戏。首次修改模组 ini 前，会在
模组内创建唯一原档备份。

依赖：Python 3.9+，仅使用标准库（tkinter）。

打包为 exe 后不显示命令窗口；启动时不自动扫描任何目录，需选择或拖入模组目录。
"""

from __future__ import annotations

import argparse
import codecs
import ctypes
import difflib
import json
import os
import queue
import re
import shutil
import sys
import threading
import unicodedata
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# 常量与工具函数
# ---------------------------------------------------------------------------

APP_TITLE = "mod快捷键管理工具"


# 程序的根目录：启动时的当前工作目录。
# 双击 exe 时通常就是 exe 所在文件夹；从其他目录启动时以启动目录为准。
BASE_DIR = Path.cwd()
SNAPSHOT_FILE_NAME = "快捷键状态.json"
LEGACY_SNAPSHOT_FILE_NAME = "快捷键快照.json"
MOD_DATA_DIR_NAME = "快捷键管理"

# ---- 图片菜单面板功能 ----
# 生成含中文的 PNG，并用自带 CustomShader 在游戏内绘制。
PANEL_KEY_SECTION = "KeyZZMIHotkeyImage"
PANEL_SECTION_COMMENT = "图片菜单面板"
PANEL_SHOW_VAR = "zzmi_hotkey_image_show"
PANEL_IMAGE_RESOURCE = "ResourceZZMIHotkeyImage"
PANEL_DRAW_LIST = "CommandListZZMIHotkeyImageDraw"
PANEL_SHADER_SECTION = "CustomShaderZZMIHotkeyImage"
PANEL_IMAGE_FILENAME = "zzmi_hotkey_image.png"
PANEL_SHADER_FILENAME = "zzmi_hotkey_image.hlsl"
# 固定画布，文字贴右下角；ini 位置参数因此与内容无关。
PANEL_IMAGE_WIDTH = 1000
PANEL_IMAGE_HEIGHT = 1000
PANEL_BEGIN = "; >>> ZZMI Hotkey Image BEGIN"
PANEL_END = "; <<< ZZMI Hotkey Image END"
PANEL_SECTION_NAMES = {
    PANEL_KEY_SECTION,
    PANEL_IMAGE_RESOURCE,
    PANEL_DRAW_LIST,
    PANEL_SHADER_SECTION,
}

# 模组管理器禁用文件的后缀/前缀（这些不是当前生效的 ini）
DISABLED_FILE_RE = re.compile(r"(?i)^disabled")
DISABLED_DIR_RE = re.compile(r"(?i)^disabled")

SECTION_RE = re.compile(r"^(?P<indent>[ \t]*)\[(?P<name>[^\]\r\n]+)\](?P<rest>[^\r\n]*)$")
COMMENT_RE = re.compile(r"^\s*([#;])\s*(.*?)\s*$")
KEY_LINE_RE = re.compile(r"^(?P<indent>[ \t]*)key\s*=\s*(?P<value>.+?)\s*$", re.I)
TYPE_RE = re.compile(r"^type\s*=\s*(?P<value>\S+)\s*$", re.I)
CONDITION_RE = re.compile(r"^condition\s*=\s*(?P<value>.+?)\s*$", re.I)
RUN_RE = re.compile(r"^(?:(?:pre|post)\s+)?run\s*=\s*(?P<value>.+?)\s*$", re.I)
VAR_ASSIGN_RE = re.compile(r"^\$(?P<name>[^=\s]+)\s*=\s*(?P<value>.*?)\s*$")
CONST_RE = re.compile(
    r"^global\s+(?P<persist>persist\s+)?(?P<name>\$[^=\s]+)(?:\s*=\s*(?P<value>.*))?$",
    re.I,
)
D3DX_ENTRY_RE = re.compile(r"^\s*(?P<name>\$[^=]+?)\s*=\s*(?P<value>.*?)\s*$")

UI_WORD_RE = re.compile(
    r"(menu|help|panel|hud|hover|navigat|clicked|selected|slot|drag)",
    re.I,
)
UI_ACRONYM_RE = re.compile(
    r"(?:^|[^A-Za-z])(?:UI|ui)(?:$|[^A-Za-z])|(?:[a-z])UI(?:$|[^a-z])"
)
MOUSE_KEY_RE = re.compile(r"VK_(?:L|R|M|X)BUTTON", re.I)
AUX_STATE_RE = re.compile(r"(credit|notif|toast|message|msg)", re.I)


def has_ui_token(text: str) -> bool:
    return bool(UI_WORD_RE.search(text) or UI_ACRONYM_RE.search(text))


def strip_panel_marker_text(text: str) -> str:
    """去掉本工具生成的文字面板标记块，便于面板检测跳过自身。"""
    out: list[str] = []
    skipping = False
    for line in text.splitlines(True):
        marker = line.strip()
        if marker == PANEL_BEGIN:
            skipping = True
            continue
        if marker == PANEL_END:
            skipping = False
            continue
        if not skipping:
            out.append(line)
    return "".join(out)

JSON_INDENT = 2


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def mod_data_dir(mod_path: Path) -> Path:
    return mod_path / MOD_DATA_DIR_NAME


def ensure_mod_data_dir(mod_path: Path) -> Path:
    path = mod_data_dir(mod_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def original_backup_path(path: Path, mod_root: Path) -> Path:
    """原档备份统一放在模组内的“快捷键管理”文件夹。"""
    try:
        relative = path.relative_to(mod_root)
        stem = "_".join(relative.with_suffix("").parts) or path.stem
    except ValueError:
        stem = path.stem
    return mod_data_dir(mod_root) / f"DISABLED_{stem}_原档{path.suffix}"


def backup_file(path: Path, mod_root: Optional[Path] = None) -> Optional[Path]:
    """首次写入前在模组的“快捷键管理”文件夹创建唯一原档；已存在则复用。"""
    if mod_root is None:
        return None
    name_lower = path.name.lower()
    if name_lower == "d3dx_user.ini" or name_lower.startswith("disabled"):
        return None
    dest = original_backup_path(path, mod_root)
    if dest.exists():
        return dest
    ensure_mod_data_dir(mod_root)
    legacy_candidates = [
        path.with_name(f"DISABLED_{path.stem}_原档{path.suffix}"),
        mod_root / f"DISABLED_{path.stem}_原档{path.suffix}",
    ]
    for old in legacy_candidates:
        if old.is_file() and old != dest:
            try:
                old.replace(dest)
                return dest
            except OSError:
                pass
    try:
        shutil.copy2(path, dest)
        return dest
    except OSError:
        return None


def line_ending(line: str) -> str:
    if line.endswith("\r\n"):
        return "\r\n"
    if line.endswith("\n"):
        return "\n"
    if line.endswith("\r"):
        return "\r"
    return ""


def atomic_write(path: Path, data: bytes) -> None:
    tmp = path.with_name(path.name + f".tmp_{os.getpid()}")
    with open(tmp, "wb") as fh:
        fh.write(data)
    os.replace(tmp, path)


def is_mod_ini(path: Path) -> bool:
    name = path.name
    if not name.lower().endswith(".ini"):
        return False
    if DISABLED_FILE_RE.match(name):
        return False
    if name.lower() in ("d3dx.ini", "d3dx_user.ini"):
        return False
    return True


def find_ini_files(root: Path) -> list[Path]:
    result: list[Path] = []
    if not root.is_dir():
        return result
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(
            d
            for d in dirnames
            if d != MOD_DATA_DIR_NAME
            and not d.startswith(".")
            and not DISABLED_DIR_RE.match(d)
        )
        for filename in sorted(filenames):
            p = Path(dirpath) / filename
            if is_mod_ini(p):
                result.append(p)
    return result


def has_mod_ini(path: Path) -> bool:
    try:
        return bool(find_ini_files(path))
    except OSError:
        return False


def find_game_root(start: Path) -> Optional[Path]:
    """从给定目录向上查找 ZZMI 根目录（含 d3dx_user.ini / d3dx.ini）。"""
    try:
        current = start.resolve()
    except OSError:
        return None
    for _ in range(12):
        if (current / "d3dx_user.ini").is_file() or (current / "d3dx.ini").is_file():
            return current
        if current.parent == current:
            break
        current = current.parent
    return None


class WindowsFileDrop:
    """Windows 原生文件拖放，不依赖第三方库。"""

    WM_DROPFILES = 0x0233
    GWLP_WNDPROC = -4

    def __init__(self, root: tk.Tk) -> None:
        import ctypes
        from ctypes import wintypes

        self.root = root
        self.pending: queue.Queue[list[str]] = queue.Queue()
        self.user32 = ctypes.windll.user32
        self.shell32 = ctypes.windll.shell32
        self._ctypes = ctypes
        self.user32.GetParent.argtypes = [wintypes.HWND]
        self.user32.GetParent.restype = wintypes.HWND

        client_hwnd = int(root.winfo_id())
        parent_hwnd = int(self.user32.GetParent(client_hwnd) or 0)
        self.hwnd = parent_hwnd or client_hwnd
        wndproc_type = ctypes.WINFUNCTYPE(
            ctypes.c_ssize_t,
            wintypes.HWND,
            wintypes.UINT,
            wintypes.WPARAM,
            wintypes.LPARAM,
        )
        self._proc = wndproc_type(self._wnd_proc)
        self._setter = getattr(
            self.user32, "SetWindowLongPtrW", self.user32.SetWindowLongW
        )
        self._setter.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_void_p]
        self._setter.restype = ctypes.c_void_p
        self._call = self.user32.CallWindowProcW
        self._call.argtypes = [
            ctypes.c_void_p,
            wintypes.HWND,
            wintypes.UINT,
            wintypes.WPARAM,
            wintypes.LPARAM,
        ]
        self._call.restype = ctypes.c_ssize_t
        self.shell32.DragAcceptFiles.argtypes = [wintypes.HWND, wintypes.BOOL]
        self.shell32.DragAcceptFiles.restype = None
        self.shell32.DragQueryFileW.argtypes = [
            wintypes.HANDLE,
            wintypes.UINT,
            wintypes.LPWSTR,
            wintypes.UINT,
        ]
        self.shell32.DragQueryFileW.restype = wintypes.UINT
        self.shell32.DragFinish.argtypes = [wintypes.HANDLE]
        self.shell32.DragFinish.restype = None

        self.old_proc = None
        self.installed = False
        targets = [self.hwnd]
        if client_hwnd and client_hwnd != self.hwnd:
            targets.append(client_hwnd)
        for hwnd in targets:
            old = self._setter(
                hwnd, self.GWLP_WNDPROC, ctypes.cast(self._proc, ctypes.c_void_p)
            )
            if old:
                self.hwnd = hwnd
                self.old_proc = old
                self.shell32.DragAcceptFiles(hwnd, True)
                self.installed = True
                break

    def _read_paths(self, drop_handle: int) -> list[str]:
        count = int(self.shell32.DragQueryFileW(drop_handle, 0xFFFFFFFF, None, 0))
        paths: list[str] = []
        for index in range(count):
            length = int(self.shell32.DragQueryFileW(drop_handle, index, None, 0))
            if length <= 0:
                continue
            buffer = self._ctypes.create_unicode_buffer(length + 1)
            self.shell32.DragQueryFileW(drop_handle, index, buffer, length + 1)
            if buffer.value:
                paths.append(buffer.value)
        return paths

    def _wnd_proc(self, hwnd: int, msg: int, wparam: int, lparam: int) -> int:
        if msg == self.WM_DROPFILES:
            paths: list[str] = []
            try:
                paths = self._read_paths(wparam)
            finally:
                try:
                    self.shell32.DragFinish(wparam)
                except Exception:  # noqa: BLE001 - 不让拖放异常打断 Tk
                    pass
            if paths:
                self.pending.put(paths)
            return 0
        if self.old_proc:
            return self._call(self.old_proc, hwnd, msg, wparam, lparam)
        return 0

    def take_paths(self) -> list[list[str]]:
        """由 Tk 主循环定时取走已拖入的路径，避免在窗口回调里调用 Tk。"""
        items: list[list[str]] = []
        while True:
            try:
                items.append(self.pending.get_nowait())
            except queue.Empty:
                break
        return items

    def close(self) -> None:
        if not self.installed:
            return
        self.installed = False
        try:
            self.shell32.DragAcceptFiles(self.hwnd, False)
        except Exception:  # noqa: BLE001
            pass
        if self.old_proc:
            try:
                self._setter(self.hwnd, self.GWLP_WNDPROC, self.old_proc)
            except Exception:  # noqa: BLE001
                pass
            self.old_proc = None


def strip_disabled_component(part: str) -> str:
    return DISABLED_DIR_RE.sub("", part, count=1)


def make_lookup_key(game_root: Optional[Path], ini_path: Path, var_name: str) -> Optional[str]:
    """生成 d3dx_user.ini 中使用的变量全名。

    例如：$\\mods\\叶瞬光\\叶瞬光-米克斯\\ye shunguang mix\\yeshunguangbh.ini\\hair
    """
    if game_root is None:
        return None
    try:
        rel = os.path.relpath(ini_path, game_root)
    except (OSError, ValueError):
        return None
    if rel.startswith(".."):
        return None
    parts = list(Path(rel).parts)
    if not parts:
        return None
    # 目录中的 DISABLED_ 前缀在启用后会被去掉，持久化键按启用时路径记录。
    parts = [strip_disabled_component(p) for p in parts[:-1]] + [parts[-1]]
    rel_norm = "\\".join(parts).lower()
    return "$\\" + rel_norm + "\\" + var_name.lower()


def normalized_mod_key(game_root: Optional[Path], mod_path: Path) -> str:
    if game_root is not None:
        try:
            rel = os.path.relpath(mod_path, game_root)
            if not rel.startswith(".."):
                parts = [strip_disabled_component(p) for p in Path(rel).parts]
                return "\\".join(parts).lower()
        except (OSError, ValueError):
            pass
    try:
        parts = [strip_disabled_component(p) for p in mod_path.resolve().parts]
        return "\\".join(parts).lower()
    except OSError:
        return str(mod_path).lower()


def validate_hotkey_name(name: str) -> Optional[str]:
    name = name.strip()
    if not name:
        return "名称不能为空。"
    if not name.startswith("Key"):
        return "名称必须以大写 Key 开头，否则 3DMigoto 不会把它识别为快捷键。"
    if any(ch in name for ch in "[]\r\n"):
        return "名称不能包含方括号或换行。"
    return None


# ---------------------------------------------------------------------------
# 快捷键中文说明
# ---------------------------------------------------------------------------

POSITIVE_MODIFIERS = {
    "ctrl": "Ctrl",
    "control": "Ctrl",
    "vk_control": "Ctrl",
    "shift": "Shift",
    "vk_shift": "Shift",
    "alt": "Alt",
    "menu": "Alt",
    "vk_menu": "Alt",
    "win": "Win",
    "windows": "Win",
    "vk_win": "Win",
    "vk_lwin": "Win",
    "vk_rwin": "Win",
}
NEGATIVE_MODIFIERS = {
    "no_ctrl": "Ctrl",
    "no_control": "Ctrl",
    "no_shift": "Shift",
    "no_alt": "Alt",
    "no_menu": "Alt",
    "no_win": "Win",
}
NO_MODIFIER_TOKENS = {"no_modifiers", "no_modifier", "nomodifiers"}

FRIENDLY_KEYS = {
    "up": "上方向键",
    "down": "下方向键",
    "left": "左方向键",
    "right": "右方向键",
    "space": "空格键",
    "spacebar": "空格键",
    "return": "回车键",
    "enter": "回车键",
    "escape": "Esc 键",
    "esc": "Esc 键",
    "tab": "Tab 键",
    "back": "退格键",
    "backspace": "退格键",
    "delete": "Delete 键",
    "del": "Delete 键",
    "insert": "Insert 键",
    "home": "Home 键",
    "end": "End 键",
    "prior": "Page Up 键",
    "pageup": "Page Up 键",
    "next": "Page Down 键",
    "pagedown": "Page Down 键",
    "capital": "大写锁定键",
    "capslock": "大写锁定键",
    "numlock": "数字锁定键",
    "scroll": "滚动锁定键",
    "scrolllock": "滚动锁定键",
    "snapshot": "Print Screen 键",
    "printscreen": "Print Screen 键",
    "pause": "Pause 键",
    "apps": "菜单键",
    "sleep": "睡眠键",
    "lbutton": "鼠标左键",
    "rbutton": "鼠标右键",
    "mbutton": "鼠标中键",
    "xbutton1": "鼠标侧键 1",
    "xbutton2": "鼠标侧键 2",
    "add": "小键盘加号 +",
    "subtract": "小键盘减号 -",
    "multiply": "小键盘乘号 *",
    "divide": "小键盘除号 /",
    "decimal": "小键盘小数点 .",
    "lshift": "左 Shift 键",
    "rshift": "右 Shift 键",
    "lcontrol": "左 Ctrl 键",
    "rcontrol": "右 Ctrl 键",
    "lmenu": "左 Alt 键",
    "rmenu": "右 Alt 键",
}
FRIENDLY_KEYS.update({
    "oem_1": "分号键 ;",
    "oem_plus": "等号键 =",
    "oem_comma": "逗号键 ,",
    "oem_minus": "减号键 -",
    "oem_period": "句号键 .",
    "oem_2": "斜杠键 /",
    "oem_3": "反引号键 `",
    "oem_4": "左方括号 [",
    "oem_5": "反斜杠键 \\",
    "oem_6": "右方括号 ]",
    "oem_7": "单引号键 '",
    "oem_8": "OEM 键",
    "oem_102": "反斜杠键 \\",
})

PUNCTUATION_KEYS = {
    ".": "句号键 .",
    ",": "逗号键 ,",
    "/": "斜杠键 /",
    ";": "分号键 ;",
    "'": "单引号键 '",
    "[": "左方括号 [",
    "]": "右方括号 ]",
    "-": "减号键 -",
    "=": "等号键 =",
    "\\": "反斜杠键 \\",
    "`": "反引号键 `",
    "+": "加号键 +",
    "_": "下划线键 _",
    "*": "星号键 *",
}


GAMEPAD_KEYS = {
    "a": "A 键",
    "b": "B 键",
    "x": "X 键",
    "y": "Y 键",
    "start": "开始键",
    "back": "返回键",
    "guide": "Guide 键",
    "left_trigger": "左扳机",
    "right_trigger": "右扳机",
    "left_shoulder": "左肩键",
    "right_shoulder": "右肩键",
    "left_thumb": "左摇杆按下",
    "right_thumb": "右摇杆按下",
    "dpad_up": "十字键上",
    "dpad_down": "十字键下",
    "dpad_left": "十字键左",
    "dpad_right": "十字键右",
}


def gamepad_label(prefix: str, body: str) -> Optional[str]:
    label = GAMEPAD_KEYS.get(body.replace("gamepad_", "", 1))
    if label is None:
        return None
    return f"手柄{prefix} {label}" if prefix else f"手柄 {label}"


GAMEPAD_BUTTON_TOKENS = {
    0x0001: "XB_DPAD_UP",
    0x0002: "XB_DPAD_DOWN",
    0x0004: "XB_DPAD_LEFT",
    0x0008: "XB_DPAD_RIGHT",
    0x0010: "XB_START",
    0x0020: "XB_BACK",
    0x0040: "XB_LEFT_THUMB",
    0x0080: "XB_RIGHT_THUMB",
    0x0100: "XB_LEFT_SHOULDER",
    0x0200: "XB_RIGHT_SHOULDER",
    0x1000: "XB_A",
    0x2000: "XB_B",
    0x4000: "XB_X",
    0x8000: "XB_Y",
}


class XINPUT_GAMEPAD(ctypes.Structure):
    _fields_ = [
        ("wButtons", ctypes.c_ushort),
        ("bLeftTrigger", ctypes.c_ubyte),
        ("bRightTrigger", ctypes.c_ubyte),
        ("sThumbLX", ctypes.c_short),
        ("sThumbLY", ctypes.c_short),
        ("sThumbRX", ctypes.c_short),
        ("sThumbRY", ctypes.c_short),
    ]


class XINPUT_STATE(ctypes.Structure):
    _fields_ = [
        ("dwPacketNumber", ctypes.c_ulong),
        ("Gamepad", XINPUT_GAMEPAD),
    ]


_XINPUT_LOADED = False
_XINPUT_DLL = None


def load_xinput():
    """加载 XInput；没有手柄或非 Windows 时返回 None。"""
    global _XINPUT_LOADED, _XINPUT_DLL
    if _XINPUT_LOADED:
        return _XINPUT_DLL
    _XINPUT_LOADED = True
    if os.name != "nt":
        return None
    for name in ("XInput1_4", "XInput1_3", "XInput9_1_0"):
        try:
            dll = getattr(ctypes.windll, name)
            dll.XInputGetState.argtypes = [
                ctypes.c_ulong,
                ctypes.POINTER(XINPUT_STATE),
            ]
            dll.XInputGetState.restype = ctypes.c_ulong
        except (AttributeError, OSError):
            continue
        _XINPUT_DLL = dll
        return dll
    return None


def describe_key_token(token: str) -> str:
    low = token.lower()
    gamepad = re.match(r"^xb([1-4])?_(.+)$", low)
    if gamepad:
        label = gamepad_label(gamepad.group(1) or "", gamepad.group(2))
        if label is not None:
            return label
    if low in FRIENDLY_KEYS:
        return FRIENDLY_KEYS[low]
    if low in PUNCTUATION_KEYS:
        return PUNCTUATION_KEYS[low]
    m = re.match(r"^(?:numpad|num)(\d)$", low)
    if m:
        return f"小键盘 {m.group(1)}"
    m = re.match(r"^f([1-9]|1\d|2[0-4])$", low)
    if m:
        return f"F{int(m.group(1))} 键"
    if low.startswith("vk_"):
        body = low[3:]
        if body in FRIENDLY_KEYS:
            return FRIENDLY_KEYS[body]
        if body in PUNCTUATION_KEYS:
            return PUNCTUATION_KEYS[body]
        if body.startswith("numpad") and body[6:].isdigit():
            return f"小键盘 {body[6:]}"
        if len(body) >= 2 and body[0] == "f" and body[1:].isdigit():
            number = int(body[1:])
            if 1 <= number <= 24:
                return f"F{number} 键"
        if body.isdigit():
            return f"数字 {body}"
        if len(body) == 1 and body.isalpha():
            return f"{body.upper()} 键"
        if body.startswith("gamepad_"):
            label = gamepad_label("", body)
            if label is not None:
                return label
            return "手柄 " + body[len("gamepad_"):].replace("_", " ")
        return token
    if low.isdigit():
        return f"数字 {low}"
    if len(token) == 1 and token.isalpha():
        return f"{token.upper()} 键"
    return token


def describe_key_line(text: str) -> str:
    raw_tokens = text.split()
    tokens: list[str] = []
    index = 0
    while index < len(raw_tokens):
        token = raw_tokens[index]
        low = token.lower()
        if low in ("num", "numpad") and index + 1 < len(raw_tokens):
            next_token = raw_tokens[index + 1]
            if next_token.isdigit():
                tokens.append(f"VK_NUMPAD{next_token}")
                index += 2
                continue
            numpad_symbols = {
                "+": "VK_ADD",
                "-": "VK_SUBTRACT",
                "*": "VK_MULTIPLY",
                "/": "VK_DIVIDE",
                ".": "VK_DECIMAL",
            }
            if next_token in numpad_symbols:
                tokens.append(numpad_symbols[next_token])
                index += 2
                continue
        tokens.append(token)
        index += 1

    positive: list[str] = []
    negative: list[str] = []
    keys: list[str] = []
    no_modifiers = False
    for token in tokens:
        low = token.lower()
        if low in NO_MODIFIER_TOKENS:
            no_modifiers = True
        elif low in POSITIVE_MODIFIERS:
            name = POSITIVE_MODIFIERS[low]
            if name not in positive:
                positive.append(name)
        elif low in NEGATIVE_MODIFIERS:
            name = NEGATIVE_MODIFIERS[low]
            if name not in negative:
                negative.append(name)
        else:
            keys.append(token)

    if not keys:
        if not positive:
            return text
        # 整行只有修饰键（例如 key = ctrl），把它当作按键本身说明。
        keys = positive
        positive = []

    key_text = " + ".join(describe_key_token(key) for key in keys)
    parts = positive + [key_text]
    result = " + ".join(part for part in parts if part)
    notes: list[str] = []
    if len(keys) > 1:
        notes.append("同时按住")
    if no_modifiers:
        notes.append("不按任何修饰键")
    elif negative:
        notes.append("不按 " + "/".join(negative))
    if notes:
        result += "（" + "；".join(notes) + "）"
    return result


def describe_key_lines(keys: list[str]) -> str:
    descriptions = [describe_key_line(key) for key in keys if key.strip()]
    return " 或 ".join(descriptions) if descriptions else "—"


def display_width(text: str) -> int:
    """按等宽字体估算显示宽度；中文和全角字符按 2 格。"""
    width = 0
    for ch in text:
        if unicodedata.combining(ch):
            continue
        width += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
    return width


def pad_display(text: str, width: int) -> str:
    return text + " " * max(0, width - display_width(text))


def wrap_display(text: str, width: int) -> list[str]:
    """按显示宽度折行，尽量在空格处断开。"""
    text = text.strip()
    if not text:
        return [""]
    lines: list[str] = []
    remaining = text
    while display_width(remaining) > width:
        used = 0
        cut = 0
        for index, ch in enumerate(remaining):
            char_width = 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
            if used + char_width > width:
                break
            used += char_width
            cut = index + 1
        if cut <= 0:
            cut = 1
        split = remaining[:cut]
        space = split.rfind(" ")
        if space > 0 and display_width(split[:space]) >= width // 3:
            cut = space + 1
        lines.append(remaining[:cut].rstrip())
        remaining = remaining[cut:].lstrip()
    if remaining:
        lines.append(remaining)
    return lines or [""]


def render_text_table(headers: list[str], rows: list[list[str]], max_widths: list[int]) -> str:
    """用 ASCII 黑框线条画表格，中文按双宽对齐。"""
    widths: list[int] = []
    for index, header in enumerate(headers):
        natural = display_width(header)
        for row in rows:
            natural = max(natural, display_width(row[index]))
        widths.append(min(natural, max_widths[index]))

    def border(char: str) -> str:
        return "+" + "+".join(char * (width + 2) for width in widths) + "+"

    def row_lines(cells: list[str]) -> list[str]:
        wrapped = [wrap_display(cell, widths[i]) for i, cell in enumerate(cells)]
        height = max(len(lines) for lines in wrapped)
        result: list[str] = []
        for line_index in range(height):
            parts = []
            for column, lines in enumerate(wrapped):
                text = lines[line_index] if line_index < len(lines) else ""
                parts.append(" " + pad_display(text, widths[column]) + " ")
            result.append("|" + "|".join(parts) + "|")
        return result

    output = [border("-"), row_lines(headers)[0], border("=")]
    for index, row in enumerate(rows):
        output.extend(row_lines(row))
        output.append(border("-"))
    return "\r\n".join(output) + "\r\n"

PANEL_SHADER_SOURCE = """\
Texture1D<float4> IniParams : register(t120);

#define SIZE IniParams[87].xy
#define OFFSET IniParams[87].zw

struct vs2ps {
    float4 pos : SV_Position0;
    float2 uv : TEXCOORD1;
};

#ifdef VERTEX_SHADER
void main(out vs2ps output, uint vertex : SV_VertexID)
{
    float2 base, off;
    off.x = OFFSET.x * 2 - 1;
    off.y = (1 - OFFSET.y) * 2 - 1;
    base.xy = float2(2 * SIZE.x, -2 * SIZE.y);
    switch (vertex) {
        case 0:
            output.pos.xy = float2(base.x + off.x, base.y + off.y);
            output.uv = float2(1, 0);
            break;
        case 1:
            output.pos.xy = float2(base.x + off.x, off.y);
            output.uv = float2(1, 1);
            break;
        case 2:
            output.pos.xy = float2(off.x, base.y + off.y);
            output.uv = float2(0, 0);
            break;
        default:
            output.pos.xy = float2(off.x, off.y);
            output.uv = float2(0, 1);
            break;
    }
    output.pos.zw = float2(0, 1);
}
#endif

#ifdef PIXEL_SHADER
Texture2D<float4> tex : register(t100);

void main(vs2ps input, out float4 result : SV_Target0)
{
    uint width, height;
    tex.GetDimensions(width, height);
    if (!width || !height)
        discard;
    input.uv.y = 1 - input.uv.y;
    result = tex.Load(int3(input.uv.xy * float2(width, height), 0));
}
#endif
"""


def collect_panel_conditions(hotkeys: list["Hotkey"]) -> list[str]:
    """收集 mod 现有快捷键的生效条件，按首次出现顺序去重。"""
    conditions: list[str] = []
    for hk in hotkeys:
        if hk.section.name == PANEL_KEY_SECTION:
            continue
        condition = hk.condition.strip()
        if condition and condition not in conditions:
            conditions.append(condition)
    return conditions


ACTIVE_CONDITION_RE = re.compile(
    r"(?i)\$\s*(?:active\d*|activecharacter)\b"
)


def recommend_panel_condition(
    hotkeys: list["Hotkey"], conditions: list[str]
) -> str:
    """多个条件时推荐占比最多的；优先角色在场类条件，同票取先出现的。"""
    counts: dict[str, int] = {}
    for hk in hotkeys:
        if hk.section.name == PANEL_KEY_SECTION:
            continue
        condition = hk.condition.strip()
        if condition:
            counts[condition] = counts.get(condition, 0) + 1
    order = {condition: index for index, condition in enumerate(conditions)}
    preferred = [
        condition for condition in conditions if ACTIVE_CONDITION_RE.search(condition)
    ]
    pool = preferred or conditions
    return max(pool, key=lambda cond: (counts.get(cond, 0), -order.get(cond, 0)))


def panel_mod_path(mod: "ModInfo") -> str:
    """面板显示的 mod 路径：从 Mods 这一层开始，不写 Mods 之前的目录。"""
    parts = mod.path.parts
    for index, part in enumerate(parts):
        if part.lower() == "mods":
            return "\\".join(parts[index:])
    return str(mod.path)


def build_panel_lines(mod: "ModInfo") -> list[str]:
    """生成图片菜单面板的文字行（支持中文，不截断）。"""
    lines = [panel_mod_path(mod), "快捷键列表"]
    for hk in mod.hotkeys:
        name = hk.section.comment.strip() or hk.section.name
        desc = describe_key_lines(hk.keys)
        lines.append(f"{name}：{desc}" if desc else name)
    return lines


def _wrap_panel_lines(lines: list[str], units: int) -> list[str]:
    wrapped: list[str] = []
    for line in lines:
        wrapped.extend(wrap_display(line, max(8, units)))
    return wrapped


def render_panel_png(
    lines: list[str],
    width: int = PANEL_IMAGE_WIDTH,
    height: int = PANEL_IMAGE_HEIGHT,
    padding: int = 14,
    bg_alpha: int = 85,
) -> tuple[bytes, int, int]:
    """用 Windows GDI 把文字画成固定画布 PNG（右下角），返回 (png, w, h)。

    内容多时自动缩小字号，必要时分两列，保证所有快捷键都显示。
    """
    if os.name != "nt":
        raise RuntimeError("图片菜单面板仅支持 Windows。")
    if not lines:
        lines = [""]
    import ctypes
    import struct
    import zlib
    from ctypes import wintypes

    gdi32 = ctypes.windll.gdi32
    gap = 18
    layout: Optional[tuple[int, int, int, int, list[str], int]] = None
    for font_size in (20, 18, 16, 14, 13, 12, 11, 10, 9):
        line_height = int(font_size * 1.4)
        capacity = (height - padding * 2) // line_height
        if capacity <= 0:
            continue
        for cols in (1, 2):
            col_width = (width - padding * 2 - gap * (cols - 1)) // cols
            units = max(8, int((col_width - 4) / font_size * 2))
            wrapped = _wrap_panel_lines(lines, units)
            need = (len(wrapped) + cols - 1) // cols
            if need <= capacity:
                layout = (font_size, line_height, cols, col_width, wrapped, need)
                break
        if layout is not None:
            break
    if layout is None:
        font_size = 9
        line_height = int(font_size * 1.4)
        cols = 2
        col_width = (width - padding * 2 - gap) // 2
        units = max(8, int((col_width - 4) / font_size * 2))
        wrapped = _wrap_panel_lines(lines, units)
        capacity = (height - padding * 2) // line_height
        wrapped = wrapped[: capacity * cols]
        need = (len(wrapped) + cols - 1) // cols
        layout = (font_size, line_height, cols, col_width, wrapped, need)
    font_size, line_height, cols, col_width, wrapped, per_col = layout

    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [
            ("biSize", wintypes.DWORD),
            ("biWidth", wintypes.LONG),
            ("biHeight", wintypes.LONG),
            ("biPlanes", wintypes.WORD),
            ("biBitCount", wintypes.WORD),
            ("biCompression", wintypes.DWORD),
            ("biSizeImage", wintypes.DWORD),
            ("biXPelsPerMeter", wintypes.LONG),
            ("biYPelsPerMeter", wintypes.LONG),
            ("biClrUsed", wintypes.DWORD),
            ("biClrImportant", wintypes.DWORD),
        ]

    class BITMAPINFO(ctypes.Structure):
        _fields_ = [
            ("bmiHeader", BITMAPINFOHEADER),
            ("bmiColors", wintypes.DWORD * 3),
        ]

    class SIZE(ctypes.Structure):
        _fields_ = [("cx", wintypes.LONG), ("cy", wintypes.LONG)]

    dc = gdi32.CreateCompatibleDC(0)
    if not dc:
        raise RuntimeError("无法创建绘图设备。")
    font = gdi32.CreateFontW(
        -font_size, 0, 0, 0, 400, 0, 0, 0,
        1, 4, 0, 4, 0, "Microsoft YaHei UI",
    )
    old_font = gdi32.SelectObject(dc, font)
    text_width = 0
    for line in wrapped:
        size = SIZE()
        gdi32.GetTextExtentPoint32W(dc, line, len(line), ctypes.byref(size))
        text_width = max(text_width, size.cx)
    text_width = min(text_width, max(1, col_width))

    block_width = (cols - 1) * (col_width + gap) + text_width
    block_height = per_col * line_height + padding * 2
    top = max(0, height - block_height)
    bg_width = min(width, block_width + padding * 2)
    bg_left = max(0, width - bg_width)
    text_left = bg_left + padding

    columns = [
        wrapped[index * per_col : (index + 1) * per_col] for index in range(cols)
    ]

    bmi = BITMAPINFO()
    bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.bmiHeader.biWidth = width
    bmi.bmiHeader.biHeight = -height
    bmi.bmiHeader.biPlanes = 1
    bmi.bmiHeader.biBitCount = 32
    bmi.bmiHeader.biCompression = 0
    bits = ctypes.c_void_p()
    hbmp = gdi32.CreateDIBSection(
        dc, ctypes.byref(bmi), 0, ctypes.byref(bits), None, 0
    )
    old_bmp = gdi32.SelectObject(dc, hbmp)
    gdi32.SetBkMode(dc, 1)
    gdi32.SetTextColor(dc, 0x00FFFFFF)
    gdi32.SelectObject(dc, font)
    for col_index, column in enumerate(columns):
        x = text_left + col_index * (col_width + gap)
        for line_index, line in enumerate(column):
            gdi32.TextOutW(
                dc,
                x,
                top + padding + line_index * line_height,
                line,
                len(line),
            )
    gdi32.GdiFlush()
    raw = ctypes.string_at(bits, width * height * 4)
    gdi32.SelectObject(dc, old_font)
    gdi32.SelectObject(dc, old_bmp)
    gdi32.DeleteObject(font)
    gdi32.DeleteObject(hbmp)
    gdi32.DeleteDC(dc)

    rgba = bytearray(width * height * 4)
    # 文字和背景只在右下角矩形内，其余像素保持全透明。
    lut = []
    for coverage in range(256):
        alpha = coverage + bg_alpha * (255 - coverage) // 255
        value = 255 * coverage // alpha if alpha else 0
        lut.append(bytes((value, value, value, alpha)))
    bg_right = min(width, bg_left + bg_width)
    for y in range(top, height):
        row = y * width * 4
        for x in range(bg_left, bg_right):
            index = row + x * 4
            coverage = max(raw[index], raw[index + 1], raw[index + 2])
            rgba[index : index + 4] = lut[coverage]

    scanlines = b"".join(
        b"\x00" + bytes(rgba[y * width * 4 : (y + 1) * width * 4])
        for y in range(height)
    )

    def chunk(kind: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(scanlines, 6))
        + chunk(b"IEND", b"")
    )
    return png, width, height


def _ini_section_ranges(lines: list[str]) -> list[tuple[str, int, int]]:
    ranges: list[tuple[str, int, int]] = []
    current_name: Optional[str] = None
    start = 0
    for idx, line in enumerate(lines):
        match = SECTION_RE.match(line.rstrip("\r\n"))
        if not match:
            continue
        if current_name is not None:
            ranges.append((current_name, start, idx))
        current_name = match.group("name").strip()
        start = idx
    if current_name is not None:
        ranges.append((current_name, start, len(lines)))
    return ranges


def strip_panel_lines(lines: list[str]) -> list[str]:
    """移除本工具注入的图片菜单面板配置，保留用户原有内容。"""
    result: list[str] = []
    skipping = False
    had_marker = False
    for line in lines:
        marker = line.strip()
        if marker == PANEL_BEGIN:
            skipping = True
            had_marker = True
            continue
        if marker == PANEL_END:
            skipping = False
            continue
        if not skipping:
            result.append(line)

    drop: set[int] = set()
    for name, start, end in _ini_section_ranges(result):
        if name in PANEL_SECTION_NAMES:
            drop.update(range(start, end))
    result = [line for idx, line in enumerate(result) if idx not in drop]

    if had_marker:
        # 删除本工具为面板新建、移除后已变空的 [Constants] / [Present]。
        empty_sections: set[int] = set()
        for name, start, end in _ini_section_ranges(result):
            if name.lower() not in ("constants", "present"):
                continue
            if all(not line.strip() for line in result[start + 1 : end]):
                empty_sections.update(range(start, end))
        result = [
            line for idx, line in enumerate(result) if idx not in empty_sections
        ]

    const_re = re.compile(
        r"(?i)^\s*global\s+\$" + re.escape(PANEL_SHOW_VAR) + r"\b"
    )
    return [
        line
        for line in result
        if not const_re.match(line.rstrip("\r\n"))
    ]


def ensure_image_panel_lines(
    lines: list[str],
    key_line: str,
    image_rel: str,
    shader_rel: str,
    active_condition: str = "",
) -> list[str]:
    """把图片菜单面板所需的常量、Present 绘制和资源段写入 ini 行列表。"""
    lines = strip_panel_lines(lines)
    eol = "\r\n" if any(line.endswith("\r\n") for line in lines) else "\n"

    def rows(*items: str) -> list[str]:
        return [item + eol for item in items]

    def append_block(block: list[str]) -> None:
        if lines and not lines[-1].endswith(("\n", "\r")):
            lines[-1] += eol
        lines.extend(block)

    def find(name: str) -> Optional[tuple[int, int]]:
        for sec_name, start, end in _ini_section_ranges(lines):
            if sec_name.lower() == name.lower():
                return start, end
        return None

    const_block = rows(PANEL_BEGIN, f"global ${PANEL_SHOW_VAR} = 0", PANEL_END)
    constants = find("Constants")
    if constants is not None:
        lines[constants[1]:constants[1]] = const_block
    else:
        append_block(rows("[Constants]") + const_block)

    if active_condition:
        show_cond = f"if ${PANEL_SHOW_VAR} && ({active_condition})"
    else:
        show_cond = f"if ${PANEL_SHOW_VAR}"
    present_block = rows(
        PANEL_BEGIN,
        show_cond,
        f"\trun = {PANEL_DRAW_LIST}",
        "endif",
        PANEL_END,
    )
    present = find("Present")
    if present is not None:
        lines[present[1]:present[1]] = present_block
    else:
        append_block(rows("[Present]") + present_block)

    append_block(
        rows(
            f"[{PANEL_KEY_SECTION}] ; {PANEL_SECTION_COMMENT}",
            f"key = {key_line}",
            *([f"condition = {active_condition}"] if active_condition else []),
            "type = cycle",
            f"${PANEL_SHOW_VAR} = 0, 1",
            "",
            f"[{PANEL_IMAGE_RESOURCE}]",
            f"filename = {image_rel}",
            "",
            f"[{PANEL_DRAW_LIST}]",
            f"x87 = ({PANEL_IMAGE_WIDTH} * res_height / 1080) / res_width",
            f"y87 = {PANEL_IMAGE_HEIGHT} / 1080",
            f"z87 = 1 - (({PANEL_IMAGE_WIDTH} + 24) * res_height / 1080) / res_width",
            f"w87 = 1 - ({PANEL_IMAGE_HEIGHT} + 24) / 1080",
            f"ps-t100 = {PANEL_IMAGE_RESOURCE}",
            f"run = {PANEL_SHADER_SECTION}",
            "post ps-t100 = null",
            "",
            f"[{PANEL_SHADER_SECTION}]",
            f"vs = {shader_rel}",
            f"ps = {shader_rel}",
            "run = BuiltInCommandListUnbindAllRenderTargets",
            "blend = ADD SRC_ALPHA INV_SRC_ALPHA",
            "cull = none",
            "topology = triangle_strip",
            "o0 = set_viewport bb",
            "Draw = 4,0",
        )
    )
    return lines


@dataclass(frozen=True)
class KeySignature:
    """一行 key 的规范化结果，用于判断两行是否会同时触发。"""

    keys: tuple[str, ...]
    required: frozenset[str]
    forbidden: frozenset[str]


def expand_key_tokens(text: str) -> list[str]:
    raw_tokens = text.split()
    tokens: list[str] = []
    index = 0
    while index < len(raw_tokens):
        token = raw_tokens[index]
        low = token.lower()
        if low in ("num", "numpad") and index + 1 < len(raw_tokens):
            next_token = raw_tokens[index + 1]
            if next_token.isdigit():
                tokens.append(f"VK_NUMPAD{next_token}")
                index += 2
                continue
            numpad_symbols = {
                "+": "VK_ADD",
                "-": "VK_SUBTRACT",
                "*": "VK_MULTIPLY",
                "/": "VK_DIVIDE",
                ".": "VK_DECIMAL",
            }
            if next_token in numpad_symbols:
                tokens.append(numpad_symbols[next_token])
                index += 2
                continue
        tokens.append(token)
        index += 1
    return tokens


def key_signature(text: str) -> Optional[KeySignature]:
    positive: set[str] = set()
    negative: set[str] = set()
    keys: list[str] = []
    no_modifiers = False
    for token in expand_key_tokens(text):
        low = token.lower()
        if low in NO_MODIFIER_TOKENS:
            no_modifiers = True
        elif low in POSITIVE_MODIFIERS:
            positive.add(POSITIVE_MODIFIERS[low])
        elif low in NEGATIVE_MODIFIERS:
            negative.add(NEGATIVE_MODIFIERS[low])
        else:
            keys.append(token)
    if not keys:
        if not positive:
            return None
        # 整行只有修饰键时，按“修饰键本身作为按键”处理。
        keys = sorted(positive)
        positive = set()
    canonical = tuple(sorted({describe_key_token(token).casefold() for token in keys}))
    if not canonical:
        return None
    if no_modifiers:
        negative.update({"Ctrl", "Shift", "Alt", "Win"})
    return KeySignature(canonical, frozenset(positive), frozenset(negative))


def key_lines_conflict(first: str, second: str) -> bool:
    a = key_signature(first)
    b = key_signature(second)
    if a is None or b is None or a.keys != b.keys:
        return False
    if a.required != b.required:
        # 必须按下的 Ctrl/Shift/Alt/Win 不同，视为不同组合。
        # 例如 ctrl + up 与 alt + up 不算冲突；只有按住两组修饰键才会同时触发。
        return False
    # 修饰键要求相同后，若没有互相禁止，则存在共同的按键状态。
    return not bool(a.required & (a.forbidden | b.forbidden))


def hotkey_label(hk: "Hotkey") -> str:
    comment = hk.section.comment.strip()
    return f"[{hk.section.name}]" + (f"（{comment}）" if comment else "")


def normalized_condition(hk: "Hotkey") -> str:
    return " ".join(hk.condition.split()).casefold()


def find_key_conflict(
    hotkeys: list["Hotkey"], target: "Hotkey", key_text: str
) -> Optional[tuple["Hotkey", str]]:
    target_condition = normalized_condition(target)
    for hk in hotkeys:
        if hk is target:
            continue
        # 同一生效条件下的同键属于“一键多开”，是正常设计，不算冲突。
        if normalized_condition(hk) == target_condition:
            continue
        for existing in hk.keys:
            if key_lines_conflict(key_text, existing):
                return hk, existing
    return None


def count_key_shares(
    hotkeys: list["Hotkey"], target: "Hotkey", key_text: str
) -> int:
    target_condition = normalized_condition(target)
    count = 0
    for hk in hotkeys:
        if hk is target or normalized_condition(hk) != target_condition:
            continue
        if any(key_lines_conflict(key_text, existing) for existing in hk.keys):
            count += 1
    return count


def find_shared_key_groups(
    hotkeys: list["Hotkey"],
) -> list[tuple[str, list["Hotkey"]]]:
    """同条件、同按键的快捷键组：一键同时切换多个功能，属正常设计。"""
    buckets: dict[tuple, tuple[str, list[Hotkey]]] = {}
    for hk in hotkeys:
        condition = normalized_condition(hk)
        for key in hk.keys:
            signature = key_signature(key)
            token = ("sig", signature) if signature is not None else ("raw", key.casefold())
            bucket_key = (token, condition)
            entry = buckets.get(bucket_key)
            if entry is None:
                buckets[bucket_key] = (key, [hk])
            elif all(hk is not other for other in entry[1]):
                entry[1].append(hk)
    return [(key, group) for key, group in buckets.values() if len(group) > 1]


def find_hotkey_conflicts(
    hotkeys: list["Hotkey"],
) -> list[tuple["Hotkey", str, "Hotkey", str]]:
    conflicts: list[tuple[Hotkey, str, Hotkey, str]] = []
    seen: set[tuple[tuple[str, int], tuple[str, int]]] = set()
    for index, first in enumerate(hotkeys):
        for second in hotkeys[index + 1 :]:
            # 同条件同键是“一键多开”，正常设计，不按冲突处理。
            if normalized_condition(first) == normalized_condition(second):
                continue
            pair = (
                (str(first.doc.path), first.section.start),
                (str(second.doc.path), second.section.start),
            )
            paired = set()
            for first_key in first.keys:
                for second_key in second.keys:
                    if (first_key, second_key) in paired:
                        continue
                    paired.add((first_key, second_key))
                    if pair in seen:
                        continue
                    if key_lines_conflict(first_key, second_key):
                        seen.add(pair)
                        conflicts.append((first, first_key, second, second_key))
                        break
                if pair in seen:
                    break
    return conflicts


def count_conflict_groups(
    conflicts: list[tuple["Hotkey", str, "Hotkey", str]]
) -> int:
    """按按键组合去重统计冲突组数，而不是按两两配对数。"""
    groups: set[frozenset] = set()
    for _first, first_key, _second, second_key in conflicts:
        first_sig = key_signature(first_key)
        second_sig = key_signature(second_key)
        if first_sig is not None and second_sig is not None:
            groups.add(frozenset((first_sig, second_sig)))
        else:
            groups.add(frozenset((first_key.casefold(), second_key.casefold())))
    return len(groups)


# Windows virtual-key codes (Tk event.keycode) to 3DMigoto key tokens.
VK_KEYCODE_SPECIAL = {
    0x08: "VK_BACK",
    0x09: "VK_TAB",
    0x0D: "VK_RETURN",
    0x13: "VK_PAUSE",
    0x14: "VK_CAPITAL",
    0x1B: "VK_ESCAPE",
    0x20: "VK_SPACE",
    0x21: "VK_PRIOR",
    0x22: "VK_NEXT",
    0x23: "VK_END",
    0x24: "VK_HOME",
    0x25: "VK_LEFT",
    0x26: "VK_UP",
    0x27: "VK_RIGHT",
    0x28: "VK_DOWN",
    0x2C: "VK_SNAPSHOT",
    0x2D: "VK_INSERT",
    0x2E: "VK_DELETE",
    0x5B: "VK_LWIN",
    0x5C: "VK_RWIN",
    0x5D: "VK_APPS",
    0x6A: "VK_MULTIPLY",
    0x6B: "VK_ADD",
    0x6D: "VK_SUBTRACT",
    0x6E: "VK_DECIMAL",
    0x6F: "VK_DIVIDE",
    0x90: "VK_NUMLOCK",
    0x91: "VK_SCROLL",
    0xBA: ";",
    0xBB: "=",
    0xBC: ",",
    0xBD: "-",
    0xBE: ".",
    0xBF: "/",
    0xC0: "`",
    0xDB: "[",
    0xDC: "\\",
    0xDD: "]",
    0xDE: "'",
    0xE2: "\\",
}

KEYSYM_FALLBACK = {
    "Up": "VK_UP",
    "Down": "VK_DOWN",
    "Left": "VK_LEFT",
    "Right": "VK_RIGHT",
    "Return": "VK_RETURN",
    "Escape": "VK_ESCAPE",
    "Tab": "VK_TAB",
    "BackSpace": "VK_BACK",
    "Delete": "VK_DELETE",
    "Insert": "VK_INSERT",
    "Home": "VK_HOME",
    "End": "VK_END",
    "Prior": "VK_PRIOR",
    "Next": "VK_NEXT",
    "space": "VK_SPACE",
    "Pause": "VK_PAUSE",
    "Print": "VK_SNAPSHOT",
    "Menu": "VK_APPS",
    "period": ".",
    "comma": ",",
    "slash": "/",
    "semicolon": ";",
    "apostrophe": "'",
    "quotedbl": "'",
    "bracketleft": "[",
    "bracketright": "]",
    "minus": "-",
    "underscore": "-",
    "equal": "=",
    "plus": "=",
    "backslash": "\\",
    "bar": "\\",
    "grave": "`",
    "asciitilde": "`",
    "exclam": "1",
    "at": "2",
    "numbersign": "3",
    "dollar": "4",
    "percent": "5",
    "asciicircum": "6",
    "ampersand": "7",
    "asterisk": "8",
    "parenleft": "9",
    "parenright": "0",
    "colon": ";",
    "less": ",",
    "greater": ".",
    "question": "/",
    "braceleft": "[",
    "braceright": "]",
    "KP_Add": "VK_ADD",
    "KP_Subtract": "VK_SUBTRACT",
    "KP_Multiply": "VK_MULTIPLY",
    "KP_Divide": "VK_DIVIDE",
    "KP_Decimal": "VK_DECIMAL",
}


def keycode_to_3dmigoto(keycode: int, keysym: str = "", char: str = "") -> Optional[str]:
    if 0x41 <= keycode <= 0x5A:
        return chr(keycode).lower()
    if 0x30 <= keycode <= 0x39:
        return chr(keycode)
    if 0x60 <= keycode <= 0x69:
        return f"VK_NUMPAD{keycode - 0x60}"
    if 0x70 <= keycode <= 0x87:
        return f"VK_F{keycode - 0x6F}"
    token = VK_KEYCODE_SPECIAL.get(keycode)
    if token:
        return token
    if keysym in KEYSYM_FALLBACK:
        return KEYSYM_FALLBACK[keysym]
    if keysym.startswith("KP_") and keysym[3:].isdigit():
        return f"VK_NUMPAD{keysym[3:]}"
    if keysym.startswith("F") and keysym[1:].isdigit():
        return f"VK_F{keysym[1:]}"
    if len(keysym) == 1:
        if keysym.isalpha():
            return keysym.lower()
        if keysym.isdigit():
            return keysym
        if keysym in PUNCTUATION_KEYS:
            return keysym
    if len(char) == 1 and char.isprintable() and char != " ":
        if char.isalpha():
            return char.lower()
        return char
    return None


# ---------------------------------------------------------------------------
# ini 文件解析
# ---------------------------------------------------------------------------


@dataclass
class Section:
    name: str
    comment: str
    comment_char: str
    indent: str
    start: int
    end: int = 0


@dataclass
class ConstInfo:
    name: str
    initial: Optional[str]
    persist: bool


@dataclass
class KeyVar:
    name: str
    options: str
    line: int


@dataclass
class VarState:
    name: str
    options: str
    initial: Optional[str]
    persist: bool
    lookup: Optional[str]
    value: Optional[str]
    source: str  # saved / default / nonpersist / unlinked


@dataclass
class Hotkey:
    doc: "IniDoc"
    section: Section
    ordinal: int
    key_lines: list[tuple[int, str]]
    type: str
    condition: str
    variables: list[KeyVar] = field(default_factory=list)
    runs: list[str] = field(default_factory=list)
    states: list[VarState] = field(default_factory=list)

    @property
    def keys(self) -> list[str]:
        return [value for _, value in self.key_lines]


class IniDoc:
    """保留原始编码/换行符的 ini 文档。"""

    def __init__(
        self,
        path: Path,
        text: str,
        encoding: str,
        bom: bool,
        newline: str,
        lossy: bool = False,
        mod_root: Optional[Path] = None,
    ) -> None:
        self.path = path
        self.mod_root = mod_root
        self.encoding = encoding
        self.bom = bom
        self.newline = newline or "\n"
        self.lossy = lossy
        self.lines: list[str] = text.splitlines(keepends=True)
        self.sections: list[Section] = []
        self.constants: dict[str, ConstInfo] = {}
        self.mtime_ns = self._stat_mtime()
        self._parse_sections()
        self.constants = self._parse_constants()

    def _stat_mtime(self) -> int:
        try:
            return self.path.stat().st_mtime_ns
        except OSError:
            return 0

    @classmethod
    def load(cls, path: Path, mod_root: Optional[Path] = None) -> "IniDoc":
        raw = path.read_bytes()
        bom = raw.startswith(codecs.BOM_UTF8)
        lossy = False
        encoding = "utf-8"
        if raw.startswith(codecs.BOM_UTF16_LE) or raw.startswith(codecs.BOM_UTF16_BE):
            encoding = "utf-16"
            text = raw.decode(encoding)
        elif bom:
            encoding = "utf-8-sig"
            text = raw.decode(encoding)
        else:
            text = None
            for enc in ("utf-8", "gbk"):
                try:
                    text = raw.decode(enc)
                    encoding = enc
                    break
                except UnicodeDecodeError:
                    continue
            if text is None:
                encoding = "utf-8"
                text = raw.decode(encoding, errors="replace")
                lossy = True
        newline = "\r\n" if "\r\n" in text else "\n"
        return cls(path, text, encoding, bom, newline, lossy, mod_root=mod_root)

    def _parse_sections(self) -> None:
        self.sections = []
        current: Optional[Section] = None
        for idx, line in enumerate(self.lines):
            raw = line.rstrip("\r\n")
            m = SECTION_RE.match(raw)
            if not m:
                continue
            if current is not None:
                current.end = idx
            rest = m.group("rest")
            comment = ""
            comment_char = ""
            cm = COMMENT_RE.match(rest)
            if cm:
                comment_char = cm.group(1)
                comment = cm.group(2).strip()
            current = Section(
                name=m.group("name").strip(),
                comment=comment,
                comment_char=comment_char,
                indent=m.group("indent"),
                start=idx,
                end=len(self.lines),
            )
            self.sections.append(current)
        if current is not None:
            current.end = len(self.lines)

    def _parse_constants(self) -> dict[str, ConstInfo]:
        result: dict[str, ConstInfo] = {}
        for sec in self.sections:
            if sec.name.lower() != "constants":
                continue
            for idx in range(sec.start + 1, sec.end):
                raw = self.lines[idx].strip()
                if not raw or raw[0] in ";#":
                    continue
                m = CONST_RE.match(raw)
                if not m:
                    continue
                name = m.group("name").strip()
                key = name.lstrip("$").lower()
                value = m.group("value")
                if value is not None:
                    value = re.split(r"\s+[;#]", value, maxsplit=1)[0].strip()
                persist = bool(m.group("persist"))
                old = result.get(key)
                if old is None:
                    result[key] = ConstInfo(name=name.lstrip("$"), initial=value, persist=persist)
                else:
                    if old.initial is None and value is not None:
                        old.initial = value
                    old.persist = old.persist or persist
        return result

    def save(self) -> None:
        if self.lossy:
            raise ValueError("文件编码无法安全识别，已阻止写入。")
        if self.mod_root is not None:
            backup_file(self.path, self.mod_root)
        data = "".join(self.lines).encode(self.encoding)
        atomic_write(self.path, data)
        self.mtime_ns = self._stat_mtime()

    def insert_lines(self, idx: int, new_lines: list[str]) -> None:
        """在指定行前插入行，并照顾文件末尾缺少换行符的情况。"""
        if not new_lines:
            return
        if idx > 0 and not self.lines[idx - 1].endswith(("\n", "\r")):
            self.lines[idx - 1] += self.newline
        prepared = [line if line.endswith(("\n", "\r")) else line + self.newline for line in new_lines]
        self.lines[idx:idx] = prepared


def parse_hotkeys(doc: IniDoc) -> list[Hotkey]:
    result: list[Hotkey] = []
    for sec in doc.sections:
        if not sec.name.lower().startswith("key"):
            continue
        key_lines: list[tuple[int, str]] = []
        variables: list[KeyVar] = []
        runs: list[str] = []
        hk_type = ""
        condition = ""
        for idx in range(sec.start + 1, sec.end):
            raw = doc.lines[idx].strip()
            if not raw or raw[0] in ";#":
                continue
            m = KEY_LINE_RE.match(raw)
            if m:
                value = m.group("value").strip()
                if value:
                    key_lines.append((idx, value))
                continue
            m = TYPE_RE.match(raw)
            if m:
                hk_type = m.group("value").strip().lower()
                continue
            m = CONDITION_RE.match(raw)
            if m:
                condition = m.group("value").strip()
                continue
            m = RUN_RE.match(raw)
            if m:
                runs.append(m.group("value").strip())
                continue
            m = VAR_ASSIGN_RE.match(raw)
            if m:
                variables.append(
                    KeyVar(
                        name=m.group("name").strip(),
                        options=m.group("value").strip(),
                        line=idx,
                    )
                )
        if not key_lines:
            continue
        result.append(
            Hotkey(
                doc=doc,
                section=sec,
                ordinal=len(result) + 1,
                key_lines=key_lines,
                type=hk_type or "press",
                condition=condition,
                variables=variables,
                runs=runs,
            )
        )
    return result


def build_states(hk: Hotkey, game_root: Optional[Path], d3dx: Optional["D3dxUser"]) -> list[VarState]:
    states: list[VarState] = []
    for var in hk.variables:
        info = hk.doc.constants.get(var.name.lower())
        persist = bool(info.persist) if info else False
        initial = info.initial if info and info.initial is not None else "0"
        lookup = make_lookup_key(game_root, hk.doc.path, var.name)
        entry_value = d3dx.get(lookup) if d3dx is not None and lookup else None
        if entry_value is not None:
            value = entry_value
            source = "saved"
        elif persist:
            value = initial
            source = "default"
        elif lookup is None:
            value = None
            source = "unlinked"
        else:
            value = None
            source = "nonpersist"
        states.append(
            VarState(
                name=var.name,
                options=var.options,
                initial=initial,
                persist=persist,
                lookup=lookup,
                value=value,
                source=source,
            )
        )
    return states


def detect_panel(docs: list[IniDoc], hotkeys: list[Hotkey]) -> list[str]:
    """检测模组是否带有屏幕界面/快捷键面板。

    命中任意一条即视为有面板（锁定按键修改；识别名仍可改）：
      * 快捷键名称包含 menu/help/ui/panel 等关键字
      * 快捷键控制的变量名包含界面关键字
      * [Present] 根据快捷键变量条件绘制内容
    鼠标键很常见（例如战斗模组用右键配合 WASD），单独出现不判为面板，
    只有已经命中其他界面证据时才作为补充提示。
    """
    reasons: list[str] = []

    def add(reason: str) -> None:
        if reason not in reasons:
            reasons.append(reason)

    panel_condition_vars: set[str] = set()
    benign_var_re = re.compile(r"(credit|notif|toast|message|msg)", re.I)
    mouse_reason: Optional[str] = None
    for hk in hotkeys:
        if hk.section.name == PANEL_KEY_SECTION:
            # 本工具生成的图片菜单面板快捷键，不算 mod 自带界面。
            continue
        if has_ui_token(hk.section.name):
            add(f"按键名含界面关键字：[{hk.section.name}]")
        for var in hk.variables:
            if has_ui_token(var.name):
                add(f"按键控制界面变量：${var.name}")
            # Present 条件只看主状态变量：逗号列表，或该按键唯一的变量。
            # 同时排除 creditinfo 这类副作用变量，避免把作者信息提示误判成面板。
            if benign_var_re.search(var.name):
                continue
            if "," in var.options or len(hk.variables) == 1:
                panel_condition_vars.add(var.name.lower())
        if mouse_reason is None:
            for value in hk.keys:
                if MOUSE_KEY_RE.search(value):
                    # 仅用鼠标键不算面板：很多战斗模组用左/右键配合 WASD。
                    mouse_reason = f"使用鼠标按键：{value}"
                    break

    # 建立段名索引，便于跟踪 [Present] -> run = CommandList... 的绘制链。
    section_index: dict[str, tuple[IniDoc, Section]] = {}
    for doc in docs:
        for sec in doc.sections:
            section_index.setdefault(sec.name.lower(), (doc, sec))

    draw_line_re = re.compile(
        r"(?im)^\s*(?:run|ps-t\d+|vs|ps|hs|ds|gs|cs)\s*=|CustomShader",
        re.I,
    )
    run_ref_re = re.compile(r"(?im)^\s*(?:pre\s+|post\s+)?run\s*=\s*(\S+)", re.I)
    if_re_cache = {
        var: re.compile(
            r"(?im)^\s*(?:if|elif)\b[^\r\n]*\$" + re.escape(var) + r"(?![A-Za-z0-9_])"
        )
        for var in panel_condition_vars
    }

    for doc in docs:
        for sec in doc.sections:
            if sec.name.lower() != "present":
                continue
            # 深度 2 足够覆盖典型的 [Present] -> CommandListDrawXxx。
            queue: list[tuple[IniDoc, Section, int]] = [(doc, sec, 0)]
            visited: set[tuple[str, int, int]] = set()
            while queue:
                cur_doc, cur_sec, depth = queue.pop(0)
                identity = (str(cur_doc.path), cur_sec.start, cur_sec.end)
                if identity in visited:
                    continue
                visited.add(identity)
                body = "".join(cur_doc.lines[cur_sec.start + 1 : cur_sec.end])
                body = strip_panel_marker_text(body)
                if not body:
                    continue
                if draw_line_re.search(body):
                    for var, if_re in if_re_cache.items():
                        if if_re.search(body):
                            add(f"[Present] 根据快捷键变量 ${var} 绘制界面")
                            break
                if depth < 2:
                    for ref in run_ref_re.findall(body):
                        key = ref.strip().lower()
                        candidates = [key]
                        if "\\" in key:
                            candidates.append(key.rsplit("\\", 1)[-1])
                        for candidate in candidates:
                            hit = section_index.get(candidate)
                            if hit is not None:
                                queue.append((hit[0], hit[1], depth + 1))
                                break
    if reasons and mouse_reason is not None:
        add(mouse_reason)
    return reasons


@dataclass
class ModInfo:
    path: Path
    name: str
    enabled: bool
    hotkeys: list[Hotkey]
    panel: bool
    panel_reasons: list[str]
    errors: list[str] = field(default_factory=list)
    loaded: bool = True
    image_panel: bool = False
    image_panel_key: str = ""
    image_panel_condition: str = ""


def analyze_mod(path: Path, game_root: Optional[Path], d3dx: Optional["D3dxUser"]) -> ModInfo:
    docs: list[IniDoc] = []
    errors: list[str] = []
    for ini in find_ini_files(path):
        try:
            docs.append(IniDoc.load(ini, mod_root=path))
        except Exception as exc:  # noqa: BLE001 - 单个文件失败不应中断扫描
            errors.append(f"{ini.name}: {exc}")
    hotkeys: list[Hotkey] = []
    for doc in docs:
        for hk in parse_hotkeys(doc):
            hk.states = build_states(hk, game_root, d3dx)
            hotkeys.append(hk)
    hotkeys.sort(key=lambda hk: (str(hk.doc.path).lower(), hk.section.start))
    reasons = detect_panel(docs, hotkeys)
    image_panel = False
    for doc in docs:
        text = "".join(doc.lines)
        if PANEL_BEGIN in text:
            image_panel = True
            break
    image_panel_key = ""
    image_panel_condition = ""
    if image_panel:
        for hk in hotkeys:
            if hk.section.name == PANEL_KEY_SECTION:
                if hk.keys and not image_panel_key:
                    image_panel_key = hk.keys[0]
                for line in hk.doc.lines[hk.section.start + 1 : hk.section.end]:
                    match = CONDITION_RE.match(line.strip())
                    if match:
                        image_panel_condition = match.group("value")
                        break
                if image_panel_key:
                    break
    return ModInfo(
        path=path,
        name=path.name,
        enabled=not bool(DISABLED_DIR_RE.match(path.name)),
        hotkeys=hotkeys,
        panel=bool(reasons),
        panel_reasons=reasons,
        errors=errors,
        image_panel=image_panel,
        image_panel_key=image_panel_key,
        image_panel_condition=image_panel_condition,
    )


def has_direct_mod_ini(path: Path) -> bool:
    """目录本身（不含子目录）是否有可识别的 mod ini。"""
    try:
        return any(p.is_file() and is_mod_ini(p) for p in path.iterdir())
    except OSError:
        return False


def collect_mods_under(container: Path) -> list[Path]:
    """展开 Mods 下的分类层，保留每个模组的整个文件夹。

    常见结构是 Mods\\角色分类\\模组\\ini，也有模组本身没有根级 ini，
    而是把各个部件的 ini 放在子文件夹里。这里只展开一层分类，
    分类下的直接子文件夹一律当作一个完整模组，避免把同一个模组拆散。
    """
    result: list[Path] = []
    try:
        entries = sorted(container.iterdir(), key=lambda p: p.name.lower())
    except OSError:
        return result
    for child in entries:
        if not child.is_dir():
            continue
        if child.name == MOD_DATA_DIR_NAME or child.name.startswith("."):
            continue
        if has_direct_mod_ini(child):
            # Mods 下直接放模组（无分类层）。
            result.append(child)
            continue
        if not has_mod_ini(child):
            continue
        sub_mods: list[Path] = []
        try:
            sub_entries = sorted(child.iterdir(), key=lambda p: p.name.lower())
        except OSError:
            sub_entries = []
        for sub in sub_entries:
            if not sub.is_dir():
                continue
            if sub.name == MOD_DATA_DIR_NAME or sub.name.startswith("."):
                continue
            if has_mod_ini(sub):
                sub_mods.append(sub)
        if sub_mods:
            # 这是角色分类目录，子文件夹各算一个完整模组。
            result.extend(sub_mods)
        else:
            # 没有分类层，本身就是一个模组。
            result.append(child)
    return result


def mods_relative_depth(path: Path) -> Optional[int]:
    """返回 path 相对最近一层 Mods 目录的层级；不在 Mods 下返回 None。"""
    try:
        current = path.resolve()
    except OSError:
        current = path
    for ancestor in (current, *current.parents):
        if ancestor.name.casefold() != "mods":
            continue
        try:
            return len(current.relative_to(ancestor).parts)
        except ValueError:
            return None
    return None


def discover_mod_paths(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    depth = mods_relative_depth(root)
    if depth == 0:
        # 选的是 Mods 根目录：展开角色分类，列出每个真实模组。
        found = collect_mods_under(root)
        found.sort(key=lambda p: (bool(DISABLED_DIR_RE.match(p.name)), str(p).lower()))
        return found
    if depth is not None and depth >= 2:
        # Mods\分类\模组：整个文件夹就是一个模组，即使 ini 分散在部件子目录。
        return [root] if has_mod_ini(root) else []
    if depth == 1:
        if has_direct_mod_ini(root):
            # 平铺结构：Mods\模组\ini。
            return [root]
        # 分类目录：直接子文件夹各算一个完整模组。
        children: list[Path] = []
        try:
            for child in sorted(root.iterdir(), key=lambda p: p.name.lower()):
                if not child.is_dir():
                    continue
                if child.name == MOD_DATA_DIR_NAME or child.name.startswith("."):
                    continue
                if has_mod_ini(child):
                    children.append(child)
        except OSError:
            return []
        children.sort(key=lambda p: (bool(DISABLED_DIR_RE.match(p.name)), p.name.lower()))
        return children
    # 不在 Mods 目录树下的手选路径，沿用原判定。
    direct = [
        p
        for p in root.iterdir()
        if p.is_file() and is_mod_ini(p)
    ]
    if direct:
        return [root]
    children = []
    try:
        for child in sorted(root.iterdir(), key=lambda p: p.name.lower()):
            if not child.is_dir():
                continue
            if child.name == MOD_DATA_DIR_NAME or child.name.startswith("."):
                continue
            if has_mod_ini(child):
                children.append(child)
    except OSError:
        return []
    if children:
        if len(children) == 1 and not direct:
            # 选择的是单个模组目录，真正的 ini 只在一个内容子目录里。
            return [root]
        children.sort(key=lambda p: (bool(DISABLED_DIR_RE.match(p.name)), p.name.lower()))
        return children
    if has_mod_ini(root):
        return [root]
    return []


# ---------------------------------------------------------------------------
# d3dx_user.ini
# ---------------------------------------------------------------------------


@dataclass
class D3dxEntry:
    line: int
    name: str
    value: str


class D3dxUser:
    """读取/修改 3DMigoto 的 d3dx_user.ini 持久化变量。"""

    def __init__(self, path: Optional[Path]) -> None:
        self.path = path
        self.doc: Optional[IniDoc] = None
        self.entries: dict[str, list[D3dxEntry]] = {}
        if path is not None and path.is_file():
            try:
                self.doc = IniDoc.load(path)
                self._parse()
            except (OSError, UnicodeError, ValueError):
                self.doc = None

    def _parse(self) -> None:
        self.entries = {}
        if self.doc is None:
            return
        for idx, line in enumerate(self.doc.lines):
            raw = line.strip()
            if not raw or raw[0] in ";#":
                continue
            m = D3DX_ENTRY_RE.match(raw)
            if not m:
                continue
            name = m.group("name").strip().lower()
            value = re.split(r"\s+[;#]", m.group("value"), maxsplit=1)[0].strip()
            self.entries.setdefault(name, []).append(
                D3dxEntry(line=idx, name=name, value=value)
            )

    @property
    def available(self) -> bool:
        return self.doc is not None

    def get(self, name: Optional[str]) -> Optional[str]:
        if not name:
            return None
        values = self.entries.get(name.lower())
        if not values:
            return None
        return values[-1].value

    def set_values(self, changes: dict[str, str]) -> tuple[int, int]:
        """修改已有项或补充新项；返回 (修改数, 新增数)。"""
        if self.path is None or not self.path.is_file():
            raise FileNotFoundError("未找到 d3dx_user.ini")
        if not changes:
            return 0, 0
        # 写前重新读取，避免用旧内容覆盖游戏或外部工具刚写入的修改。
        self.__init__(self.path)
        if self.doc is None:
            raise FileNotFoundError("d3dx_user.ini 无法读取")

        normalised: dict[str, str] = {}
        for name, value in changes.items():
            if name:
                normalised[name.lower()] = str(value)

        updated = 0
        pending: list[tuple[str, str]] = []
        for name, value in normalised.items():
            values = self.entries.get(name)
            if not values:
                pending.append((name, value))
                continue
            for entry in values:
                body = self.doc.lines[entry.line].rstrip("\r\n")
                m = re.match(r"^(\s*\$[^=]+?\s*=\s*)(.*?)(\s*)$", body)
                if not m:
                    continue
                new_body = m.group(1) + value + m.group(3)
                ending = line_ending(self.doc.lines[entry.line]) or self.doc.newline
                self.doc.lines[entry.line] = new_body + ending
                updated += 1

        added = 0
        if pending:
            constants_sec = next(
                (s for s in self.doc.sections if s.name.lower() == "constants"),
                None,
            )
            new_lines = [f"{name} = {value}" for name, value in pending]
            if constants_sec is not None:
                insert_at = constants_sec.end
                self.doc.insert_lines(insert_at, new_lines)
            else:
                if self.doc.lines and not self.doc.lines[-1].endswith(("\n", "\r")):
                    self.doc.lines[-1] += self.doc.newline
                self.doc.lines.append("[Constants]" + self.doc.newline)
                for line in new_lines:
                    self.doc.lines.append(line + self.doc.newline)
            added = len(pending)

        if updated or added:
            self.doc.save()
            self.__init__(self.path)
        return updated, added


# ---------------------------------------------------------------------------
# 模组内状态
# ---------------------------------------------------------------------------


def mod_snapshot_path(mod_path: Path) -> Path:
    return mod_data_dir(mod_path) / SNAPSHOT_FILE_NAME


def load_mod_snapshots(mod_path: Path) -> list[dict]:
    path = mod_snapshot_path(mod_path)
    if not path.is_file():
        old_files = [
            mod_path / SNAPSHOT_FILE_NAME,
            mod_path / LEGACY_SNAPSHOT_FILE_NAME,
        ]
        for old in old_files:
            if old.is_file():
                try:
                    ensure_mod_data_dir(mod_path)
                    old.replace(path)
                except OSError:
                    path = old
                break
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    if isinstance(data, dict):
        data = data.get("snapshots", [])
    if not isinstance(data, list):
        return []
    return [item for item in data if isinstance(item, dict)]


def save_mod_snapshots(mod_path: Path, snapshots: list[dict]) -> None:
    ensure_mod_data_dir(mod_path)
    path = mod_snapshot_path(mod_path)
    payload = json.dumps(
        {"version": 1, "snapshots": snapshots},
        ensure_ascii=False,
        indent=JSON_INDENT,
    )
    atomic_write(path, (payload + "\n").encode("utf-8"))


# ---------------------------------------------------------------------------
# 修改 ini
# ---------------------------------------------------------------------------


def line_body_and_ending(doc: IniDoc, idx: int) -> tuple[str, str]:
    line = doc.lines[idx]
    return line.rstrip("\r\n"), line_ending(line) or doc.newline


def build_replacement_block(
    doc: IniDoc,
    hk: Hotkey,
    new_name: str,
    new_comment: str,
    new_keys: list[str],
) -> list[str]:
    sec = hk.section
    header_nl = line_body_and_ending(doc, sec.start)[1]
    header = f"{sec.indent}[{new_name}]"
    if new_comment.strip():
        # 识别名统一用分号注释，不再写 #。
        header += f" ; {new_comment.strip()}"
    key_indent = "    "
    if hk.key_lines:
        key_indent_match = re.match(r"^([ \t]*)", doc.lines[hk.key_lines[0][0]])
        if key_indent_match:
            key_indent = key_indent_match.group(1)

    block: list[str] = [header + header_nl]
    key_line_indices = {idx for idx, _ in hk.key_lines}
    inserted = False
    for idx in range(sec.start + 1, sec.end):
        if idx in key_line_indices:
            if not inserted:
                for value in new_keys:
                    value = value.strip()
                    if value:
                        block.append(f"{key_indent}key = {value}" + doc.newline)
                inserted = True
            continue
        block.append(doc.lines[idx])
    if not inserted:
        for value in new_keys:
            value = value.strip()
            if value:
                block.append(f"{key_indent}key = {value}" + doc.newline)
    return block


def parse_new_keys(text: str) -> list[str]:
    keys = [line.strip() for line in text.splitlines()]
    return [k for k in keys if k]


def apply_hotkey_edit(
    path: Path,
    old_name: str,
    new_name: str,
    new_comment: str,
    new_keys: list[str],
    mod_root: Optional[Path] = None,
) -> None:
    doc = IniDoc.load(path, mod_root=mod_root)
    if doc.lossy:
        raise ValueError("该文件编码无法安全识别，已阻止写入。")
    if doc.mtime_ns != path.stat().st_mtime_ns:
        doc = IniDoc.load(path, mod_root=mod_root)
    hotkeys = parse_hotkeys(doc)
    target = next((hk for hk in hotkeys if hk.section.name == old_name), None)
    if target is None:
        raise ValueError("找不到原快捷键，文件可能已被外部修改，请刷新后重试。")

    problem = validate_hotkey_name(new_name)
    if problem:
        raise ValueError(problem)
    new_keys = parse_new_keys("\n".join(new_keys))
    if not new_keys:
        raise ValueError("快捷键不能为空。")

    for sec in doc.sections:
        if sec is not target.section and sec.name.lower() == new_name.lower():
            raise ValueError(f"同一文件中已存在同名段：[{sec.name}]")

    block = build_replacement_block(doc, target, new_name, new_comment, new_keys)
    old_block = doc.lines[target.section.start : target.section.end]
    if block == old_block:
        return
    doc.lines[target.section.start : target.section.end] = block
    doc.save()


INIT_DECL_RE = re.compile(
    r"^(?P<indent>[ \t]*)global\s+(?P<persist>persist\s+)?"
    r"\$(?P<name>[^=\s;#]+)(?P<rest>[^\r\n]*)$",
    re.I,
)


def update_initial_values(
    doc: IniDoc,
    changes: dict[str, tuple[str, bool]],
) -> int:
    """修改 [Constants] 中变量的初始值；返回实际变更的变量数。"""
    if not changes:
        return 0
    wanted = {name.lstrip("$").lower(): (name.lstrip("$"), value, persist or False)
              for name, (value, persist) in changes.items()}
    constants_ranges = [
        (sec.start + 1, sec.end)
        for sec in doc.sections
        if sec.name.lower() == "constants"
    ]
    changed_vars: set[str] = set()
    for start, end in constants_ranges:
        for idx in range(start, end):
            body = doc.lines[idx].rstrip("\r\n")
            m = INIT_DECL_RE.match(body)
            if not m:
                continue
            key = m.group("name").lower()
            if key not in wanted:
                continue
            original_name, value, _persist = wanted[key]
            rest = m.group("rest")
            comment = ""
            cm = re.search(r"\s+[;#].*$", rest)
            if cm:
                comment = rest[cm.start():]
            persist_kw = "persist " if m.group("persist") else ""
            new_body = (
                f"{m.group('indent')}global {persist_kw}"
                f"${m.group('name')} = {value}{comment}"
            )
            ending = line_ending(doc.lines[idx]) or doc.newline
            new_line = new_body + ending
            if new_line != doc.lines[idx]:
                doc.lines[idx] = new_line
                changed_vars.add(key)

    missing = [name for name in wanted if name not in changed_vars]
    # 已存在但内容相同的变量不需要新增；只补充完全没有声明的变量。
    declared_names = set()
    for start, end in constants_ranges:
        for idx in range(start, end):
            m = INIT_DECL_RE.match(doc.lines[idx].rstrip("\r\n"))
            if m:
                declared_names.add(m.group("name").lower())
    missing = [name for name in missing if name not in declared_names]

    if missing:
        constants_sec = next(
            (sec for sec in doc.sections if sec.name.lower() == "constants"),
            None,
        )
        new_lines = []
        for key in missing:
            original, value, persist = wanted[key]
            persist_kw = "persist " if persist else ""
            new_lines.append(f"global {persist_kw}${original} = {value}")
            changed_vars.add(key)
        if constants_sec is not None:
            doc.insert_lines(constants_sec.end, new_lines)
        else:
            if doc.lines and not doc.lines[-1].endswith(("\n", "\r")):
                doc.lines[-1] += doc.newline
            doc.lines.append("[Constants]" + doc.newline)
            for line in new_lines:
                doc.lines.append(line + doc.newline)
    return len(changed_vars)


class DefaultValueError(ValueError):
    """默认值不在该快捷键的可选值范围内。"""


class HotkeyConflictError(ValueError):
    """新快捷键与同模组已有快捷键冲突；只提醒，不自动修改原键。"""


def allowed_default_values(hotkey_type: str, options: str) -> list[str]:
    values = [part.strip() for part in options.split(",") if part.strip()]
    if not values:
        return []
    if hotkey_type != "cycle":
        for value in ("0", "1"):
            if value not in values:
                values.append(value)
    return values


def validate_default_value(hotkey_type: str, options: str, value: str) -> Optional[str]:
    allowed = allowed_default_values(hotkey_type, options)
    if allowed and value not in allowed:
        return "默认值必须是可选值之一：" + " / ".join(allowed)
    return None


def apply_initial_values(
    path: Path,
    changes: dict[str, tuple[str, bool]],
    mod_root: Optional[Path] = None,
) -> int:
    doc = IniDoc.load(path, mod_root=mod_root)
    if doc.lossy:
        raise ValueError("该文件编码无法安全识别，已阻止写入。")
    changed = update_initial_values(doc, changes)
    if changed:
        doc.save()
    return changed


# ---------------------------------------------------------------------------
# 图形界面
# ---------------------------------------------------------------------------

import tkinter as tk  # noqa: E402
import tkinter.font as tkfont  # noqa: E402
from tkinter import filedialog, messagebox, simpledialog, ttk  # noqa: E402


class SnapshotManagerDialog(tk.Toplevel):
    def __init__(self, app: "HotkeyApp") -> None:
        super().__init__(app.root)
        self.app = app
        self.title("选择已有状态")
        self.geometry("760x420")
        self.transient(app.root)
        self.grab_set()

        body = ttk.Frame(self, padding=10)
        body.pack(fill="both", expand=True)

        buttons = ttk.Frame(body)
        buttons.pack(fill="x", side="bottom", pady=(10, 0))
        ttk.Button(buttons, text="关闭", command=self.destroy).pack(side="right")
        ttk.Button(buttons, text="删除这个状态", command=self.delete_selected).pack(
            side="right", padx=6
        )
        ttk.Button(buttons, text="恢复这个状态", command=self.restore_selected).pack(side="right")
        ttk.Button(buttons, text="设为启动默认", command=self.set_as_default).pack(
            side="right", padx=6
        )

        ttk.Label(
            body,
            text="一套“状态”就是一套快捷键设置。选一套，再点“恢复这个状态”。",
            foreground="#666666",
        ).pack(fill="x", side="top", pady=(0, 6))

        table = ttk.Frame(body)
        table.pack(fill="both", expand=True, side="top")

        cols = ("time", "label", "keys", "panel")
        self.tree = ttk.Treeview(table, columns=cols, show="headings", selectmode="browse")
        for col, text, width in (
            ("time", "保存时间", 150),
            ("label", "状态名称", 300),
            ("keys", "快捷键数", 80),
            ("panel", "带面板", 80),
        ):
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor="w")
        self.tree.pack(fill="both", expand=True, side="left")
        scroll = ttk.Scrollbar(table, orient="vertical", command=self.tree.yview)
        scroll.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scroll.set)

        self.reload()

    def reload(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.items: dict[str, dict] = {}
        mod = self.app.current_mod
        if mod is None:
            return
        snapshots = self.app.snapshots_for_mod(mod)
        for snap in sorted(snapshots, key=lambda s: s.get("created", ""), reverse=True):
            iid = snap.get("id") or uuid.uuid4().hex
            self.items[iid] = snap
            self.tree.insert(
                "",
                "end",
                iid=iid,
                values=(
                    snap.get("created", ""),
                    snap.get("label", ""),
                    snap.get("key_count", 0),
                    "是" if snap.get("panel") else "否",
                ),
            )
        children = self.tree.get_children()
        if children:
            self.tree.selection_set(children[0])

    def selected_snapshot(self) -> Optional[dict]:
        selection = self.tree.selection()
        if not selection:
            return None
        return self.items.get(selection[0])

    def restore_selected(self) -> None:
        snap = self.selected_snapshot()
        if snap is None:
            messagebox.showinfo("状态", "请选择一个状态。", parent=self)
            return
        self.destroy()
        self.app.restore_snapshot(snap)

    def set_as_default(self) -> None:
        snap = self.selected_snapshot()
        if snap is None:
            messagebox.showinfo("状态", "请选择一个状态。", parent=self)
            return
        mod = self.app.current_mod
        if mod is None:
            return
        if not messagebox.askyesno(
            "设为启动默认",
            "让游戏以后每次启动都使用这套设置？\n\n"
            "工具会把这些值写进 mod 的默认值。\n"
            "这样即使 3DMigoto 因中文路径忘记状态，游戏启动时也会用这套设置。\n\n"
            "请先完全退出游戏；工具会先创建原档备份。继续？",
            parent=self,
        ):
            return

        per_file: dict[Path, dict[str, tuple[str, bool]]] = {}
        skipped = 0
        invalid: list[str] = []
        for item in snap.get("hotkeys", []):
            if not isinstance(item, dict):
                continue
            rel_mod = str(item.get("file_rel_mod", ""))
            path = self.app._resolve_snapshot_file(mod, rel_mod) if rel_mod else None
            if path is None:
                skipped += 1
                continue
            for var in item.get("vars", []):
                if not isinstance(var, dict):
                    continue
                name = str(var.get("name", "")).strip()
                value = var.get("value")
                if not name or value is None:
                    skipped += 1
                    continue
                problem = validate_default_value(
                    str(item.get("type", "")),
                    str(var.get("options", "")),
                    str(value),
                )
                if problem:
                    invalid.append(f"${name}：{problem}")
                    continue
                per_file.setdefault(path, {})[name] = (
                    str(value),
                    bool(var.get("persist")),
                )
        if not per_file:
            if invalid:
                messagebox.showwarning(
                    "默认值不在可选值内",
                    "以下值不在可选值内，未保存：\n" + "\n".join(invalid[:8]),
                    parent=self,
                )
            else:
                messagebox.showinfo(
                    "设为启动默认",
                    "这套设置没有可写入的当前值（可能都是不会记住的变量）。",
                    parent=self,
                )
            return

        written = 0
        errors: list[str] = []
        d3dx_changes: dict[str, str] = {}
        for path, changes in per_file.items():
            try:
                before = path.read_bytes() if path.is_file() else None
                count = apply_initial_values(path, changes, mod_root=mod.path)
                written += count
                if count and before is not None:
                    self.app.register_undo(path, before, "设为启动默认")
            except (OSError, ValueError) as exc:
                errors.append(f"{path.name}: {exc}")
                continue
            for name, (value, persist) in changes.items():
                if persist and self.app.game_root is not None:
                    lookup = make_lookup_key(self.app.game_root, path, name)
                    if lookup:
                        d3dx_changes[lookup] = value

        d3dx_updated = 0
        if d3dx_changes and self.app.d3dx is not None and self.app.d3dx.available:
            try:
                d3dx_updated, _added = self.app.d3dx.set_values(d3dx_changes)
            except (OSError, ValueError) as exc:
                errors.append(f"d3dx_user.ini: {exc}")

        self.destroy()
        self.app.refresh(manual=False)
        summary = [
            f"已写入启动默认值：{written} 项",
            f"已同步当前记忆：{d3dx_updated} 项",
        ]
        if skipped:
            summary.append(f"跳过没有当前值的项：{skipped} 项")
        if invalid:
            summary.append(
                "以下值不在可选值内，已跳过：\n" + "\n".join(invalid[:8])
            )
        if errors:
            summary.append("错误：\n" + "\n".join(errors[:5]))
        if invalid:
            messagebox.showwarning(
                "设为启动默认", "\n".join(summary), parent=self.app.root
            )
        else:
            messagebox.showinfo(
                "设为启动默认", "\n".join(summary), parent=self.app.root
            )

    def delete_selected(self) -> None:
        snap = self.selected_snapshot()
        if snap is None:
            messagebox.showinfo("状态", "请选择一个状态。", parent=self)
            return
        if not messagebox.askyesno(
            "删除状态",
            f"删除这套设置“{snap.get('label', '')}”？删除后找不回来。",
            parent=self,
        ):
            return
        self.app.delete_snapshot(snap.get("id", ""))
        self.reload()


class BackupRestoreDialog(tk.Toplevel):
    def __init__(self, app: "HotkeyApp", target: Path) -> None:
        super().__init__(app.root)
        self.app = app
        self.target = target
        self.mod_root = app.current_mod.path if app.current_mod is not None else target.parent
        self.backups: dict[str, Path] = {}
        self.title(f"恢复原档：{target.name}")
        self.geometry("920x600")
        self.transient(app.root)
        self.grab_set()

        body = ttk.Frame(self, padding=10)
        body.pack(fill="both", expand=True)

        buttons = ttk.Frame(body)
        buttons.pack(fill="x", side="bottom", pady=(10, 0))
        ttk.Button(buttons, text="关闭", command=self.destroy).pack(side="right")
        self.restore_btn = ttk.Button(buttons, text="恢复原档", command=self.restore_selected)
        self.restore_btn.pack(side="right", padx=6)

        preview_frame = ttk.LabelFrame(body, text="差异预览（原档 → 当前）", padding=4)
        preview_frame.pack(fill="both", expand=True, side="bottom", pady=(10, 0))
        self.preview = tk.Text(preview_frame, height=12, wrap="none", state="disabled")
        self.preview.pack(side="left", fill="both", expand=True)
        preview_scroll = ttk.Scrollbar(preview_frame, orient="vertical", command=self.preview.yview)
        preview_scroll.pack(side="right", fill="y")
        self.preview.configure(yscrollcommand=preview_scroll.set)

        table = ttk.Frame(body)
        table.pack(fill="both", expand=True)
        cols = ("time", "size", "file")
        self.tree = ttk.Treeview(table, columns=cols, show="headings", selectmode="browse")
        for col, text, width in (
            ("time", "原档时间", 160),
            ("size", "大小", 90),
            ("file", "原档文件", 600),
        ):
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor="w")
        self.tree.pack(fill="both", expand=True, side="left")
        tree_scroll = ttk.Scrollbar(table, orient="vertical", command=self.tree.yview)
        tree_scroll.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.bind("<<TreeviewSelect>>", self.update_preview)
        self.tree.bind("<Double-1>", lambda _e: self.restore_selected())

        self.load_backups()

    def load_backups(self) -> None:
        backup = original_backup_path(self.target, self.mod_root)
        candidates = [backup] if backup.is_file() else []
        for index, path in enumerate(candidates):
            try:
                stat = path.stat()
                stamp = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                size = f"{stat.st_size / 1024:.1f} KB"
            except OSError:
                stamp, size = "", ""
            iid = f"b{index}"
            self.backups[iid] = path
            self.tree.insert("", "end", iid=iid, values=(stamp, size, path.name))
        children = self.tree.get_children()
        if children:
            self.tree.selection_set(children[0])
            self.update_preview()
        else:
            self.restore_btn.config(state="disabled")
            self.show_preview(f"没有找到原档备份：\n{backup}")

    def show_preview(self, text: str) -> None:
        self.preview.config(state="normal")
        self.preview.delete("1.0", "end")
        self.preview.insert("1.0", text)
        self.preview.config(state="disabled")

    @staticmethod
    def read_text_guess(path: Path) -> str:
        for encoding in ("utf-8-sig", "gbk"):
            try:
                return path.read_text(encoding=encoding)
            except UnicodeDecodeError:
                continue
        return path.read_text(encoding="utf-8", errors="replace")

    def selected_backup(self) -> Optional[Path]:
        selection = self.tree.selection()
        if not selection:
            return None
        return self.backups.get(selection[0])

    def update_preview(self, _event: object = None) -> None:
        backup = self.selected_backup()
        if backup is None or not backup.is_file():
            self.show_preview("")
            return
        try:
            old = self.read_text_guess(backup).splitlines()
            new = self.read_text_guess(self.target).splitlines() if self.target.is_file() else []
            diff = list(
                difflib.unified_diff(
                    old,
                    new,
                    fromfile=f"原档 {backup.name}",
                    tofile=f"当前 {self.target.name}",
                    lineterm="",
                )
            )
        except OSError as exc:
            self.show_preview(f"读取失败：{exc}")
            return
        if not diff:
            self.show_preview("原档与当前文件相同。")
            return
        self.show_preview("\n".join(diff[:500]))

    def restore_selected(self) -> None:
        backup = self.selected_backup()
        if backup is None:
            return
        if not messagebox.askyesno(
            "恢复原档",
            f"用原档覆盖当前文件？\n\n原档：{backup.name}\n当前：{self.target}\n\n"
            "恢复后可用“撤销到上一步”返回。",
            parent=self,
        ):
            return
        try:
            backup_data = backup.read_bytes()
            before = self.target.read_bytes() if self.target.is_file() else None
            backup_file(self.target, self.mod_root)
            atomic_write(self.target, backup_data)
        except OSError as exc:
            messagebox.showerror("恢复失败", str(exc), parent=self)
            return
        if before is not None:
            self.app.register_undo(self.target, before, f"恢复原档 {backup.name}")
        self.destroy()
        self.app.refresh(manual=False)
        self.app.set_status(f"已从原档恢复：{self.target.name}")


class TextPanelDialog(tk.Toplevel):
    """为无面板模组生成右下角快捷键图片菜单面板。"""

    def __init__(
        self,
        app: "HotkeyApp",
        mod: "ModInfo",
        conditions: list[str],
        recommended: str,
    ) -> None:
        super().__init__(app.root)
        self.app = app
        self.mod = mod
        self.conditions = conditions
        self.recommended = recommended
        self.result_key: Optional[str] = None
        self.result_condition: Optional[str] = None
        self.title("添加图片菜单面板")
        self.transient(app.root)
        self.grab_set()
        self.resizable(False, False)

        body = ttk.Frame(self, padding=12)
        body.pack(fill="both", expand=True)
        ttk.Label(
            body,
            text=(
                "为没有快捷键面板的模组生成右下角图片菜单面板。\n"
                "图片含中文，保存在 mod 的 快捷键管理\\zzmi_hotkey_image.png。"
            ),
            justify="left",
        ).pack(anchor="w")
        ttk.Label(body, text="切换快捷键（在输入框内直接按键）：").pack(
            anchor="w", pady=(10, 2)
        )
        default_key = (
            "no_modifiers /" if len(conditions) == 1 else "alt no_ctrl no_shift /"
        )
        self.key_var = tk.StringVar(value=default_key)
        self.key_entry = ttk.Entry(body, textvariable=self.key_var, width=44)
        self.key_entry.pack(fill="x")
        self.key_entry.bind("<KeyPress>", self._on_key_press)
        self.key_entry.bind("<KeyRelease>", self._on_key_release)

        ttk.Label(body, text="生效条件（只读，不能手动输入）：").pack(
            anchor="w", pady=(10, 2)
        )
        suffix = "（推荐）"
        if len(conditions) == 1:
            condition_values = list(conditions)
            initial_condition = conditions[0]
            hint = "只有一个生效条件，已自动选中。"
        else:
            condition_values = [
                condition + suffix if condition == recommended else condition
                for condition in conditions
            ]
            initial_condition = ""
            hint = "存在多个生效条件，请从下拉列表选择（推荐项已标出）。"
        self.condition_var = tk.StringVar(value=initial_condition)
        self.condition_box = ttk.Combobox(
            body,
            textvariable=self.condition_var,
            values=condition_values,
            width=58,
            state="readonly",
        )
        self.condition_box.pack(fill="x")
        ttk.Label(
            body,
            text=hint,
            justify="left",
            foreground="#555555",
        ).pack(anchor="w", pady=(2, 0))

        ttk.Label(
            body, text="图片内容预览（生成 PNG）："
        ).pack(anchor="w", pady=(10, 2))
        preview = tk.Text(body, width=52, height=12, wrap="none", state="normal")
        preview.insert("1.0", "\n".join(build_panel_lines(mod)))
        preview.config(state="disabled")
        preview.pack(fill="both", expand=True)

        buttons = ttk.Frame(body)
        buttons.pack(fill="x", pady=(10, 0))
        ttk.Button(buttons, text="添加", command=self._confirm).pack(
            side="right", padx=4
        )
        ttk.Button(buttons, text="取消", command=self.destroy).pack(side="right")

        self._held_mods: set[str] = set()
        self._down_keys: set[str] = set()
        self._chord_keys: list[str] = []
        self.key_entry.focus_set()

    def _on_key_press(self, event: tk.Event) -> str:
        keysym = event.keysym
        if keysym == "Return":
            self._confirm()
            return "break"
        if keysym == "Escape":
            self.destroy()
            return "break"
        modifier = self.app._capture_modifier(keysym)
        if modifier:
            self._held_mods.add(modifier)
            self._update_preview()
            return "break"
        token = keycode_to_3dmigoto(
            getattr(event, "keycode", 0),
            keysym,
            getattr(event, "char", ""),
        )
        if not token:
            return "break"
        if token not in self._chord_keys:
            self._chord_keys.append(token)
        self._down_keys.add(keysym)
        self._update_preview()
        return "break"

    def _on_key_release(self, event: tk.Event) -> str:
        keysym = event.keysym
        modifier = self.app._capture_modifier(keysym)
        if modifier:
            self._held_mods.discard(modifier)
        else:
            self._down_keys.discard(keysym)
        if not self._held_mods and not self._down_keys and self._chord_keys:
            self._update_preview()
            self._chord_keys.clear()
        return "break"

    def _update_preview(self) -> None:
        key_text = " ".join(self._chord_keys) if self._chord_keys else None
        combo = self.app._format_capture_combo(set(self._held_mods), key_text)
        if combo:
            self.key_var.set(combo)

    def _confirm(self) -> None:
        value = self.key_var.get().strip()
        if not value:
            messagebox.showwarning("快捷键", "请先按一个键。", parent=self)
            return
        choice = self.condition_var.get().strip()
        if choice.endswith("（推荐）"):
            choice = choice[: -len("（推荐）")].strip()
        if not choice:
            messagebox.showwarning(
                "生效条件", "请从下拉列表选择生效条件。", parent=self
            )
            return
        self.result_key = value
        self.result_condition = choice
        self.destroy()


class HotkeyApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.mods: list[ModInfo] = []
        self.current_mod: Optional[ModInfo] = None
        self.current_hk: Optional[Hotkey] = None
        self.game_root: Optional[Path] = None
        self.d3dx: Optional[D3dxUser] = None
        self.last_signature: Optional[tuple] = None
        self._signature_paths: list[Path] = []
        self._panel_png_cache: dict[Path, tuple[tuple[str, ...], bytes]] = {}
        self._auto_ticks = 0
        self.scan_root: Optional[Path] = None
        self._analysis_gen = 0
        self._analysis_queue: queue.Queue[tuple[int, int, Optional[ModInfo]]] = queue.Queue()
        self._busy = False
        self.cell_editor: Optional[tk.Entry] = None
        self.cell_edit_context: Optional[tuple[str, str, Hotkey]] = None
        self.capture_active = False
        self.capture_buffer: list[str] = []
        self.capture_replaced = False
        self.capture_held_mods: set[str] = set()
        self.capture_session_mods: set[str] = set()
        self.capture_nonmod = False
        self.capture_down_keys: set[str] = set()
        self.capture_chord_keys: list[str] = []
        self.capture_chord_mods: set[str] = set()
        self.capture_chord_complete = False
        self.capture_save_after: Optional[str] = None
        self.capture_source: Optional[str] = None
        self.gp_after: Optional[str] = None
        self.gp_held: list[str] = []
        self.gp_prev: set[str] = set()
        self.gp_trigger_on: dict[tuple[int, str], bool] = {}
        self.undo_stack: list[tuple[Path, bytes, str]] = []
        self.last_txt_status: Optional[str] = None
        self.hotkey_conflict_notes: dict[int, list[str]] = {}
        self.shared_key_notes: dict[int, list[str]] = {}
        self.drop_target: Optional[WindowsFileDrop] = None
        self._filter_after: Optional[str] = None
        self._armed_cell: Optional[tuple[str, str]] = None
        self.mod_sort_column: Optional[str] = None
        self.mod_sort_reverse = False

        root.title(APP_TITLE)
        self._apply_window_geometry(root)
        self._setup_style()
        self.mod_root_var = tk.StringVar()
        self.game_root_var = tk.StringVar()
        self.auto_var = tk.BooleanVar(value=True)
        self._build_ui()
        # 启动不自动识别、不自动扫描目录；等用户选择或拖入。
        self.mod_root_var.set("")
        self.game_root_var.set("")
        root.bind("<F5>", lambda _e: self.refresh(manual=True))
        root.bind("<Control-z>", lambda _e: self.undo_last_edit())
        root.bind("<Button-1>", self._global_click, add="+")
        root.protocol("WM_DELETE_WINDOW", self.on_close)
        self._setup_file_drop()
        root.after(150, lambda: self.refresh(manual=True))
        root.after(2200, self.auto_tick)
        root.after(80, self._poll_analysis_queue)

    # -- 界面 --------------------------------------------------------------

    @staticmethod
    def _apply_window_geometry(root: tk.Tk) -> None:
        """按屏幕尺寸取合适的初始窗口，避免在大屏或缩放后过大。"""
        screen_w = root.winfo_screenwidth()
        screen_h = root.winfo_screenheight()
        width = min(1200, max(940, screen_w - 240))
        height = min(760, max(600, screen_h - 180))
        root.geometry(f"{width}x{height}")
        root.minsize(min(900, width), min(540, height))

    def _setup_style(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("vista")
        except tk.TclError:
            pass
        font = ("Microsoft YaHei UI", 9)
        style.configure(".", font=font)
        style.configure("Treeview", font=font, rowheight=24)
        style.configure("Treeview.Heading", font=("Microsoft YaHei UI", 9, "bold"))

    def _build_ui(self) -> None:
        top = ttk.Frame(self.root, padding=(10, 8))
        top.pack(fill="x")
        top.columnconfigure(1, weight=1)

        ttk.Label(top, text="模组目录（可拖入）：").grid(row=0, column=0, sticky="w")
        self.mod_root_entry = ttk.Entry(top, textvariable=self.mod_root_var)
        self.mod_root_entry.grid(row=0, column=1, sticky="we", padx=4)
        self.mod_root_entry.bind("<Return>", lambda _e: self.refresh(manual=True))
        ttk.Button(top, text="浏览...", command=self.browse_mod_root).grid(row=0, column=2, padx=2)
        ttk.Button(top, text="重新扫描", command=lambda: self.refresh(manual=True)).grid(
            row=0, column=3, padx=2
        )
        self.auto_check = ttk.Checkbutton(top, text="自动刷新", variable=self.auto_var)
        self.auto_check.grid(row=0, column=4, padx=(10, 0))

        ttk.Label(top, text="ZZMI 根目录：").grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.game_root_entry = ttk.Entry(top, textvariable=self.game_root_var)
        self.game_root_entry.grid(row=1, column=1, sticky="we", padx=4, pady=(6, 0))
        self.game_root_entry.bind("<Return>", lambda _e: self.refresh(manual=True))
        ttk.Button(top, text="浏览...", command=self.browse_game_root).grid(
            row=1, column=2, padx=2, pady=(6, 0)
        )
        ttk.Button(top, text="自动检测", command=self.auto_detect_game_root).grid(
            row=1, column=3, padx=2, pady=(6, 0)
        )
        self.game_root_state = ttk.Label(top, text="")
        self.game_root_state.grid(row=1, column=4, sticky="w", padx=(10, 0), pady=(6, 0))

        status = ttk.Frame(self.root, padding=(10, 3))
        status.pack(fill="x", side="bottom")
        self.status_var = tk.StringVar(value="准备就绪")
        self.game_status_var = tk.StringVar(value="")
        ttk.Label(status, textvariable=self.status_var, anchor="w").pack(side="left", fill="x", expand=True)
        ttk.Label(status, textvariable=self.game_status_var, anchor="e").pack(side="right")

        paned = ttk.Panedwindow(self.root, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=10, pady=(0, 6))

        left = ttk.Frame(paned)
        paned.add(left, weight=3)
        ttk.Label(left, text="模组").pack(anchor="w", pady=(0, 4))
        filter_frame = ttk.Frame(left)
        filter_frame.pack(fill="x", pady=(0, 4))
        ttk.Label(filter_frame, text="搜索：").pack(side="left")
        self.mod_filter_var = tk.StringVar()
        self.mod_filter_entry = ttk.Entry(filter_frame, textvariable=self.mod_filter_var)
        self.mod_filter_entry.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self.mod_filter_entry.bind("<KeyRelease>", lambda _e: self._schedule_mod_filter())
        self.mod_filter_entry.bind(
            "<Escape>", lambda _e: (self.mod_filter_var.set(""), self._apply_mod_filter())
        )
        ttk.Button(
            filter_frame, text="清空", width=4,
            command=lambda: (self.mod_filter_var.set(""), self._apply_mod_filter()),
        ).pack(side="right")
        left_tree_frame = ttk.Frame(left)
        left_tree_frame.pack(fill="both", expand=True)
        self.mod_tree = ttk.Treeview(
            left_tree_frame,
            columns=("name", "category", "keys", "panel", "enabled"),
            show="headings",
            selectmode="browse",
        )
        self.mod_heading_labels = {
            "name": "模组",
            "category": "分类",
            "keys": "按键数",
            "panel": "面板",
            "enabled": "状态",
        }
        for col, width in (
            ("name", 190),
            ("category", 90),
            ("keys", 60),
            ("panel", 50),
            ("enabled", 55),
        ):
            self.mod_tree.heading(col, text=self.mod_heading_labels[col])
            self.mod_tree.column(
                col,
                width=width,
                anchor="w" if col == "name" else "center",
                stretch=False,
            )
        self.mod_tree.grid(row=0, column=0, sticky="nsew")
        left_tree_frame.rowconfigure(0, weight=1)
        left_tree_frame.columnconfigure(0, weight=1)
        mod_scroll = ttk.Scrollbar(left_tree_frame, orient="vertical", command=self.mod_tree.yview)
        mod_scroll.grid(row=0, column=1, sticky="ns")
        self.mod_scroll_x = ttk.Scrollbar(
            left_tree_frame, orient="horizontal", command=self.mod_tree.xview
        )
        self.mod_scroll_x.grid(row=1, column=0, sticky="ew")
        left_tree_frame.rowconfigure(1, minsize=18)
        self.mod_tree.configure(yscrollcommand=mod_scroll.set, xscrollcommand=self.mod_scroll_x.set)
        self.mod_tree.tag_configure("locked", background="#f2f2f2", foreground="#777777")
        self.mod_tree.bind("<<TreeviewSelect>>", self.on_mod_select)
        self.mod_tree.bind("<Button-1>", self._global_click, add="+")
        self.mod_tree.bind("<Button-1>", self._on_mod_tree_click, add="+")
        self.mod_tree.bind(
            "<Shift-MouseWheel>",
            lambda e: self.mod_tree.xview_scroll(-1 if e.delta > 0 else 1, "units"),
            add="+",
        )

        right = ttk.Frame(paned)
        paned.add(right, weight=7)

        self.f10_notice = tk.Label(
            right,
            text="游戏内切换状态后按 F10 保存；工具会自动刷新显示当前值。",
            anchor="w",
            bg="#fff3cd",
            fg="#7a4300",
            font=("Microsoft YaHei UI", 9, "bold"),
            relief="solid",
            borderwidth=1,
            padx=8,
            pady=3,
        )
        self.f10_notice.pack(fill="x", pady=(0, 4))

        toolbar = ttk.Frame(right)
        toolbar.pack(fill="x", pady=(0, 4))

        self.btn_snapshot = tk.Button(
            toolbar,
            text="保存当前状态",
            command=self.save_snapshot,
            bg="#2f7d32",
            fg="#ffffff",
            activebackground="#1b5e20",
            activeforeground="#ffffff",
            font=("Microsoft YaHei UI", 9, "bold"),
            relief="raised",
            borderwidth=1,
            padx=8,
            pady=2,
            cursor="hand2",
        )
        self.btn_restore_latest = ttk.Button(
            toolbar, text="选择已有状态", command=self.open_restore_snapshot
        )
        self.btn_set_default = tk.Button(
            toolbar,
            text="当前值设为默认",
            command=self.set_current_as_default,
            bg="#c2410c",
            fg="#ffffff",
            activebackground="#9a3412",
            activeforeground="#ffffff",
            font=("Microsoft YaHei UI", 9, "bold"),
            relief="raised",
            borderwidth=1,
            padx=8,
            pady=2,
            cursor="hand2",
        )
        self.btn_undo = ttk.Button(
            toolbar, text="撤销到上一步", command=self.undo_last_edit
        )
        self.more_menu = tk.Menu(toolbar, tearoff=False)
        self.more_menu.add_command(label="恢复原档", command=self.open_backup_restore)
        self.more_menu.add_command(
            label="恢复所选默认", command=lambda: self.reset_states(False)
        )
        self.more_menu.add_command(
            label="恢复全部默认", command=lambda: self.reset_states(True)
        )
        self.more_menu.add_separator()
        self.more_menu.add_command(
            label="添加图片菜单面板", command=self.add_image_panel
        )
        self.more_menu.add_command(
            label="移除图片菜单面板", command=self.remove_image_panel
        )
        self.more_menu.add_separator()
        self.more_menu.add_command(label="打开ini", command=self.open_selected_ini)
        self.more_menu.add_command(label="打开模组文件夹", command=self.open_mod_folder)
        self.more_btn = ttk.Menubutton(toolbar, text="更多", menu=self.more_menu)

        for widget in (
            self.btn_snapshot,
            self.btn_restore_latest,
            self.btn_set_default,
            self.btn_undo,
            self.more_btn,
        ):
            widget.pack(side="left", padx=3)

        self.panel_label = tk.Label(
            right,
            text="未选择模组",
            anchor="w",
            fg="#555555",
            bg=self.root.cget("bg"),
        )
        self.panel_label.pack(fill="x", pady=(0, 2))
        self.panel_key_var = tk.StringVar(value="")
        self.panel_key_label = tk.Label(
            right,
            textvariable=self.panel_key_var,
            anchor="w",
            justify="left",
            fg="#a33a00",
            bg=self.root.cget("bg"),
            font=("Microsoft YaHei UI", 9, "bold"),
            wraplength=700,
        )
        self.txt_status_var = tk.StringVar(value="快捷键 txt：尚未生成")
        self.txt_status_label = tk.Label(
            right,
            textvariable=self.txt_status_var,
            anchor="w",
            fg="#555555",
            bg=self.root.cget("bg"),
        )
        self.txt_status_label.pack(fill="x", pady=(0, 2))
        self.conflict_status_var = tk.StringVar(value="")
        self.conflict_status_label = tk.Label(
            right,
            textvariable=self.conflict_status_var,
            anchor="w",
            fg="#b00020",
            bg=self.root.cget("bg"),
        )
        self.conflict_status_label.pack(fill="x", pady=(0, 2))
        hint_frame = ttk.Frame(right)
        hint_frame.pack(fill="x", pady=(0, 4))
        ttk.Label(
            hint_frame,
            text="单击两次编辑；按键格支持组合键捕获。点列头排序。",
            foreground="#666666",
        ).pack(side="left", fill="x", expand=True)
        ttk.Button(hint_frame, text="使用说明", command=self.show_usage_help).pack(
            side="right", padx=(8, 0)
        )
        self.show_all_columns_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            hint_frame,
            text="显示更多列",
            variable=self.show_all_columns_var,
            command=self._toggle_columns,
        ).pack(side="right", padx=(8, 0))
        details_frame = ttk.LabelFrame(right, text="详情", padding=4)
        details_frame.pack(fill="x", side="bottom", pady=(6, 0))
        self.details = tk.Text(details_frame, height=14, wrap="none", state="disabled")
        self.details.grid(row=0, column=0, sticky="nsew")
        details_scroll = ttk.Scrollbar(details_frame, orient="vertical", command=self.details.yview)
        details_scroll.grid(row=0, column=1, sticky="ns")
        details_scroll_x = ttk.Scrollbar(
            details_frame, orient="horizontal", command=self.details.xview
        )
        details_scroll_x.grid(row=1, column=0, columnspan=2, sticky="ew")
        details_frame.rowconfigure(0, weight=1)
        details_frame.columnconfigure(0, weight=1)
        self.details.configure(
            yscrollcommand=details_scroll.set, xscrollcommand=details_scroll_x.set
        )

        table_frame = ttk.Frame(right)
        table_frame.pack(fill="both", expand=True)
        cols = (
            "name",
            "comment",
            "key",
            "key_cn",
            "type",
            "current",
            "initial",
            "options",
            "condition",
            "file",
        )
        self.hotkey_columns = cols
        self.hotkey_tree = ttk.Treeview(
            table_frame,
            columns=cols,
            show="headings",
            selectmode="browse",
        )
        headings = (
            ("name", "内部名（固定）", 145),
            ("comment", "识别名（可改）", 145),
            ("key", "按键（可改）", 150),
            ("key_cn", "中文说明", 210),
            ("type", "切换方式", 80),
            ("current", "游戏当前值", 100),
            ("initial", "默认值（可改）", 105),
            ("options", "可选值", 100),
            ("condition", "生效条件", 155),
            ("file", "所在文件", 170),
        )
        for col, text, width in headings:
            self.hotkey_tree.heading(col, text=text)
            self.hotkey_tree.column(col, width=width, anchor="w", stretch=False)
        self.simple_columns = (
            "name",
            "comment",
            "key",
            "key_cn",
            "current",
            "initial",
            "options",
        )
        self._displayed_hotkey_columns = list(self.simple_columns)
        self.hotkey_tree.configure(displaycolumns=self.simple_columns)
        self.hotkey_tree.grid(row=0, column=0, sticky="nsew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)
        hk_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.hotkey_tree.yview)
        hk_y.grid(row=0, column=1, sticky="ns")
        hk_x = ttk.Scrollbar(table_frame, orient="horizontal", command=self.hotkey_tree.xview)
        hk_x.grid(row=1, column=0, columnspan=2, sticky="ew")
        table_frame.rowconfigure(1, minsize=18)
        self.hotkey_scroll_x = hk_x
        self.hotkey_tree.configure(yscrollcommand=hk_y.set, xscrollcommand=hk_x.set)
        self.hotkey_tree.tag_configure("locked", background="#f7f7f7", foreground="#666666")
        self.hotkey_tree.tag_configure("conflict", background="#ffe3e3", foreground="#9b1c1c")
        self.hotkey_tree.tag_configure("shared", background="#e6f4ea", foreground="#1f6b2a")
        self.hotkey_tree.bind("<<TreeviewSelect>>", self.on_hotkey_select)
        self.hotkey_tree.bind("<Button-1>", self.on_hotkey_click, add="+")
        self.hotkey_tree.bind("<Motion>", self.on_hotkey_motion, add="+")
        self.hotkey_tree.bind("<Leave>", lambda _e: self.hotkey_tree.configure(cursor=""))
        self.hotkey_tree.bind("<MouseWheel>", lambda _e: self.finish_cell_edit(True), add="+")
        self.hotkey_tree.bind(
            "<Shift-MouseWheel>",
            lambda e: self.hotkey_tree.xview_scroll(-1 if e.delta > 0 else 1, "units"),
            add="+",
        )

    # -- 配置与路径 --------------------------------------------------------

    def set_mod_root(self, chosen: Path) -> None:
        try:
            chosen = chosen.resolve()
        except OSError:
            pass
        self.mod_root_var.set(str(chosen))
        auto = find_game_root(chosen)
        current_root = self.game_root_var.get().strip()
        if auto is not None and (not current_root or not Path(current_root).is_dir()):
            self.game_root_var.set(str(auto))
        self.refresh(manual=True)

    def browse_mod_root(self) -> None:
        initial = self.mod_root_var.get().strip() or str(BASE_DIR)
        chosen = filedialog.askdirectory(
            title="选择模组目录或 Mods 文件夹", initialdir=initial, parent=self.root
        )
        if not chosen:
            return
        self.set_mod_root(Path(chosen))

    def _setup_file_drop(self) -> None:
        if sys.platform != "win32":
            return
        try:
            self.drop_target = WindowsFileDrop(self.root)
        except Exception:  # noqa: BLE001 - 拖放不可用时不影响手动选目录
            self.drop_target = None
        if self.drop_target is not None and self.drop_target.installed:
            self.root.after(150, self._poll_drop_queue)

    def _poll_drop_queue(self) -> None:
        target = self.drop_target
        if target is None:
            return
        for paths in target.take_paths():
            self.on_files_dropped(paths)
        self.root.after(150, self._poll_drop_queue)

    def _resolve_drop_root(self, raw: str) -> Optional[Path]:
        try:
            path = Path(raw).resolve()
        except OSError:
            path = Path(raw)
        if path.is_file():
            if path.suffix.lower() != ".ini" or not is_mod_ini(path):
                return None
            folder = path.parent
            # 如果 ini 在某个 Mods 分类下，找到它真正所属的模组文件夹。
            for ancestor in folder.parents:
                if ancestor.name.casefold() != "mods":
                    continue
                matches: list[Path] = []
                for mod_path in discover_mod_paths(ancestor):
                    try:
                        path.relative_to(mod_path)
                    except ValueError:
                        continue
                    matches.append(mod_path)
                if matches:
                    folder = max(matches, key=lambda p: len(p.parts))
                break
            path = folder
        elif not path.is_dir():
            return None
        # 拖入 ZZMI 根目录时，自动改用其中的 Mods。
        if (path / "Mods").is_dir() and (
            (path / "d3dx.ini").is_file() or (path / "d3dx_user.ini").is_file()
        ):
            path = path / "Mods"
        return path

    def on_files_dropped(self, paths: list[str]) -> None:
        target: Optional[Path] = None
        for raw in paths:
            candidate = self._resolve_drop_root(raw)
            if candidate is not None:
                target = candidate
                break
        if target is None:
            self.root.bell()
            messagebox.showwarning(
                "不支持的文件",
                "请拖入模组文件夹、Mods 文件夹，或 mod 的 ini 文件。",
                parent=self.root,
            )
            return
        if not discover_mod_paths(target):
            self.root.bell()
            messagebox.showwarning(
                "没有找到模组",
                f"拖入的位置没有可识别的 mod ini：\n{target}",
                parent=self.root,
            )
            return
        self.set_mod_root(target)
        self.set_status(f"已载入拖入的模组目录：{target}")

    def browse_game_root(self) -> None:
        initial = self.game_root_var.get().strip() or self.mod_root_var.get().strip()
        chosen = filedialog.askdirectory(title="选择 ZZMI 根目录", initialdir=initial, parent=self.root)
        if not chosen:
            return
        self.game_root_var.set(chosen)
        self.refresh(manual=True)

    def auto_detect_game_root(self) -> None:
        root = find_game_root(Path(self.mod_root_var.get().strip() or BASE_DIR))
        if root is None:
            messagebox.showwarning(
                "未找到",
                "向上查找未发现 d3dx_user.ini 或 d3dx.ini，请手动选择 ZZMI 根目录。",
                parent=self.root,
            )
            return
        self.game_root_var.set(str(root))
        self.refresh(manual=True)

    def set_status(self, text: str) -> None:
        self.status_var.set(text)

    def show_usage_help(self) -> None:
        messagebox.showinfo(
            "使用说明",
            "这个工具做什么\n"
            "读取 mod 的快捷键，显示每个键的作用，并可修改按键和起名字。\n\n"
            "选模组目录\n"
            "可以直接选 ZZMI 的 Mods 文件夹；程序会自动展开角色分类，\n"
            "把每个真正的模组分别列出，不会把整个分类当成一个模组。\n"
            "也可以把模组文件夹、Mods 文件夹或 mod 的 ini 拖进窗口。\n\n"
            "改快捷键\n"
            "1. 单击“按键”格，同时按住想要的键或组合，松开后自动保存。\n"
            "2. 单击“识别名”，给它起个好记的中文名字。\n"
            "3. 单击“默认值”，修改游戏启动时的默认值。\n"
            "4. 新按键不能和同模组的其他快捷键冲突；冲突时不会保存，\n"
            "   原有的键也不会被自动修改。已有冲突会标红提醒。\n\n"
            "“状态”是什么\n"
            "一套“状态”就是一套快捷键设置。\n"
            "保存当前状态：把现在这套设置存到 mod 文件夹。\n"
            "选择已有状态：从列表里选一套，恢复回来。\n\n"
            "游戏里调好之后\n"
            "1. 游戏里每切换一次状态，都按 F10 刷新并保存，或完全退出游戏。\n"
            "2. 回到工具，等自动刷新或点“重新扫描”，看“游戏当前值”是否正确。\n"
            "3. 点“保存当前状态”，起个名字。\n"
            "4. 想让它成为启动默认，点“当前值设为默认”。\n\n"
            "中文路径提醒\n"
            "mod 路径含中文时，3DMigoto 可能记不住持久状态。\n"
            "可在“选择已有状态”里选中一套，点“设为启动默认”，\n"
            "让游戏下次启动直接用这套设置。\n\n"
            "文件位置\n"
            "所有工具文件都在 mod 里的“快捷键管理”文件夹。\n"
            "点“打开模组文件夹”可进入该 mod 的文件夹；快捷键 txt、状态和原档在其“快捷键管理”里。\n"
            "修改 ini、恢复状态前请先完全退出游戏。",
            parent=self.root,
        )

    # -- 扫描 --------------------------------------------------------------

    def collect_signature(self, mod_root: Path, d3dx_path: Optional[Path]) -> tuple:
        entries: list[tuple[str, int, int]] = []
        self._signature_paths = []
        try:
            for dirpath, dirnames, filenames in os.walk(mod_root):
                dirnames[:] = [
                    d
                    for d in dirnames
                    if d != MOD_DATA_DIR_NAME
                    and not d.startswith(".")
                    and not DISABLED_DIR_RE.match(d)
                ]
                for name in filenames:
                    p = Path(dirpath) / name
                    if not is_mod_ini(p):
                        continue
                    try:
                        st = p.stat()
                        entries.append((str(p).lower(), st.st_mtime_ns, st.st_size))
                        self._signature_paths.append(p)
                    except OSError:
                        continue
        except OSError:
            pass
        return (tuple(sorted(entries)), self._d3dx_stamp(d3dx_path))

    def collect_quick_signature(self, d3dx_path: Optional[Path]) -> tuple:
        """快速签名：只检查上次已知 ini，避免每 2 秒全盘遍历。"""
        entries: list[tuple[str, int, int]] = []
        for p in self._signature_paths:
            try:
                st = p.stat()
                entries.append((str(p).lower(), st.st_mtime_ns, st.st_size))
            except OSError:
                entries.append((str(p).lower(), 0, 0))
        return (tuple(sorted(entries)), self._d3dx_stamp(d3dx_path))

    @staticmethod
    def _d3dx_stamp(d3dx_path: Optional[Path]) -> tuple:
        if d3dx_path is None:
            return ()
        try:
            st = d3dx_path.stat()
            return (str(d3dx_path).lower(), st.st_mtime_ns, st.st_size)
        except OSError:
            return (str(d3dx_path).lower(), 0, 0)

    def _show_no_root(self) -> None:
        """未指定模组目录时清空界面，不做任何目录扫描。"""
        self.mods = []
        self.scan_root = None
        self.last_signature = None
        self._signature_paths = []
        self._analysis_gen += 1

        game_root_text = self.game_root_var.get().strip()
        game_root = Path(game_root_text).resolve() if game_root_text else None
        if game_root is not None and not game_root.is_dir():
            game_root = None
        self.game_root = game_root
        d3dx_path = game_root / "d3dx_user.ini" if game_root else None
        d3dx = D3dxUser(d3dx_path) if d3dx_path else None
        self.d3dx = d3dx if d3dx is not None and d3dx.available else None

        self._populate_mods(None)
        self.panel_label.config(text="未选择模组目录：请选择或拖入模组文件夹")
        self.set_status("未选择模组目录，已停止自动扫描。请选择或拖入模组文件夹。")
        self._update_game_status()
        self._update_action_states()

    def refresh(self, manual: bool = True) -> None:
        if self._busy:
            return
        if self.cell_editor is not None:
            # 有未完成的单元格编辑时，手动刷新先提交；自动刷新保持编辑现场。
            if manual:
                self.finish_cell_edit(True)
            return
        self._busy = True
        old_cursor = self.root.cget("cursor")
        self.root.config(cursor="watch")
        self.root.update_idletasks()
        try:
            mod_root_text = self.mod_root_var.get().strip()
            if not mod_root_text:
                self._show_no_root()
                return
            mod_root = Path(mod_root_text)
            if not mod_root.is_dir():
                raise ValueError(f"模组目录不存在：{mod_root}")
            mod_root = mod_root.resolve()

            game_root_text = self.game_root_var.get().strip()
            game_root = Path(game_root_text) if game_root_text else None
            if game_root is None:
                game_root = find_game_root(mod_root)
                if game_root is not None:
                    self.game_root_var.set(str(game_root))
            if game_root is not None:
                game_root = game_root.resolve()
                if not game_root.is_dir():
                    game_root = None
            if game_root is not None:
                try:
                    mod_root.relative_to(game_root)
                except ValueError:
                    auto = find_game_root(mod_root)
                    if auto is not None:
                        game_root = auto
                        self.game_root_var.set(str(auto))

            d3dx_path = game_root / "d3dx_user.ini" if game_root else None
            d3dx = D3dxUser(d3dx_path) if d3dx_path else None

            selected_mod_path = self.current_mod.path if self.current_mod else None
            selected_hk = (
                (self.current_hk.doc.path, self.current_hk.ordinal)
                if self.current_hk is not None
                else None
            )

            mod_paths = discover_mod_paths(mod_root)
            self._analysis_gen += 1
            previous = {mod.path: mod for mod in self.mods}
            mods: list[ModInfo] = []
            for path in mod_paths:
                cached = previous.get(path)
                mods.append(
                    ModInfo(
                        path=path,
                        name=path.name,
                        enabled=not bool(DISABLED_DIR_RE.match(path.name)),
                        # 先沿用旧计数，避免按按键数/面板排序时在扫描期间塌回默认顺序。
                        hotkeys=cached.hotkeys if cached else [],
                        panel=cached.panel if cached else False,
                        panel_reasons=cached.panel_reasons if cached else [],
                        loaded=False,
                        image_panel=cached.image_panel if cached else False,
                        image_panel_key=cached.image_panel_key if cached else "",
                        image_panel_condition=(
                            cached.image_panel_condition if cached else ""
                        ),
                    )
                )

            self.mods = mods
            self.scan_root = mod_root
            self.game_root = game_root
            self.d3dx = d3dx if d3dx is not None and d3dx.available else None
            self.last_signature = self.collect_signature(mod_root, d3dx_path)
            self._populate_mods(selected_mod_path)
            if self.current_mod is not None:
                self._populate_hotkeys(selected_hk)
            self._update_game_status()

            txt_note = f" | {self.last_txt_status}" if self.last_txt_status else ""
            self.set_status(
                f"已发现 {len(mods)} 个模组，正在后台读取快捷键…{txt_note} | {now_text()}"
            )
            if mod_paths:
                self._start_background_analysis(
                    mod_paths, game_root, self.d3dx, self._analysis_gen
                )
        except Exception as exc:  # noqa: BLE001
            self.set_status(f"刷新失败：{exc}")
            if manual:
                messagebox.showerror("刷新失败", str(exc), parent=self.root)
        finally:
            self.root.config(cursor=old_cursor)
            self._busy = False
            self._update_action_states()

    def _update_game_status(self) -> None:
        if self.game_root is None:
            self.game_status_var.set("ZZMI 根目录未设置")
            self.game_root_state.config(text="未设置")
            return
        if self.d3dx is not None and self.d3dx.available:
            self.game_status_var.set(f"d3dx_user.ini 已读取：{self.d3dx.path}")
            self.game_root_state.config(text="已找到 d3dx_user.ini")
        else:
            self.game_status_var.set("ZZMI 根目录下未找到 d3dx_user.ini（只能显示默认值）")
            self.game_root_state.config(text="未找到 d3dx_user.ini")

    def auto_tick(self) -> None:
        mod_root_text = self.mod_root_var.get().strip() if self.auto_var.get() else ""
        if (
            mod_root_text
            and not self._busy
            and self.cell_editor is None
        ):
            mod_root = Path(mod_root_text).resolve()
            game_root_text = self.game_root_var.get().strip()
            game_root = Path(game_root_text).resolve() if game_root_text else None
            d3dx_path = game_root / "d3dx_user.ini" if game_root else None
            try:
                self._auto_ticks += 1
                # 每约 33 秒做一次全盘扫描以发现新增/移走的模组；
                # 其余周期只检查已知 ini 的 mtime，避免反复遍历整个 Mods。
                if not self._signature_paths or self._auto_ticks % 15 == 0:
                    sig = self.collect_signature(mod_root, d3dx_path)
                else:
                    sig = self.collect_quick_signature(d3dx_path)
                if sig != self.last_signature:
                    self.refresh(manual=False)
            except OSError:
                pass
        self.root.after(2200, self.auto_tick)

    def _start_background_analysis(
        self,
        paths: list[Path],
        game_root: Optional[Path],
        d3dx: Optional[D3dxUser],
        generation: int,
    ) -> None:
        thread = threading.Thread(
            target=self._analysis_worker,
            args=(list(paths), game_root, d3dx, generation),
            daemon=True,
        )
        thread.start()

    def _analysis_worker(
        self,
        paths: list[Path],
        game_root: Optional[Path],
        d3dx: Optional[D3dxUser],
        generation: int,
    ) -> None:
        for idx, path in enumerate(paths):
            if self._analysis_gen != generation:
                return
            mod = None
            try:
                mod = analyze_mod(path, game_root, d3dx)
            except Exception as exc:  # noqa: BLE001
                mod = ModInfo(
                    path=path,
                    name=path.name,
                    enabled=not bool(DISABLED_DIR_RE.match(path.name)),
                    hotkeys=[],
                    panel=False,
                    panel_reasons=[],
                    errors=[str(exc)],
                )
            if self._analysis_gen != generation:
                return
            self._analysis_queue.put((generation, idx, mod))
        self._analysis_queue.put((generation, -1, None))

    def _analysis_finished(self, generation: int) -> None:
        if generation != self._analysis_gen or not self.mods:
            return
        # 即使状态栏已被其他提示占用，也要按当前排序列重排一次。
        if self.mod_sort_column in ("keys", "panel"):
            self._reorder_mod_tree_rows()
        # 用户已经产生新提示时，不要用后台扫描结果覆盖。
        if "正在后台读取快捷键" not in self.status_var.get():
            return
        total_keys = sum(len(mod.hotkeys) for mod in self.mods)
        error_count = sum(len(mod.errors) for mod in self.mods)
        extra = f" | 读取错误 {error_count} 个" if error_count else ""
        txt_note = f" | {self.last_txt_status}" if self.last_txt_status else ""
        self.set_status(
            f"已读取 {len(self.mods)} 个模组，{total_keys} 个快捷键{extra}{txt_note} | {now_text()}"
        )

    def _poll_analysis_queue(self) -> None:
        while True:
            try:
                generation, idx, mod = self._analysis_queue.get_nowait()
            except queue.Empty:
                break
            if generation != self._analysis_gen:
                continue
            if idx < 0:
                self._analysis_finished(generation)
                continue
            if mod is None or idx >= len(self.mods):
                continue
            if self.mods[idx].loaded:
                continue
            self.mods[idx] = mod
            self._update_mod_row(idx)
        self.root.after(80, self._poll_analysis_queue)

    # -- 表格填充 ----------------------------------------------------------

    def _mod_category(self, mod: ModInfo) -> str:
        if self.scan_root is None:
            return "—"
        try:
            relative = mod.path.relative_to(self.scan_root)
        except ValueError:
            return "—"
        parts = relative.parts[:-1]
        return " / ".join(parts) if parts else "—"

    def _mod_values(self, mod: ModInfo) -> tuple:
        keys = str(len(mod.hotkeys)) if mod.loaded else "…"
        panel = ("是" if mod.panel else "否") if mod.loaded else "…"
        return (
            mod.name,
            self._mod_category(mod),
            keys,
            panel,
            "启用" if mod.enabled else "已禁用",
        )

    def _update_mod_row(self, idx: int) -> None:
        iid = str(idx)
        if not self.mod_tree.exists(iid):
            return
        mod = self.mods[idx]
        tags = ("locked",) if (mod.loaded and mod.panel) else ()
        self.mod_tree.item(iid, values=self._mod_values(mod), tags=tags)

    def _load_mod_at(self, idx: int) -> ModInfo:
        placeholder = self.mods[idx]
        try:
            mod = analyze_mod(placeholder.path, self.game_root, self.d3dx)
        except Exception as exc:  # noqa: BLE001
            mod = ModInfo(
                path=placeholder.path,
                name=placeholder.name,
                enabled=placeholder.enabled,
                hotkeys=[],
                panel=False,
                panel_reasons=[],
                errors=[str(exc)],
            )
        self.mods[idx] = mod
        self._update_mod_row(idx)
        return mod

    def _schedule_mod_filter(self) -> None:
        if self._filter_after is not None:
            try:
                self.root.after_cancel(self._filter_after)
            except tk.TclError:
                pass
        self._filter_after = self.root.after(200, self._apply_mod_filter)

    def _apply_mod_filter(self) -> None:
        if self._filter_after is not None:
            try:
                self.root.after_cancel(self._filter_after)
            except tk.TclError:
                pass
            self._filter_after = None
        selected_path = self.current_mod.path if self.current_mod else None
        self._populate_mods(selected_path)

    def _on_mod_tree_click(self, event: tk.Event) -> Optional[str]:
        if self.mod_tree.identify_region(event.x, event.y) != "heading":
            return None
        column = self._mod_tree_column_at(event.x)
        if not column:
            return None
        self._sort_mods(column)
        return "break"

    def _mod_tree_column_at(self, x: int) -> str:
        visual = self.mod_tree.identify_column(x)
        try:
            return str(self.mod_tree["columns"][int(visual.lstrip("#")) - 1])
        except (ValueError, IndexError, tk.TclError):
            return ""

    def _sort_mods(self, column: str) -> None:
        if self.mod_sort_column == column:
            self.mod_sort_reverse = not self.mod_sort_reverse
        else:
            self.mod_sort_column = column
            self.mod_sort_reverse = False
        self._update_mod_headings()
        selected_path = self.current_mod.path if self.current_mod else None
        self._populate_mods(selected_path)

    def _update_mod_headings(self) -> None:
        for column, label in self.mod_heading_labels.items():
            suffix = ""
            if column == self.mod_sort_column:
                suffix = " ▼" if self.mod_sort_reverse else " ▲"
            self.mod_tree.heading(column, text=label + suffix)

    def _mod_sort_key(self, mod: ModInfo, column: str) -> object:
        if column == "category":
            return self._mod_category(mod).casefold()
        if column == "keys":
            return len(mod.hotkeys)
        if column == "panel":
            return bool(mod.panel)
        if column == "enabled":
            return not mod.enabled
        return mod.name.casefold()

    def _fit_tree_columns(self, tree: ttk.Treeview, columns: tuple[str, ...], labels: dict[str, str]) -> None:
        font = tkfont.Font(root=self.root, font=("Microsoft YaHei UI", 9))
        for index, column in enumerate(columns):
            width = font.measure(labels.get(column, column)) + 24
            for iid in tree.get_children():
                values = tree.item(iid, "values")
                if index < len(values):
                    width = max(width, font.measure(str(values[index])) + 24)
            tree.column(column, width=width, stretch=False)

    def _flex_hotkey_columns(self) -> None:
        labels = {
            column: self.hotkey_tree.heading(column)["text"]
            for column in self.hotkey_columns
        }
        self._fit_tree_columns(self.hotkey_tree, self.hotkey_columns, labels)

    def _flex_mod_columns(self) -> None:
        self._fit_tree_columns(
            self.mod_tree,
            tuple(self.mod_heading_labels.keys()),
            self.mod_heading_labels,
        )

    def _visible_mod_pairs(self) -> list[tuple[int, ModInfo]]:
        query = self.mod_filter_var.get().strip().casefold()
        visible: list[tuple[int, ModInfo]] = []
        for idx, mod in enumerate(self.mods):
            category = self._mod_category(mod)
            haystack = f"{mod.name} {category} {mod.path}".casefold()
            if query and query not in haystack:
                continue
            visible.append((idx, mod))
        visible.sort(key=lambda pair: pair[1].name.casefold())
        if self.mod_sort_column:
            visible.sort(
                key=lambda pair: self._mod_sort_key(pair[1], self.mod_sort_column or ""),
                reverse=self.mod_sort_reverse,
            )
        return visible

    def _reorder_mod_tree_rows(self) -> None:
        current_iid = None
        if self.current_mod is not None:
            for idx, mod in enumerate(self.mods):
                if mod is self.current_mod:
                    current_iid = str(idx)
                    break
        for position, (idx, _mod) in enumerate(self._visible_mod_pairs()):
            iid = str(idx)
            if self.mod_tree.exists(iid):
                self.mod_tree.move(iid, "", position)
        if current_iid is not None and self.mod_tree.exists(current_iid):
            self.mod_tree.see(current_iid)

    def _populate_mods(self, selected_path: Optional[Path]) -> None:
        for item in self.mod_tree.get_children():
            self.mod_tree.delete(item)
        self.current_mod = None
        self.current_hk = None
        target_iid = None
        first_iid = None
        visible = self._visible_mod_pairs()
        for idx, mod in visible:
            iid = str(idx)
            if first_iid is None:
                first_iid = iid
            tags = ("locked",) if (mod.loaded and mod.panel) else ()
            self.mod_tree.insert(
                "", "end", iid=iid, values=self._mod_values(mod), tags=tags
            )
            if selected_path is not None and mod.path == selected_path:
                target_iid = iid
        self._flex_mod_columns()
        if target_iid is None:
            target_iid = first_iid
        if target_iid is not None:
            self.mod_tree.selection_set(target_iid)
            self.mod_tree.focus(target_iid)
            self.mod_tree.see(target_iid)
            self.on_mod_select()
        else:
            self.current_mod = None
            self.current_hk = None
            self.last_txt_status = None
            self.hotkey_conflict_notes = {}
            self.shared_key_notes = {}
            self.conflict_status_var.set("")
            self._set_panel_key_text("")
            self.txt_status_var.set("快捷键 txt：尚未生成")
            self.txt_status_label.config(fg="#555555")
            self._clear_hotkeys()
            self.panel_label.config(
                text=(
                    "没有匹配的模组"
                    if self.mod_filter_var.get().strip()
                    else "未找到模组 ini"
                )
            )
            self.hotkey_tree.heading("key", text="按键（可改）")
            self.set_details("")
            self._update_action_states()

    def _clear_hotkeys(self) -> None:
        for item in self.hotkey_tree.get_children():
            self.hotkey_tree.delete(item)

    def on_mod_select(self, _event: object = None) -> None:
        selection = self.mod_tree.selection()
        if not selection:
            return
        try:
            idx = int(selection[0])
        except ValueError:
            return
        if idx < 0 or idx >= len(self.mods):
            return
        mod = self.mods[idx]
        same_mod = self.current_mod is not None and self.current_mod.path == mod.path
        previous_hk = (
            (self.current_hk.doc.path, self.current_hk.ordinal)
            if same_mod and self.current_hk is not None
            else None
        )
        if not mod.loaded:
            mod = self._load_mod_at(idx)
        self.current_mod = mod
        self._populate_hotkeys(previous_hk)
        mod = self.current_mod
        if mod.panel:
            self.hotkey_tree.heading("key", text="按键（锁定）")
            self.panel_label.config(
                text="检测到快捷键面板：按键已锁定；识别名、默认值可编辑。",
                fg="#a33a00",
            )
            self._set_panel_key_text(self._panel_hotkey_text(mod))
        else:
            self.hotkey_tree.heading("key", text="按键（可改）")
            if mod.image_panel:
                self.panel_label.config(
                    text="未检测到 mod 自带面板；本工具已添加图片菜单面板。",
                    fg="#1f5fa8",
                )
                self._set_panel_key_text(
                    "图片菜单面板切换键："
                    + (
                        describe_key_line(mod.image_panel_key)
                        if mod.image_panel_key
                        else "未识别"
                    )
                )
            else:
                self.panel_label.config(
                    text="未检测到快捷键面板：按键、识别名、默认值可编辑；内部名固定。",
                    fg="#2d6a2d",
                )
                self._set_panel_key_text("")
        if mod.errors:
            self.set_status("部分文件读取失败：" + "；".join(mod.errors[:3]))
        self.write_hotkey_table(mod)
        self._update_action_states()

    def _set_panel_key_text(self, text: str) -> None:
        self.panel_key_var.set(text)
        if text:
            if not self.panel_key_label.winfo_manager():
                self.panel_key_label.pack(
                    fill="x", pady=(0, 2), before=self.txt_status_label
                )
        else:
            self.panel_key_label.pack_forget()

    def _panel_hotkey_text(self, mod: ModInfo) -> str:
        section_names: set[str] = set()
        variable_names: set[str] = set()
        for reason in mod.panel_reasons:
            if reason.startswith("使用鼠标按键"):
                continue
            for match in re.finditer(r"\[([^\]]+)\]", reason):
                name = match.group(1).strip().lower()
                if name != "present":
                    section_names.add(name)
            for match in re.finditer(r"\$([A-Za-z0-9_.\\]+)", reason):
                variable_names.add(match.group(1).lower())
        matches: list[Hotkey] = []
        for hk in mod.hotkeys:
            if hk.section.name.lower() in section_names or any(
                var.name.lower() in variable_names for var in hk.variables
            ):
                matches.append(hk)
        if not matches:
            matches = [
                hk for hk in mod.hotkeys
                if any(MOUSE_KEY_RE.search(value) for value in hk.keys)
            ]
        if not matches:
            return "面板快捷键：未识别"
        # 优先展示菜单/帮助等“打开面板”的键。
        def priority(hk: Hotkey) -> tuple:
            text = hk.section.name.lower() + " " + " ".join(
                var.name.lower() for var in hk.variables
            )
            key_part = 0 if re.search(r"(menu|help|panel|ui)", text) else 1
            return (key_part, str(hk.doc.path).lower(), hk.section.start)

        matches.sort(key=priority)
        descriptions: list[str] = []
        for hk in matches:
            description = describe_key_lines(hk.keys)
            # 提示只保留按键本身，去掉“同时按住/不按某键”这类长说明。
            description = re.sub(r"\s*（[^）]*）", "", description).strip()
            if description and description != "—" and description not in descriptions:
                descriptions.append(description)
        if not descriptions:
            return "面板快捷键：未识别"
        shown = "、".join(descriptions[:3])
        if len(descriptions) > 3:
            shown += "…"
        return "面板快捷键：" + shown

    def _primary_ini(self, mod: ModInfo) -> Optional[Path]:
        """取快捷键最多的 ini 作为该 mod 的主 ini。"""
        counts: dict[Path, int] = {}
        for hk in mod.hotkeys:
            counts[hk.doc.path] = counts.get(hk.doc.path, 0) + 1
        if not counts:
            return None

        def sort_key(path: Path) -> tuple:
            try:
                depth = len(path.relative_to(mod.path).parts)
            except ValueError:
                depth = 999
            return (-counts.get(path, 0), depth, str(path).lower())

        return sorted(counts, key=sort_key)[0]

    def write_hotkey_table(self, mod: ModInfo) -> Optional[Path]:
        """为当前模组生成快捷键 txt 表格，放在模组的“快捷键管理”文件夹。"""
        if not mod.hotkeys:
            removed = self._prune_hotkey_tables(mod, keep_name=None)
            note = (
                "已清理旧快捷键 txt（当前没有快捷键）"
                if removed
                else "未生成快捷键 txt（没有快捷键）"
            )
            self.last_txt_status = note
            self.txt_status_var.set(note)
            self.txt_status_label.config(fg="#a33a00")
            self.set_status(note)
            return None
        primary_ini = self._primary_ini(mod)
        if primary_ini is None:
            return None
        safe_name = re.sub(r'[\\/:*?"<>|]', "_", mod.name).strip().rstrip(".") or "mod"
        filename = f"快捷键_{safe_name}.txt"
        target = ensure_mod_data_dir(mod.path) / filename
        old_target = primary_ini.parent / filename
        if old_target.is_file() and old_target != target and not target.exists():
            try:
                old_target.replace(target)
            except OSError:
                pass
        rows: list[list[str]] = []
        for hk in mod.hotkeys:
            # 有备注就用备注作为名称，否则用 [Key...] 段名。
            display_name = hk.section.comment.strip() or hk.section.name
            name = (
                display_name.replace("\t", " ").replace("\r", " ").replace("\n", " ")
                .replace("|", "/")
            )
            keys = (
                " / ".join(hk.keys)
                .replace("\t", " ").replace("\r", " ").replace("\n", " ")
                .replace("|", "/")
            )
            description = (
                describe_key_lines(hk.keys)
                .replace("\t", " ").replace("\r", " ").replace("\n", " ")
                .replace("|", "/")
            )
            rows.append([name, keys, description])
        data = render_text_table(
            ["名称", "快捷键", "中文说明"],
            rows,
            [22, 34, 44],
        ).encode("utf-8-sig")
        try:
            if target.exists() and target.read_bytes() == data:
                removed = self._prune_hotkey_tables(mod, keep_name=target.name)
                self._notify_table_saved(mod, target, changed=False, removed=removed)
                self._update_panel_image(mod)
                return target
            atomic_write(target, data)
            removed = self._prune_hotkey_tables(mod, keep_name=target.name)
            self._notify_table_saved(mod, target, changed=True, removed=removed)
            self._update_panel_image(mod)
            return target
        except OSError as exc:
            self.last_txt_status = f"快捷键 txt 保存失败：{exc}"
            self.txt_status_var.set(f"快捷键 txt 保存失败：{exc}")
            self.txt_status_label.config(fg="#b00020")
            self.set_status(f"快捷键 txt 写入失败：{exc}")
            return None

    def _update_panel_image(self, mod: ModInfo) -> None:
        """已添加图片菜单面板时，按键变化后同步重新生成 PNG。"""
        docs = {hk.doc.path: hk.doc for hk in mod.hotkeys}
        if not any(PANEL_BEGIN in "".join(doc.lines) for doc in docs.values()):
            return
        image_path = mod_data_dir(mod.path) / PANEL_IMAGE_FILENAME
        lines = tuple(build_panel_lines(mod))
        cached = self._panel_png_cache.get(image_path)
        if cached is not None and cached[0] == lines and image_path.is_file():
            return
        try:
            png, _, _ = render_panel_png(list(lines))
            if not (image_path.is_file() and image_path.read_bytes() == png):
                atomic_write(image_path, png)
            self._panel_png_cache[image_path] = (lines, png)
        except (OSError, RuntimeError):
            pass

    def _prune_hotkey_tables(self, mod: ModInfo, keep_name: Optional[str]) -> int:
        """只保留当前快捷键 txt，删除管理文件夹里以前生成的旧文件。"""
        folder = mod_data_dir(mod.path)
        if not folder.is_dir():
            return 0
        removed = 0
        try:
            entries = list(folder.iterdir())
        except OSError:
            return 0
        for path in entries:
            if not path.is_file():
                continue
            name = path.name
            if not name.startswith("快捷键_") or not name.lower().endswith(
                (".txt", ".xlsx")
            ):
                continue
            if keep_name is not None and name == keep_name:
                continue
            try:
                path.unlink()
                removed += 1
            except OSError:
                continue
        return removed

    def _notify_table_saved(
        self, mod: ModInfo, target: Path, changed: bool, removed: int = 0
    ) -> None:
        try:
            shown = target.relative_to(mod.path)
        except ValueError:
            shown = target
        cleanup = f"；已清理旧 txt {removed} 个" if removed else ""
        if changed:
            self.last_txt_status = f"快捷键 txt 已保存：{shown}{cleanup}"
            self.txt_status_var.set(f"快捷键 txt 已保存：{shown}{cleanup}")
            self.txt_status_label.config(fg="#2d6a2d")
            self.set_status(f"已保存快捷键 txt：{target}{cleanup}")
        else:
            self.last_txt_status = f"快捷键 txt 已保存：{shown}{cleanup}"
            self.txt_status_var.set(f"快捷键 txt 已保存（内容未变）：{shown}{cleanup}")
            self.txt_status_label.config(fg="#2d6a2d")
            self.set_status(
                f"快捷键 txt 已是最新：{target}"
                + (f"；已清理旧文件 {removed} 个" if removed else "")
            )

    # -- 图片菜单面板功能 ------------------------------------------

    def add_image_panel(self) -> None:
        mod = self.current_mod
        if mod is None:
            messagebox.showinfo("图片菜单面板", "请先选择一个模组。", parent=self.root)
            return
        if mod.panel:
            messagebox.showinfo(
                "图片菜单面板",
                "当前模组已有快捷键面板，该功能只用于没有面板的模组。",
                parent=self.root,
            )
            return
        if not mod.hotkeys:
            messagebox.showinfo(
                "图片菜单面板", "当前模组没有快捷键，无法生成面板。", parent=self.root
            )
            return
        target = self._primary_ini(mod)
        if target is None:
            return

        conditions = collect_panel_conditions(mod.hotkeys)
        if not conditions:
            messagebox.showerror(
                "图片菜单面板",
                "当前 mod 没有可用的生效条件，无法生成面板。\n"
                "请先给快捷键添加 condition 后再试。",
                parent=self.root,
            )
            return
        recommended = recommend_panel_condition(mod.hotkeys, conditions)

        dialog = TextPanelDialog(self, mod, conditions, recommended)
        self.root.wait_window(dialog)
        key_line = dialog.result_key
        if not key_line:
            return
        active_condition = dialog.result_condition or ""
        if not active_condition:
            messagebox.showerror(
                "图片菜单面板",
                "必须设置生效条件才能生成面板。",
                parent=self.root,
            )
            return
        target_condition_key = " ".join(active_condition.split()).casefold()
        for hk in mod.hotkeys:
            if hk.section.name == PANEL_KEY_SECTION:
                continue
            if " ".join(hk.condition.split()).casefold() == target_condition_key:
                # 同条件下的同键属于一键多开，正常。
                continue
            for existing in hk.keys:
                if key_lines_conflict(key_line, existing):
                    messagebox.showwarning(
                        "快捷键冲突",
                        f"该快捷键与 {hotkey_label(hk)} 的 "
                        f"{describe_key_line(existing)} 冲突，未添加。",
                        parent=self.root,
                    )
                    return

        try:
            panel_lines = build_panel_lines(mod)
            png, _, _ = render_panel_png(panel_lines)
        except RuntimeError as exc:
            messagebox.showerror("图片菜单面板", str(exc), parent=self.root)
            return

        data_dir = mod_data_dir(mod.path)
        image_path = data_dir / PANEL_IMAGE_FILENAME
        shader_path = data_dir / PANEL_SHADER_FILENAME
        try:
            before = target.read_bytes()
            doc = IniDoc.load(target, mod_root=mod.path)
            if doc.lossy:
                raise ValueError("ini 编码无法安全识别，已阻止写入。")
            ensure_mod_data_dir(mod.path)
            image_rel = os.path.relpath(image_path, target.parent).replace("\\", "/")
            shader_rel = os.path.relpath(shader_path, target.parent).replace("\\", "/")
            doc.lines = ensure_image_panel_lines(
                doc.lines, key_line, image_rel, shader_rel, active_condition
            )
            atomic_write(image_path, png)
            atomic_write(shader_path, PANEL_SHADER_SOURCE.encode("ascii"))
            self._panel_png_cache[image_path] = (tuple(panel_lines), png)
            doc.save()
        except (OSError, ValueError) as exc:
            messagebox.showerror("图片菜单面板", f"写入失败：{exc}", parent=self.root)
            return

        self.register_undo(target, before, "添加图片菜单面板")
        self.refresh(manual=False)
        messagebox.showinfo(
            "图片菜单面板",
            f"已添加。游戏中按 {key_line} 显示/隐藏。\n"
            f"生效条件：{active_condition}\n"
            "回到游戏后按 F10，或重新进入，让 mod 重新加载。",
            parent=self.root,
        )

    def remove_image_panel(self) -> None:
        mod = self.current_mod
        if mod is None:
            messagebox.showinfo("图片菜单面板", "请先选择一个模组。", parent=self.root)
            return
        target = self._primary_ini(mod)
        if target is None:
            return
        try:
            before = target.read_bytes()
        except OSError as exc:
            messagebox.showerror("图片菜单面板", f"读取失败：{exc}", parent=self.root)
            return
        current = before.decode("utf-8", errors="ignore")
        if PANEL_BEGIN not in current:
            messagebox.showinfo(
                "图片菜单面板", "当前模组没有添加图片菜单面板。", parent=self.root
            )
            return
        try:
            doc = IniDoc.load(target, mod_root=mod.path)
            if doc.lossy:
                raise ValueError("ini 编码无法安全识别，已阻止写入。")
            doc.lines = strip_panel_lines(doc.lines)
            doc.save()
        except (OSError, ValueError) as exc:
            messagebox.showerror("图片菜单面板", f"移除失败：{exc}", parent=self.root)
            return

        data_dir = mod_data_dir(mod.path)
        for name in (PANEL_IMAGE_FILENAME, PANEL_SHADER_FILENAME):
            path = data_dir / name
            if path.is_file():
                try:
                    path.unlink()
                except OSError:
                    pass
        self.register_undo(target, before, "移除图片菜单面板")
        self.refresh(manual=False)
        messagebox.showinfo(
            "图片菜单面板", "已移除图片菜单面板。游戏里按 F10 刷新后消失。", parent=self.root
        )

    def _populate_hotkeys(self, selected_hk: Optional[tuple[Path, int]]) -> None:
        self._cancel_cell_editor()
        self._armed_cell = None
        self._clear_hotkeys()
        self.current_hk = None
        mod = self.current_mod
        if mod is None:
            self.hotkey_conflict_notes = {}
            self.shared_key_notes = {}
            self.conflict_status_var.set("")
            return
        conflicts = find_hotkey_conflicts(mod.hotkeys)
        notes: dict[int, list[str]] = {}
        for first, first_key, second, second_key in conflicts:
            notes.setdefault(id(first), []).append(
                f"与 {hotkey_label(second)} 的 {describe_key_line(second_key)} 冲突"
            )
            notes.setdefault(id(second), []).append(
                f"与 {hotkey_label(first)} 的 {describe_key_line(first_key)} 冲突"
            )
        self.hotkey_conflict_notes = notes
        shared_groups = find_shared_key_groups(mod.hotkeys)
        shared_notes: dict[int, list[str]] = {}
        for key_text, group in shared_groups:
            desc = describe_key_line(key_text)
            for hk in group:
                others = [hotkey_label(other) for other in group if other is not hk]
                if not others:
                    continue
                preview = "、".join(others[:4])
                if len(others) > 4:
                    preview += f" 等 {len(others)} 个"
                shared_notes.setdefault(id(hk), []).append(
                    f"与 {preview} 共用 {desc}（同条件，会同时触发，正常）"
                )
        self.shared_key_notes = shared_notes
        status_parts: list[str] = []
        if conflicts:
            status_parts.append(
                f"检测到 {count_conflict_groups(conflicts)} 组冲突"
                f"（共 {len(conflicts)} 对；条件不同；已标红；若功能正常无需修改）"
            )
        if shared_groups:
            status_parts.append(
                f"{len(shared_groups)} 组同条件共用按键（一键切换多个状态，已标绿）"
            )
        self.conflict_status_var.set("；".join(status_parts))
        if conflicts:
            self.conflict_status_label.config(fg="#b00020")
        elif shared_groups:
            self.conflict_status_label.config(fg="#1f5fa8")
        else:
            self.conflict_status_label.config(fg="#555555")
        target_iid = None
        for hk in mod.hotkeys:
            iid = f"{hk.ordinal}:{hk.doc.path}"
            try:
                rel_file = os.path.relpath(hk.doc.path, mod.path)
            except ValueError:
                rel_file = str(hk.doc.path)
            values = (
                hk.section.name,
                hk.section.comment or "",
                " | ".join(hk.keys),
                describe_key_lines(hk.keys),
                hk.type,
                self._format_state(self._visible_states(hk), "current"),
                self._format_state(self._visible_states(hk), "initial"),
                self._format_state(self._visible_states(hk), "options"),
                hk.condition or "—",
                rel_file,
            )
            tag_list: list[str] = []
            if id(hk) in notes:
                # 冲突优先用红底；有面板的锁定灰底不能盖住冲突提示。
                tag_list.append("conflict")
            elif id(hk) in shared_notes:
                tag_list.append("shared")
            elif mod.panel:
                tag_list.append("locked")
            self.hotkey_tree.insert(
                "", "end", iid=iid, values=values, tags=tuple(tag_list)
            )
            if selected_hk is not None and selected_hk[0] == hk.doc.path and selected_hk[1] == hk.ordinal:
                target_iid = iid
        self._flex_hotkey_columns()
        children = self.hotkey_tree.get_children()
        if target_iid is None and children:
            target_iid = children[0]
        if target_iid is not None:
            self.hotkey_tree.selection_set(target_iid)
            self.hotkey_tree.focus(target_iid)
            self.on_hotkey_select()
        else:
            self.set_details("该模组没有可识别的快捷键，或 ini 中不存在 [Key...] 段。")
            self._update_action_states()

    def _format_state(self, states: list[VarState], kind: str) -> str:
        if not states:
            return "—"
        values: list[str] = []
        for state in states:
            if kind == "current":
                if state.source in ("saved", "default"):
                    value = state.value if state.value is not None else "—"
                else:
                    value = "—"
            elif kind == "initial":
                value = state.initial if state.initial is not None else "—"
            else:
                value = state.options or "—"
            if len(states) > 1:
                values.append(f"{state.name}={value}")
            else:
                values.append(value)
        return " ; ".join(values)

    def on_hotkey_select(self, _event: object = None) -> None:
        selection = self.hotkey_tree.selection()
        if not selection:
            return
        iid = selection[0]
        hk = None
        if self.current_mod is not None:
            hk = next(
                (h for h in self.current_mod.hotkeys if f"{h.ordinal}:{h.doc.path}" == iid),
                None,
            )
        self.current_hk = hk
        if hk is None:
            self.set_details("")
        else:
            self.set_details(self._details_text(hk))
        self._update_action_states()

    def _details_text(self, hk: Hotkey) -> str:
        mod = self.current_mod
        lines = [
            f"文件：{hk.doc.path}",
            f"段：[{hk.section.name}]  第 {hk.section.start + 1} 行",
            f"识别名：{hk.section.comment or '—'}",
            f"快捷键：{' | '.join(hk.keys)}",
            f"中文说明：{describe_key_lines(hk.keys)}",
            f"切换方式：{hk.type}",
            f"生效条件：{hk.condition or '—'}",
            f"命令：{'; '.join(hk.runs) if hk.runs else '—'}",
        ]
        conflict_notes = self.hotkey_conflict_notes.get(id(hk))
        if conflict_notes:
            lines.append("快捷键冲突（若功能正常无需修改）：")
            lines.extend(f"  {note}" for note in conflict_notes[:6])
            if len(conflict_notes) > 6:
                lines.append(f"  …另有 {len(conflict_notes) - 6} 条")
        shared_notes = self.shared_key_notes.get(id(hk))
        if shared_notes:
            lines.append(
                "同条件共用按键（一键切换多个状态，已标绿；功能正常无需修改）："
            )
            lines.extend(f"  {note}" for note in shared_notes[:4])
            if len(shared_notes) > 4:
                lines.append(f"  …另有 {len(shared_notes) - 4} 条")
        visible_states = self._visible_states(hk)
        if visible_states:
            lines.append("可调选项：")
            for state in visible_states:
                source_text = {
                    "saved": "来自游戏保存的记忆",
                    "default": "还没保存过，显示默认值",
                    "nonpersist": "这个选项不会保存，重启游戏后回到默认值",
                    "unlinked": "无法读取保存记忆（模组不在 ZZMI 根目录下？）",
                }.get(state.source, state.source)
                current = state.value if state.value is not None else "—"
                lines.append(
                    f"  ${state.name}：游戏当前值 {current}（{source_text}）"
                    f" 默认值 {state.initial if state.initial is not None else '—'}"
                    f" 可选值 {state.options or '—'}"
                    f" 会保存到下次启动={'是' if state.persist else '否'}"
                )
                if state.lookup:
                    lines.append(f"    保存键：{state.lookup}")
        else:
            lines.append("可调选项：无（这个键只执行命令，没有可恢复的值）")
        visible_ids = {id(state) for state in visible_states}
        hidden_names: list[str] = []
        for state in hk.states:
            if id(state) in visible_ids:
                continue
            name = state.name
            if name.lower() not in {item.lower() for item in hidden_names}:
                hidden_names.append(name)
        if hidden_names:
            shown_names = "、".join(f"${name}" for name in hidden_names)
            lines.append(f"未显示内部变量（{len(hidden_names)} 个）：{shown_names}")
        if mod is not None:
            if mod.panel:
                lines.append("快捷键面板：有（按键只读；识别名/默认值可改）")
                for reason in mod.panel_reasons:
                    lines.append(f"  - {reason}")
            else:
                lines.append("快捷键面板：无（内部名固定；按键/识别名/默认值可改）")
            if mod.image_panel:
                key_note = (
                    f"切换键：{describe_key_line(mod.image_panel_key)}"
                    if mod.image_panel_key
                    else "未找到切换键"
                )
                lines.append(f"图片菜单面板：有，本工具添加（{key_note}）")
                if mod.image_panel_condition:
                    lines.append(f"  生效条件：{mod.image_panel_condition}")
                else:
                    lines.append("  生效条件：无（切换角色后可能仍显示）")
                lines.append("  可用“更多 → 移除图片菜单面板”删除。")
            else:
                lines.append("图片菜单面板：无")
        return "\n".join(lines)

    def set_details(self, text: str) -> None:
        self.details.config(state="normal")
        self.details.delete("1.0", "end")
        self.details.insert("1.0", text)
        self.details.config(state="disabled")

    def _update_action_states(self) -> None:
        mod = self.current_mod
        has_mod = mod is not None
        self.btn_undo.config(state="normal" if self.undo_stack else "disabled")
        self.btn_snapshot.config(state="normal" if has_mod else "disabled")
        snapshot_count = len(self.snapshots_for_mod(mod)) if has_mod else 0
        self.btn_restore_latest.config(
            text=(
                f"选择已有状态（{snapshot_count}个）"
                if has_mod
                else "选择已有状态"
            ),
            state="normal" if has_mod else "disabled",
        )
        has_states = bool(has_mod and any(hk_item.states for hk_item in mod.hotkeys))
        self.btn_set_default.config(state="normal" if has_states else "disabled")

    # -- 撤销 / 恢复原档 ---------------------------------------------------

    def register_undo(self, path: Path, data: bytes, description: str) -> None:
        self.undo_stack.append((path, data, description))
        if len(self.undo_stack) > 50:
            del self.undo_stack[:-50]
        self._update_action_states()

    def undo_last_edit(self) -> None:
        if self.cell_editor is not None:
            self.root.bell()
            self.set_status("请先按 Enter 或点击外部完成当前编辑，再撤销到上一步。")
            return
        if not self.undo_stack:
            self.root.bell()
            self.set_status("没有可撤销的上一步操作。")
            return
        path, data, description = self.undo_stack.pop()
        try:
            atomic_write(path, data)
        except OSError as exc:
            self.undo_stack.append((path, data, description))
            self.root.bell()
            self.set_status(f"撤销到上一步失败：{exc}")
            self._update_action_states()
            return
        self.refresh(manual=False)
        self.set_status(f"已撤销：{description}（{path.name}）")
        self._update_action_states()

    def open_backup_restore(self) -> None:
        hk = self.current_hk
        if hk is None:
            return
        BackupRestoreDialog(self, hk.doc.path)

    def on_close(self) -> None:
        if self.cell_editor is not None:
            self.finish_cell_edit(True)
        if self.drop_target is not None:
            try:
                self.drop_target.close()
            except Exception:  # noqa: BLE001
                pass
            self.drop_target = None
        self.root.destroy()

    # -- 单元格直接编辑 ----------------------------------------------------

    def _global_click(self, event: tk.Event) -> None:
        if self.cell_editor is not None and event.widget is not self.cell_editor:
            self.finish_cell_edit(True)

    def _cell_editable(self, hk: Hotkey, column: str) -> bool:
        if column == "comment":
            return True
        if column == "key":
            return not (self.current_mod is not None and self.current_mod.panel)
        if column == "initial":
            return bool(self._unique_states(hk))
        return False

    def on_hotkey_motion(self, event: tk.Event) -> None:
        if self.cell_editor is not None:
            return
        if self.hotkey_tree.identify_region(event.x, event.y) not in ("cell", "tree"):
            self.hotkey_tree.configure(cursor="")
            return
        iid = self.hotkey_tree.identify_row(event.y)
        hk = self._hotkey_by_iid(iid) if iid else None
        column = self._hotkey_column_at(event.x)
        editable = hk is not None and self._cell_editable(hk, column)
        self.hotkey_tree.configure(cursor="hand2" if editable else "arrow")

    def on_hotkey_click(self, event: tk.Event) -> None:
        if self.cell_editor is not None:
            return
        if self.hotkey_tree.identify_region(event.x, event.y) not in ("cell", "tree"):
            self._armed_cell = None
            return
        iid = self.hotkey_tree.identify_row(event.y)
        if not iid:
            self._armed_cell = None
            return
        hk = self._hotkey_by_iid(iid)
        column = self._hotkey_column_at(event.x)
        if column == "name":
            self._armed_cell = None
            self.set_status("段名固定不可改；请编辑“识别名”添加额外名字。")
            return
        if column == "key" and self.current_mod is not None and self.current_mod.panel:
            self._armed_cell = None
            self.root.bell()
            self.set_status("面板模组：按键已锁定，不能直接编辑。")
            return
        if column == "initial" and hk is not None and not self._unique_states(hk):
            self._armed_cell = None
            self.root.bell()
            self.set_status("这个快捷键没有可调选项，没有默认值可改。")
            return
        if hk is None or not self._cell_editable(hk, column):
            self._armed_cell = None
            self.set_status("此列只读")
            return
        cell = (iid, column)
        selected = iid in self.hotkey_tree.selection()
        if self._armed_cell == cell and selected:
            self.root.after_idle(lambda: self.begin_cell_edit(iid, column))
            return
        self._armed_cell = cell
        self.set_status("已选择；再点一次显示编辑框。")

    def _toggle_columns(self) -> None:
        if self.show_all_columns_var.get():
            self._displayed_hotkey_columns = list(self.hotkey_columns)
        else:
            self._displayed_hotkey_columns = list(self.simple_columns)
        self.hotkey_tree.configure(displaycolumns=self._displayed_hotkey_columns)
        self._flex_hotkey_columns()

    def _hotkey_column_at(self, x: int) -> str:
        column = self.hotkey_tree.identify_column(x)
        try:
            return self._displayed_hotkey_columns[int(column.lstrip("#")) - 1]
        except (ValueError, IndexError):
            return ""

    def _hotkey_by_iid(self, iid: str) -> Optional[Hotkey]:
        if self.current_mod is None:
            return None
        return next(
            (
                hk
                for hk in self.current_mod.hotkeys
                if f"{hk.ordinal}:{hk.doc.path}" == iid
            ),
            None,
        )

    def _visible_states(self, hk: Hotkey) -> list[VarState]:
        visible: list[VarState] = []
        for state in hk.states:
            if AUX_STATE_RE.search(state.name):
                continue
            options = [part.strip() for part in state.options.split(",") if part.strip()]
            if not state.persist and len(options) <= 1:
                # creditinfo、hold、jiggle_down 之类的内部状态，不当作可调值显示。
                continue
            visible.append(state)
        return visible

    def _unique_states(self, hk: Hotkey) -> list[VarState]:
        seen: set[str] = set()
        states: list[VarState] = []
        for state in self._visible_states(hk):
            key = state.name.lower()
            if key in seen:
                continue
            seen.add(key)
            states.append(state)
        return states

    def _cell_edit_value(self, hk: Hotkey, column: str) -> str:
        if column == "name":
            return hk.section.name
        if column == "key":
            return " | ".join(hk.keys)
        if column == "comment":
            return hk.section.comment
        if column == "initial":
            states = self._unique_states(hk)
            if not states:
                return ""
            if len(states) == 1:
                return states[0].initial if states[0].initial is not None else "0"
            return " ; ".join(
                f"{state.name}={state.initial if state.initial is not None else '0'}"
                for state in states
            )
        return ""

    def begin_cell_edit(self, iid: str, column: str) -> None:
        hk = self._hotkey_by_iid(iid)
        if hk is None:
            return
        if column == "name":
            self.root.bell()
            self.set_status("段名固定不可改；请编辑“识别名”添加额外名字。")
            return
        if column == "key" and self.current_mod is not None and self.current_mod.panel:
            self.root.bell()
            self.set_status("面板模组：按键已锁定，不能直接编辑。")
            return
        if column == "initial" and not self._unique_states(hk):
            self.root.bell()
            self.set_status("这个快捷键没有可调选项，没有默认值可改。")
            return
        self._cancel_cell_editor()
        self._reset_capture_state()
        self.hotkey_tree.see(iid)
        self.root.update_idletasks()
        bbox = self.hotkey_tree.bbox(iid, column)
        if not bbox:
            return
        x, y, width, height = bbox
        entry = tk.Entry(
            self.hotkey_tree,
            font=("Microsoft YaHei UI", 9),
            relief="solid",
            borderwidth=1,
        )
        entry.insert(0, self._cell_edit_value(hk, column))
        entry.select_range(0, "end")
        min_width = {"name": 190, "key": 240, "initial": 260, "comment": 190}.get(column, 160)
        entry.place(x=x, y=y, width=max(width, min_width), height=height)
        self.cell_editor = entry
        self.cell_edit_context = (iid, column, hk)
        if column == "key":
            self.capture_active = True
            self.capture_source = None
            self.capture_buffer = list(hk.keys)
            self.capture_replaced = False
            self._start_gamepad_poll()
            entry.configure(background="#fff4cc")
            entry.bind("<KeyPress>", self._capture_key_press)
            entry.bind("<KeyRelease>", self._capture_key_release)
            entry.bind("<<Paste>>", lambda _e: "break")
            self.set_status(
                "按键捕获：按键盘或手柄的键/组合，松开后自动保存；Esc 取消。"
            )
        else:
            entry.bind("<Return>", lambda _e: self.finish_cell_edit(True))
            entry.bind("<Escape>", lambda _e: self.finish_cell_edit(False))
        entry.bind("<FocusOut>", lambda _e: self.finish_cell_edit(True))
        entry.focus_force()
        entry.icursor("end")

    def _reset_capture_state(self) -> None:
        self._stop_gamepad_poll()
        self.capture_active = False
        self.capture_source = None
        self.gp_held = []
        self.gp_prev = set()
        self.gp_trigger_on = {}
        self.capture_buffer = []
        self.capture_replaced = False
        self.capture_held_mods.clear()
        self.capture_session_mods.clear()
        self.capture_nonmod = False
        self.capture_down_keys.clear()
        self.capture_chord_keys = []
        self.capture_chord_mods.clear()
        self.capture_chord_complete = False
        self._cancel_capture_timer()

    def _cancel_capture_timer(self) -> None:
        if self.capture_save_after is not None:
            try:
                self.root.after_cancel(self.capture_save_after)
            except tk.TclError:
                pass
            self.capture_save_after = None

    def _stop_gamepad_poll(self) -> None:
        if self.gp_after is not None:
            try:
                self.root.after_cancel(self.gp_after)
            except tk.TclError:
                pass
            self.gp_after = None

    def _read_gamepad_tokens(self) -> set[str]:
        dll = load_xinput()
        if dll is None:
            return set()
        tokens: set[str] = set()
        for user in range(4):
            state = XINPUT_STATE()
            if dll.XInputGetState(user, ctypes.byref(state)) != 0:
                continue
            gamepad = state.Gamepad
            for mask, token in GAMEPAD_BUTTON_TOKENS.items():
                if gamepad.wButtons & mask:
                    tokens.add(token)
            for suffix, value, token in (
                ("L", gamepad.bLeftTrigger, "XB_LEFT_TRIGGER"),
                ("R", gamepad.bRightTrigger, "XB_RIGHT_TRIGGER"),
            ):
                key = (user, suffix)
                was_on = self.gp_trigger_on.get(key, False)
                # 按下用较高阈值、松开用较低阈值，避免扳机抖动。
                is_on = value > 30 if was_on else value > 55
                self.gp_trigger_on[key] = is_on
                if is_on:
                    tokens.add(token)
        return tokens

    def _start_gamepad_poll(self) -> None:
        self._stop_gamepad_poll()
        self.gp_held = []
        self.gp_trigger_on = {}
        # 记录进入捕获时已按住的键，只响应之后的按下。
        self.gp_prev = self._read_gamepad_tokens()
        self.gp_after = self.root.after(60, self._poll_gamepad)

    def _update_gamepad_buffer(self) -> None:
        if not self.gp_held:
            return
        combo = " ".join(sorted(self.gp_held))
        self.capture_buffer = [combo]
        self.capture_replaced = True
        self._capture_display()
        self.set_status(
            f"已捕获手柄：{describe_key_lines([combo])}；全部松开后自动保存。"
        )

    def _poll_gamepad(self) -> None:
        self.gp_after = None
        if not self.capture_active or self.cell_editor is None:
            return
        tokens = self._read_gamepad_tokens()
        if self.capture_source != "keyboard":
            pressed = tokens - self.gp_prev
            released = self.gp_prev - tokens
            if pressed:
                self.capture_source = "gamepad"
                self._cancel_capture_timer()
                for token in sorted(pressed):
                    if token not in self.gp_held:
                        self.gp_held.append(token)
            if self.capture_source == "gamepad":
                for token in released:
                    if token in self.gp_held:
                        self.gp_held.remove(token)
                if self.gp_held:
                    self._update_gamepad_buffer()
                elif released and self.capture_replaced:
                    self._schedule_capture_save()
        self.gp_prev = tokens
        if self.capture_active:
            self.gp_after = self.root.after(60, self._poll_gamepad)

    def _schedule_capture_save(self) -> None:
        if not self.capture_active or not self.capture_replaced:
            return
        self._cancel_capture_timer()
        self.capture_save_after = self.root.after(500, self._auto_save_capture)

    def _auto_save_capture(self) -> None:
        self.capture_save_after = None
        if self.capture_active and self.capture_replaced and self.cell_editor is not None:
            self.finish_cell_edit(True)

    @staticmethod
    def _capture_modifier(keysym: str) -> Optional[str]:
        if keysym in ("Control_L", "Control_R"):
            return "ctrl"
        if keysym in ("Shift_L", "Shift_R"):
            return "shift"
        if keysym in ("Alt_L", "Alt_R"):
            return "alt"
        if keysym in ("Super_L", "Super_R", "Meta_L", "Meta_R"):
            return "win"
        return None

    @staticmethod
    def _format_capture_combo(mods: set[str], key: Optional[str]) -> str:
        if not mods:
            # 没有任何修饰键时用 no_modifiers 简写。
            return " ".join(part for part in ("no_modifiers", key) if part)
        parts = [name for name in ("ctrl", "shift", "alt", "win") if name in mods]
        # 未按下的 Ctrl/Shift/Alt 自动补 no_*，避免组合键被其他修饰键触发。
        for name, negative in (
            ("ctrl", "no_ctrl"),
            ("shift", "no_shift"),
            ("alt", "no_alt"),
        ):
            if name not in mods:
                parts.append(negative)
        if key:
            parts.append(key)
        return " ".join(parts)

    def _capture_display(self) -> None:
        entry = self.cell_editor
        if entry is None:
            return
        entry.delete(0, "end")
        entry.insert(0, " | ".join(self.capture_buffer))
        entry.icursor("end")

    def _update_capture_chord(self) -> None:
        if self.capture_chord_keys:
            mods = set(self.capture_chord_mods)
            key_text: Optional[str] = " ".join(self.capture_chord_keys)
        elif self.capture_session_mods:
            mods = set(self.capture_session_mods)
            key_text = None
        else:
            return
        combo = self._format_capture_combo(mods, key_text)
        if not combo:
            return
        self.capture_buffer = [combo]
        self.capture_replaced = True
        self._capture_display()

    def _capture_key_press(self, event: tk.Event) -> str:
        if not self.capture_active or self.cell_editor is None:
            return "break"
        keysym = event.keysym
        if keysym == "Return":
            self.finish_cell_edit(True)
            return "break"
        if keysym == "Escape":
            self.finish_cell_edit(False)
            return "break"
        if self.capture_source == "gamepad":
            # 本次捕获已由手柄接管，忽略键盘。
            return "break"
        if self.capture_source is None:
            self.capture_source = "keyboard"
            self._stop_gamepad_poll()
        self._cancel_capture_timer()
        if self.capture_chord_complete:
            # 上一组键已全部松开；新按键开始一组新的同时按键。
            self.capture_chord_keys = []
            self.capture_chord_mods = set()
            self.capture_session_mods = set()
            self.capture_held_mods = set()
            self.capture_nonmod = False
            self.capture_chord_complete = False
        modifier = self._capture_modifier(keysym)
        if modifier:
            if not self.capture_held_mods:
                self.capture_session_mods = set()
                self.capture_nonmod = False
            self.capture_held_mods.add(modifier)
            self.capture_session_mods.add(modifier)
            if self.capture_chord_keys:
                self.capture_chord_mods.add(modifier)
                self._update_capture_chord()
            return "break"
        if keysym in self.capture_down_keys:
            return "break"
        token = keycode_to_3dmigoto(
            getattr(event, "keycode", 0),
            keysym,
            getattr(event, "char", ""),
        )
        if not token:
            self.set_status("无法识别该按键，请换一个。")
            return "break"
        self.capture_down_keys.add(keysym)
        if token not in self.capture_chord_keys:
            self.capture_chord_keys.append(token)
        self.capture_chord_mods.update(self.capture_held_mods)
        self.capture_nonmod = True
        self._update_capture_chord()
        combo = self.capture_buffer[-1] if self.capture_buffer else ""
        self.set_status(f"已捕获：{combo}；全部松开后自动保存。")
        return "break"

    def _capture_key_release(self, event: tk.Event) -> str:
        if not self.capture_active or self.capture_source == "gamepad":
            return "break"
        keysym = event.keysym
        modifier = self._capture_modifier(keysym)
        if modifier:
            self.capture_held_mods.discard(modifier)
            if not self.capture_held_mods and not self.capture_down_keys:
                self._update_capture_chord()
                self.capture_chord_complete = True
                self._schedule_capture_save()
            return "break"
        self.capture_down_keys.discard(keysym)
        if not self.capture_down_keys:
            self._update_capture_chord()
            self._schedule_capture_save()
            if not self.capture_held_mods:
                self.capture_chord_complete = True
        return "break"

    def _cancel_cell_editor(self) -> None:
        entry = self.cell_editor
        self.cell_editor = None
        self.cell_edit_context = None
        self._reset_capture_state()
        if entry is not None:
            try:
                entry.destroy()
            except tk.TclError:
                pass

    def finish_cell_edit(self, commit: bool) -> None:
        entry = self.cell_editor
        context = self.cell_edit_context
        if entry is None or context is None:
            return
        capturing = self.capture_active and context[1] == "key"
        capture_new = bool(self.capture_replaced)
        if capturing:
            text = self.capture_buffer[0] if capture_new and self.capture_buffer else entry.get()
        else:
            text = entry.get()
        self.cell_editor = None
        self.cell_edit_context = None
        self._reset_capture_state()
        try:
            entry.destroy()
        except tk.TclError:
            pass
        self.hotkey_tree.focus_set()
        if not commit:
            self.set_status("已取消编辑")
            return
        if capturing and not capture_new:
            # 没有按新键：保留原有 key 行（包括模组自带的多行），不自动追加。
            self.set_status("未修改")
            return
        _iid, column, hk = context
        before = None
        try:
            before = hk.doc.path.read_bytes()
        except OSError:
            pass
        try:
            changed, message = self._apply_cell_edit(hk, column, text)
        except DefaultValueError as exc:
            self.root.bell()
            self.set_status(f"未保存：{exc}")
            messagebox.showwarning("默认值不在可选值内", str(exc), parent=self.root)
            return
        except HotkeyConflictError as exc:
            self.root.bell()
            self.set_status(f"未保存：{str(exc).splitlines()[0]}")
            messagebox.showwarning("快捷键冲突", str(exc), parent=self.root)
            return
        except (OSError, ValueError) as exc:
            self.root.bell()
            self.set_status(f"未保存：{exc}")
            return
        if changed:
            if before is not None:
                self.register_undo(hk.doc.path, before, f"{column} 修改")
            self.refresh(manual=False)
        self.set_status(message)

    def _apply_cell_edit(self, hk: Hotkey, column: str, text: str) -> tuple[bool, str]:
        mod = self.current_mod
        if column == "name":
            raise ValueError("段名固定，不可修改；请使用“识别名”。")

        if column == "key":
            if mod is not None and mod.panel:
                raise ValueError("面板模组的按键已锁定。")
            key_text = text.strip()
            if not key_text:
                raise ValueError("快捷键不能为空。")
            if "|" in key_text:
                raise ValueError("快捷键只能写入一条 key 行，不支持用 | 添加备用键。")
            keys = [key_text]
            if keys == hk.keys:
                return False, "未修改"
            if mod is not None:
                conflict = find_key_conflict(mod.hotkeys, hk, key_text)
                if conflict is not None:
                    other, existing = conflict
                    raise HotkeyConflictError(
                        f"新快捷键“{describe_key_line(key_text)}”与 "
                        f"{hotkey_label(other)} 的“{describe_key_line(existing)}”冲突。\n"
                        "该按键未保存，请换一个组合。"
                    )
            apply_hotkey_edit(
                hk.doc.path,
                hk.section.name,
                hk.section.name,
                hk.section.comment,
                keys,
                mod_root=mod.path if mod is not None else None,
            )
            shares = (
                count_key_shares(mod.hotkeys, hk, key_text)
                if mod is not None
                else 0
            )
            note = (
                f"（与 {shares} 个同条件快捷键共用，会同时触发）"
                if shares
                else ""
            )
            return True, f"已保存快捷键：{key_text}{note}"

        if column == "comment":
            new_comment = text.replace("\r", " ").replace("\n", " ").strip()
            if new_comment == hk.section.comment:
                return False, "未修改"
            apply_hotkey_edit(
                hk.doc.path,
                hk.section.name,
                hk.section.name,
                new_comment,
                hk.keys,
                mod_root=mod.path if mod is not None else None,
            )
            return True, f"已保存识别名：{new_comment or '（空）'}"

        if column == "initial":
            states = self._unique_states(hk)
            if not states:
                raise ValueError("这个快捷键没有可调选项。")
            by_name = {state.name.lower(): state for state in states}
            changes: dict[str, tuple[str, bool]] = {}
            if len(states) == 1:
                value = text.strip()
                if not value:
                    raise ValueError("默认值不能为空。")
                changes[states[0].name] = (value, states[0].persist)
            else:
                for part in text.split(";"):
                    part = part.strip()
                    if not part:
                        continue
                    if "=" not in part:
                        raise ValueError("多个选项的格式：选项=默认值；选项=默认值")
                    name, value = part.split("=", 1)
                    name = name.strip().lstrip("$")
                    value = value.strip()
                    state = by_name.get(name.lower())
                    if state is None:
                        raise ValueError(f"未知选项：{name}")
                    if not value:
                        raise ValueError(f"${name} 的默认值不能为空。")
                    changes[state.name] = (value, state.persist)
                if not changes:
                    raise ValueError("没有可保存的默认值。")
            for state in states:
                if state.name not in changes:
                    continue
                value = changes[state.name][0]
                problem = validate_default_value(hk.type, state.options, value)
                if problem:
                    raise DefaultValueError(f"${state.name}：{problem}")
            changed = apply_initial_values(
                hk.doc.path,
                changes,
                mod_root=mod.path if mod is not None else None,
            )
            if not changed:
                return False, "未修改"
            return True, f"已保存默认值（{changed} 个选项）"

        return False, "该列不可编辑"

    def set_current_as_default(self) -> None:
        self.refresh(manual=False)
        mod = self.current_mod
        if mod is None:
            messagebox.showinfo("当前值设为默认", "请先选择一个模组。", parent=self.root)
            return
        changes_by_file: dict[Path, dict[str, tuple[str, bool]]] = {}
        skipped = 0
        invalid: list[str] = []
        for hk in mod.hotkeys:
            for state in hk.states:
                if state.value is None:
                    skipped += 1
                    continue
                problem = validate_default_value(hk.type, state.options, str(state.value))
                if problem:
                    invalid.append(f"${state.name}：{problem}")
                    continue
                changes_by_file.setdefault(hk.doc.path, {})[state.name] = (
                    str(state.value),
                    bool(state.persist),
                )
        if not changes_by_file:
            if invalid:
                messagebox.showwarning(
                    "默认值不在可选值内",
                    "以下当前值不在可选值内，未保存：\n" + "\n".join(invalid[:8]),
                    parent=self.root,
                )
            else:
                messagebox.showinfo(
                    "当前值设为默认",
                    "当前没有可保存的“游戏当前值”。\n"
                    "请先在游戏里调好状态，按 F10 或退出游戏，再刷新工具。",
                    parent=self.root,
                )
            return
        if not messagebox.askyesno(
            "当前值设为默认",
            "把现在的“游戏当前值”保存为启动默认值？\n\n"
            "以后启动游戏时，如果 3DMigoto 没有记住状态，就会用这些默认值。\n"
            "中文路径导致状态丢失时也能用。\n\n"
            "请先完全退出游戏；工具会先创建原档备份。继续？",
            parent=self.root,
        ):
            return

        written = 0
        errors: list[str] = []
        for path, changes in changes_by_file.items():
            try:
                before = path.read_bytes() if path.is_file() else None
                count = apply_initial_values(path, changes, mod_root=mod.path)
                written += count
                if count and before is not None:
                    self.register_undo(path, before, "当前值设为默认")
            except (OSError, ValueError) as exc:
                errors.append(f"{path.name}: {exc}")

        self.refresh(manual=False)
        summary = [f"已把 {written} 个当前值保存为默认值。"]
        if skipped:
            summary.append(f"跳过没有当前值的选项：{skipped} 个。")
        if invalid:
            summary.append(
                "以下当前值不在可选值内，已跳过：\n" + "\n".join(invalid[:8])
            )
        if errors:
            summary.append("错误：\n" + "\n".join(errors[:5]))
        if invalid:
            messagebox.showwarning("当前值设为默认", "\n".join(summary), parent=self.root)
        else:
            messagebox.showinfo("当前值设为默认", "\n".join(summary), parent=self.root)

    def _collect_reset_changes(self, hotkeys: list[Hotkey]) -> tuple[dict[str, str], int]:
        changes: dict[str, str] = {}
        skipped = 0
        for hk in hotkeys:
            for state in hk.states:
                resettable = state.lookup is not None and (state.persist or state.source == "saved")
                if resettable:
                    changes[state.lookup] = state.initial if state.initial is not None else "0"
                else:
                    skipped += 1
        return changes, skipped

    def reset_states(self, all_keys: bool) -> None:
        mod = self.current_mod
        if mod is None:
            return
        if all_keys:
            hotkeys = mod.hotkeys
            what = f"模组“{mod.name}”的全部快捷键"
        else:
            if self.current_hk is None:
                return
            hotkeys = [self.current_hk]
            what = f"快捷键 [{self.current_hk.section.name}]"
        changes, skipped = self._collect_reset_changes(hotkeys)
        if not changes:
            messagebox.showinfo(
                "没有可恢复的默认值",
                f"{what} 没有可恢复的默认值。\n"
                f"不会保存的选项：{skipped} 个。",
                parent=self.root,
            )
            return
        if self.d3dx is None or not self.d3dx.available:
            messagebox.showerror(
                "未找到 d3dx_user.ini",
                "无法恢复默认值。请先设置正确的 ZZMI 根目录，并至少运行一次游戏生成 d3dx_user.ini。",
                parent=self.root,
            )
            return
        if not messagebox.askyesno(
            "恢复默认值",
            f"把 {what} 的 {len(changes)} 个选项恢复为默认值？\n"
            f"写入：{self.d3dx.path}\n\n"
            "请先完全退出游戏。游戏运行中修改可能在退出时被覆盖。\n\n继续？",
            parent=self.root,
        ):
            return
        try:
            updated, added = self.d3dx.set_values(changes)
        except (OSError, ValueError) as exc:
            messagebox.showerror("写入失败", str(exc), parent=self.root)
            return
        self.refresh(manual=False)
        messagebox.showinfo(
            "恢复完成",
            f"已恢复 {updated} 项，新增 {added} 项。\n"
            f"{('跳过不会保存的选项 ' + str(skipped) + ' 个。') if skipped else ''}",
            parent=self.root,
        )

    # -- 状态 --------------------------------------------------------------

    def snapshots_for_mod(self, mod: ModInfo) -> list[dict]:
        return load_mod_snapshots(mod.path)

    def save_snapshot(self) -> None:
        mod = self.current_mod
        if mod is None:
            return
        # 记忆前先读取一次，保证状态里是当前 ini / d3dx_user.ini 的参数。
        self.refresh(manual=False)
        mod = self.current_mod
        if mod is None:
            return
        default_label = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        label = simpledialog.askstring(
            "保存当前状态",
            "会保存当前 mod 的这一套快捷键设置：\n"
            "- 每个快捷键的按键\n"
            "- 识别名\n"
            "- 默认值\n"
            "- 游戏当前值（游戏会记住的选项）\n\n"
            "不会保存贴图、模型等其他文件。\n"
            "保存到本 mod 的“快捷键管理\\快捷键状态.json”。\n"
            "以后可在“选择已有状态”里选回来。\n\n"
            "给这套设置起个名字（可留空）：",
            initialvalue=default_label,
            parent=self.root,
        )
        if label is None:
            return
        label = label.strip() or default_label
        items: list[dict] = []
        try:
            for hk in mod.hotkeys:
                rel_file = os.path.relpath(hk.doc.path, mod.path)
                vars_data = []
                for state in hk.states:
                    if state.source in ("saved", "default") and state.value is not None:
                        value = state.value
                    else:
                        value = None
                    const_info = hk.doc.constants.get(state.name.lower())
                    vars_data.append(
                        {
                            "name": state.name,
                            "value": value,
                            "initial": state.initial,
                            "options": state.options,
                            "initial_declared": bool(
                                const_info is not None and const_info.initial is not None
                            ),
                            "persist": bool(state.persist),
                            "restorable": bool(state.persist or state.source == "saved"),
                        }
                    )
                items.append(
                    {
                        "file_rel_mod": rel_file,
                        "ordinal": hk.ordinal,
                        "name": hk.section.name,
                        "comment": hk.section.comment,
                        "keys": hk.keys,
                        "type": hk.type,
                        "condition": hk.condition,
                        "vars": vars_data,
                    }
                )
        except ValueError as exc:
            messagebox.showerror("保存当前状态失败", str(exc), parent=self.root)
            return
        snapshot = {
            "id": uuid.uuid4().hex[:12],
            "created": default_label,
            "label": label,
            "mod_key": normalized_mod_key(self.game_root, mod.path),
            "mod_name": mod.name,
            "mod_dir_name": mod.path.name,
            "panel": bool(mod.panel),
            "key_count": len(items),
            "hotkeys": items,
        }
        snapshots = load_mod_snapshots(mod.path)
        snapshots.append(snapshot)
        try:
            save_mod_snapshots(mod.path, snapshots)
        except OSError as exc:
            messagebox.showerror("保存当前状态失败", str(exc), parent=self.root)
            return
        self._update_action_states()
        self.set_status(
            f"已把当前设置保存为“{label}”（{len(items)} 个快捷键，"
            f"当前共 {len(snapshots)} 个保存的状态，文件：{SNAPSHOT_FILE_NAME}）"
        )


    def restore_latest(self) -> None:
        mod = self.current_mod
        if mod is None:
            return
        snapshots = self.snapshots_for_mod(mod)
        if not snapshots:
            messagebox.showinfo("选择已有状态", "当前模组还没有保存过状态。", parent=self.root)
            return
        self.restore_snapshot(snapshots[-1])

    def delete_snapshot(self, snapshot_id: str) -> None:
        mod = self.current_mod
        if mod is None:
            return
        snapshots = [
            snap
            for snap in load_mod_snapshots(mod.path)
            if snap.get("id") != snapshot_id
        ]
        try:
            save_mod_snapshots(mod.path, snapshots)
        except OSError:
            pass
        else:
            self._update_action_states()

    def open_restore_snapshot(self) -> None:
        mod = self.current_mod
        if mod is None:
            messagebox.showinfo("选择已有状态", "请先选择一个模组。", parent=self.root)
            return
        if not self.snapshots_for_mod(mod):
            messagebox.showinfo("选择已有状态", "当前模组还没有保存过状态。", parent=self.root)
            return
        SnapshotManagerDialog(self)

    def _resolve_snapshot_file(self, mod: ModInfo, rel_mod: str) -> Optional[Path]:
        candidate = mod.path / rel_mod
        if candidate.is_file():
            return candidate
        name = Path(rel_mod).name
        try:
            matches = [
                p
                for p in mod.path.rglob(name)
                if p.is_file() and is_mod_ini(p)
            ]
        except OSError:
            matches = []
        if matches:
            return matches[0]
        return None

    def restore_snapshot(self, snapshot: dict) -> None:
        mod = self.current_mod
        if mod is None:
            return
        panel_locked = bool(snapshot.get("panel") or mod.panel)
        hotkeys_data = snapshot.get("hotkeys", [])
        if not isinstance(hotkeys_data, list):
            messagebox.showerror("恢复失败", "状态数据格式无效。", parent=self.root)
            return
        if not messagebox.askyesno(
            "恢复状态",
            f"把游戏改回这套设置“{snapshot.get('label', '')}”？\n\n"
            + (
                "这个 mod 有快捷键面板：只恢复识别名和设置值，不改按键。\n"
                if panel_locked
                else "会恢复按键、识别名和设置值；内部名不变。\n"
            )
            + "请先完全退出游戏；工具会先准备原档备份。继续？",
            parent=self.root,
        ):
            return

        resolved: list[tuple[dict, Optional[Path]]] = []
        missing = 0
        for item in hotkeys_data:
            if not isinstance(item, dict):
                missing += 1
                continue
            rel_mod = str(item.get("file_rel_mod", ""))
            path = self._resolve_snapshot_file(mod, rel_mod) if rel_mod else None
            if path is None:
                missing += 1
            resolved.append((item, path))

        restored = 0
        skipped = 0
        errors: list[str] = []
        grouped: dict[Path, list[dict]] = {}
        for item, path in resolved:
            if path is not None:
                grouped.setdefault(path, []).append(item)
        for path, items in grouped.items():
            try:
                doc = IniDoc.load(path, mod_root=mod.path)
                if doc.lossy:
                    raise ValueError("编码无法安全识别")
                hotkeys = parse_hotkeys(doc)
                used_starts: set[int] = set()
                targets: list[tuple[Hotkey, dict]] = []
                for item in items:
                    snap_name = str(item.get("name", ""))
                    snap_type = str(item.get("type", ""))
                    snap_vars_raw = item.get("vars", [])
                    if not isinstance(snap_vars_raw, list):
                        snap_vars_raw = []
                    snap_vars = {
                        str(v.get("name", "")).lower()
                        for v in snap_vars_raw
                        if isinstance(v, dict) and v.get("name")
                    }
                    target = next((h for h in hotkeys if h.section.name == snap_name), None)
                    if target is None:
                        target = next(
                            (
                                h
                                for h in hotkeys
                                if h.ordinal == int(item.get("ordinal", -1))
                                and (not snap_type or h.type == snap_type)
                                and (
                                    not snap_vars
                                    or {v.name.lower() for v in h.variables} == snap_vars
                                )
                            ),
                            None,
                        )
                    if target is None or target.section.start in used_starts:
                        skipped += 1
                        continue
                    used_starts.add(target.section.start)
                    targets.append((target, item))
                changed = False
                for target, item in sorted(
                    targets, key=lambda pair: pair[0].section.start, reverse=True
                ):
                    new_comment = str(item.get("comment", ""))
                    if panel_locked:
                        # 面板模组只恢复识别名，按键与段名保持原样。
                        if new_comment == target.section.comment:
                            continue
                        # ini 的识别名统一用分号注释；# 不适用。
                        header = f"{target.section.indent}[{target.section.name}]"
                        if new_comment.strip():
                            header += f" ; {new_comment.strip()}"
                        ending = line_ending(doc.lines[target.section.start]) or doc.newline
                        new_line = header + ending
                        if new_line != doc.lines[target.section.start]:
                            doc.lines[target.section.start] = new_line
                            changed = True
                            restored += 1
                        continue
                    keys = [str(k).strip() for k in item.get("keys", []) if str(k).strip()]
                    if not keys:
                        skipped += 1
                        continue
                    # 段名固定，只用当前段名替换按键/识别名。
                    block = build_replacement_block(
                        doc,
                        target,
                        target.section.name,
                        new_comment,
                        keys,
                    )
                    old_block = doc.lines[target.section.start : target.section.end]
                    if block != old_block:
                        doc.lines[target.section.start : target.section.end] = block
                        changed = True
                        restored += 1
                if changed:
                    doc.save()
            except (OSError, ValueError) as exc:
                errors.append(f"{path.name}: {exc}")

        initial_changes_by_file: dict[Path, dict[str, tuple[str, bool]]] = {}
        initial_invalid = 0
        state_changes: dict[str, str] = {}
        state_skipped = 0
        for item, path in resolved:
            if path is None:
                continue
            vars_list = item.get("vars", [])
            if not isinstance(vars_list, list):
                continue
            for var in vars_list:
                if not isinstance(var, dict):
                    continue
                name = str(var.get("name", "")).strip()
                if var.get("initial_declared") and name and var.get("initial") is not None:
                    initial_value = str(var.get("initial"))
                    problem = validate_default_value(
                        str(item.get("type", "")),
                        str(var.get("options", "")),
                        initial_value,
                    )
                    if problem:
                        initial_invalid += 1
                    else:
                        initial_changes_by_file.setdefault(path, {})[name.lower()] = (
                            initial_value,
                            bool(var.get("persist")),
                        )
                if not var.get("restorable") or var.get("value") is None:
                    state_skipped += 1
                    continue
                lookup = make_lookup_key(self.game_root, path, name)
                if lookup is None:
                    state_skipped += 1
                    continue
                state_changes[lookup] = str(var.get("value"))

        initial_updated = 0
        for path, changes in initial_changes_by_file.items():
            try:
                initial_updated += apply_initial_values(path, changes, mod_root=mod.path)
            except (OSError, ValueError) as exc:
                errors.append(f"{path.name} 默认值: {exc}")

        updated = added = 0
        if state_changes:
            if self.d3dx is not None and self.d3dx.available:
                try:
                    updated, added = self.d3dx.set_values(state_changes)
                except (OSError, ValueError) as exc:
                    errors.append(f"d3dx_user.ini: {exc}")
            else:
                state_skipped += len(state_changes)

        self.refresh(manual=False)
        summary = [
            f"恢复按键/识别名：{restored} 项",
            f"默认值：更新 {initial_updated} 项",
            f"当前记忆：修改 {updated} 项，新增 {added} 项",
        ]
        if skipped:
            summary.append(f"跳过快捷键：{skipped} 项")
        if missing:
            summary.append(f"找不到文件：{missing} 项")
        if state_skipped:
            summary.append(f"跳过状态：{state_skipped} 项")
        if initial_invalid:
            summary.append(f"跳过不在可选值内的默认值：{initial_invalid} 项")
        if panel_locked:
            summary.append("注意：模组含面板，按键未恢复；段名始终不变。")
        if errors:
            summary.append("错误：\n" + "\n".join(errors[:5]))
        messagebox.showinfo("恢复结果", "\n".join(summary), parent=self.root)

    def open_mod_folder(self) -> None:
        mod = self.current_mod
        if mod is None:
            messagebox.showinfo("打开模组文件夹", "请先选择一个模组。", parent=self.root)
            return
        folder = mod.path
        try:
            os.startfile(str(folder))  # type: ignore[attr-defined]
            self.set_status(f"已打开模组文件夹：{folder}")
        except AttributeError:
            messagebox.showinfo("模组文件夹", str(folder), parent=self.root)
        except OSError as exc:
            messagebox.showerror("打开失败", f"{folder}\n{exc}", parent=self.root)

    def open_selected_ini(self) -> None:
        hk = self.current_hk
        if hk is None:
            return
        try:
            os.startfile(str(hk.doc.path))  # type: ignore[attr-defined]
        except AttributeError:
            messagebox.showinfo("打开文件", str(hk.doc.path), parent=self.root)
        except OSError as exc:
            messagebox.showerror("打开失败", str(exc), parent=self.root)


# ---------------------------------------------------------------------------
# 命令行扫描（调试/导出）
# ---------------------------------------------------------------------------


def scan_json(mod_root: Path, game_root: Optional[Path]) -> dict:
    d3dx_path = game_root / "d3dx_user.ini" if game_root else None
    d3dx = D3dxUser(d3dx_path) if d3dx_path else None
    mods = []
    for path in discover_mod_paths(mod_root):
        mod = analyze_mod(path, game_root, d3dx)
        mods.append(
            {
                "name": mod.name,
                "path": str(mod.path),
                "enabled": mod.enabled,
                "panel": mod.panel,
                "panel_reasons": mod.panel_reasons,
                "errors": mod.errors,
                "hotkeys": [
                    {
                        "name": hk.section.name,
                        "keys": hk.keys,
                        "key_description": describe_key_lines(hk.keys),
                        "type": hk.type,
                        "condition": hk.condition,
                        "runs": hk.runs,
                        "file": str(hk.doc.path),
                        "comment": hk.section.comment,
                        "states": [
                            {
                                "name": state.name,
                                "current": state.value,
                                "initial": state.initial,
                                "options": state.options,
                                "persist": state.persist,
                                "source": state.source,
                                "lookup": state.lookup,
                            }
                            for state in hk.states
                        ],
                    }
                    for hk in mod.hotkeys
                ],
            }
        )
    return {
        "mod_root": str(mod_root),
        "game_root": str(game_root) if game_root else None,
        "d3dx_user": str(d3dx_path) if d3dx_path else None,
        "d3dx_loaded": bool(d3dx and d3dx.available),
        "mods": mods,
    }


def _attach_parent_console() -> bool:
    """无控制台打包后，命令行模式尝试附着到启动它的控制台。"""
    if os.name != "nt":
        return False
    try:
        import ctypes

        if not ctypes.windll.kernel32.AttachConsole(-1):
            return False
        sys.stdout = open("CONOUT$", "w", encoding="utf-8", errors="replace", buffering=1)
        sys.stderr = open("CONOUT$", "w", encoding="utf-8", errors="replace", buffering=1)
    except Exception:  # noqa: BLE001
        return False
    return True


def main() -> int:
    # 打包为无窗口程序（--noconsole）时没有标准输出，先补空流避免报错。
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")

    parser = argparse.ArgumentParser(description="mod快捷键管理工具")
    parser.add_argument(
        "--scan",
        nargs="?",
        const="",
        default=None,
        metavar="模组目录",
        help="只扫描并输出 JSON（不启动界面）",
    )
    parser.add_argument("--game-root", default="", help="手动指定 ZZMI 根目录")
    parser.add_argument("mod_root", nargs="?", default="", help="启动时打开的模组目录")
    parser.add_argument("--smoke", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()

    if args.scan is not None:
        if getattr(sys, "frozen", False):
            _attach_parent_console()
        if hasattr(sys.stdout, "reconfigure"):
            try:
                sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            except OSError:
                pass
        if not args.scan:
            print("请指定要扫描的模组目录。", file=sys.stderr)
            return 2
        mod_root = Path(args.scan).resolve()
        game_root = Path(args.game_root).resolve() if args.game_root else find_game_root(mod_root)
        if not mod_root.is_dir():
            print(f"目录不存在：{mod_root}", file=sys.stderr)
            return 2
        try:
            data = scan_json(mod_root, game_root)
        except Exception as exc:  # noqa: BLE001
            print(f"扫描失败：{exc}", file=sys.stderr)
            return 1
        print(json.dumps(data, ensure_ascii=False, indent=JSON_INDENT))
        return 0

    root = tk.Tk()
    app = HotkeyApp(root)
    if args.mod_root:
        app.mod_root_var.set(str(Path(args.mod_root).resolve()))
    if args.game_root:
        app.game_root_var.set(str(Path(args.game_root).resolve()))
    if args.smoke:
        root.after(1200, root.destroy)
    root.mainloop()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:  # noqa: BLE001
        # 无控制台打包后，启动异常要用弹窗显示，否则无提示。
        import traceback

        detail = traceback.format_exc()
        sys.stderr.write(detail)
        try:
            messagebox.showerror(APP_TITLE, f"程序启动失败：\n{detail[-2000:]}")
        except Exception:  # noqa: BLE001
            pass
        raise
