# -*- coding: utf-8 -*-
"""把一次体检渲染成单文件 HTML：发给别人看，或者留档对比。

不引外部资源（字体、CSS、图片都不外链），断网也能打开。

报告跟着界面语言走：英文界面导出的报告整篇英文，连 <html lang> 都换掉 ——
中文报告发给英文用户，等于让人对着乱码猜。
"""
import html

import link2pc_core as LC
import netcheck_core as C
import netcheck_rules as A
import netcheck_scan as S
from link2pc_i18n import is_en
from link2pc_i18n import t as _t

_LEVEL_COLOR = {A.ERR: "#c0392b", A.WARN: "#c77700", A.OK: "#1f8a55"}

# 端口名不再从 netcheck_core.COMMON_PORTS 直接取：那份是模块级常量，
# 在 import 那一刻就把语言定死了。这里按端口号换文案，导出时才求值。
_PORT_KEYS = {445: "d120", 5000: "d121", 8080: "d122", 9100: "d123",
              C.LS_TCP_PORT: "d124", C.LS_WEB_PORT: "d125"}


def _level_text(lvl):
    return _t({A.ERR: "d080", A.WARN: "d081", A.OK: "d082"}.get(lvl, "d083"))


def _port_label(port, fallback):
    key = _PORT_KEYS.get(port)
    return _t(key) if key else fallback


