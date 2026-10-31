# -*- coding: utf-8 -*-
"""
手机网页端
=========
在电脑上开一个极简 HTTP 服务，手机用浏览器扫码就能收发文件 ——
不用装 App、不用数据线、不用登任何账号。

安全边界（这一层比文件传输更需要注意）
--------------------------------------
1. 只接受内网来源。公网 IP 直接 403，连页面都拿不到。
2. 口令（token）必填，24 位随机十六进制，走 URL 参数或 Cookie。
   没口令的请求一律 401，页面里不透露目录内容。
3. 上传只能落在接收目录的顶层，文件名经过清洗（去路径、去保留名），
   重名自动改成「xxx (2).ext」，绝不覆盖。
4. 不解析 multipart、不执行任何东西、不跟随符号链接。
5. 服务只在你点开「手机传文件」时启动，关窗即停 —— 不是常驻监听。
"""

import os
import re
import hmac
import json
import time
import html
import socket
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs, quote, unquote

import link2pc_core as L

WEB_PORT = 47822
MAX_UP = 8 * 1024 * 1024 * 1024        # 单文件上限 8 GB，够传视频
_BAD_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def safe_name(name):
    """
    把浏览器给的文件名洗成安全的本地文件名。

    浏览器可能给 "C:\\Users\\a\\x.jpg" 或 "../../x"，甚至带控制字符。
    这里只留最后一段、去掉非法字符、拒绝 Windows 保留名。
    """
    name = (name or "").replace("\\", "/").split("/")[-1]
    name = _BAD_CHARS.sub("_", name).strip(" .")
    if not name:
        name = "upload"
    stem = name.split(".")[0].upper()
    if stem in L._WIN_RESERVED:
        name = "_" + name
    if len(name) > 180:
        base, ext = os.path.splitext(name)
        name = base[:170] + ext
    return name


