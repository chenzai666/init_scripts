#!/usr/bin/env python3
import os
import subprocess
import sys
import glob
import platform
import shutil
import tempfile
import urllib.request

FASTFETCH_VERSION = os.environ.get("FASTFETCH_VERSION", "2.65.1")
MIN_SOURCE_BUILD_SPACE_MB = int(os.environ.get("FASTFETCH_MIN_SOURCE_BUILD_SPACE_MB", "900"))

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
    elif os_id.startswith("opensuse"):
        os_id = "opensuse"
    
    return os_id

# 安装依赖
def get_package_config(os_id):
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
    
    fastfetch_packages_by_os = {
        "debian": ["pciutils", "libpci-dev", "vulkan-tools", "libvulkan-dev", "wayland-protocols", "libdrm-dev"],
        "ubuntu": ["pciutils", "libpci-dev", "vulkan-tools", "libvulkan-dev", "wayland-protocols", "libdrm-dev"],
        "pop": ["pciutils", "libpci-dev", "vulkan-tools", "libvulkan-dev", "wayland-protocols", "libdrm-dev"],
        "kali": ["pciutils", "libpci-dev", "vulkan-tools", "libvulkan-dev", "wayland-protocols", "libdrm-dev"],
        "arch": ["pciutils", "vulkan-tools", "vulkan-headers", "wayland-protocols", "libdrm"],
        "manjaro": ["pciutils", "vulkan-tools", "vulkan-headers", "wayland-protocols", "libdrm"],
        "fedora": ["pciutils", "pciutils-devel", "vulkan-tools", "vulkan-headers", "vulkan-loader-devel", "wayland-protocols-devel", "libdrm-devel"],
        "centos": ["pciutils", "pciutils-devel", "vulkan-tools", "vulkan-headers", "vulkan-loader-devel", "wayland-protocols-devel", "libdrm-devel"],
        "rhel": ["pciutils", "pciutils-devel", "vulkan-tools", "vulkan-headers", "vulkan-loader-devel", "wayland-protocols-devel", "libdrm-devel"],
        "opensuse": ["pciutils", "pciutils-devel", "vulkan-tools", "vulkan-headers", "vulkan-devel", "wayland-protocols-devel", "libdrm-devel"],
        "alpine": ["pciutils", "pciutils-dev", "vulkan-tools", "vulkan-headers", "vulkan-loader-dev", "wayland-protocols", "libdrm-dev"]
    }

    lolcat_packages_by_os = {
        "debian": ["rubygems"],
        "ubuntu": ["rubygems"],
        "pop": ["rubygems"],
        "kali": ["rubygems"],
        "arch": ["ruby"],
        "manjaro": ["ruby"],
        "fedora": ["rubygems"],
        "centos": ["rubygems"],
        "rhel": ["rubygems"],
        "opensuse": ["ruby"],
        "alpine": ["ruby", "ruby-dev", "ruby-rake"]
    }

    return package_managers, {
        "base": ["curl"],
        "build": ["git"] + compiler_packages.get(os_id, []),
        "fastfetch": fastfetch_packages_by_os.get(os_id, []),
        "lolcat": lolcat_packages_by_os.get(os_id, [])
    }

def run_package_install(os_id, packages, label):
    package_managers, _ = get_package_config(os_id)
    # 选择正确的包管理器
    if os_id not in package_managers:
        print(f"不支持的发行版: {os_id}")
        sys.exit(1)

    if not packages:
        return

    cmd = package_managers[os_id]
    package_text = " ".join(packages)
    print(f"安装{label}: {package_text}")
    subprocess.run(f"{cmd} {package_text}".split(), check=True, stderr=subprocess.PIPE)

def install_packages(os_id):
    _, packages = get_package_config(os_id)
    run_package_install(os_id, packages["base"], "基础依赖")

    # 安装Lolcat依赖
    if packages['lolcat']:
        run_package_install(os_id, packages["lolcat"], "Lolcat依赖")

def install_build_dependencies(os_id):
    _, packages = get_package_config(os_id)
    run_package_install(os_id, packages["build"], "编译工具")
    run_package_install(os_id, packages["fastfetch"], "FastFetch编译依赖")

def get_free_space_mb(path="/"):
    usage = shutil.disk_usage(path)
    return usage.free // (1024 * 1024)

def normalize_fastfetch_arch():
    machine = platform.machine().lower()
    arch_map = {
        "x86_64": "amd64",
        "amd64": "amd64",
        "aarch64": "aarch64",
        "arm64": "aarch64",
        "i386": "i686",
        "i486": "i686",
        "i586": "i686",
        "i686": "i686",
        "armv6l": "armv6l",
        "armv7l": "armv7l",
        "ppc64le": "ppc64le",
        "riscv64": "riscv64",
        "s390x": "s390x",
    }
    return arch_map.get(machine)

def get_fastfetch_binary_asset(os_id):
    arch = normalize_fastfetch_arch()
    if not arch:
        return None

    # Alpine 使用 musl，官方目前只提供 amd64 的 musl 预编译包。
    if os_id == "alpine":
        if arch == "amd64":
            return f"fastfetch-musl-{arch}.tar.gz"
        return None

    return f"fastfetch-linux-{arch}.tar.gz"

