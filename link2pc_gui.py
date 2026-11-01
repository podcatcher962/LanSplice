# -*- coding: utf-8 -*-
"""
LanSplice 图形界面
================
双机局域网直传 · 加密通道 · 不依赖 Windows 共享
"""

import os
import sys
import json
import time
import socket
import queue
import base64
import threading
import subprocess

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    HAS_DND = True
except Exception:
    TkinterDnD = None
    DND_FILES = None
    HAS_DND = False

import link2pc_core as L
import link2pc_history as HIST
import link2pc_i18n as I18N
import link2pc_platform as P          # v1.7.1：系统差异全收在那一层
from link2pc_i18n import t as _t

# 内网聊天（v1.7.3）：没有服务器，每台都是节点
try:
    import link2pc_chat as CHAT
    import link2pc_chatwin as CHATWIN
    HAS_CHAT = True
except Exception:
    CHAT = None
    CHATWIN = None
    HAS_CHAT = False

try:
    import link2pc_tray as TRAY
    HAS_TRAY = True
except Exception:
    TRAY = None
    HAS_TRAY = False

try:
    import link2pc_web as WEB
    HAS_WEB = True
except Exception:
    WEB = None
    HAS_WEB = False

APP_NAME = "LanSplice"
APP_TITLE = "LanSplice · 双机直传"
APP_VER = L.APP_VER          # 唯一来源在 core，别在这里再写死一份
COPYRIGHT = "© 永远的兰兰"

# ---------------------------------------------------------------- 单实例

# 命名互斥量：同一台机器、同一个登录会话里只允许一个图形界面。
# 用 Local\ 而不是 Global\ —— 两个 Windows 用户各开一个互不干扰。
# Linux 上这个名字会被转成 /tmp/lansplice-Local_LanSplice-SingleInstance.lock
MUTEX_NAME = "Local\\LanSplice-SingleInstance"


def single_instance_acquire(name=MUTEX_NAME):
    """
    抢单实例锁。第一个进场的返回 True，后来者返回 False。

    具体怎么做（命名互斥量还是 flock）交给 platform 层：
    Windows 用 CreateMutexW，Linux/macOS 用 fcntl.flock —— 后者是内核锁，
    进程一死自动释放，不会留下「上次没退干净」的死锁文件。

    失败时一律放行（返回 True）：拿不到锁总比打不开程序强。
    """
    return P.single_instance(name)


def _tk_windows():
    """
    枚举本程序已经开着的窗口。

    Windows 上返回 [(hwnd, 是否可见)]；其他系统这个 API 不存在，
    返回空列表 —— 调用方 focus_existing() 会据此走「提示已经在跑」的分支。
    """
    if not P.IS_WIN:
        return []
    try:
        import ctypes
        from ctypes import wintypes
        u = ctypes.windll.user32
        out = []
        EnumProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND,
                                      wintypes.LPARAM)

        def _cb(hwnd, _lp):
            try:
                cb = ctypes.create_unicode_buffer(256)
                if not u.GetClassNameW(hwnd, cb, 256):
                    return True
                if cb.value != "TkTopLevel":
                    return True
                n = u.GetWindowTextLengthW(hwnd)
                if n <= 0:
                    return True
                tb = ctypes.create_unicode_buffer(n + 1)
                u.GetWindowTextW(hwnd, tb, n + 1)
                if tb.value.startswith(APP_NAME):
                    out.append((hwnd, bool(u.IsWindowVisible(hwnd))))
            except Exception:
                pass
            return True

        u.EnumWindows(EnumProc(_cb), 0)
        return out
    except Exception:
        return []


def focus_existing():
    """
    把已经在跑的那个窗口提到前面。

    Windows：缩到托盘时窗口是 withdraw 状态（不可见但仍存在），
    所以优先挑可见的；一个可见的都没有，就把那个隐藏的 show 出来。
    Linux：靠 wmctrl / xdotool，没装就返回 False（不报错）。
    """
    return P.focus_existing()


# ---------------------------------------------------------------- 配色

C_BG = "#eceff1"          # 窗口底色
C_PANEL = "#dfe3e6"       # 侧栏 / 顶栏
C_CARD = "#f4f6f7"        # 卡片
C_LINE = "#c7cfd4"        # 分隔线
C_TEXT = "#1f2a30"        # 主文字
C_SUB = "#5f7079"         # 次要文字
C_BLUE = "#1976d2"
C_GREEN = "#2e7d32"
C_PURPLE = "#6a1b9a"
C_RED = "#c62828"
C_GRAY = "#90a4ae"
C_WHITE = "#ffffff"

FONT = "Microsoft YaHei UI"       # 实际值在启动时由 pick_font() 重新选定

# ---------------------------------------------------------------- 剪贴板里的文件


def clipboard_file_paths():
    """
    取剪贴板里被复制的**文件/文件夹**路径。

    Windows 走 CF_HDROP（资源管理器「复制」时放的就是这个格式）；
    其他系统暂时返回空 —— 调用方会把它当作「复制的是普通文字」，
    只是不做那个接管粘贴的花活，不影响别的功能。
    """
    return P.clipboard_file_paths()


def default_lang():
    """默认跟系统走：中文环境用中文，其他用英文。"""
    return P.default_lang()


def cfg_path():
    """
    配置放在 %APPDATA%\\LanSplice\\config.json。
    名字从 Link2PC 改过来，第一次跑新版时把旧目录的配置搬过来 ——
    配对码、对端地址、接收目录都别让用户重填。
    """
    appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
    base = os.path.join(appdata, APP_NAME)
    new = os.path.join(base, "config.json")
    old = os.path.join(appdata, "Link2PC", "config.json")
    if not os.path.isfile(new) and os.path.isfile(old):
        try:
            os.makedirs(base, exist_ok=True)
            with open(old, "rb") as f:
                blob = f.read()
            with open(new, "wb") as f:
                f.write(blob)
        except Exception:
            pass
    os.makedirs(base, exist_ok=True)
    return new


def load_cfg():
    p = cfg_path()
    d = {}
    if os.path.isfile(p):
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception:
            d = {}
    if not d.get("pair_key"):
        d["pair_key"] = base64.b64encode(L.new_pair_key()).decode()
    if not d.get("recv_root"):
        d["recv_root"] = P.default_recv_root(_t("g003"))
    d.setdefault("tcp_port", L.TCP_PORT)
    d.setdefault("peer_ip", "")
    d.setdefault("peer_port", L.TCP_PORT)
    d.setdefault("discovery", True)
    d.setdefault("auto_server", True)
    # ---- v1.4 常驻相关
    d.setdefault("close_to_tray", True)   # 关窗时缩到托盘，接收不中断
    d.setdefault("notify_done", True)     # 传完弹气泡
    d.setdefault("sound", True)           # 传完响一声
    d.setdefault("deep_verify", False)    # 默认不做整文件重读校验（慢）
    d.setdefault("clip_auto", False)      # 收到文字不自动改剪贴板
    d.setdefault("last_peer", {})         # {"ip":..,"port":..,"name":..}
    d.setdefault("web_port", 47822)       # 手机网页端端口
    d.setdefault("mirror_jobs", [])       # v1.6.1 常用镜像任务
    save_cfg(d)
    return d


def autostart_cmd():
    """开机要执行的那条命令（写注册表或 .desktop 都用它）。"""
    return P.autostart_cmd()


def autostart_get():
    """当前是否已设为开机自启。Windows 读注册表，Linux 看 autostart 目录。"""
    return P.autostart_get()


def autostart_set(on):
    """开 / 关开机自启。返回是否成功。"""
    return P.autostart_set(on)


def save_cfg(d):
    try:
        json.dump(d, open(cfg_path(), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
    except Exception:
        pass


# ------------------------------------------------------------ 右键菜单 / 进件
#
# 资源管理器右键「用 LanSplice 发送」是外面起的第二个进程，路径得交给
# 已经在跑的那个窗口。用 WM_COPYDATA 要两边都改消息循环，用 socket 又要
# 多开一个端口 —— 这里用最简单可靠的办法：往一个目录里放小 JSON 文件，
# 主窗口定时捡。写用 .part + rename，捡的人永远不会读到半个文件。

def inbox_dir():
    return os.path.join(os.path.dirname(cfg_path()), "inbox")


def drop_paths(paths):
    """把一批路径投给正在运行的实例。失败不抛 —— 大不了这次传不了。"""
    paths = [str(p) for p in (paths or []) if p]
    if not paths:
        return False
    d = inbox_dir()
    try:
        os.makedirs(d, exist_ok=True)
        base = "%014d_%d" % (int(time.time() * 1000), os.getpid())
        tmp = os.path.join(d, base + ".part")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(paths, f, ensure_ascii=False)
        os.replace(tmp, os.path.join(d, base + ".json"))
        return True
    except Exception:
        return False


def take_drops():
    """捡走进件，返回路径列表（去重、保序）。"""
    d = inbox_dir()
    if not os.path.isdir(d):
        return []
    out, seen = [], set()
    try:
        names = sorted(os.listdir(d))
    except Exception:
        return []
    for n in names:
        p = os.path.join(d, n)
        if n.endswith(".part"):
            # 别人正在写，或者写一半崩了；超过一分钟的算垃圾
            try:
                if time.time() - os.path.getmtime(p) > 60:
                    os.remove(p)
            except Exception:
                pass
            continue
        try:
            with open(p, encoding="utf-8") as f:
                v = json.load(f)
            if isinstance(v, list):
                for x in v:
                    x = str(x or "")
                    if x and os.path.normcase(x) not in seen:
                        seen.add(os.path.normcase(x))
                        out.append(x)
            os.remove(p)
        except Exception:
            try:
                os.remove(p)
            except Exception:
                pass
        if len(out) >= 200:
            break
    return out


def exe_launch_path():
    """注册表里那个图标/程序该指向谁（打包后是 exe，源码运行是脚本）。"""
    if getattr(sys, "frozen", False):
        return os.path.abspath(sys.executable)
    return os.path.abspath(__file__)


def exe_launch_cmd():
    """
    注册表里的那条命令。%1 由资源管理器替换成被点的路径。
    """
    if getattr(sys, "frozen", False):
        return '"%s" --send "%%1"' % os.path.abspath(sys.executable)
    # 源码模式用 pythonw，否则每次右键都闪一个黑框
    pyw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    exe = pyw if os.path.isfile(pyw) else sys.executable
    return '"%s" "%s" --send "%%1"' % (exe, os.path.abspath(__file__))


SHELL_KEYS = (r"Software\Classes\*\shell\LanSplice",
              r"Software\Classes\Directory\shell\LanSplice")


def _reg_del_tree(root, path):
    import winreg
    try:
        k = winreg.OpenKey(root, path, 0, winreg.KEY_ALL_ACCESS)
    except FileNotFoundError:
        return
    except OSError:
        return
    while True:
        try:
            sub = winreg.EnumKey(k, 0)
        except OSError:
            break
        _reg_del_tree(root, path + "\\" + sub)
    k.Close()
    try:
        winreg.DeleteKey(root, path)
    except OSError:
        pass


def shell_menu_set(on):
    """
    在 HKCU 下挂/摘右键菜单。只改当前用户，不需要管理员。

    Linux 上右键菜单是一套完全不同的东西（Nautilus 脚本 / KIO 服务菜单 /
    .desktop 的 Actions），各家文件管理器还不一样 —— 这一版不做，
    直接返回 False，界面上那个勾选项本来就不会出现。
    """
    if not P.IS_WIN:
        return False
    try:
        import winreg
        for key in SHELL_KEYS:
            if on:
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key) as k:
                    winreg.SetValueEx(k, "", 0, winreg.REG_SZ, _t("g422"))
                    winreg.SetValueEx(k, "Icon", 0, winreg.REG_SZ,
                                      exe_launch_path() + ",0")
                    # 多选时合并成一次调用，别开一堆进程
                    winreg.SetValueEx(k, "MultiSelectModel", 0, winreg.REG_SZ,
                                      "Player")
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                                      key + r"\command") as k:
                    winreg.SetValueEx(k, "", 0, winreg.REG_SZ, exe_launch_cmd())
            else:
                _reg_del_tree(winreg.HKEY_CURRENT_USER, key)
        return True
    except Exception:
        return False


def shell_menu_get():
    if not P.IS_WIN:
        return False
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            SHELL_KEYS[0] + r"\command") as k:
            v, _ = winreg.QueryValueEx(k, "")
        return bool(v)
    except Exception:
        return False


def fmt_speed(bps):
    if not bps or bps <= 0:
        return ""
    if bps < 1024 * 1024:
        return "%.0f KB/s" % (bps / 1024.0)
    return "%.1f MB/s" % (bps / 1048576.0)


