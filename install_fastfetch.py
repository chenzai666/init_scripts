#!/usr/bin/env python3
"""
Debian 11 FastFetch 安装脚本 (最终修正版)
解决 libc6 依赖问题并使用 lolcat 彩色输出
2024.06.08 - 修正下载链接
"""
import os
import subprocess
import sys
import platform
import tarfile
import tempfile
import urllib.request
import ssl
import re

# 创建自定义 SSL 上下文
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

def run_command(cmd, sudo=False):
    """运行命令并返回输出和返回码"""
    try:
        if sudo:
            cmd = f"sudo {cmd}"
        result = subprocess.run(
            cmd, shell=True, check=False,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True
        )
        return result.stdout.strip(), result.returncode
    except Exception as e:
        print(f"❌ 命令执行失败: {str(e)}")
        return None, -1

def is_root():
    """检查是否为 root 用户"""
    return os.geteuid() == 0

def detect_architecture():
    """检测系统架构并映射到 FastFetch 的架构命名"""
    arch = platform.machine().lower()
    
    # FastFetch 使用特定的架构命名
    if arch in ["x86_64", "amd64"]:
        return "x86_64", "Linux"
    elif arch.startswith("aarch64") or arch.startswith("arm64"):
        return "aarch64", "Linux-ARM64"
    elif arch.startswith("armv7") or arch.startswith("armhf"):
        return "armv7", "Linux-ARMHF"
    else:
        return arch, "Unknown"

def install_lolcat():
    """安装 lolcat"""
    print("\n🌈 安装 lolcat...")
    
    # 检查是否已安装
    output, code = run_command("which lolcat")
    if code == 0 and output:
        print("✅ lolcat 已安装")
        return True
    
    # 安装 Ruby 和 gem
    _, code = run_command("apt install -y ruby ruby-dev", sudo=True)
    if code != 0:
        print("⚠️ Ruby 安装失败，尝试继续安装 lolcat...")
    
    # 尝试使用 gem 安装
    print("🔄 尝试 gem 安装...")
    output, code = run_command("gem install lolcat", sudo=True)
    if code == 0:
        print("✅ lolcat 安装成功")
        return True
    
    print("⚠️ lolcat 安装失败，将使用普通输出")
    return False

def fix_dependencies():
    """修复依赖关系问题"""
    print("\n🔧 修复系统依赖...")
    
    # 尝试修复损坏的依赖
    run_command("apt --fix-broken install -y", sudo=True)
    
    # 安装基本依赖
    print("\n📦 安装基本依赖...")
    run_command("apt update", sudo=True)
    run_command("apt install -y wget tar git", sudo=True)

def download_fastfetch(arch_name, release_name, version):
    """下载 FastFetch 并返回文件路径"""
    # 正确的文件名格式
    filename = f"fastfetch-{version}-{release_name}.tar.gz"
    download_url = f"https://github.com/fastfetch-cli/fastfetch/releases/download/{version}/{filename}"
    
    # 创建临时目录
    tmp_dir = tempfile.mkdtemp()
    tar_path = os.path.join(tmp_dir, filename)
    
    print(f"\n📥 下载 FastFetch {version} [{release_name}]...")
    print(f"   URL: {download_url}")
    
    try:
        # 尝试使用 urllib 下载
        with urllib.request.urlopen(download_url, context=ssl_context) as response:
            with open(tar_path, 'wb') as f:
                f.write(response.read())
        print("✅ 下载完成")
        return tar_path
    except Exception as e:
        print(f"❌ urllib 下载失败: {str(e)}")
    
    # 备选下载方式 - 使用 wget
    print("\n🔄 尝试 wget 下载...")
    wget_cmd = f"wget --no-check-certificate -O '{tar_path}' '{download_url}'"
    output, code = run_command(wget_cmd, sudo=False)
    
    if code == 0 and os.path.exists(tar_path) and os.path.getsize(tar_path) > 10240:  # 10KB
        print("✅ wget 下载成功")
        return tar_path
    
    print(f"❌ wget 下载失败 (状态码: {code})")
    print(f"   输出: {output[:200]}" if output else "")
    return None

