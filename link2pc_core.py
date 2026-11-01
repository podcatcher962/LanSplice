# -*- coding: utf-8 -*-
"""
LanSplice 传输内核
================
双机局域网直传，不依赖 Windows 文件共享（不开 445 端口）。

安全模型
--------
1. 发现层（UDP 广播）：只广播主机名/端口，不含任何密钥。发现 ≠ 信任。
2. 认证层：预共享密钥（PSK，由 16 位配对码派生）+ X25519 临时密钥交换。
   握手双方都要用 PSK 对交换消息做 HMAC，因此：
     - 没有配对码的连接方无法完成握手（进不来）
     - 中间人无法伪造（不知道 PSK 就算不出 HMAC）
     - X25519 提供前向保密（事后拿到配对码也解不开已录的流量）
3. 传输层：AES-256-GCM 分块加密，双向各用独立密钥，nonce 用单调序号，杜绝重用。
4. 访问层：服务端只写配置的接收根目录，路径做越界校验，拒绝写到根目录之外。

协议帧
------
[4 字节大端长度][1 字节类型][负载...]
  类型 C = 控制（UTF-8 JSON）
  类型 D = 数据（文件分块明文）
整帧（类型+负载）用 AES-GCM 加密后再加长度头。
"""

import os
import io
import json
import time
import hmac
import socket
import select
import struct
import base64
import hashlib
import secrets
import subprocess
import threading
from link2pc_i18n import t as _t

from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey, X25519PublicKey,
)
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

# ---------------------------------------------------------------- 常量

PROTO_VER = 1
MAGIC = b"L2P1"

# 版本号只在这里写一次。
# 以前图形界面和命令行各写一份，升级时忘了改其中一处，
# 就会出现「窗口标题 1.5.0、命令行 version 1.4.0」这种自相矛盾。
APP_VER = "1.6.0"

DISCOVERY_PORT = 47821
ANNOUNCE_EVERY = 8             # 秒。接收端隔这么久主动宣告一次自己
TCP_PORT = 47820

CHUNK = 512 * 1024                  # 单帧最大明文，512 KB
HEADER = struct.Struct(">I")        # 帧长度头
MAX_FRAME = 4 * 1024 * 1024         # 防恶意超大帧（解压炸弹式攻击）

# 完整性校验与断点续传
# --------------------
# 把文件按 16 MB 切段，每段单独算 SHA-256，发送端在段末把一个 segh 控制帧
# 递过去，接收端逐段比对。这样做而不是「整个文件算一个哈希」，有两个原因：
#   1. 断点续传时只需从「最后一个完整段」的边界接着来，已校验过的段不用重算；
#   2. 出问题时能指出坏在第几段，而不是只报一句「校验失败」。
# 16 MB 是权衡：87 MB/s 下 0.18 秒一段，哈希开销完全被网络吃掉；
# 段再大则续传浪费多，再小则控制帧太密。
SEG_SIZE = 16 * 1024 * 1024
PART_DIR = ".l2p-parts"             # 未完成分片的暂存目录（放在目标文件旁边，保证同盘）
PART_KEEP_DAYS = 7                  # 超过这么多天的残留分片，启动时清掉

# 能力协商：hello 报文里交换，双方都支持才启用新协议，
# 保证 v1.4 与 v1.3 之间互相连得上（旧版不认识 segh 帧会直接报错）。
CAP_RESUME = "resume"
MAX_TEXT = 128 * 1024               # 单条文字上限 128 KB，够贴整段代码

# 建立连接的超时（秒）
# --------------------
# 局域网里 RTT 通常不足 5 ms，剩下的时间全花在「对方到底起没起来」上：
# 对端软件没开时，SYN 会一直重试到系统上限（Windows 21 秒、Linux 130 秒），
# 用户看到的是「点了发送，然后就没然后了」。3.5 秒是 700 倍 RTT，
# 慢速 WiFi 也够用，而失败来得足够快，能立刻看到一句解释。
# 注意：这只管「连上」这一下，连上之后单帧还是要等 300 秒（大文件慢很正常）。
CONNECT_TIMEOUT = 3.5

FRAME_CTRL = b"C"
FRAME_DATA = b"D"

# 局域网内允许的来源（限定 IPv4 私有段，挡住公网 IPv6 / 外网）
ALLOWED_NETS = ("192.168.", "10.", "172.16.", "172.17.", "172.18.", "172.19.",
                "172.20.", "172.21.", "172.22.", "172.23.", "172.24.", "172.25.",
                "172.26.", "172.27.", "172.28.", "172.29.", "172.30.", "172.31.",
                "127.0.0.1", "::1")


class AuthError(Exception):
    """配对码不对，或握手被篡改。"""


class ProtocolError(Exception):
    """协议异常。"""


# ---------------------------------------------------------------- 基础工具

def tune_socket(sock):
    """
    局域网大流量传输的必备调优。

    TCP_NODELAY 必须开：关掉 Nagle 算法。
    Nagle 会把小包攒着等 ACK，而 Windows 接收端又默认「延迟 ACK」，
    两个定时器互相等，每个数据块白等 40~200 毫秒。
    在 512KB 分块下，这直接把千兆压到 7MB/s 上下。

    SO_SNDBUF/SO_RCVBUF 不动：Windows 有接收窗口自动调优，
    手工设值反而会关掉自动调优，越调越慢。
    """
    try:
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    except Exception:
        pass
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    except Exception:
        pass
    return sock


def recv_exact(sock, n):
    """严格读满 n 字节，断了就抛异常。"""
    buf = bytearray()
    while len(buf) < n:
        b = sock.recv(n - len(buf))
        if not b:
            raise ConnectionError(_t("c001"))
        buf += b
    return bytes(buf)


def human_size(n):
    if n < 1024:
        return "%d B" % n
    if n < 1024 * 1024:
        return "%.1f KB" % (n / 1024.0)
    if n < 1024 ** 3:
        return "%.1f MB" % (n / 1048576.0)
    return "%.2f GB" % (n / 1073741824.0)


def hostname():
    return socket.gethostname()


def conn_error_text(exc, ip, port):
    """
    把连不上时的底层异常翻成人话。

    以前是直接把 `str(exc)` 拼在「连不上对端：」后面，于是用户看到的是
    `连不上对端：timed out` —— 一句英文，既没说连的是谁，也没说该怎么办。
    而「连不上」其实只有两类原因，处理方式完全不同：

      · 端口被拒绝（对端在线，只是没开软件）→ 去把那台机器上的程序打开
      · 根本没回应（对端不在线 / 不在同一网段）→ 先确认两台在同一个路由器下

    区分开，用户才知道下一步该动哪台机器。
    """
    s = str(exc).lower()
    if "refused" in s or "10061" in s or "积极拒绝" in s:
        return _t("c069") % (ip, port)
    if ("timed out" in s or "timeout" in s
            or "10060" in s or "10065" in s or "10051" in s
            or "unreachable" in s or "unreach" in s):
        return _t("c070") % (ip, port)
    return _t("c071") % (ip, port, exc)


