#!/bin/bash
set -euo pipefail

#source /etc/init.d/functions
blue(){
    echo -e "\033[34m\033[01m$1\033[0m"
}
green(){
    echo -e "\033[32m\033[01m$1\033[0m"
}
yellow(){
    echo -e "\033[33m\033[01m$1\033[0m"
}
red(){
    echo -e "\033[31m\033[01m$1\033[0m"
}
#永久关闭防火墙
disable_firewalld_selinux () {
	systemctl stop firewalld
    systemctl disable --now firewalld
    setenforce 0
    sed -i "s/^SELINUX=enforcing/SELINUX=disabled/g" /etc/selinux/config
}
#网卡更名为eth0
change_Centos_networkname(){
#cd /etc/sysconfig/network-scripts/
#x=0
#i=1
#for netCardName in `cat /proc/net/dev | awk '{i++; if(i>2){print$1}}' | sed 's/^[\t]*//g' | sed 's/[:]*$//g' | egrep -v "lo|docker"`;
#do
#	if [ -f ifcfg-${netCardName} ] && [ ! -f ifcfg-eth${x} ]; then
#		mv ifcfg-${netCardName} ifcfg-eth${x}
#		sed -i "s/${netCardName}/eth${x}/g" ifcfg-eth${x}
#		sed -i 's/ONBOOT=no/ONBOOT=yes/g' ifcfg-eth${x}
#	fi
#done
# 获取所有网卡接口
#interfaces=$(ip link show | awk -F':' '/^[0-9]+/{print $2}' | egrep -v "lo|docker")
# 定义接口计数器 
#count=0
# 遍历所有接口
#for interface in $interfaces; do
  # 获取接口MAC地址
#  mac=$(ip link show $interface | awk '/link\/ether/ {print $2}')  
  # 生成新的接口名  
#  new_name="eth"$count
  # 重命名接口
#  ip link set $interface name $new_name
  # 将规则写入配置文件
#  echo "SUBSYSTEM=="net", ACTION=="add", ATTR{address}=="$mac", NAME="$new_name"" >> /etc/udev/rules.d/75-network.rules
  # 计数器加1
#  count=$((count+1)) 
#done
# 重载规则
#udevadm control --reload-rules
cat >> /etc/default/grub << EOF
GRUB_CMDLINE_LINUX="crashkernel=auto rhgb quiet net.ifnames=0 biosdevname=0"
EOF
grub2-mkconfig -o /boot/grub2/grub.cfg
cd /etc/sysconfig/network-scripts/
mv ifcfg-ens192 ifcfg-eth0
sed -i 's/ens192/eth0/g' ifcfg-eth0
systemctl restart network
}


#配置邮箱告警
set_postfix(){
source /etc/init.d/functions
rpm -q postfix mailx &> /dev/null ||yum -y install postfix mailx &> /dev/null
cat > /etc/mail.rc <<EOF
set from=18827262495@163.com
set smtp=smtp.163.com
set smtp-auth-user=18827262495@163.com
set smtp-auth-password=FNIYSDOEMBBMWXWR
EOF
systemctl restart postfix
if [ $? -eq 0 ];then
	green "postfix 服务重启成功!"
else
	red "postfix 服务重启失败!"
fi
echo  "init sucess" chenzai | mail -s " test" 18827262495@163.com
}

#设置 ssh 服务端口并开启 root 可以远程登录

set_ssh_port_rootlogin () {
	source /etc/init.d/functions
    read -p "请输入ssh端口号: " port
    cp -a /etc/ssh/sshd_config /etc/ssh/sshd_config.bak
    echo Port $port >> /etc/ssh/sshd_config
    echo PermitRootLogin yes >> /etc/ssh/sshd_config
    systemctl restart sshd
    if [ $? -eq 0 ];then
        green "SSH 服务重启成功"
    else
        red "SSH 服务重启失败"
    fi
}

