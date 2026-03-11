#!/bin/bash

# 宝塔面板一键配置脚本
# 功能：修改用户名、密码、端口、安全入口
# 执行方式：sudo bt-config

# 检查root权限
if [ "$(id -u)" != "0" ]; then
   echo "错误：此脚本必须以root权限运行！" 
   exit 1
fi

# 主菜单
show_menu() {
    clear
    echo "======================================="
    echo "  宝塔面板高级配置脚本 v1.2"
    echo "======================================="
    echo "1. 修改面板用户名"
    echo "2. 修改面板密码"
    echo "3. 修改面板端口"
    echo "4. 修改安全入口"
    echo "5. 查看当前面板信息"
    echo "6. 一键修改所有设置"
    echo "7. 退出"
    echo "======================================="
    read -p "请输入选择 [1-7]: " choice
}

# 修改用户名
change_username() {
    read -p "请输入新的用户名: " new_username
    echo "$new_username" | bt 6
    echo "✔ 用户名已修改为: $new_username"
}

# 修改密码
change_password() {
    read -p "请输入新的密码: " new_password
    echo -e "$new_password\n$new_password" | bt 5
    echo "✔ 密码已修改"
}

# 修改端口
change_port() {
    read -p "请输入新的端口号(建议1000-65535): " new_port
    echo "$new_port" | bt 8
    echo "✔ 端口已修改为: $new_port"
    
    # 自动放行防火墙
    if command -v ufw &> /dev/null; then
        ufw allow $new_port/tcp
        echo "✔ 已自动放行UFW防火墙"
    elif command -v firewall-cmd &> /dev/null; then
        firewall-cmd --permanent --add-port=$new_port/tcp
        firewall-cmd --reload
        echo "✔ 已自动放行FirewallD防火墙"
    fi
}

# 修改安全入口
change_auth_path() {
    read -p "请输入新的安全入口(格式如:/mypanel): " new_path
    echo "$new_path" | bt 28
    echo "✔ 安全入口已修改为: $new_path"
}

# 显示当前配置
show_info() {
    clear
    echo "======================================="
    echo "      当前宝塔面板配置信息"
    echo "======================================="
    
    # 获取配置文件信息
    config_file="/www/server/panel/data/default.db"
    
    # 用户名
    username=$(sqlite3 $config_file "SELECT username FROM users WHERE id=1;")
    echo "▪ 用户名: $username"
    
    # 密码（无法显示明文）
    echo "▪ 密码: [已加密存储]"
    
    # 端口
    port=$(cat /www/server/panel/data/port.pl 2>/dev/null)
    [ -z "$port" ] && port="8888"
    echo "▪ 面板端口: $port"
    
    # 安全入口
    auth_path=$(cat /www/server/panel/data/admin_path.pl 2>/dev/null)
    [ -z "$auth_path" ] && auth_path="/"
    echo "▪ 安全入口: $auth_path"
    
    # 服务器IP
    ip=$(curl -s http://checkip.amazonaws.com || hostname -I | awk '{print $1}')
    echo "▪ 服务器IP: $ip"
    
    # 完整访问地址
    echo "▪ 面板地址: http://$ip:$port$auth_path"
    echo "======================================="
    echo ""
    read -p "按Enter键返回主菜单..."
}

# 批量修改所有设置
change_all() {
    echo "正在批量修改面板设置..."
    change_username
    change_password
    change_port
    change_auth_path
    
    sleep 1
    show_info
}

# 主循环
while true; do
    show_menu
    case $choice in
        1) change_username ;;
        2) change_password ;;
        3) change_port ;;
        4) change_auth_path ;;
        5) show_info ;;
        6) change_all ;;
        7) 
            echo "已退出脚本"
            exit 0
            ;;
        *) 
            echo "无效选择，请重新输入！"
            sleep 1
            ;;
    esac
    sleep 1
done