PAGE = """<!doctype html>
<html lang="zh"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="color-scheme" content="light">
<title>LanSplice · 手机传文件</title>
<style>
  :root{--bg:#eceff1;--card:#fff;--line:#d5dde2;--text:#1f2a30;--sub:#5f7079;
        --green:#2e7d32;--blue:#1976d2;--purple:#6a1b9a}
  *{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
  /* 手机屏以「臂长距离」看，字要比桌面大一档：正文 19px、次要 15px。
     viewport 里不写最大缩放倍数 —— 写了就没法双指放大，是拿无障碍换整齐。 */
  html{-webkit-text-size-adjust:100%;text-size-adjust:100%}
  body{margin:0;padding:18px 16px 48px;background:var(--bg);color:var(--text);
       font:19px/1.6 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif}
  h1{font-size:26px;margin:0 0 4px;letter-spacing:.5px}
  .sub{color:var(--sub);font-size:15px;margin:0 0 18px}
  .card{background:var(--card);border:1px solid var(--line);border-radius:14px;
        padding:16px;margin-bottom:16px}
  h2{font-size:16px;color:var(--sub);margin:0 0 12px;font-weight:600}
  button{font:inherit;font-size:19px;border:0;border-radius:12px;padding:16px 18px;
         color:#fff;background:var(--purple);width:100%;font-weight:600;
         min-height:56px}
  button:active{opacity:.85}
  button.gray{background:#607d8b;margin-top:10px}
  #drop{border:2px dashed var(--line);border-radius:12px;padding:30px 12px;
        text-align:center;color:var(--sub);font-size:16px;margin-top:12px}
  #drop.hot{border-color:var(--purple);color:var(--purple);background:#f7f2fb}
  /* 一行放不下「长文件名 + 大小 + 下载」：文件名独占第一行（最多两行），
     大小和下载排在第二行。字放大之后尤其需要这样，否则名字只剩七八个字。 */
  .item{display:grid;grid-template-columns:1fr auto;align-items:center;
        column-gap:12px;row-gap:4px;padding:13px 0;
        border-bottom:1px solid #eef2f4;font-size:17px}
  .item:last-child{border-bottom:0}
  .item .n{grid-column:1/-1;min-width:0;overflow-wrap:anywhere;
           display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;
           overflow:hidden;line-height:1.45}
  .item .s{grid-column:1;color:var(--sub);font-size:15px}
  /* 下载是个要点的东西，按 44px 最小触控区给，别做成一串小字 */
  .item a{grid-column:2;grid-row:2;color:var(--blue);text-decoration:none;
          font-size:16px;display:inline-flex;align-items:center;
          justify-content:center;min-height:44px;padding:0 14px;
          border-radius:10px;background:#e8f1fb}
  .task{margin-top:12px;font-size:16px}
  .task .bar{height:8px;background:#e3e9ec;border-radius:4px;overflow:hidden;
             margin-top:6px}
  .task .bar i{display:block;height:100%;width:0;background:var(--green);
               transition:width .2s}
  .err{color:#c62828}
  /* 极窄屏（老机型 320~360）再收一点，避免「选择文件发送」被挤断行 */
  @media (max-width:360px){
    body{font-size:18px;padding:16px 12px 40px}
    button{font-size:18px;padding:15px 12px}
    .item{font-size:16px}
  }
</style></head>
<body>
<h1>LanSplice</h1>
<p class="sub">手机 ↔ 电脑 · 同一个路由器 · 不经过任何服务器</p>

<div class="card">
  <h2>发到电脑（接收目录）</h2>
  <button id="pick">选择文件发送</button>
  <input id="f" type="file" multiple hidden>
  <div id="drop">也可以把文件拖到这里</div>
  <div id="tasks"></div>
</div>

<div class="card">
  <h2>电脑上的文件</h2>
  <div id="files" class="sub">加载中…</div>
  <button id="reload" class="gray">刷新列表</button>
</div>

<script>
var TOKEN = "__TOKEN__";
var qs = new URLSearchParams(location.search);
if (qs.get("t")) { TOKEN = qs.get("t"); sessionStorage.setItem("ls_t", TOKEN); }
else if (sessionStorage.getItem("ls_t")) { TOKEN = sessionStorage.getItem("ls_t"); }

function api(p){ return p + (p.indexOf("?") >= 0 ? "&" : "?") + "t=" + encodeURIComponent(TOKEN); }
function fmt(n){
  if (n < 1024) return n + " B";
  if (n < 1048576) return (n/1024).toFixed(1) + " KB";
  if (n < 1073741824) return (n/1048576).toFixed(1) + " MB";
  return (n/1073741824).toFixed(2) + " GB";
}

var tasks = document.getElementById("tasks");
function addTask(name){
  var d = document.createElement("div");
  d.className = "task";
  d.innerHTML = '<div class="tname"></div><div class="bar"><i></i></div>';
  d.querySelector(".tname").textContent = name + " · 等待";
  tasks.appendChild(d);
  return d;
}
function setTask(d, text, pct, bad){
  d.querySelector(".tname").textContent = text;
  d.querySelector(".tname").className = "tname" + (bad ? " err" : "");
  if (typeof pct === "number") d.querySelector(".bar i").style.width = pct + "%";
}

function upload(file){
  var d = addTask(file.name);
  var x = new XMLHttpRequest();
  x.open("POST", api("/up?name=" + encodeURIComponent(file.name)));
  x.setRequestHeader("Content-Type", "application/octet-stream");
  x.upload.onprogress = function(e){
    if (e.lengthComputable){
      var p = Math.round(e.loaded * 100 / e.total);
      setTask(d, file.name + " · " + p + "%  " + fmt(e.loaded) + " / " + fmt(e.total), p);
    }
  };
  x.onload = function(){
    if (x.status === 200){
      setTask(d, file.name + " · 已保存", 100);
      loadFiles();
    } else {
      setTask(d, file.name + " · 失败：" + (x.responseText || x.status), 100, true);
    }
  };
  x.onerror = function(){ setTask(d, file.name + " · 网络断了", 0, true); };
  x.send(file);
}

document.getElementById("pick").onclick = function(){
  document.getElementById("f").click();
};
document.getElementById("f").onchange = function(e){
  for (var i = 0; i < e.target.files.length; i++) upload(e.target.files[i]);
  e.target.value = "";
};
var drop = document.getElementById("drop");
["dragenter","dragover"].forEach(function(t){
  drop.addEventListener(t, function(e){ e.preventDefault(); drop.classList.add("hot"); });
});
["dragleave","drop"].forEach(function(t){
  drop.addEventListener(t, function(e){ e.preventDefault(); drop.classList.remove("hot"); });
});
drop.addEventListener("drop", function(e){
  for (var i = 0; i < e.dataTransfer.files.length; i++) upload(e.dataTransfer.files[i]);
});

function loadFiles(){
  var box = document.getElementById("files");
  fetch(api("/api/list")).then(function(r){ return r.json(); }).then(function(js){
    if (!js.ok){ box.textContent = "口令不对，请重新扫码"; return; }
    if (!js.items.length){ box.textContent = "接收目录还是空的"; return; }
    box.innerHTML = "";
    box.className = "";
    js.items.forEach(function(it){
      var row = document.createElement("div");
      row.className = "item";
      var n = document.createElement("div");
      n.className = "n";
      n.textContent = it.name;
      var s = document.createElement("div");
      s.className = "s";
      s.textContent = it.dir ? "文件夹" : fmt(it.size);
      row.appendChild(n); row.appendChild(s);
      if (!it.dir){
        var a = document.createElement("a");
        a.href = api("/dl?name=" + encodeURIComponent(it.name));
        a.textContent = "下载";
        row.appendChild(a);
      }
      box.appendChild(row);
    });
  }).catch(function(){ box.textContent = "读取失败，检查是否还在同一网络"; });
}
document.getElementById("reload").onclick = loadFiles;
loadFiles();
</script>
</body></html>
"""


