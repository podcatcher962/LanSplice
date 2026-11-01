# -*- coding: utf-8 -*-
"""
系统托盘（Windows）
==================
纯 ctypes 调 Shell_NotifyIconW，不引入 pystray / Pillow。

为什么自己写：32 位打包环境里没有 pystray，为了一个托盘图标
去装 Pillow + pystray 会让单文件包涨 8 MB 左右，不值。
这套 API 从 Windows 2000 起就没变过，稳定性反而更好。

线程模型
--------
托盘要自己的消息循环，所以单开一个线程：创建隐藏窗口 ->
Shell_NotifyIcon(NIM_ADD) -> GetMessage 循环。
主线程（tkinter）想弹通知，只往队列里放一条再 PostMessage，
绝不跨线程直接碰 shell —— 那会让主线程卡在等 shell 回话上。
"""

import os
import sys

# 托盘是纯 Windows 实现（Shell_NotifyIconW + 一个隐藏窗口的消息循环）。
# Linux 上要过 libappindicator / StatusNotifierItem，各家桌面还不一样，
# 麒麟和 UOS 又各有自己的补丁 —— 这一版先不做。
# 明确抛 ImportError，让上层 try/except 干净地退到「没有托盘」的分支，
# 而不是在一堆 ctypes 调用里半路炸掉。
if os.name != "nt":
    raise ImportError("link2pc_tray is Windows-only")

import ctypes
import threading
from ctypes import wintypes

# ---------------------------------------------------------------- 常量

WM_APP = 0x8000
WM_TRAY = WM_APP + 1            # 托盘图标发回的消息
WM_TRAY_NOTIFY = WM_APP + 2     # 主线程要求弹气泡
WM_COMMAND = 0x0111

WM_LBUTTONUP = 0x0202
WM_RBUTTONUP = 0x0205
WM_LBUTTONDBLCLK = 0x0203

NIN_BALLOONUSERCLICK = 0x0405
NIN_BALLOONTIMEOUT = 0x0404

NIM_ADD = 0
NIM_MODIFY = 1
NIM_DELETE = 2

NIF_MESSAGE = 0x01
NIF_ICON = 0x02
NIF_TIP = 0x04
NIF_INFO = 0x10

NIIF_INFO = 0x01
NIIF_WARNING = 0x02

MF_STRING = 0x0000
MF_SEPARATOR = 0x0800
TPM_RIGHTBUTTON = 0x0002
TPM_RETURNCMD = 0x0100

CS_HREDRAW = 0x0002
CS_VREDRAW = 0x0001

LRESULT = ctypes.c_ssize_t
WNDPROC = ctypes.WINFUNCTYPE(LRESULT, wintypes.HWND, wintypes.UINT,
                             wintypes.WPARAM, wintypes.LPARAM)


class GUID(ctypes.Structure):
    _fields_ = [("Data1", wintypes.DWORD),
                ("Data2", wintypes.WORD),
                ("Data3", wintypes.WORD),
                ("Data4", ctypes.c_ubyte * 8)]


class NOTIFYICONDATAW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("hWnd", wintypes.HWND),
        ("uID", wintypes.UINT),
        ("uFlags", wintypes.UINT),
        ("uCallbackMessage", wintypes.UINT),
        ("hIcon", ctypes.c_void_p),
        ("szTip", wintypes.WCHAR * 128),
        ("dwState", wintypes.DWORD),
        ("dwStateMask", wintypes.DWORD),
        ("szInfo", wintypes.WCHAR * 256),
        ("uVersion", wintypes.UINT),
        ("szInfoTitle", wintypes.WCHAR * 64),
        ("dwInfoFlags", wintypes.DWORD),
        ("guidItem", GUID),
        ("hBalloonIcon", ctypes.c_void_p),
    ]


class WNDCLASSW(ctypes.Structure):
    _fields_ = [
        ("style", wintypes.UINT),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", ctypes.c_void_p),
        ("hCursor", ctypes.c_void_p),
        ("hbrBackground", ctypes.c_void_p),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
    ]


