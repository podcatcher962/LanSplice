# -*- coding: utf-8 -*-
"""LanSplice 网络体检 · 探测核心。

只用标准库 + ctypes：Windows 走 iphlpapi，Linux/macOS 走 ip 命令与系统工具。
这里不做任何判断，只负责「把事实取回来」——结论交给 netcheck_rules.py。
"""
import json
import os
import socket
import struct
import subprocess
import sys
import time

APP_NAME = "LanSplice 网络体检"
# 版本号不在这里写：报告和窗口都用 link2pc_core.APP_VER，免得两处对不上。

# 与 LanSplice 对齐的端口与协议（发现包格式就是它的广播协议）
PROTO_VER = 1
DISCOVERY_PORT = 47821
LS_TCP_PORT = 47820
LS_WEB_PORT = 47822

# 局域网体检要看的端口：常见的服务 + LanSplice 自己那两个
COMMON_PORTS = [
    (53, "DNS"),
    (80, "HTTP"),
    (443, "HTTPS"),
    (139, "NetBIOS"),
    (445, "SMB 共享"),
    (5000, "NAS / 路由器"),
    (8080, "HTTP 代理"),
    (9100, "打印机"),
    (LS_TCP_PORT, "LanSplice 传输"),
    (LS_WEB_PORT, "LanSplice 手机页"),
]

IS_WIN = sys.platform.startswith("win")
_NO_WINDOW = 0x08000000 if IS_WIN else 0


# ---------------------------------------------------------------- 本机网卡

def list_ipv4():
    """[{ip, prefix, bcast, index}]，只保留真正能用的 IPv4。"""
    if IS_WIN:
        rows, _ = _ipv4_windows()
    else:
        rows = _ipv4_posix()
    if not rows:
        rows = _ipv4_fallback()
    return _rank(rows)


def _rank(rows):
    def key(d):
        ip = d["ip"]
        # 家用网段排前面，虚拟网卡排后面；同样是 /24 的优先
        return (0 if ip.startswith("192.168.") else
                1 if ip.startswith("10.") else
                2 if ip.startswith("172.") else 3,
                d.get("prefix") != 24)
    return sorted(rows, key=key)


def _ipv4_windows():
    out, seen = [], set()
    try:
        import ctypes
        from ctypes import wintypes

        iphlpapi = ctypes.WinDLL("iphlpapi.dll")
        size = wintypes.ULONG(0)
        iphlpapi.GetIpAddrTable(None, ctypes.byref(size), 0)
        if size.value < 4:
            return [], seen
        buf = ctypes.create_string_buffer(size.value + 128)
        if iphlpapi.GetIpAddrTable(buf, ctypes.byref(size), 0) != 0:
            return [], seen
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
        return [], seen
    return out, seen


def _ipv4_posix():
    out = []
    try:
        txt = subprocess.run(["ip", "-4", "-o", "addr", "show"],
                             capture_output=True, text=True, timeout=4).stdout
    except Exception:
        return out
    for line in txt.splitlines():
        parts = line.split()
        if len(parts) < 4 or parts[2] != "inet":
            continue
        cidr = parts[3]
        if "/" not in cidr:
            continue
        ip, pfx = cidr.split("/")
        pfx = int(pfx)
        if ip.startswith(("127.", "169.254.")):
            continue
        ip_i = struct.unpack(">I", socket.inet_aton(ip))[0]
        mask = (0xFFFFFFFF << (32 - pfx)) & 0xFFFFFFFF if pfx else 0
        out.append({"ip": ip, "prefix": pfx, "index": 0,
                    "bcast": socket.inet_ntoa(
                        struct.pack(">I", ip_i | (~mask & 0xFFFFFFFF)))})
    return out


def _ipv4_fallback():
    out, seen = [], set()
    try:
        for ip in socket.gethostbyname_ex(socket.gethostname())[2]:
            if not ip or ip.startswith(("127.", "169.254.")) or ip in seen:
                continue
            seen.add(ip)
            out.append({"ip": ip, "prefix": 24, "index": 0,
                        "bcast": ".".join(ip.split(".")[:3] + ["255"])})
    except Exception:
        pass
    return out


