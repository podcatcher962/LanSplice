# 在 Linux / 信创系统上用 LanSplice

> 统信 UOS、银河麒麟 V10、深度 Deepin、Ubuntu、Debian、CentOS、openEuler 都适用。
> 飞腾 / 鲲鹏（ARM64）、海光 / 兆芯（x86_64）、龙芯（LoongArch）也一样 ——
> 协议是字节级的，跟 CPU 架构无关。

## 这一版是什么形态

**只有命令行，没有窗口。** 能收、能发、能扫设备，但要在终端里敲命令。
图形界面排在后面（见文末「后续」）。

命令和 Windows 版完全一样，因为就是同一份代码。

---

## 一、安装

把仓库里的这些文件拷到目标机器（U 盘、内网共享都行）：

```
install.sh
link2pc_core.py   link2pc_cli.py   link2pc_paths.py
link2pc_history.py link2pc_i18n.py
link2pc_web.py    link2pc_gui.py   link2pc_tray.py
app.ico  README.md  LICENSE
```

然后：

```sh
sudo sh install.sh
```

脚本会做四件事：检查 Python 版本（要 3.7+）、装 `python3-cryptography`、
把文件放到 `/opt/lansplice`、生成 `/usr/local/bin/lansplice`。

卸载：`sudo sh install.sh --uninstall`（配置和历史不会删）。

### 离线环境

信创机器大多是物理隔离内网，`pip` 根本连不出去。这时**不要**用 pip：

```sh
# 检查系统是否自带
python3 -c "import cryptography; print(cryptography.__version__)"
```

UOS 20 和麒麟 V10 都预装了这个包（`python3-cryptography`）。万一没有，
从系统安装光盘或内网源装同一个包，别从 PyPI 拉。

实在只有 wheel 文件时：

```sh
pip3 install --no-index --find-links . cryptography-*.whl
```

### 为什么不是单文件 exe 那样的一坨

麒麟默认开 SELinux。PyInstaller 打的单文件程序运行时要把自己解包到 `/tmp`，
这一步会被策略拦下来，表现是「双击没反应」或者一句很含糊的权限错误。
目录版没有解包动作，也就没这个问题；升级时只换几个 `.py` 文件，几十 KB。

---

## 二、第一步：对齐配对码

配对码是两台机器之间的**共享密钥**，两边必须一样。哪边先有都行。

```sh
lansplice serve
```

第一次跑会看到：

```
==========================================================
LanSplice 1.7.0 · 接收端
  监听 192.168.1.30:47820
接收目录 /home/lanlan/Downloads/LanSplice
配对码 K7QM-3XPD-R9TB-WVZE（对端 send 时用 --code 传这个）
==========================================================
本机原来没有配对码，已生成并保存：K7QM-3XPD-R9TB-WVZE（对端填这个）
等待连接…按 Ctrl+C 结束
```

把这一串配对码填到 Windows 那台上：**文件 → 输入配对码**，粘进去即可。
之后两台就长期认得彼此了。

反过来也行：Windows 上「文件 → 显示配对码」拿到码，在 Linux 上这样启动：

```sh
lansplice serve --code K7QM-3XPD-R9TB-WVZE
```

---

## 三、三种用法

### 1. 当接收端（最常用）

```sh
lansplice serve
```

| 参数 | 作用 |
|---|---|
| `--root 目录` | 收到的文件放哪儿，默认 `~/Downloads/LanSplice` |
| `--port 端口` | 换监听端口，默认 47820 |
| `--code 配对码` | 临时指定配对码，不写进配置 |
| `--once` | 收完一批就退出（脚本、自测用；一个都没收到返回 1） |
| `--timeout 秒` | 最多等多久，0 表示一直等 |
| `--no-discovery` | 不响应局域网自动查找（安全要求高的环境） |

### 2. 发文件

```sh
lansplice send /home/lanlan/报表.xlsx --to 192.168.1.20
lansplice send /data/备份 --to 192.168.1.20:47820
lansplice send "/data/音乐/*.flac" --to 192.168.1.20 --verify
```

| 参数 | 作用 |
|---|---|
| `--to ip[:port]` | 对端地址，必填 |
| `--code 配对码` | 对端的配对码 |
| `--overwrite` | 对端有同名文件时直接覆盖（默认另存 `xxx (2).ext`） |
| `--verify` | 传完再整文件重读校验一遍（慢，但能查出读写出错） |

退出码：`0` 全成、`1` 有文件没传成（可以重跑，断点续传会接上）、
`2` 压根没开始（连不上或配对码不对）。

