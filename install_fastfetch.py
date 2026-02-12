#!/usr/bin/env python3
import os
import subprocess
import sys
import platform
import shutil
import tempfile
from pathlib import Path

# 检查root权限
def check_root():
    if os.geteuid() != 0:
        print("错误：请使用sudo或以root用户运行此脚本")
        sys.exit(1)

# 检测系统类型
def detect_os():
    os_id = ""
    try:
        with open("/etc/os-release", "r") as f:
            for line in f:
                if line.startswith("ID="):
                    os_id = line.split("=")[1].strip().strip('"')
                    break
    except FileNotFoundError:
        pass
    
    # 特殊处理Ubuntu衍生版
    if os_id == "ubuntu":
        if "pop" in platform.release().lower():
            os_id = "pop"
    
    return os_id

# 安装依赖
def install_packages(os_id):
    package_managers = {
        "debian": "apt-get install -y",
        "ubuntu": "apt-get install -y",
        "pop": "apt-get install -y",
        "kali": "apt-get install -y",
        "arch": "pacman -S --noconfirm",
        "manjaro": "pacman -S --noconfirm",
        "fedora": "dnf install -y",
        "centos": "yum install -y",
        "rhel": "yum install -y",
        "opensuse": "zypper install -y",
        "alpine": "apk add"
    }
    
    # 编译器包名根据系统调整
    compiler_packages = {
        "debian": ["gcc", "g++", "make", "cmake", "pkgconf"],
        "ubuntu": ["gcc", "g++", "make", "cmake", "pkg-config"],
        "pop": ["gcc", "g++", "make", "cmake", "pkg-config"],
        "kali": ["gcc", "g++", "make", "cmake", "pkg-config"],
        "arch": ["base-devel", "cmake"],
        "manjaro": ["base-devel", "cmake"],
        "fedora": ["gcc", "gcc-c++", "make", "cmake", "pkgconf"],
        "centos": ["gcc", "gcc-c++", "make", "cmake", "pkgconf"],
        "rhel": ["gcc", "gcc-c++", "make", "cmake", "pkgconf"],
        "opensuse": ["gcc", "gcc-c++", "make", "cmake", "pkgconf"],
        "alpine": ["build-base", "cmake", "pkgconf"]
    }
    
    packages = {
        "base": ["curl", "git"] + compiler_packages.get(os_id, []),
        "fastfetch": ["pciutils", "vulkan-tools", "wayland-protocols"],
        "lolcat": ["rubygems"]
    }

    # 选择正确的包管理器
    if os_id not in package_managers:
        print(f"不支持的发行版: {os_id}")
        sys.exit(1)
    
    cmd = package_managers[os_id]
    
    # 安装基础依赖
    base_packages = " ".join(packages['base'])
    print(f"安装基础依赖: {base_packages}")
    subprocess.run(f"{cmd} {base_packages}".split(), check=True, stderr=subprocess.PIPE)
    
    # 安装FastFetch依赖
    fastfetch_packages = " ".join(packages['fastfetch'])
    print(f"安装FastFetch依赖: {fastfetch_packages}")
    subprocess.run(f"{cmd} {fastfetch_packages}".split(), check=True, stderr=subprocess.PIPE)