def local_ips():
    return [d["ip"] for d in list_ipv4()]


def gateways():
    """{if_index: 网关 IP}，只取默认路由常用的那几条。"""
    if not IS_WIN:
        return _gateways_posix()
    out = {}
    try:
        import ctypes
        from ctypes import wintypes

        class ROW(ctypes.Structure):
            _fields_ = [("dwForwardDest", wintypes.DWORD),
                        ("dwForwardMask", wintypes.DWORD),
                        ("dwForwardPolicy", wintypes.DWORD),
                        ("dwForwardNextHop", wintypes.DWORD),
                        ("dwForwardIfIndex", wintypes.DWORD),
                        ("dwForwardType", wintypes.DWORD),
                        ("dwForwardProto", wintypes.DWORD),
                        ("dwForwardAge", wintypes.DWORD),
                        ("dwForwardNextHopAS", wintypes.DWORD),
                        ("dwForwardMetric1", wintypes.DWORD),
                        ("dwForwardMetric2", wintypes.DWORD),
                        ("dwForwardMetric3", wintypes.DWORD),
                        ("dwForwardMetric4", wintypes.DWORD),
                        ("dwForwardMetric5", wintypes.DWORD)]

        iphlpapi = ctypes.WinDLL("iphlpapi.dll")
        size = wintypes.ULONG(0)
        iphlpapi.GetIpForwardTable(None, ctypes.byref(size), 0)
        if size.value < 4:
            return out
        buf = ctypes.create_string_buffer(size.value + 128)
        if iphlpapi.GetIpForwardTable(buf, ctypes.byref(size), 0) != 0:
            return out
        raw = ctypes.string_at(buf, size.value)
        n = struct.unpack("<I", raw[:4])[0]
        step = ctypes.sizeof(ROW)
        for i in range(n):
            off = 4 + i * step
            if off + step > len(raw):
                break
            row = ROW.from_buffer_copy(raw[off:off + step])
            if row.dwForwardDest != 0:          # 只要默认路由
                continue
            gw = socket.inet_ntoa(struct.pack("<I", row.dwForwardNextHop))
            if gw.startswith("0."):
                continue
            idx = row.dwForwardIfIndex
            if idx not in out or row.dwForwardMetric1 < 9999:
                out.setdefault(idx, gw)
    except Exception:
        return {}
    return out


def _gateways_posix():
    out = {}
    try:
        txt = subprocess.run(["ip", "route", "show", "default"],
                             capture_output=True, text=True, timeout=4).stdout
    except Exception:
        return out
    for line in txt.splitlines():
        parts = line.split()
        if "via" in parts:
            out[0] = parts[parts.index("via") + 1]
            break
    return out


def link_speeds():
    """{接口描述或名字: (速率文本, 是否无线)}。拿不到就返回空，不编造。"""
    out = {}
    if IS_WIN:
        ps = ("Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | "
              "Select-Object Name,InterfaceDescription,LinkSpeed,MediaType | "
              "ConvertTo-Json -Compress")
        try:
            r = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
                capture_output=True, text=True, timeout=8,
                creationflags=_NO_WINDOW, encoding="utf-8", errors="replace")
            data = json.loads(r.stdout or "[]")
            if isinstance(data, dict):
                data = [data]
            for d in data:
                mt = (d.get("MediaType") or "")
                out[d.get("InterfaceDescription") or d.get("Name") or "?"] = (
                    d.get("LinkSpeed") or "—", "802.11" in mt or "Native" in mt)
        except Exception:
            pass
        return out
    try:
        txt = subprocess.run(["ip", "-o", "link", "show"],
                             capture_output=True, text=True, timeout=4).stdout
        for line in txt.splitlines():
            parts = line.split(":")
            if len(parts) >= 2:
                out[parts[1].split("@")[0].strip()] = ("—", "wlan" in parts[1])
    except Exception:
        pass
    return out


# ---------------------------------------------------------------- 邻居表

