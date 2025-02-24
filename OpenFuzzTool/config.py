import json
from pathlib import Path
from typing import Dict
import random
import string
import os
import re

class ConfigLoader:
    def __init__(self, current_directory: str):
        self.ALLFuzzWorkPath = os.path.join(current_directory, 'FuzzWorkDir')

    def generate_config(self,file_path):
        """加载并预处理配置文件"""
        Inputconfig = self.load_Inputconfig(file_path)
        # 生成4个字符的随机字符串作为ProjectID
        ProjectID = ''.join(random.choices(string.ascii_letters + string.digits, k=4))
        self.currentworkpath = Path(os.path.abspath(self.ALLFuzzWorkPath)).joinpath(f"{Inputconfig['program_name']}_{ProjectID}")
        self.fuzz_time = self.parse_fuzz_time(Inputconfig["afl_fuzz_args"]['fuzz_time'])
        self.UpladFile = Inputconfig['source_code_path']
        self.bin_cmd = Inputconfig["afl_fuzz_args"]['fuzz_target']
        self.extractdir = Path(os.path.abspath(self.ALLFuzzWorkPath)).joinpath(f"{Inputconfig['program_name']}_{ProjectID}").joinpath("extractdir")#压缩包解压目录
        self.container_name = f"{Inputconfig['program_name']}_{ProjectID}"
        self.executable = self.bin_cmd.split()[0]

    def parse_fuzz_time(self,fuzz_time):
        # 使用正则表达式提取数字和单位
        match = re.match(r'(\d+)\s*(\w+)', fuzz_time)
        if not match:
            raise ValueError("Invalid fuzz_time format")

        value, unit = match.groups()
        value = int(value)

        # 根据单位转换为秒
        if unit in ['s', 'sec', 'second', 'seconds']:
            return value
        elif unit in ['m', 'min', 'minute', 'minutes']:
            return value * 60
        elif unit in ['h', 'hr', 'hour', 'hours']:
            return value * 3600
        elif unit in ['d', 'day', 'days']:
            return value * 86400
        elif unit in ['month', 'months']:
            return value * 2592000  # 假设一个月为30天
        else:
            # raise ValueError("Unknown time unit")
            return 60

    def convert_path(self,host_path,bind_mount,to_docker=False):
        """
        将宿主机路径转换为 Docker 路径，或将 Docker 路径转换为宿主机路径。
        
        :param host_path: 输入路径
        :param bind_mount: 绑定挂载的映射字典 {宿主机路径: Docker路径}
        :param to_docker: 如果为True，表示从宿主机路径转换为Docker路径，False表示反向转换
        :return: 转换后的路径
        """
        if to_docker:  # 从宿主机路径到Docker路径
            for host_dir, docker_dir in bind_mount.items():
                if host_path.startswith(host_dir):  # 检查宿主机路径是否在映射路径下
                    # 获取宿主机路径相对于绑定路径的部分，并替换为容器内的路径
                    docker_path = host_path.replace(host_dir, docker_dir, 1)
                    return docker_path
            return host_path  # 如果没有找到映射关系，返回原路径
        else:  # 从Docker路径到宿主机路径
            for host_dir, docker_dir in bind_mount.items():
                if host_path.startswith(docker_dir):  # 检查容器路径是否在映射路径下
                    # 获取Docker路径相对于绑定路径的部分，并替换为宿主机路径
                    host_path = host_path.replace(docker_dir, host_dir, 1)
                    return host_path
            return host_path  # 如果没有找到映射关系，返回原路径

    def updatebin_cmd(self,binpath,bind_mount):
        dokcertargetbinpath = self.convert_path(binpath,bind_mount,to_docker=True)
        newbinary_cmd = f"{dokcertargetbinpath} {self.bin_cmd[len(self.executable):]}"
        self.bin_cmd = newbinary_cmd

    def load_Inputconfig(self, file_path: str) -> dict:
        """加载并预处理配置文件"""
        with open(file_path) as f:
            config = json.load(f)
            # if not self.validate_config(config):
            #     raise ValueError("Invalid configuration format")
            return config
        
    # def validate_config(self, config: dict) -> bool:
    #     """验证配置文件完整性"""
    #     required_keys = {'project_id', 'program_name', 'UpladFile',
    #                     'Urls', 'version','fuzz_time','parallel','bin_cmd'}
    #     return required_keys.issubset(config.keys())