def _demo_net_type(ip):
    """给本机地址做个粗分类，只用于界面提示（不影响功能）。"""
    if ip.startswith("192.168.56.") or ip.startswith("192.168.51."):
        return _t("c002")
    if ip.startswith("192.168.137."):
        return _t("c003")
    if ip.startswith("172."):
        try:
            second = int(ip.split(".")[1])
        except Exception:
            second = -1
        if 16 <= second <= 31:
            return _t("c004")
    return ""


def list_ipv4():
    """
    列出本机所有已启用网卡的 IPv4：[{ip, prefix, bcast, index}]。

    走 iphlpapi 的 GetIpAddrTable，拿得到掩码才能算子网广播地址——
    Windows 上只发 255.255.255.255 时，系统只挑一块网卡发出去，
    一旦那块是 VMware/Hyper-V/VPN 的虚拟网卡，真实局域网就永远收不到。
    """
    out = []
    seen = set()
    try:
        import ctypes
        from ctypes import wintypes

        class MIB_IPADDRROW(ctypes.Structure):
            _fields_ = [
                ("dwAddr", wintypes.DWORD), ("dwIndex", wintypes.DWORD),
                ("dwMask", wintypes.DWORD), ("dwBCastAddr", wintypes.DWORD),
                ("dwReasmSize", wintypes.DWORD),
                ("unused1", wintypes.USHORT), ("wType", wintypes.USHORT),
            ]

        iphlpapi = ctypes.WinDLL("iphlpapi.dll")
        size = wintypes.ULONG(0)
        iphlpapi.GetIpAddrTable(None, ctypes.byref(size), 0)
        if size.value < 4:
            raise OSError(_t("c005"))
        buf = ctypes.create_string_buffer(size.value + 128)
        rc = iphlpapi.GetIpAddrTable(buf, ctypes.byref(size), 0)
        if rc != 0:
            raise OSError(_t("c006") % rc)

        raw = ctypes.string_at(buf, size.value)
        n = struct.unpack("<I", raw[:4])[0]
        for i in range(n):
            off = 4 + i * 24
            chunk = raw[off:off + 24]
            if len(chunk) < 24:
                break
            addr, index, mask = struct.unpack("<III", chunk[:12])
            ip = socket.inet_ntoa(struct.pack("<I", addr))
            if ip in seen:
                continue
            seen.add(ip)
            if ip.startswith(("127.", "0.", "169.254.", "255.")):
                continue
            ip_i = struct.unpack(">I", struct.pack("<I", addr))[0]
            mask_i = struct.unpack(">I", struct.pack("<I", mask))[0]
            prefix = bin(mask_i).count("1")
            if prefix == 0 or prefix >= 32:
                continue
            bcast = socket.inet_ntoa(
                struct.pack(">I", ip_i | (~mask_i & 0xFFFFFFFF)))
            out.append({"ip": ip, "prefix": prefix,
                        "bcast": bcast, "index": index})
    except Exception:
        out = []

    if not out:
        # 老系统兜底：拿不到掩码，就按 /24 猜
        try:
            for ip in socket.gethostbyname_ex(socket.gethostname())[2]:
                if not ip or ip.startswith(("127.", "169.254.")) or ip in seen:
                    continue
                seen.add(ip)
                parts = ip.split(".")
                out.append({"ip": ip, "prefix": 24,
                            "bcast": ".".join(parts[:3] + ["255"]),
                            "index": 0})
        except Exception:
            pass

    # 家用主网段（192.168.0.x 这类）排前面，虚拟网卡排后面
    def _rank(d):
        ip = d["ip"]
        return (0 if ip.startswith("192.168.") else
                1 if ip.startswith("10.") else 2, d["prefix"] != 24)

    return sorted(out, key=_rank)


def local_ips():
    """本机所有 IPv4（去重）。用于界面显示与「排除自己」。"""
    ips = [d["ip"] for d in list_ipv4()]
    if not ips:
        ip = local_ip()
        if ip and not ip.startswith("127."):
            ips = [ip]
    return ips


def is_own_addr(ip, me=None):
    """
    这个地址是不是「本机自己」。

    回环地址一定要算 —— 给 255.255.255.255 发广播时，Windows 会把副本
    回送给本机的 UDP socket，某些网卡组合下 recvfrom 拿到的源地址就是
    127.0.0.1。以前只比 local_ips()，于是自己的包被当成了对端，
    列表里多出一台「127.0.0.1:47820」的幽灵设备。
    """
    if not ip:
        return True
    if ip.startswith("127.") or ip in ("0.0.0.0", "::1"):
        return True
    ips = me if me is not None else local_ips()
    return ip in set(ips)


def local_ip():
    """本机在局域网里的主 IPv4（连不出去时回环）。"""
    d = list_ipv4()
    if d:
        return d[0]["ip"]
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("223.5.5.5", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


def is_private_ipv4(ip):
    """只放行内网/回环来源。"""
    if ip is None:
        return False
    if ip.startswith("::ffff:"):
        ip = ip[7:]
    return ip.startswith(ALLOWED_NETS)


# ---------------------------------------------------------------- 配对码

# base32 字母表去掉容易看错的字符，方便手抄
_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def new_pair_key():
    """生成 10 字节随机密钥（80 位熵）。"""
    return secrets.token_bytes(10)


def key_to_code(key):
    """10 字节 -> 'ABCD-EFGH-JKLM-NPQR' 16 字符（高位在前，与 code_to_key 对齐）。"""
    n = int.from_bytes(key, "big")
    out = []
    for i in range(15, -1, -1):
        out.append(_ALPHABET[(n >> (5 * i)) & 0x1F])
    return "-".join("".join(out)[i:i + 4] for i in range(0, 16, 4))


def code_to_key(code):
    """配对码 -> 10 字节。容忍空格、横线、小写。"""
    clean = "".join(ch for ch in code.upper() if ch in _ALPHABET)
    if len(clean) != 16:
        raise ValueError(_t("c007") % len(clean))
    n = 0
    for ch in clean:
        n = (n << 5) | _ALPHABET.index(ch)
    return n.to_bytes(10, "big")


# ---------------------------------------------------------------- 加密封装

def _hkdf(shared, salt, info):
    return HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        info=info,
    ).derive(shared)


