# -*- coding: utf-8 -*-
"""
LanSplice 平台差异层
==================
把所有「一个系统一个做法」的东西收在这里：

    开机自启     Windows 注册表 / Linux .desktop / macOS 暂无
    打开目录      os.startfile / xdg-open / open
    定位文件      explorer /select / nautilus --select / open -R
    打开链接      同上，交给 webbrowser
    单实例        Windows 命名互斥量 / POSIX flock
    窗口前置      EnumWindows / wmctrl（没装就算了）
    剪贴板文件    Windows CF_HDROP / 其余返回空
    防火墙        Windows netsh-规则 / Linux 只给命令，不自动改
    界面字体      雅黑 / Noto Sans CJK 系列

原则：**任何一条失败都不许抛异常**。拿不到就返回 False / 空列表 / None，
让上层的默认分支接住 —— 一个查不到字体就崩掉的界面，比字体难看糟糕得多。

这里不 import tkinter，方便在纯命令行环境（比如测试、serve 模式）复用。
"""

import os
import sys
import re
import time
import shutil
import subprocess

IS_WIN = os.name == "nt"
IS_MAC = sys.platform == "darwin"
IS_LINUX = sys.platform.startswith("linux")

# Windows 常量：别指望 ctypes.wintypes 在别的系统上存在
ERROR_ALREADY_EXISTS = 183

_fh_single = None       # POSIX 单实例锁的文件句柄，必须一直开着
_mutex_handle = None    # Windows 互斥量句柄，同理


def _run(cmd, timeout=8):
    """跑个外部命令，只关心成功没有。任何异常都吃掉。"""
    try:
        with open(os.devnull, "wb") as dn:
            p = subprocess.run(cmd, stdout=dn, stderr=dn, timeout=timeout)
        return p.returncode
    except Exception:
        return -1


def _which(name):
    try:
        return shutil.which(name)
    except Exception:
        return None


# ---------------------------------------------------------------- 界面字体


def ui_font_candidates():
    """
    按优先级排的界面字体候选，GUI 起来后用 tkinter 的字体列表挑第一个存在的。

    微软雅黑在 Linux 上当然没有；信创机器上常见的是 Noto Sans CJK 和
    文泉驿，麒麟有时装的是「Source Han Sans」。都给上。
    """
    if IS_WIN:
        return ["Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI", "Arial"]
    if IS_MAC:
        return ["PingFang SC", "Hiragino Sans GB", "Helvetica Neue"]
    return ["Noto Sans CJK SC", "Source Han Sans SC", "Source Han Sans CN",
            "WenQuanYi Micro Hei", "WenQuanYi Zen Hei",
            "Droid Sans Fallback", "DejaVu Sans"]


def pick_font(available, fallback="TkDefaultFont"):
    """
    available: tkinter.font.families() 的结果。
    返回第一个真正装着的字体名。
    """
    names = set(available or ())
    for f in ui_font_candidates():
        if f in names:
            return f
    return fallback


# ---------------------------------------------------------------- 打开东西


def open_path(path):
    """用系统默认程序打开一个文件或目录。"""
    if not path:
        return False
    if IS_WIN:
        try:
            os.startfile(path)          # noqa: S606  Windows 专有
            return True
        except Exception:
            return False
    if IS_MAC:
        return _run(["open", path]) == 0
    # Linux：xdg-open 是标准，但老一点的桌面可能只有别的
    for cmd in (["xdg-open", path], ["gio", "open", path],
                ["kde-open5", path], ["kde-open", path], ["exo-open", path]):
        if _which(cmd[0]) and _run(cmd) == 0:
            return True
    return False


def reveal_path(path):
    """
    在文件管理器里把某个文件「选中」；做不到就退一步打开它所在的目录。

    Windows 的 explorer /select 会返回 1，不能用返回码判断。
    """
    if not path:
        return False
    exists = os.path.exists(path)
    if IS_WIN:
        try:
            if exists and os.path.isfile(path):
                subprocess.Popen(["explorer", "/select,", path])
            elif exists:
                subprocess.Popen(["explorer", path])
            else:
                return False
            return True
        except Exception:
            return False
    if IS_MAC:
        return _run(["open", "-R", path]) == 0 if exists else open_path(
            os.path.dirname(path))
    if exists:
        for cmd in (["nautilus", "--select", path],
                    ["dolphin", "--select", path],
                    ["nemo", path],
                    ["thunar", path]):
            if _which(cmd[0]) and _run(cmd) == 0:
                return True
    # 都不行：打开父目录，至少人能自己找
    parent = path if os.path.isdir(path) else os.path.dirname(path)
    return open_path(parent if parent else path)


