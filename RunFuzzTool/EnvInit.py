from RunFuzzTool import *

#读取json文件
def read_config(file_path):
    """读取JSON配置文件并返回内容"""
    with open(file_path, 'r') as f:
        return json.load(f)

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
    
    pv_manager_path = os.path.join(fuzz_config["ProjectionVerionManager"], "PVManager.json")
    
    # 如果 PVManger.json 文件不存在，则创建并初始化
    if not os.path.exists(pv_manager_path):
        pv_manager = {
            "TotalProjects": 0,
            "Projects": []
        }
        
        with open(pv_manager_path, 'w') as f:
            json.dump(pv_manager, f, indent=4)


def copy_files_to_current_task(release_file_path, current_task_path):
    """
    复制 release_file_path 中的所有文件和文件夹到 current_task_path。
    """
    # 确保目标路径存在，如果不存在则创建
    os.makedirs(current_task_path, exist_ok=True)

    # 遍历 ReleaseFilePath 文件夹中的所有文件和文件夹
    for item in os.listdir(release_file_path):
        source_path = os.path.join(release_file_path, item)
        destination_path = os.path.join(current_task_path, item)

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



