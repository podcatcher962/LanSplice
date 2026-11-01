# -*- coding: utf-8 -*-
"""
传输历史
========
一行一条 JSON 追加到 %APPDATA%\\LanSplice\\history.jsonl。

为什么不用 config.json
----------------------
历史会一直长，塞进配置里每次保存都要重写整份配置，越用越慢，
而且一条写坏就把整份配置带坏。jsonl 追加只写一行，坏一行也只丢一条。

为什么只留 500 条
----------------
用户真正要的是「刚才那批传哪儿去了」「上次失败的那个文件叫什么」，
不是完整日志。超过 500 条就从头砍，文件稳定在几十 KB。
"""

import os
import json
import threading

MAX_ENTRIES = 500
_LOCK = threading.Lock()


def hist_path(cfg_dir=None):
    """history.jsonl 的位置；cfg_dir 只给测试用。"""
    base = cfg_dir or os.path.join(
        os.environ.get("APPDATA", os.path.expanduser("~")), "LanSplice")
    return os.path.join(base, "history.jsonl")


def make_entry(direction, peer="", ip="", port=0, files=0, nbytes=0,
               ok=0, fail=0, skip=0, root="", src=None, err=""):
    """
    组装一条记录。

    direction: "out" 本机发出 / "in" 本机收到
    src:       本次涉及的本地路径（发出时用来「一键重发」）
    """
    return {
        "t": __import__("time").time(),
        "dir": direction,
        "peer": peer or "",
        "ip": ip or "",
        "port": int(port or 0),
        "files": int(files or 0),
        "bytes": int(nbytes or 0),
        "ok": int(ok or 0),
        "fail": int(fail or 0),
        "skip": int(skip or 0),
        "root": root or "",
        "src": list(src or []),
        "err": err or "",
    }


def append(entry, cfg_dir=None):
    """追加一条。失败不抛 —— 历史记不上不该影响传输本身。"""
    p = hist_path(cfg_dir)
    try:
        os.makedirs(os.path.dirname(p), exist_ok=True)
    except Exception:
        pass
    with _LOCK:
        try:
            with open(p, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            return False
    prune(cfg_dir=cfg_dir)
    return True


def load(limit=200, cfg_dir=None):
    """读最近 limit 条，**新的在前**（界面直接按顺序显示）。"""
    p = hist_path(cfg_dir)
    if not os.path.isfile(p):
        return []
    rows = []
    try:
        with open(p, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except Exception:
                    continue          # 半行写入 / 手改坏了：跳过这一条
    except Exception:
        return []
    if limit and len(rows) > limit:
        rows = rows[-limit:]
    return rows[::-1]


def count(cfg_dir=None):
    p = hist_path(cfg_dir)
    if not os.path.isfile(p):
        return 0
    n = 0
    try:
        with open(p, encoding="utf-8", errors="replace") as f:
            for line in f:
                if line.strip():
                    n += 1
    except Exception:
        return 0
    return n


def prune(maxn=MAX_ENTRIES, cfg_dir=None):
    """超过上限就重写成最近 maxn 条。只在 append 里顺手调用。"""
    p = hist_path(cfg_dir)
    if not os.path.isfile(p):
        return False
    try:
        if os.path.getsize(p) < 400 * 1024:      # 小文件不必每次读一遍
            if count(cfg_dir) <= maxn:
                return False
    except Exception:
        return False
    rows = load(limit=maxn, cfg_dir=cfg_dir)[::-1]
    with _LOCK:
        try:
            tmp = p + ".tmp"
            with open(tmp, "w", encoding="utf-8", newline="\n") as f:
                for r in rows:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
            os.replace(tmp, p)
        except Exception:
            return False
    return True


def clear(cfg_dir=None):
    p = hist_path(cfg_dir)
    with _LOCK:
        try:
            if os.path.isfile(p):
                os.remove(p)
        except Exception:
            return False
    return True
