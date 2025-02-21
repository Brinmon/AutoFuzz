import docker
import os
import argparse

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
        print(f"An error occurred while checking existing container: {e}")
        return None

    # 如果需要挂载文件夹，添加 volumes 参数，统一服务器与docker内的时间
    volumes = {
        '/etc/localtime': {'bind': '/etc/localtime', 'mode': 'ro'},
        '/etc/timezone': {'bind': '/etc/timezone', 'mode': 'ro'}
    }
    if bind_mount:
        for local_path, container_path in bind_mount.items():
            # 检查本地路径是否存在，如果不存在则创建
            if not os.path.exists(local_path):
                print(f"Local path {local_path} does not exist. Creating it...")
                os.makedirs(local_path, exist_ok=True)
            volumes[local_path] = {'bind': container_path, 'mode': 'rw'}
        print(f"Volumes to be mounted: {volumes}")

    # 启动容器
    try:
        # 启动新的容器
        container = client.containers.run(
            "aflplusplus/aflplusplus",  # 假设使用 AFL++ 镜像
            name=container_name,
            detach=True,
            auto_remove=False,  # 不自动删除容器，便于后续操作
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

# 示例用法
if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="启动 AFL Docker 容器并挂载共享文件夹。")
    parser.add_argument("--local_dir", type=str, required=True, help="本地文件夹路径")
    parser.add_argument("--container_dir", type=str, default="/tmp", help="容器内文件夹路径")
    parser.add_argument("--container_name", type=str, default="my_afl_container", help="容器名称")
    args = parser.parse_args()

    # 创建 Docker 客户端
    client = docker.from_env()

    # 设置挂载路径
    bind_mount = {
        args.local_dir: args.container_dir  # 本地路径: 容器内路径
    }

    # 启动容器
    container = CreateAFLDocker(client, args.container_name, bind_mount=bind_mount)
    if container:
        print(f"Container ID: {container.id}")