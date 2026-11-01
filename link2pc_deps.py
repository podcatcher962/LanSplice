# -*- coding: utf-8 -*-
"""
LanSplice 的第三方依赖引导（只用标准库）。

UOS 20 专业版可能同时没有 cryptography、pip 和可用的 apt 源。
安装包因此在 wheels/ 里带一套 UOS 20 x86_64 的离线轮子，安装时解到
程序目录的 vendor/。本模块只负责把那个目录加入 sys.path，绝不自动联网，
也不在每次启动时解包。

其他 Linux 仍优先使用系统 cryptography；离线包目前只覆盖实测过的
Python 3.7 / x86_64，别的平台继续走系统软件源。
"""
import glob
import os
import platform
import sys
import zipfile


def _crypto_import():
    """导入程序真正用到的接口，避免顶层 import 成功但 C 扩展坏了的假绿。"""
    from cryptography.hazmat.primitives.asymmetric.x25519 import (
        X25519PrivateKey, X25519PublicKey,
    )
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.serialization import (
        Encoding, PublicFormat,
    )
    return (X25519PrivateKey, X25519PublicKey, HKDF, hashes, AESGCM,
            Encoding, PublicFormat)


def vendor_dir():
    """已安装离线库的位置；Windows/PyInstaller 正常不会走到这里。"""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor")


def _clear_failed_crypto_modules():
    """第一次导入失败后，清掉半初始化的模块再试 vendor。"""
    for name in list(sys.modules):
        if (name == "cryptography" or name.startswith("cryptography.")
                or name == "cffi" or name.startswith("cffi.")):
            sys.modules.pop(name, None)


def _error_text(detail):
    """
    缺加密库时给一句「照着做就能好」的中文。

    必须按平台分开说：Windows 用户看到「重新运行 install.sh」只会更困惑 ——
    那边根本没有 install.sh，是单文件 exe。
    """
    head = "LanSplice 缺少可用的加密组件 cryptography，无法启动。"
    if sys.platform.startswith("win"):
        tip = ("Windows 版是单文件 exe，加密组件本来就打包在里面。"
               "出现这个问题通常是杀毒软件把解压出来的文件隔离了，"
               "或者下载的包不完整 —— 请重新下载 LanSplice 的 exe，"
               "必要时在杀毒软件里把它加进白名单。")
    elif sys.platform == "darwin":
        tip = ("请先安装依赖：python3 -m pip install cryptography；"
               "用 build_macos.sh 打的 .app 已内置，不会走到这里。")
    else:
        tip = ("请使用完整的 Linux 安装包重新运行 install.sh；"
               "UOS 20 x86_64 可离线自动安装，其他系统请安装 python3-cryptography。")
    return "%s%s原始错误：%s" % (head, tip, detail)


def ensure_crypto():
    """
    确保加密接口可用。返回 system / bundled，失败给一句能照着做的中文。

    不做无加密降级：传文件的安全性不能因为缺一个依赖就悄悄消失。
    """
    try:
        _crypto_import()
        return "system"
    except Exception as first:
        vend = vendor_dir()
        if not os.path.isdir(vend):
            raise ImportError(_error_text(first)) from first
        if vend not in sys.path:
            sys.path.insert(0, vend)
        _clear_failed_crypto_modules()
        try:
            _crypto_import()
            return "bundled"
        except Exception as second:
            raise ImportError(_error_text(second)) from second


def offline_tag(version_info=None, machine=None):
    """返回随包离线轮子的目录名；没有对应轮子就返回空字符串。"""
    vi = version_info if version_info is not None else sys.version_info
    mach = (machine if machine is not None else platform.machine()).lower()
    if tuple(vi[:2]) == (3, 7) and mach in ("x86_64", "amd64"):
        return "cp37-x86_64"
    return ""


def extract_offline_wheels(wheels_root, dest, version_info=None, machine=None):
    """
    把匹配当前 Python/CPU 的轮子解到 dest，返回 (目录名, 轮子数)。

    显式由 install.sh / verify.sh 调用；ensure_crypto() 不做写盘操作。
    wheel 内的 .dist-info 与许可证也一起保留。
    """
    tag = offline_tag(version_info, machine)
    if not tag:
        raise RuntimeError(
            "这套离线包只为 UOS 20 的 Python 3.7 / x86_64 准备；"
            "当前系统请从软件源安装 python3-cryptography。"
        )
    src = os.path.join(wheels_root, tag)
    wheels = sorted(glob.glob(os.path.join(src, "*.whl")))
    if not wheels:
        raise RuntimeError("安装包不完整：找不到 wheels/%s/*.whl" % tag)
    os.makedirs(dest, exist_ok=True)
    for wheel in wheels:
        with zipfile.ZipFile(wheel) as zf:
            zf.extractall(dest)
    return tag, len(wheels)


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) == 3 and args[0] == "--extract":
        try:
            tag, count = extract_offline_wheels(args[1], args[2])
        except Exception as ex:
            sys.stderr.write("错误：%s\n" % ex)
            return 1
        print("离线依赖：%s，已解包 %d 个 wheel" % (tag, count))
        return 0
    sys.stderr.write("用法：python3 link2pc_deps.py --extract wheels目录 目标目录\n")
    return 2


if __name__ == "__main__":
    sys.exit(main())
