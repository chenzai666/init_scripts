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

def write_system_profile(fastfetch_path: str, lolcat_path: str):
    profile_file = "/etc/profile"
    start_marker = "# >>> init_fastfetch_start >>>"
    end_marker = "# <<< init_fastfetch_end <<<"

    new_block = (
        f"\n{start_marker}\n"
        f"{fastfetch_path} | {lolcat_path}\n"
        f"{end_marker}\n"
    )

    # 读取现有内容
    if os.path.exists(profile_file):
        with open(profile_file, "r") as f:
            content = f.read()
    else:
        content = ""

    # 删除旧标记块
    if start_marker in content and end_marker in content:
        import re
        pattern = re.compile(f"{start_marker}.*?{end_marker}", re.DOTALL)
        content = pattern.sub("", content)
        print("🧹 已删除旧的 fastfetch 配置块")

    # 额外清理旧版本（没有标记的旧写法）
    lines = content.splitlines()
    cleaned_lines = [
        line for line in lines
        if "fastfetch" not in line and "lolcat" not in line
    ]
    cleaned_content = "\n".join(cleaned_lines)

    # 重新写入 /etc/profile，需要 sudo
    try:
        import tempfile
        tmpfile = tempfile.NamedTemporaryFile(mode='w', delete=False)
        tmpfile.write(cleaned_content.strip() + "\n" + new_block)
        tmpfile.close()
        run_command(["sudo", "mv", tmpfile.name, profile_file])
        print(f"✅ 已更新系统配置文件: {profile_file}")
    except Exception as e:
        print(f"❌ 写入 {profile_file} 失败: {e}")




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
    write_system_profile(fastfetch_path, lolcat_path)

    print("\n🎉 安装与配置完成！")
    print("请重新打开终端生效。")


if __name__ == "__main__":
    main()