def pub_raw(key):
    """
    取 X25519 公钥的 32 字节裸数据。

    `public_bytes_raw()` 是 cryptography 40 才有的；32 位包用的旧版
    （36.x）没有这个方法，直接调会 AttributeError、彻底握不上手。
    这里统一走老接口，新旧版本都能用。
    """
    return key.public_bytes(Encoding.Raw, PublicFormat.Raw)


class SecureChannel:
    """加密帧通道。收方向、发方向各用一把独立密钥，nonce 用单调序号。"""

    def __init__(self, sock, tx_key, rx_key):
        self.sock = sock
        self.tx = AESGCM(tx_key)
        self.rx = AESGCM(rx_key)
        self.tx_seq = 0
        self.rx_seq = 0
        self._buf = bytearray()

    # ---- 发送
    def send_frame(self, ftype, payload):
        body = ftype + payload
        nonce = struct.pack(">Q", self.tx_seq) + b"\x00" * 4
        self.tx_seq += 1
        blob = self.tx.encrypt(nonce, body, None)
        self.sock.sendall(HEADER.pack(len(blob)) + blob)

    def send_json(self, obj):
        self.send_frame(FRAME_CTRL, json.dumps(obj, ensure_ascii=False).encode("utf-8"))

    def send_data(self, data):
        self.send_frame(FRAME_DATA, data)

    # ---- 接收
    def _read_frame_raw(self):
        hdr = recv_exact(self.sock, 4)
        (n,) = HEADER.unpack(hdr)
        if n <= 0 or n > MAX_FRAME:
            raise ProtocolError(_t("c008") % n)
        blob = recv_exact(self.sock, n)
        nonce = struct.pack(">Q", self.rx_seq) + b"\x00" * 4
        self.rx_seq += 1
        try:
            body = self.rx.decrypt(nonce, blob, None)
        except Exception:
            raise ProtocolError(_t("c009"))
        if not body:
            raise ProtocolError(_t("c010"))
        return body[:1], body[1:]

    def recv_frame(self):
        return self._read_frame_raw()

    def recv_json(self):
        ftype, payload = self._read_frame_raw()
        if ftype != FRAME_CTRL:
            raise ProtocolError(_t("c011") % ftype)
        return json.loads(payload.decode("utf-8"))

    def recv_data(self):
        ftype, payload = self._read_frame_raw()
        if ftype != FRAME_DATA:
            raise ProtocolError(_t("c012") % ftype)
        return payload

    def close(self):
        try:
            self.sock.close()
        except Exception:
            pass


def _hs_client(sock, psk):
    """客户端握手：发公钥 -> 验服务端 HMAC -> 发自己 HMAC -> 派生双密钥。"""
    priv = X25519PrivateKey.generate()
    cpub = pub_raw(priv.public_key())
    cnonce = secrets.token_bytes(32)
    sock.sendall(MAGIC + cpub + cnonce)

    blob = recv_exact(sock, 4 + 32 + 32 + 32)
    if blob[:4] != MAGIC:
        raise ProtocolError(_t("c013"))
    spub, snonce, smac = blob[4:36], blob[36:68], blob[68:100]

    expect = hmac.new(psk, b"SERVER" + cpub + spub + cnonce + snonce,
                      hashlib.sha256).digest()
    if not hmac.compare_digest(smac, expect):
        raise AuthError(_t("c014"))

    shared = priv.exchange(X25519PublicKey.from_public_bytes(spub))
    cmac = hmac.new(psk, b"CLIENT" + cpub + spub + cnonce + snonce,
                    hashlib.sha256).digest()
    sock.sendall(cmac)

    salt = cnonce + snonce
    k_c2s = _hkdf(shared, salt, b"Link2PC-v1-c2s")
    k_s2c = _hkdf(shared, salt, b"Link2PC-v1-s2c")
    return SecureChannel(sock, k_c2s, k_s2c)


def _hs_server(sock, psk):
    """服务端握手（与客户端镜像）。"""
    blob = recv_exact(sock, 4 + 32 + 32)
    if blob[:4] != MAGIC:
        raise ProtocolError(_t("c015"))
    cpub, cnonce = blob[4:36], blob[36:68]

    priv = X25519PrivateKey.generate()
    spub = pub_raw(priv.public_key())
    snonce = secrets.token_bytes(32)

    smac = hmac.new(psk, b"SERVER" + cpub + spub + cnonce + snonce,
                    hashlib.sha256).digest()
    sock.sendall(MAGIC + spub + snonce + smac)

    cmac = recv_exact(sock, 32)
    expect = hmac.new(psk, b"CLIENT" + cpub + spub + cnonce + snonce,
                      hashlib.sha256).digest()
    if not hmac.compare_digest(cmac, expect):
        raise AuthError(_t("c014"))

    shared = priv.exchange(X25519PublicKey.from_public_bytes(cpub))
    salt = cnonce + snonce
    k_c2s = _hkdf(shared, salt, b"Link2PC-v1-c2s")
    k_s2c = _hkdf(shared, salt, b"Link2PC-v1-s2c")
    # 服务端方向相反
    return SecureChannel(sock, k_s2c, k_c2s)


# ---------------------------------------------------------------- 路径安全

_WIN_RESERVED = {"CON", "PRN", "AUX", "NUL"} | \
                {"COM%d" % i for i in range(1, 10)} | \
                {"LPT%d" % i for i in range(1, 10)}


def safe_join(root, rel):
    """
    把对端给的相对路径安全地拼到 root 下。
    拒绝：绝对路径、盘符、.. 越界、Windows 保留设备名。
    """
    if not rel or rel in (".", "/"):
        raise ValueError(_t("c016"))
    r = rel.replace("/", "\\").strip("\\")
    if not r:
        raise ValueError(_t("c016"))
    if len(r) >= 2 and r[1] == ":":
        raise ValueError(_t("c017") % rel)

    parts = [p for p in r.split("\\") if p not in ("", ".")]
    for p in parts:
        if p == "..":
            raise ValueError(_t("c018") % rel)
        stem = p.split(".")[0].upper()
        if stem in _WIN_RESERVED:
            raise ValueError(_t("c019") % p)

    root_abs = os.path.abspath(root)
    target = os.path.abspath(os.path.join(root_abs, *parts))
    if target != root_abs and not target.lower().startswith(root_abs.lower() + os.sep):
        raise ValueError(_t("c018") % rel)
    return target


def _free_space(path):
    try:
        import shutil
        return shutil.disk_usage(path).free
    except Exception:
        return None