def arp_table():
    """[{ip, mac, index}]。Windows 走 GetIpNetTable，比解析 arp -a 稳。"""
    rows = _arp_windows() if IS_WIN else _arp_posix()
    me = set(local_ips())
    out = []
    for r in rows:
        if r["ip"] in me:
            continue
        if r["ip"].startswith(("224.", "239.", "255.", "0.")):
            continue
        # .255 是网段广播，不是设备；静态表项里常留着一条，别把它算成一台机器
        if r["ip"].endswith(".255"):
            continue
        if r.get("type") == 4:
            continue
        if r["mac"].upper() in ("00-00-00-00-00-00", "FF-FF-FF-FF-FF-FF", ""):
            continue
        out.append(r)
    return out


def _arp_windows():
    out = []
    try:
        import ctypes
        from ctypes import wintypes

        class ROW(ctypes.Structure):
            _fields_ = [("dwIndex", wintypes.DWORD),
                        ("dwPhysAddrLen", wintypes.DWORD),
                        ("bPhysAddr", wintypes.BYTE * 8),
                        ("dwAddr", wintypes.DWORD),
                        ("dwType", wintypes.DWORD)]

        iphlpapi = ctypes.WinDLL("iphlpapi.dll")
        size = wintypes.ULONG(0)
        iphlpapi.GetIpNetTable(None, ctypes.byref(size), 0)
        if size.value < 4:
            return out
        buf = ctypes.create_string_buffer(size.value + 128)
        if iphlpapi.GetIpNetTable(buf, ctypes.byref(size), 0) != 0:
            return out
        raw = ctypes.string_at(buf, size.value)
        n = struct.unpack("<I", raw[:4])[0]
        step = ctypes.sizeof(ROW)
        for i in range(n):
            off = 4 + i * step
            if off + step > len(raw):
                break
            row = ROW.from_buffer_copy(raw[off:off + step])
            ln = min(row.dwPhysAddrLen, 8)
            mac = "-".join("%02X" % row.bPhysAddr[j] for j in range(ln))
            out.append({"ip": socket.inet_ntoa(
                struct.pack("<I", row.dwAddr)), "mac": mac,
                "index": row.dwIndex, "type": row.dwType})
    except Exception:
        return out
    return out


def _arp_posix():
    out = []
    try:
        txt = subprocess.run(["ip", "neigh"], capture_output=True, text=True,
                             timeout=4).stdout
    except Exception:
        return out
    for line in txt.splitlines():
        parts = line.split()
        if len(parts) < 5 or "lladdr" not in parts:
            continue
        try:
            mac = parts[parts.index("lladdr") + 1].upper()
        except Exception:
            continue
        out.append({"ip": parts[0], "mac": mac, "index": 0})
    return out


# ---------------------------------------------------------------- 延迟

def icmp_stats(ip, count=8, timeout_ms=800, interval=0.12):
    """打 ICMP，返回 {sent, recv, loss, min, max, avg, jitter, samples}。

    Windows 走 IcmpSendEcho（不需要管理员），其他平台退回系统 ping。
    """
    if not ip:
        return _empty_stats(count)
    if IS_WIN:
        samples = _icmp_windows(ip, count, timeout_ms, interval)
    else:
        samples = _icmp_posix(ip, count)
    return _stats_from(samples, count)


def _empty_stats(count):
    return {"sent": count, "recv": 0, "loss": 100.0, "min": None, "max": None,
            "avg": None, "jitter": None, "samples": []}


def _stats_from(samples, sent):
    if not samples:
        return _empty_stats(sent)
    avg = sum(samples) / len(samples)
    jitter = 0.0
    if len(samples) > 1:
        diffs = [abs(samples[i] - samples[i - 1]) for i in range(1, len(samples))]
        jitter = sum(diffs) / len(diffs)
    return {"sent": sent, "recv": len(samples),
            "loss": round(100.0 * (sent - len(samples)) / sent, 1),
            "min": min(samples), "max": max(samples),
            "avg": round(avg, 1), "jitter": round(jitter, 1),
            "samples": samples}


