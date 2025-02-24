import argparse
import os
from OpenFuzzTool.config import ConfigLoader
from OpenFuzzTool.preprocessor import FilePreprocessor
from OpenFuzzTool.docker_manager import DockerManager
from OpenFuzzTool.build import BuildExecutor
from OpenFuzzTool.fuzzer import AFLRunner
from OpenFuzzTool.analyzer import ResultAnalyzer, ReportGenerator


def AutoFuzzMain(config_path):
    # 获取当前文件的绝对路径
    current_file_path = os.path.abspath(__file__)
    # 获取当前文件所在的目录
    current_directory = os.path.dirname(current_file_path)

    # 创建并启动线程
    loader = ConfigLoader(current_directory)
    processor = FilePreprocessor()
    
    # 执行流程
    loader.generate_config(config_path)
    fuzzconfig = loader
    bind_mount = {f'{fuzzconfig.currentworkpath}': '/tmp'}
    docker_mgr = DockerManager(fuzzconfig.container_name,bind_mount)

    #清理工作目录
    processor.clean_workspace(fuzzconfig.currentworkpath)

    #解压文件
    processor.decompressionALL(fuzzconfig.UpladFile,fuzzconfig.extractdir)
    processor.copy_files_to_workspace(fuzzconfig.extractdir,fuzzconfig.currentworkpath)

    #创建docker
    docker_mgr.CreateAFLDocker()

    buildexe = BuildExecutor()

    buildexe.inital_build(docker_mgr.containerid)
    IsBuildSuccess = buildexe.check_buildsuccess(docker_mgr.containerid,fuzzconfig.currentworkpath,fuzzconfig.executable)
    if IsBuildSuccess == None :
        raise Exception("构建失败！")
    fuzzconfig.updatebin_cmd(buildexe.binpath,bind_mount)

    aflrunner = AFLRunner(fuzzconfig.bin_cmd,fuzzconfig.fuzz_time,str(fuzzconfig.currentworkpath.joinpath("FuzzStatus.json")))
    aflrunner.start_fuzzing(docker_mgr.containerid)

    buildexe.inital_env(docker_mgr.containerid)

    docker_mgr.stop_docker()
    


def analyze_fuzz_results(FuzzTaskInfo):
    pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-jsonfile',
                        help='读取json文件',
                        type=str, default=False)

    parser.add_argument('-analyze',
                        help='调用 analyze_fuzz_results 函数分析fuzz结果',
                        action='store_true', default=False)

    args = parser.parse_args()

    if args.jsonfile:
        if args.analyze:
            # 调用 analyze_fuzz_results 函数分析fuzz结果
            analyze_fuzz_results(args.jsonfile)
            pass

        # 调用 AutoFuzzMain 函数，自动化Fuuzz
        AutoFuzzMain(args.jsonfile)