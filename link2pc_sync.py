# -*- coding: utf-8 -*-
"""
目录自动同步
============

盯着本机一个（或多个）文件夹，发现变化就推给对端。这是「镜像」的常驻版：
镜像要人点，同步不用管 —— 网盘真正留住人的地方不是传输速度，是「不用管」。

设计上刻意保守的三处
--------------------
1. **只做加法。** 本地删了文件，对端那份不删。删除不可逆，一个判断失误就是
   别人的数据没了；而「多一份备份」几乎从来不是坏事。界面上照实写清楚。
2. **两次扫描都稳定才传。** 一个文件正在被写入时，大小和修改时间每一秒都在变。
   只看到一次就传，传出去的是半截文件。所以第一次看见只是记下来，下一轮没变
   才真的推 —— 代价是延迟一个周期（默认 6 秒），换来的是不会传出坏文件。
3. **同名覆盖。** 「同步」的语义就是让对端和本地一致。不覆盖会存成 `xxx (2).txt`，
   越同步越乱。内容没变的文件在比对阶段就被排除了，所以覆盖只会发生在确实
   改过的文件上。

同步状态只存在内存里：重启后第一轮会把所有文件重新问一遍对端（每个文件一次
stat），没变的一个字节都不传。这是「宁可多问、不可错传」的取舍。
"""

import os
import time
import threading

SYNC_INTERVAL = 6.0          # 秒。一轮扫描的间隔
MAX_FILES = 200000           # 单个任务的文件数上限，超了就停下并在界面报出来

# 这些目录整棵跳过：不是用户资料，扫起来还特别贵
_SKIP_DIRS = {".git", ".svn", ".hg", "__pycache__", "node_modules",
              ".venv", "venv", ".idea", ".vs"}

# 临时文件、锁文件、我们自己的分片，都不该被同步
_SKIP_PREFIX = (".l2p", "~$", ".~", ".goutputstream")
_SKIP_SUFFIX = (".tmp", ".temp", ".part", ".l2ptmp", ".swp", ".swx", ".crdownload")


def ignored_name(name):
    """文件名是否该跳过。大小写不敏感 —— Windows 上 `A.TMP` 和 `a.tmp` 是一回事。"""
    low = name.lower()
    if low.startswith(_SKIP_PREFIX):
        return True
    return low.endswith(_SKIP_SUFFIX)


def scan(root, max_files=MAX_FILES):
    """
    扫一棵树，返回 ({相对路径: (大小, 修改时间秒)}, 是否被截断)。

    相对路径统一用 `/` 分隔：对端可能是 Linux，反斜杠在那边不是分隔符。
    """
    out = {}
    if not root or not os.path.isdir(root):
        return out, False
    for cur, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs
                   if not d.startswith(".") and d.lower() not in _SKIP_DIRS]
        for n in names:
            if ignored_name(n):
                continue
            p = os.path.join(cur, n)
            try:
                st = os.stat(p)
            except OSError:
                continue
            rel = os.path.relpath(p, root).replace(os.sep, "/")
            out[rel] = (st.st_size, int(st.st_mtime))
            if len(out) >= max_files:
                return out, True
    return out, False


def diff(done, cur):
    """
    对比「已经同步过的状态」和「这一轮扫到的状态」。

    返回 [(相对路径, 大小, 修改时间), ...]，只含新增和有改动的。
    本地删掉的文件不在返回值里 —— 见模块开头第 1 条。
    """
    changed = []
    for rel, meta in cur.items():
        if done.get(rel) != meta:
            changed.append((rel, meta[0], meta[1]))
    return changed