# 编译安装FastFetch
def install_fastfetch():
    print("\n正在安装FastFetch...")
    
    # 查找现有安装路径
    existing_path = shutil.which("fastfetch")
    if existing_path:
        print(f"FastFetch 已经安装于: {existing_path}")
        return existing_path
    
    # 检查编译环境
    if not shutil.which("g++") or not shutil.which("cmake"):
        print("错误：缺少必要的编译工具 (g++ 或 cmake)")
        sys.exit(1)
    
    # 创建临时工作目录
    work_dir = tempfile.mkdtemp(prefix="fastfetch-build-")
    print(f"创建临时构建目录: {work_dir}")
    
    try:
        # 清理可能存在的旧目录
        if os.path.exists("/tmp/fastfetch"):
            print("清理旧构建目录: /tmp/fastfetch")
            shutil.rmtree("/tmp/fastfetch", ignore_errors=True)
        
        # 克隆仓库
        repo_url = "https://github.com/fastfetch-cli/fastfetch.git"
        clone_cmd = f"git clone --depth 1 {repo_url} {work_dir}/fastfetch"
        print(f"克隆仓库: {clone_cmd}")
        subprocess.run(clone_cmd.split(), check=True, stderr=subprocess.PIPE)
        
        # 编译安装
        os.chdir(f"{work_dir}/fastfetch")
        build_dir = f"{work_dir}/fastfetch/build"
        os.makedirs(build_dir, exist_ok=True)
        os.chdir(build_dir)
        
        # 添加编译选项
        install_prefix = "/usr"  # 标准安装路径
        cmake_cmd = ["cmake", "..", "-DCMAKE_BUILD_TYPE=Release", f"-DCMAKE_INSTALL_PREFIX={install_prefix}"]
        print(f"运行CMake: {' '.join(cmake_cmd)}")
        subprocess.run(cmake_cmd, check=True, stderr=subprocess.PIPE)
        
        # 使用并行编译加速
        cpu_count = os.cpu_count() or 1
        make_cmd = ["make", "-j", str(cpu_count)]
        print(f"编译FastFetch: {' '.join(make_cmd)}")
        subprocess.run(make_cmd, check=True, stderr=subprocess.PIPE)
        
        # 安装
        install_cmd = ["make", "install"]
        print(f"安装FastFetch: {' '.join(install_cmd)}")
        subprocess.run(install_cmd, check=True, stderr=subprocess.PIPE)
        
        # 获取安装路径
        fastfetch_path = shutil.which("fastfetch") or f"{install_prefix}/bin/fastfetch"
        print(f"FastFetch 安装成功: {fastfetch_path}")
        return fastfetch_path
        
    finally:
        # 清理工作目录
        print(f"清理构建目录: {work_dir}")
        shutil.rmtree(work_dir, ignore_errors=True)

