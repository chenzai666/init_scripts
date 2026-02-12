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

# 从源码编译安装Lolcat
def install_lolcat_from_source():
    print("\n正在从源码安装Lolcat...")
    
    # 创建临时工作目录
    work_dir = tempfile.mkdtemp(prefix="lolcat-build-")
    print(f"创建临时构建目录: {work_dir}")
    
    try:
        # 下载源码
        zip_url = "https://github.com/busyloop/lolcat/archive/master.zip"
        zip_path = f"{work_dir}/master.zip"
        print(f"下载Lolcat源码: {zip_url}")
        
        # 使用urllib下载
        with urllib.request.urlopen(zip_url) as response:
            with open(zip_path, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
        
        # 解压源码
        print(f"解压源码: {zip_path}")
        shutil.unpack_archive(zip_path, work_dir)
        
        # 进入源代码目录
        src_dir = glob.glob(f"{work_dir}/lolcat-*")[0]
        os.chdir(src_dir)
        
        # 安装依赖
        print("安装Lolcat依赖...")
        subprocess.run(["gem", "install", "rake"], check=True)
        
        # 编译并安装
        print("编译安装Lolcat...")
        subprocess.run(["rake", "install"], check=True)
        
        # 获取安装路径
        lolcat_path = shutil.which("lolcat")
        if not lolcat_path:
            # 尝试在gem路径中查找
            gem_path = subprocess.check_output(["gem", "env", "exec_prefix"], text=True).strip()
            lolcat_path = f"{gem_path}/bin/lolcat"
        
        print(f"Lolcat 安装成功: {lolcat_path}")
        return lolcat_path
        
    except Exception as e:
        print(f"源码安装失败: {str(e)}")
        print("尝试替代方法：直接使用gem安装到系统目录")
        os.chdir("/")
        subprocess.run(["gem", "install", "lolcat", "--no-document"], check=True)
        return shutil.which("lolcat") or "/usr/local/bin/lolcat"
        
    finally:
        # 清理工作目录
        print(f"清理构建目录: {work_dir}")
        shutil.rmtree(work_dir, ignore_errors=True)
# 查找Lolcat路径
def find_lolcat_path():
    # 标准路径
    possible_paths = [
        "/usr/bin/lolcat",
        "/usr/local/bin/lolcat",
        "/bin/lolcat",
        "/snap/bin/lolcat",
        "/usr/games/lolcat"
    ]
    
    # 用户gem路径
    home = os.path.expanduser("~")
    possible_paths.extend([
        f"{home}/.local/bin/lolcat",
        f"{home}/.gem/ruby/*/bin/lolcat",
        f"{home}/.rbenv/shims/lolcat"
    ])
    
    # 系统gem路径
    try:
        gem_path = subprocess.check_output(["gem", "env", "exec_prefix"], text=True).strip()
        possible_paths.append(f"{gem_path}/bin/lolcat")
    except:
        pass
    
    # 遍历所有可能路径
    for path in possible_paths:
        if "*" in path:
            matches = glob.glob(path)
            if matches:
                return matches[0]
        elif os.path.exists(path) and os.access(path, os.X_OK):
            return path
    
    return None
# 安装Lolcat
def install_lolcat():
    print("\n正在安装Lolcat...")
    
    # 查找现有安装路径
    existing_path = find_lolcat_path()
    if existing_path:
        print(f"Lolcat 已经安装于: {existing_path}")
        return existing_path
    
    # 尝试通过包管理器安装
    try:
        print("尝试通过系统包管理器安装lolcat...")
        os_id = detect_os()
        if os_id in ["ubuntu", "debian", "pop"]:
            subprocess.run(["apt-get", "install", "-y", "lolcat"], check=True)
        elif os_id in ["arch", "manjaro"]:
            subprocess.run(["pacman", "-S", "--noconfirm", "lolcat"], check=True)
        elif os_id in ["fedora", "centos", "rhel"]:
            subprocess.run(["dnf", "install", "-y", "lolcat"], check=True)
        elif os_id in ["opensuse"]:
            subprocess.run(["zypper", "install", "-y", "lolcat"], check=True)
        elif os_id in ["alpine"]:
            subprocess.run(["apk", "add", "lolcat"], check=True)
        
        # 检查路径
        lolcat_path = find_lolcat_path()
        if lolcat_path:
            print(f"通过包管理器安装成功: {lolcat_path}")
            return lolcat_path
        else:
            print("包管理器安装后未找到lolcat，尝试其他方法")
    except Exception as e:
        print(f"包管理器安装失败: {str(e)}")
    
    # 尝试使用gem安装
    try:
        print("尝试使用gem安装lolcat...")
        # 确保在根目录下执行，避免工作目录问题
        os.chdir("/")
        gem_env = subprocess.check_output(["gem", "env"])
        
        # 尝试不同安装方式
        for install_method in ["--user-install", ""]:
            cmd = ["gem", "install", "lolcat", "--no-document"]
            if install_method:
                cmd.append(install_method)
            
            print(f"执行: {' '.join(cmd)}")
            try:
                subprocess.run(cmd, check=True)
                print("gem安装成功")
                break
            except:
                print(f"gem安装方式 {install_method if install_method else 'system'} 失败，尝试其他方式")
        
        # 查找路径
        lolcat_path = find_lolcat_path()
        if lolcat_path:
            return lolcat_path
        else:
            print("gem安装后未找到lolcat路径")
        
    except Exception as e:
        print(f"gem安装失败: {str(e)}")
    
    # 如果上述方法都失败，使用源码安装
    print("所有其他方法失败，使用源码安装...")
    return install_lolcat_from_source()
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
            if os.path.exists(temp_path):
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
            subprocess.run([fastfetch_path, "--version"], check=True, stdout=subprocess.DEVNULL)
            print("FastFetch测试通过")
        except subprocess.CalledProcessError as e:
            print(f"FastFetch测试失败: {e.stderr.decode('utf-8') if e.stderr else '未知错误'}")
            print("提示：可能需要安装额外的依赖，尝试运行: sudo apt install libpci-dev libvulkan-dev")
            sys.exit(1)
        
        # 测试Lolcat是否能正常运行
        print("\n测试Lolcat...")
        try:
            test_cmd = f'echo "测试彩色输出" | {lolcat_path} --version'
            subprocess.run(test_cmd, shell=True, check=True)
            print("Lolcat测试通过")
        except Exception as e:
            print(f"Lolcat测试失败: {str(e)}")
            print("提示：可能需要手动配置Ruby环境")
        
        # 配置启动脚本
        configure_terminal_startup(fastfetch_path, lolcat_path)
        
        print("\n安装完成！")
        print(f"FastFetch路径: {fastfetch_path}")
        print(f"Lolcat路径: {lolcat_path}")
        print("请执行以下命令立即生效或重启终端:")
        print("  source /etc/profile")
        print("提示：可通过编辑 /etc/profile 自定义配置")
        print("卸载提示: 要卸载配置，请编辑 /etc/profile 并删除脚本添加的配置块")
    
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
