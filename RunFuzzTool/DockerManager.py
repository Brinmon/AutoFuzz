from RunFuzzTool import *

def CreateAFLDocker(client, container_name, bind_mount=None, use_existing=False):
    """
    启动 Docker 容器，并使用标签来标识容器，便于后续查找。
    如果容器已经存在且 use_existing 为 True，则返回已有容器；否则停止并删除已有容器，启动新容器。
    支持挂载本地文件夹到容器内。
    
    :param client: Docker 客户端对象
    :param container_name: 容器名称
    :param bind_mount: 本地文件夹挂载路径及容器内路径的字典 {local_path: container_path}
    :param use_existing: 是否使用已经存在的容器，如果为 True 则返回已有容器
    :return: 启动的容器对象
    """
    # 检查容器是否已经存在
    try:
        existing_container = client.containers.get(container_name)
        if use_existing:
            print(f"Container {container_name} already exists. Returning the existing container.")
            return existing_container
        else:
            # 如果容器存在且不重用，则停止并删除它
            print(f"Container {container_name} already exists. Stopping and removing it...")
            existing_container.stop()
            existing_container.remove()
    except docker.errors.NotFound:
        # 如果容器不存在，继续
        print(f"Container {container_name} does not exist. Proceeding to create it...")
    except Exception as e:
        # 处理其他可能的异常
        print(f"An error occurred: {e}")
        return None

    # 如果需要挂载文件夹，添加 volumes 参数，统一服务器与docker内的时间
    volumes = {
        '/etc/localtime': {'bind': '/etc/localtime', 'mode': 'ro'},
        '/etc/timezone': {'bind': '/etc/timezone', 'mode': 'ro'}
    }
    if bind_mount:
        for local_path, container_path in bind_mount.items():
            volumes[local_path] = {'bind': container_path, 'mode': 'rw'}
        print(volumes)

    # 启动容器
    try:
        # 启动新的容器
        container = client.containers.run(
            "aflplusplus/aflplusplus",  # 假设使用 AFL++ 镜像
            name=container_name,
            detach=True,
            auto_remove=True,  # 不自动删除容器，便于后续操作
            labels={'project': container_name},  # 设置标签
            volumes=volumes,  # 挂载文件夹
            tty=True,  # 保持终端
            stdin_open=True,  # 保持标准输入
        )
        print(f"Container {container_name} started successfully.")
        return container
    except Exception as e:
        print(f"Failed to start container: {e}")
        return None
    
def execute_commands_in_container(container, commands, CurrentWorkDir, log_file="/tmp/dockerinfo.txt", RUNCMDtimeout=800):
    """
    """
    # 使用主机的路径来检查和清空日志文件
    host_log_file = os.path.join(CurrentWorkDir, "dockerinfo.txt")

    # 确保命令列表不为空
    if not commands:
        print("命令列表为空，无需执行。")
        return

    # 定义全局变量存储命令执行结果
    global exit_code_Current, output_Current
    exit_code_Current = None
    output_Current = None

    # 循环执行每个命令
    for command in commands:
        print(f"正在执行命令: {command}")

        # 重定向命令输出到日志文件
        exec_command = f"bash -c '{command} >> {log_file} 2>&1'"

        # 使用 threading 实现超时控制
        def run_command():
            global exit_code_Current, output_Current
            exit_code_Current, output_Current = container.exec_run(exec_command, detach=False, stdout=True, stderr=True)

        # 创建并启动线程
        thread = threading.Thread(target=run_command)
        thread.start()

        # 等待超时时间
        thread.join(timeout=RUNCMDtimeout)

        # 如果线程仍然存活，说明超时
        if thread.is_alive():
            print(f"命令执行超时: {command}，已终止。")
            # 终止容器中的命令
            container.exec_run("bash -c 'killall -9 bash'", detach=True) #该命令并未终止afl的模糊测试进程
            continue  # 跳过当前命令，继续执行下一个命令

        # 检查命令的退出状态码
        if exit_code_Current != 0:
            print(f"命令执行失败: {command}")
            print("状态码的值:",exit_code_Current)
            # 读取日志文件
            with open(host_log_file, 'r') as f:
                lines = f.readlines()
                # 如果日志文件行数大于 20，读取最后 20 行；否则读取全部行
                last_lines = ''.join(lines[-20:]) if len(lines) > 20 else ''.join(lines)
            print(f"日志文件最后 20 行内容:\n{last_lines}")
            return False
        else:
            print(f"命令执行成功: {command}")
    print("所有命令已执行完成。")
    return True



