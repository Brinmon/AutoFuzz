"""
 /≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡\
 |✨            CyberPunk Code Annotation v2.0            ✨|
 \≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡/

(ﾉ>ω<)ﾉ 作者: liyong @ 2025-02-25-00:49  
ヽ(>▽<)ノ 作者:  @
🛸 模块功能：自动Fuzz测试引擎的结果环境编译模块
🔥!! 此代码可能召唤电子恶魔！！ 
🔥!! 运行前请准备三只烤鸡腿作为祭品！！
"""

import os
import logging
import concurrent.futures
import time
import subprocess
from typing import List, Dict, Any
from docker.models.containers import Container

class BuildExecutor:
    def __init__(self):
        self.max_retries = 3
        self.timeout = 600  # 10分钟超时
        self.parallel_jobs = 4

    def execute_command(self, container: Container, command: str, workdir: str = "/tmp", env: Dict[str, str] = {}) -> bool:
        """执行单个命令并处理结果"""
        for attempt in range(self.max_retries):
            try:
                exit_code, output = container.exec_run(
                    command,
                    workdir=workdir,
                    environment=env,
                    stream=True
                )

                # 实时输出执行日志
                for line in output:
                    logging.info(f"Command output: {line.decode().strip()}")

                if exit_code == 0 or exit_code == None:
                    logging.info(f"Command executed successfully: {command}")
                    return True
                else:
                    print(exit_code)
                    logging.error(f"Command failed (attempt {attempt + 1}/{self.max_retries}): {command}")
                    if attempt < self.max_retries - 1:
                        time.sleep(2 ** attempt)  # 指数退避重试
                        continue
            except Exception as e:
                logging.error(f"Error executing command: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return False
        return False

    def parallel_execute(self, container: Container, commands: List[str], workdir: str = "/tmp", env: Dict[str, str] = {}) -> bool:
        """并行执行多个命令"""
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.parallel_jobs) as executor:
            futures = []
            for cmd in commands:
                futures.append(executor.submit(self.execute_command, container, cmd, workdir, env))

            # 等待所有命令执行完成
            results = []
            for future in concurrent.futures.as_completed(futures):
                try:
                    results.append(future.result())
                except Exception as e:
                    logging.error(f"Command execution failed: {str(e)}")
                    results.append(False)

            return all(results)

    def sequential_execute(self, container: Container, commands: List[str], workdir: str = "/tmp", env: Dict[str, str] = {}) -> bool:
        """顺序执行多个命令，如果某个命令失败则停止执行"""
        for cmd in commands:
            if not self.execute_command(container, cmd, workdir, env):
                logging.error(f"Sequential execution stopped due to command failure: {cmd}")
                return False
        return True

    def inital_build(self, container: Container) -> bool:
        """在容器内执行构建过程"""
        try:
            commands =[
                'chmod -R 777 /tmp/',
                'bash Build.sh'
            ]

            if not commands:
                logging.warning("No commands found in build script")
                return True

            logging.info(f"Executing {len(commands)} initialization commands...")
            start_time = time.time()

            # 并行执行命令
            success = self.sequential_execute(container, commands)

            execution_time = time.time() - start_time
            logging.info(f"Initialization completed in {execution_time:.2f} seconds")

            if not success:
                raise RuntimeError("One or more initialization commands failed")

            return True

        except Exception as e:
            logging.error(f"Initialization failed: {str(e)}")
            return False

    def inital_env(self, container: Container) -> bool:
        """在容器内执行构建过程"""
        try:
            commands =[
                'chmod -R 777 /tmp/'
            ]

            if not commands:
                logging.warning("No commands found in build script")
                return True

            logging.info(f"Executing {len(commands)} initialization commands...")
            start_time = time.time()

            # 并行执行命令
            success = self.sequential_execute(container, commands)

            execution_time = time.time() - start_time
            logging.info(f"Initialization completed in {execution_time:.2f} seconds")

            if not success:
                raise RuntimeError("One or more initialization commands failed")

            return True

        except Exception as e:
            logging.error(f"Initialization failed: {str(e)}")
            return False

    def check_buildsuccess(self, container: Container,directory:str,filename:str) -> bool:
        matching_files = []
        
        # 遍历目录下的所有文件和子目录
        for root, dirs, files in os.walk(directory):
            if filename in files:
                full_path = os.path.join(root, filename)
                # 使用 'file' 命令来检测文件类型
                try:
                    result = subprocess.run(['file', full_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    if result.returncode == 0:
                        file_info = result.stdout.decode('utf-8')
                        if 'executable' in file_info or 'script' in file_info:
                            matching_files.append(full_path)
                except Exception as e:
                    logging.info(f"错误：无法执行 'file' 命令，原因: {e}")
        
        if len(matching_files) > 1:
            logging.info(f"警告：在目录 {directory} 中找到了多个可执行文件：")
            for f in matching_files:
                logging.info(f)
        
        if matching_files:
            self.binpath = matching_files[0]
            return matching_files[0]
        else:
            logging.error(f"未找到可执行文件 {filename}。")
            return None