def render_html(ev):
    esc = html.escape
    findings = ev.get("findings") or []
    lvl, line = A.summary(findings)
    c = A.counts(findings)
    hosts = S.hosts(ev)

    def rows(items, cols):
        if not items:
            return '<tr><td colspan="%d" class="empty">%s</td></tr>' % (
                len(cols), esc(_t("d083")))
        out = []
        for it in items:
            out.append("<tr>" + "".join("<td>%s</td>" % esc(str(it.get(k, "") or "—"))
                                        for k in cols) + "</tr>")
        return "".join(out)

    nic_rows = [{"ip": d["ip"], "prefix": "/%d" % d["prefix"],
                 "bcast": d["bcast"]} for d in ev.get("ipv4") or []]
    kind_txt = {"gateway": _t("g550"), "pc": _t("g551"),
                "phone": _t("g552"), "other": _t("g553")}
    dev_rows = [{"ip": d["ip"],
                 "kind": kind_txt.get(d["kind"], _t("g553")),
                 "name": d["name"] or "—", "mac": d["mac"] or "—",
                 "note": d["note"] or "—"} for d in hosts]

    def stat_block(st, label):
        if not st:
            return '<p class="muted">%s</p>' % esc(_t("d084"))
        return (
            '<div class="stats">'
            '<div><b>%s</b><span>%s</span></div>'
            '<div><b>%s ms</b><span>%s</span></div>'
            '<div><b>%s ms</b><span>%s</span></div>'
            '<div><b>%s%%</b><span>%s</span></div>'
            '</div>'
            '<p class="muted">%s</p>'
            % (st.get("avg") if st.get("avg") is not None else "—",
               esc(_t("d085")),
               "%s / %s" % (st.get("min", "—"), st.get("max", "—")),
               esc(_t("d086")),
               st.get("jitter", "—"), esc(_t("d087")),
               st.get("loss", "—"), esc(_t("d088")),
               esc(_t("d089") % (", ".join(str(x) for x in (st.get("samples") or []))
                                 or "—"))))

    findings_html = "".join(
        '<div class="finding %s"><div class="fh"><span class="badge" style="background:%s">%s</span>'
        '<b>%s</b></div><p>%s</p>%s</div>'
        % (f["level"], _LEVEL_COLOR.get(f["level"], "#666"),
           esc(_level_text(f["level"])), esc(f["title"]), esc(f["detail"]),
           ('<p class="act">→ %s</p>' % esc(f["action"])) if f.get("action") else "")
        for f in findings)

    peer = ev.get("peer") or {}
    peer_html = ""
    if peer.get("ip"):
        ports = peer.get("ports") or []
        open_ports = [p for p in ports if p[2]]
        peer_html = (
            "<h2>%s</h2>" % esc(_t("d090") % peer["ip"]) +
            stat_block(peer.get("stats"), "ICMP") +
            "<h3>%s</h3><p>" % esc(_t("d091"))
            + (esc(_t("d013")).join(esc(_t("d092") % (p[0], _port_label(p[0], p[1])))
                                    for p in open_ports)
               if open_ports else esc(_t("d093")))
            + "</p>")

    return """<!DOCTYPE html>
<html lang="%(lang)s"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%(title)s</title>
<style>
:root{--bg:#f6f7f9;--card:#fff;--ink:#1d2329;--sub:#5d6a75;--line:#e3e7eb}
@media (prefers-color-scheme:dark){:root{--bg:#14181c;--card:#1c2229;--ink:#e8edf2;--sub:#9aa8b4;--line:#2b333b}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
 font:15px/1.65 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}
.wrap{max-width:880px;margin:0 auto;padding:28px 20px 60px}
h1{font-size:24px;margin:0 0 4px}
h2{font-size:17px;margin:28px 0 10px;padding-bottom:6px;border-bottom:1px solid var(--line)}
h3{font-size:14px;color:var(--sub);margin:16px 0 6px;font-weight:600}
.head{display:flex;justify-content:space-between;align-items:flex-end;gap:12px;flex-wrap:wrap}
.verdict{background:var(--card);border:1px solid var(--line);border-radius:10px;
 padding:14px 16px;margin:16px 0 6px;border-left:4px solid %(vcolor)s}
.verdict b{font-size:17px}
.muted{color:var(--sub);font-size:13px}
.stats{display:flex;gap:10px;flex-wrap:wrap;margin:8px 0}
.stats div{background:var(--card);border:1px solid var(--line);border-radius:10px;
 padding:10px 14px;min-width:120px}
.stats b{display:block;font-size:19px}
.stats span{color:var(--sub);font-size:12px}
table{width:100%%;border-collapse:collapse;background:var(--card);
 border:1px solid var(--line);border-radius:10px;overflow:hidden;font-size:14px}
th,td{padding:9px 12px;text-align:left;border-bottom:1px solid var(--line)}
th{background:rgba(127,127,127,.06);color:var(--sub);font-weight:600;font-size:13px}
tr:last-child td{border-bottom:0}
td.empty{color:var(--sub);text-align:center}
.finding{background:var(--card);border:1px solid var(--line);border-radius:10px;
 padding:12px 14px;margin:8px 0}
.finding p{margin:6px 0 0;color:var(--sub);font-size:14px}
.finding .act{color:var(--ink)}
.fh{display:flex;align-items:center;gap:8px}
.badge{color:#fff;font-size:12px;padding:1px 7px;border-radius:4px}
footer{margin-top:34px;color:var(--sub);font-size:12px;border-top:1px solid var(--line);padding-top:12px}
</style></head><body><div class="wrap">
<div class="head"><div><h1>%(h1)s</h1>
<p class="muted">%(time_line)s</p></div>
<p class="muted">%(counts)s</p></div>

<div class="verdict" style="border-left-color:%(vcolor)s">
<b>%(verdict)s</b></div>

<h2>%(h_findings)s</h2>
%(findings)s

<h2>%(h_local)s</h2>
<table><tr><th>%(th_ip)s</th><th>%(th_mask)s</th><th>%(th_bcast)s</th></tr>%(nics)s</table>
<h3>%(h_link)s</h3><table><tr><th>%(th_nic)s</th><th>%(th_speed)s</th><th>%(th_type)s</th></tr>%(links)s</table>

<h2>%(h_wan)s</h2>
<h3>%(gw_head)s</h3>%(gwstats)s
<h3>%(net_head)s</h3>%(netstats)s

<h2>%(h_lan)s</h2>
<table><tr><th>%(th_ip)s</th><th>%(th_type)s</th><th>%(th_name)s</th><th>MAC</th><th>%(th_src)s</th></tr>%(devs)s</table>

%(peer)s

<footer>%(footer)s</footer>
</div></body></html>""" % {
        "lang": "en" if is_en() else "zh-CN",
        "title": esc(_t("d094") % (ev.get("finished") or C.now_text())),
        "h1": esc(_t("d095")),
        "time_line": esc(_t("d096") % (ev.get("finished") or C.now_text(), _secs(ev))),
        "counts": esc(_t("d097") % (c.get(A.ERR, 0), c.get(A.WARN, 0), c.get(A.OK, 0))),
        "verdict": esc(line),
        "vcolor": _LEVEL_COLOR.get(lvl, "#666"),
        "h_findings": esc(_t("g535")),
        "findings": findings_html,
        "h_local": esc(_t("g034")),
        "th_ip": esc(_t("g547")),
        "th_mask": esc(_t("d099")),
        "th_bcast": esc(_t("d100")),
        "nics": rows(nic_rows, ["ip", "prefix", "bcast"]),
        "h_link": esc(_t("d101")),
        "th_nic": esc(_t("d102")),
        "th_speed": esc(_t("d103")),
        "th_type": esc(_t("g548")),
        "links": "".join("<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            esc(k), esc(v[0]), esc(_t("g574") if v[1] else _t("g575")))
            for k, v in (ev.get("links") or {}).items()) or
            '<tr><td colspan="3" class="empty">%s</td></tr>' % esc(_t("d083")),
        "h_wan": esc(_t("d105")),
        "gw_head": esc(_t("d106") % (ev.get("gateway_ip") or "—")),
        "gwstats": stat_block(ev.get("gateway_stats"), "ICMP"),
        "net_head": esc(_t("d107") % S.INTERNET_TARGET),
        "netstats": stat_block(ev.get("internet_stats"), "ICMP"),
        "h_lan": esc(_t("g534")),
        "th_name": esc(_t("d109")),
        "th_src": esc(_t("d110")),
        "devs": rows(dev_rows, ["ip", "kind", "name", "mac", "note"]),
        "peer": peer_html,
        "footer": esc(_t("d113") % LC.APP_VER),
    }


def _secs(ev):
    try:
        import datetime
        a = datetime.datetime.strptime(ev["started"], "%Y-%m-%d %H:%M:%S")
        b = datetime.datetime.strptime(ev["finished"], "%Y-%m-%d %H:%M:%S")
        return max(1, int((b - a).total_seconds()))
    except Exception:
        return "—"


def save(ev, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write(render_html(ev))
    return path