def open_url(url):
    """打开浏览器。不依赖 webbrowser 的实现细节，Linux 上更可控。"""
    if not url:
        return False
    if IS_WIN:
        try:
            os.startfile(url)           # noqa: S606
            return True
        except Exception:
            pass
    if IS_MAC:
        if _run(["open", url]) == 0:
            return True
    else:
        for cmd in (["xdg-open", url], ["gio", "open", url],
                    ["sensible-browser", url]):
            if _which(cmd[0]) and _run(cmd) == 0:
                return True
    try:
        import webbrowser
        return bool(webbrowser.open(url))
    except Exception:
        return False


# ---------------------------------------------------------------- 开机自启

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _linux_autostart_file():
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(
        os.path.expanduser("~"), ".config")
    return os.path.join(base, "autostart", "lansplice.desktop")


def autostart_cmd():
    """
    开机要执行的那条命令。

    打包成 exe：exe 自己的路径。
    从源码跑：python3 -B 脚本路径（-B 是不写 __pycache__，
    装在 /opt 下普通用户改不动，会一直刷权限警告）。
    """
    if getattr(sys, "frozen", False):
        return '"%s" --min' % os.path.abspath(sys.executable)
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "link2pc_gui.py")
    return "%s -B %s --min" % (sys.executable or "python3", script)


def autostart_get():
    """当前是否已设为开机自启。"""
    if IS_WIN:
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
                v, _ = winreg.QueryValueEx(k, "LanSplice")
            return bool(v)
        except Exception:
            return False
    if IS_LINUX:
        return os.path.exists(_linux_autostart_file())
    return False


def autostart_set(on):
    """开 / 关开机自启。返回是否成功。"""
    if IS_WIN:
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0,
                                winreg.KEY_SET_VALUE) as k:
                if on:
                    winreg.SetValueEx(k, "LanSplice", 0, winreg.REG_SZ,
                                      autostart_cmd())
                else:
                    try:
                        winreg.DeleteValue(k, "LanSplice")
                    except FileNotFoundError:
                        pass
            return True
        except Exception:
            return False
    if IS_LINUX:
        p = _linux_autostart_file()
        try:
            if not on:
                if os.path.exists(p):
                    os.remove(p)
                return True
            os.makedirs(os.path.dirname(p), exist_ok=True)
            # Exec 里的 %-转义：desktop 文件里 % 是字段码，真要用得写 %%
            cmd = autostart_cmd().replace("%", "%%")
            body = (
                "[Desktop Entry]\n"
                "Type=Application\n"
                "Name=LanSplice\n"
                "Name[zh_CN]=LanSplice 双机直传\n"
                "Comment=Direct PC-to-PC transfer on your LAN\n"
                "Exec=%s\n"
                "Icon=lansplice\n"
                "Terminal=false\n"
                "Categories=Network;FileTransfer;\n"
                "X-GNOME-Autostart-enabled=true\n"
                "X-GNOME-Autostart-Delay=6\n"
            ) % cmd
            with open(p, "w", encoding="utf-8", newline="\n") as f:
                f.write(body)
            return True
        except Exception:
            return False
    return False


# ---------------------------------------------------------------- 单实例


def single_instance(name):
    """
    抢一把「只能有一个人拿」的锁。抢到返回 True。

    为什么必须要有：双击两次会出现两个进程抢同一个 47820 端口。
    Windows 允许 SO_REUSEADDR 二次绑定，于是两边都「启动成功」，
    但接收到底落在哪个进程是不确定的 —— 这就是「传了没反应」的经典成因。

    Linux 用 flock：内核锁，进程一死自动释放，不会留下「上次没退干净」的死锁文件。

    失败时一律放行（返回 True）：拿不到锁总比打不开程序强。
    """
    global _fh_single, _mutex_handle

    if IS_WIN:
        try:
            import ctypes
            from ctypes import wintypes
            k32 = ctypes.windll.kernel32
            k32.CreateMutexW.restype = wintypes.HANDLE
            k32.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL,
                                         wintypes.LPCWSTR]
            k32.GetLastError.restype = wintypes.DWORD
            h = k32.CreateMutexW(None, False, name)
            if not h:
                return True
            if k32.GetLastError() == ERROR_ALREADY_EXISTS:
                k32.CloseHandle(h)
                return False
            _mutex_handle = h       # 故意不关：进程活着就一直持有
            return True
        except Exception:
            return True

    if IS_LINUX or IS_MAC:
        try:
            import fcntl
            base = os.environ.get("XDG_RUNTIME_DIR") or "/tmp"
            if not os.path.isdir(base):
                base = "/tmp"
            safe = re.sub(r"[^A-Za-z0-9_.-]", "_", name)
            p = os.path.join(base, "lansplice-%s.lock" % safe)
            fh = open(p, "a+")
            try:
                fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                fh.close()
                return False
            try:
                fh.seek(0)
                fh.truncate()
                fh.write("%d\n" % os.getpid())
                fh.flush()
            except Exception:
                pass
            _fh_single = fh
            return True
        except Exception:
            return True

    return True


