#!/bin/sh
# LanSplice 在 Linux / 信创系统上的安装脚本
# -----------------------------------------
#   sudo sh install.sh              装到 /opt/lansplice
#   sudo sh install.sh --prefix /usr/local/lansplice
#   sudo sh install.sh --uninstall
#
# 只用 POSIX sh，不依赖 bash —— 统信 UOS / 麒麟 V10 上都直接能跑。
#
# 为什么不打包成单文件可执行：SELinux / AppArmor 策略（麒麟默认开）会拦住
# PyInstaller 单文件往 /tmp 解包。目录版没这个问题，而且升级时只换 .py 文件。

set -e

APP="LanSplice"
PREFIX="/opt/lansplice"
BINLINK="/usr/local/bin/lansplice"
SRC_DIR=$(cd "$(dirname "$0")" && pwd)

# 装哪些文件：只装真正要跑的，_build/ _tests/ 不进目标机器
FILES="link2pc_core.py link2pc_cli.py link2pc_gui.py link2pc_i18n.py \
link2pc_platform.py link2pc_paths.py link2pc_history.py link2pc_web.py \
link2pc_deps.py link2pc_tray.py app.ico README.md LICENSE"

DESKTOP_FILE="/usr/share/applications/lansplice.desktop"
ICON_DIR="/usr/share/icons/hicolor"

say() { printf '%s\n' "$*"; }
die() { printf '错误：%s\n' "$*" >&2; exit 1; }

# 不只看顶层 import：C 扩展没装好时，顶层 cryptography 也可能导得进去。
crypto_works() {
    python3 -c 'from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey; from cryptography.hazmat.primitives.ciphers.aead import AESGCM' >/dev/null 2>&1
}
vendor_crypto_works() {
    PYTHONPATH="$PREFIX/vendor${PYTHONPATH:+:$PYTHONPATH}" \
        python3 -c 'from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey; from cryptography.hazmat.primitives.ciphers.aead import AESGCM' >/dev/null 2>&1
}

need_root() {
    [ "$(id -u)" -eq 0 ] || die "需要管理员权限，请用 sudo sh install.sh"
}

# ---------------------------------------------------------------- 卸载
if [ "$1" = "--uninstall" ]; then
    need_root
    rm -f "$BINLINK"
    rm -f "$DESKTOP_FILE"
    rm -rf "$PREFIX"
    say "已卸载。配置和传输历史留在原位，没有删："
    say "  ~/.config/LanSplice       （配置）"
    say "  ~/.local/share/LanSplice  （历史）"
    exit 0
fi

while [ $# -gt 0 ]; do
    case "$1" in
        --prefix) PREFIX="$2"; shift 2 ;;
        --prefix=*) PREFIX="${1#*=}"; shift ;;
        -h|--help)
            say "用法：sudo sh install.sh [--prefix 目录] [--uninstall]"
            exit 0 ;;
        *) die "不认识的参数：$1" ;;
    esac
done

need_root

# ---------------------------------------------------------------- 系统
DISTRO=""
if [ -r /etc/os-release ]; then
    DISTRO=$(. /etc/os-release; printf '%s' "${ID:-}${ID_LIKE:+ }${ID_LIKE:-}")
fi
say "系统：${DISTRO:-未知}"

command -v python3 >/dev/null 2>&1 || die "没找到 python3，请先装 python3（3.7 或更高）"

PYVER=$(python3 -c 'import sys;print("%d.%d"%sys.version_info[:2])')
PYMAJ=$(python3 -c 'import sys;print(sys.version_info[0])')
PYMIN=$(python3 -c 'import sys;print(sys.version_info[1])')
if [ "$PYMAJ" -lt 3 ] || { [ "$PYMAJ" -eq 3 ] && [ "$PYMIN" -lt 7 ]; }; then
    die "Python 版本太低（$PYVER）。需要 3.7+，麒麟 V10 / 统信 UOS 20 自带的都够。"
fi
say "Python：$(python3 -c 'import sys;print(sys.version.split()[0])')"

# ---------------------------------------------------------------- 依赖
# 只依赖 cryptography 一个第三方库。优先用系统自带的包；UOS 20 实测可能
# 没有它、没有 pip，apt 还会报「无法定位软件包」，所以完整安装包自带离线轮子。
if crypto_works; then
    say "依赖：cryptography 已有（$(python3 -c 'import cryptography;print(cryptography.__version__)')）"
