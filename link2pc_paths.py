# -*- coding: utf-8 -*-
"""
目录放哪儿
==========
配置、历史、默认收件箱的位置，三个平台不一样：

    Windows   %APPDATA%\\LanSplice                    （配置与历史同处一目录）
    macOS     ~/Library/Application Support/LanSplice
    Linux     ~/.config/LanSplice（配置） + ~/.local/share/LanSplice（历史）

**Windows 这一支必须和以前一模一样。** 老用户升级时配置、配对码、
传输历史全靠这条路径找回来；为了「更规范」把它挪走，等于让人重配一次，
历史也凭空消失。

Linux 为什么拆成两个：按 XDG 规范，配置是用户会去改的文件（config.json），
数据是程序自己堆的（history.jsonl、分片）。信创机器上做「备份用户配置」的
运维脚本默认只抄 ~/.config，放对了才被抄到。另外这两个变量都可能被环境
覆盖（比如 root 用 sudo 跑时 HOME 会变），所以先认 XDG_CONFIG_HOME /
XDG_DATA_HOME，且只接受绝对路径 —— 相对路径按规范应当忽略。
"""

import os
import sys

APP = "LanSplice"


def os_kind():
    """windows / macos / linux —— 只分这三类，够用。"""
    if sys.platform.startswith("win"):
        return "windows"
    if sys.platform == "darwin":
        return "macos"
    return "linux"


def _env_abs(var, fallback):
    """取环境变量里的目录；空值或相对路径都按「没设」处理。"""
    v = (os.environ.get(var) or "").strip()
    if v and os.path.isabs(v):
        return v
    return fallback


def _home():
    return os.path.expanduser("~") or "."


def config_dir():
    """config.json 所在目录。"""
    k = os_kind()
    if k == "windows":
        # 与 v1.6.x 完全一致，勿改
        return os.path.join(os.environ.get("APPDATA") or _home(), APP)
    if k == "macos":
        return os.path.join(_home(), "Library", "Application Support", APP)
    return os.path.join(_env_abs("XDG_CONFIG_HOME",
                                 os.path.join(_home(), ".config")), APP)


def data_dir():
    """history.jsonl、分片、收件箱这类程序数据。"""
    k = os_kind()
    if k == "windows":
        return os.path.join(os.environ.get("APPDATA") or _home(), APP)
    if k == "macos":
        return os.path.join(_home(), "Library", "Application Support", APP)
    return os.path.join(_env_abs("XDG_DATA_HOME",
                                 os.path.join(_home(), ".local", "share")), APP)


def inbox_dir():
    """资源管理器右键投递用的中转目录（Windows 专用，其他平台也给它一个位置）。"""
    return os.path.join(data_dir(), "inbox")


def config_file():
    return os.path.join(config_dir(), "config.json")


def default_recv_root():
    """
    没有配置过接收目录时的默认值。

    放「下载」下面而不是家目录根：家目录根上凭空多一个文件夹最招人烦，
    而接收的东西本来就是「下载」的一种。中文系统可能叫「下载」而不是
    Downloads，两个都试。
    """
    home = _home()
    for name in ("Downloads", "下载"):
        p = os.path.join(home, name)
        if os.path.isdir(p):
            return os.path.join(p, APP)
    return os.path.join(home, APP)


def ensure(d):
    """建目录，失败不抛 —— 调用方拿到路径后自己会再校验。"""
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    return d