def unique_path(p):
    """
    重名时给出一个不冲突的名字：素材.mp4 -> 素材 (2).mp4 -> 素材 (3).mp4 …

    这是「不静默覆盖」的落点。以前接收端直接 os.replace，
    对端有同名文件就被无声顶掉，对端只看见进度条走完，这是丢数据的隐患。
    Windows 资源管理器给的是「 - 副本」，这里用 (2) 更好排序、也更好找。
    """
    if not os.path.exists(p):
        return p
    d, name = os.path.split(p)
    stem, ext = os.path.splitext(name)
    if not stem:
        stem, ext = name, ""
    for i in range(2, 1000):
        cand = os.path.join(d, "%s (%d)%s" % (stem, i, ext))
        if not os.path.exists(cand):
            return cand
    # 极端情况：同名太多，退回时间戳，绝不覆盖
    return os.path.join(d, "%s (%d)%s" % (stem, int(time.time()), ext))


def transfer_id(rel, size, mtime):
    """
    一次传输的稳定标识。

    同一个文件（同相对路径、同大小、同修改时间）每次算出来的 rid 都一样，
    所以「传了一半断了，再点一次发送」会自动接上，而不是从头再来。
    内容变了（大小或时间不同）就是新的 rid，不会把旧分片当成本次的。
    """
    raw = "%s|%d|%d" % (rel, int(size), int(mtime or 0))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def clean_parts(root, days=PART_KEEP_DAYS):
    """
    清掉过期的残留分片。

    分片是刻意保留的（为了续传），但用户取消过的传输会一直躺在那儿占空间。
    只删 PART_DIR 里超过 days 天的 .part，绝不碰用户文件。
    """
    removed = 0
    cutoff = time.time() - days * 86400
    try:
        for cur, dirs, _files in os.walk(root):
            if PART_DIR not in dirs:
                continue
            pdir = os.path.join(cur, PART_DIR)
            try:
                names = os.listdir(pdir)
            except Exception:
                continue
            for n in names:
                if not n.endswith(".part"):
                    continue
                fp = os.path.join(pdir, n)
                try:
                    if os.path.getmtime(fp) < cutoff:
                        os.remove(fp)
                        removed += 1
                except Exception:
                    pass
            # 目录空了就顺手删掉，别在用户的文件夹里留空壳
            try:
                if not os.listdir(pdir):
                    os.rmdir(pdir)
            except Exception:
                pass
    except Exception:
        pass
    return removed


def _try_json(payload):
    """控制帧解码，坏了就当空对象，不让一个畸形帧把整条连接带崩。"""
    try:
        return json.loads(payload.decode("utf-8"))
    except Exception:
        return {}


def _rmdir_if_empty(p):
    if not p:
        return
    try:
        if os.path.isdir(p) and not os.listdir(p):
            os.rmdir(p)
    except Exception:
        pass


def file_sha256(path, progress=None, cancel=None):
    """
    整文件 SHA-256，带进度与取消。

    分段摘要只能证明「收到的东西和发出的东西一样」，证明不了
    「读盘时没读错、写盘后没写坏」—— 因为两端算的都是同一份流。
    真要验证落盘结果，只能各自把文件完整读一遍再对。这个函数就是干这个的，
    8.9 GB 大概 30~60 秒，所以只在用户主动勾选时才调用。
    """
    h = hashlib.sha256()
    total = 0
    try:
        total = os.path.getsize(path)
    except Exception:
        pass
    done = 0
    with open(path, "rb") as f:
        while True:
            if cancel and cancel():
                raise InterruptedError(_t("c043"))
            b = f.read(4 * 1024 * 1024)
            if not b:
                break
            h.update(b)
            done += len(b)
            if progress:
                try:
                    progress(done, total)
                except Exception:
                    pass
    return h.hexdigest()


def open_in_file_manager(path):
    """
    用系统文件管理器打开一个目录（Windows 下是资源管理器）。
    只做「打开」，不执行路径里的任何东西；调用方负责先确认目录存在。
    """
    path = os.path.normpath(path)
    if os.name == "nt":
        exe = os.path.join(os.environ.get("SystemRoot") or r"C:\Windows",
                           "explorer.exe")
        if not os.path.isfile(exe):
            exe = "explorer.exe"
        # explorer 对逗号/引号有怪癖，用 list2cmdline 让它自己加引号
        subprocess.Popen([exe, path])
    else:
        import sys
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.Popen([opener, path])


# ---------------------------------------------------------------- 服务端