else
    OFFLINE_OK=""
    # 这条失败时不能让 set -e 直接把脚本带走 —— 那样用户只会看到脚本无声无息
    # 就不跑了，连是哪一步出事都看不出来。取不到就当没有离线包，往后面走。
    OFFLINE_TAG=$(PYTHONPATH="$SRC_DIR" python3 -c \
        'from link2pc_deps import offline_tag; print(offline_tag())' 2>/dev/null || true)
    if [ -n "$OFFLINE_TAG" ] && [ -d "$SRC_DIR/wheels/$OFFLINE_TAG" ]; then
        say "依赖：缺 cryptography，使用安装包里的离线依赖（$OFFLINE_TAG）…"
        mkdir -p "$PREFIX"
        if python3 -B "$SRC_DIR/link2pc_deps.py" --extract \
                "$SRC_DIR/wheels" "$PREFIX/vendor" && vendor_crypto_works; then
            OFFLINE_OK="1"
            say "依赖：离线加密组件已装好，不需要 pip、apt 或联网"
        fi
    fi

    if [ -z "$OFFLINE_OK" ]; then
        say "依赖：离线包不匹配或不可用，尝试用系统包管理器安装…"
        if command -v apt-get >/dev/null 2>&1; then
            apt-get install -y python3-cryptography || true
        elif command -v dnf >/dev/null 2>&1; then
            dnf install -y python3-cryptography || true
        elif command -v yum >/dev/null 2>&1; then
            yum install -y python3-cryptography || true
        elif command -v zypper >/dev/null 2>&1; then
            zypper -n install python3-cryptography || true
        elif command -v pacman >/dev/null 2>&1; then
            pacman -S --noconfirm python-cryptography || true
        fi
    fi

    if [ -z "$OFFLINE_OK" ] && ! crypto_works && ! vendor_crypto_works; then
        say ""
        say "还是装不上。请确认使用的是完整 Linux 安装包（含 wheels/ 目录），"
        say "或从系统安装光盘/内网源安装 python3-cryptography。"
        die "缺 cryptography，装不了；程序不会降级成不加密传输"
    fi
fi

# tkinter 是图形界面必需的，而且它不在 pip 里 —— 只能走系统包。
# 信创最小安装常常没有，缺了就只能用命令行。
if python3 -c 'import tkinter' >/dev/null 2>&1; then
    say "依赖：tkinter 已有"
else
    say "依赖：缺 tkinter（图形界面要用），尝试用系统包管理器安装…"
    if command -v apt-get >/dev/null 2>&1; then
        apt-get install -y python3-tk || true
    elif command -v dnf >/dev/null 2>&1; then
        dnf install -y python3-tkinter || true
    elif command -v yum >/dev/null 2>&1; then
        yum install -y python3-tkinter || true
    elif command -v zypper >/dev/null 2>&1; then
        zypper -n install python3-tk || true
    elif command -v pacman >/dev/null 2>&1; then
        pacman -S --noconfirm tk || true
    fi
    if python3 -c 'import tkinter' >/dev/null 2>&1; then
        say "依赖：tkinter 已装好"
    else
        say ""
        say "tkinter 装不上，图形界面用不了，但命令行仍然可用："
        say "  lansplice serve / lansplice send / lansplice devices"
        say "要图形界面的话，从系统安装光盘/内网源装 python3-tk（UOS、麒麟都提供）。"
    fi
fi

# ---------------------------------------------------------------- 复制
say "安装到 $PREFIX"
mkdir -p "$PREFIX"
for f in $FILES; do
    if [ -f "$SRC_DIR/$f" ]; then
        cp -f "$SRC_DIR/$f" "$PREFIX/$f"
    fi
done

# 父目录不一定存在：极简安装的 Debian / UOS 可能压根没有 /usr/local/bin，
# 少了这句 cat 会直接失败，后面 set -e 还会把脚本无声带走。
mkdir -p "$(dirname "$BINLINK")" 2>/dev/null || true
cat > "$BINLINK" <<EOF
#!/bin/sh
# LanSplice 启动器（由 install.sh 生成）
# -B：不写 __pycache__ —— 装在 /opt 下普通用户改不动，否则每次启动都报权限警告
#
# 入口是 link2pc_gui.py 而不是 link2pc_cli.py：
# 它的 main() 会先看参数，带 send/serve/devices 就转给命令行，
# 什么都不带才开窗口。所以一个 lansplice 命令两用：
#   lansplice              开图形界面
#   lansplice serve        纯命令接收
exec python3 -B "$PREFIX/link2pc_gui.py" "\$@"
EOF
chmod 755 "$BINLINK"

# 文件建好了也 chmod 了，终端里却敲不出命令 —— 这是 Linux 上最让人懵的一类
# 问题：只因为目录不在 PATH 里。信创精简安装的 root shell 常常就是这样，
# 用户会以为软件装坏了。这里主动兜住：补进 profile.d 让新终端生效，
# 同时给当前终端一行能直接粘的命令。
BIN_DIR=$(dirname "$BINLINK")
case ":$PATH:" in
    *":$BIN_DIR:"*) : ;;
    *)
        say ""
        say "注意：$BIN_DIR 不在当前 PATH 里，直接敲 lansplice 会提示找不到命令。"
        if mkdir -p /etc/profile.d 2>/dev/null; then
            if printf 'export PATH="$PATH:%s"\n' "$BIN_DIR" \
                    > /etc/profile.d/lansplice.sh 2>/dev/null; then
                chmod 644 /etc/profile.d/lansplice.sh 2>/dev/null || true
                say "  已写入 /etc/profile.d/lansplice.sh —— 新开终端就能直接用。"
            fi
        fi
        say "  想在当前这个终端立刻用，先执行："
        say "    export PATH=\"\$PATH:$BIN_DIR\""
        say "  （桌面图标不受影响，它写的是绝对路径。）"
        ;;
