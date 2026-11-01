#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LanSplice macOS 自检
====================

    python3 mac_check.py                十几秒，不传文件
    python3 mac_check.py --full         连回环收发 + 图形界面一起测
    python3 mac_check.py --report URL   测完把报告 POST 回去（可选）

全程在临时目录里跑，不改系统、不碰现有配置。
只支持 macOS —— 在别的系统上跑会直接告诉你它什么都不做。
"""
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = []
PORTS = range(47900, 48000)
STAT = {"pass": 0, "fail": 0, "skip": 0, "fail_names": []}


def say(s=""):
    print(s)
    LOG.append(str(s))


def sec(s):
    say("")
    say("―― %s" % s)


def ok(name, extra=""):
    STAT["pass"] += 1
    say("  [通过] %s %s" % (name, extra))


def bad(name, extra=""):
    STAT["fail"] += 1
    STAT["fail_names"].append(name)
    say("  [失败] %s %s" % (name, extra))


def skp(name, why):
    STAT["skip"] += 1
    say("  [跳过] %s —— %s" % (name, why))


def sha256_of(p):
    import hashlib
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 16), b""):
            h.update(b)
    return h.hexdigest()


def free_port():
    for p in PORTS:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind(("127.0.0.1", p))
            s.close()
            return p
        except OSError:
            s.close()
    return 0


def wait_port(port, secmax):
    end = time.time() + secmax
    while time.time() < end:
        s = socket.socket()
        s.settimeout(0.4)
        try:
            s.connect(("127.0.0.1", port))
            s.close()
            return True
        except OSError:
            s.close()
            time.sleep(0.3)
    return False


def run(args, timeout=30, env=None):
    e = dict(os.environ)
    e.setdefault("PYTHONIOENCODING", "utf-8")
    if env:
        e.update(env)
    try:
        p = subprocess.run(args, capture_output=True, timeout=timeout, env=e)
        return p.returncode, (p.stdout or b"").decode("utf-8", "replace"), \
            (p.stderr or b"").decode("utf-8", "replace")
    except Exception as ex:
        return -1, "", "%s: %s" % (type(ex).__name__, ex)


def compile_all():
    import py_compile
    n = 0
    for f in sorted(os.listdir(HERE)):
        if not f.endswith(".py") or f.startswith("_"):
            continue
        py_compile.compile(os.path.join(HERE, f), doraise=True)
        n += 1
    return n


def t_deps():
    sec("1. 依赖：cryptography（真做一次加解密，不看 import 脸色）")
    try:
        import cryptography
        from cryptography.hazmat.primitives.asymmetric.x25519 import (
            X25519PrivateKey)
        from cryptography.hazmat.primitives.kdf.hkdf import HKDF
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        a = X25519PrivateKey.generate()
        b = X25519PrivateKey.generate()
        shared = a.exchange(b.public_key())
        key = HKDF(algorithm=hashes.SHA256(), length=32, salt=None,
                   info=b"lansplice").derive(shared)
        c = AESGCM(key)
        nonce = b"0123456789ab"
        assert c.decrypt(nonce, c.encrypt(nonce, b"ok", None), None) == b"ok"
        ok("cryptography", "版本 %s，X25519+AESGCM 回环通过"
           % getattr(cryptography, "__version__", "?"))
        return True
    except Exception as ex:
        bad("cryptography 可用",
            "%s —— python3 -m pip install cryptography" % ex)
        return False


def main():
    full = "--full" in sys.argv
    url = ""
    if "--report" in sys.argv:
        i = sys.argv.index("--report")
        url = sys.argv[i + 1] if i + 1 < len(sys.argv) else ""

    if sys.platform != "darwin":
        say("这个脚本只在 macOS 上跑（当前 %s）。" % sys.platform)
        return 2

    sec("0. 环境")
    v = sys.version_info
    say("  Python %s.%s.%s" % (v[0], v[1], v[2]))
    say("  架构 %s" % os.uname().machine)
    try:
        r = subprocess.run(["sw_vers", "-productVersion"],
                           capture_output=True, timeout=5)
        say("  macOS %s" % r.stdout.decode().strip())
    except Exception:
        pass
    if v < (3, 7):
        bad("Python 版本", "要 3.7 以上")
        return 2
    ok("Python 版本")

    t_deps()

    sec("2. tkinter")
    has_tk = False
    try:
        import tkinter
        has_tk = True
        ok("tkinter", "Tk %s" % tkinter.TkVersion)
    except Exception as ex:
        bad("tkinter 可用", "%s —— python.org 的安装包自带；"
            "Homebrew 装的要 brew install python-tk" % ex)

    sec("3. 源码编译（当前 Python 语法全过一遍）")
    try:
        n = compile_all()
        ok("%d 个 .py 全部编译通过" % n)
    except Exception as ex:
        bad("源码编译", "%s" % ex)

    sec("4. 模块导入")
    got = {}
    for mod in ("link2pc_core", "link2pc_paths", "link2pc_platform",
                "link2pc_history", "link2pc_deps", "link2pc_i18n",
                "link2pc_web", "link2pc_cli",
                # 聊天（v1.7.3 加的）。GUI 里是 try/except 导入的，
                # 缺了不报错、只是「没有聊天」—— 所以单独查一遍。
                "link2pc_chat", "link2pc_chatwin"):
        sys.modules.pop(mod, None)
        try:
            got[mod] = __import__(mod)
            ok(mod)
        except Exception as ex:
            bad(mod, "%s" % ex)

    # 聊天逻辑真跑一遍：造一条消息、进成员表、存一条历史再读回来。
    # 这比「import 成功」有用得多 —— 模块能导入但逻辑坏了，一样是坏的。
    CH = got.get("link2pc_chat")
    if CH is None:
        skp("聊天逻辑", "模块没导进来")
    else:
        try:
            m = CH.make_msg("自检消息", "selfcheck")
            assert m.get("body") == "自检消息", m
            r = CH.Roster()
            r.update({"name": "本机", "port": 47820, "ip": "127.0.0.1"})
            assert r.online(), "成员表没记上"
            tmp = os.path.join(tmpbase, "chat-test.jsonl")
            st = CH.ChatStore(tmp)
            st.append(m)
            got_msg = st.recent(1)
            assert got_msg and got_msg[0]["body"] == "自检消息", got_msg
            ok("聊天逻辑：造消息 / 成员表 / 存取历史", "一条消息往返正常")
        except Exception as ex:
            bad("聊天逻辑", "%s: %s" % (type(ex).__name__, ex))

    sec("5. 数据目录（~/Library/Application Support）")
    try:
        pp = got.get("link2pc_paths")
        cfg, data = pp.config_dir(), pp.data_dir()
        say("  配置 %s" % cfg)
        say("  数据 %s" % data)
        good = ("Library" in cfg and "Application Support" in cfg
                and cfg != data)
        if good:
            ok("macOS 目录规范")
        else:
            bad("macOS 目录规范", "落在 %s —— 不对" % cfg)
    except Exception as ex:
        bad("目录规范", "%s" % ex)

    sec("6. 单实例锁（flock，第二个进程要被挡下）")
    try:
        pf = got.get("link2pc_platform")
        if pf.single_instance("LanSplice-check-mac"):
            if pf.single_instance("LanSplice-check-mac"):
                bad("第二个进程被挡下", "居然也抢到了锁")
            else:
                ok("第二个进程被挡下")
        else:
            skp("单实例锁", "第一个锁就没抢到（可能程序本体在跑）")
    except Exception as ex:
        bad("单实例锁", "%s" % ex)

    sec("7. 开机自启（LaunchAgent plist，写到临时目录）")
    try:
        pf = got.get("link2pc_platform")
        real_expand = pf.os.path.expanduser
        tmp = tempfile.mkdtemp(prefix="lansplice-check-")
        pf.os.path.expanduser = lambda p: p.replace("~", tmp)
        try:
            if pf.autostart_set(True):
                with open(pf._mac_launch_file(), encoding="utf-8") as f:
                    body = f.read()
                if "com.lansplice.app" in body and "RunAtLoad" in body:
                    ok("plist 写入且内容正确")
                else:
                    bad("plist 写入", "内容不对")
                pf.autostart_set(False)
                if not os.path.exists(pf._mac_launch_file()):
                    ok("plist 清理")
                else:
                    bad("plist 清理", "文件还在")
            else:
                bad("plist 写入", "autostart_set 返回 False")
        finally:
            pf.os.path.expanduser = real_expand
            shutil.rmtree(tmp, ignore_errors=True)
    except Exception as ex:
        bad("开机自启", "%s" % ex)

    sec("8. 防火墙提示")
    try:
        cmd = got["link2pc_platform"].firewall_manual_command()
        if cmd:
            ok("socketfilterfw 命令", cmd[:80])
        else:
            bad("防火墙提示", "返回空")
    except Exception as ex:
        bad("防火墙提示", "%s" % ex)

    sec("9. 命令行")
    cli = os.path.join(HERE, "link2pc_cli.py")
    rc, out, err = run([sys.executable, "-B", cli, "version"])
    if rc == 0 and "LanSplice" in out:
        ok("version", out.splitlines()[0])
    else:
        bad("version", "rc=%d %s" % (rc, (err or out)[-160:]))

    if not full:
        _summary(url)
        return 1 if STAT["fail"] else 0

    sec("10. 回环真传（中文文件名 + 子目录）")
    try:
        import link2pc_core as L
        port = free_port()
        tmp = tempfile.mkdtemp(prefix="lansplice-e2e-")
        recv = os.path.join(tmp, "收件箱")
        os.makedirs(recv)
        src = os.path.join(tmp, "发件")
        os.makedirs(os.path.join(src, "子目录"))
        f1 = os.path.join(src, "中文 文件名 (测试).txt")
        with open(f1, "wb") as f:
            f.write(("你好 macOS %s\n" % time.ctime()).encode("utf-8"))
        f2 = os.path.join(src, "子目录", "a.bin")
        with open(f2, "wb") as f:
            f.write(os.urandom(200 * 1024))
        code = L.key_to_code(L.new_pair_key())
        logf = open(os.path.join(tmp, "serve.log"), "w+")
        sp = subprocess.Popen(
            [sys.executable, "-B", cli, "serve", "--root", recv,
             "--port", str(port), "--code", code, "--once",
             "--timeout", "40", "--no-discovery"],
            stdout=logf, stderr=subprocess.STDOUT, cwd=HERE)
        if not wait_port(port, 15):
            bad("接收端起来了", "15 秒没监听上 %d" % port)
        else:
            ok("接收端起来了", "端口 %d" % port)
            rc, out, err = run([sys.executable, "-B", cli, "send", src,
                                "--to", "127.0.0.1:%d" % port,
                                "--code", code], timeout=90)
            if rc != 0:
                bad("发送端返回 0", (err or out)[-300:])
            else:
                ok("发送端返回 0")
            top = os.path.basename(src)
            want = {os.path.join(top, "中文 文件名 (测试).txt"): f1,
                    os.path.join(top, "子目录", "a.bin"): f2}
            end = time.time() + 20
            while time.time() < end:
                if all(os.path.exists(os.path.join(recv, k))
                       for k in want):
                    break
                time.sleep(0.4)
            for rel, local in want.items():
                dst = os.path.join(recv, rel)
                if not os.path.exists(dst):
                    bad("收到 %s" % rel, "文件没到")
                elif sha256_of(dst) == sha256_of(local):
                    ok("收到且内容一致", rel)
                else:
                    bad("收到且内容一致", rel)
        try:
            if sp.poll() is None:
                sp.terminate()
                sp.wait(timeout=5)
        except Exception:
            pass
        logf.close()
        shutil.rmtree(tmp, ignore_errors=True)
    except Exception as ex:
        bad("回环真传", "%s: %s" % (type(ex).__name__, ex))

    sec("11. 图形界面（真起一次窗口，9 秒）")
    if not has_tk:
        skp("图形界面", "没有 tkinter")
    else:
        gui = os.path.join(HERE, "link2pc_gui.py")
        tmp = tempfile.mkdtemp(prefix="lansplice-gui-")
        e = dict(os.environ)
        e["HOME"] = tmp            # 隔离配置，不碰正在跑的实例
        e["PYTHONIOENCODING"] = "utf-8"
        logf = open(os.path.join(tmp, "gui.log"), "w+")
        p = None
        try:
            p = subprocess.Popen([sys.executable, "-B", gui], stdout=logf,
                                 stderr=subprocess.STDOUT, cwd=HERE, env=e)
            time.sleep(9)
            if p.poll() is None:
                ok("图形界面跑了 9 秒没退出")
            else:
                bad("图形界面跑了 9 秒没退出",
                    "提前退出，返回码 %s" % p.returncode)
            logf.flush()
            with open(os.path.join(tmp, "gui.log"), encoding="utf-8",
                      errors="replace") as f:
                txt = f.read()
            if "Traceback" in txt:
                bad("启动无异常", txt.strip()[-400:])
            else:
                ok("启动无异常（stderr 无 Traceback）")
            say("         → 窗口应该已经弹出来了，脚本会自己关")
        finally:
            try:
                if p and p.poll() is None:
                    p.terminate()
                    p.wait(timeout=5)
            except Exception:
                pass
            logf.close()
            shutil.rmtree(tmp, ignore_errors=True)

    _summary(url)
    return 1 if STAT["fail"] else 0


def _summary(url):
    sec("汇总")
    say("通过 %d 项，失败 %d 项，跳过 %d 项"
        % (STAT["pass"], STAT["fail"], STAT["skip"]))
    for n in STAT["fail_names"]:
        say("  ✗ %s" % n)
    say("")
    say(STAT["fail"] == 0 and " ✓ 全部通过" or " ✗ 有未通过的项")
    if url:
        try:
            import urllib.request
            req = urllib.request.Request(
                url, data=("\n".join(LOG) + "\n").encode("utf-8"),
                method="POST")
            urllib.request.urlopen(req, timeout=30).read()
            say(" 报告已传回 %s" % url)
        except Exception as ex:
            say(" 报告回传失败：%s" % ex)


if __name__ == "__main__":
    sys.exit(main())
