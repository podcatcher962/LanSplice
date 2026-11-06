# -*- coding: utf-8 -*-
"""LanSplice 内置的网络体检窗口（v2.0.0 并入）。

它原来是独立程序 LanPulse。并进来的理由不是「少一个图标」，而是：
用户打开体检的时机，八成就是 LanSplice 连不上的时候。分成两个 exe
之后，对端 IP 要手抄、配色是另一套、报告落款是另一个名字 —— 处处都在
提醒「这是两个软件」。

并进来之后：

  * 配色跟着主窗口走（主窗口换深浅色，这个窗口跟着变）；
  * 对端 IP 由主窗口带进来，不用手输；
  * 诊断规则里提到端口时，指的就是当前这份程序的两个端口；
  * 导出的报告落款是 LanSplice。

窗口是独立的 Toplevel，不是主窗口里的一栏 —— 主界面现在只有「设备」
和「待办」两件事，塞进三栏诊断会把它弄乱。体检是「出事才打开」的东西，
点开一个窗口，比在主界面里挤一块常驻区域合适。
"""
import os
import threading
import time
import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, messagebox, ttk

import link2pc_core
import netcheck_core as C
import netcheck_report as R
import netcheck_rules as A
import netcheck_scan as S
from link2pc_i18n import is_en, t as _t

MONO = "Consolas"


def _G():
    """延迟取主模块。

    主模块要 import 本模块（菜单里那个入口），本模块在导入期再回头
    import 它就会形成循环；放到函数里就断开了。
    """
    import link2pc_gui
    return link2pc_gui


def palette():
    """把主窗口当前那套配色翻译成本窗口要用的角色名。"""
    G = _G()
    P = G.PALETTE
    dark = P["bg"].lower() == G.THEME_DARK["bg"].lower()
    return {
        "bg": P["bg"], "card": P["card"], "ink": P["text"], "sub": P["sub"],
        "line": P["line"], "head": P["panel"], "sel": P["sel"],
        "field": P["field"],
        "btn": P["blue"], "btn_ink": "#0e1a22" if dark else P["white"],
        "ghost": P["gray_btn"], "ghost_ink": P["white"],
        "err": P["red"], "warn": P["warn"], "ok": P["green"],
        "dark": dark,
    }


