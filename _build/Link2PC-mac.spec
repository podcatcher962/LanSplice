# -*- mode: python ; coding: utf-8 -*-
"""
macOS 打包配置 —— 只能在 Mac 上跑（PyInstaller 不能交叉编译）。

    pyinstaller Link2PC-mac.spec --noconfirm

产物 dist-mac/LanSplice.app。**未签名**：Gatekeeper 会拦第一次打开，
解法见 docs/macos.md（右键打开，或 xattr -dr com.apple.quarantine）。
"""
import os

datas = []
binaries = []
hiddenimports = []

# ---------------------------------------------------------------- 源码位置
# 这里不能用 __file__：
# PyInstaller 执行 spec 时会先 chdir 到 spec 所在目录（_build/），
# `os.path.dirname(os.path.abspath(__file__))` 得到的也是 _build/，
# 于是去找 _build/link2pc_gui.py —— 那里没这个文件，打包一开头就失败。
# （v1.7.4 才发现：之前从没在 Mac 上真跑过，所以一直没暴露。）
# 正确做法是用 PyInstaller 提供的 SPECPATH（spec 所在目录），再往上一级。
ROOT = os.path.abspath(os.path.join(SPECPATH, os.pardir))
MAIN = os.path.join(ROOT, "link2pc_gui.py")
if not os.path.isfile(MAIN):
    raise SystemExit("找不到入口 %s —— 本 spec 应放在仓库的 _build/ 目录下" % MAIN)

# 版本号从 link2pc_core.py 里读，不在这里再写一遍。
# （写死的话升级时一定要忘，忘一次就是「关于窗口说 1.7.4、包信息说 1.7.3」。）
# 用正则在源码里找，不 import —— import 会连带 cryptography，打包机上未必装好。
import re as _re


def _app_ver():
    with open(os.path.join(ROOT, "link2pc_core.py"), encoding="utf-8") as f:
        m = _re.search(r'^APP_VER\s*=\s*"([^"]+)"', f.read(), _re.M)
    return m.group(1) if m else "0.0.0"


VER = _app_ver()

# qrcode / 网页 / 聊天模块是 try/except 里按需 import 的，静态分析不一定追得到；
# 缺了不崩，但功能会**静默消失**（Linux 包就漏过聊天模块，教训记在 README）。
# 所以逐个显式声明。
hiddenimports += ['qrcode', 'qrcode.constants', 'qrcode.util',
                  'link2pc_web', 'link2pc_cli',
                  'link2pc_i18n', 'link2pc_core', 'link2pc_history',
                  'link2pc_paths', 'link2pc_platform', 'link2pc_deps',
                  'link2pc_chat', 'link2pc_chatwin', 'link2pc_sync']
# link2pc_tray 在非 Windows 上主动 raise ImportError，不进包。

# cryptography 的 openssl 后端有一批模块是运行时按名导入的，静态分析追不全。
hiddenimports += ['cryptography.hazmat.backends.openssl.x509',
                  'cryptography.hazmat.backends.openssl.decode_asn1',
                  'cryptography.hazmat.backends.openssl.encode_asn1']

a = Analysis(
    [MAIN],
    pathex=[ROOT],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='LanSplice',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,                      # macOS 上 upx 反而会被 Gatekeeper 起疑
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,               # None = 本机架构；要 universal2
                                    # 就得装 universal2 的 Python
    codesign_identity=None,         # None = 只做 ad-hoc 签名（未公证）
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='LanSplice',
)

app = BUNDLE(
    coll,
    name='LanSplice.app',
    bundle_identifier='com.lansplice.app',
    # 不设 icon 就是系统默认的空白图标：做 .icns 要用 macOS 的 iconutil，
    # 这个仓库没有 Mac，生成不了。其余信息在这里补上。
    info_plist={
        'CFBundleName': 'LanSplice',
        'CFBundleDisplayName': 'LanSplice',
        'CFBundleShortVersionString': VER,
        'CFBundleVersion': VER,
        'CFBundleGetInfoString': 'LanSplice %s - LAN file transfer and chat, no server'
                                 % VER,
        'NSHighResolutionCapable': True,           # Retina 屏上不至于糊
        'NSRequiresAquaSystemAppearance': False,   # 跟随系统深/浅色
        'LSMinimumSystemVersion': '10.15',
        'LSApplicationCategoryType': 'public.app-category.utilities',
        # 局域网广播/连接：macOS 14+ 首次会弹「是否允许查找本地网络设备」。
        # 这个键用来把用途说清楚，弹窗本身由系统控制。
        'NSLocalNetworkUsageDescription':
            'LanSplice 需要访问本地网络，才能发现同一局域网里的其他设备并互传文件。',
    },
)