def _icmp_windows(ip, count, timeout_ms, interval):
    import ctypes
    from ctypes import wintypes

    class IP_OPTION_INFORMATION(ctypes.Structure):
        _fields_ = [("Ttl", ctypes.c_ubyte), ("Tos", ctypes.c_ubyte),
                    ("Flags", ctypes.c_ubyte), ("OptionsSize", ctypes.c_ubyte),
                    ("OptionsData", ctypes.c_void_p)]

    class ICMP_ECHO_REPLY(ctypes.Structure):
        _fields_ = [("Address", wintypes.ULONG), ("Status", wintypes.ULONG),
                    ("RoundTripTime", wintypes.ULONG),
                    ("DataSize", wintypes.USHORT),
                    ("Reserved", wintypes.USHORT),
                    ("Data", ctypes.c_void_p),
                    ("Options", IP_OPTION_INFORMATION)]

    samples = []
    iphlpapi = ctypes.WinDLL("iphlpapi.dll")
    # 必须显式声明签名：64 位下不声明，指针会被当成 int 压成 32 位，直接 access violation
    iphlpapi.IcmpCreateFile.restype = wintypes.HANDLE
    iphlpapi.IcmpSendEcho.argtypes = [
        wintypes.HANDLE, wintypes.ULONG, ctypes.c_char_p, wintypes.USHORT,
        ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD]
    iphlpapi.IcmpSendEcho.restype = wintypes.DWORD
    iphlpapi.IcmpCloseHandle.argtypes = [wintypes.HANDLE]
    iphlpapi.IcmpCloseHandle.restype = wintypes.BOOL
    h = iphlpapi.IcmpCreateFile()
    if not h or h == wintypes.HANDLE(-1).value:
        return samples
    try:
        payload = b"lanpulse-probe-0123456789abcdef"
        size = ctypes.sizeof(ICMP_ECHO_REPLY) + len(payload) + 64
        reply = ctypes.create_string_buffer(size)
        dest_u = struct.unpack("<I", socket.inet_aton(ip))[0]
        for i in range(count):
            t0 = time.time()
            n = iphlpapi.IcmpSendEcho(h, dest_u, payload, len(payload), None,
                                      reply, size, timeout_ms)
            if n:
                rep = ICMP_ECHO_REPLY.from_buffer_copy(reply.raw)
                if rep.Status == 0:
                    samples.append(int(rep.RoundTripTime) if rep.RoundTripTime
                                   else max(0, int((time.time() - t0) * 1000)))
            if i < count - 1:
                time.sleep(interval)
    finally:
        iphlpapi.IcmpCloseHandle(h)
    return samples


def _icmp_posix(ip, count):
    samples = []
    try:
        r = subprocess.run(["ping", "-c", str(count), "-W", "1", ip],
                           capture_output=True, text=True, timeout=count * 2 + 4)
        for line in r.stdout.splitlines():
            if "time=" in line:
                try:
                    samples.append(float(line.split("time=")[1].split()[0]))
                except Exception:
                    pass
    except Exception:
        pass
    return samples


# ---------------------------------------------------------------- 端口

def tcp_probe(ip, port, timeout=0.65):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((ip, port))
        return True
    except Exception:
        return False
    finally:
        try:
            s.close()
        except Exception:
            pass


def probe_ports(ip, ports=None, timeout=0.65):
    """并发探端口，返回 [(port, label, open)]。"""
    import threading
    ports = ports or COMMON_PORTS
    out = {}
    lock = threading.Lock()

    def work(port, label):
        ok = tcp_probe(ip, port, timeout)
        with lock:
            out[port] = (port, label, ok)

    ts = [threading.Thread(target=work, args=p, daemon=True) for p in ports]
    for t in ts:
        t.start()
    for t in ts:
        t.join(timeout + 1.5)
    return [out[p[0]] for p in ports if p[0] in out]