class Window(tk.Toplevel):
    """一屏三段：左看自己，中间看邻居，右边看结论。"""

    def __init__(self, app, peer_ip=None):
        tk.Toplevel.__init__(self, app.root)
        self.app = app
        self.G = _G()
        self.FONT = self.G.FONT
        self.P = palette()
        self.ev = None
        self.secs = 0.0
        self.busy = False
        self.widgets = []
        self.cards = []
        self.card_lbls = []

        self.title(_t("g532") + " · LanSplice v" + link2pc_core.APP_VER)
        self.geometry("1080x690")
        self.minsize(940, 600)
        self.configure(bg=self.P["bg"])
        try:
            self.transient(app.root)
        except tk.TclError:
            pass
        try:
            self.G.set_dark_titlebar(self, self.P["dark"])
        except Exception:
            pass
        try:
            self.iconbitmap(os.path.join(_res_dir(), "app.ico"))
        except Exception:
            pass

        self._build()
        self.apply_theme()
        seed = peer_ip or (getattr(app, "peer_ip", "") or "")
        if seed:
            self.ent_peer.delete(0, "end")
            self.ent_peer.insert(0, seed)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.bind("<Escape>", lambda e: self.close())
        self.after(120, self.run)

    # ------------------------------------------------------------ 布局
    def _build(self):
        F = self.FONT
        self.head = tk.Frame(self, height=58)
        self.head.pack(fill="x", side="top")
        self.head.pack_propagate(False)

        self.lbl_title = tk.Label(self.head, text=_t("g532"),
                                  font=(F, 14, "bold"))
        self.lbl_title.pack(side="left", padx=(16, 6), pady=12)
        self.lbl_ver = tk.Label(self.head, text="v" + link2pc_core.APP_VER
                                + "　·　" + _t("g580"), font=(F, 9))
        self.lbl_ver.pack(side="left", pady=(18, 12))

        self.lbl_peer = tk.Label(self.head, text=_t("g536"), font=(F, 9))
        self.lbl_peer.pack(side="left", padx=(22, 6))
        self.ent_peer = tk.Entry(self.head, width=15, font=(MONO, 10),
                                 relief="flat", highlightthickness=1)
        self.ent_peer.pack(side="left", ipady=4)
        self.ent_peer.bind("<Return>", lambda e: self.run())

        self.btn_go = tk.Button(self.head, text=_t("g537"), font=(F, 10, "bold"),
                                relief="flat", cursor="hand2", command=self.run)
        self.btn_go.pack(side="right", padx=(8, 16), pady=12, ipadx=16, ipady=5)
        self.btn_save = tk.Button(self.head, text=_t("g541"), font=(F, 9),
                                  relief="flat", cursor="hand2", command=self.save)
        self.btn_save.pack(side="right", padx=4, pady=12, ipadx=12, ipady=5)
        self.btn_close = tk.Button(self.head, text=_t("g542"), font=(F, 9),
                                   relief="flat", cursor="hand2", command=self.close)
        self.btn_close.pack(side="right", padx=4, pady=12, ipadx=12, ipady=5)

        self.widgets += [(self.head, "bg", None),
                         (self.lbl_title, "bg", "ink"),
                         (self.lbl_ver, "bg", "sub"),
                         (self.lbl_peer, "bg", "sub")]

        self.body = tk.Frame(self)
        self.body.pack(fill="both", expand=True, padx=14, pady=(4, 8))
        for i, w in enumerate((3, 4, 4)):
            self.body.columnconfigure(i, weight=w, uniform="col")
        self.body.rowconfigure(0, weight=1)
        self.widgets.append((self.body, "bg", None))

        self._build_left(self.body)
        self._build_center(self.body)
        self._build_right(self.body)

        self.foot = tk.Frame(self, height=34)
        self.foot.pack(fill="x", side="bottom")
        self.foot.pack_propagate(False)
        self.lbl_state = tk.Label(self.foot, text=_t("g543"), font=(F, 9),
                                  anchor="w")
        self.lbl_state.pack(side="left", fill="x", expand=True, pady=8,
                            padx=(16, 8))
        self.widgets += [(self.foot, "bg", None), (self.lbl_state, "bg", "sub")]
        self.pb = ttk.Progressbar(self.foot, mode="indeterminate", length=130)

    def _card(self, parent, title):
        outer = tk.Frame(parent, bd=0, highlightthickness=1)
        head = tk.Frame(outer, height=34)
        head.pack(fill="x")
        head.pack_propagate(False)
        lbl = tk.Label(head, text=title, font=(self.FONT, 10, "bold"), anchor="w")
        lbl.pack(side="left", padx=12, pady=7)
        self.card_lbls.append(lbl)
        body = tk.Frame(outer)
        body.pack(fill="both", expand=True, padx=12, pady=(2, 10))
        self.cards.append(outer)
        self.widgets.append((head, "head", None))
        self.widgets.append((lbl, "head", "ink"))
        self.widgets.append((body, "card", None))
        return outer, body

    def _build_left(self, parent):
        outer, body = self._card(parent, _t("g533"))
        outer.grid(row=0, column=0, sticky="nsew", padx=(0, 7))

        # 标签列按最长的那个实测像素宽来定。写死字符宽度的话，
        # 「LanSplice」这种长英文会被 Label 直接裁掉尾巴。
        cap_font = tkfont.Font(font=(self.FONT, 9))
        self.cap_w = max(cap_font.measure(t) for t in (
            _t("g544"), _t("g545"), _t("g546"), "LanSplice")) + 8

        self.lbl_ip = tk.Label(body, text="—", font=(self.FONT, 15, "bold"),
                               anchor="w")
        self.lbl_ip.pack(fill="x", pady=(2, 0))
        self.lbl_nic = tk.Label(body, text="", font=(self.FONT, 9), anchor="w")
        self.lbl_nic.pack(fill="x")
        self.widgets += [(self.lbl_ip, "card", "ink"),
                         (self.lbl_nic, "card", "sub")]

        self.sep1 = tk.Frame(body, height=1)
        self.sep1.pack(fill="x", pady=10)
        self.widgets.append((self.sep1, "line", None))

        self._metric(body, _t("g544"), "gw")
        self._metric(body, _t("g545"), "net")
        self._metric(body, _t("g546"), "lan")
        self._metric(body, "LanSplice", "ls")

        self.lbl_note = tk.Label(body, text="", font=(self.FONT, 9), anchor="w",
                                 justify="left", wraplength=250)
        self.lbl_note.pack(fill="x", pady=(10, 0))
        self.widgets.append((self.lbl_note, "card", "sub"))

    def _metric(self, parent, label, key):
        row = tk.Frame(parent)
        row.pack(fill="x", pady=4)
        self.widgets.append((row, "card", None))
        row.columnconfigure(0, minsize=getattr(self, "cap_w", 72))
        cap = tk.Label(row, text=label, font=(self.FONT, 9), anchor="w")
        cap.grid(row=0, column=0, sticky="w")
        val = tk.Label(row, text="—", font=(MONO, 11), anchor="w")
        val.grid(row=0, column=1, sticky="w", padx=(6, 0))
        self.widgets += [(cap, "card", "sub"), (val, "card", "ink")]
        setattr(self, "v_" + key, val)

    def _build_center(self, parent):
        outer, body = self._card(parent, _t("g534"))
        outer.grid(row=0, column=1, sticky="nsew", padx=7)

        cols = ("ip", "kind", "name")
        self.tree = ttk.Treeview(body, columns=cols, show="headings",
                                 selectmode="browse", style="Diag.Treeview")
        for c, t, w, a in (("ip", _t("g547"), 112, "w"),
                           ("kind", _t("g548"), 56, "w"),
                           ("name", _t("g549"), 150, "w")):
            self.tree.heading(c, text=t, anchor=a)
            self.tree.column(c, width=w, minwidth=60, anchor=a,
                             stretch=(c == "name"))
        self.tree.bind("<<TreeviewSelect>>", self._on_pick)

        self.tree_vs = tk.Scrollbar(body, orient="vertical", width=11,
                                    bd=0, relief="flat",
                                    command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.tree_vs.set)
        # 先占住底部那条，再让表格吃满剩下的 —— 反过来会被树挤没
        self.lbl_dev = tk.Label(body, text="", font=(self.FONT, 9), anchor="w")
        self.lbl_dev.pack(side="bottom", fill="x", pady=(6, 0))
        self.widgets.append((self.lbl_dev, "card", "sub"))
        self.tree.pack(side="left", fill="both", expand=True)

    def _on_pick(self, _ev=None):
        """选中一行时在底部补上 MAC —— 列里放不下，但不想丢掉这个信息。"""
        sel = self.tree.selection()
        if not sel or not self.ev:
            return
        vals = self.tree.item(sel[0], "values")
        ip = vals[0] if vals else ""
        for d in S.hosts(self.ev):
            if d["ip"] == ip:
                mac = d["mac"] or _t("g569")
                self.lbl_dev.config(text=_t("g568") % (ip, mac,
                                                       d["note"] or "—"))
                return

    def _build_right(self, parent):
        outer, body = self._card(parent, _t("g535"))
        outer.grid(row=0, column=2, sticky="nsew", padx=(7, 0))

        self.txt = tk.Text(body, wrap="word", relief="flat", bd=0,
                           highlightthickness=0, font=(self.FONT, 10), height=10,
                           padx=2, pady=2, cursor="arrow")
        vs = tk.Scrollbar(body, orient="vertical", width=11, bd=0,
                          relief="flat", command=self.txt.yview)
        self.txt.configure(yscrollcommand=vs.set)
        self.txt.pack(side="left", fill="both", expand=True)
        vs.pack(side="right", fill="y")
        self.txt_vs = vs
        self.txt.tag_configure("title", font=(self.FONT, 10, "bold"),
                               spacing1=6, spacing3=2)
        self.txt.tag_configure("body", lmargin1=14, lmargin2=14, spacing3=6)
        self.txt.tag_configure("act", lmargin1=14, lmargin2=14, spacing3=10)
        for lvl in ("error", "warn", "ok", "other"):
            self.txt.tag_configure("t_" + lvl, font=(self.FONT, 10, "bold"),
                                   spacing1=6, spacing3=2)
        self.txt.configure(state="disabled")

    # ------------------------------------------------------------ 语言
    def relocalize(self):
        """主窗口切语言时被调：只换文字，不重建控件、不重新扫网络。"""
        self.title(_t("g532") + " · LanSplice v" + link2pc_core.APP_VER)
        self.lbl_title.config(text=_t("g532"))
        self.lbl_ver.config(text="v" + link2pc_core.APP_VER + "　·　" + _t("g580"))
        self.lbl_peer.config(text=_t("g536"))
        self.btn_go.config(text=(_t("g538") if self.busy else _t("g539"))
                           if self.ev else _t("g537"))
        self.btn_save.config(text=_t("g541"))
        self.btn_close.config(text=_t("g542"))
        for lbl, key in zip(self.card_lbls, ("g533", "g534", "g535")):
            lbl.config(text=_t(key))
        for col, key in (("ip", "g547"), ("kind", "g548"), ("name", "g549")):
            self.tree.heading(col, text=_t(key))
        if self.ev:
            self.set_state(_t("g555") % self.secs + "　·　"
                           + (self.ev.get("finished") or ""))
            self.render(self.ev)
        elif not self.busy:
            self.set_state(_t("g543"))

    # ------------------------------------------------------------ 主题
    def on_theme_changed(self):
        """主窗口换配色时被调。这里不重建界面，只换颜色，正在跑的体检不中断。"""
        self.P = palette()
        try:
            self.G.set_dark_titlebar(self, self.P["dark"])
        except Exception:
            pass
        self.apply_theme()

    def apply_theme(self):
        P = self.P
        F = self.FONT
        self.configure(bg=P["bg"])
        for w, bg, fg in self.widgets:
            try:
                w.config(bg=P[bg])
                if fg:
                    w.config(fg=P[fg])
            except tk.TclError:
                pass
        for b, kind in ((self.btn_go, "btn"), (self.btn_save, "ghost"),
                        (self.btn_close, "ghost")):
            ink = P["btn_ink"] if kind == "btn" else P["ghost_ink"]
            b.config(bg=P[kind], fg=ink, activebackground=P[kind],
                     activeforeground=ink, bd=0, highlightthickness=0)
        self.ent_peer.config(bg=P["field"], fg=P["ink"],
                             insertbackground=P["ink"],
                             highlightbackground=P["line"],
                             highlightcolor=P["btn"])
        self.txt.config(bg=P["card"], fg=P["ink"], insertbackground=P["ink"],
                        selectbackground=P["sel"])
        self.txt.tag_configure("title", foreground=P["ink"])
        self.txt.tag_configure("body", foreground=P["sub"])
        self.txt.tag_configure("act", foreground=P["ink"])
        for lvl, key in (("error", "err"), ("warn", "warn"),
                         ("ok", "ok"), ("other", "sub")):
            self.txt.tag_configure("t_" + lvl, foreground=P[key])
        for c in self.cards:
            c.config(bg=P["card"], highlightbackground=P["line"],
                     highlightcolor=P["line"])
        for sb in (self.tree_vs, self.txt_vs):
            try:
                sb.config(bg=P["head"], troughcolor=P["card"],
                          activebackground=P["ghost"],
                          highlightbackground=P["card"],
                          highlightcolor=P["card"])
            except tk.TclError:
                pass

        # 只配 Diag.* 这一套样式，绝不动全局 Treeview ——
        # 主窗口的设备列表也在用那个样式，改它会让列表行高一跳。
        st = ttk.Style()
        try:
            st.theme_use("clam")
        except tk.TclError:
            pass
        st.configure("Diag.Treeview", background=P["card"],
                     fieldbackground=P["card"], foreground=P["ink"],
                     borderwidth=0, relief="flat", lightcolor=P["card"],
                     darkcolor=P["card"], bordercolor=P["card"],
                     rowheight=25, font=(F, 8))
        st.configure("Diag.Treeview.Heading", background=P["head"],
                     foreground=P["sub"], borderwidth=0, relief="flat",
                     font=(F, 9))
        st.map("Diag.Treeview", background=[("selected", P["sel"])],
               foreground=[("selected", P["ink"])])
        st.map("Diag.Treeview.Heading", background=[("active", P["head"])])
        try:
            # clam 给 Treeview 留了一圈浅色 border，深色下像贴了白胶布
            st.layout("Diag.Treeview",
                      [("Diag.Treeview.treearea", {"sticky": "nswe"})])
        except tk.TclError:
            pass
        st.configure("Diag.Horizontal.TProgressbar", background=P["btn"],
                     troughcolor=P["head"], borderwidth=0, thickness=8)

    # ------------------------------------------------------------ 体检
    def run(self):
        if self.busy:
            return
        peer = self.ent_peer.get().strip()
        if peer and not _looks_ip(peer):
            messagebox.showwarning(_t("g571"), _t("g570"), parent=self)
            return
        self.busy = True
        self.btn_go.config(state="disabled", text=_t("g538"))
        try:
            self.pb.config(mode="indeterminate",
                           style="Diag.Horizontal.TProgressbar")
            if not self.pb.winfo_ismapped():
                self.pb.pack(side="left", padx=(4, 14), pady=9,
                             before=self.lbl_state)
            self.pb.start(12)
        except tk.TclError:
            pass
        self.set_state(_t("g554"))
        threading.Thread(target=self._work, args=(peer or None,),
                         daemon=True).start()

    def _work(self, peer):
        t0 = time.time()
        try:
            ev = S.collect(peer_ip=peer, progress=self._progress)
            self.after(0, lambda: self._done(ev, time.time() - t0, None))
        except Exception as exc:
            self.after(0, lambda: self._done(None, 0, exc))

    def _progress(self, msg):
        try:
            self.after(0, lambda: self.set_state(msg))
        except Exception:
            pass

    def _done(self, ev, secs, exc):
        self.busy = False
        try:
            self.pb.stop()
            self.pb.pack_forget()
        except tk.TclError:
            pass
        self.btn_go.config(state="normal", text=_t("g539"))
        if exc:
            self.set_state(_t("g577") % exc)
            messagebox.showerror(_t("g556"), str(exc), parent=self)
            return
        self.ev = ev
        self.secs = secs
        self.set_state(_t("g555") % secs + "　·　" + (ev.get("finished") or ""))
        self.render(ev)

    def set_state(self, txt):
        self.lbl_state.config(text=txt)

    # ------------------------------------------------------------ 渲染
    def render(self, ev):
        P = self.P
        # 结论在这里现算，而不是沿用 collect() 那一遍的结果 —— 切语言时
        # 只要重跑一次规则，右侧整栏就跟着换语言，不用重新扫一遍网络。
        ev["findings"] = A.diagnose(ev)
        main = ev.get("main") or {}
        links = ev.get("links") or {}
        self.lbl_ip.config(text=main.get("ip") or _t("g573"))
        speed = ""
        for k, v in links.items():
            if main.get("ip") and main["ip"] in k:
                speed = "%s · %s" % (v[0], _t("g574") if v[1] else _t("g575"))
                break
        if not speed and links:
            _k, v = list(links.items())[0]
            speed = "%s · %s" % (v[0], _t("g574") if v[1] else _t("g575"))
        # 地址/掩码/速率是纯格式串，不进文案表 —— 中英文在这里没有区别
        self.lbl_nic.config(text="%s/%d　%s" % (main.get("ip", "—"),
                                                main.get("prefix", 24), speed))

        self.v_gw.config(text=_ms(ev.get("gateway_stats") or {}))
        self.v_net.config(text=_ms(ev.get("internet_stats") or {}))
        hosts = S.hosts(ev)
        self.v_lan.config(text=_t("g581") % len(hosts))

        listen = ev.get("listening") or {}
        mine = [n for n in listen.values()
                if "lansplice" in (n or "").lower() or "link2pc" in (n or "").lower()]
        if mine:
            self.v_ls.config(text=_t("g564"))
        elif listen:
            self.v_ls.config(text=_t("g566"))
        else:
            self.v_ls.config(text=_t("g565"))
        self.lbl_note.config(text=_t("g567") % (ev.get("gateway_ip") or "—",
                                                S.INTERNET_TARGET))

        self.tree.delete(*self.tree.get_children())
        kind_txt = {"gateway": _t("g550"), "pc": _t("g551"),
                    "phone": _t("g552"), "other": _t("g553")}
        for d in hosts:
            self.tree.insert("", "end", values=(
                d["ip"], kind_txt.get(d["kind"], _t("g553")),
                d["name"] or "—"))
        self.lbl_dev.config(text=_t("g563") % len(hosts))
        # 设备少的时候不摆一根空滚动条，看着像还有内容似的
        try:
            if len(hosts) > 12:
                if not self.tree_vs.winfo_ismapped():
                    self.tree_vs.pack(side="right", fill="y")
            else:
                self.tree_vs.pack_forget()
        except tk.TclError:
            pass

        self.txt.configure(state="normal")
        self.txt.delete("1.0", "end")
        for f in ev.get("findings") or []:
            lvl = f["level"]
            mark = {"error": "×  ", "warn": "!  ", "ok": "✓  "}.get(lvl, "·  ")
            tag = "t_" + lvl if lvl in ("error", "warn", "ok") else "title"
            self.txt.insert("end", mark + f["title"] + "\n", (tag,))
            self.txt.insert("end", f["detail"] + "\n", ("body",))
            if f.get("action"):
                self.txt.insert("end", "→ " + f["action"] + "\n", ("act",))
        self.txt.configure(state="disabled")

    # ------------------------------------------------------------ 导出
    def save(self):
        if not self.ev:
            messagebox.showinfo(_t("g557"), _t("g558"), parent=self)
            return
        stem = "LanSplice-Checkup" if is_en() else "LanSplice-网络体检"
        name = "%s-%s.html" % (stem, time.strftime("%Y%m%d-%H%M"))
        path = filedialog.asksaveasfilename(
            parent=self, title=_t("g559"), defaultextension=".html",
            initialfile=name, filetypes=[("HTML", "*.html")])
        if not path:
            return
        try:
            R.save(self.ev, path)
        except Exception as exc:
            messagebox.showerror(_t("g556"), str(exc), parent=self)
            return
        self.set_state(_t("g560") % path)
        if messagebox.askyesno(_t("g561"), _t("g562") % path, parent=self):
            try:
                os.startfile(path)
            except Exception:
                pass

    def close(self):
        try:
            app = getattr(self, "app", None)
            if app is not None and getattr(app, "_diag_win", None) is self:
                app._diag_win = None
        except Exception:
            pass
        self.destroy()