class SyncEngine(object):
    """
    同步引擎。不是 Thread 的子类：`tick()` 可以单独调，测试里才好一条条摆局面。
    需要常驻时调 `start()`，它自己起一个 daemon 线程反复 tick。
    """

    def __init__(self, get_jobs, make_client, interval=SYNC_INTERVAL,
                 log=None, on_event=None, max_files=MAX_FILES):
        self.get_jobs = get_jobs          # () -> [job dict]
        self.make_client = make_client    # () -> 已连接的 LinkClient
        self.interval = interval
        self.log = log or (lambda s: None)
        self.on_event = on_event or (lambda kind, data: None)
        self.max_files = max_files

        self._done = {}                   # job_id -> {rel: (size, mtime)}
        self._prev = {}                   # job_id -> 上一轮扫到的 {rel: (size, mtime)}
        self._state = {}                  # job_id -> "idle" / "busy" / "error"
        self._last = {}                   # job_id -> (时间, 传了几个, 字节)
        self._err = {}                    # job_id -> 最后一次错误文本
        self._stop = threading.Event()
        self._thread = None
        self._client = None
        # 「立即同步一次」和后台线程可能同时进来，tick 必须串行：
        # 两条线程同时算差量会互相把基准改乱，接着就是重复上传。
        self._lock = threading.Lock()
        self._err_notified = {}           # job_id -> 上次已经报过的错误文本

    # ---- 常驻
    def start(self):
        # 先清停止标志再判断线程：否则「关掉开关马上又打开」时，
        # 旧线程还活着但已被标记停止，start 直接返回，同步就再也不跑了。
        self._stop.clear()
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._loop, daemon=True,
                                        name="LanSplice-Sync")
        self._thread.start()

    def stop(self):
        self._stop.set()

    def _loop(self):
        while not self._stop.is_set():
            try:
                self.tick()
            except Exception as e:            # tick 内部已分任务兜过，这里只是保险
                self.log("sync loop: %s" % e)
            # 用 wait 而不是 sleep：退出时立刻能醒
            self._stop.wait(self.interval)

    # ---- 状态给界面看
    def job_state(self, job_id):
        return (self._state.get(job_id, "idle"),
                self._err.get(job_id, ""),
                self._last.get(job_id))

    # ---- 一轮
    def tick(self):
        jobs = [j for j in (self.get_jobs() or [])
                if isinstance(j, dict) and j.get("id")
                and j.get("enabled", True) and j.get("local")]
        if not jobs:
            return 0

        with self._lock:
            sent_total = 0
            for job in jobs:
                if self._stop.is_set():
                    break
                try:
                    sent_total += self._tick_job(job)
                except Exception as e:
                    self._fail(job.get("id"), str(e))
            self._close_client()
            return sent_total

    def _fail(self, jid, msg):
        """记下错误，但同一个错误只往外报一次 —— 对端没开时每 6 秒报一遍
        会把状态栏刷成滚动条，用户只会以为软件坏了。"""
        self._state[jid] = "error"
        self._err[jid] = msg
        if self._err_notified.get(jid) != msg:
            self._err_notified[jid] = msg
            self.on_event("error", (jid, msg))

    def _tick_job(self, job):
        jid = job["id"]
        local = job.get("local") or ""
        remote = (job.get("remote") or "").strip().strip("/\\")

        cur, truncated = scan(local, self.max_files)
        if truncated:
            self._state[jid] = "error"
            self._err[jid] = "too-many"
            if self._err_notified.get(jid) != "too-many":
                self._err_notified[jid] = "too-many"
                self.on_event("truncated", (jid, self.max_files))
            # 截断时不要把这份不完整的结果当成基准，否则下一轮会把
            # 「刚才没扫到」误判成删除，越同步越乱
            self._prev[jid] = cur
            return 0

        done = self._done.setdefault(jid, {})
        prev = self._prev.get(jid) or {}

        # 只传「这一轮和上一轮一样」的文件：正在写的文件两轮之间一定在变
        todo = []
        for rel, size, mtime in diff(done, cur):
            if prev.get(rel) == (size, mtime):
                todo.append((rel, size, mtime))
        self._prev[jid] = cur

        # 本地删掉的文件：把基准也清掉，别让它永远挂在那儿
        for rel in list(done):
            if rel not in cur:
                done.pop(rel, None)

        if not todo:
            if self._state.get(jid) == "busy":
                self._state[jid] = "idle"
            return 0

        self._state[jid] = "busy"
        self.on_event("begin", (jid, len(todo)))

        sent = 0
        n = 0
        for rel, size, mtime in todo:
            if self._stop.is_set():
                break
            target = ("%s/%s" % (remote, rel)) if remote else rel
            path = os.path.join(local, *rel.split("/"))
            try:
                cli = self._client_or_connect()
                if cli is None:
                    # 还没选对端：这一轮什么都不做，也不算错。
                    # 报成错误的话，没用过这个功能的人每次开机都会看到一行红字。
                    self._state[jid] = "idle"
                    return sent
                cli.upload(path, target, overwrite=True)
            except Exception as e:
                # 这条连接多半已经废了，下一轮重连
                self._close_client()
                self._fail(jid, str(e))
                return sent
            done[rel] = (size, mtime)
            n += 1
            sent += size
            self.on_event("file", (jid, rel))

        self._state[jid] = "idle"
        self._err[jid] = ""
        self._err_notified.pop(jid, None)
        self._last[jid] = (time.time(), n, sent)
        self.on_event("done", (jid, n, sent))
        return sent

    # ---- 连接
    def _client_or_connect(self):
        if self._client is None:
            self._client = self.make_client()
        return self._client

    def _close_client(self):
        c = self._client
        self._client = None
        if c is not None:
            try:
                c.close()
            except Exception:
                pass
