# -*- coding: utf-8 -*-
"""把探测结果攒成一份证据，交给诊断规则。

界面和命令行都调 collect()，保证两边看到的东西一模一样。
"""
import time
from concurrent.futures import ThreadPoolExecutor

import netcheck_core as C
import netcheck_rules as A
from link2pc_i18n import t as _t

INTERNET_TARGET = "223.5.5.5"      # 阿里 DNS，国内可达，不依赖域名解析
PEER_PING_COUNT = 6
GATEWAY_PING_COUNT = 6


def collect(peer_ip=None, progress=None, deep=True):
    """跑一次完整体检，返回 ev（含 findings）。

    各项互不依赖，全部并行跑：总时长由最慢的那项决定（约 2~3 秒），
    而不是加起来十几秒 —— 体检工具让人等十秒，没人会用第二次。
    progress(msg) 用来更新界面上那行进度文字。
    """
    def step(msg):
        if progress:
            try:
                progress(msg)
            except Exception:
                pass

    ev = {"started": time.strftime("%Y-%m-%d %H:%M:%S"), "peer": None}

    step(_t("d071"))
    ev["ipv4"] = C.list_ipv4()
    ev["gateways"] = C.gateways()
    main = ev["ipv4"][0] if ev["ipv4"] else None
    ev["main"] = main
    ev["gateway_ip"] = ev["gateways"].get(main["index"]) if main else None

    step(_t("d072"))
    with ThreadPoolExecutor(max_workers=6) as pool:
        f_arp = pool.submit(C.arp_table)
        f_ssdp = pool.submit(C.ssdp_scan, 1.1) if deep else None
        f_ls = pool.submit(C.discover_lansplice, 1.5)
        f_snap = pool.submit(C.win_snapshot)
        f_gw = (pool.submit(C.icmp_stats, ev["gateway_ip"], GATEWAY_PING_COUNT)
                if ev["gateway_ip"] else None)
        f_net = pool.submit(C.icmp_stats, INTERNET_TARGET, 5)
        f_peer = pool.submit(probe_peer, peer_ip) if peer_ip else None

        ev["arp"] = f_arp.result()
        ev["ssdp"] = f_ssdp.result() if f_ssdp else []
        ev["lansplice"] = f_ls.result()
        snap = f_snap.result()
        ev["links"] = snap.get("links") or {}
        ev["listening"] = snap.get("listening") or {}
        ev["gateway_stats"] = f_gw.result() if f_gw else None
        ev["internet_stats"] = f_net.result()
        if f_peer:
            ev["peer"] = f_peer.result()

    step(_t("d073"))
    ev["findings"] = A.diagnose(ev)
    ev["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
    return ev


def probe_peer(ip):
    ports = C.probe_ports(ip, C.COMMON_PORTS)
    return {
        "ip": ip,
        "stats": C.icmp_stats(ip, PEER_PING_COUNT),
        "ports": ports,
        "lansplice": [p for p in C.discover_lansplice(1.2) if p["ip"] == ip],
    }


def hosts(ev):
    """把 ARP / SSDP / LanSplice 三路信息按 IP 合并成设备列表。

    返回 [{ip, mac, kind, name, note}]，kind: gateway / pc / phone / other
    """
    rows = {}
    gw = ev.get("gateway_ip")
    for a in ev.get("arp") or []:
        rows[a["ip"]] = {"ip": a["ip"], "mac": a.get("mac", ""), "kind": "other",
                         "name": "", "note": _t("d074")}
    for ip, server in ev.get("ssdp") or []:
        d = rows.setdefault(ip, {"ip": ip, "mac": "", "kind": "other",
                                 "name": "", "note": ""})
        if not d["name"]:
            d["name"] = _model_from_server(server)
            d["note"] = "SSDP"
    for p in ev.get("lansplice") or []:
        d = rows.setdefault(p["ip"], {"ip": p["ip"], "mac": "", "kind": "pc",
                                      "name": "", "note": ""})
        d["kind"] = "pc"
        d["name"] = p.get("name") or d["name"]
        d["note"] = _t("d075")
    for d in rows.values():
        if gw and d["ip"] == gw:
            d["kind"] = "gateway"
            # 名字留在空里：「类型」那列已经写着「路由器」了，再把它当名字填一遍，
            # 表格里就会是「路由器 | 路由器」。有 SSDP 型号时 d["name"] 早就有了。
    order = {"gateway": 0, "pc": 1, "phone": 2, "other": 3}
    return sorted(rows.values(), key=lambda d: (order.get(d["kind"], 9), d["ip"]))


def _model_from_server(txt):
    """从 SSDP 的 SERVER 头里抠一个像人话的型号。

    'vxWorks/5.5 UPnP/1.0 TL-XDR3010易展版/8.0' → 'TL-XDR3010易展版'
    """
    if not txt:
        return ""
    parts = [p for p in txt.split() if p]
    for p in parts:
        low = p.lower()
        if low.startswith(("upnp", "vxworks", "linux", "windows", "darwin")):
            continue
        if "/" in p:
            p = p.rsplit("/", 1)[0]
        if len(p) >= 2:
            return p[:40]
    return ""