def check_and_stop_container(client,container_name):
    """
    检测容器是否存在，如果存在则停止容器
    :param container_name: 容器名称或 ID
    """

    try:
        # 获取容器对象
        container = client.containers.get(container_name)
        print(f"容器 {container_name} 存在，正在停止...")
        
        # 停止容器
        container.stop()
        print(f"容器 {container_name} 已停止。")
    except docker.errors.NotFound:
        print(f"容器 {container_name} 不存在。")
    except Exception as e:
        print(f"检测或停止容器时出错: {e}")


def BuildTargetProjectInDocker(container, CurrentWorkDir):
    print(f"完整的编译目标项目")
    build_commands = [
        "rm -rf /tmp/out",  # 删除初始化文件夹
        "rm -f /tmp/dockerinfo.txt",  # 删除文件
        "touch /tmp/dockerinfo.txt",  # 重新创建文件
        'chmod -R 777 /tmp',
        "echo '开始构建fuzz目标'",
        "cd /tmp && bash ./Build.sh",  # 构建命令
        "echo '构建和启动完成'"
    ]

    buildresult = execute_commands_in_container(container,build_commands,CurrentWorkDir)
    return buildresult

def DockerRunAFL(dokcertargetbinpath,newbinary_cmd,Currentcontainer,CurrentTaskPath,fuzz_time):
    aflseed = 123

    #执行命令
    # 创建命令列表
    commands_run = [
        "echo '开始测试目标程序是否可以运行'",
        f"chmod 777 {dokcertargetbinpath}",
        f"cd /tmp && AFL_MAP_SIZE=10000000 afl-fuzz -i ./input -o ./out -s {aflseed} -- {newbinary_cmd}", # 构建命令
        "chmod -R 777 /tmp/out"  #由于运行后共享文件夹内并未将docker内的文件共享出来所以多赋予权限
    ]
    fuzzresult = execute_commands_in_container(Currentcontainer,commands_run,CurrentTaskPath,RUNCMDtimeout=int(fuzz_time))
    return fuzzresult


def ExecuteCmdInDocker(container, command):
    """在 Docker 容器中执行命令并返回执行结果"""
    exit_code_current = None
    output_current = None
    exec_command = f"bash -c '{command}'"
    exit_code_current, output_current = container.exec_run(exec_command, detach=False, stdout=True, stderr=True)

    if exit_code_current == 0:
        return {"status": "success", "output": output_current.decode("utf-8")}
    else:
        return {"status": "error", "output": output_current.decode("utf-8"), "exit_code": exit_code_current}

def parse_summary_stats(text):
    """解析命令输出中的 Summary stats 并返回 JSON 格式"""
    summary_start = text.find("Summary stats")
    if summary_start == -1:
        return None
    
    summary_text = text[summary_start:].split("=============")[1].strip()
    
    data = {}
    for line in summary_text.split('\n'):
        line = line.strip()
        if line and ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            data[key] = value

    # 判断是否所有重要字段为空或为 0
    if (data.get("Fuzzers alive", "0") == "0" and
        data.get("Total run time", "0") == "0 seconds" and
        data.get("Total execs", "0 thousands") == "0 thousands" and
        data.get("Cumulative speed", "0 execs/sec") == "0 execs/sec" and
        data.get("Pending items", "0 faves, 0 total") == "0 faves, 0 total" and
        data.get("Crashes saved", "0") == "0" and
        data.get("Hangs saved", "0") == "0"):
        return None  # 返回 None 表示没有有效数据，不需要更新文件
    
    return data

def save_status_to_file(status_data, directory):
    """将命令执行结果以 JSON 格式保存到指定目录的文件"""
    # 确保目录存在
    if not os.path.exists(directory):
        os.makedirs(directory)

    # 定义文件路径
    file_path = os.path.join(directory, "FuzzStatus.json")

    with open(file_path, "w") as f:
        json.dump(status_data, f, indent=4)