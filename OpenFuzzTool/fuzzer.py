"""
 /≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡\
 |✨            CyberPunk Code Annotation v2.0            ✨|
 \≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡/

(ﾉ>ω<)ﾉ 作者: liyong @ 2025-02-25-00:49  
ヽ(>▽<)ノ 作者:  @
🛸 模块功能：自动Fuzz测试引擎的fuzz模块
🔥!! 此代码可能召唤电子恶魔！！ 
🔥!! 运行前请准备三只烤鸡腿作为祭品！！
"""

import time
import logging
import concurrent.futures
from typing import List, Dict, Any
from docker.models.containers import Container
import re
import json

class AFLRunner:
    def __init__(self,fuzzbincmd,fuzztime,fuzzing_status_file):
        self.fuzzparallel = 1
        self.fuzzbincmd = fuzzbincmd
        self.fuzztime = fuzztime
        self.fuzzing_status_file = fuzzing_status_file
        self.max_retries = 3
        self.timeout = 600  # 10分钟超时
        self.parallel_jobs = 4

    def start_fuzzing(self, container: Container):
        try:
            env: Dict[str, str] = {}
            env["AFL_MAP_SIZE"] = "10000000"
            commands = f"afl-fuzz -i ./input -o ./output -- {self.fuzzbincmd}"

            logging.info(f"Executing {commands} ...")
            start_time = time.time()

            # 并行执行命令
            success = self.fuzzexecute_command(container, commands, env=env, timeout=self.fuzztime)

            execution_time = time.time() - start_time
            logging.info(f"Initialization completed in {execution_time:.2f} seconds")

            if not success:
                raise RuntimeError("One or more initialization commands failed")

            return True

        except Exception as e:
            logging.error(f"Initialization failed: {str(e)}")
            return False

    def stop_fuzz(self):
        """设置标志以停止当前正在运行的fuzz命令"""
        self._stop_fuzz_flag = True

    def fuzzexecute_command(self, container: Container, command: str, workdir: str = "/tmp", 
                           env: Dict[str, str] = {}, timeout: int = None) -> bool:
        """执行单个命令并处理结果，支持超时和停止标志"""
        # 使用timeout命令包装原命令以限制运行时间
        if timeout is not None:
            command = f"timeout {timeout} {command}"
        
        for attempt in range(self.max_retries):
            self._stop_fuzz_flag = False  # 每次重试前重置停止标志
            try:
                exit_code, output = container.exec_run(
                    command,
                    workdir=workdir,
                    environment=env,
                    stream=True
                )

                #时时输出的原理是output是一个不断迭代的对象（由docker构造），所以可以直接用for循环来遍历
                for line in output:
                    logging.info(f"Command output: {line.decode().strip()}")
                    print(self.fuzzing_status_file)
                    self.get_fuzzing_status(container=container,output_file=self.fuzzing_status_file )
                    #如果检测到模糊测试启动失败，抛出异常
                    if re.search(r"PROGRAM ABORT", line.decode().strip()):  
                        raise Exception("模糊测试启动失败！")
                    if self._stop_fuzz_flag:
                        logging.info("Received stop signal, terminating command...")
                        container.exec_run(f"pkill -f '{command}'")  # 尝试终止命令
                        break

                
                # 处理退出码
                if exit_code == 0 or exit_code is None:
                    logging.info(f"Command executed exit_code: {exit_code}")
                    logging.info(f"Command executed successfully: {command}")
                    return True
                elif timeout is not None and exit_code == 124:
                    logging.info(f"Command terminated due to timeout: {command}")
                    return True  # 根据需求决定是否返回True
                else:
                    logging.error(f"Command failed (attempt {attempt + 1}/{self.max_retries}): {command}")
                    if attempt < self.max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue

            except Exception as e:
                logging.error(f"Error executing command: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return False
        return False

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

    def get_fuzzing_status(self, container: Container, output_file: str = None) -> dict:
        """获取AFL fuzzing的实时状态，并将结果写入JSON文件
        Args:
            container: Docker容器实例
            output_file: 输出JSON文件的路径（可选）
        Returns:
            dict: 包含fuzzing状态的字典，包括总执行次数、路径数等信息
        """

        try:
            print("获取AFL fuzzing的实时状态，并将结果写入JSON文件")
            result = container.exec_run('cat /tmp/output/default/fuzzer_stats ')
            if result.exit_code != 0 and result.exit_code != None:
                logging.info(f"执行后的状态码: {result.exit_code} ")
                return {'error': '无法读取fuzzer_stats文件'}
            logging.info(f"执行读取文件: cat /tmp/output/default/fuzzer_stats ")
            stats = {}
            for line in result.output.decode().splitlines():
                if ':' in line:
                    key, value = line.split(':', 1)
                    stats[key.strip()] = value.strip()
            
            status = {
                'total_execs': stats.get('execs_done', '0'),
                'paths_total': stats.get('paths_total', '0'),
                'paths_found': stats.get('paths_found', '0'),
                'unique_crashes': stats.get('unique_crashes', '0'),
                'last_path': stats.get('last_path', 'none'),
                'last_crash': stats.get('last_crash', 'none')
            }
            
            # 如果指定了输出文件路径，则将状态写入JSON文件
            if output_file:
                try:
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(status, f, indent=4)
                    logging.info(f"状态已写入文件: {output_file}")
                except Exception as e:
                    logging.error(f"写入JSON文件时出错: {str(e)}")
            
            return status
        except Exception as e:
            return {'error': f'获取状态时出错: {str(e)}'}