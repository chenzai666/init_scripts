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
    except Exception as e:
        print(f"❌ {description}发生意外错误: {str(e)}")
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
    try:
        v1_parts = list(map(int, version1.split(".")))
        v2_parts = list(map(int, version2.split(".")))
    except ValueError:
        return 0  # 版本号格式错误时不比较
    
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
def get_command_path(command):
    """获取命令的实际安装路径"""
    try:
        result = subprocess.run(
            ["which", command],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        if result.returncode == 0:
            return result.stdout.strip()
        
        # 如果在PATH中找不到，尝试在常见路径中搜索
        search_paths = [
            "/usr/bin", "/usr/local/bin", "/bin", "/usr/sbin", 
            "/usr/local/sbin", "/sbin", "/usr/games", "/usr/local/games"
        ]
        for path in search_paths:
            full_path = os.path.join(path, command)
            if os.path.exists(full_path):
                return full_path
        
        return None
    except Exception as e:
        print(f"❌ 获取命令路径失败: {str(e)}")
        return None
def install_lolcat_from_github():
    """从GitHub安装lolcat"""
    print("🎯 尝试从GitHub源码安装lolcat...")
    
    # 1. 安装Ruby（如果尚未安装）
    if not check_installed("ruby"):
        pm = detect_package_manager()
        ruby_pkg = "ruby-dev" if pm == "apt" else "ruby"
        
        if pm == "apt":
            run_command("apt update -y", "更新仓库")
            run_command(f"apt install -y {ruby_pkg}", "安装Ruby")
        elif pm == "dnf" or pm == "yum":
            run_command(f"{pm} install -y ruby", "安装Ruby")
        elif pm == "pacman":
            run_command("pacman -Sy --noconfirm ruby", "安装Ruby")
        elif pm == "zypper":
            run_command("zypper install -y ruby", "安装Ruby")
        elif pm == "apk":
            run_command("apk add ruby", "安装Ruby")
        
        if not check_installed("ruby"):
            print("❌ Ruby安装失败，无法继续安装lolcat")
            return None
    
    # 2. 安装gem（如果尚未安装）
    if not check_installed("gem"):
        gem_pkg = "rubygems" if detect_package_manager() == "apt" else "rubygems"
        run_command(f"{detect_package_manager()} install -y {gem_pkg}", "安装gem")
    
    # 3. 使用gem安装lolcat
    if run_command("gem install lolcat", "使用gem安装lolcat"):
        gem_path = get_command_path("lolcat")
        print(f"✅ 成功通过gem安装lolcat ({gem_path})")
        return gem_path
    
    # 4. 终极方法：直接下载lolcat脚本
    lolcat_url = "https://raw.githubusercontent.com/busyloop/lolcat/master/bin/lolcat"
    install_path = "/usr/local/bin/lolcat"
    
    try:
        print("📦 直接下载lolcat脚本...")
        # 下载脚本
        urllib.request.urlretrieve(lolcat_url, install_path)
        
        # 添加执行权限
        os.chmod(install_path, 0o755)
        print(f"✅ lolcat已安装到 {install_path}")
        
        # 检查依赖
        print("🔍 检查依赖...")
        run_command("lolcat --help > /dev/null", "测试lolcat", check=False)
        return install_path
    except Exception as e:
        print(f"❌ 下载lolcat失败: {str(e)}")
        return None
def install_lolcat(pm):
    """安装 lolcat（优先包管理器，失败时使用GitHub）"""
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
        
        result = run_command(install_cmds[pm], "使用包管理器安装 lolcat")
        if result and result.returncode == 0:
            return get_command_path("lolcat")
    
    # 包管理器安装失败，尝试GitHub安装
    print("⚠️ 包管理器安装失败，尝试GitHub方法...")
    return install_lolcat_from_github()
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
        if add_ppa and add_ppa.returncode == 0:
            run_command("apt update -y", "更新 PPA 仓库")
            install = run_command("apt install -y fastfetch", "从 PPA 安装 fastfetch")
            return install is not None and install.returncode == 0
    
    # Ubuntu 20.04+/Debian 11+：下载 deb 包安装
    arch = platform.machine()
    arch_map = {"x86_64": "amd64", "aarch64": "arm64", "armv7l": "armhf", "armv8l": "arm64"}
    deb_arch = arch_map.get(arch, arch)
    
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
        if install and install.returncode == 0:
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
        return install is not None and install.returncode == 0
    
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
        return result is not None and result.returncode == 0
    else:
        print("❌ 暂不支持当前系统自动安装 fastfetch，请手动安装")
        return False
def add_to_profile(fastfetch_path, lolcat_path):
    """将 fastfetch | lolcat 写入 profile 文件"""
    # 确保路径正确
    if not fastfetch_path or not os.path.exists(fastfetch_path):
        print(f"❌ 无法找到 fastfetch 路径: {fastfetch_path}")
        return False
    
    if not lolcat_path or not os.path.exists(lolcat_path):
        print(f"❌ 无法找到 lolcat 路径: {lolcat_path}")
        return False
    
    # 构造配置命令
    config_command = f"{fastfetch_path} | {lolcat_path}"
    
    # 配置文件模板
    config_content = f"""
# Auto-run fastfetch with lolcat (added by installer)
if [[ $- == *i* ]]; then  # Only run in interactive shells
    if command -v {fastfetch_path} >/dev/null 2>&1 && command -v {lolcat_path} >/dev/null 2>&1; then
        {config_command}
    fi
fi
"""
    
    print(f"📝 配置命令: {config_command}")
    
    # 优先用户级配置文件
    profile_files = [
        os.path.expanduser("/etc/profile"),
        os.path.expanduser("~/.zshrc"),
        os.path.expanduser("~/.bashrc"),
    ]
    
    target_file = None
    # 查找已存在的配置文件
    for pf in profile_files:
        if os.path.exists(pf):
            target_file = pf
            print(f"🔍 找到配置文件: {target_file}")
            break
    
    # 如果未找到任何配置文件，默认使用 ~/.bashrc
    if not target_file:
        target_file = os.path.expanduser("~/.bashrc")
        print(f"⚠️ 未找到配置文件，将创建新文件: {target_file}")
    
    # 检查是否已存在配置
    try:
        if os.path.exists(target_file):
            with open(target_file, "r") as f:
                content = f.read()
                if config_command in content:
                    print(f"✅ fastfetch 配置已存在于 {target_file}，无需重复写入")
                    return True
                elif "fastfetch | lolcat" in content:
                    print(f"⚠️ 检测到旧的配置，建议手动更新: {target_file}")
    except Exception as e:
        print(f"❌ 检查配置文件失败: {str(e)}")
    
    # 写入配置
    try:
        with open(target_file, "a") as f:
            f.write(config_content)
        print(f"✅ 已将配置写入 {target_file}")
        return True
    except PermissionError:
        print(f"❌ 无权限写入 {target_file}，请以 root 运行")
        print("💡 您可以手动添加以下内容到配置文件中:")
        print("-" * 60)
        print(config_content)
        print("-" * 60)
        return False
    except Exception as e:
        print(f"❌ 写入配置文件失败: {str(e)}")
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
    print(f"📦 检测到包管理器: {pm}")
    
    # 1. 安装 lolcat
    lolcat_path = None
    if not check_installed("lolcat"):
        print("📦 lolcat 未安装，开始安装...")
        lolcat_path = install_lolcat(pm)
        if not lolcat_path:
            print("❌ lolcat 安装失败，脚本终止")
            sys.exit(1)
        else:
            print(f"✅ lolcat 安装成功: {lolcat_path}")
    else:
        lolcat_path = get_command_path("lolcat")
        print(f"✅ lolcat 已安装: {lolcat_path}")
    
    # 2. 安装 fastfetch
    fastfetch_path = None
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
            fastfetch_path = get_command_path("fastfetch")
            print(f"✅ fastfetch 安装成功: {fastfetch_path}")
    else:
        fastfetch_path = get_command_path("fastfetch")
        print(f"✅ fastfetch 已安装: {fastfetch_path}")
    
    # 3. 配置自动执行
    if not fastfetch_path:
        fastfetch_path = get_command_path("fastfetch")
    if not lolcat_path:
        lolcat_path = get_command_path("lolcat")
    
    if add_to_profile(fastfetch_path, lolcat_path):
        print("✅ 配置成功写入")
    else:
        print("⚠️ 配置写入失败，可能需要手动配置")
    
    # 验证
    if fastfetch_path and lolcat_path:
        print("\n🎉 安装完成！")
        print("📌 生效方式：重启终端 或 执行 source /etc/profile (bash) / source ~/.zshrc (zsh)")
        
        # 尝试立即显示效果
        print("\n尝试显示效果（可能需要重启终端才能正常显示颜色）...")
        run_command(f"{fastfetch_path} | {lolcat_path}", "显示系统信息", check=False)
    else:
        print("\n❌ 安装未完全成功，请检查错误信息")

if __name__ == "__main__":
    main()
