#!/usr/bin/env python3
import os
import subprocess
import re
import sys

def run_cmd(cmd):
    try:
        result = subprocess.run(
            cmd.split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {e.stderr}")
        sys.exit(1)

def get_root_device():
    """获取根分区设备路径"""
    df_output = run_cmd("df -h /")
    lines = df_output.split('\n')
    if len(lines) < 2:
        print("无法确定根分区设备")
        sys.exit(1)
    
    device = lines[1].split()[0]
    return device

def check_lvm(device):
    """检查是否为LVM设备"""
    return device.startswith("/dev/mapper") or "dm-" in device

def get_unallocated_space(disk):
    """获取未分配空间大小（GB）"""
    parted_output = run_cmd(f"parted -s {disk} unit GB print free")
    free_lines = [line for line in parted_output.split('\n') if "Free Space" in line]
    
    if not free_lines:
        print("未找到可用空间")
        return 0.0
    
    # 取最后一个未分配空间（通常是最新创建的）
    last_free = free_lines[-1].split()
    size_gb = float(re.search(r"(\d+\.\d+)GB", last_free[2]).group(1))
    return size_gb

def expand_root_lvm():
    """扩展LVM根分区"""
    print("检测到LVM系统，开始扩展...")
    
    # 获取物理卷信息
    pvs_output = run_cmd("pvs --noheadings -o pv_name")
    pv_device = pvs_output.split()[0]
    
    # 获取卷组名
    vg_name = run_cmd("vgs --noheadings -o vg_name | head -n1").strip()
    
    # 获取逻辑卷路径
    lv_path = run_cmd("lvs --noheadings -o lv_path | grep root | head -n1").strip()
    
    if not all([pv_device, vg_name, lv_path]):
        print("获取LVM信息失败")
        sys.exit(1)
    
    # 扩展物理卷
    print(f"扩展物理卷: {pv_device}")
    run_cmd(f"pvresize {pv_device}")
    
    # 扩展逻辑卷（使用100%空闲空间）
    print(f"扩展逻辑卷: {lv_path}")
    run_cmd(f"lvextend -l +100%FREE {lv_path}")
    
    # 调整文件系统
    fs_type = run_cmd(f"blkid -o value -s TYPE {lv_path}")
    if "xfs" in fs_type:
        run_cmd(f"xfs_growfs {lv_path}")
    else:
        run_cmd(f"resize2fs {lv_path}")
    
    print("✅ LVM根分区扩展完成")

def expand_root_non_lvm(disk, root_part):
    """扩展非LVM根分区"""
    print("检测到非LVM系统，开始扩展...")
    
    # 检查未分配空间
    free_gb = get_unallocated_space(disk)
    if free_gb < 0.1:
        print("⚠️ 可用空间不足1GB，无法扩展")
        sys.exit(1)
    
    # 扩展分区
    print(f"扩展分区 {root_part}")
    run_cmd(f"growpart {disk} {root_part[-1]}")
    
    # 调整文件系统
    fs_type = run_cmd(f"blkid -o value -s TYPE {root_part}")
    if "xfs" in fs_type:
        run_cmd(f"xfs_growfs {root_part}")
    else:
        run_cmd(f"resize2fs {root_part}")
    
    print("✅ 非LVM根分区扩展完成")

def main():
    # 检查root权限
    if os.geteuid() != 0:
        print("❌ 请使用sudo运行此脚本")
        sys.exit(1)
    
    # 获取根设备
    root_device = get_root_device()
    print(f"根设备: {root_device}")
    
    # 确定磁盘设备
    if check_lvm(root_device):
        disk_device = run_cmd("pvs --noheadings -o pv_name | head -n1").strip()
        if not disk_device:
            print("无法确定物理卷设备")
            sys.exit(1)
        expand_root_lvm()
    else:
        # 非LVM系统
        disk_device = re.match(r"(/dev/[a-z]+)\d+", root_device)
        if not disk_device:
            print("无法确定磁盘设备")
            sys.exit(1)
        disk_device = disk_device.group(1)
        expand_root_non_lvm(disk_device, root_device)
    
    # 验证结果
    print("\n扩展后磁盘空间:")
    print(run_cmd("df -h /"))

if __name__ == "__main__":
    main()