def win_snapshot(ports=None):
    """一次拿网卡速率和端口占用，纯 ctypes，不走 PowerShell。

    为什么不用 Get-NetAdapter / Get-NetTCPConnection：那两个 cmdlet 要加载模块，
    每次启动 3~5 秒，体检会被拖成十几秒。iphlpapi 这两个函数是毫秒级。
    返回 {"links": {名字: (速率文本, 无线)}, "listening": {端口: 进程名}}。
    """
    ports = ports or [LS_TCP_PORT, LS_WEB_PORT]
    out = {"links": {}, "listening": {}}
    if not IS_WIN:
        out["links"] = link_speeds()
        out["listening"] = listening_ports(ports)
        return out
    try:
        import ctypes
        from ctypes import wintypes

        iphlpapi = ctypes.WinDLL("iphlpapi.dll")
        # MIB_IFROW 是定长 860 字节；只读前几个字段，按偏移取，省得定义整个结构。
        # wszName[256] = 512 字节，dwIndex @512，dwType @516，dwMtu @520，dwSpeed @524
        for d in list_ipv4():
            buf = ctypes.create_string_buffer(1024)
            struct.pack_into("<I", buf, 512, d["index"])
            if iphlpapi.GetIfEntry(buf) != 0:
                continue
            iftype = struct.unpack_from("<I", buf, 516)[0]
            speed = struct.unpack_from("<I", buf, 524)[0]
            label = "%s · %s" % (d["ip"], _speed_text(speed))
            out["links"][label] = (_speed_text(speed), iftype == 71)
    except Exception:
        pass

    try:
        out["listening"] = _tcp_listeners(ports)
    except Exception:
        pass
    return out


def _speed_text(bps):
    if not bps:
        return "—"
    if bps >= 1000000000:
        v = bps / 1000000000.0
        return ("%g Gbps" % v) if v % 1 else ("%d Gbps" % int(v))
    if bps >= 1000000:
        return "%d Mbps" % int(round(bps / 1000000.0))
    return "%d bps" % bps


def _tcp_listeners(ports):
    """{port: 进程名}，GetExtendedTcpTable(OWNER_PID_LISTENER)。"""
    import ctypes
    from ctypes import wintypes

    iphlpapi = ctypes.WinDLL("iphlpapi.dll")
    AF_INET, TCP_TABLE_OWNER_PID_LISTENER = 2, 3
    size = wintypes.DWORD(0)
    iphlpapi.GetExtendedTcpTable(None, ctypes.byref(size), False, AF_INET,
                                 TCP_TABLE_OWNER_PID_LISTENER, 0)
    if size.value < 4:
        return {}
    buf = ctypes.create_string_buffer(size.value + 256)
    rc = iphlpapi.GetExtendedTcpTable(buf, ctypes.byref(size), False, AF_INET,
                                      TCP_TABLE_OWNER_PID_LISTENER, 0)
    if rc != 0:
        return {}
    raw = ctypes.string_at(buf, size.value)
    n = struct.unpack("<I", raw[:4])[0]
    want = set(int(p) for p in ports)
    out = {}
    for i in range(n):
        off = 4 + i * 24
        chunk = raw[off:off + 24]
        if len(chunk) < 24:
            break
        _state, _la, lport, _ra, _rp, pid = struct.unpack("<6I", chunk)
        port = ((lport & 0xFF) << 8) | ((lport >> 8) & 0xFF)   # 端口是网络字节序
        if port in want:
            # 体检现在跑在 LanSplice 进程里，它自己监听的那两个端口
            # 归我们所有 —— 按 PID 认，不要靠进程名去猜。
            # （源码方式运行时进程名是 python.exe，光看名字会误报「端口被占」。）
            out[port] = ("LanSplice" if int(pid) == os.getpid()
                         else _proc_name(pid))
    return out


def _proc_name(pid):
    import ctypes
    from ctypes import wintypes

    if not pid:
        return "?"
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    k32 = ctypes.WinDLL("kernel32.dll")
    k32.OpenProcess.restype = wintypes.HANDLE
    k32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    h = k32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, int(pid))
    if not h:
        return "?"
    try:
        size = wintypes.DWORD(1024)
        buf = ctypes.create_unicode_buffer(1024)
        k32.QueryFullProcessImageNameW.argtypes = [
            wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR,
            ctypes.POINTER(wintypes.DWORD)]
        if not k32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size)):
            return "?"
        return os.path.basename(buf.value) or "?"
    finally:
        k32.CloseHandle(h)


