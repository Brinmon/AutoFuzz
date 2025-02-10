import argparse
from RunFuzzTool.EnvInit import *

def AutoFuzzMain(jsonfile):
    """
    第一步检测版本信息判断是否需要重新编译还是将原有编译好的文件直接进行模糊测试
    如果发现已经存在现有编译好的文件就直接将文件复制过来而无需重新编译
    运行测试目标
    分析运行结果
    """
    pass

if __name__ == '__main__':
    # 获取当前文件的绝对路径
    current_file_path = os.path.abspath(__file__)
    # 获取当前文件所在的目录
    current_directory = os.path.dirname(current_file_path)

    #初始化Fuzz工具所需的配置文件 FuzzConfig.json。
    fuzz_config_path = initialize_fuzz_config(current_directory)
    print(fuzz_config_path)
    #初始化项目版本管理文件 PVManger.json。
    initialize_pv_manager(fuzz_config_path)

    parser = argparse.ArgumentParser()
    parser.add_argument('--jsonfile',
                        help='读取json文件',
                        type=str, required=True, default=None)

    args = parser.parse_args()
    FuzzTaskInfo = read_config(args.jsonfile)
    AutoFuzzMain(FuzzTaskInfo)#
