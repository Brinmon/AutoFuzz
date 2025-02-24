"""
 /≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡\
 |✨            CyberPunk Code Annotation v2.0            ✨|
 \≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡/

(ﾉ>ω<)ﾉ 作者: liyong @ 2025-02-25-00:49  
ヽ(>▽<)ノ 作者:  @
🛸 模块功能：自动Fuzz测试引擎的结果分析模块
🔥!! 此代码可能召唤电子恶魔！！ 
🔥!! 运行前请准备三只烤鸡腿作为祭品！！
"""

import os
import subprocess
import json
from typing import Dict

class ResultAnalyzer:
    def __init__(self, container=None):
        """初始化分析器
        Args:
            container: Docker容器实例
        """
        self.container = container

    def process_crashes(self, output_dir: str):
        """处理crash样本"""
        crash_dir = os.path.join(output_dir, 'crashes')
        self._deduplicate(crash_dir)
        self._generate_reports(crash_dir)

    def _deduplicate(self, directory: str):
        """使用afl-cmin去重
        Args:
            directory: crash目录的本地路径
        """
        if not self.container:
            raise RuntimeError("需要Docker容器实例来执行afl-cmin命令")
        
        # 假设本地目录已经被挂载到容器的/workspace目录下
        container_dir = os.path.join('/workspace', os.path.basename(directory))
        container_dir_min = container_dir + '_min'
        
        # 在容器内执行afl-cmin命令
        result = self.container.exec_run(
            cmd=["afl-cmin", "-i", container_dir, "-o", container_dir_min],
            workdir="/workspace"
        )
        
        if result.exit_code != 0:
            raise RuntimeError(f"afl-cmin命令执行失败: {result.output.decode()}")

    def _generate_reports(self, crash_dir: str):
        """生成ASAN报告"""
        for crash in os.listdir(crash_dir):
            if crash.startswith('id:'):
                self._analyze_crash(os.path.join(crash_dir, crash))

    def _analyze_crash(self, crash_file: str):
        """分析单个崩溃样本"""
        # 实现具体的崩溃分析逻辑
        pass

class ReportGenerator:
    def create_summary(self, output_dir: str) -> Dict:
        """生成结构化报告"""
        return {
            "crashes": self._count_files(os.path.join(output_dir, 'crashes')),
            "hangs": self._count_files(os.path.join(output_dir, 'hangs')),
            "stats": self._parse_stats(os.path.join(output_dir, 'fuzzer_stats'))
        }

    def _count_files(self, directory: str) -> int:
        """统计目录中的文件数量"""
        return len([f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))])

    def _parse_stats(self, stats_file: str) -> Dict:
        """解析AFL状态文件"""
        stats = {}
        if os.path.exists(stats_file):
            with open(stats_file) as f:
                for line in f:
                    if ':' in line:
                        key, value = line.strip().split(':', 1)
                        stats[key.strip()] = value.strip()
        return stats