def focus_existing():
    """
    把已经在跑的那个窗口提到前面。

    Linux 上不强求：没装 wmctrl / xdotool 就返回 False，
    让上层用「已经有一个在跑了」的提示兜住。
    """
    if IS_WIN:
        return _focus_win()
    for cmd in (["wmctrl", "-a", "LanSplice"], ["wmctrl", "-x", "-a", "lansplice"]):
        if _which(cmd[0]) and _run(cmd, timeout=4) == 0:
            return True
    if _which("xdotool"):
        r = _run(["xdotool", "search", "--name", "LanSplice", "windowactivate"],
                 timeout=4)
        if r == 0:
            return True
    return False


def _focus_win():
    """Windows：枚举 TkTopLevel，挑一个可见的恢复并抢焦点。"""
    try:
        import ctypes
        from ctypes import wintypes
        u = ctypes.windll.user32
        found = []
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
                if tb.value.startswith("LanSplice"):
                    found.append((hwnd, bool(u.IsWindowVisible(hwnd))))
            except Exception:
                pass
            return True

        u.EnumWindows(EnumProc(_cb), 0)
        if not found:
            return False
        vis = [h for h, v in found if v]
        hwnd = (vis or [found[0][0]])[0]
        if not vis:
            u.ShowWindow(hwnd, 5)       # SW_SHOW：先在托盘里待着的那个显出来
        u.ShowWindow(hwnd, 9)           # SW_RESTORE
        u.SetForegroundWindow(hwnd)
        return True
    except Exception:
        return False


# ---------------------------------------------------------------- 剪贴板文件

CF_HDROP = 15


def clipboard_file_paths():
    """
    取剪贴板里被复制的**文件/文件夹**路径。

    目前只在 Windows 上实现（CF_HDROP）。Linux 上要分 GNOME 的
    x-special/gnome-copied-files、KDE 的 application/x-kde-cutselection，
    流派太多，暂时返回空 —— 上层会当作「复制的是普通文字」，不影响其他功能。
    """
    if not IS_WIN:
        return []
    try:
        import ctypes
        from ctypes import wintypes
        u = ctypes.windll.user32
        s = ctypes.windll.shell32
        u.OpenClipboard.argtypes = [wintypes.HWND]
        u.OpenClipboard.restype = wintypes.BOOL
        u.GetClipboardData.argtypes = [wintypes.UINT]
        u.GetClipboardData.restype = wintypes.HANDLE
        u.CloseClipboard.restype = wintypes.BOOL
        s.DragQueryFileW.argtypes = [wintypes.HANDLE, wintypes.UINT,
                                     wintypes.LPWSTR, wintypes.UINT]
        s.DragQueryFileW.restype = wintypes.UINT
    except Exception:
        return []

    opened = False
    for _ in range(6):              # 剪贴板可能被别的程序占着一瞬间
        if u.OpenClipboard(None):
            opened = True
            break
        time.sleep(0.03)
    if not opened:
        return []

    out = []
    try:
        h = u.GetClipboardData(CF_HDROP)
        if not h:
            return out
        n = s.DragQueryFileW(h, 0xFFFFFFFF, None, 0)
        if not n or n > 4096:
            return out
        buf = ctypes.create_unicode_buffer(32768)
        for i in range(n):
            if s.DragQueryFileW(h, i, buf, 32768):
                out.append(buf.value)
    except Exception:
        return out
    finally:
        try:
            u.CloseClipboard()
        except Exception:
            pass
    return out


# ---------------------------------------------------------------- 界面语言


