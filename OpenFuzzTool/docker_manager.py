import docker
from docker.models.containers import Container
from typing import Dict

class DockerManager:
    def __init__(self,container_name,bind_mount):
        self.client = docker.from_env()
        self.container_name = container_name
        self.bind_mount = bind_mount


    def CreateAFLDocker(self, use_existing=False):
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
            existing_container = self.client.containers.get(self.container_name)
            if use_existing:
                print(f"Container {self.container_name} already exists. Returning the existing container.")
                return existing_container
            else:
                # 如果容器存在且不重用，则停止并删除它
                print(f"Container {self.container_name} already exists. Stopping and removing it...")
                existing_container.stop()
                existing_container.remove()
        except docker.errors.NotFound:
            # 如果容器不存在，继续
            print(f"Container {self.container_name} does not exist. Proceeding to create it...")
        except Exception as e:
            # 处理其他可能的异常
            print(f"An error occurred: {e}")
            return None

        # 如果需要挂载文件夹，添加 volumes 参数，统一服务器与docker内的时间
        volumes = {
            '/etc/localtime': {'bind': '/etc/localtime', 'mode': 'ro'},
            '/etc/timezone': {'bind': '/etc/timezone', 'mode': 'ro'}
        }
        if self.bind_mount:
            for local_path, container_path in self.bind_mount.items():
                volumes[local_path] = {'bind': container_path, 'mode': 'rw'}
            print(volumes)

        # 启动容器
        try:
            # 启动新的容器
            containerid = self.client.containers.run(
                "aflplusplus/aflplusplus",  # 假设使用 AFL++ 镜像
                name=self.container_name,
                detach=True,
                auto_remove=True,  # 不自动删除容器，便于后续操作
                labels={'project': self.container_name},  # 设置标签
                volumes=volumes,  # 挂载文件夹
                tty=True,  # 保持终端
                stdin_open=True,  # 保持标准输入
            )
            print(f"Container {self.container_name} started successfully.")
            self.containerid = containerid
        except Exception as e:
            print(f"Failed to start container: {e}")
            return None


    def stop_docker(self):
        """
        停止并删除指定名称的 Docker 容器。

        :param client: Docker 客户端对象
        :param container_name: 要停止和删除的容器名称
        """
        try:
            container = self.client.containers.get(self.container_name)
            container.stop()      
            print(f"Container {self.container_name} stopped and removed successfully.")
        except docker.errors.NotFound:
            print(f"Container {self.container_name} not found.")