class PeerServer(threading.Thread):
    """接收端：监听 TCP，接受已配对的对端推送/取回。"""

    def __init__(self, recv_root, psk, port=TCP_PORT, log=None,
                 allow_discovery=True, notify=None):
        super().__init__(daemon=True, name="LanSplice-Server")
        self.recv_root = recv_root
        self.psk = psk
        self.port = port
        self.log = log or (lambda s: None)
        self.notify = notify or (lambda kind, data: None)
        self.allow_discovery = allow_discovery
        # 本实例的身份证：宣告里带上，收到就认得「这是我自己发的」。
        # 光比 IP 不够（多网卡、回环、NAT 会让自己的包换个源地址回来）。
        self.inst = secrets.token_hex(8)
        self._stop = threading.Event()
        self._srv = None
        self._disc = None
        self.running = False
        self.error = None

    # ---- 生命周期
    def start_server(self):
        self.start()

    def run(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(("0.0.0.0", self.port))
            s.listen(8)
            s.settimeout(0.5)
            self._srv = s
            self.running = True
            os.makedirs(self.recv_root, exist_ok=True)
            self.log(_t("c020") % (self.port, self.recv_root))
            # 清掉过期分片：分片是为续传故意留的，但取消过的传输会一直占地方
            n = clean_parts(self.recv_root)
            if n:
                self.log(_t("c063") % n)
        except Exception as e:
            self.error = str(e)
            self.log(_t("c021") % e)
            return

        if self.allow_discovery:
            threading.Thread(target=self._discovery_loop, daemon=True,
                             name="LanSplice-Discovery").start()

        while not self._stop.is_set():
            try:
                conn, addr = self._srv.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            tune_socket(conn)
            if not is_private_ipv4(addr[0]):
                self.log(_t("c022") % addr[0])
                try:
                    conn.close()
                except Exception:
                    pass
                continue
            threading.Thread(target=self._handle_conn, args=(conn, addr),
                             daemon=True).start()

        self.running = False
        try:
            self._srv.close()
        except Exception:
            pass

    def stop_server(self):
        self._stop.set()
        self.running = False
        for s in (self._srv, self._disc):
            try:
                s.close()
            except Exception:
                pass

    # ---- 发现应答
    def _discovery_loop(self):
        """
        发现服务：一边应答别人的查找，一边定期主动宣告自己。

        只应答不宣告的话，会造成一个很别扭的体验：
        先开的那台永远看不见后开的那台，必须自己重开一次程序，
        或者手动点「重新查找」才行。定期宣告 + 收到别人的宣告就记一笔，
        两台不管谁先开，几秒内都会自动互相看见。
        """
        try:
            d = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            d.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            d.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            d.bind(("0.0.0.0", DISCOVERY_PORT))
            d.settimeout(0.4)
            self._disc = d
        except Exception as e:
            self.log(_t("c023") % e)
            return

        me = set(local_ips())
        last_announce = 0.0
        last_refresh = time.time()

        while not self._stop.is_set():
            now = time.time()

            # 地址偶尔会变（插拔网线、换 Wi-Fi），一分钟刷一次
            if now - last_refresh > 60:
                me = set(local_ips())
                last_refresh = now

            if now - last_announce >= ANNOUNCE_EVERY:
                last_announce = now
                self._announce(d)

            try:
                data, addr = d.recvfrom(1024)
            except socket.timeout:
                continue
            except OSError:
                break

            ip = addr[0]
            if not is_private_ipv4(ip):
                continue

            # 有人来找：一律应答。这里**不能**过滤本机地址 ——
            # 同一台机器上跑客户端扫描（或以后开两个实例）时，
            # 源的 IP 就是本机 IP，过滤掉就永远发现不了。
            if data.startswith(b"L2P-DISCOVER"):
                self._send_offer(d, addr)
                continue

            # 别人在宣告自己 —— 记下来交给界面，列表里自动出现。
            # 自己周期宣告的包也会回到这个 socket，这里必须滤掉。
            if data.startswith(b"L2P-OFFER"):
                if is_own_addr(ip, me):
                    continue
                try:
                    info = json.loads(data[9:].decode("utf-8"))
                except Exception:
                    continue
                if self._is_self_offer(info, ip, me):
                    continue                         # 绕了一圈回来的自己的包
                info["ip"] = ip                      # 以封包源地址为准
                info["port"] = int(info.get("port") or TCP_PORT)
                info["self"] = False
                self.notify("peer_seen", info)

    def _is_self_offer(self, info, ip, me=None):
        """这条通告是不是本机自己发的：源地址命中，或者实例号命中。"""
        if is_own_addr(ip, me):
            return True
        inst = (info or {}).get("inst")
        return bool(inst) and inst == self.inst

    def _offer_payload(self, ip=None):
        return (b"L2P-OFFER" + json.dumps({
            "magic": "L2P",
            "v": PROTO_VER,
            "name": hostname(),
            "port": self.port,
            "ip": ip or local_ip(),
            "inst": self.inst,
        }).encode("utf-8"))

    def _send_offer(self, sock, addr):
        try:
            sock.sendto(self._offer_payload(), addr)
        except Exception:
            pass

    def _announce(self, sock):
        """向每块网卡的子网广播地址各喊一声「我在」。"""
        msg = self._offer_payload()
        targets = set(d["bcast"] for d in list_ipv4())
        targets.add("255.255.255.255")
        for t in targets:
            try:
                sock.sendto(msg, (t, DISCOVERY_PORT))
            except Exception:
                pass

    # ---- 单连接处理
    def _handle_conn(self, conn, addr):
        conn.settimeout(120)
        peer = addr[0]
        try:
            ch = _hs_server(conn, self.psk)
        except AuthError:
            self.log(_t("c024") % peer)
            try:
                conn.close()
            except Exception:
                pass
            return
        except Exception as e:
            self.log(_t("c025") % (peer, e))
            try:
                conn.close()
            except Exception:
                pass
            return

        self.log(_t("c026") % peer)
        try:
            while not self._stop.is_set():
                try:
                    msg = ch.recv_json()
                except (ConnectionError, ProtocolError, OSError):
                    break
                if not self._dispatch(ch, msg):
                    break
        except Exception as e:
            self.log(_t("c027") % (peer, e))
        finally:
            ch.close()
            self.log(_t("c028") % peer)

    def _dispatch(self, ch, msg):
        t = msg.get("t")

        if t == "hello":
            ch.send_json({"t": "hello", "name": hostname(), "ver": "1.4",
                          "proto": PROTO_VER,
                          "caps": [CAP_RESUME],
                          "root": self.recv_root})
            return True

        if t == "bye":
            return False

        if t == "text":
            return self._do_text(ch, msg)

        if t == "stat":
            return self._do_stat(ch, msg)

        if t == "put":
            return self._do_put(ch, msg)

        if t == "get":
            return self._do_get(ch, msg)

        if t == "open_dir":
            return self._do_open_dir(ch, msg)

        if t == "mkdir":
            try:
                p = safe_join(self.recv_root, msg["path"])
                os.makedirs(p, exist_ok=True)
                ch.send_json({"t": "ok"})
            except Exception as e:
                ch.send_json({"t": "error", "msg": str(e)})
            return True

        ch.send_json({"t": "error", "msg": _t("c029") % t})
        return True

    def _do_text(self, ch, msg):
        """
        收到一段文字（剪贴板内容、链接、代码片段）。

        不落盘、不写进日志正文：日志只记长度。用户从剪贴板推过来的东西
        可能是密码或密钥，留在日志里等于埋雷。
        """
        body = msg.get("body") or ""
        if not isinstance(body, str):
            body = str(body)
        if len(body.encode("utf-8")) > MAX_TEXT:
            ch.send_json({"t": "error", "msg": _t("c061") % (MAX_TEXT // 1024)})
            return True
        self.log(_t("c062") % len(body))
        self.notify("recv_text", {"body": body,
                                  "from": msg.get("from") or "",
                                  "clip": bool(msg.get("clip"))})
        ch.send_json({"t": "ok"})
        return True

    def _do_stat(self, ch, msg):
        try:
            p = safe_join(self.recv_root, msg["path"])
            if os.path.isfile(p):
                st = os.stat(p)
                rel = msg["path"]
                ch.send_json({"t": "stat", "exists": True, "is_dir": False,
                              "size": st.st_size, "mtime": int(st.st_mtime)})
            elif os.path.isdir(p):
                ch.send_json({"t": "stat", "exists": True, "is_dir": True,
                              "size": 0, "mtime": int(os.stat(p).st_mtime)})
            else:
                ch.send_json({"t": "stat", "exists": False})
        except Exception as e:
            ch.send_json({"t": "error", "msg": str(e)})
        return True

    def _do_put(self, ch, msg):
        rel = msg.get("path")
        size = int(msg.get("size") or 0)
        mtime = msg.get("mtime")
        rid = msg.get("rid") or ""
        overwrite = bool(msg.get("overwrite"))
        expect = msg.get("expect") or ""
        # 只有对端明确说要校验才走新流程。老版本（v1.3.x）不认识 segh 帧，
        # 给它多发一个控制帧会让它直接报协议错，所以能力协商不能省。
        use_seg = bool(msg.get("hash")) and bool(rid)

        try:
            target = safe_join(self.recv_root, rel)
        except Exception as e:
            ch.send_json({"t": "error", "msg": str(e)})
            return True

        free = _free_space(os.path.dirname(target) or self.recv_root)
        if free is not None and size > free - 50 * 1024 * 1024:
            ch.send_json({"t": "error", "msg": _t("c030")})
            return True

        d = os.path.dirname(target) or os.path.abspath(self.recv_root)
        os.makedirs(d, exist_ok=True)

        # ---- 断点续传：找回同一 rid 上次留下的分片
        part = None
        offset = 0
        if use_seg:
            pdir = os.path.join(d, PART_DIR)
            try:
                os.makedirs(pdir, exist_ok=True)
            except Exception:
                pass
            part = os.path.join(pdir, rid + ".part")
            if os.path.isfile(part):
                try:
                    offset = os.path.getsize(part)
                except Exception:
                    offset = 0
                if offset > size:
                    offset = 0
                # 只认完整的段：末尾那截不完整的丢掉，让发送端补上。
                # 这样 offset 永远落在段边界上，续传时分段哈希才对得齐。
                offset = (offset // SEG_SIZE) * SEG_SIZE
                try:
                    with open(part, "r+b") as f:
                        f.truncate(offset)
                except Exception:
                    offset = 0

        # ---- 重名处理：默认绝不覆盖
        # 续传必须落回原来的名字，否则分片和目标对不上。
        if offset > 0 or overwrite:
            final_path = target
        else:
            final_path = unique_path(target)

        if offset == 0 and part:
            try:
                if os.path.exists(part):
                    os.remove(part)
            except Exception:
                pass

        tmp = part if part else (final_path + ".l2ptmp")
        root_abs = os.path.abspath(self.recv_root)
        rel_final = os.path.relpath(final_path, root_abs).replace("\\", "/")
        renamed = os.path.normcase(final_path) != os.path.normcase(target)

        ch.send_json({"t": "ready", "offset": offset, "path": rel_final})
        self.notify("recv_begin", {"path": final_path, "size": size,
                                   "offset": offset, "renamed": renamed})

        got = offset
        t0 = time.time()
        seg_local = []          # 本端对每一段算出的摘要
        seg_remote = []         # 对端送来的摘要
        seg_hasher = hashlib.sha256()
        corrupt = False
        try:
            with open(tmp, "r+b" if offset else "wb") as f:
                if offset:
                    f.seek(offset)
                while got < size:
                    ftype, payload = ch.recv_frame()
                    if ftype == FRAME_CTRL:
                        obj = _try_json(payload)
                        if obj.get("t") == "segh":
                            seg_remote.append(obj.get("h") or "")
                        elif obj.get("t") == "error":
                            raise ProtocolError(obj.get("msg")
                                                or _t("c031") % (size, got))
                        continue
                    if ftype != FRAME_DATA:
                        continue
                    f.write(payload)
                    got += len(payload)
                    if use_seg:
                        seg_hasher.update(payload)
                        if got % SEG_SIZE == 0 or got == size:
                            seg_local.append(seg_hasher.hexdigest())
                            seg_hasher = hashlib.sha256()
                    self.notify("recv_progress", {"path": final_path, "done": got,
                                                  "total": size})

                if got != size:
                    raise ProtocolError(_t("c031") % (size, got))

                # 最后一段的摘要还在路上，读完再比，否则会漏掉尾巴那一刀
                while use_seg and len(seg_remote) < len(seg_local):
                    ftype, payload = ch.recv_frame()
                    if ftype != FRAME_CTRL:
                        continue
                    obj = _try_json(payload)
                    if obj.get("t") == "segh":
                        seg_remote.append(obj.get("h") or "")
                    elif obj.get("t") == "error":
                        raise ProtocolError(obj.get("msg")
                                            or _t("c031") % (size, got))

            if use_seg and seg_remote != seg_local:
                bad = 0
                for i in range(min(len(seg_local), len(seg_remote))):
                    if seg_local[i] != seg_remote[i]:
                        bad = i
                        break
                corrupt = True
                raise ProtocolError(_t("c060") % (bad + 1,
                                                  SEG_SIZE // 1048576))

            if expect:
                # 整体重读一遍再对。这一步才真正覆盖「读盘/写盘出错」，
                # 前面的分段摘要只能证明两端算的是同一份流。
                self.notify("recv_verify", {"path": final_path})
                actual = file_sha256(tmp)
                if actual != expect:
                    corrupt = True
                    raise ProtocolError(_t("c066"))

            if mtime:
                try:
                    os.utime(tmp, (mtime, mtime))
                except Exception:
                    pass
            os.replace(tmp, final_path)
            dt = max(time.time() - t0, 0.001)
            ch.send_json({"t": "done", "bytes": got, "path": rel_final})
            self.log(_t("c032") % (
                rel_final, human_size(got), (got - offset) / 1048576.0 / dt))
            self.notify("recv_done", {"path": final_path, "size": got,
                                      "resumed": offset > 0})
            if part:
                _rmdir_if_empty(os.path.dirname(part))
        except Exception as e:
            # 断线：分片故意留着，下次点发送自动续传。
            # 校验失败：分片里的数据已经坏了，删掉重来，留着只会一直错。
            if corrupt and part:
                try:
                    os.remove(part)
                except Exception:
                    pass
            elif not part:
                try:
                    if os.path.exists(tmp):
                        os.remove(tmp)
                except Exception:
                    pass
            try:
                ch.send_json({"t": "error", "msg": str(e)})
            except Exception:
                pass
            self.log(_t("c033") % (rel, e))
            self.notify("recv_error", {"path": rel, "msg": str(e),
                                       "kept": bool(part) and not corrupt})
        return True

    def _do_get(self, ch, msg):
        """对端来取文件，服务端读它的接收目录发过去。"""
        rel = msg.get("path")
        try:
            p = safe_join(self.recv_root, rel)
        except Exception as e:
            ch.send_json({"t": "error", "msg": str(e)})
            return True
        if not os.path.isfile(p):
            ch.send_json({"t": "error", "msg": _t("c034")})
            return True

        st = os.stat(p)
        ch.send_json({"t": "file", "size": st.st_size, "mtime": int(st.st_mtime)})
        sent = 0
        t0 = time.time()
        try:
            with open(p, "rb") as f:
                while sent < st.st_size:
                    buf = f.read(CHUNK)
                    if not buf:
                        break
                    ch.send_data(buf)
                    sent += len(buf)
            dt = max(time.time() - t0, 0.001)
            self.log(_t("c035") % (
                rel, human_size(sent), sent / 1048576.0 / dt))
        except Exception as e:
            self.log(_t("c036") % (rel, e))
        return True

    def _do_open_dir(self, ch, msg):
        """
        对端请求：在**这台机器**上用资源管理器打开接收目录（或其子目录）。
        只允许落在 recv_root 之内，防止被当成任意路径打开器。
        """
        rel = (msg.get("path") or "").strip()
        root_abs = os.path.abspath(self.recv_root)
        if not os.path.isdir(root_abs):
            ch.send_json({"t": "error",
                          "msg": _t("c037") % self.recv_root})
            return True
        try:
            if rel in ("", ".", "\\", "/"):
                target = root_abs
            else:
                target = safe_join(self.recv_root, rel)
        except Exception as e:
            ch.send_json({"t": "error", "msg": str(e)})
            return True

        # 子目录可能已被改名/删除：往上退，但**不许越过接收根目录**
        while target != root_abs and not os.path.isdir(target):
            target = os.path.dirname(target)
        if not os.path.isdir(target):
            target = root_abs

        try:
            open_in_file_manager(target)
        except Exception as e:
            ch.send_json({"t": "error", "msg": _t("c038") % e})
            return True
        self.log(_t("c039") % target)
        ch.send_json({"t": "ok", "path": target})
        return True


# ---------------------------------------------------------------- 客户端

class LinkClient:
    """发送端：连上对端，推送或取回文件。"""

    def __init__(self, ip, port, psk, timeout=10):
        self.ip = ip
        self.port = port
        self.psk = psk
        self.timeout = timeout
        self.sock = None
        self.ch = None
        self.peer_name = None
        self.peer_ver = ""
        self.peer_caps = ()      # 对端能力集，决定能不能续传/分段校验
        self.peer_root = ""      # 对端接收目录，握手时上报，用于结果里显示"存到哪"

    def open(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(self.timeout)
        try:
            s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        except Exception:
            pass
        s.connect((self.ip, self.port))
        tune_socket(s)
        s.settimeout(300)
        self.sock = s
        self.ch = _hs_client(s, self.psk)
        self.ch.send_json({"t": "hello", "name": hostname(), "ver": "1.4",
                           "proto": PROTO_VER, "caps": [CAP_RESUME]})
        info = self.ch.recv_json()
        if info.get("t") != "hello":
            raise ProtocolError(_t("c040"))
        self.peer_name = info.get("name")
        self.peer_ver = info.get("ver") or ""
        caps = info.get("caps")
        # 老版本没有 caps 字段，这里给空元组，后面的新协议特性全部自动退回
        self.peer_caps = tuple(caps) if isinstance(caps, (list, tuple)) else ()
        # 对端可能回 "E:/新建文件夹" 这种正斜杠写法，统一成本地习惯的形式
        _root = info.get("root") or ""
        self.peer_root = os.path.normpath(_root) if _root else ""
        return self

    def close(self):
        try:
            if self.ch:
                self.ch.send_json({"t": "bye"})
        except Exception:
            pass
        try:
            if self.sock:
                self.sock.close()
        except Exception:
            pass

    def stat(self, rel):
        self.ch.send_json({"t": "stat", "path": rel})
        return self.ch.recv_json()

    def open_dir(self, rel=""):
        """
        让对端在它自己的屏幕上打开接收目录（rel 为空即接收根目录）。
        返回被打开的绝对路径；对端报错时抛 ProtocolError。
        """
        self.ch.send_json({"t": "open_dir", "path": rel or ""})
        r = self.ch.recv_json()
        if r.get("t") == "error":
            raise ProtocolError(r.get("msg") or _t("c041"))
        return r.get("path") or ""

    def upload(self, local_path, rel_path, progress=None, cancel=None,
               overwrite=False, deep_verify=False, verify_progress=None):
        """
        推送一个文件。progress(done, total, speed_bps) 会被频繁调用。

        返回 (是否跳过, 本次实际发送字节, 对端最终落点相对路径)。

        第三项在对端重名被改名时和 rel_path 不同 —— 界面靠它告诉用户
        「另存为 xxx (2).mp4」，否则用户去接收目录会找不到文件。

        断点续传：发送前对端会回报已收字节数 offset，从那里接着发。
        跳过的部分不计入速度，否则续传刚开始会显示一个假的超高速度。

        deep_verify：发送前把整个文件读一遍算出 SHA-256，接收端写完后
        也读一遍比对。这是唯一能查出「读盘/写盘出错」的办法，
        代价是两边各多读一遍磁盘，所以默认关，由用户勾选。
        """
        size = os.path.getsize(local_path)
        mtime = int(os.path.getmtime(local_path))
        v2 = CAP_RESUME in self.peer_caps

        # 增量判断：对端已有同大小同修改时间就跳过
        st = self.stat(rel_path)
        if st.get("t") == "error":
            raise ProtocolError(st.get("msg"))
        if st.get("t") == "stat" and st.get("exists") and not st.get("is_dir"):
            if st.get("size") == size and abs((st.get("mtime") or 0) - mtime) <= 2:
                if progress:
                    progress(size, size, 0.0)
                return (True, 0, rel_path)

        expect = None
        if deep_verify and v2 and size > 0:
            expect = file_sha256(local_path, progress=verify_progress,
                                 cancel=cancel)

        req = {"t": "put", "path": rel_path, "size": size, "mtime": mtime}
        if v2:
            req["rid"] = transfer_id(rel_path, size, mtime)
            req["hash"] = True
            req["overwrite"] = bool(overwrite)
            if expect:
                req["expect"] = expect
        self.ch.send_json(req)
        resp = self.ch.recv_json()
        if resp.get("t") != "ready":
            raise ProtocolError(resp.get("msg") or _t("c042"))

        offset = int(resp.get("offset") or 0) if v2 else 0
        if offset > size:
            offset = 0
        final_rel = resp.get("path") or rel_path

        sent = offset
        t0 = time.time()
        seg = hashlib.sha256()
        with open(local_path, "rb") as f:
            f.seek(offset)
            while sent < size:
                if cancel and cancel():
                    raise InterruptedError(_t("c043"))
                buf = f.read(min(CHUNK, size - sent))
                if not buf:
                    break
                self.ch.send_data(buf)
                sent += len(buf)
                if v2:
                    seg.update(buf)
                    # 段末把摘要递过去，再发下一段，对端逐段对账
                    if sent % SEG_SIZE == 0 or sent == size:
                        self.ch.send_json({"t": "segh", "h": seg.hexdigest()})
                        seg = hashlib.sha256()
                if progress:
                    dt = max(time.time() - t0, 0.001)
                    progress(sent, size, (sent - offset) / dt)

        done = self.ch.recv_json()
        if done.get("t") != "done":
            raise ProtocolError(done.get("msg") or _t("c044"))
        return (False, sent - offset, final_rel)

    def send_text(self, body, clip=False):
        """
        把一段文字推给对端（剪贴板内容或手输的链接）。

        对端会直接弹出来，用户点一下就能粘贴 —— 双机工作流里，
        这个动作的频率通常比传文件还高。
        """
        if not isinstance(body, str):
            body = str(body)
        if not body:
            raise ProtocolError(_t("c064"))
        if len(body.encode("utf-8")) > MAX_TEXT:
            raise ProtocolError(_t("c061") % (MAX_TEXT // 1024))
        self.ch.send_json({"t": "text", "body": body,
                           "from": hostname(), "clip": bool(clip)})
        r = self.ch.recv_json()
        if r.get("t") != "ok":
            raise ProtocolError(r.get("msg") or _t("c065"))
        return True

    def download(self, rel_path, local_path, progress=None, cancel=None):
        """从对端取回一个文件。返回 (是否跳过, 传输字节)。"""
        st = self.stat(rel_path)
        if st.get("t") != "stat" or not st.get("exists") or st.get("is_dir"):
            raise ProtocolError(_t("c045") % rel_path)

        size = st.get("size") or 0
        mtime = st.get("mtime") or 0

        if os.path.isfile(local_path):
            ls = os.path.getsize(local_path)
            lm = int(os.path.getmtime(local_path))
            if ls == size and abs(lm - mtime) <= 2:
                if progress:
                    progress(size, size, 0.0)
                return (True, 0)

        self.ch.send_json({"t": "get", "path": rel_path})
        resp = self.ch.recv_json()
        if resp.get("t") != "file":
            raise ProtocolError(resp.get("msg") or _t("c046"))

        os.makedirs(os.path.dirname(local_path) or ".", exist_ok=True)
        tmp = local_path + ".l2ptmp"
        got = 0
        t0 = time.time()
        with open(tmp, "wb") as f:
            while got < size:
                if cancel and cancel():
                    raise InterruptedError(_t("c043"))
                buf = self.ch.recv_data()
                if not buf:
                    continue
                f.write(buf)
                got += len(buf)
                if progress:
                    dt = max(time.time() - t0, 0.001)
                    progress(got, size, got / dt)

        if got != size:
            try:
                os.remove(tmp)
            except Exception:
                pass
            raise ProtocolError(_t("c047") % (size, got))
        if mtime:
            try:
                os.utime(tmp, (mtime, mtime))
            except Exception:
                pass
        os.replace(tmp, local_path)
        return (False, got)


# ---------------------------------------------------------------- 发现

def discover(timeout=1.5, verbose=None):
    """
    找局域网里的 LanSplice，返回 [{name, ip, port}]。

    关键：对**每一块**网卡的子网广播地址各发一遍。
    只发 255.255.255.255 时 Windows 只挑一块网卡（按路由度量），
    机器上装了 VMware / VirtualBox / Hyper-V / VPN 就极易挑中虚拟网卡，
    广播进了虚拟网段，真实局域网上的对端永远收不到。
    """
    log = verbose or (lambda s: None)
    found = {}
    socks = []          # [(sock, 广播地址, 本网卡IP)]
    me = set(local_ips())
    msg = b"L2P-DISCOVER" + str(PROTO_VER).encode()

    for d in list_ipv4():
        try:
            sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sk.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sk.bind((d["ip"], 0))       # 绑到这块网卡，才能从它发出去
            sk.setblocking(False)
            socks.append((sk, d["bcast"], d["ip"]))
        except Exception:
            try:
                sk.close()
            except Exception:
                pass

    # 兜底：不绑网卡，发受限广播（有些系统上反而是它能出去）
    try:
        sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sk.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sk.setblocking(False)
        socks.append((sk, "255.255.255.255", "0.0.0.0"))
    except Exception:
        pass

    if not socks:
        return []

    sent = 0
    for _ in range(3):
        for sk, bcast, _ip in socks:
            try:
                sk.sendto(msg, (bcast, DISCOVERY_PORT))
                sent += 1
            except Exception as e:
                log(_t("c048") % (bcast, e))
        time.sleep(0.05)

    sock_map = {sk: (bcast, ip) for sk, bcast, ip in socks}
    t_end = time.time() + timeout
    try:
        while time.time() < t_end:
            try:
                ready, _, _ = select.select(list(sock_map), [], [], 0.15)
            except OSError:
                break
            for sk in ready:
                while True:
                    try:
                        data, addr = sk.recvfrom(2048)
                    except (BlockingIOError, socket.timeout):
                        break
                    except OSError:
                        break
                    if not data.startswith(b"L2P-OFFER"):
                        continue
                    try:
                        info = json.loads(data[9:].decode("utf-8"))
                    except Exception:
                        continue
                    ip = addr[0]
                    info["ip"] = ip
                    info["port"] = int(info.get("port") or TCP_PORT)
                    info["self"] = is_own_addr(ip, me)
                    info["via"] = sock_map[sk][0]
                    found[(ip, info["port"])] = info
    finally:
        for sk, _b, _i in socks:
            try:
                sk.close()
            except Exception:
                pass

    log(_t("c049")
        % (len(list_ipv4()), sent, len(found)))
    return sorted(found.values(),
                  key=lambda x: (x.get("self", False), x.get("name", "")))


# ---------------------------------------------------------------- 任务编排

def collect_targets(paths):
    """
    把用户拖进来的文件/文件夹展开成 [(本地绝对路径, 发送时的相对路径)]。
    多个目标各取自己的名字做根，保持目录结构。
    """
    out = []
    for p in paths:
        p = os.path.abspath(p)
        if os.path.isfile(p):
            out.append((p, os.path.basename(p)))
        elif os.path.isdir(p):
            base = os.path.dirname(p)
            for root, dirs, files in os.walk(p):
                for f in files:
                    full = os.path.join(root, f)
                    rel = os.path.relpath(full, base)
                    out.append((full, rel))
    return out
