import argparse
from RunFuzzTool.EnvInit import *
from RunFuzzTool.DockerManager import *
from RunFuzzTool.PVManager import *
from RunFuzzTool.decompression_tool import *
from RunFuzzTool.decompression_tool import decompressionALL
from RunFuzzTool.classify import *


# 全局标志，用于控制线程停止
GetAFLFuzzStatusstop_thread = False

def GetAFLFuzzStatus(container,dirpath):
    """启动一个线程执行命令并保存输出到文件"""
    global GetAFLFuzzStatusstop_thread
    while not GetAFLFuzzStatusstop_thread:
        result = ExecuteCmdInDocker(container, "chmod -R 777 /tmp && afl-whatsup /tmp/out/")
        # print(result)
        if 'error' not in result['status']:
            parsed_data = parse_summary_stats(result['output'])
            # print(parsed_data)
            if parsed_data:
                save_status_to_file(parsed_data,dirpath)
        
        # 每隔一定时间重新执行命令，避免过于频繁的执行
        time.sleep(5)

def stop_thread_execution():
    """停止执行线程"""
    global GetAFLFuzzStatusstop_thread
    GetAFLFuzzStatusstop_thread = True

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

    ReleaseFilePath = None
    if IsExistReleaseValue == False :
        sys.exit(0)
    elif IsExistReleaseValue == None:
        print("使用正常的运行Build.sh脚本正常编译项目文件！并且需要存储！")
        decompressionALL(UpladFile,CurrentTaskPath) #解压目标数据
    else :
        #发现目标后将已经编译完成的数据复制过来直接开启模糊测试
        #将目标文件夹的数据都复制到目标文件夹
        versioncontext = FuzzTaskInfo["version"]
        ReleaseFilePath = Path(get_projection_version_manager()).joinpath(f"{versioncontext}")
        copy_files_to_current_task(ReleaseFilePath,CurrentTaskPath)

    # 创建 Docker 客户端
    Mainclient = docker.from_env()
    bind_mount = {f'{CurrentTaskPath}': '/tmp'}
    dockername = f"{FuzzTaskName}_{ProjectID}"  #避免测试同一个项目时候发生冲突
    Currentcontainer = CreateAFLDocker(Mainclient,dockername,bind_mount,use_existing=True)


    # print(f"为docker内的容器设置默认初始化环境！")
    # init_commands = [
    #     "rm -rf /tmp/out",  # 删除初始化文件夹
    #     "rm -f /tmp/dockerinfo.txt",  # 删除文件
    #     "touch /tmp/dockerinfo.txt",  # 重新创建文件
    #     'chmod -R 777 /tmp'
    # ]

    # execute_commands_in_container(Currentcontainer,init_commands,CurrentTaskPath)
    # print("查看生成的命令和信息:",init_commands)

    # #如果模式是运行build.sh脚本则运行以下步骤:
    # if IsExistReleaseValue == None:
    #     #创建命令列表,执行编译命令
    #     commands_build = [
    #         "echo '开始构建fuzz目标'",
    #         "cd /tmp && bash ./Build.sh",  # 构建命令
    #         "echo '构建和启动完成'"
    #     ]
    #     buildresult = execute_commands_in_container(Currentcontainer,commands_build,CurrentTaskPath)
    #     rebuildtime = 0
    #     while rebuildtime <= 5:
    #         if buildresult == False: #如果编译失败尝试删除所有文件重新解压目录
    #             print("如果编译失败尝试删除所有文件重新解压目录!")
    #             #创建命令列表,执行编译命令
    #             commands_deleteall = [
    #                 "echo '开始尝试重新编译目标'",
    #                 "rm -rf /tmp/*",  # 构建命令
    #                 "echo '删除完成'"
    #             ]
    #             execute_commands_in_container(Currentcontainer,commands_deleteall,CurrentTaskPath)
    #             decompressionALL(UpladFile,CurrentTaskPath) #解压目标数据
    #             buildresult = BuildTargetProjectInDocker(Currentcontainer,CurrentTaskPath)
    #             rebuildtime = rebuildtime + 1
    #         elif buildresult == True:
    #             print("目标项目,重新编译成功!")
    #             #将编译好的文件按照版本存储起来
    #             #将CurrentTaskPath目录中的文件全部复制到一个新的目录ReleaseFilePath = Path(get_projection_version_manager()).joinpath(f"{versioncontext}")
    #             #并且更新json文件调用这个函数即可
    #             versioncontext = FuzzTaskInfo["version"]
    #             FinishBuildFilePath = Path(get_projection_version_manager()).joinpath(f"{versioncontext}")
    #             copy_files_to_current_task(CurrentTaskPath,FinishBuildFilePath)
    #             FuzzConfigInfo = read_config(os.getenv('FUZZCONFIGFILE')) 
    #             BaseFileProcessJson(FuzzConfigInfo)
    #             break
    #         if rebuildtime == 5 :
    #             raise RuntimeError("重复编译5次都失败了!结束编译!")

    #我需要在一个目录中寻找指定文件名的可执行文件
    targetbinname = binary_cmd.split()[0]
    hosttargetbinpath = find_executable_in_directory(CurrentTaskPath,targetbinname)
    dokcertargetbinpath = convert_host_to_docker_path(hosttargetbinpath,bind_mount)
    newbinary_cmd = f"{dokcertargetbinpath} {binary_cmd[len(targetbinname):]}"

    # # 启动线程执行命令
    # GetFuzzStatusthread = threading.Thread(target=GetAFLFuzzStatus, args=(Currentcontainer,CurrentTaskPath,))
    # GetFuzzStatusthread.start()

    # #执行afl fuzz命令
    # aflfuzztime = 0
    # while aflfuzztime <= 5 :
    #     fuzzresult = DockerRunAFL(dokcertargetbinpath,newbinary_cmd,Currentcontainer,CurrentTaskPath,fuzz_time)
    #     if fuzzresult == False :
    #         print("尝试运行AFL发现运行失败了!")
    #         #创建命令列表,执行编译命令
    #         commands_deleteall = [
    #             "echo '开始尝试重新编译目标'",
    #             "rm -rf /tmp/*",  # 构建命令
    #             "echo '删除完成'"
    #         ]
    #         execute_commands_in_container(Currentcontainer,commands_deleteall,CurrentTaskPath)
    #         copy_files_to_current_task(ReleaseFilePath,CurrentTaskPath)
    #         aflfuzztime = aflfuzztime + 1
    #         time.sleep(2)
    #     elif fuzzresult == True :
    #         print("成功运行fuzz")
    #         break
    #     if aflfuzztime == 5 :
    #         raise RuntimeError("重复fuzz5次都失败了!结束fuzz!")
        
    # #我需要开辟一个线程不断在docker内读取线程内的数据并且输出json数据
    # #AFL运行完毕，关闭线程
    # stop_thread_execution()
    # # 等待线程完全结束
    # GetFuzzStatusthread.join()
    # print("Command execution stopped and output saved to FuzzStatus.json")

    #开始最后的整理Crash样本文件
    classify_crashes(Currentcontainer,newbinary_cmd,CurrentTaskPath)


    #结束docker容器的运行
    # if Currentcontainer:
        # check_and_stop_container(Mainclient,Currentcontainer.id)  # 使用容器的 ID



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
