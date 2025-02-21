import docker
import json
import os
import sys
import shutil
import threading
import subprocess
from datetime import datetime, timezone
from pathlib import Path
import time
from collections import defaultdict
import re

def get_fuzz_work_dir():
    """
    """
    fuzz_config_path = os.getenv('FUZZCONFIGFILE')
    try:
        with open(fuzz_config_path, 'r') as f:
            config_data = json.load(f)
            return config_data.get("FuzzWorkDir", None)  # 返回 FuzzWorkDir 的路径
    except Exception as e:
        print(f"Error reading FuzzConfig file: {e}")
        return None

def get_projection_version_manager():
    """
    从给定的配置文件中读取 ProjectionVerionManager 的路径。

    Args:
        fuzz_config_path (str): 配置文件的完整路径。

    Returns:
        str: ProjectionVerionManager 的路径，若读取失败则返回 None。
    """
    fuzz_config_path = os.getenv('FUZZCONFIGFILE')
    try:
        with open(fuzz_config_path, 'r') as f:
            config_data = json.load(f)
            return config_data.get("ProjectionVerionManager", None)  # 返回 ProjectionVerionManager 的路径
    except Exception as e:
        print(f"Error reading FuzzConfig file: {e}")
        return None

def copy_files_to_current_task(release_file_path, current_task_path):
    """
    复制 release_file_path 中的所有文件和文件夹到 current_task_path，但跳过 dockerinfo.txt 文件。
    """
    # 确保目标路径存在，如果不存在则创建
    os.makedirs(current_task_path, exist_ok=True)

    # 遍历 ReleaseFilePath 文件夹中的所有文件和文件夹
    print(release_file_path)
    for item in os.listdir(release_file_path):
        source_path = os.path.join(release_file_path, item)
        destination_path = os.path.join(current_task_path, item)

        # 如果文件是 dockerinfo.txt，跳过复制
        if item == "dockerinfo.txt":
            print(f"Skipping {source_path}, it is excluded.")
            continue

        if os.path.isfile(source_path):
            # 如果是文件，进行文件复制
            try:
                shutil.copy(source_path, destination_path)
                print(f"Copied file {source_path} to {destination_path}")
            except Exception as e:
                print(f"Error copying file {source_path} to {destination_path}: {e}")
        elif os.path.isdir(source_path):
            # 如果是文件夹，进行目录复制
            try:
                shutil.copytree(source_path, destination_path, dirs_exist_ok=True)  # Python 3.8+ 支持 dirs_exist_ok 参数
                print(f"Copied directory {source_path} to {destination_path}")
            except Exception as e:
                print(f"Error copying directory {source_path} to {destination_path}: {e}")
        else:
            print(f"Skipping {source_path}, it's neither a file nor a directory.")

def convert_path(host_path, bind_mount, to_docker=True):
    """
    将宿主机路径转换为 Docker 路径，或将 Docker 路径转换为宿主机路径。
    
    :param host_path: 输入路径
    :param bind_mount: 绑定挂载的映射字典 {宿主机路径: Docker路径}
    :param to_docker: 如果为True，表示从宿主机路径转换为Docker路径，False表示反向转换
    :return: 转换后的路径
    """
    if to_docker:  # 从宿主机路径到Docker路径
        for host_dir, docker_dir in bind_mount.items():
            if host_path.startswith(host_dir):  # 检查宿主机路径是否在映射路径下
                # 获取宿主机路径相对于绑定路径的部分，并替换为容器内的路径
                docker_path = host_path.replace(host_dir, docker_dir, 1)
                return docker_path
        return host_path  # 如果没有找到映射关系，返回原路径
    else:  # 从Docker路径到宿主机路径
        for host_dir, docker_dir in bind_mount.items():
            if host_path.startswith(docker_dir):  # 检查容器路径是否在映射路径下
                # 获取Docker路径相对于绑定路径的部分，并替换为宿主机路径
                host_path = host_path.replace(docker_dir, host_dir, 1)
                return host_path
        return host_path  # 如果没有找到映射关系，返回原路径

def find_executable_in_directory(directory, filename):
    matching_files = []
    
    # 遍历目录下的所有文件和子目录
    for root, dirs, files in os.walk(directory):
        if filename in files:
            full_path = os.path.join(root, filename)
            # 使用 'file' 命令来检测文件类型
            try:
                result = subprocess.run(['file', full_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if result.returncode == 0:
                    file_info = result.stdout.decode('utf-8')
                    if 'executable' in file_info or 'script' in file_info:
                        matching_files.append(full_path)
            except Exception as e:
                print(f"错误：无法执行 'file' 命令，原因: {e}")
    
    if len(matching_files) > 1:
        print(f"警告：在目录 {directory} 中找到了多个可执行文件：")
        for f in matching_files:
            print(f)
    
    if matching_files:
        return matching_files[0]
    else:
        print(f"未找到可执行文件 {filename}。")
        return None