#制作光盘yum源和阿里云、epel源
#centos6配置yum源
centos6_make_yum_repo () {
cd /etc/yum.repos.d/
if [ -d /etc/yum.repos.d/bak ]; then
    red "bak 目录已存在!"
 else
    mkdir -p /etc/yum.repos.d/bak
	green "bak 目录已创建!"
fi
mv *.repo bak
curl -o /etc/yum.repos.d/CentOS-Base.repo https://mirrors.aliyun.com/repo/Centos-vault-6.10.repo
rpm -q epel-release &> /dev/null ||yum install -y epel-release &> /dev/null
#cat > local.repo << EOF
#[local]
#name=local repo
#baseurl=file:///iso
#enabled=1
#gpgcheck=0
#EOF
yum clean all
yum makecache fast
#if [ -d /iso ];then
#	echo "iso 目录已存在!"
# else
#	mkdir /iso
#	echo "iso 目录已创建!"
#fi
#mount /dev/sr0 /iso
#echo "/dev/sr0 /iso iso9660 defaults 0 0" >> /etc/fstab
}
#centos7配置yum源
centos7_make_yum_repo (){
cd /etc/yum.repos.d/
if [ -d /etc/yum.repos.d/bak ]; then
    red "bak 目录已存在!"
 else
    mkdir -p /etc/yum.repos.d/bak
	green "bak 目录已创建!"
fi
mv *.repo bak
curl -o /etc/yum.repos.d/CentOS-Base.repo https://repo.huaweicloud.com/repository/conf/CentOS-7-reg.repo 
rpm -q epel-release &> /dev/null || yum install -y epel-release &> /dev/null
#cat > local.repo << EOF
#[local]
#name=local repo
#baseurl=file:///iso
#enabled=1
#gpgcheck=0
#EOF
yum clean all
yum makecache fast
#if [ -d /iso ];then
#	echo "iso 目录已存在!"
# else
#	mkdir /iso
#	echo "iso 目录已创建!"
#fi
#mount /dev/sr0 /iso
#echo "/dev/sr0 /iso iso9660 defaults 0 0" >> /etc/fstab
}
#Rocky8配置yum源
Rocky8_make_yum_repo (){
sed -e 's|^mirrorlist=|#mirrorlist=|g' \
    -e 's|^#baseurl=http://dl.rockylinux.org/$contentdir|baseurl=https://mirrors.aliyun.com/rockylinux|g' \
    -i.bak \
    /etc/yum.repos.d/Rocky-*.repo
#cat > local.repo << EOF
#[BaseOS]
#name=BaseOS
#baseurl=file:///iso/BaseOS
#enabled=1
#gpgcheck=0

#[AppStream]
#name=AppStream
#baseurl=file:///iso/AppStream
#enabled=1
#gpgcheck=0
#EOF
dnf clean all
dnf makecache fast
}
#Ubuntu18配置yum源
Ubuntu18_make_yum_repo (){
cat > /etc/apt/source.list << EOF
deb https://repo.huaweicloud.com/ubuntu/ bionic main restricted universe multiverse
deb-src https://repo.huaweicloud.com/ubuntu/ bionic main restricted universe multiverse

deb https://repo.huaweicloud.com/ubuntu/ bionic-security main restricted universe multiverse
deb-src https://repo.huaweicloud.com/ubuntu/ bionic-security main restricted universe multiverse

deb https://repo.huaweicloud.com/ubuntu/ bionic-updates main restricted universe multiverse
deb-src https://repo.huaweicloud.com/ubuntu/ bionic-updates main restricted universe multiverse

# deb https://repo.huaweicloud.com/ubuntu/ bionic-proposed main restricted universe multiverse
# deb-src https://repo.huaweicloud.com/ubuntu/ bionic-proposed main restricted universe multiverse

deb https://repo.huaweicloud.com/ubuntu/ bionic-backports main restricted universe multiverse
deb-src https://repo.huaweicloud.com/ubuntu/ bionic-backports main restricted universe multiverse
EOF
}
#Ubuntu20配置yum源
Ubuntu20_make_yum_repo () {
cat > /etc/apt/source.list << EOF
deb https://repo.huaweicloud.com/ubuntu/ focal main restricted universe multiverse
deb-src https://repo.huaweicloud.com/ubuntu/ focal main restricted universe multiverse

deb https://repo.huaweicloud.com/ubuntu/ focal-security main restricted universe multiverse
deb-src https://repo.huaweicloud.com/ubuntu/ focal-security main restricted universe multiverse

deb https://repo.huaweicloud.com/ubuntu/ focal-updates main restricted universe multiverse
deb-src https://repo.huaweicloud.com/ubuntu/ focal-updates main restricted universe multiverse

# deb https://repo.huaweicloud.com/ubuntu/ focal-proposed main restricted universe multiverse
# deb-src https://repo.huaweicloud.com/ubuntu/ focal-proposed main restricted universe multiverse

deb https://repo.huaweicloud.com/ubuntu/ focal-backports main restricted universe multiverse
deb-src https://repo.huaweicloud.com/ubuntu/ focal-backports main restricted universe multiverse
EOF
}