def default_lang():
    """跟系统走：中文环境用中文，其他用英文。"""
    if IS_WIN:
        try:
            import ctypes
            langid = ctypes.windll.kernel32.GetSystemDefaultUILanguage()
            return "zh" if (langid & 0x3FF) == 0x04 else "en"
        except Exception:
            pass
    # Linux / macOS：看环境变量。zh_CN.UTF-8、zh_TW、zh-Hans 都算中文
    for k in ("LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE"):
        v = (os.environ.get(k) or "").strip().lower()
        if not v:
            continue
        if v.startswith("zh"):
            return "zh"
        if v not in ("c", "posix"):
            return "en"
    if IS_MAC:
        try:
            r = subprocess.run(["defaults", "read", "-g", "AppleLanguages"],
                               capture_output=True, timeout=4)
            if b"zh" in r.stdout.lower():
                return "zh"
        except Exception:
            pass
    return "zh"


# ---------------------------------------------------------------- 防火墙

TCP_PORT = 47820
UDP_PORT = 47821


def firewall_manual_command():
    """
    Linux 上不自动改防火墙：改防火墙要 root，而弹 pkexec 让用户在
    「授权窗口」里输密码这件事，在各家信创系统上表现并不一致，
    失败了还会留个空转的对话框。给一条能直接粘到终端的命令更可靠。
    """
    if _which("ufw"):
        return "sudo ufw allow %d/tcp && sudo ufw allow %d/udp" % (
            TCP_PORT, UDP_PORT)
    if _which("firewall-cmd"):
        return ("sudo firewall-cmd --permanent --add-port=%d/tcp "
                "--add-port=%d/udp && sudo firewall-cmd --reload"
                % (TCP_PORT, UDP_PORT))
    if _which("iptables"):
        return ("sudo iptables -I INPUT -p tcp --dport %d -j ACCEPT && "
                "sudo iptables -I INPUT -p udp --dport %d -j ACCEPT"
                % (TCP_PORT, UDP_PORT))
    return ""


def firewall_hint():
    """Linux 上防火墙这一栏该显示的那句话。"""
    cmd = firewall_manual_command()
    if cmd:
        return cmd
    return "请确认本机防火墙放行 TCP %d 与 UDP %d" % (TCP_PORT, UDP_PORT)


def firewall_tool():
    """当前系统用的是哪套防火墙（只用于界面上显示一行说明）。"""
    for name, label in (("ufw", "UFW"), ("firewall-cmd", "firewalld"),
                        ("iptables", "iptables")):
        if _which(name):
            return label
    return ""


# ---------------------------------------------------------------- 杂项


def enable_dpi_awareness():
    """Windows 高 DPI 下界面糊成一团，得显式声明。别的系统不用管。"""
    if not IS_WIN:
        return
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            import ctypes
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def tray_supported():
    """
    托盘目前只有 Windows 实现（Shell_NotifyIcon）。

    Linux 上托盘要过 libappindicator / StatusNotifierItem，各家桌面
    支持情况不一，麒麟和 UOS 又各有自己的实现 —— 先不做，
    界面上把这个开关藏起来，关窗口就是退出。
    """
    return IS_WIN


def default_recv_root(leaf="接收"):
    """
    第一次运行时，接收目录放哪儿。

    Windows 沿用老习惯：有 E 盘就 E:\\_xfer —— 这是从第一版就有的约定，
    改成别的会让老用户那个熟路径凭空消失。

    Linux / macOS 交给 link2pc_paths（它按「下载」目录挑，中文系统叫
    「下载」也认）。不在这里再写一遍，是为了让图形界面和命令行
    落到同一个地方 —— 两边不一致的话，命令行收的文件在界面上找不到。
    """
    if IS_WIN:
        if os.path.isdir("E:\\"):
            return "E:\\_xfer"
        return os.path.join(os.path.expanduser("~"), leaf)
    try:
        import link2pc_paths as _paths
        return _paths.default_recv_root()
    except Exception:
        home = os.path.expanduser("~")
        for name in ("Downloads", "下载"):
            p = os.path.join(home, name)
            if os.path.isdir(p):
                return os.path.join(p, "LanSplice")
        return os.path.join(home, "LanSplice")


def platform_label():
    if IS_WIN:
        return "Windows"
    if IS_MAC:
        return "macOS"
    if IS_LINUX:
        try:
            with open("/etc/os-release", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("PRETTY_NAME="):
                        return line.split("=", 1)[1].strip().strip('"')
        except Exception:
            pass
        return "Linux"
    return sys.platform