# ---------------------------------------------------------------- 工具

def _res_dir():
    """图标这类随包资源的目录。打包后是解压出来的临时目录。"""
    import sys
    return getattr(sys, "_MEIPASS",
                   os.path.dirname(os.path.abspath(__file__)))


def _ms(st):
    if not st:
        return "—"
    if not st.get("recv"):
        return _t("g578")
    if st.get("avg") is None:
        return "—"
    avg = st["avg"]
    s = "<1 ms" if avg < 1 else "%.1f ms" % avg
    if st.get("loss"):
        s += " · -%d%%" % round(st["loss"])
    return s


def _looks_ip(s):
    parts = s.split(".")
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(p) <= 255 for p in parts)
    except ValueError:
        return False


def open_window(app, peer_ip=None):
    """主窗口的「连接诊断」入口。同一个窗口只开一个，再点就抬起来。"""
    win = getattr(app, "_diag_win", None)
    if win is not None:
        try:
            if win.winfo_exists():
                if peer_ip:
                    win.ent_peer.delete(0, "end")
                    win.ent_peer.insert(0, peer_ip)
                win.deiconify()
                win.lift()
                win.focus_force()
                return win
        except tk.TclError:
            pass
    win = Window(app, peer_ip)
    app._diag_win = win
    return win