def _load_app_icon():
    """
    取图标句柄：优先从自己这个 exe 里抠（PyInstaller 单文件把图标写进资源，
    sys.executable 就是 exe），失败再退回系统默认图标。
    """
    try:
        shell32 = ctypes.windll.shell32
        large = ctypes.c_void_p()
        small = ctypes.c_void_p()
        n = shell32.ExtractIconExW(ctypes.c_wchar_p(sys.executable), 0,
                                   ctypes.byref(large), ctypes.byref(small), 1)
        if n > 0:
            return small.value or large.value
    except Exception:
        pass
    try:
        # 源码运行时 cwd 下通常有 app.ico
        ico = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.ico")
        if os.path.isfile(ico):
            u = ctypes.windll.user32
            u.LoadImageW.restype = ctypes.c_void_p
            return u.LoadImageW(None, ctypes.c_wchar_p(ico), 1, 0, 0, 0x10)
    except Exception:
        pass
    try:
        u = ctypes.windll.user32
        u.LoadIconW.restype = ctypes.c_void_p
        return u.LoadIconW(None, ctypes.c_void_p(32512))      # IDI_APPLICATION
    except Exception:
        return None


class Tray:
    """
    托盘图标 + 右键菜单 + 气泡通知。

    items: [(id, label), ...]，id 为 None 表示一条分隔线。
    on_cmd(id) 会在托盘线程里被调用 —— 调用方要自己 root.after 切回主线程。
    """

    def __init__(self, tip, items, on_show, on_cmd, on_quit=None):
        self.tip = tip or ""
        self.items = list(items or [])
        self.on_show = on_show
        self.on_cmd = on_cmd
        self.on_quit = on_quit

        self.hwnd = None
        self.hicon = None
        self._nid = None
        self._thread = None
        self._ready = threading.Event()
        self._stop = False
        self._queue = []
        self._lock = threading.Lock()
        self._wndproc_ref = None
        self.error = None

    # ---------------------------------------------------------- 生命周期
    def start(self, timeout=3.0):
        self._thread = threading.Thread(target=self._run, daemon=True,
                                        name="LanSplice-Tray")
        self._thread.start()
        self._ready.wait(timeout)
        return self.hwnd is not None

    def _run(self):
        try:
            self._create()
        except Exception as e:
            self.error = str(e)
            self._ready.set()
            return
        self._ready.set()
        self._loop()

    def _create(self):
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        user32.DefWindowProcW.restype = LRESULT
        user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT,
                                          wintypes.WPARAM, wintypes.LPARAM]
        user32.CreateWindowExW.restype = wintypes.HWND
        user32.CreateWindowExW.argtypes = [
            wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
            ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
            wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID]
        user32.RegisterClassW.restype = wintypes.ATOM
        user32.RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASSW)]

        hinst = kernel32.GetModuleHandleW(None)
        cls_name = "LanSpliceTrayWnd"

        self._wndproc_ref = WNDPROC(self._wndproc)
        wc = WNDCLASSW()
        wc.style = CS_HREDRAW | CS_VREDRAW
        wc.lpfnWndProc = self._wndproc_ref
        wc.cbClsExtra = 0
        wc.cbWndExtra = 0
        wc.hInstance = hinst
        wc.hIcon = None
        wc.hCursor = None
        wc.hbrBackground = None
        wc.lpszMenuName = None
        wc.lpszClassName = cls_name
        user32.RegisterClassW(ctypes.byref(wc))   # 重复注册会失败，忽略即可

        self.hwnd = user32.CreateWindowExW(
            0, cls_name, cls_name, 0, 0, 0, 0, 0,
            None, None, hinst, None)
        if not self.hwnd:
            raise OSError("CreateWindowEx failed: %d" % ctypes.get_last_error())

        self.hicon = _load_app_icon()
        self._nid = self._make_nid()
        ctypes.windll.shell32.Shell_NotifyIconW.restype = wintypes.BOOL

        for _ in range(5):
            if ctypes.windll.shell32.Shell_NotifyIconW(
                    NIM_ADD, ctypes.byref(self._nid)):
                return
            # 开机时 explorer 还没准备好，等一下再试
            threading.Event().wait(0.6)
        raise OSError("Shell_NotifyIcon(NIM_ADD) failed")

    def _make_nid(self, info=False):
        nid = NOTIFYICONDATAW()
        nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        nid.hWnd = self.hwnd
        nid.uID = 1
        nid.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP
        nid.uCallbackMessage = WM_TRAY
        nid.hIcon = self.hicon
        nid.szTip = self.tip[:127]
        if info:
            nid.uFlags |= NIF_INFO
        return nid

    def _loop(self):
        user32 = ctypes.windll.user32
        msg = wintypes.MSG()
        user32.GetMessageW.restype = ctypes.c_int
        while not self._stop:
            r = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if r in (0, -1):
                break
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

    def stop(self):
        self._stop = True
        try:
            if self._nid is not None:
                ctypes.windll.shell32.Shell_NotifyIconW(
                    NIM_DELETE, ctypes.byref(self._nid))
        except Exception:
            pass
        try:
            if self.hwnd:
                ctypes.windll.user32.PostMessageW(self.hwnd, 0x0012, 0, 0)  # WM_QUIT
        except Exception:
            pass

    # ---------------------------------------------------------- 窗口过程
    def _wndproc(self, hwnd, msg, wparam, lparam):
        try:
            if msg == WM_TRAY:
                ev = lparam & 0xFFFF
                if ev in (WM_LBUTTONUP, WM_LBUTTONDBLCLK):
                    self._safe(self.on_show)
                elif ev == WM_RBUTTONUP:
                    self._popup(hwnd)
                elif ev == NIN_BALLOONUSERCLICK:
                    self._safe(self.on_show)
                return 0
            if msg == WM_TRAY_NOTIFY:
                self._drain()
                return 0
        except Exception:
            pass
        return ctypes.windll.user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def _safe(self, fn, *a):
        if not fn:
            return
        try:
            fn(*a)
        except Exception:
            pass

    def _popup(self, hwnd):
        user32 = ctypes.windll.user32
        hmenu = user32.CreatePopupMenu()
        if not hmenu:
            return
        user32.AppendMenuW.argtypes = [wintypes.HMENU, wintypes.UINT,
                                       ctypes.c_size_t, wintypes.LPCWSTR]
        try:
            for item in self.items:
                if item is None:
                    user32.AppendMenuW(hmenu, MF_SEPARATOR, 0, None)
                    continue
                iid, label = item[0], item[1]
                if callable(label):
                    label = label()
                user32.AppendMenuW(hmenu, MF_STRING, int(iid), str(label))
            user32.SetForegroundWindow(hwnd)
            pt = wintypes.POINT()
            user32.GetCursorPos(ctypes.byref(pt))
            user32.TrackPopupMenu.restype = ctypes.c_int
            cmd = user32.TrackPopupMenu(
                hmenu, TPM_RIGHTBUTTON | TPM_RETURNCMD,
                pt.x, pt.y, 0, hwnd, None)
            user32.PostMessageW(hwnd, 0x0000, 0, 0)     # WM_NULL，让菜单能正常收起来
            if cmd:
                self._safe(self.on_cmd, int(cmd))
        finally:
            user32.DestroyMenu(hmenu)

    # ---------------------------------------------------------- 通知
    def notify(self, title, text, warning=False):
        """从任意线程调用都安全：只是入队 + 唤醒窗口线程。"""
        with self._lock:
            self._queue.append((title, text, warning))
        try:
            ctypes.windll.user32.PostMessageW(self.hwnd, WM_TRAY_NOTIFY, 0, 0)
        except Exception:
            pass

    def _drain(self):
        with self._lock:
            items = self._queue[:]
            del self._queue[:]
        for title, text, warning in items:
            nid = self._make_nid(info=True)
            nid.szInfoTitle = (title or "")[:63]
            nid.szInfo = (text or "")[:255]
            nid.dwInfoFlags = NIIF_WARNING if warning else NIIF_INFO
            nid.uVersion = 0
            try:
                ctypes.windll.shell32.Shell_NotifyIconW(
                    NIM_MODIFY, ctypes.byref(nid))
            except Exception:
                pass

    def set_tip(self, tip):
        self.tip = tip or ""
        try:
            nid = self._make_nid()
            ctypes.windll.shell32.Shell_NotifyIconW(
                NIM_MODIFY, ctypes.byref(nid))
        except Exception:
            pass