#修改提示符颜色
#cat >> /etc/profile.d/PS1.sh <<EOF
#PS1='\[\e[31;1m\][\u@\h \w]\$\[\e[0m\]'
#EOF
set_ps1 () {
    #echo "PS1='\[\e[32;1m\][\[\e[34;1m\]\u@\[\e[1;31m\]\h \[\e[1;33m\]\w \[\e[1;32m\]]\\$ \[\e[0m\]'" > /etc/profile.d/PS1.sh
    echo "PS1='\[\e[32;1m\][\[\e[34;1m\]\u@\[\e[1;31m\]\h \[\e[1;33m\]\w \[\e[1;32m\]]\\$ \[\e[0m\]'" >> /root/.bashrc
    echo "命令提示符优化完毕,请重新登录"
}
#安装常用软件
#centos_install_package() {
#package="sudo vim curl jq lrzsz tree tmux lsof tcpdump wget net-tools iotop bc bzip2 zip unzip nfs-utils man-pages dos2unix nc telnet ntpdate bash-completion bash-completion-extras gcc make autoconf gcc-c++ glibc glibc-devel pcre pcre-devel openssl openssl-devel systemd-devel zlib-devel htop git"
#for i in $package
#do
#    rpm -q $i &>/dev/null || yum -q install -y $i
#done
#}
#ubuntu_install_package() {
#apt-get install -y sudo vim curl tree net-tools wget jq iproute2 ntpdate tcpdump telnet traceroute nfs-kernel-server nfs-common lrzsz tree openssl libssl-dev libpcre3 libpcre3-dev zlib1g-dev gcc openssh-server iotop unzip zip bzip2 htop git
#}

#debian_install_package() {
#apt install -y sudo vim curl tree net-tools wget jq iputils-ping traceroute htop lshw inxi lm-sensors unzip zip bzip2 p7zip-full unrar-free git tcpdump traceroute iotop gcc
#}

