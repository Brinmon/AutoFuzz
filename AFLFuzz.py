import argparse
import RunFuzzTool
from RunFuzzTool.EnvInit import *
from RunFuzzTool.DockerManager import *
from RunFuzzTool.PVManager import *

def AutoFuzzMain(FuzzTaskInfo):
    """
    第一步检测版本信息判断是否需要重新编译还是将原有编译好的文件直接进行模糊测试
    如果发现已经存在现有编译好的文件就直接将文件复制过来而无需重新编译
    运行测试目标
    分析运行结果
    """

    FuzzTaskName = FuzzTaskInfo["program_name"]
    ProjectID = FuzzTaskInfo["project_id"]
    UpladFile = FuzzTaskInfo['UpladFile']
    fuzz_time = FuzzTaskInfo["fuzz_time"]
    binary_cmd = FuzzTaskInfo["bin_cmd"]

    #检测该项目是否经过源码编译
    IsExistReleaseValue = CheckIsExistRelease(FuzzTaskInfo["version"])

    #创建存放项目文件的文件夹
    CurrentTaskPath = Path(get_fuzz_work_dir()).joinpath(f"{FuzzTaskName}_{ProjectID}")
    os.makedirs(CurrentTaskPath, exist_ok=True)

    if IsExistReleaseValue == False :
        sys.exit(0)
    elif IsExistReleaseValue == None:
        print("使用正常的运行Build.sh脚本正常编译项目文件！并且需要存储！")

    else :
        #发现目标后将已经编译完成的数据复制过来直接开启模糊测试
        #将目标文件夹的数据都复制到目标文件夹
        versioncontext = FuzzTaskInfo["version"]
        ReleaseFilePath = Path(get_projection_version_manager()).joinpath(f"{versioncontext}")
        print(ReleaseFilePath)
        copy_files_to_current_task(ReleaseFilePath,CurrentTaskPath)

    # 创建 Docker 客户端
    # Mainclient = docker.from_env()
    # bind_mount = {f'{CurrentTaskPath}': '/tmp'}
    # dockername = f"{FuzzTaskName}_{ProjectID}"  #避免测试同一个项目时候发生冲突
    # Currentcontainer = CreateAFLDocker(Mainclient,dockername,bind_mount,use_existing=True)




if __name__ == '__main__':
    # 获取当前文件的绝对路径
    current_file_path = os.path.abspath(__file__)
    # 获取当前文件所在的目录
    current_directory = os.path.dirname(current_file_path)

    #初始化Fuzz工具所需的配置文件 FuzzConfig.json。
    fuzz_config_path = initialize_fuzz_config(current_directory)

    # 设置一个环境变量,存储配置文件的路径
    os.environ['FUZZCONFIGFILE'] = fuzz_config_path

    #初始化项目版本管理文件 PVManger.json。
    initialize_pv_manager(fuzz_config_path)

    parser = argparse.ArgumentParser()
    parser.add_argument('-jsonfile',
                        help='读取json文件',
                        type=str, default=False)

    parser.add_argument('-initpvm',
                        help='初始化版本管理器环境',
                        action='store_true', default=False)  

    args = parser.parse_args()

    if args.initpvm:
        FuzzConfigInfo = read_config(os.path.join(current_directory, "FuzzConfig.json")) 
        BaseFileProcessJson(FuzzConfigInfo)

    if args.jsonfile:
        print("开始AutoFuzzMain")
        FuzzTaskInfo = read_config(args.jsonfile)
        AutoFuzzMain(FuzzTaskInfo)#