def install_fastfetch():
    """安装 FastFetch"""
    if not is_root():
        print("❌ 请使用 sudo 或以 root 用户运行此脚本")
        sys.exit(1)
    
    print("🚀 Debian 11 FastFetch 安装程序 (最终修正版)")
    print("=" * 50)
    
    # 修复依赖问题
    fix_dependencies()
    
    # 安装 lolcat
    lolcat_installed = install_lolcat()
    
    # 获取系统架构
    arch, release_name = detect_architecture()
    print(f"🔍 检测到系统架构: {arch} → {release_name}")
    
    if release_name == "Unknown":
        print(f"❌ 不支持的架构: {arch}")
        sys.exit(1)
    
    # FastFetch 版本
    version = "2.58.0"
    
    # 下载 FastFetch
    tar_path = download_fastfetch(arch, release_name, version)
    if not tar_path:
        print("❌ 下载失败，无法继续安装")
        sys.exit(1)
    
    # 解压文件
    print("\n📂 解压文件...")
    tmp_dir = os.path.dirname(tar_path)
    try:
        with tarfile.open(tar_path, "r:gz") as tar:
            tar.extractall(path=tmp_dir)
        print("✅ 解压完成")
    except Exception as e:
        print(f"❌ 解压失败: {str(e)}")
        sys.exit(1)
    
    # 查找二进制文件
    bin_path = None
    for root, dirs, files in os.walk(tmp_dir):
        if "fastfetch" in files:
            bin_path = os.path.join(root, "fastfetch")
            break
    
    if not bin_path:
        print("❌ 找不到 fastfetch 可执行文件")
        print("   尝试在解压目录中查找...")
        sys.exit(1)
    
    print(f"🔍 找到可执行文件: {bin_path}")
    
    # 安装到系统
    print("\n🚀 安装到系统目录...")
    install_dir = "/usr/local/bin"
    dest_path = os.path.join(install_dir, "fastfetch")
    
    try:
        # 确保目录存在
        os.makedirs(install_dir, exist_ok=True)
        
        # 复制文件
        cmd = f"cp '{bin_path}' '{dest_path}' && chmod 755 '{dest_path}'"
        output, code = run_command(cmd, sudo=True)
        
        if code == 0:
            print(f"✅ 安装完成: {dest_path}")
        else:
            print(f"❌ 安装失败 (状态码: {code})")
            print(f"   输出: {output[:200]}" if output else "")
            sys.exit(1)
    except Exception as e:
        print(f"❌ 安装失败: {str(e)}")
        sys.exit(1)
    
    # 验证安装
    print("\n🔍 验证安装...")
    output, code = run_command("fastfetch --version")
    if code == 0 and output:
        version_line = output.splitlines()[0] if output else "unknown"
        print(f"✅ FastFetch 安装成功: {version_line}")
    else:
        print("❌ FastFetch 验证失败")
        sys.exit(1)
    
    # 添加到 /etc/profile
    print("\n⚙️ 配置全局自动启动...")
    config_script = """
# 自动运行 FastFetch (由安装脚本添加)
if [ -n "$SSH_CONNECTION" ]; then
    if command -v fastfetch >/dev/null 2>&1; then
        # 使用 lolcat 输出彩色效果
        if command -v lolcat >/dev/null 2>&1; then
            fastfetch | lolcat
        else
            fastfetch
        fi
    fi
fi
"""
    
    profile_path = "/etc/profile"
    try:
        # 检查是否已存在配置
        with open(profile_path, "r") as f:
            content = f.read()
            if "fastfetch" in content:
                print("ℹ️ 配置已存在于 /etc/profile")
            else:
                # 添加配置
                with open(profile_path, "a") as f:
                    f.write("\n" + config_script)
                print(f"✅ 已添加到 {profile_path}")
                print("   配置将在下次登录时生效")
    except Exception as e:
        print(f"❌ 写入配置文件失败: {str(e)}")
    
    # 创建测试命令
    test_script = """#!/bin/bash
if command -v fastfetch >/dev/null 2>&1; then
    if command -v lolcat >/dev/null 2>&1; then
        fastfetch | lolcat
    else
        fastfetch
    fi
fi
"""
    test_path = "/usr/local/bin/test-fetch"
    try:
        with open(test_path, "w") as f:
            f.write(test_script)
        run_command(f"chmod +x {test_path}", sudo=True)
        print(f"✅ 创建测试命令: test-fetch")
    except Exception as e:
        print(f"⚠️ 创建测试命令失败: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🎉 安装成功！")
    print(f"💡 FastFetch 已安装在 {dest_path}")
    print(f"⚙️  配置已添加到 {profile_path}")
    print(f"🌈  lolcat 状态: {'已安装' if lolcat_installed else '未安装'}")
    print("\n👉 您可以立即测试:")
    print("   test-fetch")
    print("\n👉 下次 SSH 登录时将自动显示系统信息")
    print("✨ 享受炫酷的系统信息展示吧！")

if __name__ == "__main__":
    install_fastfetch()