centos_install_package() {
    local packages=("sudo" "vim" "curl" "tree" "net-tools" "wget" "jq" "iproute2" "ntpdate" "tcpdump" "telnet" "traceroute" "nfs-kernel-server" "nfs-common" "lrzsz" "tree" "openssl" "libssl-dev" "libpcre3" "libpcre3-dev" "zlib1g-dev" "gcc" "openssh-server" "iotop" "unzip" "zip" "bzip2" "htop" "git") # 示例包名，请替换为实际需要的包
    # 检查包管理器
    if command -v dnf &> /dev/null; then
        pm_cmd="dnf"
    elif command -v yum &> /dev/null; then
        pm_cmd="yum"
    else
        echo "错误：找不到包管理器（dnf/yum）" >&2
        exit 1
    fi
    # 更新包缓存
    sudo $pm_cmd makecache
    
    for pkg in "${packages[@]}"; do
        # 检查包是否已安装
        if rpm -q "$pkg" &> /dev/null; then
            echo "[跳过] $pkg 已安装"
        else
            echo "[安装] $pkg..."
            sudo $pm_cmd install -y "$pkg"
        fi
    done
}
# 定义Ubuntu安装函数（独立包检测）
ubuntu_install_package() {
    local packages=("sudo" "vim" "curl" "tree" "net-tools" "wget" "jq" "bc" "netcat" "dnsutils" "iproute2" "ntpdate" "tcpdump" "telnet" "traceroute" "nfs-kernel-server" "nfs-common" "lrzsz" "tree" "openssl" "libssl-dev" "libpcre3" "libpcre3-dev" "zlib1g-dev" "gcc" "openssh-server" "iotop" "unzip" "zip" "bzip2" "htop" "git") # Ubuntu特有包
    
    # 更新包列表
    apt-get update
    
    for pkg in "${packages[@]}"; do
        # Ubuntu特有的包检测方式
        if dpkg -l "$pkg" 2>/dev/null | grep -q "^ii"; then
            echo "[跳过] $pkg - Ubuntu包已安装"
        else
            echo "[安装] $pkg - Ubuntu..."
            sudo apt-get install -y "$pkg"
        fi
    done
}
# 定义Debian安装函数（独立包检测）
debian_install_package() {
    local packages=("sudo" "vim" "curl" "tree" "net-tools" "wget" "jq" "bc" "netcat" "dnsutils" "iproute2" "iputils-ping" "traceroute" "htop" "lshw" "inxi" "lm-sensors" "unzip" "zip" "bzip2" "p7zip-full" "unrar-free" "git" "tcpdump" "iotop" "gcc") # Debian特有包
    
    # 更新包列表
    apt-get update
    
    for pkg in "${packages[@]}"; do
        # Debian专用的包检测方式
        if apt list --installed 2>/dev/null | grep -q "^$pkg/"; then
            echo "[跳过] $pkg - Debian包已安装"
        else
            echo "[安装] $pkg - Debian..."
            sudo apt-get install -y "$pkg"
        fi
    done
}


