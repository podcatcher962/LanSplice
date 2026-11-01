# -*- mode: python ; coding: utf-8 -*-
"""
macOS 打包配置 —— 只能在 Mac 上跑（PyInstaller 不能交叉编译）。

    pyinstaller Link2PC-mac.spec --noconfirm

产物 dist/LanSplice.app。**未签名**：Gateway（Gatekeeper）会拦第一次打开，
解法见 docs/macos.md（右键打开，或 xattr -dr com.apple.quarantine）。
"""
import os
import sys

datas = []
binaries = []
hiddenimports = []

# qrcode / 托盘 / 网页模块是 try/except 里按需 import 的，静态分析追不到；
# 缺了不崩，但功能会静默消失，所以显式声明。
hiddenimports += ['qrcode', 'qrcode.constants', 'qrcode.util',
                  'link2pc_web', 'link2pc_cli',
                  'link2pc_i18n', 'link2pc_core', 'link2pc_history',
                  'link2pc_paths', 'link2pc_platform', 'link2pc_deps']
# link2pc_tray 在非 Windows 上主动 raise ImportError，不进包。

# cryptography 的 openssl 后端有一批模块是运行时按名导入的，静态分析追不全。
hiddenimports += ['cryptography.hazmat.backends.openssl.x509',
                  'cryptography.hazmat.backends.openssl.decode_asn1',
                  'cryptography.hazmat.backends.openssl.encode_asn1']

a = Analysis(
    [os.path.join(os.path.dirname(os.path.abspath(__file__)),
                  'link2pc_gui.py')],
    pathex=[],
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
    target_arch=None,               # None = 本机架构；Apple Silicon 上要
                                    # universal2 就装 universal2 的 Python
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
)