# 安装Lolcat
def install_lolcat():
    print("\n正在安装Lolcat...")
    
    # 查找现有安装路径
    existing_path = shutil.which("lolcat")
    if existing_path:
        print(f"Lolcat 已经安装于: {existing_path}")
        return existing_path
    
    # 检查Ruby是否已安装
    try:
        subprocess.run(["which", "ruby"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("Ruby 已安装")
    except:
        os_id = detect_os()
        print(f"安装 Ruby ({os_id})")
        package_managers = {
            "debian": "apt-get install -y ruby-full",
            "ubuntu": "apt-get install -y ruby-full",
            "pop": "apt-get install -y ruby-full",
            "kali": "apt-get install -y ruby-full",
            "arch": "pacman -S --noconfirm ruby",
            "manjaro": "pacman -S --noconfirm ruby",
            "fedora": "dnf install -y ruby",
            "centos": "yum install -y ruby",
            "rhel": "yum install -y ruby",
            "opensuse": "zypper install -y ruby",
            "alpine": "apk add ruby"
        }
        
        if os_id in package_managers:
            subprocess.run(package_managers[os_id].split(), check=True, stderr=subprocess.PIPE)
        else:
            print("错误：无法安装Ruby，请手动安装后再运行脚本")
            sys.exit(1)
    
    # 使用gem安装
    print("使用 gem 安装 Lolcat")
    subprocess.run(["gem", "install", "lolcat", "--no-document"], check=True, stderr=subprocess.PIPE)
    
    # 获取gem安装路径
    gem_env = subprocess.check_output(["gem", "env"], universal_newlines=True, stderr=subprocess.DEVNULL)
    gem_path = None
    for line in gem_env.splitlines():
        if "EXECUTABLE DIRECTORY" in line:
            gem_path = line.split(":")[1].strip()
            break
    
    lolcat_path = None
    if gem_path:
        lolcat_path = os.path.join(gem_path, "lolcat")
        if os.path.exists(lolcat_path):
            print(f"找到 Lolcat: {lolcat_path}")
    
    # 添加到PATH（如果gem bin目录不在PATH中）
    if gem_path and gem_path not in os.environ["PATH"]:
        print(f"添加 gem 路径到系统 PATH: {gem_path}")
        with open("/etc/profile.d/gem_path.sh", "w") as f:
            f.write(f'export PATH="$PATH:{gem_path}"\n')
        os.chmod("/etc/profile.d/gem_path.sh", 0o755)
        # 立即更新当前环境
        os.environ["PATH"] += f":{gem_path}"
    
    # 获取安装路径
    if not lolcat_path:
        lolcat_path = shutil.which("lolcat")
    
    if not lolcat_path:
        print("错误：无法找到 Lolcat 安装路径")
        sys.exit(1)
    
    print(f"Lolcat 安装成功: {lolcat_path}")
    return lolcat_path

# 清理旧的失效配置
def remove_old_config():
    config_path = "/etc/profile"
    backup_path = "/etc/profile.bak"
    marker_start = "# ==== 由FastFetch安装脚本添加 ===="
    marker_end = "# ==== 结束FastFetch配置 ===="
    
    # 创建备份
    if not os.path.exists(backup_path):
        shutil.copy(config_path, backup_path)
        print(f"已创建备份: {backup_path}")
    
    # 检测并移除旧配置
    temp_path = "/etc/profile.tmp"
    in_old_block = False
    old_config_found = False
    
    try:
        with open(config_path, "r") as infile, open(temp_path, "w") as outfile:
            for line in infile:
                # 检测开始标记
                if marker_start in line:
                    in_old_block = True
                    old_config_found = True
                    print("检测到旧的FastFetch配置块，正在清理...")
                    continue
                
                # 检测结束标记
                if marker_end in line:
                    in_old_block = False
                    continue
                
                # 跳过旧配置块内的所有内容
                if in_old_block:
                    continue
                
                # 写入非旧配置块的内容
                outfile.write(line)
        
        # 如果有旧配置被移除，替换原始文件
        if old_config_found:
            shutil.move(temp_path, config_path)
            print(f"已移除旧的FastFetch配置块")
            return True
        else:
            print("未检测到旧的FastFetch配置块")
            os.remove(temp_path)
            return False
            
    except Exception as e:
        print(f"清理旧配置时出错: {str(e)}")
        # 确保删除临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return False
# 配置终端启动脚本
def configure_terminal_startup(fastfetch_path, lolcat_path):
    # 清理旧配置
    remove_old_config()
    
    # 使用绝对路径创建命令
    config_command = f'{fastfetch_path} | {lolcat_path} -f || true'
    
    # 检查命令是否已存在
    with open("/etc/profile", "r") as f:
        content = f.read()
        if config_command in content:
            print("\n配置已存在，跳过写入")
            return
    
    print("\n配置终端启动脚本...")
    print(f"使用绝对路径: FastFetch -> {fastfetch_path}, Lolcat -> {lolcat_path}")
    
    # 定义新的配置块
    config_block = f"""
# ==== 由FastFetch安装脚本添加 ====
# 系统启动时显示彩色系统信息
# 注意：fastfetch默认会显示系统信息，无需特殊参数
{config_command}
# ==== 结束FastFetch配置 ===="""
    
    # 追加配置
    with open("/etc/profile", "a") as f:
        f.write(config_block)
    
    print("配置已写入 /etc/profile")
def main():
    try:
        check_root()
        os_id = detect_os()
        
        print(f"检测到系统: {os_id.capitalize()}")
        print("安装依赖...")
        install_packages(os_id)
        
        # 安装并获取二进制路径
        fastfetch_path = install_fastfetch()
        lolcat_path = install_lolcat()
        
        # 验证路径有效性
        if not fastfetch_path or not os.access(fastfetch_path, os.X_OK):
            print(f"错误: FastFetch不可执行: {fastfetch_path}")
            sys.exit(1)
            
        if not lolcat_path or not os.access(lolcat_path, os.X_OK):
            print(f"错误: Lolcat不可执行: {lolcat_path}")
            sys.exit(1)
        
        # 测试FastFetch是否能正常运行
        print("\n测试FastFetch...")
        try:
            subprocess.run([fastfetch_path], check=True, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL)
            print("FastFetch测试通过")
        except subprocess.CalledProcessError as e:
            print(f"FastFetch测试失败: {e.stderr.decode('utf-8') if e.stderr else '未知错误'}")
            print("提示：可能需要安装额外的依赖，尝试运行: sudo apt install libpci-dev libvulkan-dev")
            sys.exit(1)
        
        # 配置启动脚本
        configure_terminal_startup(fastfetch_path, lolcat_path)
        
        print("\n安装完成！")
        print(f"FastFetch路径: {fastfetch_path}")
        print(f"Lolcat路径: {lolcat_path}")
        print("请执行以下命令立即生效或重启终端:")
        print("  source /etc/profile")
        print("提示：可通过编辑 /etc/profile 自定义配置")
    
    except subprocess.CalledProcessError as e:
        print(f"\n错误：命令执行失败: {e.cmd}")
        print(f"返回代码: {e.returncode}")
        print(f"错误输出: {e.stderr.decode('utf-8') if e.stderr else '无'}")
        
        if "git clone" in " ".join(e.cmd):
            print("\n解决方法:")
            print("1. 手动清理临时目录: sudo rm -rf /tmp/fastfetch*")
            print("2. 检查网络连接是否正常")
            print("3. 重新运行安装脚本")
        
        sys.exit(1)
    except Exception as e:
        print(f"\n发生未知错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
if __name__ == "__main__":
    main()
