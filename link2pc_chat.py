# -*- coding: utf-8 -*-
"""
LanSplice 内网聊天
==================

设计原则：**没有服务器，每台都是节点。**

小公司的痛点很具体：几台电脑，谁都不保证一直开着。
所以这里不选「主机」，而是全互联（mesh）：

    · 靠现有的 UDP 广播（47821）互相知道谁在线
    · 发消息时直接连到每个在线的人，并行发，不经过任何人中转
    · 谁关机都不影响其他几台之间继续聊
    · 配对码 = 房间口令，同一个码就是同一个圈子

代价与边界
----------
一条消息要发 N-1 次。3~10 台时，局域网里每次几十毫秒，感觉不出来；
到几十台就该换方案了 —— 那种规模也不该用这个软件。

离线消息不存：人在公司就在线，这是内网工具的定位。
要补的话，让某台常开的机器代存即可，但那是另一套设计，先不做。
"""

import json
import os
import socket
import threading
import time
import uuid

import link2pc_core as L


# ---------------------------------------------------------------- 身份

def default_name():
    """自己没有设名字时，用主机名 —— 至少比一串 IP 好认。"""
    try:
        n = socket.gethostname().strip()
        return n[:24] or "LanSplice"
    except Exception:
        return "LanSplice"


def clean_name(s, fallback=None):
    """显示名只留一行，别让人用换行把界面撑乱。"""
    t = (s or "").replace("\r", " ").replace("\n", " ").strip()
    return t[:24] or (fallback or default_name())


# ---------------------------------------------------------------- 成员表

class Roster:
    """
    在线成员表。

    数据来源只有一处：PeerServer 收到的 UDP 广播（_offer_payload）。
    每条广播刷新一次时间戳，超过 TTL 就认为掉线。

    为什么不用 TCP 心跳：广播本来就在跑（发现设备用的），
    复用它不用额外开连接，也不占端口。
    """

    TTL = 45.0          # 秒。广播每 8 秒一次，45 秒够容忍丢几个包

    def __init__(self, ttl=None):
        self.ttl = ttl or self.TTL
        self._lock = threading.Lock()
        self._peers = {}        # (ip, port) -> dict

    def update(self, info, ip=None):
        """
        收到一条广播就登记一次。返回 True 表示这是新面孔。

        info 是 _offer_payload 里那段 JSON：name / port / ip / inst
        """
        try:
            port = int(info.get("port") or 0)
        except Exception:
            return False
        addr = (ip or info.get("ip") or "").strip()
        if not addr or not port:
            return False
        key = (addr, port)
        now = time.time()
        with self._lock:
            old = self._peers.get(key)
            fresh = old is None or (now - old["seen"]) > self.ttl
            self._peers[key] = {
                "ip": addr,
                "port": port,
                "name": clean_name(info.get("name")),
                "inst": str(info.get("inst") or ""),
                "seen": now,
            }
            return fresh

    def touch(self, addr, port=None, name=None):
        """有人主动连上来（比如发消息），也当作在线证据。"""
        try:
            port = int(port or 0)
        except Exception:
            port = 0
        addr = (addr or "").strip()
        if not addr:
            return
        with self._lock:
            for k, v in list(self._peers.items()):
                if v["ip"] != addr:
                    continue
                if port and v["port"] != port:
                    continue
                v["seen"] = time.time()
                if name:
                    v["name"] = clean_name(name)
                return
            if port:
                self._peers[(addr, port)] = {
                    "ip": addr, "port": port,
                    "name": clean_name(name), "inst": "",
                    "seen": time.time(),
                }

    def online(self):
        """当前在线的人，按名字排好序。"""
        now = time.time()
        with self._lock:
            out = [dict(v) for v in self._peers.values()
                   if now - v["seen"] <= self.ttl]
        out.sort(key=lambda p: (p["name"].lower(), p["ip"]))
        return out

    def prune(self):
        """把掉线的清掉，返回清掉几个。"""
        now = time.time()
        with self._lock:
            dead = [k for k, v in self._peers.items()
                    if now - v["seen"] > self.ttl]
            for k in dead:
                self._peers.pop(k, None)
        return len(dead)

    def clear(self):
        with self._lock:
            self._peers.clear()

    def count(self):
        return len(self.online())


# ---------------------------------------------------------------- 聊天记录

