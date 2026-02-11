#!/usr/bin/env python3
"""
Fastfetch 自动安装脚本
--------------------------------------
兼容:
- Arch (pacman)
- Debian / Ubuntu (apt)
- Fedora (dnf)
- Alpine (apk)

设计原则:
- 不依赖系统 which 命令
- 使用 Python 内置 shutil.which() 判断命令存在
- 统一安装流程
- 清晰错误提示
"""

import os
import platform
import shutil
import subprocess
import sys


def run_command(cmd: list) -> bool:
    """
    执行系统命令

    :param cmd: 命令列表，例如 ["sudo", "pacman", "-S", "fastfetch"]
    :return: 成功返回 True，失败返回 False
    """
    try:
        subprocess.check_call(cmd)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 命令执行失败: {' '.join(cmd)}")
        print(f"错误信息: {e}")
        return False


def command_exists(cmd: str) -> bool:
    """
    判断命令是否存在

    使用 shutil.which() 而不是系统 which，
    避免 Arch 等系统未安装 which 时出错。

    :param cmd: 命令名称
    :return: 存在返回 True
    """
    return shutil.which(cmd) is not None


def detect_package_manager() -> str | None:
    """
    自动检测系统包管理器

    :return: 包管理器名称或 None
    """
    if command_exists("pacman"):
        return "pacman"
    elif command_exists("apt"):
        return "apt"
    elif command_exists("dnf"):
        return "dnf"
    elif command_exists("apk"):
        return "apk"
    else:
        return None


def install_package(pkg_manager: str, package_name: str) -> bool:
    """
    根据包管理器安装软件

    :param pkg_manager: 包管理器名称
    :param package_name: 软件包名
    :return: 安装是否成功
    """
    print(f"📦 使用 {pkg_manager} 安装 {package_name}...")

    if pkg_manager == "pacman":
        return run_command(["sudo", "pacman", "-Sy", "--noconfirm", package_name])

    elif pkg_manager == "apt":
        # apt 需要先 update
        run_command(["sudo", "apt", "update"])
        return run_command(["sudo", "apt", "install", "-y", package_name])

    elif pkg_manager == "dnf":
        return run_command(["sudo", "dnf", "install", "-y", package_name])

    elif pkg_manager == "apk":
        return run_command(["sudo", "apk", "add", package_name])

    else:
        print("❌ 不支持的包管理器")
        return False


def ensure_installed(pkg_manager: str, package_name: str) -> bool:
    """
    确保软件已安装

    如果未安装则自动安装，并再次验证。

    :param pkg_manager: 包管理器
    :param package_name: 软件名
    :return: 是否安装成功
    """
    print(f"🔍 检查 {package_name} 是否已安装...")

    # 先检测是否已经存在
    if command_exists(package_name):
        print(f"✅ {package_name} 已安装")
        return True

    print(f"📦 {package_name} 未安装，开始安装...")

    success = install_package(pkg_manager, package_name)

    # 安装后再次检查
    if success and command_exists(package_name):
        print(f"✅ {package_name} 安装成功")
        return True
    else:
        print(f"❌ {package_name} 安装失败")
        return False
        
def add_to_shell_config():
    """
    自动写入当前用户 shell 配置文件
    """

    shell = os.environ.get("SHELL", "")

    if "bash" in shell:
        config_file = os.path.expanduser("~/.bashrc")
    elif "zsh" in shell:
        config_file = os.path.expanduser("~/.zshrc")
    else:
        print("⚠️ 未识别的 shell，跳过自动写入")
        return

    line = "\n# Auto start fastfetch\nfastfetch\n"

    # 避免重复写入
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            if "fastfetch" in f.read():
                print("ℹ️ 已存在 fastfetch 启动项")
                return

    with open(config_file, "a") as f:
        f.write(line)

    print(f"✅ 已写入配置文件: {config_file}")

def main():
    """
    主函数
    """
    print("📌 正在检测系统信息...")

    system = platform.system().lower()
    distro = platform.platform()

    print(f"系统类型: {system}")
    print(f"发行版信息: {distro}")

    pkg_manager = detect_package_manager()

    if not pkg_manager:
        print("❌ 未检测到支持的包管理器")
        sys.exit(1)

    print(f"📦 检测到包管理器: {pkg_manager}")

    # 安装 fastfetch
    if not ensure_installed(pkg_manager, "fastfetch"):
        print("\n❌ fastfetch 安装失败，请检查权限或网络")
        sys.exit(1)

    # 可选安装 lolcat（增强显示效果）
    ensure_installed(pkg_manager, "lolcat")

    add_to_shell_config()

    print("\n🎉 安装完成！")
    print("现在可以运行:")
    print("   fastfetch")


if __name__ == "__main__":
    main()
