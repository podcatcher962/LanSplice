#!/bin/sh
# ======================================================================
# LanSplice macOS 打包脚本 —— 在 Mac 的终端里跑这一个文件
#
#   sh build_macos.sh            打出未签名的 dist/LanSplice.app
#   sh build_macos.sh --check    打包前先跑一遍环境自检（mac_check.py）
#
# 前提：
#   · macOS 10.15+（更老的没试过）
#   · python3（Xcode 命令行工具或 python.org 安装包都行，建议 3.9+）
#   · 第一次会联网装 pyinstaller 和 cryptography（约 20 MB）
# ======================================================================
set -e
cd "$(dirname "$0")"

echo "=============================================="
echo " LanSplice macOS 打包（未签名版）"
echo " $(sw_vers -productName) $(sw_vers -productVersion) / $(sw_vers -buildVersion)"
echo " Python: $(python3 -V 2>&1)"
echo " 架构:   $(uname -m)"
echo "=============================================="

if [ "$1" = "--check" ]; then
    python3 mac_check.py
    exit 0
fi

# ---------- 虚拟环境 ----------
if [ ! -x .venv-mac/bin/python ]; then
    echo ""
    echo "[1/3] 建虚拟环境…"
    python3 -m venv .venv-mac
fi
. .venv-mac/bin/activate
echo ""
echo "[2/3] 装 pyinstaller + cryptography…"
python -m pip install --quiet --upgrade pip
python -m pip install --quiet pyinstaller cryptography || {
    echo "安装失败 —— 大概率是网络。换手机热点再试一次，或者："
    echo "  python -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pyinstaller cryptography"
    exit 1
}

# ---------- 打包 ----------
echo ""
echo "[3/3] pyinstaller 打包中（2~4 分钟）…"
python -m PyInstaller _build/Link2PC-mac.spec --noconfirm --distpath dist-mac \
    --workpath build-mac

APP="dist-mac/LanSplice.app"
if [ ! -d "$APP" ]; then
    echo "打包失败：没找到 $APP"
    exit 1
fi

echo ""
echo "=============================================="
echo " 完成：$APP"
echo " 拷到 /Applications 后，第一次打开："
echo "   右键 → 打开 → 再点「打开」（绕过 Gatekeeper）；"
echo "   或终端里：xattr -dr com.apple.quarantine $APP"
echo "=============================================="
