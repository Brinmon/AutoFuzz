import docker
import json
import os
import sys
import shutil
from datetime import datetime, timezone
from pathlib import Path


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