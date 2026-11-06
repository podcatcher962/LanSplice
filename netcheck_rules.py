# -*- coding: utf-8 -*-
"""LanSplice 网络体检规则。

原则：只输出「能动手改的结论」。所有规则都是纯函数（输入证据，输出结论），
方便单测——不需要真的拔网线。

证据结构见 netcheck_scan.py 的 collect()。

文案一律走 link2pc_i18n 的 _t()：结论是体检窗口右侧整栏的内容，英文界面下
如果还吐中文，那半屏英文就等于白做。规则里只留判断逻辑和格式串顺序。
"""
from link2pc_i18n import t as _t

OK = "ok"
WARN = "warn"
ERR = "error"

_ORDER = {ERR: 0, WARN: 1, OK: 2}


def finding(level, title, detail, action=""):
    return {"level": level, "title": title, "detail": detail, "action": action}


def diagnose(ev):
    """返回 [(finding)]，按严重程度排序。"""
    out = []
    for rule in (rule_no_nic, rule_virtual_nic, rule_gateway, rule_internet,
                 rule_lan_empty, rule_port_busy, rule_peer):
        try:
            r = rule(ev)
        except Exception as exc:              # 单条规则出错不能拖垮整次体检
            r = [finding(WARN, _t("d001"), "%s: %s" % (rule.__name__, exc))]
        if not r:
            continue
        out.extend(r if isinstance(r, list) else [r])
    if not out:
        out = [finding(OK, _t("d002"), _t("d003"), "")]
    out.sort(key=lambda f: _ORDER.get(f["level"], 3))
    return out


# ------------------------------------------------------------------ 本机

def rule_no_nic(ev):
    if ev.get("ipv4"):
        return None
    return finding(ERR, _t("d004"), _t("d005"), _t("d006"))


def _looks_virtual(ip):
    """按地址段猜虚拟网卡。只用来决定措辞，不参与任何判断。"""
    return ip.startswith(("172.17.", "192.168.56.", "10.0.2.", "169.254."))


def _join(items):
    return _t("d013").join(items)


def rule_virtual_nic(ev):
    """多块网卡时，广播很可能从虚拟网卡发出去——LanSplice 的头号坑。

    但如果这次体检已经通过广播找到了对端，说明广播没发错地方，
    再提醒「注意广播从哪块出去」只是噪音，所以直接不报。
    """
    rows = ev.get("ipv4") or []
    if len(rows) < 2:
        return None
    peer = (ev.get("peer") or {}).get("ip")
    # 广播找到对端的证据有两份：整次体检的全局列表，和 probe_peer 自己那一次。
    # 任一份里有，就说明广播确实落到了对端，多网卡没有造成影响。
    found = set(p["ip"] for p in (ev.get("lansplice") or []))
    found |= set(p["ip"] for p in ((ev.get("peer") or {}).get("lansplice") or []))
    if peer and peer in found:
        return None
    virt = [r["ip"] for r in rows if _looks_virtual(r["ip"])]
    real = [r["ip"] for r in rows if not _looks_virtual(r["ip"])]

    if virt:
        title = _t("d007") % (len(rows), len(virt))
        detail = _t("d008") % (_join(real) or _t("d012"), _join(virt))
    else:
        title = _t("d009") % len(rows)
        detail = _t("d010") % _join(real)
    return finding(WARN, title, detail, _t("d011"))


def rule_gateway(ev):
    st = ev.get("gateway_stats")
    gw = ev.get("gateway_ip")
    if not st or not gw:
        return None
    loss, jitter, avg = st["loss"], st["jitter"] or 0, st["avg"] or 0
    if loss >= 20:
        return finding(ERR, _t("d014") % loss,
                       _t("d015") % (gw, st["sent"], st["recv"]),
                       _t("d016"))
    if loss >= 3:
        return finding(WARN, _t("d017") % loss,
                       _t("d018") % (gw, avg, jitter),
                       _t("d019"))
    if jitter >= 50:
        return finding(WARN, _t("d020") % jitter,
                       _t("d021") % (avg, jitter),
                       _t("d022"))
    if avg >= 10:
        return finding(WARN, _t("d023") % avg, _t("d024"), _t("d025"))
    return finding(OK, _t("d026"),
                   _t("d027") % (gw, st["recv"], st["sent"], avg, jitter))