def listening_ports(ports=None):
    """{port: 进程名}，只列正在 LISTEN 的。拿不到进程名就给 "?"。

    用途：47820 被占不一定是故障 —— 如果占它的是 LanSplice 本身，那是正常的。
    """
    ports = ports or [LS_TCP_PORT, LS_WEB_PORT]
    out = {}
    if not IS_WIN:
        try:
            txt = subprocess.run(["ss", "-ltnp"], capture_output=True, text=True,
                                 timeout=4).stdout
        except Exception:
            return out
        for line in txt.splitlines():
            for p in ports:
                if (":%d " % p) in line:
                    name = "?"
                    if 'users:(("' in line:
                        name = line.split('users:(("')[1].split('"')[0]
                    out[int(p)] = name
        return out
    ids = ",".join(str(p) for p in ports)
    ps = ("Get-NetTCPConnection -State Listen -LocalPort %s -ErrorAction SilentlyContinue | "
          "ForEach-Object { [pscustomobject]@{ Port=$_.LocalPort; "
          "Name=(Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue).ProcessName } } | "
          "ConvertTo-Json -Compress" % ids)
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
            capture_output=True, text=True, timeout=10,
            creationflags=_NO_WINDOW, encoding="utf-8", errors="replace")
        data = json.loads(r.stdout or "[]")
        if isinstance(data, dict):
            data = [data]
        for d in data:
            out[int(d.get("Port") or 0)] = d.get("Name") or "?"
    except Exception:
        return out
    return out


# ---------------------------------------------------------------- 发现

def discover_lansplice(timeout=1.5):
    """广播找 LanSplice，协议与它自己的发现包一致。"""
    found = {}
    msg = b"L2P-DISCOVER" + str(PROTO_VER).encode()
    socks = []
    for d in list_ipv4():
        try:
            sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sk.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sk.bind((d["ip"], 0))
            sk.setblocking(False)
            socks.append((sk, d["bcast"]))
        except Exception:
            try:
                sk.close()
            except Exception:
                pass
    if not socks:
        return []
    t_end = time.time() + timeout
    try:
        while time.time() < t_end:
            for sk, bcast in socks:
                try:
                    sk.sendto(msg, (bcast, DISCOVERY_PORT))
                except Exception:
                    pass
            time.sleep(0.22)
            for sk, _b in socks:
                while True:
                    try:
                        data, addr = sk.recvfrom(4096)
                    except Exception:
                        break
                    if not data.startswith(b"L2P-OFFER"):
                        continue
                    try:
                        info = json.loads(data[9:].decode("utf-8"))
                    except Exception:
                        continue
                    ip = addr[0]
                    if ip in local_ips():
                        continue
                    found[ip] = {"ip": ip, "name": info.get("name") or ip,
                                 "port": int(info.get("port") or LS_TCP_PORT),
                                 "web": int(info.get("web") or 0)}
    finally:
        for sk, _b in socks:
            try:
                sk.close()
            except Exception:
                pass
    return list(found.values())


def ssdp_scan(timeout=1.2):
    """很轻的 SSDP 探测：能拿到几台设备就算几台，拿不到不影响结论。"""
    names = []
    sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sk.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sk.settimeout(0.35)
    try:
        sk.bind(("", 0))
        req = ("M-SEARCH * HTTP/1.1\r\nHOST: 239.255.255.250:1900\r\n"
               'MAN: "ssdp:discover"\r\nMX: 1\r\nST: ssdp:all\r\n\r\n')
        sk.sendto(req.encode(), ("239.255.255.250", 1900))
        t_end = time.time() + timeout
        while time.time() < t_end:
            try:
                data, addr = sk.recvfrom(4096)
            except Exception:
                continue
            txt = data.decode("utf-8", "replace")
            for line in txt.splitlines():
                if line.lower().startswith("server:"):
                    names.append((addr[0], line.split(":", 1)[1].strip()[:60]))
                    break
    except Exception:
        pass
    finally:
        sk.close()
    return names


def now_text():
    return time.strftime("%Y-%m-%d %H:%M:%S")
