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
            container.exec_run("bash -c 'killall -9 -1'", detach=True)
            continue  # 跳过当前命令，继续执行下一个命令

        # 检查命令的退出状态码
        if exit_code_Current != 0:
            print(f"命令执行失败: {command}")
            # 读取日志文件
            with open(host_log_file, 'r') as f:
                lines = f.readlines()
                # 如果日志文件行数大于 20，读取最后 20 行；否则读取全部行
                last_lines = ''.join(lines[-20:]) if len(lines) > 20 else ''.join(lines)

            print(f"日志文件最后 20 行内容:\n{last_lines}")
        else:
            print(f"命令执行成功: {command}")
    print("所有命令已执行完成。")

def convert_host_to_docker_path(host_path, bind_mount):
    # 遍历 bind_mount，找到宿主机路径的映射关系
    for host_dir, docker_dir in bind_mount.items():
        if host_path.startswith(host_dir):  # 检查宿主机路径是否在映射路径下
            # 获取宿主机路径相对于绑定路径的部分，并替换为容器内的路径
            docker_path = host_path.replace(host_dir, docker_dir, 1)
            return docker_path
    # 如果没有找到映射关系，返回原路径
    return host_path