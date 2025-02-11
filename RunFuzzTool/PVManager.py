from RunFuzzTool import *

def BaseFileProcessJson(FuzzConfigInfo):   
    """
    基于文件路径生成编译完成程序的版本管理
    """ 
    # 获取 PVManager 文件夹路径
    pv_manager_path = FuzzConfigInfo.get("ProjectionVerionManager")
    if not pv_manager_path:
        raise ValueError("ProjectionVerionManager path not found in FuzzConfig.json")
    
    # 初始化 JSON 结构
    result = {
        "TotalProjects": 0,
        "Projects": []
    }
    
    # 遍历 PVManager 文件夹
    for project_dir in os.listdir(pv_manager_path):
        project_path = os.path.join(pv_manager_path, project_dir)
        if os.path.isdir(project_path):
            # 初始化项目信息
            project_info = {
                "ProjectNameVersion": project_dir,
                "CompiledResults": []
            }
            
            # 查找 Build.sh 文件
            build_script_path = os.path.join(project_path, "Build.sh")
            if os.path.isfile(build_script_path):
                # 初始化编译结果信息
                compiled_result = {
                    "BuildScript": build_script_path,
                    "ReleaseFile": [],
                    "InputSamples": [],
                    "BuildTimestamp": datetime.now(timezone.utc).isoformat()
                }
                
                # 查找 ReleaseFile 文件夹
                release_file_path = None
                for item in os.listdir(project_path):
                    item_path = os.path.join(project_path, item)
                    if os.path.isdir(item_path) and item != "input":
                        release_file_path = item_path
                        break
                
                if release_file_path:
                    compiled_result["ReleaseFile"].append({
                        "FileName": os.path.basename(release_file_path),
                        "FileType": "directory",
                        "Path": release_file_path
                    })
                
                # 查找 input 文件夹
                input_path = os.path.join(project_path, "input")
                if os.path.isdir(input_path):
                    # 获取 input 文件夹中的文件类型
                    sample_types = set()
                    for root, dirs, files in os.walk(input_path):
                        for file in files:
                            _, ext = os.path.splitext(file)
                            if ext:
                                sample_types.add(ext[1:])  # 去掉点号
                    
                    compiled_result["InputSamples"].append({
                        "FileName": "input",
                        "FileType": "directory",
                        "Path": input_path,
                        "SampleType": list(sample_types)
                    })
                
                # 将编译结果添加到项目信息中
                project_info["CompiledResults"].append(compiled_result)
            
            # 将项目信息添加到结果中
            result["Projects"].append(project_info)
            result["TotalProjects"] += 1
    
    # 将结果写入 JSON 文件
    output_json_path = os.path.join(pv_manager_path, "PVManager.json")
    with open(output_json_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"JSON file generated at: {output_json_path}")


def CheckIsExistRelease(ReleaseVersion):
    """
    检查项目版本是否存在于备份文件中，并返回匹配的项目数据。

    Args:
        ReleaseVersion (str): 需要检查的发布版本号，通常为项目的版本号字符串（例如 "fuzzgoat_1.0"）。
        FuzzConfigFilePath (str): FuzzConfig.json 文件的完整路径，包含 ProjectionVerionManager 字段。

    Description:
        该函数用于检查是否存在与传入的 ReleaseVersion 匹配的备份文件。首先，函数读取指定的 FuzzConfig.json 文件，
        获取其中的 ProjectionVerionManager 字段值，然后根据该路径找到 PVManager.json 文件。
        接着，函数会遍历 PVManager.json 文件中的 "Projects" 字段，查找每个项目的 "ProjectNameVersion" 是否与
        ReleaseVersion 字符串相匹配。如果找到匹配的版本，函数返回该项目的 JSON 数据；如果未找到匹配项，
        则返回 False，表示需要重新编译。

    Returns:
        dict: 如果 PVManager.json 文件中存在与 ReleaseVersion 匹配的项目版本，返回该项目的 JSON 数据；
              否则，返回 False。

    Notes:
        如果读取 FuzzConfig.json 或 PVManager.json 文件时发生错误，函数会捕获异常并打印错误信息，同时返回 False。
    """
    
    # Step 1: 读取配置文件 FuzzConfigFilePath，获取 ProjectionVerionManager 路径
    FuzzConfigFilePath = os.getenv('FUZZCONFIGFILE')
    try:
        with open(FuzzConfigFilePath, 'r') as f:
            fuzz_config = json.load(f)
    except Exception as e:
        print(f"Error reading FuzzConfig file: {e}")
        return False

    # Step 2: 获取 ProjectionVerionManager 字段，找出 PVManager.json 的路径
    pv_manager_path = fuzz_config.get("ProjectionVerionManager")
    if not pv_manager_path:
        print("ProjectionVerionManager path not found in FuzzConfig.json")
        return False
    
    # Step 3: 读取 PVManager.json 文件
    pv_manager_json_path = os.path.join(pv_manager_path, "PVManager.json")
    if not os.path.isfile(pv_manager_json_path):
        print(f"{pv_manager_json_path} not found.")
        return False
    
    try:
        with open(pv_manager_json_path, 'r') as f:
            pv_manager_data = json.load(f)
    except Exception as e:
        print(f"Error reading PVManager.json file: {e}")
        return False

    # Step 4: 检查 "Projects" 字段下的每个 "ProjectNameVersion"
    for project in pv_manager_data.get("Projects", []):
        project_name_version = project.get("ProjectNameVersion")
        if project_name_version == ReleaseVersion:
            # 找到匹配的版本，返回该项目的数据
            return project
    
    # 如果没有找到匹配项，返回 False
    return None