class _Handler(BaseHTTPRequestHandler):
    server_version = "LanSpliceWeb/1.0"
    sys_version = ""

    # 交给 WebShare 填
    root_dir = ""
    token = ""

    def log_message(self, fmt, *a):
        # 默认实现往 stderr 打，打包后没有控制台会报错，这里吞掉
        pass

    # ---------------------------------------------------------- 工具
    def _client_ok(self):
        ip = self.client_address[0]
        return L.is_private_ipv4(ip) or ip in ("::1", "127.0.0.1")

    def _token_ok(self, q):
        t = (q.get("t") or [""])[0]
        if not t:
            ck = self.headers.get("Cookie") or ""
            m = re.search(r"ls_t=([0-9a-f]{8,})", ck)
            if m:
                t = m.group(1)
        return bool(t) and hmac.compare_digest(t, self.token)

    def _send(self, code, body=b"", ctype="text/plain; charset=utf-8",
              extra=None):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        for k, v in (extra or {}):
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            try:
                self.wfile.write(body)
            except Exception:
                pass

    # ---------------------------------------------------------- GET
    def do_GET(self):
        if not self._client_ok():
            self._send(403, "只允许局域网访问")
            return
        u = urlparse(self.path)
        q = parse_qs(u.query)

        if u.path in ("/", "/index.html"):
            if not self._token_ok(q):
                self._send(401, _NEED_TOKEN, "text/html; charset=utf-8")
                return
            body = PAGE.replace("__TOKEN__", self.token)
            self._send(200, body, "text/html; charset=utf-8",
                       [("Set-Cookie", "ls_t=%s; Path=/; HttpOnly; SameSite=Lax"
                         % self.token)])
            return

        if u.path == "/api/list":
            if not self._token_ok(q):
                self._send(401, json.dumps({"ok": False}), "application/json")
                return
            self._send(200, json.dumps({"ok": True, "items": self._listing()}),
                       "application/json; charset=utf-8")
            return

        if u.path == "/dl":
            if not self._token_ok(q):
                self._send(401, "口令不对")
                return
            name = safe_name((q.get("name") or [""])[0])
            p = os.path.join(self.root_dir, name)
            if not os.path.isfile(p):
                self._send(404, "没有这个文件")
                return
            try:
                size = os.path.getsize(p)
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Length", str(size))
                self.send_header(
                    "Content-Disposition",
                    "attachment; filename*=UTF-8''%s" % quote(name))
                self.end_headers()
                with open(p, "rb") as f:
                    while True:
                        b = f.read(256 * 1024)
                        if not b:
                            break
                        self.wfile.write(b)
            except Exception:
                pass
            return

        self._send(404, "not found")

    # ---------------------------------------------------------- POST
    def do_POST(self):
        if not self._client_ok():
            self._send(403, "只允许局域网访问")
            return
        u = urlparse(self.path)
        q = parse_qs(u.query)
        if u.path != "/up":
            self._send(404, "not found")
            return
        if not self._token_ok(q):
            self._send(401, "口令不对")
            return

        name = safe_name((q.get("name") or ["upload"])[0])
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except Exception:
            n = 0
        if n <= 0:
            self._send(400, "空文件")
            return
        if n > MAX_UP:
            self._send(413, "文件太大")
            return

        free = L._free_space(self.root_dir)
        if free is not None and n > free - 50 * 1024 * 1024:
            self._send(507, "接收盘空间不足")
            return

        target = L.unique_path(os.path.join(self.root_dir, name))
        tmp = target + ".l2pweb"
        got = 0
        try:
            with open(tmp, "wb") as f:
                while got < n:
                    b = self.rfile.read(min(256 * 1024, n - got))
                    if not b:
                        break
                    f.write(b)
                    got += len(b)
            if got != n:
                raise IOError("字节数不符")
            os.replace(tmp, target)
            self._send(200, "ok")
        except Exception as e:
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except Exception:
                pass
            self._send(500, "写入失败：%s" % e)

    # ---------------------------------------------------------- 列表
    def _listing(self):
        out = []
        try:
            names = os.listdir(self.root_dir)
        except Exception:
            return out
        for name in names:
            if name.startswith(".l2p") or name.startswith("."):
                continue
            p = os.path.join(self.root_dir, name)
            try:
                if os.path.isdir(p):
                    out.append({"name": name, "dir": True, "size": 0,
                                "mtime": int(os.path.getmtime(p))})
                elif os.path.isfile(p):
                    out.append({"name": name, "dir": False,
                                "size": os.path.getsize(p),
                                "mtime": int(os.path.getmtime(p))})
            except Exception:
                pass
        out.sort(key=lambda x: (-x["mtime"], x["name"].lower()))
        return out[:200]