def fmt_eta(done, total, bps):
    if bps <= 0 or total <= 0:
        return ""
    left = (total - done) / bps
    if left < 1:
        return _t("g004")
    if left < 60:
        return _t("g005") % left
    if left < 3600:
        return _t("g006") % (left // 60, left % 60)
    return _t("g007") % (left // 3600)


def parse_fw_status(out, expected_exe):
    """
    解析「防火墙状态」那段 PowerShell 的输出。

    返回 (alive, has_public, stale)：
      alive      —— 有几条启用的 LanSplice 规则
      has_public —— 当前网络是不是「公用」（公用网络默认更严）
      stale      —— 规则存在，但 -Program 指的是**另一个 exe**

    stale 这一条是 v1.6.0 补的：规则按 exe 完整路径绑定，
    `LanSplice-v1.5.2.exe` 升到 `v1.6.0.exe` 就是另一条路径，
    Windows 认为「这个程序没被放行」，而旧规则还在、灯还是绿的 ——
    用户看到的正是「昨天还好的，今天连不上」。
    """
    pub = False
    alive = 0
    progs = set()
    for line in (out or "").splitlines():
        line = line.strip()
        if line.startswith("CAT|"):
            if line[4:] not in ("Private", "DomainAuthenticated"):
                pub = True
        elif line.startswith("RULE|"):
            p = line.split("|")
            if len(p) >= 3 and p[2].lower() == "true":
                alive += 1
        elif line.startswith("PROG|"):
            p = line.split("|", 2)
            raw = (p[2] if len(p) >= 3 else "").strip()
            if not raw:
                continue
            try:
                raw = os.path.expandvars(raw)
                progs.add(os.path.normcase(os.path.abspath(raw)))
            except Exception:
                continue
    stale = False
    if alive and progs and expected_exe:
        try:
            want = os.path.normcase(os.path.abspath(expected_exe))
            stale = want not in progs
        except Exception:
            stale = False
    return alive, pub, stale


# ---------------------------------------------------------------- 主窗口

class App:
    def __init__(self, root):
        self.root = root
        # quiet=True：后台启动（开机自启 --min），窗口在托盘里，
        # 不能弹任何模态框 —— 弹了也没人点得到。
        self.quiet = False
        self.cfg = load_cfg()
        I18N.set_lang(self.cfg.get("lang") or default_lang())
        try:
            self.key = base64.b64decode(self.cfg["pair_key"])
        except Exception:
            self.key = L.new_pair_key()

        self.peer_ip = self.cfg.get("peer_ip") or ""
        self.peer_port = int(self.cfg.get("peer_port") or L.TCP_PORT)
        self.peer_name = ""

        self.queue_paths = []           # 待发送的顶层路径
        self.rows = {}                  # path -> treeview item id
        self.events = queue.Queue()
        self.sending = False
        self.cancel_flag = threading.Event()
        self.server = None

        self._found = []                # 设备列表第 N 行对应的数据
        self._seen = set()              # 已出现过的 (ip, port)，防重复插入

        # ---- 内网聊天（v1.7.3）
        # 不选主机：每台都是节点，靠广播互相知道，发消息直接连过去。
        self.chat_roster = CHAT.Roster() if HAS_CHAT else None
        self.chat_store = (CHAT.ChatStore(self._chat_path())
                           if HAS_CHAT else None)
        self.chat_name = CHAT.clean_name(
            self.cfg.get("chat_name") or CHAT.default_name()) if HAS_CHAT else ""
        self.chat_win = (CHATWIN.ChatWindow(self) if HAS_CHAT else None)

        self.peer_root = ""             # 对端接收目录（发送时握手取回）
        self.rel_rows = {}              # 发送用的相对路径 -> 清单行
        self.item_total = {}            # 清单行 -> 该行总字节
        self.item_done = {}             # 清单行 -> 已完成字节
        self.item_rels = {}             # 清单行 -> [相对路径...]
        self.item_ok = {}               # 清单行 -> 已完成的相对路径集合
        self.item_files_total = {}      # 清单行 -> 文件总数
        self.item_files_done = {}       # 清单行 -> 已完成文件数
        self._send_t0 = 0.0
        self.last_result = None         # 上一次传输的结果，供「详情」查看
        self.total_bytes = 0            # 本次总字节（进度条用）
        self.done_bytes = 0             # 本次已完成字节
        self.last_ui = 0.0              # 进度刷新节流时间戳
        self.tray = None                # 托盘对象
        self._quitting = False          # 真正退出（区别于缩到托盘）
        self.last_peer = dict(self.cfg.get("last_peer") or {})
        self._tx_text_win = None        # 发送文字的窗口（避免重复开）
        self._text_win = None           # 收到文字的窗口
        self._qr_win = None             # 手机传文件窗口
        self.web = None                 # 手机网页端服务
        self._mirror_win = None         # 文件夹镜像窗口
        self._mirror_ui = None          # (win, pbar, lbl, btn)
        self.mirror_cancel = threading.Event()

        self._build_ui()
        self._start_server()
        self._pump()
        self.root.after(400, self.scan_peers)
        self.root.after(600, self._refresh_fw_status)
        self.root.after(1600, self._try_last_peer)
        self.root.after(300, self._poll_inbox)     # 右键菜单投进来的路径
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self._init_tray()

    # ------------------------------------------------------------ 界面

    def _build_ui(self):
        r = self.root
        r.title("%s  v%s" % (_t("g001"), APP_VER))
        r.geometry("900x640")
        r.minsize(820, 580)
        r.configure(bg=C_BG)

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TFrame", background=C_BG)
        style.configure("Panel.TFrame", background=C_PANEL)
        style.configure("Card.TFrame", background=C_CARD, relief="flat")
        style.configure("TLabel", background=C_BG, foreground=C_TEXT, font=(FONT, 9))
        style.configure("Sub.TLabel", background=C_BG, foreground=C_SUB, font=(FONT, 8))
        style.configure("H1.TLabel", background=C_PANEL, foreground=C_TEXT,
                        font=(FONT, 12, "bold"))
        style.configure("Card.TLabel", background=C_CARD, foreground=C_TEXT, font=(FONT, 9))
        style.configure("Drop.TLabel", background=C_CARD, foreground=C_SUB, font=(FONT, 11))
        style.configure("DropBig.TLabel", background=C_CARD, foreground=C_BLUE,
                        font=(FONT, 15, "bold"))

        style.configure("Treeview", background=C_CARD, fieldbackground=C_CARD,
                        foreground=C_TEXT, rowheight=24, font=(FONT, 9),
                        borderwidth=0)
        style.configure("Treeview.Heading", background=C_PANEL, foreground=C_TEXT,
                        font=(FONT, 9, "bold"), relief="flat")
        style.map("Treeview", background=[("selected", "#bbdefb")],
                  foreground=[("selected", C_TEXT)])
        style.map("Treeview.Heading", background=[("active", "#cfd8dc")])
        style.configure("TProgressbar", background=C_BLUE, troughcolor="#d3dade",
                        borderwidth=0, thickness=14)
        style.configure("TEntry", fieldbackground="#ffffff", font=(FONT, 9))

        # ---- 菜单
        m = tk.Menu(r, font=(FONT, 9))
        r.config(menu=m)

        fm = tk.Menu(m, tearoff=0, font=(FONT, 9))
        fm.add_command(label=_t("g008"), command=self.pick_files, accelerator="Ctrl+O")
        fm.add_command(label=_t("g009"), command=self.pick_folder, accelerator="Ctrl+Shift+O")
        fm.add_separator()
        fm.add_command(label=_t("g010"), command=self.start_send)
        fm.add_command(label=_t("g011"), command=self.pull_dialog)
        fm.add_command(label=_t("g320"), command=self.send_text_dialog,
                       accelerator="Ctrl+Shift+V")
        fm.add_command(label=_t("g460") + "…", command=self.open_chat,
                       accelerator="Ctrl+M")
        fm.add_command(label=_t("g328"), command=self.send_clipboard)
        fm.add_separator()
        fm.add_command(label=_t("g360"), command=self.show_qr_share)
        fm.add_separator()
        fm.add_command(label=_t("g012"), command=self.show_result_detail)
        fm.add_command(label=_t("g386"), command=self.history_dialog)
        fm.add_separator()
        fm.add_command(label=_t("g013"), command=self.on_close)
        m.add_cascade(label=_t("g014"), menu=fm)

        tm = tk.Menu(m, tearoff=0, font=(FONT, 9))
        tm.add_command(label=_t("g015"), command=self.scan_peers, accelerator="F5")
        tm.add_command(label=_t("g016"), command=self.manual_peer)
        tm.add_command(label=_t("g017"), command=self.net_info)
        tm.add_command(label=_t("g018"), command=self.diagnose)
        tm.add_separator()
        tm.add_command(label=_t("g019"), command=self.open_recv_root)
        tm.add_command(label=_t("g020"), command=self.clear_queue)
        tm.add_separator()
        tm.add_command(label=_t("g370"), command=self.mirror_dialog)
        tm.add_separator()
        tm.add_command(label=_t("g021"), command=self.toggle_server)
        m.add_cascade(label=_t("g022"), menu=tm)

        sm = tk.Menu(m, tearoff=0, font=(FONT, 9))
        sm.add_command(label=_t("g023"), command=self.show_code)
        sm.add_command(label=_t("g024"), command=self.enter_code)
        sm.add_command(label=_t("g025"), command=self.regen_code)
        sm.add_separator()
        sm.add_command(label=_t("g026"), command=self.set_recv_root)
        sm.add_command(label=_t("g027"), command=self.fw_dialog)
        sm.add_command(label=_t("g028"), command=self.security_check)
        m.add_cascade(label=_t("g029"), menu=sm)

        hm = tk.Menu(m, tearoff=0, font=(FONT, 9))
        hm.add_command(label=_t("g030"), command=self.show_help)
        hm.add_command(label=_t("g031"), command=self.show_disclaimer)
        hm.add_separator()
        hm.add_command(label=_t("g428"), command=self.show_license)
        hm.add_separator()
        hm.add_command(label=_t("g032"), command=self.show_about)
        m.add_cascade(label=_t("g033"), menu=hm)

        # ---- 设置：常驻相关的几个开关，都在这里，不占主界面
        stm = tk.Menu(m, tearoff=0, font=(FONT, 9))
        self.var_notify = tk.BooleanVar(value=bool(self.cfg.get("notify_done", True)))
        self.var_sound = tk.BooleanVar(value=bool(self.cfg.get("sound", True)))
        self.var_tray = tk.BooleanVar(value=bool(self.cfg.get("close_to_tray", True)))
        self.var_boot = tk.BooleanVar(value=autostart_get())
        self.var_verify = tk.BooleanVar(value=bool(self.cfg.get("deep_verify")))
        self.var_clipauto = tk.BooleanVar(value=bool(self.cfg.get("clip_auto")))
        stm.add_checkbutton(label=_t("g350"), variable=self.var_notify,
                            command=self._save_opts)
        stm.add_checkbutton(label=_t("g351"), variable=self.var_sound,
                            command=self._save_opts)
        # 「关窗缩到托盘」只在有托盘的系统上才有意义；
        # Linux 上没有托盘，关窗就是退出，这条留着会让用户以为能常驻
        if P.tray_supported() and HAS_TRAY:
            stm.add_checkbutton(label=_t("g352"), variable=self.var_tray,
                                command=self._save_opts)
            stm.add_separator()
        stm.add_checkbutton(label=_t("g331"), variable=self.var_verify,
                            command=self._save_toggles)
        stm.add_checkbutton(label=_t("g330"), variable=self.var_clipauto,
                            command=self._save_toggles)
        stm.add_separator()
        stm.add_checkbutton(label=_t("g353"), variable=self.var_boot,
                            command=self._toggle_boot)
        # 资源管理器右键菜单是 Windows 专有（HKCU）。Linux 上同理不显示，
        # 免得勾了没反应 —— 那比没有这一项更让人困惑。
        if P.IS_WIN:
            stm.add_separator()
            self.var_shell = tk.BooleanVar(value=shell_menu_get())
            stm.add_checkbutton(label=_t("g423"), variable=self.var_shell,
                                command=self._toggle_shell_menu)
        else:
            self.var_shell = tk.BooleanVar(value=False)
        stm.add_separator()
        if self.tray and P.tray_supported():
            stm.add_command(label=_t("g457") + "…",
                            command=self.ask_close_action_again)
        stm.add_command(label=_t("g355"), command=self.open_cfg_folder)
        m.add_cascade(label=_t("g354"), menu=stm)

        r.bind("<Control-m>", lambda e: self.open_chat())
        r.bind("<Control-o>", lambda e: self.pick_files())
        r.bind("<Control-O>", lambda e: self.pick_folder())
        r.bind("<Control-v>", self.on_paste)
        r.bind("<Control-V>", self.on_paste)
        r.bind("<F5>", lambda e: self.scan_peers())
        r.bind("<Control-Shift-v>", self.send_clipboard)
        r.bind("<Control-Shift-V>", self.send_clipboard)

        # ---- 顶栏：状态
        top = tk.Frame(r, bg=C_PANEL, height=62)
        top.pack(fill="x")
        top.pack_propagate(False)

        self.lamp_self = tk.Label(top, text="●", bg=C_PANEL, fg=C_GRAY, font=(FONT, 13))
        self.lamp_self.pack(side="left", padx=(14, 4), pady=10)
        self.lbl_self = tk.Label(top, text=_t("g034"), bg=C_PANEL, fg=C_TEXT,
                                 font=(FONT, 10, "bold"), anchor="w")
        self.lbl_self.pack(side="left")
        self.lbl_self_sub = tk.Label(top, text="", bg=C_PANEL, fg=C_SUB, font=(FONT, 8),
                                     anchor="w")
        self.lbl_self_sub.pack(side="left", padx=(8, 0))

        sep = tk.Frame(top, bg=C_LINE, width=1)
        sep.pack(side="left", fill="y", padx=14, pady=12)

        self.lamp_peer = tk.Label(top, text="●", bg=C_PANEL, fg=C_RED, font=(FONT, 13))
        self.lamp_peer.pack(side="left", padx=(0, 4))
        self.lbl_peer = tk.Label(top, text=_t("g035"), bg=C_PANEL, fg=C_TEXT,
                                 font=(FONT, 10, "bold"), anchor="w")
        self.lbl_peer.pack(side="left")
        self.lbl_peer_sub = tk.Label(top, text=_t("g036"), bg=C_PANEL,
                                     fg=C_SUB, font=(FONT, 8), anchor="w")
        self.lbl_peer_sub.pack(side="left", padx=(8, 0))

        self.lbl_sec = tk.Label(top, text="", bg=C_PANEL, fg=C_GREEN, font=(FONT, 8, "bold"))
        self.lbl_sec.pack(side="right", padx=(8, 14))

        # 语言切换：两个小键，当前语言高亮。放首页顶栏右侧，一眼能找到。
        self.lang_box = tk.Frame(top, bg=C_PANEL)
        self.lang_box.pack(side="right", pady=10)
        for _code, _text in (("zh", "中文"), ("en", "EN")):
            _cur = (I18N.get_lang() == _code)
            tk.Button(
                self.lang_box, text=_text,
                command=lambda c=_code: self.set_language(c),
                bg=C_BLUE if _cur else "#cfd8dc",
                fg=C_WHITE if _cur else C_TEXT,
                font=(FONT, 8) + (("bold",) if _cur else ()),
                relief="flat", cursor="hand2", padx=7, pady=1,
                activebackground=C_BLUE, activeforeground=C_WHITE,
                bd=0, highlightthickness=0,
            ).pack(side="left", padx=(0, 2))

        # ---- 快捷设置条：接收目录 + 防火墙（这两个是上手最关键的两步，直接摆在首页）
        qb = tk.Frame(r, bg="#e2e8ec", height=56)
        qb.pack(fill="x")
        qb.pack_propagate(False)
        tk.Frame(r, bg=C_LINE, height=1).pack(fill="x")

        tk.Label(qb, text=_t("g037"), bg="#e2e8ec", fg=C_TEXT,
                 font=(FONT, 9, "bold")).pack(side="left", padx=(14, 8), pady=14)
        self.lbl_recv = tk.Label(qb, text="", bg="#e2e8ec", fg=C_BLUE,
                                 font=(FONT, 10, "bold"), anchor="w")
        self.lbl_recv.pack(side="left")
        self.lbl_recv_port = tk.Label(qb, text="", bg="#e2e8ec", fg=C_SUB,
                                      font=(FONT, 8), anchor="w")
        self.lbl_recv_port.pack(side="left", padx=(8, 10))
        self._mk_btn(qb, _t("g038"), self.set_recv_root, C_BLUE, width=7).pack(side="left", padx=(0, 4))
        self._mk_btn(qb, _t("g039"), self.open_recv_root, "#607d8b", width=6).pack(side="left")

        # 按钮一开始就写对：Linux 上没有「一键」，只有「把命令给你」。
        # 等线程回来再改文字的话，开机那一两秒是误导的。
        self.btn_fw = self._mk_btn(
            qb, _t("g433") if not P.IS_WIN else _t("g040"),
            self.fw_dialog, "#e65100", width=14)
        self.btn_fw.pack(side="right", padx=(6, 14))
        self.lbl_fw = tk.Label(qb, text=_t("g041"), bg="#e2e8ec", fg=C_SUB,
                               font=(FONT, 9, "bold"))
        self.lbl_fw.pack(side="right", padx=(0, 4))
        self.lbl_fw.bind("<Button-1>", lambda e: self._refresh_fw_status())

        # ---- 主体：左栏 + 右区
        body = tk.Frame(r, bg=C_BG)
        body.pack(fill="both", expand=True, padx=10, pady=(8, 0))

        left = tk.Frame(body, bg=C_PANEL, width=214)
        left.pack(side="left", fill="y", padx=(0, 8))
        left.pack_propagate(False)

        tk.Label(left, text=_t("g042"), bg=C_PANEL, fg=C_TEXT, font=(FONT, 9, "bold"),
                 anchor="w").pack(fill="x", padx=12, pady=(12, 4))

        self.peer_list = tk.Listbox(left, height=5, bg=C_CARD, fg=C_TEXT,
                                    font=(FONT, 9), relief="flat", activestyle="none",
                                    selectbackground="#bbdefb", selectforeground=C_TEXT,
                                    highlightthickness=0, borderwidth=0)
        self.peer_list.pack(fill="x", padx=12)
        self.peer_list.bind("<<ListboxSelect>>", self.on_pick_peer)

        self.btn_scan = tk.Button(left, text=_t("g043"), command=self.scan_peers,
                                  bg="#546e7a", fg=C_WHITE, font=(FONT, 9),
                                  relief="flat", cursor="hand2", activebackground="#37474f",
                                  activeforeground=C_WHITE)
        self.btn_scan.pack(fill="x", padx=12, pady=(6, 12))

        tk.Frame(left, bg=C_LINE, height=1).pack(fill="x", padx=12)

        tk.Label(left, text=_t("g044"), bg=C_PANEL, fg=C_TEXT, font=(FONT, 9, "bold"),
                 anchor="w").pack(fill="x", padx=12, pady=(12, 2))
        self.lbl_code = tk.Label(left, text="", bg=C_CARD, fg=C_BLUE,
                                 font=("Consolas", 10, "bold"), pady=6)
        self.lbl_code.pack(fill="x", padx=12)

        self.btn_copy = tk.Button(left, text=_t("g045"), command=self.copy_code,
                                  bg="#546e7a", fg=C_WHITE, font=(FONT, 9),
                                  relief="flat", cursor="hand2",
                                  activebackground="#37474f", activeforeground=C_WHITE)
        self.btn_copy.pack(fill="x", padx=12, pady=(6, 4))

        self.btn_setcode = tk.Button(left, text=_t("g046"), command=self.enter_code,
                                     bg="#546e7a", fg=C_WHITE, font=(FONT, 9),
                                     relief="flat", cursor="hand2",
                                     activebackground="#37474f", activeforeground=C_WHITE)
        self.btn_setcode.pack(fill="x", padx=12)

        tk.Frame(left, bg=C_LINE, height=1).pack(fill="x", padx=12, pady=12)

        self.lbl_port = tk.Label(left, text="", bg=C_PANEL, fg=C_SUB, font=(FONT, 8),
                                 anchor="w", justify="left", wraplength=200)
        self.lbl_port.pack(fill="x", padx=12)

        # ---- 右区
        right = tk.Frame(body, bg=C_BG)
        right.pack(side="left", fill="both", expand=True)

        self.drop = tk.Frame(right, bg=C_CARD, height=136,
                             highlightbackground=C_LINE, highlightthickness=1)
        self.drop.pack(fill="x")
        self.drop.pack_propagate(False)

        self.lbl_drop_big = tk.Label(self.drop, text=_t("g047"),
                                     bg=C_CARD, fg=C_BLUE, font=(FONT, 15, "bold"))
        self.lbl_drop_big.pack(pady=(22, 2))
        self.lbl_drop_sub = tk.Label(
            self.drop,
            text=(_t("g048")
                  if HAS_DND else
                  _t("g049")),
            bg=C_CARD, fg=C_SUB, font=(FONT, 9))
        self.lbl_drop_sub.pack()

        btns = tk.Frame(self.drop, bg=C_CARD)
        btns.pack(pady=(8, 0))
        self._mk_btn(btns, _t("g050"), self.pick_files, "#607d8b", width=None).pack(side="left", padx=4)
        self._mk_btn(btns, _t("g051"), self.pick_folder, "#607d8b", width=None).pack(side="left", padx=4)
        self._mk_btn(btns, _t("g052"), self.clear_queue, "#90a4ae", width=None).pack(side="left", padx=4)
        self._mk_btn(btns, _t("g320"), self.send_text_dialog, C_PURPLE,
                     width=None).pack(side="left", padx=4)

        if HAS_DND:
            ok = 0
            for w in (self.drop, self.lbl_drop_big, self.lbl_drop_sub):
                try:
                    w.drop_target_register(DND_FILES)
                    w.dnd_bind("<<Drop>>", self.on_drop)
                    ok += 1
                except Exception:
                    pass
            if ok == 0:
                self.lbl_drop_sub.config(
                    text=_t("g053"))

        # 队列
        qhead = tk.Frame(right, bg=C_BG)
        qhead.pack(fill="x", pady=(10, 4))
        tk.Label(qhead, text=_t("g054"), bg=C_BG, fg=C_TEXT,
                 font=(FONT, 9, "bold")).pack(side="left")
        self.lbl_qsum = tk.Label(qhead, text=_t("g055"), bg=C_BG, fg=C_SUB, font=(FONT, 8))
        self.lbl_qsum.pack(side="left", padx=10)

        self.btn_clearq = self._mk_btn(qhead, _t("g056"), self.clear_queue,
                                       "#78909c", width=None)
        self.btn_clearq.pack(side="right", padx=(4, 0))
        self.btn_rmsel = self._mk_btn(qhead, _t("g057"), self.remove_selected,
                                      "#607d8b", width=None)
        self.btn_rmsel.pack(side="right", padx=(4, 0))
        tk.Label(qhead, text=_t("g058"), bg=C_BG, fg=C_SUB,
                 font=(FONT, 8)).pack(side="right", padx=(0, 6))

        cols = ("name", "size", "prog", "speed", "state")
        self.tree = ttk.Treeview(right, columns=cols, show="headings", height=8)
        for c, t, w, a in (("name", _t("g014"), 240, "w"),
                           ("size", _t("g059"), 80, "e"),
                           ("prog", _t("g060"), 70, "center"),
                           ("speed", _t("g061"), 90, "e"),
                           ("state", _t("g062"), 80, "w")):
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, anchor=a, stretch=(c == "name"))

        sb = ttk.Scrollbar(right, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)

        self.tree.bind("<Double-1>", self.on_tree_double)
        self.tree.bind("<Delete>", lambda e: self.remove_selected())
        self.tree.bind("<Button-3>", self.queue_menu)          # 右键菜单
        self.tree.bind("<Shift-F10>", self.queue_menu)
        self.qmenu = self._build_queue_menu()

        # ---- 底栏（必须在 body 之前 pack，否则会被 expand 的主体挤扁）
        bottom = tk.Frame(r, bg=C_PANEL, height=98)
        bottom.pack(fill="x", side="bottom", before=body)
        bottom.pack_propagate(False)

        inner = tk.Frame(bottom, bg=C_PANEL)
        inner.pack(fill="x", padx=14, pady=(10, 6))

        self.btn_send = self._mk_btn(inner, _t("g063"), self.start_send,
                                     C_BLUE, width=16, big=True)
        self.btn_send.pack(side="left")
        self.btn_pull = self._mk_btn(inner, _t("g064"), self.pull_dialog,
                                     C_GREEN, width=16, big=True)
        self.btn_pull.pack(side="left", padx=8)
        self.btn_stop = self._mk_btn(inner, _t("g065"), self.stop_send, C_RED, width=8, big=True)
        self.btn_stop.pack(side="left")
        self.btn_stop.config(state="disabled")

        self.btn_detail = self._mk_btn(inner, _t("g066"), self.show_result_detail,
                                       "#546e7a", width=7, big=True)
        self.btn_detail.pack(side="right", padx=(10, 0))
        self.btn_detail.config(state="disabled")

        self.lbl_status = tk.Label(inner, text=_t("g067"), bg=C_PANEL, fg=C_SUB,
                                   font=(FONT, 9), anchor="e", justify="right")
        self.lbl_status.pack(side="right")

        self.pbar = ttk.Progressbar(bottom, mode="determinate", maximum=1000)
        self.pbar.pack(fill="x", padx=14, pady=(2, 10))

        self._refresh_self()
        self._refresh_code()
        self._refresh_queue_summary()

    # ------------------------------------------------------------ 语言

    def set_language(self, lang):
        if lang == I18N.get_lang():
            return
        if self.sending:
            messagebox.showinfo(APP_NAME, _t("g248"))
            return
        self.cfg["lang"] = lang
        save_cfg(self.cfg)
        I18N.set_lang(lang)
        self._rebuild_ui()

    def _rebuild_ui(self):
        """
        切换语言时整块重建控件。逐个改 text 一定会漏（菜单、表头、右键菜单、
        Treeview 列标题），重建最省心；清单、设备列表、对端选择在重建后原样恢复。
        """
        rows = []
        for p in self.queue_paths:
            iid = self.rows.get(p)
            if iid:
                rows.append((p, self.tree.item(iid, "values")))
        found = [dict(f) for f in self._found]
        peer = (self.peer_ip, self.peer_port, self.peer_name)

        for w in self.root.winfo_children():
            w.destroy()
        self.rows = {}
        self._build_ui()

        self._found = found
        self._seen = set((f["ip"], int(f.get("port") or L.TCP_PORT))
                         for f in found)
        for f in found:
            self.peer_list.insert(
                "end", "  %s  %s:%d" % (f.get("name", "?"), f["ip"],
                                        int(f.get("port") or L.TCP_PORT)))
        if peer[0]:
            for i, f in enumerate(found):
                if f["ip"] == peer[0]:
                    self.peer_list.selection_set(i)
                    break
            self.set_peer(peer[0], int(peer[1] or L.TCP_PORT), peer[2])
        for p, vals in rows:
            self.rows[p] = self.tree.insert("", "end", values=vals)
        self._refresh_queue_summary()
        self.lbl_status.config(text=_t("g067"))
        self._refresh_fw_status()

    def _mk_btn(self, parent, text, cmd, color, width=12, big=False):
        # width=None 时按文字自然宽度撑开 —— 中文按钮写死字符宽度会被截断
        extra = {} if not width else {"width": width}
        b = tk.Button(parent, text=text, command=cmd, bg=color, fg=C_WHITE,
                      font=(FONT, 10 if big else 9) + (("bold",) if big else ()),
                      relief="flat", cursor="hand2",
                      pady=7 if big else 5,
                      activebackground=color, activeforeground=C_WHITE,
                      disabledforeground="#cfd8dc", **extra)
        b.bind("<Enter>", lambda e, w=b, c=color: w.config(bg=self._darken(c)) if str(w["state"]) != "disabled" else None)
        b.bind("<Leave>", lambda e, w=b, c=color: w.config(bg=c) if str(w["state"]) != "disabled" else None)
        return b

    @staticmethod
    def _darken(hexcolor, f=0.86):
        h = hexcolor.lstrip("#")
        r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
        return "#%02x%02x%02x" % (int(r * f), int(g * f), int(b * f))

    # ------------------------------------------------------------ 状态刷新

    def _refresh_self(self):
        ips = L.local_ips()
        self.lbl_self.config(text=_t("g068") % L.hostname())
        if not ips:
            sub = _t("g069")
        elif len(ips) == 1:
            sub = ips[0]
        else:
            sub = _t("g070") % (ips[0], len(ips))
        self.lbl_self_sub.config(text=sub)
        on = self.server is not None and self.server.running
        self.lamp_self.config(fg=C_GREEN if on else C_GRAY)
        self.lbl_sec.config(
            text=_t("g071") if on else _t("g072"),
            fg=C_GREEN if on else C_GRAY)
        root_dir = self.cfg["recv_root"]
        # 路径太长会把右边的「一键放行」挤出去，中间省略只留结尾
        if len(root_dir) > 34:
            root_dir = "…" + root_dir[-30:]
        self.lbl_recv.config(text=root_dir)
        self.lbl_recv_port.config(text=_t("g073") % int(self.cfg["tcp_port"]))
        self.lbl_port.config(text=_t("g074") % int(self.cfg["tcp_port"]))

    def _refresh_code(self):
        self.lbl_code.config(text=L.key_to_code(self.key))

    def _refresh_queue_summary(self):
        if not self.queue_paths:
            self.lbl_qsum.config(text=_t("g055"))
            return
        n = 0
        sz = 0
        for p in self.queue_paths:
            if os.path.isfile(p):
                n += 1
                try:
                    sz += os.path.getsize(p)
                except Exception:
                    pass
            elif os.path.isdir(p):
                for root, dirs, files in os.walk(p):
                    for f in files:
                        try:
                            sz += os.path.getsize(os.path.join(root, f))
                            n += 1
                        except Exception:
                            pass
        self.lbl_qsum.config(text=_t("g075") % (
            len(self.queue_paths), n, L.human_size(sz)))

    def set_peer(self, ip, port, name=""):
        self.peer_ip = ip
        self.peer_port = port
        self.peer_name = name or ip
        self.lbl_peer.config(text=_t("g076") % self.peer_name)
        self.lbl_peer_sub.config(text="%s:%d" % (ip, port))
        self.lamp_peer.config(fg=C_GREEN)
        self.cfg["peer_ip"] = ip
        self.cfg["peer_port"] = port
        save_cfg(self.cfg)
        self._remember_peer()

    def clear_peer(self):
        self.lamp_peer.config(fg=C_RED)
        self.lbl_peer.config(text=_t("g077"))
        self.lbl_peer_sub.config(text=_t("g036"))

    # ------------------------------------------------------------ 设备发现

    def scan_peers(self, silent=False):
        if not silent:
            self.btn_scan.config(text=_t("g078"), state="disabled")
            self.peer_list.delete(0, "end")

        def work():
            try:
                found = L.discover(timeout=1.6)
            except Exception:
                found = []
            self.events.put(("peers", found))
        threading.Thread(target=work, daemon=True).start()

    def on_peers(self, found):
        self.btn_scan.config(text=_t("g043"), state="normal")
        me = set(L.local_ips())
        # 回环 / 本机网卡地址都算自己（广播副本会带着 127.0.0.1 回来）
        shown = [f for f in found if not L.is_own_addr(f.get("ip"), me)]
        # 同一台机器可能从多个地址应答（有线+无线、虚拟网卡），按主机名只留一条
        uniq, names = [], set()
        for f in shown:
            n = (f.get("name") or "?").lower()
            if n in names:
                continue
            names.add(n)
            uniq.append(f)
        shown = uniq
        self._found = shown
        self._seen = set((f.get("ip"), int(f.get("port") or L.TCP_PORT))
                         for f in shown)
        if not shown:
            self.peer_list.insert("end", _t("g079"))
            self.clear_peer()
            self.lbl_status.config(
                text=_t("g080") % len(me))
            return
        for f in shown:
            self.peer_list.insert(
                "end", "  %s  %s:%d" % (f.get("name", "?"), f.get("ip"),
                                        int(f.get("port") or L.TCP_PORT)))
        self.peer_list.selection_set(0)
        self.on_pick_peer(None)
        self.lbl_status.config(text=_t("g081") % len(shown))

    def on_peer_seen(self, d):
        """
        对端主动通告了自己：它刚打开，或者每 8 秒的例行宣告。
        自动加进列表并选中，不用再点「重新查找」。
        """
        ip = d.get("ip")
        port = int(d.get("port") or L.TCP_PORT)
        name = d.get("name") or "?"
        if L.is_own_addr(ip):
            return

        # 同一条广播顺手推进聊天成员表 —— 聊天不需要另开一套心跳，
        # 广播本来每 8 秒就有一轮。
        if HAS_CHAT and self.chat_roster is not None:
            try:
                is_new = self.chat_roster.update(
                    {"name": name, "port": port, "ip": ip,
                     "inst": d.get("inst")}, ip=ip)
                if self.chat_win is not None and self.chat_win.win is not None:
                    if is_new or True:
                        self.chat_win.refresh_roster()
            except Exception:
                pass

        # 同一台机器的多个地址只保留一条（否则列表里会出现两台同名设备）
        low = name.lower()
        for i, f in enumerate(self._found):
            if (f.get("name") or "").lower() == low:
                if f.get("ip") != ip or int(f.get("port") or 0) != port:
                    # 注意：Listbox 的 delete 会把选中状态一起清掉，
                    # 必须先记住，再恢复，否则对端地址更新了但 peer 还是旧的
                    was_sel = (i in self.peer_list.curselection())
                    f["ip"] = ip
                    f["port"] = port
                    self.peer_list.delete(i)
                    self.peer_list.insert(i, "  %s  %s:%d" % (name, ip, port))
                    if was_sel:
                        self.peer_list.selection_clear(0, "end")
                        self.peer_list.selection_set(i)
                        self.on_pick_peer(None)
                return

        key = (ip, port)
        if key in self._seen:
            return
        self._seen.add(key)

        # 清掉"没找到"那行占位文字
        for i, txt in enumerate(self.peer_list.get(0, "end")):
            if txt.startswith(_t("g082")):
                self.peer_list.delete(i)
                break

        self._found.append({"ip": ip, "port": port, "name": name})
        self.peer_list.insert("end", "  %s  %s:%d" % (name, ip, port))

        # 关键：以前这里判断 "没有 peer_ip 才自动选中"，结果配置里存着上次的
        # 对端地址，条件恒为假 —— 列表有设备但对端栏还是红色「未连接」，
        # 必须手点「重新查找」才正常。改成看**列表有没有选中行**。
        sel = self.peer_list.curselection()
        same = (ip == self.peer_ip
                and self.peer_port is not None
                and port == int(self.peer_port))
        if not sel or same:
            self.peer_list.selection_clear(0, "end")
            self.peer_list.selection_set(self.peer_list.size() - 1)
            self.on_pick_peer(None)
        self.lbl_status.config(text=_t("g083") % (name, ip))

    def on_pick_peer(self, _evt):
        sel = self.peer_list.curselection()
        if not sel:
            return
        idx = sel[0]
        found = getattr(self, "_found", [])
        if idx < len(found):
            f = found[idx]
            self.set_peer(f["ip"], int(f.get("port") or L.TCP_PORT), f.get("name"))

    def manual_peer(self):
        v = simpledialog.askstring(
            _t("g084"),
            _t("g085") % L.TCP_PORT,
            initialvalue=self.peer_ip, parent=self.root)
        if not v:
            return

        cands = []
        for tok in v.replace(",", " ").replace(_t("g086"), " ").replace(";", " ").split():
            ip, port = tok, L.TCP_PORT
            if ":" in tok:
                ip, ps = tok.rsplit(":", 1)
                try:
                    port = int(ps)
                except Exception:
                    port = L.TCP_PORT
            ip = ip.strip()
            if ip and ip not in [c[0] for c in cands]:
                cands.append((ip, port))
        if not cands:
            return
        if len(cands) == 1:
            self.set_peer(cands[0][0], cands[0][1], cands[0][0])
            self.test_peer()
            return
        self._try_candidates(cands)

    def _try_candidates(self, cands):
        """一次填了多个地址：逐个连，第一个连通的就用。"""
        self.lbl_peer_sub.config(text=_t("g087") % len(cands))
        self.lbl_status.config(text=_t("g088") % len(cands))

        def work():
            errs = []
            for ip, port in cands:
                try:
                    c = L.LinkClient(ip, port, self.key, timeout=L.CONNECT_TIMEOUT).open()
                    name = c.peer_name
                    c.close()
                    self.events.put(("peer_ok", (ip, port, name)))
                    return
                except L.AuthError:
                    self.events.put(("peer_auth_fail", ip))
                    return
                except Exception as e:
                    errs.append(_t("g089") % (ip, str(e)[:36]))
            self.events.put(("peer_fail", _t("g090").join(errs)))
        threading.Thread(target=work, daemon=True).start()

    def net_info(self):
        d = L.list_ipv4()
        rows = []
        for x in d:
            tag = L._demo_net_type(x["ip"])
            rows.append(_t("g091") % (
                x["ip"], x["prefix"], x["bcast"], tag))
        if not rows:
            rows.append(_t("g092"))
        txt = (_t("g093") % (L.hostname(), "\n".join(rows)))
        messagebox.showinfo(_t("g094"), txt.replace("**", ""), parent=self.root)

    def test_peer(self):
        if not self.peer_ip:
            messagebox.showinfo(APP_NAME, _t("g095"))
            return
        self.lbl_peer_sub.config(text=_t("g096"))

        def work():
            try:
                c = L.LinkClient(self.peer_ip, self.peer_port, self.key, timeout=L.CONNECT_TIMEOUT).open()
                name = c.peer_name
                c.close()
                self.events.put(("peer_ok", (self.peer_ip, self.peer_port, name)))
            except L.AuthError:
                self.events.put(("peer_auth_fail", self.peer_ip))
            except Exception as e:
                self.events.put(("peer_fail", str(e)))
        threading.Thread(target=work, daemon=True).start()

    # ------------------------------------------------------------ 添加目标

    def on_drop(self, event):
        try:
            items = self.root.tk.splitlist(event.data)
        except Exception:
            items = [event.data]
        self.add_paths([i for i in items if i])

    def on_paste(self, event=None, force=False):
        """
        Ctrl+V / 右键「粘贴」：把资源管理器里「复制」的文件/文件夹塞进待发清单。
        剪贴板里是普通文字时不动它 —— 该给输入框用的还是给输入框。
        force=True 表示是鼠标点菜单进来的，不用管焦点在哪个控件上。
        """
        if not force:
            try:
                w = self.root.focus_get()
            except Exception:
                w = None
            if isinstance(w, (tk.Entry, tk.Text, ttk.Entry, ttk.Combobox)):
                return None
        if self.sending:
            self.lbl_status.config(text=_t("g097"))
            return "break"
        paths = clipboard_file_paths()
        if not paths:
            self.lbl_status.config(
                text=_t("g098"))
            return "break"
        added = self.add_paths(paths)
        if not added:
            self.lbl_status.config(
                text=_t("g099") % len(paths))
        return "break"

    def _build_queue_menu(self):
        """待发清单右键菜单。索引：0 粘贴 / 2 加文件 / 3 加文件夹 / 5 移除 / 6 清空。"""
        m = tk.Menu(self.root, tearoff=0, font=(FONT, 9))
        m.add_command(label=_t("g100"),
                      command=lambda: self.on_paste(force=True))
        m.add_separator()
        m.add_command(label=_t("g008"), command=self.pick_files)
        m.add_command(label=_t("g009"), command=self.pick_folder)
        m.add_separator()
        m.add_command(label=_t("g057"), command=self.remove_selected)
        m.add_command(label=_t("g056"), command=self.clear_queue)
        return m

    def queue_menu(self, event):
        """
        在待发清单里点右键：弹菜单，最上面就是「粘贴」。
        点到某一行就顺带选中它；点在空白处则保留原来的多选。
        """
        row = self.tree.identify_row(event.y)
        sel = self.tree.selection()
        if row:
            self.tree.focus(row)
            if row not in sel:
                self.tree.selection_set(row)
                sel = self.tree.selection()

        busy = bool(self.sending)
        m = self.qmenu
        try:
            for idx in (0, 2, 3):
                m.entryconfigure(idx, state="disabled" if busy else "normal")
            m.entryconfigure(5, state="normal" if (sel and not busy) else "disabled")
            m.entryconfigure(6, state="normal"
                             if (self.queue_paths and not busy) else "disabled")
        except Exception:
            pass
        try:
            m.tk_popup(event.x_root, event.y_root)
        finally:
            m.grab_release()
        return "break"

    # ------------------------------------------------------------ 文字互传

    # ------------------------------------------------------------ 内网聊天

    def open_chat(self):
        """打开聊天窗口。没有局域网其他人也能开，只是发不出去。"""
        if not HAS_CHAT:
            messagebox.showinfo(APP_NAME, _t("g460"), parent=self.root)
            return
        self.chat_win.open()
        # 打开时顺手扫一遍，别让人干等广播
        try:
            self.scan_peers(silent=True)
        except Exception:
            pass

    def set_chat_name(self, name):
        self.chat_name = CHAT.clean_name(name)
        self.cfg["chat_name"] = self.chat_name
        save_cfg(self.cfg)

    @staticmethod
    def _my_ips_cached():
        return set(d["ip"] for d in L.list_ipv4())

    def chat_peers(self):
        """当前能发的人（去掉自己这台）。"""
        if not HAS_CHAT or self.chat_roster is None:
            return []
        out = []
        mine = self._my_ips_cached()
        my_ports = set()
        try:
            if self.server:
                my_ports.add(int(self.server.port))
        except Exception:
            pass
        for p in self.chat_roster.online():
            # 自己发出去的广播也会回来，按「端口相同 + IP 是本机」排掉
            if p["port"] in my_ports and p["ip"] in mine:
                continue
            out.append(p)
        return out

    def chat_send(self, body, on_done=None):
        """
        把一句话发给所有在线的人。

        关键：**没有中转**。每台自己连过去发，谁关机都不影响别人。
        单台失败不算整体失败 —— 内网里有人睡眠、关机是常态。
        """
        peers = self.chat_peers()
        msg = CHAT.make_msg(body, self.chat_name)
        if not peers:
            if on_done:
                on_done(0, [_t("g476")], msg)
            return

        def work():
            res = CHAT.broadcast(self.key, peers, msg)
            ok_n = sum(1 for _p, ok, _e in res if ok)
            fails = ["%s：%s" % (p.get("name") or p["ip"], e)
                     for p, ok, e in res if not ok and e]
            if ok_n:
                try:
                    self.chat_store.append(msg)
                except Exception:
                    pass
            try:
                self.events.put(("chat_sent", (ok_n, fails, msg, on_done)))
            except Exception:
                pass

        threading.Thread(target=work, daemon=True,
                         name="LanSplice-ChatSend").start()

    def on_chat_incoming(self, msg):
        """服务端收到一条聊天消息（在事件泵里被调用）。"""
        clean = CHAT.handle_incoming(msg, roster=self.chat_roster,
                                     store=self.chat_store)
        if not clean:
            return
        try:
            self.lbl_status.config(text=_t("g466") % clean["from"])
        except Exception:
            pass
        if self.chat_win is not None:
            self.chat_win.on_incoming(clean)
        # 窗口没开也要让人知道有新消息
        if self.chat_win is None or self.chat_win.win is None:
            self._notify(_t("g460"), _t("g466") % clean["from"] + "：" +
                         clean["body"][:60])

    def _chat_path(self):
        """聊天记录放配置目录，跟 history.jsonl 做邻居。"""
        try:
            return os.path.join(os.path.dirname(cfg_path()), "chat.jsonl")
        except Exception:
            return "chat.jsonl"

    def _save_toggles(self):
        self.cfg["deep_verify"] = bool(self.var_verify.get())
        self.cfg["clip_auto"] = bool(self.var_clipauto.get())
        save_cfg(self.cfg)

    def _save_opts(self):
        self.cfg["notify_done"] = bool(self.var_notify.get())
        self.cfg["sound"] = bool(self.var_sound.get())
        self.cfg["close_to_tray"] = bool(self.var_tray.get())
        save_cfg(self.cfg)

    def _toggle_boot(self):
        on = bool(self.var_boot.get())
        if autostart_set(on):
            self.lbl_status.config(text=_t("g307") if on else _t("g308"))
        else:
            self.var_boot.set(autostart_get())
            messagebox.showwarning(APP_NAME, _t("g306"), parent=self.root)

    def _toggle_shell_menu(self):
        """v1.6.1：在资源管理器右键里挂/摘「用 LanSplice 发送」。"""
        on = bool(self.var_shell.get())
        if shell_menu_set(on):
            self.cfg["shell_menu"] = on
            save_cfg(self.cfg)
            self.lbl_status.config(text=_t("g424") if on else _t("g425"))
        else:
            self.var_shell.set(shell_menu_get())
            messagebox.showwarning(APP_NAME, _t("g426"), parent=self.root)

    def _poll_inbox(self):
        """
        捡走右键菜单投进来的路径（另一个进程写的小 JSON）。
        800ms 一次，空目录就是一次 listdir，开销可以忽略。
        """
        try:
            got = take_drops()
            if got:
                self.add_paths(got)
                self.lbl_status.config(text=_t("g427") % len(got))
                if not self.root.winfo_viewable():
                    self.show_window()
        except Exception:
            pass
        try:
            self.root.after(800, self._poll_inbox)
        except Exception:
            pass

    def open_cfg_folder(self):
        try:
            L.open_in_file_manager(os.path.dirname(cfg_path()))
        except Exception:
            pass

    def clipboard_text(self):
        """读剪贴板里的纯文字；不是文字就返回空串。"""
        try:
            return self.root.clipboard_get() or ""
        except Exception:
            return ""

    def _set_clipboard(self, text):
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.root.update_idletasks()
            return True
        except Exception:
            return False

    def _push_text(self, body, clip=False):
        if not body:
            self.lbl_status.config(text=_t("g329"))
            return
        if not self.peer_ip:
            messagebox.showinfo(APP_NAME, _t("g340"), parent=self.root)
            return

        def work():
            try:
                cli = L.LinkClient(self.peer_ip, self.peer_port, self.key,
                                   timeout=L.CONNECT_TIMEOUT).open()
                try:
                    cli.send_text(body, clip=clip)
                    name = cli.peer_name or self.peer_ip
                finally:
                    cli.close()
                self.events.put(("text_ok", (name, len(body))))
            except L.AuthError:
                self.events.put(("text_fail", _t("g111")))
            except Exception as e:
                self.events.put(("text_fail", str(e)))

        threading.Thread(target=work, daemon=True).start()

    def send_clipboard(self, event=None):
        """Ctrl+Shift+V：把本机剪贴板文字直接推到对端。"""
        w = self.root.focus_get()
        if event is not None and isinstance(w, (tk.Entry, tk.Text)):
            return None          # 光标在输入框里，用户是想粘自己的，让路
        self._push_text(self.clipboard_text(), clip=True)
        return "break"

    def send_text_dialog(self):
        if self._tx_text_win is not None:
            try:
                self._tx_text_win.lift()
                self._tx_text_win.focus_force()
                return
            except Exception:
                self._tx_text_win = None

        win = tk.Toplevel(self.root)
        self._tx_text_win = win
        win.title(_t("g321"))
        win.configure(bg=C_BG)
        win.geometry("520x380")
        win.transient(self.root)

        # 底部按钮栏必须先占位，正文后放。
        # tk.Text 默认要 24 行高 × 80 字符宽，又是 expand=True：排在前面的活，
        # 它会把 520x380 的窗口吃到只剩 1px 给后面的按钮栏 ——
        # 三个按钮因此跑到窗口外面，非要手动把窗口拉大才露出来。
        bar = tk.Frame(win, bg=C_BG)
        bar.pack(side="bottom", fill="x", padx=14, pady=10)

        tk.Label(win, text=_t("g342"), bg=C_BG, fg=C_TEXT,
                 font=(FONT, 9), anchor="w").pack(fill="x", padx=14, pady=(12, 4))

        wrap = tk.Frame(win, bg=C_LINE)
        wrap.pack(fill="both", expand=True, padx=14)
        # 给 Text 一个明确的小尺寸，别用默认的 24 行 × 80 列；
        # expand=True 照样会让它撑满剩下的空间，只是不再反过来挤压别人。
        txt = tk.Text(wrap, font=(FONT, 10), bg=C_CARD, fg=C_TEXT,
                      relief="flat", wrap="word", undo=True, padx=8, pady=6,
                      height=10, width=40)
        sb = ttk.Scrollbar(wrap, orient="vertical", command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        txt.pack(side="left", fill="both", expand=True, padx=1, pady=1)
        txt.focus_set()

        def fill_clip():
            t = self.clipboard_text()
            if not t:
                return
            txt.delete("1.0", "end")
            txt.insert("1.0", t)

        def do_send():
            body = txt.get("1.0", "end-1c")
            if not body.strip():
                return
            self._on_text_win_close()
            self._push_text(body, clip=False)

        def on_close():
            self._on_text_win_close()

        self._mk_btn(bar, _t("g341"), fill_clip, "#607d8b",
                     width=None).pack(side="left")
        self._mk_btn(bar, _t("g327"), on_close, C_GRAY,
                     width=None).pack(side="right", padx=(6, 0))
        self._mk_btn(bar, _t("g321"), do_send, C_PURPLE,
                     width=None).pack(side="right")

        win.protocol("WM_DELETE_WINDOW", on_close)
        win.bind("<Escape>", lambda e: on_close())

    def _on_text_win_close(self):
        try:
            if self._tx_text_win is not None:
                self._tx_text_win.destroy()
        except Exception:
            pass
        self._tx_text_win = None

    def on_recv_text(self, d):
        """
        对端推来一段文字。

        默认弹窗让用户自己决定复制不复制；勾了「自动写剪贴板」就直接写。
        不默认自动写 —— 它会把用户手上正要粘的东西顶掉，属于帮倒忙。
        """
        body = d.get("body") or ""
        who = d.get("from") or self.peer_ip or "?"
        self.lbl_status.config(text=_t("g324") % who)

        if self.cfg.get("clip_auto"):
            if self._set_clipboard(body):
                self._notify(_t("g324") % who, _t("g326"))
            else:
                self._notify(_t("g324") % who, body[:80])
            return

        self._notify(_t("g324") % who, body[:80])
        self._show_text_window(who, body)

    def _show_text_window(self, who, body):
        if self._text_win is not None:
            try:
                self._text_win.destroy()
            except Exception:
                pass
        win = tk.Toplevel(self.root)
        self._text_win = win
        win.title(_t("g344"))
        win.configure(bg=C_BG)
        win.geometry("520x360")
        win.transient(self.root)

        # 同发送窗口：按钮栏先占底，Text 给明确尺寸，别让它把按钮挤出去
        bar = tk.Frame(win, bg=C_BG)
        bar.pack(side="bottom", fill="x", padx=14, pady=10)

        tk.Label(win, text=_t("g324") % who, bg=C_BG, fg=C_TEXT,
                 font=(FONT, 9, "bold"), anchor="w").pack(fill="x", padx=14,
                                                          pady=(12, 4))
        wrap = tk.Frame(win, bg=C_LINE)
        wrap.pack(fill="both", expand=True, padx=14)
        txt = tk.Text(wrap, font=(FONT, 10), bg=C_CARD, fg=C_TEXT,
                      relief="flat", wrap="word", padx=8, pady=6,
                      height=10, width=40)
        sb = ttk.Scrollbar(wrap, orient="vertical", command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        txt.pack(side="left", fill="both", expand=True, padx=1, pady=1)
        txt.insert("1.0", body)
        txt.config(state="disabled")

        lab = tk.Label(bar, text="", bg=C_BG, fg=C_GREEN, font=(FONT, 8))
        lab.pack(side="left")

        def do_copy():
            if self._set_clipboard(body):
                lab.config(text=_t("g326"))

        self._mk_btn(bar, _t("g325"), do_copy, C_GREEN,
                     width=None).pack(side="right", padx=(6, 0))
        self._mk_btn(bar, _t("g327"), win.destroy, C_GRAY,
                     width=None).pack(side="right")

        def on_close():
            self._text_win = None
            win.destroy()
        win.protocol("WM_DELETE_WINDOW", on_close)

    # ------------------------------------------------------------ 手机网页端

    def show_qr_share(self):
        if not HAS_WEB:
            return
        if self._qr_win is not None:
            try:
                self._qr_win.lift()
                self._qr_win.focus_force()
                return
            except Exception:
                self._qr_win = None

        recv = self.cfg["recv_root"]
        port = int(self.cfg.get("web_port") or WEB.WEB_PORT)
        try:
            os.makedirs(recv, exist_ok=True)
        except Exception as e:
            messagebox.showerror(APP_NAME, str(e), parent=self.root)
            return

        if self.web is not None:
            try:
                self.web.stop()
            except Exception:
                pass
            self.web = None

        sv = WEB.WebShare(recv, port=port,
                          log=lambda s: self.events.put(("log", s)))
        if not sv.start():
            messagebox.showerror(APP_NAME, _t("g365") % port, parent=self.root)
            return
        self.web = sv
        url = sv.url()

        win = tk.Toplevel(self.root)
        self._qr_win = win
        win.title(_t("g360"))
        win.configure(bg=C_BG)
        win.resizable(False, False)
        win.transient(self.root)

        tk.Label(win, text=_t("g361"), bg=C_BG, fg=C_SUB, font=(FONT, 9),
                 justify="left").pack(anchor="w", padx=18, pady=(14, 4))

        cv = tk.Canvas(win, width=252, height=252, bg=C_WHITE,
                       highlightthickness=1, highlightbackground=C_LINE)
        cv.pack(padx=18, pady=4)
        if not self._draw_qr(cv, url, 232):
            cv.create_text(126, 126, text="QR", fill=C_SUB, font=(FONT, 12))

        tk.Label(win, text=_t("g369"), bg=C_BG, fg=C_TEXT,
                 font=(FONT, 9, "bold")).pack(pady=(0, 2))

        ent = tk.Entry(win, font=("Consolas", 9), bg=C_CARD, fg=C_TEXT,
                       relief="flat", justify="center", width=46)
        ent.insert(0, url)
        ent.config(state="readonly")
        ent.pack(padx=18, pady=(2, 2))

        tk.Label(win, text=_t("g366"), bg=C_BG, fg=C_SUB,
                 font=(FONT, 8)).pack(pady=(6, 0))

        bar = tk.Frame(win, bg=C_BG)
        bar.pack(padx=18, pady=12)
        lab = tk.Label(bar, text=_t("g362") % sv.token[:8], bg=C_BG,
                       fg=C_SUB, font=(FONT, 8))
        lab.pack(side="left")

        def do_copy():
            if self._set_clipboard(url):
                lab.config(text=_t("g364"), fg=C_GREEN)

        def do_open():
            P.open_url(url)

        self._mk_btn(bar, _t("g368"), do_open, "#607d8b",
                     width=None).pack(side="right", padx=(6, 0))
        self._mk_btn(bar, _t("g363"), do_copy, C_BLUE,
                     width=None).pack(side="right")
        self._mk_btn(bar, _t("g327"), self._close_qr, C_GRAY,
                     width=None).pack(side="right", padx=(6, 0))

        win.protocol("WM_DELETE_WINDOW", self._close_qr)

    def _close_qr(self):
        try:
            if self.web is not None:
                self.web.stop()
        except Exception:
            pass
        self.web = None
        try:
            if self._qr_win is not None:
                self._qr_win.destroy()
        except Exception:
            pass
        self._qr_win = None

    def _draw_qr(self, canvas, text, size=232):
        """
        把二维码矩阵直接画到 Canvas 上。

        不用 qrcode 的图片输出（那需要 Pillow），只要矩阵 ——
        qrcode 的矩阵是纯 Python 算的，32 位包里现成能用，也少一个依赖。
        """
        try:
            import qrcode
            q = qrcode.QRCode(border=2, box_size=1,
                              error_correction=qrcode.constants.ERROR_CORRECT_M)
            q.add_data(text)
            q.make(fit=True)
            m = q.get_matrix()
        except Exception:
            return False
        n = len(m)
        if not n:
            return False
        cell = max(1, int(size // n))
        off = (size - cell * n) // 2 + 8
        canvas.delete("all")
        for y, row in enumerate(m):
            y0 = off + y * cell
            for x, v in enumerate(row):
                if v:
                    x0 = off + x * cell
                    canvas.create_rectangle(x0, y0, x0 + cell, y0 + cell,
                                            outline="", fill="#1f2a23")
        return True

    def mirror_dialog(self):
        """
        把本机一个文件夹「补齐」到对端。

        只做加法：新增和改动过的传过去，对端多出来的文件一律不动。
        删除是不可逆的，一个手滑就是别人的数据没了 —— 这个功能不值得冒那个险。
        """
        if self._mirror_win is not None:
            try:
                self._mirror_win.lift()
                self._mirror_win.focus_force()
                return
            except Exception:
                self._mirror_win = None

        win = tk.Toplevel(self.root)
        self._mirror_win = win
        win.title(_t("g370"))
        win.configure(bg=C_BG)
        win.geometry("640x364")
        win.transient(self.root)

        tk.Label(win, text=_t("g371"), bg=C_BG, fg=C_SUB, font=(FONT, 9),
                 justify="left").pack(anchor="w", padx=16, pady=(14, 8))

        # v1.6.1：常用任务。同一对文件夹每周都要同步一次，
        # 每次重新点两遍目录太傻 —— 存下来，下拉里挑一下就行。
        row0 = tk.Frame(win, bg=C_BG)
        row0.pack(fill="x", padx=16, pady=(0, 6))
        tk.Label(row0, text=_t("g417"), bg=C_BG, fg=C_TEXT,
                 font=(FONT, 9), width=8, anchor="w").pack(side="left")
        job_var = tk.StringVar()
        cb = ttk.Combobox(row0, textvariable=job_var, state="readonly",
                          font=(FONT, 9))
        cb.pack(side="left", fill="x", expand=True, padx=(0, 6))
        b_save = self._mk_btn(row0, _t("g419"), None, C_GREEN, width=None)
        b_save.pack(side="left")
        b_del = self._mk_btn(row0, _t("g420"), None, C_RED, width=None)
        b_del.pack(side="left", padx=(6, 0))

        row1 = tk.Frame(win, bg=C_BG)
        row1.pack(fill="x", padx=16, pady=3)
        tk.Label(row1, text=_t("g372"), bg=C_BG, fg=C_TEXT,
                 font=(FONT, 9), width=8, anchor="w").pack(side="left")
        src_var = tk.StringVar()
        tk.Entry(row1, textvariable=src_var, font=(FONT, 9), bg=C_CARD,
                 fg=C_TEXT, relief="flat").pack(side="left", fill="x",
                                               expand=True, padx=(0, 6))

        def pick():
            d = filedialog.askdirectory(parent=win)
            if d:
                src_var.set(os.path.normpath(d))
                if not dst_var.get().strip():
                    dst_var.set(os.path.basename(d))

        self._mk_btn(row1, _t("g038"), pick, "#607d8b",
                     width=None).pack(side="left")

        row2 = tk.Frame(win, bg=C_BG)
        row2.pack(fill="x", padx=16, pady=3)
        tk.Label(row2, text=_t("g373"), bg=C_BG, fg=C_TEXT,
                 font=(FONT, 9), width=8, anchor="w").pack(side="left")
        dst_var = tk.StringVar()
        tk.Entry(row2, textvariable=dst_var, font=(FONT, 9), bg=C_CARD,
                 fg=C_TEXT, relief="flat").pack(side="left", fill="x",
                                               expand=True)
        tk.Label(row2, text=_t("g380"), bg=C_BG, fg=C_GRAY,
                 font=(FONT, 8)).pack(side="left", padx=(6, 0))

        pbar = ttk.Progressbar(win, maximum=1000)
        pbar.pack(fill="x", padx=16, pady=(14, 4))
        lbl = tk.Label(win, text="", bg=C_BG, fg=C_SUB, font=(FONT, 8),
                       anchor="w", justify="left", wraplength=600)
        lbl.pack(fill="x", padx=16)

        # ---- 常用任务：存 / 取 / 删
        def jobs_list():
            return [j for j in (self.cfg.get("mirror_jobs") or [])
                    if isinstance(j, dict) and j.get("src")]

        def job_text(j):
            name = HIST.disp_name(j.get("src")) or j.get("src") or ""
            dst = j.get("dst") or ""
            if dst and dst != name:
                return "%s  →  %s" % (name, dst)
            return name or dst          # 同名时别写成 "X → X"，像出了 bug

        def refresh_jobs(sel=None):
            js = jobs_list()
            vals = [job_text(j) for j in js]
            cb["values"] = vals
            if sel is not None and 0 <= sel < len(js):
                job_var.set(vals[sel])
                cb.current(sel)
            elif vals and job_var.get() in vals:
                pass                     # 还指着一条有效记录，别去动它
            elif vals:
                # 空着会让人以为这里没东西：先显示最近一条，
                # 但不自动填进输入框 —— 用户点了才算数
                job_var.set(vals[0])
                cb.current(0)
            else:
                job_var.set("")          # 没有任何收藏：清空即可（current(-1) 会报错）

        def on_pick(_e=None):
            i = cb.current()
            js = jobs_list()
            if not (0 <= i < len(js)):
                return
            src_var.set(js[i].get("src") or "")
            dst_var.set(js[i].get("dst") or "")
            if not os.path.isdir(src_var.get()):
                lbl.config(text=_t("g418"))

        def save_job():
            src = src_var.get().strip()
            dst = dst_var.get().strip().strip("/\\")
            if not src or not os.path.isdir(src):
                messagebox.showinfo(APP_NAME, _t("g378"), parent=win)
                return
            if not dst:
                dst = os.path.basename(src)
            key = (os.path.normcase(os.path.normpath(src)), dst)
            js = [j for j in jobs_list()
                  if (os.path.normcase(os.path.normpath(j.get("src") or "")),
                      j.get("dst") or "") != key]
            js.insert(0, {"src": os.path.normpath(src), "dst": dst,
                          "t": time.time()})
            self.cfg["mirror_jobs"] = js[:12]      # 再多也记不住，12 条够用
            save_cfg(self.cfg)
            refresh_jobs(0)
            lbl.config(text=_t("g421") % dst)

        def del_job():
            i = cb.current()
            js = jobs_list()
            if not (0 <= i < len(js)):
                return
            del js[i]
            self.cfg["mirror_jobs"] = js
            save_cfg(self.cfg)
            refresh_jobs()
            lbl.config(text="")

        cb.bind("<<ComboboxSelected>>", on_pick)
        b_save.config(command=save_job)
        b_del.config(command=del_job)
        refresh_jobs()

        bar = tk.Frame(win, bg=C_BG)
        bar.pack(fill="x", padx=16, pady=12)
        btn = self._mk_btn(bar, _t("g374"), None, C_GREEN, width=None)
        btn.pack(side="right")

        def start():
            src = src_var.get().strip()
            if not src or not os.path.isdir(src):
                messagebox.showinfo(APP_NAME, _t("g378"), parent=win)
                return
            if not self.peer_ip:
                messagebox.showinfo(APP_NAME, _t("g340"), parent=win)
                return
            dst = dst_var.get().strip().strip("/\\")
            if not dst:
                dst = os.path.basename(src)
            btn.config(state="disabled")
            lbl.config(text=_t("g375"))
            pbar["value"] = 0
            self._mirror_ui = (win, pbar, lbl, btn)
            self.mirror_cancel.clear()
            threading.Thread(target=self._mirror_worker,
                             args=(src, dst), daemon=True).start()

        btn.config(command=start)

        def on_close():
            self.mirror_cancel.set()
            self._mirror_win = None
            self._mirror_ui = None
            win.destroy()

        win.protocol("WM_DELETE_WINDOW", on_close)
        win.bind("<Escape>", lambda e: on_close())

    def _mirror_worker(self, src, dst_rel):
        try:
            files = []
            for cur, dirs, names in os.walk(src):
                dirs[:] = [d for d in dirs if not d.startswith(".")]
                for n in names:
                    if n.startswith(".l2p"):
                        continue
                    p = os.path.join(cur, n)
                    try:
                        st = os.stat(p)
                    except Exception:
                        continue
                    rel = os.path.relpath(p, src).replace(os.sep, "/")
                    files.append((p, rel, st.st_size, int(st.st_mtime)))
            if not files:
                self.events.put(("mirror_done", (0, 0, 0)))
                return

            cli = L.LinkClient(self.peer_ip, self.peer_port, self.key,
                               timeout=L.CONNECT_TIMEOUT).open()
            updated = 0
            skipped_n = 0
            try:
                # ---------------------------------------------------- 一、核对
                # 先逐个问对端「这个文件在不在、还是不是同大小同修改时间」。
                # 目的只有一个：让用户在开工之前知道这活有多大。
                # 不做这一步的话，进度条按总字节算，看起来永远在慢慢爬，
                # 分不清「已经在传」还是「大部分都会跳过」。
                todo = []
                need = 0
                for i, (p, rel, size, mtime) in enumerate(files, 1):
                    if self.mirror_cancel.is_set():
                        break
                    target = ("%s/%s" % (dst_rel, rel)) if dst_rel else rel
                    self.events.put(("mirror_scan", (i, len(files))))
                    try:
                        st = cli.stat(target)
                    except Exception:
                        st = {}
                    same = (st.get("t") == "stat" and st.get("exists")
                            and not st.get("is_dir")
                            and st.get("size") == size
                            and abs((st.get("mtime") or 0) - mtime) <= 2)
                    if same:
                        skipped_n += 1
                    else:
                        todo.append((p, target))
                        need += size
                if self.mirror_cancel.is_set():
                    self.events.put(("mirror_done", (0, skipped_n, 0)))
                    return
                self.events.put(("mirror_plan",
                                 (len(files), len(todo), need, skipped_n)))
                if not todo:
                    self.events.put(("mirror_done", (0, skipped_n, 0)))
                    return

                # ---------------------------------------------------- 二、传
                total = need
                sent_total = 0
                deep = bool(self.cfg.get("deep_verify"))
                for i, (p, target) in enumerate(todo, 1):
                    if self.mirror_cancel.is_set():
                        break
                    self.events.put(("mirror_file",
                                     (i, len(todo), os.path.basename(p))))
                    base = sent_total

                    def prog(d, t, spd, _b=base):
                        now = time.time()
                        if now - self.last_ui < 0.12 and d < t:
                            return
                        self.last_ui = now
                        self.events.put(("mirror_prog", (_b + d, total, spd)))

                    is_skipped, _sent, _f = cli.upload(
                        p, target, progress=prog,
                        cancel=self.mirror_cancel.is_set, deep_verify=deep,
                        # 镜像的语义就是"让对端和本地一致"，同名的必须覆盖。
                        # 不覆盖的话改动过的文件会被存成 xxx (2).txt，越同步越乱。
                        # 内容没变的文件在核对阶段已经排除，所以这个 overwrite
                        # 只在"确实改了"的时候才真的动到对端文件。
                        overwrite=True)
                    if is_skipped:
                        skipped_n += 1
                    else:
                        updated += 1
                    sent_total += os.path.getsize(p)
            finally:
                try:
                    cli.close()
                except Exception:
                    pass
            self.events.put(("mirror_done", (updated, skipped_n, need)))
        except Exception as e:
            self.events.put(("mirror_err", str(e)))

    def pick_files(self):
        ps = filedialog.askopenfilenames(title=_t("g101"), parent=self.root)
        if ps:
            self.add_paths(list(ps))

    def pick_folder(self):
        p = filedialog.askdirectory(title=_t("g102"), parent=self.root)
        if p:
            self.add_paths([p])

    def add_paths(self, paths):
        """加进待发清单，返回真正新增的项数（重复/不存在的会跳过）。"""
        if len(paths) > 1:
            self.lbl_status.config(text=_t("g103") % len(paths))
            try:
                self.root.update_idletasks()
            except Exception:
                pass
        added = 0
        for p in paths:
            p = os.path.normpath(p)
            if p in self.queue_paths:
                continue
            if not (os.path.isfile(p) or os.path.isdir(p)):
                continue
            self.queue_paths.append(p)
            added += 1
            name = os.path.basename(p.rstrip("\\/")) or p
            if os.path.isdir(p):
                n = 0
                sz = 0
                for root, dirs, files in os.walk(p):
                    for f in files:
                        n += 1
                        try:
                            sz += os.path.getsize(os.path.join(root, f))
                        except Exception:
                            pass
                self._tree_row(p, name + "\\", L.human_size(sz) + _t("g104") % n, "", "", _t("g105"))
            else:
                sz = os.path.getsize(p)
                self._tree_row(p, name, L.human_size(sz), "", "", _t("g105"))
        self._refresh_queue_summary()
        if added:
            self.lbl_status.config(text=_t("g106") % added)
        return added

    def _tree_row(self, keypath, name, size, prog, speed, state):
        if keypath in self.rows:
            iid = self.rows[keypath]
            self.tree.item(iid, values=(name, size, prog, speed, state))
            return iid
        iid = self.tree.insert("", "end", values=(name, size, prog, speed, state))
        self.rows[keypath] = iid
        return iid

    def clear_queue(self):
        if self.sending:
            messagebox.showinfo(APP_NAME, _t("g107"))
            return
        self.queue_paths = []
        self.rows = {}
        for i in self.tree.get_children():
            self.tree.delete(i)
        self._refresh_queue_summary()
        self.pbar["value"] = 0
        self.lbl_status.config(text=_t("g067"))

    def remove_selected(self):
        if self.sending:
            return
        for iid in self.tree.selection():
            for k, v in list(self.rows.items()):
                if v == iid:
                    if k in self.queue_paths:
                        self.queue_paths.remove(k)
                    del self.rows[k]
            self.tree.delete(iid)
        self._refresh_queue_summary()

    def on_tree_double(self, _e):
        sel = self.tree.selection()
        if not sel:
            return
        for k, v in self.rows.items():
            if v == sel[0]:
                # 双击：在文件管理器里把它选出来（Windows 是 /select，
                # Linux 是 nautilus --select，都做不到就打开父目录）
                P.reveal_path(k)
                break

    # ------------------------------------------------------------ 发送

    def start_send(self):
        if self.sending:
            return
        if not self.queue_paths:
            messagebox.showinfo(APP_NAME, _t("g108"))
            return
        if not self.peer_ip:
            messagebox.showinfo(APP_NAME, _t("g109"))
            return

        self.sending = True
        self.cancel_flag.clear()
        self.btn_send.config(state="disabled")
        self.btn_pull.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.pbar["value"] = 0
        self.last_ui = 0.0
        self.total_bytes = 0
        self.done_bytes = 0

        targets = L.collect_targets(self.queue_paths)

        self._prepare_rows(targets)

        self._send_t0 = time.time()
        threading.Thread(target=self._send_worker, args=(targets,), daemon=True).start()

    def _prepare_rows(self, targets):
        """
        建映射：发送时用的相对路径 -> 清单里对应的那一行。

        以前这里没映射，进度/速度/状态列全都更新不到（rows 的键是本地绝对
        路径，而进度回调给的是相对路径），传完清单还显示"待发送"。
        """
        self.rel_rows = {}
        self.item_total = {}
        self.item_done = {}
        self.item_rels = {}
        self.item_ok = {}
        self.item_files_total = {}
        self.item_files_done = {}
        for local, rel in targets:
            top = self._top_of(local)
            iid = self.rows.get(top) if top else None
            if not iid:
                continue
            self.rel_rows[rel] = iid
            self.item_rels.setdefault(iid, []).append(rel)
            self.item_ok.setdefault(iid, set())
            self.item_files_total[iid] = self.item_files_total.get(iid, 0) + 1
            try:
                self.item_total[iid] = self.item_total.get(iid, 0) + os.path.getsize(local)
            except Exception:
                pass
            vals = list(self.tree.item(iid, "values"))
            vals[2], vals[3], vals[4] = "0%", "", _t("g110")
            self.tree.item(iid, values=vals)

    def _top_of(self, local):
        """本地文件属于清单里的哪一项（文件本身，或它所属的文件夹）。"""
        lp = os.path.normpath(local)
        for p in self.queue_paths:
            np = os.path.normpath(p)
            if lp == np:
                return p
            if os.path.isdir(np):
                try:
                    if os.path.commonpath([lp, np]) == np:
                        return p
                except ValueError:
                    pass
        return None

    def _send_worker(self, targets):
        total_all = sum(os.path.getsize(p) for p, _ in targets if os.path.isfile(p))
        self.total_bytes = total_all
        done_all = 0
        skipped_n = 0
        failed = []
        deep = bool(self.cfg.get("deep_verify"))

        try:
            cli = L.LinkClient(self.peer_ip, self.peer_port, self.key,
                               timeout=L.CONNECT_TIMEOUT).open()
        except L.AuthError:
            self.events.put(("send_end", (0, 0, [], _t("g111"))))
            return
        except Exception as e:
            self.events.put(("send_end",
                             (0, 0, [], L.conn_error_text(e, self.peer_ip,
                                                          self.peer_port))))
            return

        self.peer_root = cli.peer_root or ""
        self.events.put(("peer_root", self.peer_root))
        self.events.put(("status", _t("g113") % (cli.peer_name or self.peer_ip)))

        try:
            for idx, (local, rel) in enumerate(targets):
                if self.cancel_flag.is_set():
                    break
                try:
                    size = os.path.getsize(local)
                except Exception:
                    continue

                state = ("file_start", (rel, idx + 1, len(targets), size))
                self.events.put(state)

                base = done_all

                def prog(d, t, spd, _base=base, _size=size):
                    now = time.time()
                    if now - self.last_ui < 0.10 and d < t:
                        return
                    self.last_ui = now
                    self.done_bytes = _base + d
                    self.events.put(("progress", (rel, d, t, spd)))

                try:
                    vstate = {"last": -1}

                    def vprog(d, t, _rel=rel):
                        # 深校验要先把整个文件读一遍，不给进度用户会以为卡死
                        if not t:
                            return
                        pct = int(d * 100 / t)
                        if pct >= vstate["last"] + 5 or pct >= 100:
                            vstate["last"] = pct
                            self.events.put(("status", _t("g334") % pct))

                    skipped, sent, final_rel = cli.upload(
                        local, rel, progress=prog,
                        cancel=self.cancel_flag.is_set,
                        deep_verify=deep, verify_progress=vprog)
                    if skipped:
                        skipped_n += 1
                        self.events.put(("file_done", (rel, size, _t("g114"), 0)))
                    elif final_rel and final_rel.replace("\\", "/") != rel.replace("\\", "/"):
                        # 对端有同名文件，被改名了。不说清楚用户去接收目录会找不到。
                        self.events.put(("file_done", (
                            rel, size,
                            _t("g336") % os.path.basename(final_rel.replace("\\", "/")),
                            0)))
                    else:
                        self.events.put(("file_done", (rel, size, _t("g115"), 0)))
                    done_all += size
                except InterruptedError:
                    self.events.put(("file_done", (rel, 0, _t("g116"), 0)))
                    break
                except Exception as e:
                    failed.append((rel, str(e)))
                    self.events.put(("file_done", (rel, size, _t("g117"), 0)))
                    done_all += size
        finally:
            try:
                cli.close()
            except Exception:
                pass

        self.events.put(("send_end", (done_all, skipped_n, failed, None)))

    def _send_done(self, done, skipped, failed, err):
        self.sending = False
        self.btn_send.config(state="normal")
        self.btn_pull.config(state="normal")
        self.btn_stop.config(state="disabled")

        if err:
            self.lbl_status.config(text=err)
            messagebox.showerror(APP_NAME, err)
            return

        secs = max(0.001, time.time() - self._send_t0) if self._send_t0 else 0.0
        avg = (done / secs / 1048576.0) if secs else 0.0

        items = []
        for p in list(self.queue_paths):
            iid = self.rows.get(p)
            if not iid:
                continue
            vals = self.tree.item(iid, "values")
            items.append({
                "name": os.path.basename(p.rstrip("\\/")) + ("\\" if os.path.isdir(p) else ""),
                "size": str(vals[1]),
                "state": str(vals[4]),
            })

        self.last_result = {
            "peer": self.peer_name or self.peer_ip,
            "addr": "%s:%s" % (self.peer_ip, self.peer_port),
            "root": self.peer_root or "",
            "items": items,
            "bytes": done,
            "secs": secs,
            "avg": avg,
            "skipped": skipped,
            "failed": list(failed or []),
            "when": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.btn_detail.config(state="normal")

        short = _t("g118") % (
            len(items), (self.peer_name or self.peer_ip),
            L.human_size(done), secs, avg)
        if self.peer_root:
            short += _t("g119") % self.peer_root
        if skipped:
            short += _t("g120") % skipped
        if failed:
            short = _t("g121") % (short, len(failed))

        if failed:
            self.lbl_status.config(text=short)
            detail = "\n".join(_t("g122") % (n, e) for n, e in failed[:8])
            messagebox.showwarning(
                APP_NAME, short + _t("g123") + detail +
                _t("g124"))
        else:
            self.pbar["value"] = 1000
            self.lbl_status.config(text=short)

        # 缩到托盘时用户看不见进度条，没个动静就完全不知道传完了
        if not failed and not self.root.winfo_viewable():
            self._notify(self.peer_name or self.peer_ip, short[:120])

        # 落一条历史：这是「上次那个失败的文件叫什么」的唯一答案
        try:
            HIST.append(HIST.make_entry(
                "out",
                peer=self.peer_name or self.peer_ip,
                ip=self.peer_ip, port=int(self.peer_port or 0),
                files=len(items), nbytes=done,
                ok=max(0, len(items) - len(failed or []) - int(skipped or 0)),
                fail=len(failed or []), skip=skipped,
                root=self.peer_root,
                src=[p for p in list(self.queue_paths)],
                names=[HIST.disp_name(p) for p in self.queue_paths],
                bad=[[n, e] for n, e in (failed or [])]))
        except Exception:
            pass

        self._remember_peer()

        # 传完就把已经成功的条目从清单里移走，只留失败/取消的
        self._prune_finished()

    def _remember_peer(self):
        """记下这次连的是谁，下次启动直接连它，不用再扫一遍。"""
        if not self.peer_ip:
            return
        d = {"ip": self.peer_ip, "port": int(self.peer_port),
             "name": self.peer_name or ""}
        if d != self.last_peer:
            self.last_peer = d
            self.cfg["last_peer"] = d
            save_cfg(self.cfg)

    def _try_last_peer(self):
        """
        启动时自动连上次那台。

        两台固定搭配是常态，每次都重新点设备、等扫描纯属浪费。
        连不上就安静放弃，不弹窗打扰。
        """
        if self.peer_ip:
            return
        lp = self.last_peer or {}
        ip = lp.get("ip")
        if not ip:
            return
        port = int(lp.get("port") or L.TCP_PORT)

        def work():
            try:
                cli = L.LinkClient(ip, port, self.key, timeout=L.CONNECT_TIMEOUT).open()
                name = cli.peer_name or lp.get("name") or ip
                root = cli.peer_root
                cli.close()
                self.events.put(("peer_ok", (ip, port, name)))
                if root:
                    self.events.put(("peer_root", root))
            except Exception:
                pass

        threading.Thread(target=work, daemon=True).start()

    def _prune_finished(self):
        """已全部成功的清单项自动移走；有失败/取消的留着，方便直接重发。"""
        if self.sending:
            return
        gone_ids = []
        for p in list(self.queue_paths):
            iid = self.rows.get(p)
            if not iid:
                self.queue_paths.remove(p)
                continue
            rels = self.item_rels.get(iid) or []
            ok = self.item_ok.get(iid, set())
            if rels and len(ok) >= len(rels):
                self.queue_paths.remove(p)
                self.rows.pop(p, None)
                for r in rels:
                    self.rel_rows.pop(r, None)
                self.tree.delete(iid)
                gone_ids.append(iid)
        for iid in gone_ids:
            for d in (self.item_total, self.item_done, self.item_rels,
                      self.item_ok, self.item_files_total, self.item_files_done):
                d.pop(iid, None)
        if gone_ids:
            self._refresh_queue_summary()
            if not self.queue_paths:
                self.lbl_qsum.config(text=_t("g125"))

    def show_result_detail(self):
        """上一次传输的完整结果：发到哪台机的哪个目录、都发了些什么。"""
        r = self.last_result
        if not r:
            messagebox.showinfo(APP_NAME, _t("g126"),
                                parent=self.root)
            return

        L_ = []
        L_.append(_t("g127") % (r["peer"], r["addr"]))
        L_.append(_t("g128") % (r["root"] or _t("g129")))
        L_.append(_t("g130") % r["when"])
        L_.append("")
        L_.append(_t("g131") % (
            len(r["items"]), L.human_size(r["bytes"]), r["secs"], r["avg"]))
        L_.append("")
        L_.append(_t("g132"))
        L_.append("-" * 62)
        for it in r["items"]:
            L_.append("  %-34s %16s  %s" % (it["name"], it["size"], it["state"]))
        if r["skipped"]:
            L_.append("")
            L_.append(_t("g133") % r["skipped"])
        L_.append("")
        L_.append(_t("g134"))
        if r["root"]:
            L_.append(_t("g135"))
        L_.append("-" * 62)
        for it in r["items"]:
            nm = it["name"].rstrip("\\/")
            full = os.path.join(r["root"], nm) if r["root"] else nm
            L_.append("  %s%s" % (full, _t("g136") if it["name"].endswith("\\") else ""))
        L_.append("")
        if r["failed"]:
            L_.append(_t("g137") % len(r["failed"]))
            L_.append("-" * 62)
            for n, e in r["failed"]:
                L_.append(_t("g138") % (n, e))
        else:
            L_.append(_t("g139"))
        text = "\n".join(L_)

        win = tk.Toplevel(self.root)
        win.title(_t("g140"))
        win.configure(bg=C_BG)
        # 小屏上别超出可用区域：宽度、高度都按屏幕兜一下
        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        win.geometry("%dx%d" % (min(780, max(560, sw - 80)),
                                min(500, max(360, sh - 160))))
        win.minsize(560, 340)
        win.transient(self.root)

        # 先占底部按钮栏，再放正文 —— 否则 expand 的 Text 会把按钮挤出去，
        # 只剩半截露在窗口边沿（v1.2.2 在小屏机器上的样子）。
        bar = tk.Frame(win, bg=C_BG)
        bar.pack(side="bottom", fill="x", pady=8)
        btn_box = tk.Frame(bar, bg=C_BG)
        btn_box.pack(fill="x", padx=12)

        txt = tk.Text(win, wrap="none", bg="#fbfcfd", fg=C_TEXT,
                      font=(FONT, 9), relief="flat", padx=12, pady=10)
        sb = ttk.Scrollbar(win, orient="vertical", command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        txt.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=(10, 0))
        txt.insert("1.0", text)
        txt.config(state="disabled")

        def copy_all():
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.lbl_status.config(text=_t("g141"))

        btn_close = self._mk_btn(btn_box, _t("g142"), win.destroy, "#78909c", width=8)
        btn_close.pack(side="right")
        self._mk_btn(btn_box, _t("g143"), copy_all, "#546e7a", width=10).pack(
            side="left")
        if r.get("root"):
            self._mk_btn(btn_box, _t("g144"),
                         lambda: self.open_peer_dir(r), C_GREEN,
                         width=None).pack(side="left", padx=(10, 0))
        win.bind("<Escape>", lambda e: win.destroy())
        win.after(30, lambda: self._fit_detail(win, txt, btn_box))

    def _fit_detail(self, win, txt, btn_box):
        """
        兜底调整：某些 DPI 缩放下按钮会比窗口宽 / 正文被压没，
        这里按实际所需尺寸把窗口撑开一点（不超出屏幕）。
        """
        try:
            win.update_idletasks()
            sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
            need_w = btn_box.winfo_reqwidth() + 48
            w, h = win.winfo_width(), win.winfo_height()
            if need_w > w:
                w = min(need_w, sw - 40)
            if txt.winfo_height() < 80:
                h = min(h + (80 - txt.winfo_height()), sh - 80)
            if (w, h) != (win.winfo_width(), win.winfo_height()):
                win.geometry("%dx%d" % (w, h))
                win.update_idletasks()
        except Exception:
            pass

    # ------------------------------------------------------------ 传输历史

    def history_dialog(self):
        """
        v1.6.0：传输历史。只读历史文件，不碰当前队列。

        v1.6.1：加了「内容」列。只有「2 个文件 17 MB」这种记录没法回答
        「上次那个装驱动的包到底传没传」—— 用户要的是名字。
        """
        win = tk.Toplevel(self.root)
        win.title(_t("g387"))
        win.geometry("960x560")
        win.minsize(780, 440)
        win.configure(bg=C_BG)
        win.transient(self.root)

        cols = ("when", "dir", "name", "peer", "files", "size", "res")
        heads = (_t("g388"), _t("g389"), _t("g410"), _t("g390"),
                 _t("g391"), _t("g392"), _t("g393"))
        widths = (126, 54, 300, 196, 46, 86, 138)
        tv = ttk.Treeview(win, columns=cols, show="headings", height=14)
        for c, h, w in zip(cols, heads, widths):
            tv.heading(c, text=h)
            tv.column(c, width=w, anchor="w", stretch=(c == "name"))
        tv.pack(fill="both", expand=True, padx=14, pady=(14, 6))

        by_id = {}

        def fmt_dir(e):
            return _t("g394") if e.get("dir") == "out" else _t("g395")

        def fmt_peer(e):
            name = (e.get("peer") or "").strip()
            ip = (e.get("ip") or "").strip()
            if name and ip and name != ip:
                return "%s (%s)" % (name, ip)
            return name or ip or "—"

        def fmt_name(e):
            names = HIST.entry_names(e)
            if not names:
                return "—"
            if len(names) == 1:
                return names[0]
            return _t("g407") % (names[0], len(names))

        def fmt_res(e):
            if e.get("err"):
                return e["err"][:30]
            ok, fail = int(e.get("ok") or 0), int(e.get("fail") or 0)
            if fail:
                return _t("g396") % (ok, fail)
            return _t("g397") % ok

        def fill():
            tv.delete(*tv.get_children())
            by_id.clear()
            rows = HIST.load(limit=300)
            if not rows:
                tv.insert("", "end", values=("", "", _t("g398"), "", "", "", ""))
                return
            for e in rows:
                ts = time.strftime("%m-%d %H:%M:%S",
                                   time.localtime(float(e.get("t") or 0)))
                iid = tv.insert("", "end", values=(
                    ts, fmt_dir(e), fmt_name(e), fmt_peer(e),
                    int(e.get("files") or 0),
                    L.human_size(int(e.get("bytes") or 0)), fmt_res(e)))
                by_id[iid] = e

        def cur_entry():
            sel = tv.selection()
            return by_id.get(sel[0]) if sel else None

        def resend(e):
            if e.get("dir") != "out":
                messagebox.showinfo(APP_NAME, _t("g399"), parent=win)
                return False
            src = [p for p in (e.get("src") or []) if p and os.path.exists(p)]
            if not src:
                messagebox.showinfo(APP_NAME, _t("g399") + "\n" + _t("g400"),
                                    parent=win)
                return False
            if e.get("ip"):
                self.set_peer(e["ip"], int(e.get("port") or L.TCP_PORT),
                              e.get("peer") or "")
            self.add_paths(src)
            self.lbl_status.config(text=_t("g401") % len(src))
            return True

        def do_resend():
            e = cur_entry()
            if not e:
                return
            if resend(e):
                win.destroy()
                if self.peer_ip and not self.sending:
                    self.start_send()

        def open_root(e):
            path = (e or {}).get("root") or self.cfg.get("recv_root") or ""
            if path and os.path.isdir(path):
                if P.open_path(path):
                    return
            self.open_recv_root()

        def do_open():
            e = cur_entry()
            if e:
                open_root(e)
            else:
                self.open_recv_root()

        def do_clear():
            if not messagebox.askyesno(APP_NAME, _t("g402"), parent=win):
                return
            HIST.clear()
            fill()

        def show_detail():
            e = cur_entry()
            if e:
                self._hist_detail(win, e, resend, open_root)

        fill()

        bar = tk.Frame(win, bg=C_BG)
        bar.pack(fill="x", padx=14, pady=(0, 12))
        self._mk_btn(bar, _t("g408"), show_detail, "#455a64",
                     width=None).pack(side="left")
        self._mk_btn(bar, _t("g403"), do_resend, C_BLUE,
                     width=None).pack(side="left", padx=6)
        self._mk_btn(bar, _t("g404"), do_open, C_GRAY,
                     width=None).pack(side="left")
        self._mk_btn(bar, _t("g405"), do_clear, C_RED,
                     width=None).pack(side="left", padx=6)
        self._mk_btn(bar, _t("g406"), win.destroy, C_GRAY,
                     width=None).pack(side="right")
        tk.Label(bar, text=_t("g413"), bg=C_BG, fg=C_GRAY,
                 font=(FONT, 8)).pack(side="right", padx=(0, 10))

        tv.bind("<Double-1>", lambda _e: show_detail())
        tv.bind("<Return>", lambda _e: show_detail())

    def _hist_detail(self, parent, e, resend_cb, open_cb):
        """一条历史的详情：到底传了哪些文件、哪个失败了、为什么。"""
        d = tk.Toplevel(parent)
        d.title(_t("g409"))
        d.geometry("700x540")
        d.minsize(560, 400)
        d.configure(bg=C_BG)
        d.transient(parent)

        names = HIST.entry_names(e)
        bad = {}
        for b in (e.get("bad") or []):
            if b:
                bad[str(b[0])] = str(b[1]) if len(b) > 1 else ""

        # ---- 抬头几行：时间 / 方向 / 对端 / 大小 / 结果
        head = tk.Frame(d, bg=C_BG)
        head.pack(fill="x", padx=16, pady=(14, 6))
        ts = time.strftime("%Y-%m-%d %H:%M:%S",
                           time.localtime(float(e.get("t") or 0)))
        peer = (e.get("peer") or "").strip()
        ip = (e.get("ip") or "").strip()
        if peer and ip and peer != ip:
            fmt = "%s (%s)" % (peer, ip)
        else:
            fmt = peer or ip or "—"
        ok, fail = int(e.get("ok") or 0), int(e.get("fail") or 0)
        res = (_t("g396") % (ok, fail)) if fail else (_t("g397") % ok)
        if e.get("err"):
            res = str(e["err"])[:60]
        rows = (
            (_t("g388"), ts),
            (_t("g389"), _t("g394") if e.get("dir") == "out" else _t("g395")),
            (_t("g390"), fmt),
            (_t("g392"), L.human_size(int(e.get("bytes") or 0))),
            (_t("g393"), res),
        )
        if e.get("root"):
            rows += (((_t("g415") if e.get("dir") == "in" else _t("g414")),
                      str(e["root"])[:80]),)
        for r, (k, v) in enumerate(rows):
            tk.Label(head, text=k, bg=C_BG, fg=C_SUB, font=(FONT, 9),
                     width=8, anchor="w").grid(row=r, column=0, sticky="w")
            tk.Label(head, text=v, bg=C_BG,
                     fg=(C_RED if (k == _t("g393") and fail) else C_TEXT),
                     font=(FONT, 9), anchor="w",
                     justify="left").grid(row=r, column=1, sticky="w")

        # ---- 文件清单
        cap = _t("g411") % (len(names) or int(e.get("files") or 0))
        if fail:
            cap += "  ·  " + (_t("g412") % fail)
        tk.Label(d, text=cap, bg=C_BG, fg=C_SUB, font=(FONT, 9),
                 anchor="w").pack(fill="x", padx=16, pady=(8, 2))

        box = tk.Frame(d, bg=C_BG)
        box.pack(fill="both", expand=True, padx=16)
        txt = tk.Text(box, bg=C_CARD, fg=C_TEXT, font=(FONT, 9), wrap="word",
                      relief="flat", padx=8, pady=6, height=10)
        sb = ttk.Scrollbar(box, orient="vertical", command=txt.yview)
        txt.config(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        txt.pack(side="left", fill="both", expand=True)
        txt.tag_config("ok", foreground=C_TEXT)
        txt.tag_config("bad", foreground=C_RED)
        txt.tag_config("why", foreground=C_SUB)

        if names:
            for n in names:
                if n in bad:
                    txt.insert("end", "✗  " + n + "\n", "bad")
                    if bad[n]:
                        txt.insert("end", "     " + bad[n] + "\n", "why")
                else:
                    txt.insert("end", "✓  " + n + "\n", "ok")
            more = int(e.get("files") or 0) - len(names)
            if more > 0:
                txt.insert("end", _t("g416") % (more, len(names)) + "\n", "why")
        else:
            for p in (e.get("src") or []):
                if p:
                    txt.insert("end", "   " + str(p) + "\n", "ok")
            if not (e.get("src") or []):
                txt.insert("end", _t("g398") + "\n", "why")
        txt.config(state="disabled")

        bar = tk.Frame(d, bg=C_BG)
        bar.pack(fill="x", padx=16, pady=12)

        def do_resend():
            if resend_cb(e):
                d.destroy()

        self._mk_btn(bar, _t("g431"), do_resend, C_BLUE,
                     width=None).pack(side="left")
        self._mk_btn(bar, _t("g404"), lambda: open_cb(e), C_GRAY,
                     width=None).pack(side="left", padx=6)
        self._mk_btn(bar, _t("g406"), d.destroy, C_GRAY,
                     width=None).pack(side="right")
        d.bind("<Escape>", lambda _e: d.destroy())

    def open_peer_dir(self, r=None):
        """
        让对端在**它自己的屏幕**上打开接收目录。
        走 LanSplice 自己的加密通道，不需要开文件共享、不用输账号密码。
        """
        r = r if isinstance(r, dict) else self.last_result
        if not r:
            return
        name = r.get("peer") or ""
        addr = r.get("addr") or ""
        if ":" in addr:
            ip, port_s = addr.rsplit(":", 1)
        else:
            ip, port_s = addr, str(self.peer_port or "")
        try:
            port = int(port_s)
        except Exception:
            port = 0
        if not ip or not port:
            messagebox.showinfo(APP_NAME, _t("g145"),
                                parent=self.root)
            return
        name = name or ip
        # 先试上次传输的那个地址；对端可能换了 IP（DHCP 续租/拔插网线），
        # 再退到当前列表里选中的设备地址。
        cands = [(ip, port)]
        try:
            cur = (self.peer_ip or "", int(self.peer_port or 0))
        except Exception:
            cur = ("", 0)
        if cur[0] and cur[1] and cur != (ip, port):
            cands.append(cur)
        self.lbl_status.config(text=_t("g146") % name)

        def work():
            err = ""
            for a_ip, a_port in cands:
                cli = None
                try:
                    cli = L.LinkClient(a_ip, a_port, self.key, timeout=L.CONNECT_TIMEOUT).open()
                    path = cli.open_dir("")
                    self.events.put(("open_peer_ok", (name, path)))
                    return
                except Exception as e:
                    err = str(e)
                finally:
                    if cli:
                        try:
                            cli.close()
                        except Exception:
                            pass
            self.events.put(("open_peer_err", (name, err)))

        threading.Thread(target=work, daemon=True).start()

    # ------------------------------------------------------------ 防火墙状态

    def _refresh_fw_status(self):
        if not P.IS_WIN:
            # Linux 上没什么可「检测」的：读规则要 root，工具各家不同。
            # 直接把该说的话摆在状态条上，不绕线程也不显示「检测中…」——
            # 那个「检测中」在 Linux 上永远转不出结果。
            tool = P.firewall_tool()
            txt = (_t("g432") % tool) if tool else _t("g433")
            self.lbl_fw.config(text="● " + txt, fg=C_BLUE)
            self.btn_fw.config(text=_t("g433"))
            return
        self.lbl_fw.config(text=_t("g041"), fg=C_SUB)
        threading.Thread(target=self._fw_status_worker, daemon=True).start()

    def _fw_status_worker(self):
        # Linux：不跑 PowerShell，也不假装知道防火墙开没开。
        # 只有 root 才能读规则，各发行版工具还不一样 ——
        # 与其显示一个绿点骗人，不如老老实实说「请手动放行」。
        if not P.IS_WIN:
            tool = P.firewall_tool()
            if tool:
                self.events.put(("fw_status", ("manual", _t("g432") % tool)))
            else:
                self.events.put(("fw_status", ("manual", _t("g433"))))
            return
        # 规则查询本身要 3~4 秒（PowerShell 启动 + 遍历规则），
        # 所以把网络类别和规则合并成一次调用，别让状态灯一直停在"检测中"。
        # PROG 那两行是 v1.6.0 加的：只有「规则里绑的 exe」才说明这版被放行。
        script = (
            "$o=@();"
            "Get-NetConnectionProfile -ErrorAction SilentlyContinue | "
            "ForEach-Object { $o += 'CAT|' + $_.NetworkCategory };"
            "Get-NetFirewallRule -DisplayName 'LanSplice*' -ErrorAction SilentlyContinue | "
            "ForEach-Object { $o += 'RULE|' + $_.DisplayName + '|' + $_.Enabled;"
            "  $pr = ($_ | Get-NetFirewallApplicationFilter).Program;"
            "  $o += 'PROG|' + $_.DisplayName + '|' + $pr };"
            "if ($o.Count -eq 0) { 'NONE' } else { $o }")
        try:
            rc, out, err = self._ps(script, timeout=25)
            # 必须和 _fw_script 里 -Program 用的那个路径完全一致：
            # 打包后是 exe 自己，源码运行时是 python.exe
            try:
                want = os.path.abspath(sys.executable)
            except Exception:
                want = ""
            alive, pub, stale = parse_fw_status(out, want)
            if stale:
                self.events.put(("fw_status", ("stale", _t("g383"))))
            elif alive:
                txt = _t("g147") + (_t("g148") if pub else "")
                self.events.put(("fw_status", (True, txt)))
            else:
                self.events.put(("fw_status", (False, _t("g149"))))
        except Exception:
            self.events.put(("fw_status", (False, _t("g150"))))

    def stop_send(self):
        if self.sending:
            self.cancel_flag.set()
            self.lbl_status.config(text=_t("g151"))

    # ------------------------------------------------------------ 取回

    def pull_dialog(self):
        if not self.peer_ip:
            messagebox.showinfo(APP_NAME, _t("g109"))
            return
        rel = simpledialog.askstring(
            _t("g152"),
            _t("g153"),
            parent=self.root)
        if not rel:
            return
        self.lbl_status.config(text=_t("g154"))

        def work():
            try:
                cli = L.LinkClient(self.peer_ip, self.peer_port, self.key, timeout=L.CONNECT_TIMEOUT).open()
                st = cli.stat(rel)
                cli.close()
                self.events.put(("pull_stat", (rel, st)))
            except Exception as e:
                self.events.put(("pull_stat", (rel, {"t": "error", "msg": str(e)})))
        threading.Thread(target=work, daemon=True).start()

    def _on_pull_stat(self, rel, st):
        if st.get("t") == "error":
            messagebox.showerror(APP_NAME, st.get("msg"))
            self.lbl_status.config(text=_t("g067"))
            return
        if not st.get("exists"):
            messagebox.showinfo(APP_NAME, _t("g155") % rel)
            self.lbl_status.config(text=_t("g067"))
            return
        if st.get("is_dir"):
            messagebox.showinfo(
                APP_NAME,
                _t("g156") % rel)
            self.lbl_status.config(text=_t("g067"))
            return
        dst = filedialog.asksaveasfilename(
            title=_t("g157"), initialfile=os.path.basename(rel), parent=self.root)
        if not dst:
            return
        self.sending = True
        self.btn_stop.config(state="normal")
        threading.Thread(target=self._pull_worker, args=(rel, dst), daemon=True).start()

    def _pull_worker(self, rel, dst):
        try:
            cli = L.LinkClient(self.peer_ip, self.peer_port, self.key, timeout=L.CONNECT_TIMEOUT).open()
        except Exception as e:
            self.events.put(("pull_end", str(e)))
            return
        self.last_ui = 0.0

        def prog(d, t, spd):
            now = time.time()
            if now - self.last_ui < 0.10 and d < t:
                return
            self.last_ui = now
            self.events.put(("progress", (rel, d, t, spd)))

        try:
            self.events.put(("file_start", (rel, 1, 1, 0)))
            cli.download(rel, dst, progress=prog, cancel=self.cancel_flag.is_set)
            self.events.put(("file_done", (rel, os.path.getsize(dst), _t("g115"), 0)))
            cli.close()
            self.events.put(("pull_end", None))
        except Exception as e:
            try:
                cli.close()
            except Exception:
                pass
            self.events.put(("pull_end", str(e)))

    # ------------------------------------------------------------ 接收端

    def _start_server(self, force=False, retry=0):
        if not force and not self.cfg.get("auto_server", True):
            self.lbl_status.config(text=_t("g158"))
            return
        if self.server and self.server.running:
            return
        recv = self.cfg["recv_root"]
        try:
            os.makedirs(recv, exist_ok=True)
        except Exception as e:
            messagebox.showerror(APP_NAME, _t("g159") % e)
            return
        self.server = L.PeerServer(
            recv, self.key, port=int(self.cfg["tcp_port"]),
            log=lambda s: self.events.put(("log", s)),
            notify=lambda k, d: self.events.put(("recv", (k, d))),
            allow_discovery=bool(self.cfg.get("discovery", True)),
        )
        self.server.start_server()
        self.root.after(500, lambda: self._after_server(retry))

    def _after_server(self, retry=0):
        s = self.server
        if s and s.error:
            err = str(s.error)
            # 10048 = 端口已占用。常见于另一个窗口还开着（旧版没关），
            # 或刚重启过接收端、上一个 socket 还没被系统回收。
            busy = ("10048" in err or "in use" in err.lower()
                    or _t("g160") in err or _t("g161") in err)
            if busy and retry < 3:
                self.lbl_status.config(
                    text=_t("g162")
                         % (int(self.cfg["tcp_port"]), 2, retry + 1))
                self.server = None
                self.root.after(
                    2000,
                    lambda: self._start_server(force=True, retry=retry + 1))
                return
            messagebox.showwarning(
                APP_NAME,
                _t("g163")
                % (err,
                   _t("g164")
                   if busy else
                   _t("g165")))
        self._refresh_self()

    def _restart_server(self):
        """
        关闭并重新创建接收端。

        为什么必须这么做：实测发现，改完防火墙规则（或把网络类别
        从「公用」改成「专用」）之后，**已经存在的监听 socket 不会
        自动套用新规则**，表现就是"放行了还是连不上，关掉程序重开才好"。
        重建一次监听，新规则立刻生效。
        """
        try:
            if self.server:
                self.server.stop_server()
        except Exception:
            pass
        self.server = None
        time.sleep(0.4)          # 让旧 socket 真正释放，避免 10048
        try:
            self._start_server(force=True)
            return True
        except Exception:
            return False

    def toggle_server(self):
        if self.server and self.server.running:
            self.server.stop_server()
            self.server = None
            self.lbl_status.config(text=_t("g072"))
        else:
            self._start_server()
            self.lbl_status.config(text=_t("g166"))
        self.root.after(400, self._refresh_self)

    def open_recv_root(self):
        os.makedirs(self.cfg["recv_root"], exist_ok=True)
        P.open_path(self.cfg["recv_root"])

    # ------------------------------------------------------------ 配对码

    def show_code(self):
        code = L.key_to_code(self.key)
        messagebox.showinfo(
            _t("g044"),
            _t("g167") % code)
        self.copy_code()

    def copy_code(self):
        code = L.key_to_code(self.key)
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(code)
            self.lbl_status.config(text=_t("g168"))
        except Exception:
            pass

    def enter_code(self):
        v = simpledialog.askstring(
            _t("g046"),
            _t("g169"),
            parent=self.root)
        if not v:
            return
        try:
            key = L.code_to_key(v)
        except ValueError as e:
            messagebox.showerror(APP_NAME, str(e))
            return
        self.key = key
        self.cfg["pair_key"] = base64.b64encode(key).decode()
        save_cfg(self.cfg)
        self._refresh_code()
        # 重启接收端，让新码生效
        if self.server and self.server.running:
            self.server.stop_server()
            self.server = None
            self.root.after(300, self._start_server)
        messagebox.showinfo(APP_NAME, _t("g170"))
        if self.peer_ip:
            self.test_peer()

    def regen_code(self):
        if not messagebox.askyesno(
                APP_NAME, _t("g171")):
            return
        self.key = L.new_pair_key()
        self.cfg["pair_key"] = base64.b64encode(self.key).decode()
        save_cfg(self.cfg)
        self._refresh_code()
        if self.server and self.server.running:
            self.server.stop_server()
            self.server = None
            self.root.after(300, self._start_server)
        self.show_code()

    # ------------------------------------------------------------ 设置 / 安全

    def set_recv_root(self):
        p = filedialog.askdirectory(title=_t("g172"),
                                    initialdir=self.cfg["recv_root"], parent=self.root)
        if not p:
            return
        if p.rstrip("\\").upper() in ("C:", "C:\\WINDOWS", "C:\\WINDOWS\\SYSTEM32"):
            messagebox.showerror(APP_NAME, _t("g173"))
            return
        self.cfg["recv_root"] = p
        save_cfg(self.cfg)
        if self.server and self.server.running:
            self.server.stop_server()
            self.server = None
            self.root.after(300, self._start_server)
        self._refresh_self()
        self.lbl_status.config(text=_t("g174"))

    # ------------------------------------------------------------ 防火墙

    def _ps(self, script, timeout=25):
        """跑一段系统管理脚本，返回 (rc, stdout, stderr)。"""
        exe = "powershell"
        try:
            p = subprocess.run(
                [exe, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
                capture_output=True, text=True, timeout=timeout,
                encoding="utf-8", errors="ignore")
            return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()
        except Exception as e:
            return -1, "", str(e)

    def _net_categories(self):
        """本机各接口的网络类别 [(索引, Private/Public/DomainAuthenticated)]。"""
        rc, out, _ = self._ps(
            "Get-NetConnectionProfile -ErrorAction SilentlyContinue "
            "| ForEach-Object { \"$($_.InterfaceIndex)|$($_.NetworkCategory)\" }")
        res = []
        for line in out.splitlines():
            line = line.strip()
            if "|" not in line:
                continue
            a, b = line.split("|", 1)
            try:
                res.append((int(a), b.strip()))
            except Exception:
                pass
        return res

    def _fw_rules(self):
        """现存 LanSplice 规则 [(名称, 启用, 作用域)]。"""
        rc, out, _ = self._ps(
            "Get-NetFirewallRule -DisplayName 'LanSplice*' -ErrorAction SilentlyContinue "
            "| ForEach-Object { \"$($_.DisplayName)|$($_.Enabled)|$($_.Profile)\" }")
        res = []
        for line in out.splitlines():
            parts = line.strip().split("|")
            if len(parts) >= 3:
                res.append(tuple(parts[:3]))
        return res

    def _fw_script(self, port, auto_private=False):
        """
        拼「一键放行」要执行的脚本。抽出来是为了能单独测语法 ——
        这段脚本一旦拼错，用户看到的就是一屏红字。
        """
        ps_list = ["$ErrorActionPreference='SilentlyContinue';",
                   # 旧名 Link2PC 的规则一起清掉，避免升级后两套规则并存
                   "Get-NetFirewallRule | Where-Object { $_.DisplayName -like '*LanSplice*' "
                   "-or $_.DisplayName -like '*Link2PC*' } | Remove-NetFirewallRule;"]
        if auto_private:
            ps_list.append(
                "Get-NetConnectionProfile | Where-Object { $_.NetworkCategory -ne 'Private' } "
                "| Set-NetConnectionProfile -NetworkCategory Private;")
        # 规则**按端口**建，不绑 -Program。
        #
        # 为什么改：Windows 的防火墙规则是按 exe 完整路径记的。
        # 每发一版，文件名就从 v1.7.2.exe 变成 v1.7.3.exe，路径一变旧规则就
        # 管不到新文件 —— 于是每次升级都要重新放行一次。用户看到的是
        # 「怎么又问我」，而且点错一次（或系统记住了「阻止」）就再也收不到文件。
        #
        # 按端口就不一样了：一条规则管所有版本，换多少次都不用再问。
        #
        # 安全性没有退步：
        #   · RemoteAddress 仍然只放行局域网段，公网连不进来
        #   · 端口是本软件专用，冲突概率极低
        #   · 数据本身还有 AES-256-GCM + 配对码两道关
        # 代价是：本机别的程序若也监听这两个端口，同样能被内网访问。
        # 这个取舍写在 README 的「防火墙这件事」里，不藏着。
        for proto, pnum in (("TCP", port), ("UDP", L.DISCOVERY_PORT)):
            ps_list.append(
                "New-NetFirewallRule -DisplayName 'LanSplice-%s' -Direction Inbound "
                "-Protocol %s -LocalPort %d -Action Allow -Profile Any "
                "-RemoteAddress 192.168.0.0/16,10.0.0.0/8,172.16.0.0/12,127.0.0.1 "
                "| Out-Null;" % (proto, proto, pnum))
        ps_list.append("Write-Output 'L2P-FW-OK'")
        return "".join(ps_list)

    def _offer_reallow(self):
        """
        规则还绑着旧版 exe 时，问一次「要不要重新放行」。

        每个 exe 路径只问一次（记住 fw_prompt_for）：
        用户点「否」之后再点状态灯也能手动放行，不必每次启动都弹。
        """
        try:
            exe = os.path.abspath(sys.executable)
        except Exception:
            exe = ""
        if self.cfg.get("fw_prompt_for") == exe:
            return
        self.cfg["fw_prompt_for"] = exe
        save_cfg(self.cfg)

        # 开机自启是带 --min 缩到托盘里的：这时候弹模态框，用户根本看不见，
        # 程序就卡在那儿等一个永远不来的点击 —— 表面上像「开机后没启动」。
        # 改成只在状态栏留一句，用户点开窗口能看到，也能点状态灯手动放行。
        if getattr(self, "quiet", False):
            try:
                self.lbl_status.config(text=_t("g384"))
            except Exception:
                pass
            return

        if messagebox.askyesno(_t("g384"), _t("g385") % APP_VER, parent=self.root):
            self.fw_dialog(quick=True)

    def _fw_linux_dialog(self):
        """
        Linux 上的「防火墙」窗口：不自动改，只给一条按本机情况挑好的命令。

        为什么不弹 pkexec 替用户执行：改防火墙要 root，各发行版工具不同，
        pkexec 在麒麟/UOS 上的授权代理不一定装、装了行为也不一样。
        与其做一个三成概率失败还要背锅的「一键」，不如把命令写清楚。
        """
        cmd = P.firewall_manual_command()
        win = tk.Toplevel(self.root)
        win.title(_t("g440"))
        win.configure(bg=C_BG)
        win.geometry("640x330")
        win.minsize(560, 300)
        win.transient(self.root)

        tk.Label(win, text=_t("g436"), bg=C_BG, fg=C_TEXT, font=(FONT, 9),
                 justify="left", anchor="w", wraplength=580).pack(
            anchor="w", padx=18, pady=(16, 10))

        if not cmd:
            # 没有防火墙工具：多半是不需要放行，把话说清楚别让人瞎找
            tk.Label(win, text=_t("g438"), bg=C_BG, fg=C_SUB, font=(FONT, 9),
                     justify="left", anchor="w", wraplength=580).pack(
                anchor="w", padx=18)
        else:
            box = tk.Frame(win, bg=C_WHITE, highlightthickness=1,
                           highlightbackground=C_LINE)
            box.pack(fill="x", padx=18, pady=4)
            ent = tk.Entry(box, font=("Consolas", 10), bd=0, bg=C_WHITE,
                           fg=C_TEXT, readonlybackground=C_WHITE)
            ent.insert(0, cmd)
            ent.config(state="readonly")
            ent.pack(fill="x", padx=8, pady=8)

            tip = tk.Label(win, text="", bg=C_BG, fg=C_GREEN, font=(FONT, 8))

            def do_copy():
                if self._set_clipboard(cmd):
                    tip.config(text="✓ " + _t("g435"))

            row = tk.Frame(win, bg=C_BG)
            row.pack(anchor="w", padx=18, pady=(10, 0))
            tk.Button(row, text=_t("g434"), command=do_copy, bg=C_BLUE,
                      fg=C_WHITE, relief="flat", cursor="hand2",
                      font=(FONT, 9), padx=12, pady=5).pack(side="left")
            tip.pack(in_=row, side="left", padx=10)

        # 不 pack 到 bottom —— 那会在中间留一大片空白。
        # 紧跟内容往下排，窗口再按实际需要收缩。
        bar = tk.Frame(win, bg=C_BG)
        bar.pack(fill="x", padx=18, pady=(20, 14))
        self._mk_btn(bar, _t("g437"), self._refresh_fw_status, C_GRAY,
                     width=None).pack(side="left")
        self._mk_btn(bar, _t("g406"), win.destroy, C_GRAY,
                     width=None).pack(side="right")

        # 内容多少跟本机装了几套防火墙工具有关（没装就没有命令框），
        # 写死高度会剩一大片空白或者把按钮挤出去。
        # 这里直接量「最后一排按钮的下沿」，比 reqheight 准 ——
        # reqheight 会把 pack 时留下的间距也算进去，出来总是偏高。
        try:
            win.update_idletasks()
            bottom = bar.winfo_y() + bar.winfo_height()
            if bottom > 120:
                win.geometry("640x%d" % (bottom + 12))
        except Exception:
            win.geometry("640x384")

    def fw_dialog(self, auto_private=False, quick=False):
        if not P.IS_WIN:
            self._fw_linux_dialog()
            return
        port = int(self.cfg["tcp_port"])
        if not quick:
            cats = self._net_categories()
            has_public = any(c not in ("Private", "DomainAuthenticated")
                             for _i, c in cats)

            if has_public and not auto_private:
                msg = (_t("g175"))
                if messagebox.askyesno(_t("g176"), msg, parent=self.root):
                    auto_private = True

            msg2 = (
                _t("g177")
                % (port, L.DISCOVERY_PORT,
                   _t("g178") if auto_private
                   else _t("g179")))
            if not messagebox.askyesno(APP_NAME, msg2, parent=self.root):
                return

        ps = self._fw_script(port, auto_private)

        # 提权执行。
        #
        # 这里**绝对不能**把脚本用双引号拼进外层 PowerShell 命令行：
        # 外层的双引号字符串会先做一次变量展开，`$ErrorActionPreference`
        # 变成它的当前值 `Continue`、`$_` 变成空，脚本就废了 ——
        # 用户看到的报错正是「无法将 Continue='SilentlyContinue' 识别为 cmdlet」。
        # 改用 -EncodedCommand（base64 里只有字母数字和 +/=），外层怎么解析都不会动它。
        inner = base64.b64encode(ps.encode("utf-16-le")).decode("ascii")
        outer = ("Start-Process powershell -Verb RunAs -Wait -WindowStyle Hidden "
                 "-ArgumentList "
                 "'-NoProfile','-ExecutionPolicy','Bypass','-EncodedCommand','%s'" % inner)
        try:
            subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                 "-Command", outer],
                capture_output=True, text=True, timeout=120)
        except Exception as e:
            messagebox.showerror(APP_NAME, _t("g180") % e)
            return

        rules = self._fw_rules()
        alive = [r for r in rules if r[1].lower() == "true"]

        # 关键一步：规则变了必须重建监听，否则用户得手动关程序重开才生效
        self.lbl_status.config(text=_t("g181"))
        self.root.update_idletasks()
        ok = self._restart_server()

        summary = _t("g182") % (len(alive),
                                _t("g183") if alive else _t("g184"),
                                _t("g185") if ok else _t("g186"))
        if quick:
            self.lbl_status.config(text=summary)
        else:
            messagebox.showinfo(APP_NAME, summary)
        self._refresh_fw_status()

    def diagnose(self):
        self.lbl_status.config(text=_t("g187"))
        threading.Thread(target=self._diag_worker, daemon=True).start()

    def _diag_worker(self):
        out = []
        port = int(self.cfg["tcp_port"])

        try:
            ips = ["%s/%d" % (d["ip"], d["prefix"]) for d in L.list_ipv4()]
            out.append(_t("g188") % L.hostname())
            out.append("        %s" % ("  ".join(ips) or _t("g069")))
        except Exception as e:
            out.append(_t("g189") % e)

        try:
            cats = self._net_categories()
            cn = {"Private": _t("g190"), "Public": _t("g191"), "DomainAuthenticated": _t("g192")}
            if cats:
                out.append(_t("g193") +
                           "  ".join(_t("g194") % (i, cn.get(c, c)) for i, c in cats))
                if any(c not in ("Private", "DomainAuthenticated") for _i, c in cats):
                    out.append(_t("g195"))
            else:
                out.append(_t("g196"))
        except Exception as e:
            out.append(_t("g197") % e)

        ok = False
        sk = socket.socket()
        sk.settimeout(1.2)
        try:
            sk.connect(("127.0.0.1", port))
            ok = True
        except Exception:
            pass
        finally:
            sk.close()
        out.append(_t("g198") % (_t("g199") if ok else _t("g200"), port))

        try:
            rules = self._fw_rules()
            if rules:
                for n, en, pr in rules:
                    out.append(_t("g201") % (n, en, pr))
            else:
                out.append(_t("g202"))
        except Exception as e:
            out.append(_t("g203") % e)

        if self.peer_ip:
            sk = socket.socket()
            sk.settimeout(2.0)
            try:
                sk.connect((self.peer_ip, int(self.peer_port)))
                out.append(_t("g204") % (self.peer_ip, self.peer_port))
            except ConnectionRefusedError:
                out.append(_t("g205")
                           % (self.peer_ip, self.peer_port))
            except socket.timeout:
                out.append(_t("g206")
                           % (self.peer_ip, self.peer_port))
            except Exception as e:
                out.append(_t("g207")
                           % (self.peer_ip, self.peer_port, type(e).__name__))
            finally:
                sk.close()
        else:
            out.append(_t("g208"))

        self.events.put(("diag", "\n".join(out)))

    def _show_diag(self, text):
        self.lbl_status.config(text=_t("g067"))
        if messagebox.askyesno(_t("g209"), text + _t("g210"),
                               parent=self.root):
            self.fw_dialog()

    def security_check(self):
        lines = []
        ips = L.local_ips()
        lines.append(_t("g211") % (L.hostname(), " / ".join(ips) or _t("g212")))
        try:
            s = self.server
            lines.append(_t("g213") % (
                _t("g214") if (s and s.running) else _t("g215"), int(self.cfg["tcp_port"])))
        except Exception:
            pass
        lines.append("")
        lines.append(_t("g216"))
        lines.append(_t("g217"))
        lines.append(_t("g218"))
        lines.append(_t("g219"))
        lines.append(_t("g220"))
        lines.append("")
        lines.append(_t("g221"))
        lines.append(_t("g222"))
        messagebox.showinfo(_t("g223"), "\n".join(lines))

    # ------------------------------------------------------------ 帮助

    def _info_dialog(self, title, body, w=600, h=480):
        """
        可滚动、可复制的说明窗口。

        帮助文本越来越长，messagebox 会撑到屏幕外面去，
        而且里面字还选不中、复制不出来。
        """
        win = tk.Toplevel(self.root)
        win.title(title)
        win.configure(bg=C_BG)
        win.geometry("%dx%d" % (w, h))
        win.transient(self.root)
        wrap = tk.Frame(win, bg=C_LINE)
        wrap.pack(fill="both", expand=True, padx=12, pady=(12, 0))
        sb = tk.Scrollbar(wrap)
        sb.pack(side="right", fill="y")
        txt = tk.Text(wrap, font=(FONT, 9), bg=C_CARD, fg=C_TEXT,
                      relief="flat", wrap="word", padx=10, pady=8,
                      yscrollcommand=sb.set)
        sb.config(command=txt.yview)
        txt.pack(side="left", fill="both", expand=True, padx=1, pady=1)
        txt.insert("1.0", body)
        txt.config(state="disabled")
        bar = tk.Frame(win, bg=C_BG)
        bar.pack(fill="x", padx=12, pady=10)
        self._mk_btn(bar, _t("g327"), win.destroy, C_GRAY,
                     width=None).pack(side="right")
        win.bind("<Escape>", lambda e: win.destroy())
        return win

    def show_help(self):
        self._info_dialog(_t("g030"), _t("g224"))

    def show_disclaimer(self):
        messagebox.showinfo(
            _t("g031"),
            _t("g225"))

    def show_about(self):
        messagebox.showinfo(
            _t("g032"),
            _t("g226") %
            (APP_NAME, APP_VER, _t("g002")))

    def show_license(self):
        """
        v1.6.1：许可与署名。

        关于窗口里放不下这么多字，塞进 messagebox 会被系统截成一屏乱折行；
        单独开一个只读文本框，能滚、能选中、能复制。
        """
        win = tk.Toplevel(self.root)
        win.title(_t("g430"))
        win.geometry("640x580")
        win.minsize(520, 420)
        win.configure(bg=C_BG)
        win.transient(self.root)

        box = tk.Frame(win, bg=C_BG)
        box.pack(fill="both", expand=True, padx=16, pady=(16, 8))
        txt = tk.Text(box, bg=C_CARD, fg=C_TEXT, font=(FONT, 9), wrap="word",
                      relief="flat", padx=12, pady=10)
        sb = ttk.Scrollbar(box, orient="vertical", command=txt.yview)
        txt.config(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        txt.pack(side="left", fill="both", expand=True)
        txt.insert("1.0", _t("g429"))
        txt.config(state="disabled")

        bar = tk.Frame(win, bg=C_BG)
        bar.pack(fill="x", padx=16, pady=(0, 12))
        self._mk_btn(bar, _t("g406"), win.destroy, C_GRAY,
                     width=None).pack(side="right")
        win.bind("<Escape>", lambda _e: win.destroy())
        win.after(60, lambda: txt.focus_set())

    # ------------------------------------------------------------ 事件泵

    def _pump(self):
        try:
            while True:
                try:
                    kind, data = self.events.get_nowait()
                except queue.Empty:
                    break
                try:
                    self._handle(kind, data)
                except Exception:
                    pass          # 单个事件出错不能拖垮整个界面循环
        finally:
            self.root.after(60, self._pump)

    def _handle(self, kind, data):
        if kind == "diag":
            self._show_diag(data)
        elif kind == "peers":
            self.on_peers(data)
        elif kind == "peer_ok":
            ip, port, name = data
            self.set_peer(ip, port, name)
            self.lbl_status.config(text=_t("g227") % (name or ip))
        elif kind == "peer_auth_fail":
            self.lamp_peer.config(fg=C_RED)
            self.lbl_peer_sub.config(text=_t("g228"))
            self.lbl_status.config(text=_t("g228"))
        elif kind == "peer_fail":
            self.lamp_peer.config(fg=C_RED)
            self.lbl_peer_sub.config(text=str(data)[:40])
            self.lbl_status.config(text=_t("g229") % str(data)[:60])
        elif kind == "status":
            self.lbl_status.config(text=str(data))
        elif kind == "text_ok":
            name, n = data
            self.lbl_status.config(text=_t("g322") % name)
            self._notify(_t("g320"), _t("g345") % n)
        elif kind == "chat_sent":
            ok_n, fails, msg, cb = data
            if cb:
                try:
                    cb(ok_n, fails, msg)
                except Exception:
                    pass
        elif kind == "text_fail":
            self.lbl_status.config(text=_t("g323") % str(data)[:60])
        elif kind == "mirror_scan":
            i, n = data
            ui = self._mirror_ui
            if ui and ui[0].winfo_exists():
                ui[2].config(text=_t("g381") % (i, n))
                if n:
                    # 核对只占前四分之一，剩下留给真正在传的那一段
                    ui[1]["value"] = i * 1000.0 / n * 0.25
        elif kind == "mirror_plan":
            nfiles, ntodo, nbytes, nskip = data
            ui = self._mirror_ui
            if ui and ui[0].winfo_exists():
                ui[1]["value"] = 0
                ui[2].config(text=_t("g382") % (
                    nfiles, ntodo, L.human_size(nbytes), nskip))
        elif kind == "mirror_file":
            i, n, base = data
            ui = self._mirror_ui
            if ui and ui[0].winfo_exists():
                ui[2].config(text=_t("g376") % (i, n, base))
        elif kind == "mirror_prog":
            done, total, spd = data
            ui = self._mirror_ui
            if ui and ui[0].winfo_exists():
                if total:
                    ui[1]["value"] = 250 + done * 750.0 / total
                ui[2].config(text="%s / %s   %s" % (
                    L.human_size(done), L.human_size(total),
                    fmt_speed(spd)))
        elif kind == "mirror_done":
            updated, skipped_n, total = data
            ui = self._mirror_ui
            if ui and ui[0].winfo_exists():
                ui[1]["value"] = 1000
                if updated == 0 and skipped_n == 0:
                    ui[2].config(text=_t("g379"))
                else:
                    ui[2].config(text=_t("g377") % (
                        updated, skipped_n, L.human_size(total)))
                try:
                    ui[3].config(state="normal")
                except Exception:
                    pass
        elif kind == "mirror_err":
            ui = self._mirror_ui
            if ui and ui[0].winfo_exists():
                ui[2].config(text=str(data)[:90])
                try:
                    ui[3].config(state="normal")
                except Exception:
                    pass
        elif kind == "log":
            if "✗" in data or _t("g117") in data:
                self.lbl_status.config(text=data)
        elif kind == "recv":
            k, d = data
            if k == "peer_seen":
                self.on_peer_seen(d)
            elif k == "recv_text":
                self.on_recv_text(d)
            elif k == "chat_msg":
                self.on_chat_incoming(d.get("msg") or {})
            elif k == "recv_begin":
                off = int(d.get("offset") or 0)
                name = os.path.basename(d.get("path", ""))
                if off > 0:
                    self.lbl_status.config(
                        text=_t("g335") % L.human_size(off))
                else:
                    self.lbl_status.config(text=_t("g230") % name)
            elif k == "recv_verify":
                self.lbl_status.config(text=_t("g334") % 0)
            elif k == "recv_done":
                name = os.path.basename(d.get("path", ""))
                self.lbl_status.config(text=_t("g230") % name)
                if name:
                    self._notify(_t("g230") % name,
                                 L.human_size(int(d.get("size") or 0)))
                    try:
                        HIST.append(HIST.make_entry(
                            "in", files=1, nbytes=int(d.get("size") or 0),
                            ok=1, root=self.cfg.get("recv_root", ""),
                            src=[d.get("path", "")],
                            names=[name],
                            peer=self.peer_name or self.peer_ip,
                            ip=self.peer_ip,
                            port=int(self.peer_port or 0)))
                    except Exception:
                        pass
            elif k == "recv_error":
                msg = str(d.get("msg") or "")
                if d.get("kept"):
                    # 分片留着，用户再点一次发送就能接着传
                    self.lbl_status.config(text=_t("g337"))
                else:
                    self.lbl_status.config(text=msg[:80])
        elif kind == "peer_root":
            self.peer_root = str(data or "")
            if self.peer_root:
                self.lbl_peer_sub.config(
                    text="%s:%d  →  %s" % (self.peer_ip, int(self.peer_port), self.peer_root))
        elif kind == "open_peer_ok":
            name, path = data
            self.lbl_status.config(text=_t("g231") % (name, path))
        elif kind == "open_peer_err":
            name, err = data
            self.lbl_status.config(text=_t("g067"))
            if _t("g232") in (err or ""):
                err = (_t("g233") % APP_VER)
            messagebox.showwarning(
                APP_NAME, _t("g234") % (name, err or _t("g235")),
                parent=self.root)
        elif kind == "fw_status":
            state, txt = data
            ok = (state is True)
            manual = (state == "manual")
            self.lbl_fw.config(text="● " + txt,
                               fg=(C_GREEN if ok else
                                   (C_BLUE if manual else C_RED)))
            self.btn_fw.config(text=(_t("g236") if ok else
                                     (_t("g433") if manual else _t("g040"))))
            if state == "stale":
                self._offer_reallow()
        elif kind == "file_start":
            rel, i, n, size = data
            iid = self.rel_rows.get(rel)
            if iid:
                vals = list(self.tree.item(iid, "values"))
                vals[4] = _t("g237")
                self.tree.item(iid, values=vals)
            self.lbl_status.config(
                text="(%d/%d) %s" % (i, n, os.path.basename(rel.replace("\\", "/"))))
        elif kind == "progress":
            rel, d, t, spd = data
            iid = self.rel_rows.get(rel) or self.rows.get(rel)
            if iid:
                tot = self.item_total.get(iid) or t
                got = self.item_done.get(iid, 0) + d
                pct = int(got * 100 / tot) if tot else 0
                vals = list(self.tree.item(iid, "values"))
                vals[2] = "%d%%" % min(100, pct)
                vals[3] = fmt_speed(spd)
                vals[4] = _t("g237")
                self.tree.item(iid, values=vals)
            if self.total_bytes:
                v = int(self.done_bytes * 1000 / self.total_bytes)
                self.pbar["value"] = max(0, min(1000, v))
                eta = fmt_eta(self.done_bytes, self.total_bytes, spd)
                self.lbl_status.config(text="%s / %s  %s%s" % (
                    L.human_size(self.done_bytes), L.human_size(self.total_bytes),
                    fmt_speed(spd), (_t("g238") % eta) if eta else ""))
        elif kind == "file_done":
            rel, size, st, _ = data
            iid = self.rel_rows.get(rel) or self.rows.get(rel)
            if iid:
                vals = list(self.tree.item(iid, "values"))
                if st == _t("g115") or _t("g239") in st:
                    self.item_done[iid] = self.item_done.get(iid, 0) + size
                    self.item_ok.setdefault(iid, set()).add(rel)
                    self.item_files_done[iid] = self.item_files_done.get(iid, 0) + 1
                    ft = self.item_files_total.get(iid, 0)
                    tot = self.item_total.get(iid, 0)
                    done_i = self.item_done.get(iid, 0)
                    if ft <= 1:
                        vals[2] = "100%"
                        vals[4] = _t("g115")
                    else:
                        vals[2] = "%d%%" % (int(done_i * 100 / tot) if tot else 100)
                        vals[4] = _t("g240") % (self.item_files_done[iid], ft)
                elif st == _t("g117"):
                    vals[2] = "—"
                    vals[3] = ""
                    vals[4] = _t("g117")
                elif st == _t("g116"):
                    vals[4] = _t("g116")
                self.tree.item(iid, values=vals)
        elif kind == "send_end":
            done, skipped, failed, err = data
            self._send_done(done, skipped, failed, err)
        elif kind == "pull_stat":
            self._on_pull_stat(*data)
        elif kind == "pull_end":
            self.sending = False
            self.btn_stop.config(state="disabled")
            if data:
                self.lbl_status.config(text=_t("g241") % data)
                messagebox.showerror(APP_NAME, _t("g241") % data)
            else:
                self.lbl_status.config(text=_t("g242"))
                self.pbar["value"] = 1000

    # ------------------------------------------------------------ 托盘与常驻

    def _tray_server_label(self):
        # 只在托盘线程里被读，不能碰 tkinter 变量，只能看纯 Python 状态
        running = bool(self.server and self.server.running)
        return _t("g303") if running else _t("g304")

    def _tray_autostart_label(self):
        return ("✓ " if autostart_get() else "   ") + _t("g305")

    def _init_tray(self):
        if not HAS_TRAY:
            return
        try:
            items = [
                (1, _t("g300")),
                (2, _t("g301")),
                (5, _t("g360")),
                None,
                (3, self._tray_server_label),
                (4, self._tray_autostart_label),
                None,
                (9, _t("g302")),
            ]
            self.tray = TRAY.Tray(
                "%s  v%s" % (APP_NAME, APP_VER),
                items,
                on_show=lambda: self.root.after(0, self.show_window),
                on_cmd=lambda i: self.root.after(0, self.on_tray_cmd, i),
                on_quit=lambda: self.root.after(0, self.quit_app))
            if not self.tray.start(timeout=3.0):
                self.tray = None
        except Exception:
            self.tray = None
        self._tray_tip()

    def _tray_tip(self):
        if not self.tray:
            return
        running = bool(self.server and self.server.running)
        try:
            self.tray.set_tip("%s v%s · %s" % (
                APP_NAME, APP_VER, _t("g309") if running else _t("g310")))
        except Exception:
            pass

    def on_tray_cmd(self, i):
        if i == 1:
            self.show_window()
        elif i == 2:
            self.open_recv_root()
        elif i == 3:
            self.toggle_server()
            self._tray_tip()
        elif i == 5:
            self.show_qr_share()
        elif i == 4:
            on = not autostart_get()
            if autostart_set(on):
                self.lbl_status.config(text=_t("g307") if on else _t("g308"))
            else:
                self.show_window()
                messagebox.showwarning(APP_NAME, _t("g306"), parent=self.root)
        elif i == 9:
            self.quit_app()

    def show_window(self):
        try:
            self.root.deiconify()
            # 回到任务栏。顺序要紧：先 deiconify 让它可见，
            # 再清掉 TOOLWINDOW，任务栏才会挂回一个（且只有一个）按钮。
            P.taskbar_set_visible(self.root, True)
            self.root.lift()
            self.root.focus_force()
        except Exception:
            pass

    def hide_window(self):
        # 手机网页端的承诺是「关掉窗口就停」，缩到托盘也照办
        try:
            if self._qr_win is not None:
                self._close_qr()
        except Exception:
            pass
        # 先把它从任务栏摘掉，再藏。
        # 只 withdraw 的话 Windows 任务栏按钮时常留着，等 deiconify 又挂一个，
        # 用户看到的就是「关了一次，任务栏里两个图标」。
        P.taskbar_set_visible(self.root, False)
        try:
            self.root.withdraw()
        except Exception:
            pass

    def _notify(self, title, text, warning=False):
        """
        传完给个动静。

        缩到托盘之后，用户看不见进度条，没通知就完全不知道传完了 ——
        这是「常驻」带来的必要配套，不是锦上添花。
        """
        if self.cfg.get("notify_done", True) and self.tray:
            try:
                self.tray.notify(title, text, warning)
            except Exception:
                pass
        if self.cfg.get("sound", True):
            try:
                import winsound
                winsound.MessageBeep(0x30 if warning else 0x40)
            except Exception:
                pass

    # ------------------------------------------------------------ 关闭

    def on_close(self):
        """
        点右上角 × 要做两件事之一：缩到托盘继续接收，或者彻底退出。

        以前是「默认缩托盘、第一次提示一下」—— 用户点关闭以为关了，
        结果程序还在后台，任务栏也还留着图标，容易误会。
        现在第一次点关闭就明着问，并且可以记住选择。
        """
        if self._quitting:
            return

        # 没有托盘的平台没得选：缩进去就再也叫不出来，只能退出
        if not (self.tray and P.tray_supported()):
            self.quit_app()
            return

        act = self.cfg.get("close_action")
        if act == "tray":
            self._close_to_tray()
            return
        if act == "quit":
            self.quit_app()
            return

        # 还没选过：问一次
        self._ask_close_action()

    def _close_to_tray(self):
        self.hide_window()
        try:
            self.lbl_status.config(text=_t("g455"))
        except Exception:
            pass
        if not self.cfg.get("_tray_hint_shown"):
            self.cfg["_tray_hint_shown"] = True
            save_cfg(self.cfg)
            try:
                self.tray.notify(_t("g311"), _t("g312"))
            except Exception:
                pass

    def _ask_close_action(self):
        """第一次关窗口时问一句，顺便让人可以勾「以后不再问」。"""
        win = tk.Toplevel(self.root)
        win.title(_t("g450"))
        win.configure(bg=C_BG)
        win.transient(self.root)
        win.resizable(False, False)

        # 按钮栏先占底 —— 这个项目在这上面栽过一次，见 send_text_dialog
        bar = tk.Frame(win, bg=C_BG)
        bar.pack(side="bottom", fill="x", padx=18, pady=(6, 14))

        tk.Label(win, text=_t("g451"), bg=C_BG, fg=C_TEXT, font=(FONT, 9),
                 justify="left", anchor="w", wraplength=430).pack(
                     fill="x", padx=18, pady=(16, 8))

        var_remember = tk.BooleanVar(value=True)
        chk = tk.Checkbutton(
            win, text=_t("g454"), variable=var_remember, bg=C_BG, fg=C_SUB,
            font=(FONT, 9), activebackground=C_BG, activeforeground=C_TEXT,
            selectcolor=C_CARD, anchor="w", bd=0, highlightthickness=0)
        chk.pack(fill="x", padx=16, pady=(0, 4))

        tk.Label(win, text=_t("g456"), bg=C_BG, fg=C_SUB, font=(FONT, 8),
                 anchor="w").pack(fill="x", padx=18, pady=(0, 4))

        def pick(action):
            if var_remember.get():
                self.cfg["close_action"] = action
                save_cfg(self.cfg)
            try:
                win.destroy()
            except Exception:
                pass
            if action == "tray":
                self._close_to_tray()
            else:
                self.quit_app()

        self._mk_btn(bar, _t("g327"), win.destroy, C_GRAY,
                     width=None).pack(side="right", padx=(8, 0))
        self._mk_btn(bar, _t("g453"), lambda: pick("quit"), "#b0413e",
                     width=None).pack(side="right", padx=(8, 0))
        self._mk_btn(bar, _t("g452"), lambda: pick("tray"), C_BLUE,
                     width=None).pack(side="right")

        win.protocol("WM_DELETE_WINDOW", win.destroy)
        win.bind("<Escape>", lambda _e: win.destroy())

        # 居中到主窗口上方
        win.update_idletasks()
        try:
            rx, ry = self.root.winfo_rootx(), self.root.winfo_rooty()
            rw, rh = self.root.winfo_width(), self.root.winfo_height()
            ww, wh = win.winfo_reqwidth(), win.winfo_reqheight()
            win.geometry("+%d+%d" % (max(0, rx + (rw - ww) // 2),
                                     max(0, ry + (rh - wh) // 3)))
        except Exception:
            pass
        win.grab_set()
        win.focus_force()

    def ask_close_action_again(self):
        """设置菜单里主动改「关闭时怎么办」——先清掉记忆再问。"""
        self.cfg.pop("close_action", None)
        save_cfg(self.cfg)
        self._ask_close_action()

    def quit_app(self):
        if self.sending:
            self.show_window()
            if not messagebox.askyesno(APP_NAME, _t("g243")):
                return
            self.cancel_flag.set()
        self._quitting = True
        try:
            self._close_qr()
        except Exception:
            pass
        try:
            if self.tray:
                self.tray.stop()
        except Exception:
            pass
        try:
            if self.server:
                self.server.stop_server()
        except Exception:
            pass
        self.root.destroy()


def _apply_font(root):
    """
    挑一个这台机器上真有的中文字体。

    Windows 是微软雅黑；Linux 上大概率是 Noto Sans CJK，老一点的信创机
    可能是文泉驿。硬写「Microsoft YaHei UI」的话，Tk 会抱着一个不存在的
    字体名去找替代，中文常常掉成方框。

    非 Windows 上还要顺手改掉 Tk 的几个具名字体（TkDefaultFont 等）——
    ttk 的表格、菜单、对话框走的是那几个名字，只改 FONT 变量管不到它们，
    结果就是主窗口中文正常、菜单里全是方框。

    Windows 上不动具名字体：那边默认就是雅黑，改了反而可能让老用户
    觉得字号或行距变了。
    """
    global FONT
    try:
        import tkinter.font as tkfont
        FONT = P.pick_font(tkfont.families(root), fallback=FONT)
        if not P.IS_WIN:
            for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont",
                         "TkHeadingFont", "TkCaptionFont", "TkSmallCaptionFont"):
                try:
                    tkfont.nametofont(name).configure(family=FONT)
                except Exception:
                    pass
    except Exception:
        pass
    return FONT


def _run():
    P.enable_dpi_awareness()

    global HAS_DND
    root = None
    if HAS_DND:
        try:
            root = TkinterDnD.Tk()
        except Exception:
            HAS_DND = False          # 打包后 tkdnd 缺失时优雅降级
            root = None
    if root is None:
        root = tk.Tk()
    _apply_font(root)
    app = App(root)
    # --min：开机自启时直接缩到托盘，不弹窗打断开机。
    # 没有托盘的平台（Linux）不能这么干 —— 缩进去就再没人叫得出来了。
    # 打包冒烟用：打开聊天窗口停留几秒再退出，验证模块真的打进去了。
    # 用户不会用到，写在 --help 里也不提。
    if "--selftest-chat" in sys.argv:
        app.quiet = True
        opened = {"ok": False, "err": ""}

        def _try_open():
            try:
                app.open_chat()
            except Exception as e:
                opened["err"] = "%s: %s" % (type(e).__name__, e)
                return
            try:
                w = app.chat_win.win if app.chat_win else None
                if w is not None and w.winfo_exists():
                    opened["ok"] = True
                    print("CHATWINDOW_TITLE=%s" % w.title())
                    print("CHATWINDOW_SIZE=%dx%d"
                          % (w.winfo_width(), w.winfo_height()))
            except Exception as e:
                opened["err"] = str(e)

        root.after(900, _try_open)
        root.after(4500, app.root.destroy)
        root.mainloop()
        print("HAS_CHAT=%s" % HAS_CHAT)
        print("CHAT_WINDOW_OPENED=%s" % opened["ok"])
        if opened["err"]:
            print("CHAT_ERROR=%s" % opened["err"])
        sys.exit(0 if opened["ok"] else 2)

    if "--min" in sys.argv and P.tray_supported() and HAS_TRAY:
        # 同时进入「安静模式」：模态框（比如防火墙要重新放行）一律不弹，
        # 否则用户开机时根本看不到那个框，程序却卡着等点击。
        app.quiet = True
        root.after(700, app.hide_window)
    root.mainloop()


def main():
    # 带子命令就交给命令行模块，什么都不带才是图形界面。
    # 这一步必须在建 Tk 之前 —— 否则批处理里调用会闪一下窗口。
    args = sys.argv[1:]

    # v1.6.1：资源管理器右键过来的 "--send <路径>"。
    # 先把路径投给在跑的那个实例，自己再决定要不要开窗口。
    send_paths = []
    if "--send" in args:
        i = args.index("--send")
        send_paths = [a for a in args[i + 1:] if a and not a.startswith("--")]
        args = args[:i]
        drop_paths(send_paths)

    if args and args[0] in ("send", "devices", "serve", "version",
                            "-h", "--help", "help"):
        import link2pc_cli as CLI
        CLI._attach_console()
        try:
            code = CLI.main(args)
        except SystemExit as e:
            code = e.code or 0
        except Exception:
            # 命令行模式下别弹那个 PyInstaller 的异常对话框，
            # 把 traceback 打到控制台，退出码 1 —— 批处理能判断出来。
            import traceback
            traceback.print_exc()
            code = 1
        try:
            sys.stdout.flush()
        except Exception:
            pass
        sys.exit(code or 0)

    # 单实例守在这里：命令行不受影响（上面已经分流走了），
    # 只有「要开图形界面」才需要抢锁。
    if not single_instance_acquire():
        # 开机自启（--min）撞上已在运行的那份：安静退出，别弹窗、别抢焦点
        if "--min" not in args:
            # 前一个实例可能还在建窗口，给它 1 秒多；找不到就算了，别卡着用户
            for _ in range(8):
                if focus_existing():
                    break
                time.sleep(0.15)
        sys.exit(0)

    try:
        _run()
    except Exception:
        import traceback
        tb = traceback.format_exc()
        logp = _t("g244")
        try:
            logp = os.path.join(os.path.dirname(cfg_path()), "crash.log")
            with open(logp, "w", encoding="utf-8") as f:
                f.write(tb)
        except Exception:
            pass
        try:
            r = tk.Tk()
            r.withdraw()
            messagebox.showerror(
                _t("g245"),
                _t("g246") + tb[-1200:] + _t("g247") + logp)
            r.destroy()
        except Exception:
            pass


if __name__ == "__main__":
    main()