def install_fastfetch_from_release(os_id):
    asset = get_fastfetch_binary_asset(os_id)
    if not asset:
        print("当前系统架构没有匹配的FastFetch预编译包，准备尝试源码编译")
        return None

    version = FASTFETCH_VERSION
    url = f"https://github.com/fastfetch-cli/fastfetch/releases/download/{version}/{asset}"
    work_dir = tempfile.mkdtemp(prefix="fastfetch-release-")
    archive_path = os.path.join(work_dir, asset)

    try:
        print(f"尝试安装FastFetch官方预编译包: {asset}")
        print(f"下载: {url}")
        urllib.request.urlretrieve(url, archive_path)

        print(f"解压: {archive_path}")
        shutil.unpack_archive(archive_path, work_dir)
        extracted_dirs = [
            os.path.join(work_dir, name)
            for name in os.listdir(work_dir)
            if os.path.isdir(os.path.join(work_dir, name))
        ]
        if not extracted_dirs:
            raise RuntimeError("预编译包解压后未找到目录")

        src_usr = os.path.join(extracted_dirs[0], "usr")
        if not os.path.isdir(src_usr):
            raise RuntimeError("预编译包中未找到 usr 目录")

        print("安装FastFetch预编译文件到 /usr")
        shutil.copytree(src_usr, "/usr", dirs_exist_ok=True)

        fastfetch_path = shutil.which("fastfetch") or "/usr/bin/fastfetch"
        if not os.path.exists(fastfetch_path):
            raise RuntimeError("预编译包安装后未找到 fastfetch")

        print(f"FastFetch 预编译包安装成功: {fastfetch_path}")
        return fastfetch_path
    except Exception as e:
        print(f"预编译包安装失败: {str(e)}")
        return None
    finally:
        print(f"清理预编译包临时目录: {work_dir}")
        shutil.rmtree(work_dir, ignore_errors=True)

# 编译安装FastFetch
def install_fastfetch_from_source(os_id):
    print("\n正在安装FastFetch...")

    free_mb = get_free_space_mb("/")
    if free_mb < MIN_SOURCE_BUILD_SPACE_MB:
        print(f"错误：当前根分区可用空间约 {free_mb} MB，不建议源码编译FastFetch")
        print(f"源码编译至少预留约 {MIN_SOURCE_BUILD_SPACE_MB} MB；小盘LXC请优先使用官方预编译包")
        sys.exit(1)

    install_build_dependencies(os_id)

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
        fastfetch_version = FASTFETCH_VERSION
        clone_cmd = ["git", "clone", "--depth", "1", "--branch", fastfetch_version, repo_url, f"{work_dir}/fastfetch"]
        print(f"克隆仓库: {' '.join(clone_cmd)}")
        subprocess.run(clone_cmd, check=True, stderr=subprocess.PIPE)
        
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

def install_fastfetch(os_id):
    print("\n正在安装FastFetch...")

    # 查找现有安装路径
    existing_path = shutil.which("fastfetch")
    if existing_path:
        print(f"FastFetch 已经安装于: {existing_path}")
        return existing_path

    install_method = os.environ.get("FASTFETCH_INSTALL_METHOD", "auto").lower()
    if install_method not in ("auto", "binary", "source"):
        print(f"错误：FASTFETCH_INSTALL_METHOD 不支持: {install_method}")
        sys.exit(1)

    if install_method in ("auto", "binary"):
        fastfetch_path = install_fastfetch_from_release(os_id)
        if fastfetch_path:
            return fastfetch_path
        if install_method == "binary":
            print("错误：已指定只使用预编译包安装，但安装失败")
            sys.exit(1)

    return install_fastfetch_from_source(os_id)

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
            lolcat_path = find_lolcat_path()
        
        print(f"Lolcat 安装成功: {lolcat_path}")
        return lolcat_path
        
    except Exception as e:
        print(f"源码安装失败: {str(e)}")
        print("尝试替代方法：直接使用gem安装到系统目录")
        os.chdir("/")
        subprocess.run(["gem", "install", "lolcat", "--no-document"], check=True)
        return find_lolcat_path() or "/usr/local/bin/lolcat"
        
    finally:
        # 清理工作目录
        print(f"清理构建目录: {work_dir}")
        shutil.rmtree(work_dir, ignore_errors=True)
