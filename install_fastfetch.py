#!/usr/bin/env python3
"""
Fastfetch + lolcat 自动安装 & 自动写入 shell 配置
兼容：
- Arch (pacman)
- Debian / Ubuntu (apt)
- Fedora (dnf)
- Alpine (apk)
"""

import os
import shutil
import subprocess
import sys
import platform


# ------------------------------
# 基础工具函数
# ------------------------------

def run_command(cmd: list) -> bool:
    """执行系统命令"""
    try:
        subprocess.check_call(cmd)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 命令执行失败: {' '.join(cmd)}")
        print(f"错误: {e}")
        return False


def command_exists(cmd: str) -> bool:
    """判断命令是否存在（不依赖 which）"""
    return shutil.which(cmd) is not None


def get_real_path(cmd: str) -> str | None:
    """获取命令真实路径"""
    path = shutil.which(cmd)
    if path:
        return os.path.realpath(path)
    return None


# ------------------------------
# 包管理器检测
# ------------------------------

def detect_package_manager() -> str | None:
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
    print(f"📦 使用 {pkg_manager} 安装 {package_name}...")

    if pkg_manager == "pacman":
        return run_command(["sudo", "pacman", "-Sy", "--noconfirm", package_name])

    elif pkg_manager == "apt":
        run_command(["sudo", "apt", "update"])
        return run_command(["sudo", "apt", "install", "-y", package_name])

    elif pkg_manager == "dnf":
        return run_command(["sudo", "dnf", "install", "-y", package_name])

    elif pkg_manager == "apk":
        return run_command(["sudo", "apk", "add", package_name])

    return False


def ensure_installed(pkg_manager: str, package_name: str) -> bool:
    print(f"🔍 检查 {package_name} 是否已安装...")

    if command_exists(package_name):
        print(f"✅ {package_name} 已安装")
        return True

    print(f"📦 {package_name} 未安装，开始安装...")
    success = install_package(pkg_manager, package_name)

    if success and command_exists(package_name):
        print(f"✅ {package_name} 安装成功")
        return True

    print(f"❌ {package_name} 安装失败")
    return False


# ------------------------------
# 写入 Shell 配置
# ------------------------------

def write_shell_config(fastfetch_path: str, lolcat_path: str):
    shell = os.environ.get("SHELL", "")

    if "bash" in shell:
        config_file = os.path.expanduser("~/.bashrc")
    elif "zsh" in shell:
        config_file = os.path.expanduser("~/.zshrc")
    else:
        print("⚠️ 未识别的 shell，跳过自动写入")
        return

    command_line = f"\n# Auto start fastfetch\n{fastfetch_path} | {lolcat_path}\n"

    # 避免重复写入
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            content = f.read()
            if fastfetch_path in content:
                print("ℹ️ 已存在 fastfetch 启动配置，跳过写入")
                return

    with open(config_file, "a") as f:
        f.write(command_line)

    print(f"✅ 已写入配置文件: {config_file}")


# ------------------------------
# 主程序
# ------------------------------

def main():
    print("📌 正在检测系统信息...")
    print(f"系统: {platform.platform()}")

    pkg_manager = detect_package_manager()

    if not pkg_manager:
        print("❌ 未检测到支持的包管理器")
        sys.exit(1)

    print(f"📦 检测到包管理器: {pkg_manager}")

    # 强制安装 fastfetch
    if not ensure_installed(pkg_manager, "fastfetch"):
        sys.exit(1)

    # 强制安装 lolcat
    if not ensure_installed(pkg_manager, "lolcat"):
        sys.exit(1)

    # 获取真实路径
    fastfetch_path = get_real_path("fastfetch")
    lolcat_path = get_real_path("lolcat")

    if not fastfetch_path or not lolcat_path:
        print("❌ 无法获取程序真实路径")
        sys.exit(1)

    print(f"📍 fastfetch 路径: {fastfetch_path}")
    print(f"📍 lolcat 路径: {lolcat_path}")

    # 写入 shell 配置
    write_shell_config(fastfetch_path, lolcat_path)

    print("\n🎉 安装与配置完成！")
    print("请重新打开终端生效。")


if __name__ == "__main__":
    main()