esac

chmod 755 "$PREFIX"
for f in $FILES; do
    [ -f "$PREFIX/$f" ] && chmod 644 "$PREFIX/$f"
done
[ ! -d "$PREFIX/vendor" ] || chmod -R a+rX "$PREFIX/vendor"

# 装完立刻用真实入口验一次，不让「缺依赖」拖到用户双击时才暴露。
python3 -B "$PREFIX/link2pc_cli.py" version >/dev/null 2>&1 || \
    die "安装后启动检查失败，请运行 python3 $PREFIX/link2pc_cli.py version 查看原因"

# ---------------------------------------------------------------- 桌面项
# 有了它，应用菜单里会出现 LanSplice，双击就能开图形界面。
# 图标用 app.ico 转的 png —— 没装转换工具就退回一个通用图标名，
# 少个图标不影响能不能用。
mkdir -p "$ICON_DIR/256x256/apps" 2>/dev/null || true
ICON_LINE="Icon=applications-internet"
if [ -f "$SRC_DIR/app.ico" ] && command -v convert >/dev/null 2>&1; then
    if convert "$SRC_DIR/app.ico[0]" "$ICON_DIR/256x256/apps/lansplice.png" 2>/dev/null; then
        ICON_LINE="Icon=lansplice"
    fi
elif [ -f "$SRC_DIR/app.ico" ] && command -v python3 >/dev/null 2>&1; then
    # 没有 ImageMagick 就用 Python 试一次（PIL 不一定有，失败就算了）
    if python3 -c "
import sys
try:
    from PIL import Image
    Image.open(sys.argv[1]).convert('RGBA').save(sys.argv[2])
except Exception:
    sys.exit(1)
" "$SRC_DIR/app.ico" "$ICON_DIR/256x256/apps/lansplice.png" 2>/dev/null; then
        ICON_LINE="Icon=lansplice"
    fi
fi

mkdir -p "$(dirname "$DESKTOP_FILE")" 2>/dev/null || true
cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=LanSplice
Name[zh_CN]=LanSplice 双机直传
GenericName=LAN file transfer
GenericName[zh_CN]=局域网文件直传
Comment=Push files straight onto the other PC's disk, no cloud, no sharing
Comment[zh_CN]=把文件直接推到对方硬盘上，不走网盘、不开共享
Exec=$BINLINK
$ICON_LINE
Terminal=false
Categories=Network;FileTransfer;
Keywords=transfer;lan;share;
StartupNotify=true
EOF
chmod 644 "$DESKTOP_FILE"
say "桌面项：$DESKTOP_FILE"

# ---------------------------------------------------------------- 放行
say ""
say "防火墙：接收端需要 TCP 47820，自动发现需要 UDP 47821。"
if command -v ufw >/dev/null 2>&1; then
    say "  已检测到 ufw，执行："
    ufw allow 47820/tcp >/dev/null 2>&1 || true
    ufw allow 47821/udp >/dev/null 2>&1 || true
    say "    ufw allow 47820/tcp && ufw allow 47821/udp   （本次已自动执行）"
elif command -v firewall-cmd >/dev/null 2>&1; then
    say "  已检测到 firewalld，执行："
    firewall-cmd --permanent --add-port=47820/tcp >/dev/null 2>&1 || true
    firewall-cmd --permanent --add-port=47821/udp >/dev/null 2>&1 || true
    firewall-cmd --reload >/dev/null 2>&1 || true
    say "    firewall-cmd --permanent --add-port=47820/tcp"
    say "    firewall-cmd --permanent --add-port=47821/udp && firewall-cmd --reload"
else
    say "  没检测到 ufw/firewalld。如果系统另装了防火墙（麒麟常见），手动放行这两个端口。"
fi

say ""
say "装好了。试一下："
say "  lansplice                             # 开图形界面（应用菜单里也有）"
say "  lansplice version"
say "  lansplice serve                       # 纯命令行当接收端，收进 ~/Downloads/LanSplice"
say "  lansplice send 文件 --to 192.168.1.20 # 发给对端（配对码在界面或 serve 里能看到）"
say ""
say "提示：两台机器的配对码必须一致。第一次用，在其中一台上打开界面或跑 serve，"
say "它会把配对码显示出来并存进 ~/.config/LanSplice/config.json。"
