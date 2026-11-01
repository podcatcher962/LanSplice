# -*- coding: utf-8 -*-
"""
内网聊天窗口。

刻意保持简单：一个成员栏、一块消息区、一个输入框。
不做表情包、不做已读回执、不做离线消息 —— 这个软件的定位是
「自己家 / 自己办公室里传东西方便」，不是跟微信抢人。

布局按这个项目的教训来：**底部按钮栏先 pack(side="bottom")**，
再放会 expand 的正文。否则 Text 会把按钮挤成 1 像素。
"""

import time
import tkinter as tk
from tkinter import messagebox, ttk

import link2pc_chat as CH
import link2pc_core as L
from link2pc_i18n import t as _t


class ChatWindow:
    """
    聊天窗口本体。

    它不自己起服务端、不自己保存配置 —— 那些都由 App 握着，
    这里只负责「显示 + 把用户的话交出去」。
    """

    def __init__(self, app):
        self.app = app
        self.root = app.root
        self.win = None
        self._list = None            # 消息列表
        self._input = None
        self._roster_box = None
        self._lbl_online = None
        self._sending = False

    # ------------------------------------------------------------ 生命周期

    def _ui(self):
        """
        拿 link2pc_gui 模块本身。

        不能 `import link2pc_gui`（它反过来导入了本文件，会循环）；
        也不能把 FONT / C_BG 这些当成 App 的属性 —— 它们是模块级变量，
        而且 FONT 会被 _apply_font() 在运行时改掉，走模块才能拿到最新值。
        """
        import sys
        # 直接跑 link2pc_gui.py（或打包后的 exe）时，模块名是 __main__，
        # 不是 link2pc_gui —— 写死模块名会在这里 KeyError。
        # 从 App 类反查它定义在哪个模块，两种入口都对。
        name = type(self.app).__module__
        return sys.modules[name]

    def open(self):
        if self.win is not None:
            try:
                self.win.deiconify()
                self.win.lift()
                self.win.focus_force()
                self.refresh_roster()
                return
            except Exception:
                self.win = None

        G = self._ui()
        win = tk.Toplevel(self.root)
        self.win = win
        win.title("%s  ·  %s" % (G.APP_NAME, _t("g460")))
        win.configure(bg=G.C_BG)
        win.geometry("760x520")
        win.minsize(620, 420)
        win.transient(self.root)

        # ---- 左侧：在线的人
        left = tk.Frame(win, bg=G.C_PANEL, width=170)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        tk.Label(left, text=_t("g460"), bg=G.C_PANEL, fg=G.C_TEXT,
                 font=(G.FONT, 10, "bold"), anchor="w").pack(
                     fill="x", padx=12, pady=(14, 2))
        self._lbl_online = tk.Label(left, text=_t("g462") % 0,
                                    bg=G.C_PANEL, fg=G.C_SUB,
                                    font=(G.FONT, 8), anchor="w")
        self._lbl_online.pack(fill="x", padx=12, pady=(0, 8))

        self._roster_box = tk.Listbox(
            left, bg=G.C_PANEL, fg=G.C_TEXT, font=(G.FONT, 9),
            relief="flat", highlightthickness=0, activestyle="none",
            selectbackground=G.C_CARD, selectforeground=G.C_TEXT)
        self._roster_box.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        tk.Label(left, text="", bg=G.C_PANEL).pack(fill="x", pady=2)
        self._mk_side_btn(left, _t("g470"), self._rename)
        self._mk_side_btn(left, _t("g472"), self._clear_history)

        # ---- 右侧
        right = tk.Frame(win, bg=G.C_BG)
        right.pack(side="left", fill="both", expand=True)

        # 输入区 + 按钮栏必须先占底，再放会 expand 的消息区
        bar = tk.Frame(right, bg=G.C_BG)
        bar.pack(side="bottom", fill="x", padx=12, pady=(6, 12))

        self._hint = tk.Label(bar, text="", bg=G.C_BG, fg=G.C_SUB,
                              font=(G.FONT, 8))
        self._hint.pack(side="left")

        self._btn_send = self._mk_btn(bar, _t("g461"), self._do_send,
                                      G.C_BLUE)
        self._btn_send.pack(side="right")

        box = tk.Frame(right, bg=G.C_BG)
        box.pack(side="bottom", fill="x", padx=12, pady=(0, 4))
        wrap_in = tk.Frame(box, bg=G.C_LINE)
        wrap_in.pack(fill="x")
        self._input = tk.Text(wrap_in, height=3, width=40, font=(G.FONT, 10),
                              bg=G.C_CARD, fg=G.C_TEXT, relief="flat",
                              wrap="word", padx=8, pady=6)
        sb_in = ttk.Scrollbar(wrap_in, orient="vertical",
                              command=self._input.yview)
        self._input.configure(yscrollcommand=sb_in.set)
        sb_in.pack(side="right", fill="y")
        self._input.pack(side="left", fill="both", expand=True, padx=1, pady=1)
        self._input.bind("<Return>", self._on_enter)
        self._input.bind("<Shift-Return>", lambda e: None)

        # ---- 消息区（最后 pack，占剩下的地方）
        wrap = tk.Frame(right, bg=G.C_LINE)
        wrap.pack(fill="both", expand=True, padx=12, pady=(12, 6))
        self._list = tk.Text(wrap, font=(G.FONT, 10), bg=G.C_CARD,
                             fg=G.C_TEXT, relief="flat", wrap="word",
                             padx=10, pady=8, height=10, width=40,
                             state="disabled", cursor="arrow")
        sb = ttk.Scrollbar(wrap, orient="vertical", command=self._list.yview)
        self._list.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._list.pack(side="left", fill="both", expand=True, padx=1, pady=1)
        self._list.tag_config("who", foreground=G.C_BLUE,
                              font=(G.FONT, 9, "bold"))
        self._list.tag_config("me", foreground=G.C_PURPLE,
                              font=(G.FONT, 9, "bold"))
        self._list.tag_config("time", foreground=G.C_SUB, font=(G.FONT, 7))
        self._list.tag_config("body", foreground=G.C_TEXT, font=(G.FONT, 10))

        win.protocol("WM_DELETE_WINDOW", self.close)
        win.bind("<Escape>", lambda _e: self.close())

        self._render_history()
        self.refresh_roster()
        self._input.focus_set()

    def close(self):
        w = self.win
        self.win = None
        try:
            if w is not None:
                w.destroy()
        except Exception:
            pass

    # ------------------------------------------------------------ 小工具

    def _mk_btn(self, parent, text, cmd, color):
        G = self._ui()
        b = tk.Button(parent, text=text, command=cmd, bg=color,
                      fg="#ffffff", font=(G.FONT, 9), relief="flat",
                      cursor="hand2", padx=14, pady=5,
                      activebackground=color, activeforeground="#ffffff")
        return b

    def _mk_side_btn(self, parent, text, cmd):
        G = self._ui()
        b = tk.Button(parent, text=text, command=cmd, bg=G.C_PANEL,
                      fg=G.C_SUB, font=(G.FONT, 8), relief="flat",
                      cursor="hand2", anchor="w", padx=10, pady=4,
                      activebackground=G.C_CARD, activeforeground=G.C_TEXT,
                      bd=0, highlightthickness=0)
        b.pack(fill="x", padx=4, pady=1)
        return b

    # ------------------------------------------------------------ 成员

    def refresh_roster(self):
        if self.win is None or self._roster_box is None:
            return
        try:
            peers = self.app.chat_roster.online()
        except Exception:
            peers = []
        try:
            self._roster_box.delete(0, "end")
            for p in peers:
                self._roster_box.insert("end", "● " + p["name"])
            self._lbl_online.config(text=_t("g462") % len(peers))
            if peers:
                self._hint.config(text="")
            else:
                self._hint.config(text=_t("g476"))
        except Exception:
            pass

    # ------------------------------------------------------------ 消息

    def _fmt_time(self, ts):
        try:
            return time.strftime("%H:%M", time.localtime(float(ts)))
        except Exception:
            return ""

    def _append(self, msg, mine=False):
        if self._list is None:
            return
        try:
            self._list.config(state="normal")
            self._list.insert("end", self._fmt_time(msg.get("ts")) + "  ",
                              "time")
            who = _t("g465") if mine else (msg.get("from") or "?")
            self._list.insert("end", who + "\n", "me" if mine else "who")
            self._list.insert("end", (msg.get("body") or "") + "\n\n", "body")
            self._list.see("end")
            self._list.config(state="disabled")
        except Exception:
            pass

    def _render_history(self):
        try:
            items = self.app.chat_store.recent(200)
        except Exception:
            items = []
        for m in items:
            self._append(m, mine=(m.get("from") == self.app.chat_name))
        if not items and self._list is not None:
            try:
                self._list.config(state="normal")
                self._list.insert("end", _t("g463") + "\n", "time")
                self._list.config(state="disabled")
            except Exception:
                pass

    def on_incoming(self, msg):
        """App 收到消息后调这里。窗口没开也要存（App 负责存）。"""
        if self.win is None:
            return
        self._append(msg, mine=False)

    # ------------------------------------------------------------ 发送

    def _on_enter(self, event):
        # Shift+回车 = 换行；直接回车 = 发
        if event.state & 0x0001:      # Shift
            return None
        self._do_send()
        return "break"

    def _do_send(self):
        if self._sending or self._input is None:
            return
        body = self._input.get("1.0", "end-1c").strip()
        if not body:
            return
        self._input.delete("1.0", "end")
        self._sending = True
        try:
            self._btn_send.config(state="disabled")
            self._hint.config(text=_t("g469"))
        except Exception:
            pass
        self.app.chat_send(body, on_done=self._send_done)

    def _send_done(self, ok_n, fail, msg):
        self._sending = False
        if self.win is None:
            return
        try:
            self._btn_send.config(state="normal")
            self._hint.config(text="")
        except Exception:
            pass
        if ok_n:
            self._append(msg, mine=True)
        if fail:
            try:
                messagebox.showwarning(
                    _t("g460"), _t("g467") % "; ".join(fail)[:300],
                    parent=self.win)
            except Exception:
                pass

    # ------------------------------------------------------------ 设置

    def _rename(self):
        from tkinter import simpledialog
        cur = self.app.chat_name
        new = simpledialog.askstring(_t("g470"),
                                     _t("g471") + "\n\n" + _t("g470") + "：",
                                     initialvalue=cur, parent=self.win)
        if new:
            self.app.set_chat_name(new)
            self.refresh_roster()

    def _clear_history(self):
        if not messagebox.askyesno(_t("g472"), _t("g473"), parent=self.win):
            return
        try:
            self.app.chat_store.clear()
        except Exception:
            pass
        if self._list is not None:
            try:
                self._list.config(state="normal")
                self._list.delete("1.0", "end")
                self._list.config(state="disabled")
            except Exception:
                pass
