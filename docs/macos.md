# macOS 使用指南（未签名版）

LanSplice 在 macOS 上是**源码 / .app 双形态**，全部免费、无广告、不联网上报。
这一版**未做 Apple 签名与公证**（那需要 Apple 开发者账号，约 688 元/年，即 $99），
所以第一次打开要走一个一次性步骤，见下文「第一次打开」。

---

## ⚠️ 先读：这一版的验证状态

**诚实说明：macOS 部分没有在真机 Mac 上跑过。**

开发与验证这两件事是分开的，这里把边界划清楚：

| 项目 | 状态 | 说明 |
|---|---|---|
| 传输协议、加密、断点续传 | ✅ 已验证 | 纯标准库 + cryptography，与平台无关；在 Windows 与 UOS 20 真机上跑通 |
| 命令行（`serve` / `send` / `devices`） | ✅ 代码层面已验证 | 与 Linux 版是同一份代码，Linux 真机 44 项全过 |
| 内网聊天 | ⚠️ 仅代码层面 | 与 Windows / Linux 同一份实现（无服务器、全互联），那边有真机证据，macOS 没有 |
| 图形界面 | ⚠️ **未在 Mac 上运行过** | tkinter 跨平台，但没有 Mac 就没有实机证据 |
| `build_macos.sh` 打包 | ⚠️ **未在 Mac 上执行过** | 见下方「v1.7.4 修掉的路径 bug」—— 修了，但修得对不对只有 Mac 能证明 |
| LaunchAgent 开机自启 | ⚠️ 仅单元测试 | 生成的 plist 结构与内容有测试覆盖，但没在真机上被 launchd 加载过 |
| Finder 复制后粘贴发送 | ⚠️ 仅单元测试 | osascript 脚本逻辑有测试，没有真机剪贴板验证 |

**为什么会这样**：这个项目没有任何一台 Mac 可用。与其假装验证过，
不如把哪些有证据、哪些没有写清楚 —— 你拿到 Mac 后跑一次
`python3 mac_check.py --full`，十几秒就能把上面那些 ⚠️ 变成 ✅ 或 ❌。

如果自检报错，把输出发到仓库的 Issues 里就行。

### v1.7.4 修掉的路径 bug（重要）

`_build/Link2PC-mac.spec` 原来用 `__file__` 定位源码。但 PyInstaller
执行 spec 之前会 `chdir` 到 spec 所在目录（`_build/`），于是它去找
`_build/link2pc_gui.py` —— 那里没有这个文件，**任何人跑 `build_macos.sh`
都会在第一步就失败**，报「找不到入口脚本」。

已经改成用 PyInstaller 提供的 `SPECPATH` 求仓库根，并且在 Windows 上
用桩环境跑过一遍验证（`_tests/_test_macpack.py`，46 项）。
同时补了两个同样「静默坏掉」的问题：`hiddenimports` 漏了聊天模块、
版本号写死在 spec 里。

**如果你在 v1.7.4 之前拿过这个仓库，请更新后再打包。**

---


## 一、最快能用：源码直接跑（2 分钟）

不需要打包、不需要任何安装器。系统自带 `python3`（10.15+ 都有）：

```sh
cd LanSplice            # 就是这份源码目录
python3 -m pip install --user cryptography    # 唯一的第三方依赖
python3 link2pc_gui.py                        # 图形界面
python3 link2pc_cli.py serve                  # 或：只当接收端（无界面）
```

第一次跑先自检一遍（可选但推荐）：

```sh
python3 mac_check.py --full
```

它会逐项确认加密、界面、单实例锁、开机自启、真传文件，十几秒出结论。

## 二、打包成 .app（像正常 Mac 软件一样用）

```sh
sh build_macos.sh --check     # 先自检
sh build_macos.sh             # 打包（第一次联网装 pyinstaller，约 2-4 分钟）
```

产物是 `dist-mac/LanSplice.app`，拖进「应用程序」即可。

## 三、第一次打开（未签名，只需一次）

双击 .app 会被 Gatekeeper 拦（「无法打开，因为无法验证开发者」或「已损坏」）。
这不是病毒，只是没有 Apple 开发者账号（约 688 元/年）的签名。三选一：

| 办法 | 操作 |
|---|---|
| 右键打开（最简单） | 在 Finder 里**按住 Control 点一下图标 → 打开 → 再点「打开」**，之后永远不再问 |
| 终端一条命令 | `xattr -dr com.apple.quarantine /Applications/LanSplice.app` |
| 系统设置放行 | 「隐私与安全性」页面底部会出现「仍要打开」按钮 |

## 四、功能对照

| 功能 | macOS 上的状态 |
|---|---|
| 局域网收发、断点续传、配对码、AES-256-GCM 加密 | ✅ 与 Windows / Linux 完全互通（协议是字节级的） |
| 图形界面、中文界面 | ✅ 苹方字体自动挑选 |
| **内网聊天**（多人、不用服务器） | ✅ 与 Windows / Linux 同一实现；无主机、全互联 |
| 接收目录 | 默认 `~/Downloads/LanSplice`（下载里的 LanSplice 文件夹），可改 |
| 「在 Finder 中显示」 | ✅ |
| 在 Finder 复制文件后在 LanSplice 里粘贴发送 | ✅（v1.7.2 新增，走 osascript） |
| 开机自启 | ✅ `~/Library/LaunchAgents/com.lansplice.app.plist`（v1.7.2 新增） |
| 托盘 / 菜单栏常驻 | ❌ 关窗口就是退出（与 Linux 版一致） |
| 拖拽文件进窗口 | 看环境：装了 tkinterdnd2 才有，否则用「添加文件」按钮 |

## 五、两个 macOS 特有的坑

**1. 本地网络权限（macOS 14 Sonoma 及以上）**

第一次扫描局域网时系统会弹「“LanSplice”想要查找并连接本地网络上的设备」，
必须点**允许**，否则永远扫不到别的设备、也发不出去。如果当时点了拒绝：
系统设置 → 隐私与安全性 → 本地网络 → 把 LanSplice 打开。

**2. 应用防火墙**

macOS 的应用防火墙默认是关的，一般不用管。如果开过（系统设置 → 网络 → 防火墙），
第一次监听时会弹「是否允许 LanSplice 接受传入连接」，点允许即可；
程序里的「防火墙」按钮也会给出等价的终端命令（socketfilterfw）。

## 六、命令行

与 Linux 版完全相同：

```sh
python3 link2pc_cli.py serve                       # 当接收端，打印配对码
python3 link2pc_cli.py send 报告.pdf --to 192.168.0.20   # 发给某台机器
python3 link2pc_cli.py devices                     # 扫一下谁在收
python3 link2pc_cli.py version                     # 版本与署名
```

## 七、架构与打包说明

- Intel（x86_64）与 Apple Silicon（arm64）都能跑；用哪台 Mac 打包就是哪个架构，
  PyInstaller 不支持交叉编译。要两边通吃需要各打一份（或装 universal2 的 Python）。
- 老系统：macOS 10.15 Catalina 起可用。Python 3.9+ 建议（更老的没测）。
- 想要正式签名版：需要 Apple Developer 账号，`Link2PC-mac.spec` 里把
  `codesign_identity` 填上你的 Developer ID，再跑一次
  `codesign --deep --force --options runtime` + `xcrun notarytool submit` 即可，
  代码不用改。
