# -*- coding: utf-8 -*-
"""
LanSplice 命令行
================
给批处理和计划任务用的最小接口：

    LanSplice.exe send D:\\音频\\*.mp3 --to 192.168.1.20
    LanSplice.exe send E:\\备份文件夹 --to 192.168.1.20:47820 --verify
    LanSplice.exe devices
    LanSplice.exe version

打包出来的是 windowed exe（双击不能弹黑框），所以从命令行调用时
必须先 AttachConsole 把控制台抢回来，否则一个字都看不到 —— 这一点
在开发时非常容易忽略：直接双击运行是正常的，从 cmd 里跑就是全程静默。
"""

import os
import sys
import glob
import time
import base64
import argparse

import link2pc_core as L
from link2pc_i18n import t as _t


def _force_utf8_out():
    """
    让输出不再因为「编不出来」而崩掉。

    中文 Windows 的 cmd 默认是 GBK（cp936），而 `©`（U+00A9）根本不在 GBK 里，
    一 print 就抛 UnicodeEncodeError —— 程序直接崩，用户只看到一个异常对话框。
    所以：真控制台先把代码页切到 65001，再把输出流改成 UTF-8（编不出来就替成 ?），
    管道和重定向到文件的情况本来就是 UTF-8 更合适。
    """
    if os.name == "nt":
        try:
            import ctypes
            k32 = ctypes.windll.kernel32
            h = k32.GetStdHandle(-11)          # STD_OUTPUT_HANDLE
            # GetFileType: 0=UNKNOWN 1=DISK 2=CHAR(真控制台) 3=PIPE
            if k32.GetFileType(h) == 2:
                k32.SetConsoleOutputCP(65001)
                k32.SetConsoleCP(65001)
        except Exception:
            pass
    for s in (sys.stdout, sys.stderr):
        if s is None:
            continue
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def _attach_console():
    """
    把父进程的控制台接过来。

    成功返回 True；失败（比如从资源管理器双击）就自己开一个窗口，
    至少让用户看到 error 而不是「点了没反应」。

    源码从终端里跑时 stdout 本来就在，这时候不要去抢 CONOUT$ ——
    那会让输出绕过管道，测试脚本就抓不到任何东西了。
    但编码还是要修一遍：管道里的 gbk 写不了 ©，一样会崩。
    """
    if os.name != "nt":
        return True
    if sys.stdout is not None:
        try:
            sys.stdout.fileno()
            _force_utf8_out()
            return True
        except Exception:
            pass
    try:
        import ctypes
        ATTACH_PARENT_PROCESS = -1
        if not ctypes.windll.kernel32.AttachConsole(ATTACH_PARENT_PROCESS):
            ctypes.windll.kernel32.AllocConsole()
    except Exception:
        return False
    try:
        sys.stdout = open("CONOUT$", "w", encoding="utf-8", errors="replace",
                          buffering=1)
        sys.stderr = sys.stdout
        sys.stdin = open("CONIN$", "r", encoding="utf-8", errors="replace")
    except Exception:
        pass
    _force_utf8_out()
    return True


def _cfg():
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    p = os.path.join(base, "LanSplice", "config.json")
    try:
        import json
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return {}


def _pair_key(cfg, code):
    if code:
        return L.code_to_key(code)
    raw = cfg.get("pair_key")
    if not raw:
        print(_t("cli01"))
        # 「还没开始就失败」统一给 2，和「传了一半失败」的 1 分开：
        # 前者重跑一百次也一样，后者重跑才是对的。
        raise SystemExit(2)
    return base64.b64decode(raw)


def _parse_to(s):
    """192.168.1.20 或 192.168.1.20:47820"""
    s = (s or "").strip()
    if ":" in s:
        ip, _, port = s.partition(":")
        try:
            return ip.strip(), int(port)
        except Exception:
            print(_t("cli02") % s)
            raise SystemExit(2)
    return s, L.TCP_PORT


def _expand(paths):
    """支持通配符（cmd 下用户习惯写 *.mp3）。"""
    out = []
    for p in paths:
        if any(ch in p for ch in "*?"):
            out.extend(sorted(glob.glob(p)))
        else:
            out.append(p)
    return out


def _progress_factory(name, total):
    state = {"last": 0.0, "t0": time.time()}

    def cb(done, tot, spd):
        now = time.time()
        if now - state["last"] < 0.1 and done < tot:
            return
        state["last"] = now
        pct = int(done * 100 / tot) if tot else 100
        bar_w = 24
        filled = int(bar_w * pct / 100)
        bar = "#" * filled + "-" * (bar_w - filled)
        sys.stdout.write("\r  [%s] %3d%%  %-10s %8s / %s" % (
            bar, pct, _speed(spd), L.human_size(done), L.human_size(tot)))
        sys.stdout.flush()

    return cb