### 3. 找设备

```sh
lansplice devices
```

列出局域网里正在接收的机器。找不到时先确认两台在同一个网段、
对端开着 `serve`、UDP 47821 没被防火墙挡。

---

## 四、防火墙

接收端要 **TCP 47820**，自动发现要 **UDP 47821**。

```sh
# ufw（Ubuntu / 深度常用）
sudo ufw allow 47820/tcp && sudo ufw allow 47821/udp

# firewalld（麒麟 / openEuler / CentOS 常用）
sudo firewall-cmd --permanent --add-port=47820/tcp
sudo firewall-cmd --permanent --add-port=47821/udp
sudo firewall-cmd --reload

# 只有 iptables 的老系统
sudo iptables -A INPUT -p tcp --dport 47820 -j ACCEPT
sudo iptables -A INPUT -p udp --dport 47821 -j ACCEPT
```

`install.sh` 检测到 ufw 或 firewalld 时会顺手放行。

**麒麟的安全中心是另一层。** 有些版本除了 firewalld，还有自己的
「防火墙」图形开关，那个也要放行，否则命令行看规则是对的、包还是被丢。

不用自动发现也可以：`serve --no-discovery`，发送时直接写 IP。

---

## 五、开机就等着收

用 systemd，比 `nohup` 稳（开机时网络还没起来也能重试）：

```ini
# /etc/systemd/system/lansplice.service
[Unit]
Description=LanSplice receiver
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=lanlan
ExecStart=/usr/local/bin/lansplice serve --root /srv/inbox
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```sh
sudo systemctl daemon-reload
sudo systemctl enable --now lansplice
journalctl -u lansplice -f     # 看日志
```

注意 `User=` 要写成真实用户，否则文件会落在 root 的家目录下，
配置和配对码也跟着跑到 `/root/.config` 里 —— 之后用普通用户跑就「没有配对码」了。
这是这类服务最常见的坑。

---

## 六、文件放在哪

| 内容 | 路径 |
|---|---|
| 配置（含配对码） | `~/.config/LanSplice/config.json`（权限 600） |
| 传输历史 | `~/.local/share/LanSplice/history.jsonl` |
| 默认接收目录 | `~/Downloads/LanSplice`（没有 Downloads 就用 `~/下载/LanSplice`） |

Windows 上仍然是 `%APPDATA%\LanSplice`，和以前一样，升级不会丢东西。

想换位置：设 `XDG_CONFIG_HOME` / `XDG_DATA_HOME` 环境变量即可，只认绝对路径。

---

## 七、和 Windows 互通

前提只有一条：**配对码一致**。

```
麒麟 ──(serve, 打印配对码 K7QM-...)──▶ 填到 Windows 界面
Windows ──(发送 或 拖文件进窗口)──▶ 麒麟收到 ~/Downloads/LanSplice
麒麟 ──(lansplice send 文件 --to 192.168.1.20)──▶ Windows 界面收到
```

Windows 侧不需要任何额外设置，还是原来的图形界面。

文件名的差异由两边自动处理：Windows 不允许 `: ? * " < > |`，Linux 传来的
文件名里带这些字符时会自动替换；大小写、长路径同理。

---

## 八、常见问题

| 现象 | 原因 | 怎么办 |
|---|---|---|
| `没有找到配对码` | 本机从没生成过 | 直接跑 `lansplice serve`，它会生成并打印；或加 `--code` |
| `连不上对端` | 端口没人听 / 不同网段 | 对端跑 `serve`；`lansplice devices` 看能不能发现 |
| `配对码不对，对端拒绝了` | 两边码不一样 | 以一边为准，另一边重新输入 |
| 收不到但端口是通的 | 麒麟安全中心另有一层防火墙 | 图形界面里也放行 47820 |
| `devices` 空列表 | UDP 47821 被挡 / 对端 `--no-discovery` | 放行 UDP，或直接写 IP |
| 文件落在 `/root/` 下 | systemd 里没写 `User=` | 加上 `User=你的用户名` |
| 传大文件中途断了 | 网络抖动 | 重跑同一条 `send`，会从断点接着传 |

---

## 九、后续

- **P5**：图形界面版（tkinter 在 Linux 上能跑，要换掉 `winreg` / `explorer` /
  防火墙管理，托盘先不做）
- **P6**：`.deb` 包 + 各架构真机验证（PyInstaller 不能交叉编译，每个架构
  都得在真机上打）

在那之前，`serve` + `send` 已经足够跑通「信创 ↔ Windows」和「信创 ↔ 信创」。