class ChatStore:
    """
    本地聊天记录，一行一条 JSONL。

    每人存自己的一份 —— 不追求各端完全一致（那需要中心库），
    但每台机器都能看到「自己收到过的全部消息」，够用且不依赖任何人。

    只保留最近 MAX 条；文件超过 4 MB 时重写一次（把更早的丢掉）。
    """

    MAX = 800

    def __init__(self, path):
        self.path = path
        self._lock = threading.Lock()
        self._items = []
        self._load()

    def _load(self):
        if not os.path.isfile(self.path):
            return
        out = []
        try:
            with open(self.path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        d = json.loads(line)
                    except Exception:
                        continue          # 坏一行只丢那一条
                    if isinstance(d, dict) and d.get("body"):
                        out.append(d)
        except Exception:
            return
        self._items = out[-self.MAX:]

    def append(self, msg):
        """存一条。同一 id 只存一次（重发、自己那份都靠它去重）。"""
        mid = msg.get("id")
        if mid and any(m.get("id") == mid for m in self._items[-200:]):
            return False
        with self._lock:
            self._items.append(msg)
            if len(self._items) > self.MAX:
                self._items = self._items[-self.MAX:]
            try:
                os.makedirs(os.path.dirname(self.path), exist_ok=True)
                with open(self.path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(msg, ensure_ascii=False) + "\n")
            except Exception:
                pass
            self._compact_if_needed()
        return True

    def _compact_if_needed(self):
        try:
            if os.path.getsize(self.path) < 4 * 1024 * 1024:
                return
        except Exception:
            return
        try:
            tmp = self.path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                for m in self._items[-self.MAX // 2:]:
                    f.write(json.dumps(m, ensure_ascii=False) + "\n")
            os.replace(tmp, self.path)
        except Exception:
            pass

    def recent(self, n=None):
        with self._lock:
            items = list(self._items)
        return items[-n:] if n else items

    def clear(self):
        with self._lock:
            self._items = []
            try:
                if os.path.isfile(self.path):
                    os.remove(self.path)
            except Exception:
                pass


# ---------------------------------------------------------------- 发消息

def make_msg(body, name, to=None, reply_to=None):
    return {
        "id": uuid.uuid4().hex[:16],
        "from": clean_name(name),
        "body": str(body)[:4000],
        "ts": time.time(),
        "to": to or "",             # 空 = 群里所有人
        "re": reply_to or "",
    }


def send_one(key, peer, msg, timeout=6):
    """
    发给一个对端。返回 (成功?, 错误说明)。

    走的是现成的加密通道 + 配对码，跟传文件同一套安全模型：
    不知道配对码的人连不上，也不存在明文经过网络。
    """
    cli = None
    try:
        cli = L.LinkClient(peer["ip"], peer["port"], key, timeout=timeout)
        cli.open()
        cli.ch.send_json({"t": "chat", "msg": msg})
        r = cli.ch.recv_json()
        if r.get("t") != "ok":
            return False, str(r.get("msg") or "对端没接受")
        return True, ""
    except L.AuthError:
        return False, "配对码不一致"
    except Exception as e:
        return False, str(e)[:80]
    finally:
        try:
            if cli is not None:
                cli.close()
        except Exception:
            pass


def broadcast(key, peers, msg, timeout=6, max_workers=8):
    """
    并行发给所有人，返回 [(peer, 成功?, 错误)]。

    并行很重要：10 台机器串行发，一条消息要等 10 个往返；
    并行的话总耗时约等于最慢的那一个。

    单台失败不影响其他人 —— 内网里某台关机、睡眠是常态。
    """
    if not peers:
        return []
    results = []
    lock = threading.Lock()

    def work(p):
        ok, err = send_one(key, p, msg, timeout=timeout)
        with lock:
            results.append((p, ok, err))

    threads = []
    for p in peers:
        if len(threads) >= max_workers:
            # 简单的并发闸门：凑够一批就等一下
            for t in threads:
                t.join(timeout=timeout + 2)
            threads = []
        t = threading.Thread(target=work, args=(p,), daemon=True)
        t.start()
        threads.append(t)
    for t in threads:
        t.join(timeout=timeout + 2)
    return results


def handle_incoming(msg, roster=None, store=None, from_ip=None, from_name=None):
    """
    收到一条聊天消息：登记成员、存进历史。返回规整后的消息。

    单独抽出来是为了能脱离网络做单元测试。
    """
    if not isinstance(msg, dict):
        return None
    body = msg.get("body")
    if not isinstance(body, str) or not body.strip():
        return None
    clean = {
        "id": str(msg.get("id") or uuid.uuid4().hex[:16]),
        "from": clean_name(msg.get("from") or from_name or from_ip),
        "body": body[:4000],
        "ts": float(msg.get("ts") or time.time()),
        "to": str(msg.get("to") or ""),
        "re": str(msg.get("re") or ""),
    }
    if roster is not None and from_ip:
        roster.touch(from_ip, msg.get("port"), clean["from"])
    if store is not None:
        store.append(clean)
    return clean