def _speed(bps):
    if not bps or bps <= 0:
        return "-"
    if bps < 1024 * 1024:
        return "%.0f KB/s" % (bps / 1024.0)
    return "%.1f MB/s" % (bps / 1048576.0)


# ---------------------------------------------------------------- 子命令

def cmd_send(a):
    cfg = _cfg()
    key = _pair_key(cfg, a.code)
    ip, port = _parse_to(a.to)
    paths = _expand(a.paths)
    if not paths:
        print(_t("cli03"))
        return 2

    targets = L.collect_targets(paths)
    if not targets:
        print(_t("cli03"))
        return 1
    total_bytes = sum(os.path.getsize(p) for p, _ in targets
                      if os.path.isfile(p))

    print(_t("cli04") % (len(targets), L.human_size(total_bytes), ip, port))
    t0 = time.time()
    try:
        cli = L.LinkClient(ip, port, key, timeout=L.CONNECT_TIMEOUT).open()
    except L.AuthError:
        print(_t("cli05"))
        return 2
    except Exception as e:
        # 不直接 print(e)：socket 的原文是 "timed out" / "[WinError 10061] ..."，
        # 对普通用户等于没说。分类之后再讲。
        print(L.conn_error_text(e, ip, port))
        return 2

    ok_n = skip_n = 0
    failed = []
    try:
        for i, (local, rel) in enumerate(targets, 1):
            size = os.path.getsize(local)
            print("\n[%d/%d] %s  (%s)" % (i, len(targets), rel,
                                          L.human_size(size)))
            try:
                skipped, sent, final_rel = cli.upload(
                    local, rel, progress=_progress_factory(rel, size),
                    overwrite=a.overwrite, deep_verify=a.verify)
                sys.stdout.write("\n")
                if skipped:
                    skip_n += 1
                    print(_t("cli07"))
                else:
                    ok_n += 1
                    if final_rel and final_rel != rel:
                        print(_t("cli08") % final_rel)
            except Exception as e:
                sys.stdout.write("\n")
                failed.append((rel, str(e)))
                print(_t("cli09") % e)
    finally:
        try:
            cli.close()
        except Exception:
            pass

    secs = max(0.001, time.time() - t0)
    print("\n" + "-" * 58)
    print(_t("cli10") % (ok_n, skip_n, len(failed), secs,
                         total_bytes / secs / 1048576.0))
    if failed:
        for rel, err in failed[:10]:
            print("  %s: %s" % (rel, err))
        return 1
    return 0


def cmd_devices(a):
    print(_t("cli11"))
    found = L.discover(timeout=a.timeout)
    if not found:
        print(_t("cli12"))
        return 1
    print("-" * 58)
    for d in found:
        print("  %-16s :%-6d %s" % (d.get("ip", "?"), int(d.get("port") or 0),
                                    d.get("name") or ""))
    print("-" * 58)
    print(_t("cli13") % len(found))
    return 0


def cmd_version(a):
    print("LanSplice %s" % L.APP_VER)
    print("© 永远的兰兰")
    print("https://github.com/podcatcher962/LanSplice")
    return 0


# ---------------------------------------------------------------- 入口

def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        return None                     # 无参数交回 GUI

    p = argparse.ArgumentParser(
        prog="LanSplice",
        description="双机局域网直传 · 命令行",
        add_help=True)
    sub = p.add_subparsers(dest="cmd")

    s = sub.add_parser("send", help="发送文件或文件夹到对端")
    s.add_argument("paths", nargs="+", help="文件/文件夹路径，支持通配符")
    s.add_argument("--to", required=True, help="对端地址 ip[:port]")
    s.add_argument("--code", help="配对码（默认用本机配置里的）")
    s.add_argument("--overwrite", action="store_true",
                   help="对端有同名文件时直接覆盖（默认另存为 xxx (2).ext）")
    s.add_argument("--verify", action="store_true",
                   help="传完再校验一遍（慢，但能查出读写出错）")

    d = sub.add_parser("devices", help="扫描局域网里的设备")
    d.add_argument("--timeout", type=float, default=1.5)

    sub.add_parser("version", help="显示版本")

    a = p.parse_args(argv)
    if a.cmd == "send":
        return cmd_send(a)
    if a.cmd == "devices":
        return cmd_devices(a)
    if a.cmd == "version":
        return cmd_version(a)
    p.print_help()
    return 1
