import json
import os

#读取json文件
def read_config(file_path):
    """读取JSON配置文件并返回内容"""
    with open(file_path, 'r') as f:
        return json.load(f)

import os
import json

def initialize_fuzz_config(current_directory):
    """
    初始化Fuzz工具所需的配置文件 FuzzConfig.json。

    Args:
        current_directory (str): 当前工作目录的路径。

    Returns:
        str: FuzzConfig.json 文件的完整路径。

    Description:
        该函数用于初始化 Fuzz 工具所需的配置文件 FuzzConfig.json。如果文件不存在或内容为空，
        则会创建该文件并初始化其内容。配置文件包括以下字段：
        - FuzzWorkDir: Fuzz 工作目录的路径。
        - ProjectionVerionManager: 项目版本管理目录的路径。

        同时，函数还会创建 FuzzWorkDir 和 ProjectionVerionManager 目录。
    """
    fuzz_config_path = os.path.join(current_directory, "FuzzConfig.json")
    
    # 如果 FuzzConfig.json 文件不存在或内容为空，则创建并初始化
    if not os.path.exists(fuzz_config_path) or os.path.getsize(fuzz_config_path) == 0:
        fuzz_config = {
            "FuzzWorkDir": os.path.join(current_directory, "FuzzWorkDir"),
            "ProjectionVerionManager": os.path.join(current_directory, "PVManager")
        }
        
        with open(fuzz_config_path, 'w') as f:
            json.dump(fuzz_config, f, indent=4)
        
        # 创建 FuzzWorkDir 和 ProjectionVerionManager 目录
        os.makedirs(fuzz_config["FuzzWorkDir"], exist_ok=True)
        os.makedirs(fuzz_config["ProjectionVerionManager"], exist_ok=True)
    
    return fuzz_config_path

def initialize_pv_manager(fuzz_config_path):
    """
    初始化项目版本管理文件 PVManger.json。

    Args:
        fuzz_config_path (str): FuzzConfig.json 文件的完整路径。

    Description:
        该函数用于初始化项目版本管理文件 PVManger.json。首先读取 FuzzConfig.json 文件，
        获取 ProjectionVerionManager 目录的路径，然后在该目录下创建并初始化 PVManger.json 文件。
        文件内容如下：
        - TotalProjects: 总项目数，初始值为 0。
        - Projects: 项目列表，初始为空列表。
    """
    with open(fuzz_config_path, 'r') as f:
        fuzz_config = json.load(f)
    
    pv_manager_path = os.path.join(fuzz_config["ProjectionVerionManager"], "PVManger.json")
    
    # 如果 PVManger.json 文件不存在，则创建并初始化
    if not os.path.exists(pv_manager_path):
        pv_manager = {
            "TotalProjects": 0,
            "Projects": []
        }
        
        with open(pv_manager_path, 'w') as f:
            json.dump(pv_manager, f, indent=4)






