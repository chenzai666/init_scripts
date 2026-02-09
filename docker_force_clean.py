#!/usr/bin/env python3
import os
import subprocess
import shlex
import sys
import json
import re
import time
from datetime import datetime

# 颜色代码
COLOR_RED = "\033[1;31m"
COLOR_GREEN = "\033[1;32m"
COLOR_YELLOW = "\033[1;33m"
COLOR_BLUE = "\033[1;34m"
COLOR_CYAN = "\033[1;36m"
COLOR_RESET = "\033[0m"

def run_command(cmd, capture=False, check=False, exit_on_fail=False, verbose=True):
    """执行系统命令并返回结果"""
    if verbose:
        print(f"{COLOR_BLUE}[+] Executing: {cmd}{COLOR_RESET}")
    
    try:
        if capture:
            result = subprocess.run(
                shlex.split(cmd),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode != 0:
                if verbose: print(f"{COLOR_RED}[!] Command failed (code {result.returncode}): {result.stderr.strip()}{COLOR_RESET}")
                if exit_on_fail:
                    sys.exit(1)
            return result
        else:
            result = subprocess.run(
                shlex.split(cmd),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode != 0 and verbose:
                print(f"{COLOR_RED}[!] Command failed (code {result.returncode}): {result.stderr.strip()}{COLOR_RESET}")
            return result
    except Exception as e:
        if verbose: print(f"{COLOR_RED}[!] Command execution error: {str(e)}{COLOR_RESET}")
        if exit_on_fail:
            sys.exit(1)
        return None

def get_container_info(container_id):
    """获取容器详细信息"""
    cmd = f"docker inspect {container_id}"
    result = run_command(cmd, capture=True, exit_on_fail=True, verbose=False)
    
    if not result or result.returncode != 0:
        print(f"{COLOR_RED}[!] Failed to inspect container {container_id}{COLOR_RESET}")
        print(f"Error: {result.stderr.strip() if result else 'Unknown error'}")
        return None
    
    try:
        return json.loads(result.stdout)[0]
    except (json.JSONDecodeError, IndexError):
        print(f"{COLOR_RED}[!] Invalid JSON response from docker inspect{COLOR_RESET}")
        return None

def kill_container_processes(container_info):
    """强制杀死容器相关进程"""
    if not container_info:
        print(f"{COLOR_RED}[!] No container info available{COLOR_RESET}")
        return False
    
    container_id = container_info.get('Id', '')
    print(f"{COLOR_YELLOW}[+] Killing processes for container: {container_id[:12]}{COLOR_RESET}")
    
    # 方法1：通过容器ID查找进程
    cmd = f"ps aux | grep '{container_id}' | grep -v grep | awk '{{print $2}}'"
    result = run_command(cmd, capture=True)
    pids = []
    if result and result.stdout:
        pids = [pid.strip() for pid in result.stdout.splitlines() if pid.strip()]
    
    # 方法2：查找所有docker-containerd-shim进程
    if not pids:
        cmd = "pgrep -f 'docker-containerd-shim'"
        result = run_command(cmd, capture=True)
        if result and result.stdout:
            all_shim_pids = result.stdout.splitlines()
            print(f"{COLOR_YELLOW}[+] Found {len(all_shim_pids)} containerd-shim processes{COLOR_RESET}")
            
            # 检查每个shim进程是否与当前容器有关
            for pid in all_shim_pids:
                pid = pid.strip()
                if not pid:
                    continue
                
                cmd = f"cat /proc/{pid}/cmdline | grep -a '{container_id}'"
                grep_result = run_command(cmd, capture=True)
                if grep_result and grep_result.stdout:
                    pids.append(pid)
    
    # 杀死找到的进程
    if pids:
        pid_list = " ".join(pids)
        run_command(f"kill -9 {pid_list}")
        print(f"{COLOR_GREEN}[+] Killed {len(pids)} processes: {pid_list}{COLOR_RESET}")
        return True
    else:
        print(f"{COLOR_YELLOW}[!] No processes found for container{COLOR_RESET}")
        return False

def cleanup_mounts(container_info):
    """清理容器挂载点"""
    if not container_info:
        return False
    
    container_id = container_info.get('Id', '')
    print(f"{COLOR_YELLOW}[+] Cleaning up mounts for container: {container_id[:12]}{COLOR_RESET}")
    
    # 尝试卸载常见挂载点
    mount_points = [
        f"/var/lib/docker/containers/{container_id}/mounts/shm",
        f"/var/lib/docker/containers/{container_id}/mounts/mqueue",
        f"/var/lib/docker/containers/{container_id}/shm"
    ]
    
    cleaned = False
    for mp in mount_points:
        if os.path.exists(mp):
            run_command(f"umount -f {mp} 2>/dev/null", verbose=False)
            cleaned = True
            print(f"{COLOR_GREEN}[+] Unmounted: {mp}{COLOR_RESET}")
    
    if not cleaned:
        print(f"{COLOR_YELLOW}[!] No mount points found{COLOR_RESET}")
    
    return cleaned

def cleanup_network(container_info):
    """清理容器的网络命名空间"""
    if not container_info:
        return False
    
    print(f"{COLOR_YELLOW}[+] Cleaning up network namespace{COLOR_RESET}")
    
    # 获取网络命名空间ID
    sandbox_key = container_info.get('NetworkSettings', {}).get('SandboxKey', '')
    if not sandbox_key:
        print(f"{COLOR_YELLOW}[!] Cannot determine network namespace{COLOR_RESET}")
        return False
    
    # 提取命名空间ID
    netns_id = sandbox_key.split('/')[-1]
    print(f"{COLOR_YELLOW}[+] Found network namespace ID: {netns_id}{COLOR_RESET}")
    
    # 删除网络命名空间
    netns_path = f"/var/run/netns/{netns_id}"
    if os.path.exists(netns_path):
        run_command(f"ip netns del {netns_id}")
        print(f"{COLOR_GREEN}[+] Removed network namespace{COLOR_RESET}")
    else:
        print(f"{COLOR_YELLOW}[!] Network namespace not found at {netns_path}{COLOR_RESET}")
    
    # 清理iptables规则 - 更安全的方法
    print(f"{COLOR_YELLOW}[+] Cleaning up iptables rules{COLOR_RESET}")
    run_command("iptables-save | grep -v surgio | iptables-restore", exit_on_fail=False, verbose=False)
    
    return True

def remove_container_files(container_info):
    """删除容器的残留文件"""
    if not container_info:
        return False
    
    container_id = container_info.get('Id', '')
    print(f"{COLOR_YELLOW}[+] Removing container files: {container_id[:12]}{COLOR_RESET}")
    
    # 容器文件路径
    container_path = f"/var/lib/docker/containers/{container_id}"
    
    # 递归删除容器文件
    if os.path.exists(container_path):
        run_command(f"rm -rf {container_path}")
        print(f"{COLOR_GREEN}[+] Removed container files at {container_path}{COLOR_RESET}")
        return True
    else:
        print(f"{COLOR_YELLOW}[!] Container directory not found{COLOR_RESET}")
        return False

def restart_docker():
    """重启Docker服务"""
    print(f"{COLOR_YELLOW}[+] Restarting Docker service{COLOR_RESET}")
    
    # 先停止Docker
    run_command("systemctl stop docker", verbose=False)
    
    # 清理残留进程
    run_command("pkill -9 docker-containerd-shim", exit_on_fail=False, verbose=False)
    run_command("pkill -9 dockerd", exit_on_fail=False, verbose=False)
    
    # 确保进程被杀死
    time.sleep(2)
    
    # 启动Docker
    result = run_command("systemctl start docker", verbose=False)
    
    # 检查Docker状态
    status_result = run_command("systemctl status docker --no-pager", capture=True, verbose=False)
    if status_result and "active (running)" in status_result.stdout:
        print(f"{COLOR_GREEN}[+] Docker restarted successfully{COLOR_RESET}")
        return True
    else:
        print(f"{COLOR_RED}[!] Docker failed to start{COLOR_RESET}")
        if status_result:
            print(status_result.stdout)
        return False

def cleanup_network_resources():
    """清理网络资源"""
    print(f"{COLOR_YELLOW}[+] Cleaning up network resources{COLOR_RESET}")
    
    # 清理docker网络
    run_command("docker network rm surgio_default", exit_on_fail=False, verbose=False)
    
    # 清理残留网络
    run_command("docker network prune -f", exit_on_fail=False, verbose=False)
    
    # 清理iptables规则再次确认
    run_command("iptables-save | grep -v docker | iptables-restore", exit_on_fail=False, verbose=False)
    
    return True

def check_docker_service():
    """检查Docker服务状态"""
    print(f"{COLOR_YELLOW}[+] Checking Docker service status{COLOR_RESET}")
    
    # 检查Docker是否安装
    result = run_command("which docker", capture=True)
    if not result.stdout.strip():
        print(f"{COLOR_RED}[!] Docker is not installed{COLOR_RESET}")
        return False
    
    # 检查Docker服务状态
    result = run_command("systemctl is-active docker", capture=True)
    if result.stdout.strip() != "active":
        print(f"{COLOR_RED}[!] Docker service is not active{COLOR_RESET}")
        print(f"Status: {result.stdout.strip()}")
        return False
    
    return True

def list_all_containers():
    """列出所有容器（包括停止的）"""
    print(f"{COLOR_YELLOW}[+] Listing all containers{COLOR_RESET}")
    
    # 列出所有容器
    cmd = "docker ps -a --format 'table {{.ID}}\\t{{.Names}}\\t{{.Status}}\\t{{.Image}}'"
    result = run_command(cmd, capture=True)
    
    if not result.stdout.strip():
        print(f"{COLOR_RED}[!] No containers found at all{COLOR_RESET}")
        return False
    
    # 打印容器列表
    print(result.stdout)
    return True

def main():
    # 检查root权限
    if os.geteuid() != 0:
        print(f"{COLOR_RED}[!] This script must be run as root{COLOR_RESET}")
        sys.exit(1)
    
    print(f"\n{COLOR_CYAN}=== Docker Container Force Cleanup Tool ==={COLOR_RESET}\n")
    
    # 检查Docker服务状态
    if not check_docker_service():
        print(f"{COLOR_RED}[!] Docker service is not running, attempting to start it{COLOR_RESET}")
        run_command("systemctl start docker")
        time.sleep(2)  # 等待服务启动
        
        # 再次检查
        if not check_docker_service():
            print(f"{COLOR_RED}[!] Failed to start Docker service. Please check Docker installation.{COLOR_RESET}")
            sys.exit(1)
    
    # 显示所有容器（包括停止的）
    if not list_all_containers():
        print(f"{COLOR_YELLOW}No containers found. Exiting.{COLOR_RESET}")
        sys.exit(0)
    
    # 获取用户输入
    container_id = input(f"\n{COLOR_GREEN}Enter container ID or name to force remove (or 'exit' to quit): {COLOR_RESET}").strip()
    
    if container_id.lower() == 'exit':
        print(f"{COLOR_YELLOW}Operation canceled{COLOR_RESET}")
        sys.exit(0)
    
    # 验证容器ID格式
    if not re.match(r'^[a-f0-9]+$', container_id) and not re.match(r'^[\w\-]+$', container_id):
        print(f"{COLOR_RED}[!] Invalid container identifier{COLOR_RESET}")
        sys.exit(1)
    
    # 获取容器信息
    print(f"\n{COLOR_CYAN}Processing container: {container_id}{COLOR_RESET}")
    container_info = get_container_info(container_id)
    
    if not container_info:
        print(f"{COLOR_RED}[!] Container {container_id} not found or inaccessible{COLOR_RESET}")
        sys.exit(1)
    
    # 显示容器信息
    container_id_full = container_info.get('Id', '')
    print(f"Container Name: {container_info.get('Name', '')}")
    print(f"Container ID: {container_id_full[:12]}...{container_id_full[-12:]}")
    print(f"Status: {container_info.get('State', {}).get('Status', 'unknown')}")
    print(f"Image: {container_info.get('Config', {}).get('Image', 'unknown')}")
    
    # 确认操作
    confirm = input(f"\n{COLOR_RED}WARNING: This will force remove the container. Continue? (y/N): {COLOR_RESET}").strip().lower()
    if confirm != 'y':
        print(f"{COLOR_YELLOW}Operation canceled{COLOR_RESET}")
        sys.exit(0)
    
    # 创建日志文件
    log_file = f"/var/log/docker_force_clean_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    print(f"{COLOR_YELLOW}[+] Logging to: {log_file}{COLOR_RESET}")
    
    # 清理过程
    print(f"\n{COLOR_RED}=== Starting Force Removal Procedure ==={COLOR_RESET}")
    
    steps = [
        ("Trying regular docker removal", lambda: run_command(f"docker rm -f {container_id}")),
        ("Force killing container processes", lambda: kill_container_processes(container_info)),
        ("Cleaning up mounts", lambda: cleanup_mounts(container_info)),
        ("Cleaning up network namespace", lambda: cleanup_network(container_info)),
        ("Removing container files", lambda: remove_container_files(container_info)),
        ("Restarting Docker service", restart_docker),
        ("Final removal attempt", lambda: run_command(f"docker rm -f {container_id}", exit_on_fail=False)),
        ("Cleaning up network resources", cleanup_network_resources)
    ]
    
    for i, (desc, action) in enumerate(steps, 1):
        print(f"\n{COLOR_YELLOW}[{i}] {desc}{COLOR_RESET}")
        with open(log_file, "a") as log:
            log.write(f"\n\n=== Step {i}: {desc} ===\n")
        
        try:
            result = action()
            status = "SUCCESS" if result or result is None else "FAILED"
            color = COLOR_GREEN if status == "SUCCESS" else COLOR_RED
            print(f"{color}[+] Step {i}: {status}{COLOR_RESET}")
        except Exception as e:
            print(f"{COLOR_RED}[!] Step {i} failed: {str(e)}{COLOR_RESET}")
    
    print(f"\n{COLOR_GREEN}=== Cleanup completed successfully! ==={COLOR_RESET}")
    print(f"{COLOR_CYAN}Log file saved to: {log_file}{COLOR_RESET}")

if __name__ == "__main__":
    main()