_NEED_TOKEN = """<!doctype html><html lang=zh><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<body style="font:18px/1.65 -apple-system,'PingFang SC','Microsoft YaHei',sans-serif;
background:#eceff1;color:#1f2a30;padding:40px 22px">
<h2 style="font-size:22px">需要扫码进入</h2>
<p style="color:#5f7079;font-size:16px">这个页面只对拿到口令的人开放。<br>
请用电脑上的 LanSplice 打开「手机传文件」，重新扫一次二维码。</p>
</body></html>"""


class WebShare:
    """手机网页端的生命周期。GUI 只在用户点开时才启动它。"""

    def __init__(self, root_dir, token=None, port=WEB_PORT, log=None):
        self.root_dir = root_dir
        self.token = token or secrets.token_hex(12)
        self.port = int(port)
        self.log = log or (lambda s: None)
        self._srv = None
        self._thread = None
        self.error = None
        self.running = False

    def start(self):
        try:
            os.makedirs(self.root_dir, exist_ok=True)
            cls = type("_H", (_Handler,), {"root_dir": self.root_dir,
                                           "token": self.token})
            srv = ThreadingHTTPServer(("0.0.0.0", self.port), cls)
            srv.daemon_threads = True
            self._srv = srv
        except Exception as e:
            self.error = str(e)
            return False
        self._thread = threading.Thread(target=self._serve, daemon=True,
                                        name="LanSplice-Web")
        self._thread.start()
        self.running = True
        return True

    def _serve(self):
        try:
            self._srv.serve_forever(poll_interval=0.4)
        except Exception:
            pass
        self.running = False

    def stop(self):
        self.running = False
        try:
            if self._srv:
                self._srv.shutdown()
                self._srv.server_close()
        except Exception:
            pass
        self._srv = None

    def url(self, ip=None):
        ip = ip or L.local_ip() or "127.0.0.1"
        return "http://%s:%d/?t=%s" % (ip, self.port, self.token)