def rule_internet(ev):
    st = ev.get("internet_stats")
    if not st:
        return None
    if st["loss"] >= 50:
        return finding(WARN, _t("d028"),
                       _t("d029") % (st["sent"], st["recv"]),
                       _t("d030"))
    if st["loss"] >= 5:
        return finding(WARN, _t("d031") % st["loss"],
                       _t("d032") % (st["avg"] or 0, st["jitter"] or 0),
                       _t("d033"))
    return finding(OK, _t("d034"),
                   _t("d035") % (st["avg"] or 0, st["jitter"] or 0, st["loss"]))


def rule_lan_empty(ev):
    if ev.get("peer"):
        return None
    arp = ev.get("arp") or []
    if not arp:
        return finding(WARN, _t("d036"), _t("d037"), _t("d038"))
    if len(arp) == 1:
        return finding(WARN, _t("d039"), _t("d040"), _t("d041"))
    return finding(OK, _t("d042") % len(arp), _t("d043"))


def rule_port_busy(ev):
    listen = ev.get("listening") or {}
    mine, bad = {}, {}
    for p, name in listen.items():
        low = (name or "").lower()
        if "lansplice" in low or "link2pc" in low:
            mine[p] = name
        else:
            bad[p] = name
    if bad:
        sep = _t("d013")
        desc = sep.join(_t("d045") % (p, n) for p, n in sorted(bad.items()))
        return finding(ERR, _t("d044") % desc, _t("d046"), _t("d047"))
    if mine:
        return finding(OK, _t("d048"),
                       _t("d049") % _t("d013").join(sorted(set(mine.values()))))
    return None


# ------------------------------------------------------------------ 对端

def rule_peer(ev):
    p = ev.get("peer") or {}
    ip = p.get("ip")
    if not ip:
        return []
    # 对端填成本机地址：能连上、能 ping 通，但结论毫无意义（自己连自己），
    # 而且广播永远「发现不到对端」，会顺手多出一条假警告。
    local = set(r["ip"] for r in (ev.get("ipv4") or []))
    if ip in local:
        return [finding(WARN, _t("d050") % ip, _t("d051") % ip, _t("d052"))]
    st = p.get("stats") or {}
    ports = p.get("ports") or []
    open_ports = [x for x in ports if x[2]]
    ls_open = any(x[0] == 47820 and x[2] for x in ports)
    web_open = any(x[0] == 47822 and x[2] for x in ports)
    ping_ok = bool(st.get("recv"))
    # 端口比 ping 可信：Windows 防火墙默认挡入站 ICMP，却会放行应用自己开的端口。
    # 只要有一个 TCP 端口连上了，对端就是活着的 —— 这时候再报「ping 都不通」
    # 就是自相矛盾，用户会以为两台机器连不上，实际上文件已经能传了。
    alive = ping_ok or bool(open_ports)
    out = []

    if not alive:
        out.append(finding(
            ERR, _t("d053") % ip,
            _t("d054") % (st.get("sent") or 0),
            _t("d055")))
        return out

    if ls_open:
        note = "" if ping_ok else _t("d058")
        out.append(finding(OK, _t("d056") % ip, _t("d057") + note, ""))
    elif web_open:
        out.append(finding(WARN, _t("d059"), _t("d060"), _t("d061")))
    else:
        out.append(finding(ERR, _t("d062"), _t("d063"), _t("d064")))

    if ping_ok and not ls_open and not web_open:
        out.append(finding(WARN, _t("d065"), _t("d066"), _t("d067")))

    if ls_open and not (p.get("lansplice") or []):
        out.append(finding(WARN, _t("d068"), _t("d069"), _t("d070")))
    return out


def summary(findings):
    """给界面顶部用的一句话。"""
    if not findings:
        return OK, _t("d002")
    bad = [f for f in findings if f["level"] in (ERR, WARN)]
    if not bad:
        return OK, findings[0]["title"]
    return bad[0]["level"], bad[0]["title"]


def counts(findings):
    c = {ERR: 0, WARN: 0, OK: 0}
    for f in findings:
        c[f["level"]] = c.get(f["level"], 0) + 1
    return c
