#!/usr/bin/env python3
import os
import subprocess
import platform
import sys
import urllib.request
import json
import tarfile
import shutil
import re

def is_root():
    """检查是否以 root 权限运行脚本"""
    return os.geteuid() == 0

def run_command(cmd, description, check=True):
    """执行系统命令并处理输出和异常"""
    try:
        print(f"正在{description}...")
        result = subprocess.run(
            cmd,
            shell=True,
            check=check,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ {description}失败: {e.stderr.strip()}")
        return None

def detect_os_info():
    """检测系统发行版和版本"""
    os_info = {"distro": None, "version": None}
    
    # 读取 /etc/os-release
    if os.path.exists("/etc/os-release"):
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("ID="):
                    os_info["distro"] = line.strip().split("=")[1].strip('"')
                elif line.startswith("VERSION_ID="):
                    os_info["version"] = line.strip().split("=")[1].strip('"')
    
    # 兼容 Ubuntu 的变种（如 Linux Mint）
    if os_info["distro"] in ["ubuntu", "linuxmint"]:
        os_info["distro"] = "ubuntu"
    elif os_info["distro"] in ["debian", "raspbian"]:
        os_info["distro"] = "debian"
    
    return os_info

def compare_version(version1, version2):
    """比较版本号（如 22.04 > 20.04）"""
    v1_parts = list(map(float, version1.split(".")))
    v2_parts = list(map(float, version2.split(".")))
    
    # 补齐版本号位数
    max_len = max(len(v1_parts), len(v2_parts))
    v1_parts += [0] * (max_len - len(v1_parts))
    v2_parts += [0] * (max_len - len(v2_parts))
    
    for v1, v2 in zip(v1_parts, v2_parts):
        if v1 > v2:
            return 1
        elif v1 < v2:
            return -1
    return 0

def detect_package_manager():
    """检测系统包管理器"""
    if os.path.exists("/usr/bin/apt"):
        return "apt"
    elif os.path.exists("/usr/bin/dnf"):
        return "dnf"
    elif os.path.exists("/usr/bin/yum"):
        return "yum"
    elif os.path.exists("/usr/bin/pacman"):
        return "pacman"
    elif os.path.exists("/usr/bin/zypper"):
        return "zypper"
    elif os.path.exists("/usr/bin/apk"):
        return "apk"
    else:
        print("❌ 不支持的系统包管理器")
        sys.exit(1)

def check_installed(package):
    """检查软件是否已安装"""
    result = run_command(f"command -v {package}", f"检查{package}是否安装", check=False)
    return result is not None and result.returncode == 0

def install_lolcat(pm):
    """安装 lolcat"""
    install_cmds = {
        "apt": "apt install -y lolcat",
        "dnf": "dnf install -y lolcat",
        "yum": "yum install -y lolcat",
        "pacman": "pacman -S --noconfirm lolcat",
        "zypper": "zypper install -y lolcat",
        "apk": "apk add lolcat"
    }
    
    if pm in install_cmds:
        if pm == "apt":
            run_command("apt update -y", "更新软件仓库")
        result = run_command(install_cmds[pm], "安装 lolcat")
        return result is not None
    else:
        print("❌ 暂不支持当前系统安装 lolcat，请手动安装")
        return False

def install_fastfetch_ubuntu_debian(os_info):
    """针对 Ubuntu/Debian 安装 fastfetch"""
    distro = os_info["distro"]
    version = os_info["version"]
    
    # Ubuntu 22.04+：使用 PPA
    if distro == "ubuntu" and compare_version(version, "22.04") >= 0:
        run_command("apt update -y", "更新软件仓库")
        run_command("apt install -y software-properties-common", "安装依赖")
        # 添加 PPA
        add_ppa = run_command("add-apt-repository -y ppa:zhangsongcui3371/fastfetch", "添加 fastfetch PPA")
        if add_ppa:
            run_command("apt update -y", "更新 PPA 仓库")
            install = run_command("apt install -y fastfetch", "从 PPA 安装 fastfetch")
            return install is not None
    
    # Ubuntu 20.04+/Debian 11+：下载 deb 包安装
    arch = platform.machine()
    arch_map = {"x86_64": "amd64", "aarch64": "arm64", "armv7l": "armhf"}
    deb_arch = arch_map.get(arch, None)
    if not deb_arch:
        print(f"❌ 不支持的架构 {arch}，无法安装 deb 包")
        return False
    
    # 获取最新 deb 包下载链接
    api_url = "https://api.github.com/repos/fastfetch-cli/fastfetch/releases/latest"
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        req = urllib.request.Request(api_url, headers=headers)
        response = urllib.request.urlopen(req, timeout=10)
        release_data = json.loads(response.read().decode())
        
        deb_url = None
        for asset in release_data.get("assets", []):
            if f"fastfetch-linux-{deb_arch}.deb" in asset["name"]:
                deb_url = asset["browser_download_url"]
                break
        
        if not deb_url:
            print("❌ 未找到适配的 deb 安装包")
            return False
        
        # 下载 deb 包
        deb_file = "/tmp/fastfetch.deb"
        print(f"正在下载 fastfetch deb 包: {deb_url}")
        urllib.request.urlretrieve(deb_url, deb_file)
        
        # 安装 deb 包
        install = run_command(f"dpkg -i {deb_file}", "安装 fastfetch deb 包")
        if install:
            # 修复依赖问题
            run_command("apt install -f -y", "修复依赖")
            os.remove(deb_file)
            return True
    except Exception as e:
        print(f"❌ 下载 deb 包失败: {str(e)}")
        return False
    
    # Debian 13+/Ubuntu 25.04+：直接仓库安装
    if (distro == "debian" and compare_version(version, "13") >= 0) or \
       (distro == "ubuntu" and compare_version(version, "25.04") >= 0):
        run_command("apt update -y", "更新软件仓库")
        install = run_command("apt install -y fastfetch", "从仓库安装 fastfetch")
        return install is not None
    
    return False

def install_fastfetch_other(pm):
    """其他发行版安装 fastfetch"""
    install_cmds = {
        "pacman": "pacman -S --noconfirm fastfetch",
        "dnf": "dnf install -y fastfetch",
        "yum": "yum install -y fastfetch",
        "zypper": "zypper install -y fastfetch",
        "apk": "apk add fastfetch"
    }
    
    if pm in install_cmds:
        result = run_command(install_cmds[pm], f"使用 {pm} 安装 fastfetch")
        return result is not None
    else:
        print("❌ 暂不支持当前系统自动安装 fastfetch，请手动安装")
        return False

def add_to_profile():
    """将 fastfetch | lolcat 写入 profile 文件"""
    config_line = "\n# Auto-run fastfetch with lolcat (added by fastfetch install script)\n/usr/bin/fastfetch | lolcat\n"
    
    # 优先用户级配置文件
    profile_files = [
        os.path.expanduser("/etc/profile"),
        os.path.expanduser("~/.zshrc"),
        "~/.bashrc"
    ]
    
    target_file = None
    for pf in profile_files:
        if os.path.exists(pf):
            target_file = pf
            break
    if not target_file:
        target_file = os.path.expanduser("/etc/profile")
    
    # 检查是否已存在配置
    try:
        with open(target_file, "r") as f:
            if "/usr/bin/fastfetch | lolcat" in f.read():
                print("✅ fastfetch 配置已存在，无需重复写入")
                return True
    except FileNotFoundError:
        pass
    
    # 写入配置
    try:
        with open(target_file, "a") as f:
            f.write(config_line)
        print(f"✅ 已将 /usr/bin/fastfetch | lolcat 写入 {target_file}")
        return True
    except PermissionError:
        print(f"❌ 无权限写入 {target_file}，请以 root 运行")
        return False

def main():
    """主函数"""
    if not is_root():
        print("❌ 请以 root 权限运行（sudo python3 脚本名.py）")
        sys.exit(1)
    
    # 检测系统信息
    os_info = detect_os_info()
    if not os_info["distro"]:
        print("❌ 无法检测系统发行版")
        sys.exit(1)
    print(f"📌 检测到系统：{os_info['distro']} {os_info['version']}")
    
    # 检测包管理器
    pm = detect_package_manager()
    
    # 1. 安装 lolcat
    if not check_installed("lolcat"):
        if not install_lolcat(pm):
            sys.exit(1)
    else:
        print("✅ lolcat 已安装")
    
    # 2. 安装 fastfetch
    if not check_installed("fastfetch"):
        print("📦 fastfetch 未安装，开始安装...")
        install_success = False
        
        # 处理 Ubuntu/Debian
        if os_info["distro"] in ["ubuntu", "debian"]:
            install_success = install_fastfetch_ubuntu_debian(os_info)
        # 其他发行版
        else:
            install_success = install_fastfetch_other(pm)
        
        if not install_success:
            print("❌ fastfetch 安装失败，请参考官方文档手动安装")
            sys.exit(1)
    else:
        print("✅ fastfetch 已安装")
    
    # 3. 配置自动执行
    add_to_profile()
    
    # 验证
    if check_installed("fastfetch") and check_installed("lolcat"):
        print("\n🎉 安装完成！")
        print("📌 生效方式：重启终端 或 执行 source /etc/profile (bash) / source ~/.zshrc (zsh)")
    else:
        print("\n❌ 安装未完全成功")

if __name__ == "__main__":
    main()