minimal_install() {
	# 系统检测部分（优化版）
if [ -f /etc/*-release ]; then
    # 优先使用现代标准
    OS_ID=$(grep -E '^ID=' /etc/*-release | cut -d= -f2 | tr -d '"' | tr '[:upper:]' '[:lower:]')
    
    # 处理CentOS变体
    if [[ "$OS_ID" == "rhel" || "$OS_ID" == "rocky" || "$OS_ID" == "almalinux" ]]; then
        OS_ID="centos"
    fi
fi
# 如果无法通过标准文件识别，使用回退方法
if [ -z "$OS_ID" ]; then
    # 回退方法：检查特定文件
    if [ -f /etc/debian_version ]; then
        if grep -q "ubuntu" /etc/issue 2>/dev/null; then
            OS_ID="ubuntu"
        else
            OS_ID="debian"
        fi
    elif [ -f /etc/centos-release ]; then
        OS_ID="centos"
    elif [ -f /etc/redhat-release ]; then
        OS_ID="centos"
    else
        # 最后尝试在所有*-release文件中搜索关键字
        if grep -q -i 'centos' /etc/*-release 2>/dev/null || \
           grep -q -i 'red hat' /etc/*-release 2>/dev/null || \
           grep -q -i 'rocky' /etc/*-release 2>/dev/null || \
           grep -q -i 'alma' /etc/*-release 2>/dev/null; then
            OS_ID="centos"
        elif grep -q -i 'ubuntu' /etc/*-release 2>/dev/null; then
            OS_ID="ubuntu"
        elif grep -q -i 'debian' /etc/*-release 2>/dev/null; then
            OS_ID="debian"
        else
            OS_ID="unknown"
        fi
    fi
fi
# 确保OS_ID是小写
OS_ID=$(echo "$OS_ID" | tr '[:upper:]' '[:lower:]')
echo "检测到的系统: $OS_ID"
# 根据系统类型执行安装
case "$OS_ID" in
    centos*)
        centos_install_package
        ;;
    ubuntu)
        ubuntu_install_package
        ;;
    debian)
        debian_install_package
        ;;
    *)
        echo "错误：无法识别的操作系统" >&2
        exit 1
        ;;
esac
}

#yum install vim lrzsz tree tmux lsof tcpdump wget net-tools iotop bc bzip2 zip unzip nfs-utils man-pages dos2unix nc telnet wget ntpdate bash-completion bash-completion-extras gcc make autoconf gcc-c++ glibc glibc-devel pcre pcre-devel openssl openssl-devel systemd-devel zlib-devel -y
#添加常用别名
set_alias(){
cat >> ~/.bashrc <<EOF
alias scandisk='echo - - - > /sys/class/scsi_host/host0/scan;echo - - - > /sys/class/scsi_host/host1/scan;echo - - - > /sys/class/scsi_host/host2/scan'
alias cdnet='cd /etc/sysconfig/network-scripts/'
alias cdrepo='cd /etc/yum.repos.d/'
EOF
}
#修改vim格式
set_vimrc(){
cat >> ~/.vimrc << EOF
set number
set ignorecase
set cursorline
set autoindent
set et
set ts=4
inoremap ( ()<ESC>i
inoremap [ []<ESC>i
inoremap { {}<ESC>i
inoremap < <><ESC>i
inoremap ' ''<ESC>i
inoremap " ""<ESC>i
autocmd BufNewFile *.sh exec ":call SetTitle()"
func SetTitle()
    if expand("%:e") == 'sh'
    call setline(1,"#!/bin/bash")
    call setline(2,"#********************************************************************")
    call setline(3,"#Name:          Bocchi")
    call setline(4,"#Date:          ".strftime("%Y-%m-%d"))
    call setline(5,"#FileName：     ".expand("%"))
    call setline(6,"#Description:   The test script")
    call setline(7,"#********************************************************************")
    call setline(8,"")
    endif
endfunc
autocmd BufNewFile * normal G
EOF
}
#配置Ubuntu的root登录
set_ubuntu_root(){
	source /etc/init.d/functions
	echo PermitRootLogin yes >> /etc/ssh/sshd_config
	/etc/init.d/ssh restart
	if [ $? -eq 0 ];then
		green "SSH 服务重启成功!"
	else
		red "SSH 服务重启失败!"
	fi
}

#禁用SWAP
set_swap(){
sed -i '/swap/s/^/#/' /etc/fstab
swapoff -a
}

#配置主机名
set_host_name(){
	read -p "请输入主机名: " name
	hostnamectl set-hostname $name
}

#centos6配置静态网络
centos6_setip(){
ipname=`ip link show | awk -F':' '/^[0-9]+/{print $2}' | egrep -v "lo|docker" | head -1`
ipdir="/etc/sysconfig/network-scripts"
cp -a $ipdir/ifcfg-$ipname $ipdir/ifcfg-$ipname.bak
read -p "请输入IP地址: " ip
read -p "请输入网关: " gateway
cat > $ipdir/ifcfg-$ipname << EOF
DEVICE=$ipname
TYPE=Ethernet
ONBOOT=yes
BOOTPROTO=static
IPADDR=$ip
PREFIX=23
GATEWAY=$gateway
DNS1=223.5.5.5
DNS2=8.8.8.8
EOF
service network restart
if [ $? -eq 0 ];then
	green "NETWORK 服务重启成功!"
else
	red "NETWORK 服务重启失败!"
fi
}

#centos7配置静态网络
centos7_setip(){
ipname=`ip link show | awk -F':' '/^[0-9]+/{print $2}' | egrep -v "lo|docker" | head -1`
ipdir="/etc/sysconfig/network-scripts"
cp -a $ipdir/ifcfg-$ipname $ipdir/ifcfg-$ipname.bak
read -p "请输入IP地址: " ip
read -p "请输入网关: " gateway
cat > $ipdir/ifcfg-$ipname << EOF
TYPE="Ethernet"
BOOTPROTO="static"
DEFROUTE="yes"
NAME="$ipname"
DEVICE="$ipname"
ONBOOT="yes"
IPADDR=$ip
PREFIX=23
GATEWAY=$gateway
DNS1=223.5.5.5
DNS2=8.8.8.8
EOF
systemctl restart network
if [ $? -eq 0 ];then
	green "NETWORK 服务重启成功!"
else
	red "NETWORK 服务重启失败!"
fi
}

#Ubuntu配置静态网络
Ubuntu_setip(){
ipname=`ip link show | awk -F':' '/^[0-9]+/{print $2}' | egrep -v "lo|docker" | head -1`
ipdir="/etc/netplan"
cp -a $ipdir/00-installer-config.yaml $ipdir/00-installer-config.yaml.bak
read -p "请输入IP地址: " ip
read -p "请输入网关: " gateway
cat > $ipdir/00-installer-config.yaml << EOF
network:
    ethernets:
        $ipname:
            addresses: [$ip/23]
            gateway4: $gateway
            dhcp4: false
            nameservers:
                    addresses: [223.6.6.6, 180.76.76.76]
                    search: [baidu.com]
            optional: true
    version: 2
EOF
netplan apply
if [ $? -eq 0 ];then
	green "NETWORK 服务重启成功!"
else
	red "NETWORK 服务重启失败!"
fi
}

Centos_neofetch(){
	#rpm -q dnf dnf-plugins-core &> /dev/null || sudo yum install -y dnf-plugins-core dnf
	#sudo dnf copr enable konimex/neofetch
    #sudo dnf install -y neofetch
    rpm -q epel-release sudo unzip &> /dev/null || sudo yum install epel-release sudo unzip
    curl -o /etc/yum.repos.d/konimex-neofetch-epel-7.repo https://copr.fedorainfracloud.org/coprs/konimex/neofetch/repo/epel-7/konimex-neofetch-epel-7.repo
    sudo yum install -y neofetch
    rpm -q ruby rubygems &> /dev/null || sudo yum install -y ruby rubygems
    wget https://github.com/busyloop/lolcat/archive/master.zip
    unzip master.zip && cd  lolcat-master
    gem install lolcat && lolcat  --version
    rm -rf ~/master.zip
    rm -rf ~/lolcat-master
    grep "/usr/bin/neofetch | lolcat" /etc/profile
	if [ $? -eq 0 ];then
	  green "已添加到/etc/profile,如未成功请自行确认！"
	else
	  echo "/usr/bin/neofetch | lolcat" >> /etc/profile
	fi
}

Ubuntu_neofetch(){
    sudo apt-get update
    sudo apt-get install -y neofetch sudo unzip
    sudo apt-get install -y ruby gem
    wget https://github.com/busyloop/lolcat/archive/master.zip
    unzip master.zip && cd  lolcat-master
    gem install lolcat && lolcat  --version
    rm -rf ~/master.zip
    rm -rf ~/lolcat-master
    grep "/usr/bin/neofetch | lolcat" /etc/profile
	if [ $? -eq 0 ];then
	  green "已添加到/etc/profile,如未成功请自行确认！"
	else
	  echo "/usr/bin/neofetch | lolcat" >> /etc/profile
	fi
}

Debian_neofetch(){
    sudo apt-get update
    sudo apt-get install -y neofetch sudo unzip
    sudo apt-get install -y ruby gem
    wget https://github.com/busyloop/lolcat/archive/master.zip
    unzip master.zip && cd  lolcat-master
    gem install lolcat && lolcat  --version
    rm -rf ~/master.zip
    rm -rf ~/lolcat-master
    grep "/usr/bin/neofetch | lolcat" /etc/profile
	if [ $? -eq 0 ];then
	  green "已添加到/etc/profile,如未成功请自行确认！"
	else
	  echo "/usr/bin/neofetch | lolcat" >> /etc/profile
	fi
}

install_fastfetch(){
# ===================== 配置项（可根据你的 GitHub 仓库修改） =====================
# GitHub 上 Python 脚本的原始文件地址
PY_SCRIPT_URL="https://raw.githubusercontent.com/chenzai666/init_scripts/refs/heads/main/install_fastfetch.py"
# 超时时间（秒）
TIMEOUT=30
# ==============================================================================

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # 重置颜色

# 日志打印函数
info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# 检查网络连通性
check_network() {
    info "检查网络连通性..."
    if ! curl -s --connect-timeout 5 github.com > /dev/null; then
        error "无法连接到 GitHub，请检查网络或代理设置"
    fi
}

# 检查前置依赖（root 权限、python3、curl/wget）
check_dependencies() {
    # 检查 root 权限
    if [ "$(id -u)" -ne 0 ]; then
        error "请以 root 权限运行此脚本（sudo ./install_fastfetch.sh）"
    fi

    # 检查 Python3
    if ! command -v python3 &> /dev/null; then
        info "未检测到 Python3，正在自动安装..."
        # 自动适配不同系统安装 Python3
        if command -v apt &> /dev/null; then
            apt update -y && apt install -y python3
        elif command -v dnf &> /dev/null; then
            dnf install -y python3
        elif command -v yum &> /dev/null; then
            yum install -y python3
        elif command -v pacman &> /dev/null; then
            pacman -S --noconfirm python
        else
            error "无法自动安装 Python3，请手动安装后重试"
        fi
    fi

    # 检查 curl 或 wget（至少需要一个）
    if ! command -v curl &> /dev/null && ! command -v wget &> /dev/null; then
        info "未检测到 curl/wget，正在自动安装 curl..."
        if command -v apt &> /dev/null; then
            apt install -y curl
        elif command -v dnf &> /dev/null; then
            dnf install -y curl
        elif command -v yum &> /dev/null; then
            yum install -y curl
        elif command -v pacman &> /dev/null; then
            pacman -S --noconfirm curl
        else
            error "无法自动安装 curl，请手动安装后重试"
        fi
    fi
}

# 从 GitHub 拉取并执行 Python 脚本
run_python_script() {
    info "开始从 GitHub 拉取安装脚本: $PY_SCRIPT_URL"
    
    # 优先使用 curl，没有则用 wget
    if command -v curl &> /dev/null; then
        # 使用 curl 拉取并通过管道执行（添加超时、静默模式、失败重试）
        if ! curl -sSL --max-time "$TIMEOUT" --retry 3 "$PY_SCRIPT_URL" | python3 -; then
            error "Python 脚本执行失败，请检查 GitHub 地址是否正确，或网络是否稳定"
        fi
    else
        # 使用 wget 拉取并通过管道执行
        if ! wget -qO- --timeout="$TIMEOUT" --tries=3 "$PY_SCRIPT_URL" | python3 -; then
            error "Python 脚本执行失败，请检查 GitHub 地址是否正确，或网络是否稳定"
        fi
    fi
}

# 主函数
main() {
    info "===== Fastfetch 一键安装脚本 ====="
    
    # 前置检查
    check_dependencies
    check_network
    
    # 执行核心逻辑
    run_python_script
    
    # 执行完成提示
    info "===== 安装流程执行完毕 ====="
    info "✅ 请重启终端，或执行以下命令立即生效："
    echo "   source ~/.bashrc  # Bash 用户"
    echo "   source ~/.zshrc   # Zsh 用户"
}

# 启动主函数
main "$@"
}

Choice_change(){
    clear
     yellow " ================== "
     blue " 1.更换国内版仓库源"
     blue " 2.更换教育版仓库源"
     blue " 3.更换海外版仓库源"
	 yellow " ================== "
    echo
   read -p "请输入您的选项(1-3): " choice
clear
  case $choice in
  	1)
      Change_mirrors
      ;;
    2)
      Change_educate_mirrors
      ;;
    3)
      Change_overseas_mirrors
      ;;
    *)
      clear
	red "输入错误,请输入正确的数字!"
        start_menu
    sleep 2s
    start_menu
      ;;
  esac 
}

Change_mirrors(){
	bash <(curl -sSL https://linuxmirrors.cn/main.sh)
}

Change_educate_mirrors(){
	bash <(curl -sSL https://linuxmirrors.cn/main.sh) --edu 	
}

Change_overseas_mirrors(){
	bash <(curl -sSL https://linuxmirrors.cn/main.sh) --abroad
}


Install_Docker(){
	bash <(curl -sSL https://linuxmirrors.cn/docker.sh)
}

start_menu(){
    clear
     yellow " ======================常规配置============================ "
     blue " 1.永久关闭防火墙"
     blue " 2. 网卡更名为eth0"
     blue " 3.配置邮箱告警"
     blue " 4.设置ssh服务和root远程登录"
     blue " 5.禁用SWAP"
     blue " 6.配置主机名"
	 blue " 7.修改vim格式"
	 blue " 8.修改提示符颜色"
	 blue " 9.配置Ububtu的root登录"
	 yellow " =====================修改ip和软件源相关=================== "
	 blue " 10.修改centos6静态ip "
	 blue " 11.修改centos7静态ip"
	 blue " 12.修改Ubuntu静态ip"
	 blue " 13.配置centos6的yum源仓库"
	 blue " 14.配置centos7的yum源仓库"
	 blue " 15.配置Rocky8的yum源仓库"
	 blue " 16.配置Ubuntu18的软件源仓库"
	 blue " 17.配置Ubuntu20的软件源仓库"
	 blue " 18.配置Centos的neofetch"
	 blue " 19.配置Ubuntu的neofetch"
	 blue " 20.配置Debian的neofetch"
	 blue " 21.自适应配置fastfetch"
	 blue " 22.建议安装软件包"
	 blue " 23.一键更换仓库源"
	 blue " 24.一键安装docker"
	 yellow " ========================================================== "
     red " 0. 退出脚本"
    echo
    read -p "请输入数字:" num
clear
case $num in
1)
	disable_firewalld_selinux
	green "防火墙已永久关闭!"
	;;
2)
	change_Centos_networkname
	green "网卡名已修改,请重启!"
	;;
3)
	set_postfix
	green "邮箱告警已配置!"
	;;
4)
	set_ssh_port_rootlogin
	green "SSH 端口和root远程登录已配置成功！"
	;;
5)
	set_swap
	green "swap已禁用成功!"
	;;
6)
	set_host_name
	green "主机名已设置成功!"
	;;
7)
	set_vimrc
	green "vimrc已配置成功!"
	;;
8)
	set_ps1
	green "PS1颜色已设置,请重新登录终端!"
	;;
9)
	set_ubuntu_root
	green "Ubuntu的root远程登录已配置成功!"
	;;
10)
	centos6_setip
	green "centos6静态IP已配置!"
	;;
11)
	centos7_setip
	green "centos7静态IP已配置!"
	;;
12)
	Ubuntu_setip
	green "Ubuntu静态IP已配置"
	;;
13)
	centos6_make_yum_repo
	green "centos6的yum仓库源已配置!"
	;;
14)
	centos7_make_yum_repo
	green "centos7的yum仓库源已配置!"
	;;
15)
	Rocky8_make_yum_repo
	green "Rocky8的yum仓库源已配置!"
	;;
16)
	Ubuntu18_make_yum_repo
	green "Ubuntu18的yum仓库源已配置!"
	;;
17)
	Ubuntu20_make_yum_repo
	green "Ubuntu20的yum仓库源已配置!"
	;;
18)
	Centos_neofetch
	green "Centos的neofetch已配置!"
	;;
19)
	Ubuntu_neofetch
	green "Ubuntu的neofetch已配置!"
	;;
20)
	Debian_neofetch
	green "Debian的neofetch已配置!"
	;;
21)
	install_fastfetch
	green "neofetch已配置完成!"
	;;
22)
    minimal_install
    green "建议安装软件包已安装完成!"
    ;;
23)
    Choice_change
    ;;
24)
    Install_Docker
    ;;
0)
	exit 0
	;;
*)
    clear
	red "输入错误,请输入正确的数字!"
        start_menu
    sleep 2s
    start_menu
    ;;
esac
}
start_menu