# 查找Lolcat路径（优化版）
def find_lolcat_path():
    """更健壮的Lolcat路径查找方法"""
    # 1. 首先尝试标准路径查找
    lolcat_path = shutil.which("lolcat")
    if lolcat_path:
        return lolcat_path
    
    # 2. 常见系统路径
    common_paths = [
        "/usr/bin/lolcat",
        "/usr/bin/lolcat*",
        "/usr/local/bin/lolcat",
        "/usr/games/lolcat",  # Debian特有路径
        "/snap/bin/lolcat",
        "/opt/homebrew/bin/lolcat",  # macOS
        "/home/linuxbrew/.linuxbrew/bin/lolcat"  # Linuxbrew
    ]
    
    for path in common_paths:
        if "*" in path:
            matches = glob.glob(path)
            for match in matches:
                if os.path.exists(match) and os.access(match, os.X_OK):
                    return match
        elif os.path.exists(path) and os.access(path, os.X_OK):
            return path
    
    # 3. 尝试Ruby gem路径
    try:
        # 使用更可靠的gem路径查找方法
        gem_path = subprocess.check_output(
            ["gem", "environment", "gempath"],
            text=True,
            stderr=subprocess.DEVNULL
        ).split(":")[0].strip()
        gem_bindir = subprocess.check_output(
            ["gem", "environment", "bindir"],
            text=True,
            stderr=subprocess.DEVNULL
        ).strip()
        
        possible_paths = [
            f"{gem_bindir}/lolcat",
            f"{gem_bindir}/lolcat*",
            f"{gem_path}/bin/lolcat",
            f"{gem_path}/bin/lolcat*",
            f"{gem_path}/gems/lolcat-*/bin/lolcat"
        ]
        
        for path in possible_paths:
            if "*" in path:
                matches = glob.glob(path)
                if matches:
                    return matches[0]
            elif os.path.exists(path) and os.access(path, os.X_OK):
                return path
    
    except Exception:
        pass  # 忽略错误
    
    # 4. 尝试用户gem路径
    home = os.environ.get("HOME", "/root")
    user_paths = [
        f"{home}/.local/bin/lolcat",
        f"{home}/.gem/ruby/*/bin/lolcat",
        f"{home}/.rbenv/shims/lolcat"
    ]
    
    for path in user_paths:
        if "*" in path:
            matches = glob.glob(path)
            if matches:
                return matches[0]
        elif os.path.exists(path) and os.access(path, os.X_OK):
            return path
    
    return None
# 安装Lolcat（优化版）
def install_lolcat():
    print("\n正在安装Lolcat...")
    
    # 查找现有安装路径
    lolcat_path = find_lolcat_path()
    if lolcat_path:
        print(f"Lolcat 已经安装于: {lolcat_path}")
        return lolcat_path
    
    # 尝试通过包管理器安装
    try:
        print("尝试通过系统包管理器安装lolcat...")
        os_id = detect_os()
        package_name = {
            "debian": "lolcat",
            "ubuntu": "lolcat",
            "pop": "lolcat",
            "arch": "lolcat",
            "manjaro": "lolcat",
            "fedora": "lolcat",
            "centos": "lolcat-c",
            "rhel": "lolcat-c",
            "opensuse": "rubygem-lolcat",
            "alpine": None
        }.get(os_id, "lolcat")

        if not package_name:
            raise RuntimeError(f"{os_id} 没有可用的系统 lolcat 包，尝试使用 gem 安装")
        
        if os_id in ["ubuntu", "debian", "pop", "kali"]:
            subprocess.run(["apt-get", "install", "-y", package_name], check=True)
        elif os_id in ["arch", "manjaro"]:
            subprocess.run(["pacman", "-S", "--noconfirm", package_name], check=True)
        elif os_id == "fedora":
            subprocess.run(["dnf", "install", "-y", package_name], check=True)
        elif os_id in ["centos", "rhel"]:
            rpm_pm = "dnf" if shutil.which("dnf") else "yum"
            subprocess.run([rpm_pm, "install", "-y", package_name], check=True)
        elif os_id in ["opensuse"]:
            subprocess.run(["zypper", "install", "-y", package_name], check=True)
        elif os_id in ["alpine"]:
            subprocess.run(["apk", "add", package_name], check=True)
        
        # 检查路径
        lolcat_path = find_lolcat_path()
        if lolcat_path:
            print(f"通过包管理器安装成功: {lolcat_path}")
            return lolcat_path
        else:
            print("包管理器安装后未找到lolcat，尝试其他方法")
    except Exception as e:
        print(f"包管理器安装失败: {str(e)}")
    
    # 尝试使用gem安装（优化版）
    try:
        print("尝试使用gem安装lolcat...")
        os.chdir("/")  # 避免工作目录问题
        
        # 尝试两种安装方式
        for install_method in ["", "--user-install"]:
            cmd = ["gem", "install", "lolcat", "--no-document"]
            if install_method:
                cmd.append(install_method)
            
            print(f"执行: {' '.join(cmd)}")
            try:
                subprocess.run(cmd, check=True)
                print("gem安装成功")
                break
            except Exception as e:
                print(f"尝试失败: {str(e)}")
                
        # 查找路径
        lolcat_path = find_lolcat_path()
        if lolcat_path:
            return lolcat_path
        else:
            print("gem安装后未找到lolcat路径")
        
    except Exception as e:
        print(f"gem安装失败: {str(e)}")
    
    # 如果上述方法都失败，使用源码安装
    print("所有方法失败，使用源码安装...")
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
    removed = remove_old_config()
    
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
        fastfetch_path = install_fastfetch(os_id)
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
            subprocess.run([lolcat_path, "--version"], check=True)
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
        
        failed_cmd = " ".join(e.cmd) if isinstance(e.cmd, (list, tuple)) else str(e.cmd)
        if "git clone" in failed_cmd:
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
