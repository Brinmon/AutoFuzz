from RunFuzzTool.DockerManager import *

def sanitize_filename(filename):
    """
    替换文件名中的特殊字符为下划线。
    :param filename: 原始文件名
    :return: 处理后的文件名
    """
    return re.sub(r'[:\/,]', '_', filename)

def write_asan_output_to_file(asan_output, asan_output_file):
    """
    将 ASAN 输出内容写入指定文件
    :param asan_output: ASAN 输出内容（字符串或字节）
    :param asan_output_file: 目标文件路径
    """
    try:
        # 如果 asan_output 是字节类型，解码为字符串
        if isinstance(asan_output, bytes):
            asan_output = asan_output.decode('utf-8', errors='ignore')
        # 将内容写入文件
        with open(asan_output_file, 'w', encoding="utf-8") as f:
            f.write(asan_output)
        print(f"ASAN 输出已成功写入文件: {asan_output_file}")
    except Exception as e:
        print(f"写入文件时发生错误: {e}")

#样本去重
def cmin_crashes(Currentcontainer,newbinary_cmd,CurrentTaskPath):
    print("开始精简crash样本！")
    #执行afl fuzz命令
    aflfuzztime = 0
    #优先创建文件夹
    retoutput = ExecuteCmdInDocker(Currentcontainer,f"mkdir -p /tmp/minimized_crashes && chmod -R 777 /tmp/minimized_crashes")
    while aflfuzztime <= 5 :
        fuzzresult = ExecuteCmdInDocker(Currentcontainer,f"afl-cmin -i /tmp/out/default/crashes/ -o /tmp/minimized_crashes -- {newbinary_cmd}")
        # print(fuzzresult)
        if fuzzresult["status"] == "error" :
            print("精简失败重新精简!")
            aflfuzztime = aflfuzztime + 1
            time.sleep(2)
        elif fuzzresult["status"] == "success" :
            print("成功精简crashes样本！")
            break
        if aflfuzztime == 5 :
            print("重复精简样本5次都失败了!结束直接将文件复制进入目标文件夹!")
            MasterCrashPath = Path(os.path.abspath(CurrentTaskPath)).joinpath("out").joinpath("default").joinpath("crashes")
            MasterMiniCrashPath = Path(os.path.abspath(CurrentTaskPath)).joinpath("minimized_crashes")
            copy_files_to_current_task(MasterCrashPath,MasterMiniCrashPath)
    
    #删除多余的README.txt文件
    ExecuteCmdInDocker(Currentcontainer,f"rm  /tmp/minimized_crashes/README.txt && chmod -R 777 /tmp/minimized_crashes")

def classify_crashes(Currentcontainer,newbinary_cmd,CurrentTaskPath,bind_mount):
    # 构建 MasterCrashPath
    MasterCrashPath = Path(os.path.abspath(CurrentTaskPath)).joinpath("out", "default", "crashes")

    # 检查 crashes 目录是否存在
    if not MasterCrashPath.exists() or not MasterCrashPath.is_dir():
        print(f"崩溃目录 {MasterCrashPath} 不存在。")
        return

    # 获取崩溃目录中的所有文件
    crash_files = os.listdir(MasterCrashPath)

    # 过滤掉 README 文件和其他非崩溃文件
    crash_files = [f for f in crash_files if f != "README.txt" and not f.endswith(".txt")]
    print("崩溃文件列表:", crash_files)  # 调试信息

    if not crash_files:
        print("未发现崩溃文件，跳过分类和去重。")
        return
    
    #将crash样本进行精简去重
    cmin_crashes(Currentcontainer,newbinary_cmd,CurrentTaskPath)

    #获取被去重后的crash样本
    MasterMiniCrashPath = Path(os.path.abspath(CurrentTaskPath)).joinpath("minimized_crashes")

    # 检查 crashes 目录是否存在
    if not MasterMiniCrashPath.exists() or not MasterMiniCrashPath.is_dir():
        print(f"崩溃目录 {MasterMiniCrashPath} 不存在。")
        return

    # 获取崩溃目录中的所有文件
    crash_files = os.listdir(MasterMiniCrashPath)

    # 过滤掉 README 文件和其他非崩溃文件
    crash_files = [f for f in crash_files if f != "README.txt" and not f.endswith(".txt")]
    print("崩溃文件列表:", crash_files)  # 调试信息

    # 分类和去重崩溃文件
    classification_summary = defaultdict(int)
    bugs_found = []
    output_analysis_dir = Path(os.path.abspath(CurrentTaskPath)).joinpath("output_analysis")
    os.makedirs(output_analysis_dir, exist_ok=True)

    for crash_file in crash_files:
        DockerCrashFilepath = os.path.join("/tmp/minimized_crashes", crash_file)
        asan_output = DumpAsanIndo(Currentcontainer,newbinary_cmd,DockerCrashFilepath)
        sanitized_filename = sanitize_filename(f"asan_output_{os.path.basename(crash_file)}.txt")
        asan_output_file = os.path.join(output_analysis_dir, sanitized_filename)
        write_asan_output_to_file(asan_output,asan_output_file)
        print("开始分类崩溃文件....................")
        category = classify_crashAsan(asan_output)
        classification_summary[category] += 1
        vulnerability_info = get_vulnerability_info(category)
        risk_code_display_filedata = extract_and_extract_code(asan_output, str(CurrentTaskPath))
        print("记录漏洞信息...........")
        MasterCrashPath = convert_path(DockerCrashFilepath, bind_mount, to_docker=False)

        # 记录漏洞信息
        bug = {
            "bug_id": f"{category}_{classification_summary[category]:03}",
            "bug_type": category,
            "crash_file_path": MasterCrashPath,
            "asan_report_file":asan_output,
            "risk_code_display_file": risk_code_display_filedata,
            "total_discovery_count": 1,
            "first_discovery_time": time.ctime(os.path.getctime(MasterCrashPath)),
            "bug_description": vulnerability_info['bug_description'],
            "risk_level": vulnerability_info['risk_level'],
            "fix_recommendation": vulnerability_info['fix_recommendation']
        }
        bugs_found.append(bug)

    FuzzStatusDataPath = Path(os.path.abspath(CurrentTaskPath)).joinpath("FuzzStatus.json")
    fuzzer_statscvg = read_coverage_reached_from_json(FuzzStatusDataPath)
    # 生成报告
    report = {
        "code_path": str(CurrentTaskPath),
        "code_coverage": fuzzer_statscvg,
        "total_bugs_found": len(bugs_found),
        "fuzzing_task_count": 1,
        "bugs_found": bugs_found,
    }
    
    # 将报告写入JSON文件
    report_path = Path(CurrentTaskPath).joinpath("report.json")
    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=4)
        print(f"成功生成报告文件:{report_path}")
    except Exception as e:
        print(f"写入报告文件失败：{str(e)}")


def DumpAsanIndo(Currentcontainer,newbinary_cmd,CrashFilepath):
    print("开始获取Asan分析报告！")
    #执行afl fuzz命令
    aflfuzztime = 0

    # 替换 '@@' 为 crash_filepath,用于获取Asan报告
    replaced_cmd = newbinary_cmd.replace("@@", CrashFilepath)

    while aflfuzztime <= 9 :
        fuzzresult = ExecuteCmdInDocker(Currentcontainer,f"{replaced_cmd}")
        # print(fuzzresult)
        if  "AddressSanitizer" in fuzzresult["output"] :
            print("成功获得了该crash样本的Asan报告！")
            return fuzzresult["output"]
        else :
            print("输出的Asan报告不合法，重新尝试！")
            print(fuzzresult["output"])
            aflfuzztime = aflfuzztime + 1
            time.sleep(1)
        if aflfuzztime == 9 :
            print("重复获取Asan报告9次失败，返回指定信息！")
            return "达到最大重试次数，ASAN 输出仍为空。需要手动分析!"

#根据Asan信息进行分类
def classify_crashAsan(asan_output):
    # 根据 ASAN 输出分类
    if "heap-buffer-overflow" in asan_output:
        return "heap-buffer-overflow"
    elif "stack-buffer-overflow" in asan_output:
        return "stack-buffer-overflow"
    elif "use-after-free" in asan_output:
        return "use-after-free"
    elif "SEGV" in asan_output or "invalid memory access" in asan_output or "Segmentation fault" in asan_output:
        return "segmentation_fault"
    elif "out-of-memory" in asan_output:
        return "out-of-memory"
    elif "double-free" in asan_output:
        return "double-free"
    elif "memory-leaks" in asan_output:
        return "memory-leak"
    elif "integer-overflow" in asan_output:
        return "integer-overflow"
    elif "format-string" in asan_output:
        return "format-string-bug"
    elif "null dereference" in asan_output:
        return "null-dereference"
    elif "out-of-bounds" in asan_output:
        return "out-of-bounds"
    elif "type-confusion" in asan_output:
        return "type-confusion"
    elif "stack-overflow" in asan_output:
        return "stack-overflow"
    elif "heap-use-after-free" in asan_output:
        return "heap-use-after-free"
    elif "attempting free on address" in asan_output:
        return "free-illegal-address"
    else:
        return "other"

def get_vulnerability_info(category):
    """
    根据漏洞分类返回风险等级、描述和修复建议
    :param category: 漏洞类型
    :return: 包含风险等级、描述和修复建议的字典
    """
    if category in ["heap-buffer-overflow", "stack-buffer-overflow"]:
        risk_level = "高"
        bug_description = "向预期输入缓冲区的边界之外读入或写入数据，可能导致内存损坏或程序崩溃。"
        fix_recommendation = "确保对缓冲区的访问操作不会超过其边界，建议使用安全的库函数如 `strncpy`, `memcpy_s` 或者增加边界检查。"
    elif category in ["use-after-free", "UAF"]:
        risk_level = "中"
        bug_description = "程序尝试使用已经释放后的堆块，可能导致未定义行为或内存损坏。"
        fix_recommendation = "避免在释放内存后继续访问，确保释放后指针被置为 `NULL`，并在重新分配内存时正确更新指针。"
    elif category in ["segmentation_fault", "SEGV on unknown address", "invalid memory access"]:
        risk_level = "中"
        bug_description = "程序访问了无效或未分配的内存地址，导致段错误（Segmentation Fault）。"
        fix_recommendation = "检查指针是否为 `NULL` 或是否指向有效的内存地址，确保所有指针在使用前都被正确初始化。"
    elif category in ["out-of-memory", "failed to allocate"]:
        risk_level = "中"
        bug_description = "程序无法分配足够的内存，导致崩溃或无法继续执行。"
        fix_recommendation = "优化内存使用，避免大规模内存分配；同时检查系统内存资源，并处理分配失败的情况。"
    elif category == "double-free":
        risk_level = "高"
        bug_description = "程序对同一内存块进行了两次释放，导致未定义行为或内存损坏。"
        fix_recommendation = "确保每个内存块只被释放一次，使用智能指针或增加标志位来避免重复释放。"
    elif category in ["memory-leak", "memory-leaks", "leaked memory"]:
        risk_level = "中"
        bug_description = "程序在使用后没有释放动态分配的内存，导致内存泄漏，可能最终耗尽系统内存。"
        fix_recommendation = "使用内存泄漏检测工具如 `valgrind` 或 `ASAN` 来检查并确保所有动态分配的内存都能被正确释放。"
    elif category in ["integer-overflow", "signed-integer-overflow"]:
        risk_level = "中"
        bug_description = "整数操作超出其表示范围，可能导致未定义行为或逻辑错误。"
        fix_recommendation = "检查所有整数运算是否超出范围，使用库函数进行边界检查并避免未定义行为。"
    elif category in ["format-string-bug", "format overflow"]:
        risk_level = "高"
        bug_description = "格式化字符串漏洞可能导致任意代码执行或内存损坏。"
        fix_recommendation = "避免使用不受控的格式字符串，确保输入的格式化字符串安全且经过校验，推荐使用 `snprintf` 等安全函数。"
    elif category in ["null-dereference", "null-pointer-access"]:
        risk_level = "中"
        bug_description = "程序试图解引用空指针，导致崩溃或未定义行为。"
        fix_recommendation = "在使用指针之前检查其是否为 `NULL`，确保在解引用之前指针指向有效内存。"
    elif category in ["out-of-bounds", "oob-read", "oob-write"]:
        risk_level = "高"
        bug_description = "程序尝试访问数组或缓冲区边界之外的内存，可能导致内存损坏或信息泄露。"
        fix_recommendation = "确保对数组和缓冲区的访问在有效范围内，使用边界检查或安全的数组访问函数。"
    elif category in ["type-confusion", "bad-cast"]:
        risk_level = "中"
        bug_description = "类型混淆可能导致未定义行为或内存损坏，通常发生在不安全的类型转换中。"
        fix_recommendation = "在进行类型转换时，确保目标类型与原类型兼容，避免强制转换，使用 `dynamic_cast` 等安全的类型转换方法。"
    elif category == "stack-overflow":
        risk_level = "高"
        bug_description = "程序使用的栈空间超过了系统限制，导致栈溢出，可能引发崩溃或安全漏洞。"
        fix_recommendation = "优化递归函数或减少栈空间的使用，避免过深的函数调用或大规模局部变量分配。"
    elif category == "heap-use-after-free":
        risk_level = "中"
        bug_description = "程序在释放堆内存后继续使用该内存，可能导致未定义行为或内存损坏。"
        fix_recommendation = "避免在释放内存后继续访问，确保释放后指针被置为 `NULL`，并在重新分配内存时正确更新指针。"
    elif category == "free-illegal-address":
        risk_level = "高"
        bug_description = "程序尝试释放一个无效的内存地址，可能导致未定义行为或崩溃。"
        fix_recommendation = "确保只释放动态分配的内存地址，并在释放前检查指针的有效性。"
    else:
        risk_level = "中"
        bug_description = "未知漏洞类型，需要进一步分析。"
        fix_recommendation = "请查看 ASAN 输出或进行进一步分析。"

    # 返回风险等级、描述和修复建议
    return {
        "risk_level": risk_level,
        "bug_description": bug_description,
        "fix_recommendation": fix_recommendation
    }

def extract_and_extract_code(log_text, new_directory, context_lines=2):
    if "AddressSanitizer" not in log_text:
        return "该奔溃样本的源码报错路径需要手动定位！"

    """
    从日志文本中提取 .c 文件路径及其行号，替换路径中的 /tmp 目录，并提取指定行号及其附近的源码
    :param log_text: 日志文本
    :param new_directory: 新的目录（用于替换 /tmp）
    :param context_lines: 上下文的行数（默认提取前后各 2 行）
    :return: 提取的源码列表，每个元素为 (文件路径, 行号, 源码)
    """
    def extract_c_file_paths_with_line_numbers(log_text):
        """
        从日志文本中提取所有 .c 或 .h 文件路径及其行号
        """
        pattern = r"(/(?:[^\s/]+/)*[^\s/]+\.(?:c|h)):(\d+)"
        matches = re.findall(pattern, log_text)
        return matches

    def replace_tmp_directory(path, new_directory):
        """
        将路径中的 /tmp 目录替换为新的目录
        """
        if path.startswith("/tmp"):
            return path.replace("/tmp", new_directory, 1)
        return path

    def extract_source_code(file_path, line_number, context_lines=2):
        """
        从指定文件中提取指定行号及其附近的源码
        """
        try:
            with open(file_path, 'r') as file:
                lines = file.readlines()
                total_lines = len(lines)

                if 1 <= line_number <= total_lines:
                    start_line = max(1, line_number - context_lines)
                    end_line = min(total_lines, line_number + context_lines)

                    extracted_lines = []
                    for i in range(start_line - 1, end_line):
                        extracted_lines.append(f"{i + 1}: {lines[i].strip()}")

                    return "\n".join(extracted_lines)
                else:
                    return f"错误：行号 {line_number} 超出文件范围（文件总行数：{total_lines}）"
        except FileNotFoundError:
            return f"错误：文件 {file_path} 不存在"
        except Exception as e:
            return f"错误：读取文件时发生异常 - {str(e)}"

    # 提取 .c 文件路径及其行号
    c_file_paths_with_line_numbers = extract_c_file_paths_with_line_numbers(log_text)
    
    if not c_file_paths_with_line_numbers:
        # 如果为空，返回提示信息
        return "未找到源码定位信息，请手动进行源码定位。"

    # 替换路径并提取源码
    results = []
    for file_path, line_number in c_file_paths_with_line_numbers:
        new_path = replace_tmp_directory(file_path, new_directory)
        source_code = extract_source_code(new_path, int(line_number), context_lines)
        results.append((new_path, line_number, source_code))

    resultsCodeInfo = ""

    resultsCodeInfo += f"文件路径: {results[0][0]}"
    resultsCodeInfo += f"\n{results[0][2]}\n"
    return resultsCodeInfo

def read_coverage_reached_from_json(file_path):
    """读取指定 JSON 文件中的 'Coverage reached' 字段"""
    try:
        # 读取 JSON 文件
        with open(file_path, 'r') as file:
            data = json.load(file)
        
        # 提取 'Coverage reached' 字段
        coverage_reached = data.get("Coverage reached")
        
        return coverage_reached
    
    except FileNotFoundError:
        print(f"文件 {file_path} 未找到。")
        return None
    except json.JSONDecodeError:
        print("文件不是有效的 JSON 格式。")
        return None
    

def analyze_fuzz_results(FuzzTaskInfo,CurrentTaskPath):
    """
    汇总分析fuzz结果的功能，包括以下步骤：
    1. 检测版本信息，判断是否需要重新编译还是直接使用现有编译好的文件。
    2. 创建存放项目文件的文件夹。
    3. 根据检测结果，解压目标数据或复制已编译好的文件。
    4. 创建 Docker 客户端并启动容器。
    5. 查找目标可执行文件并转换路径。
    6. 分类整理 Crash 样本文件。
    """

    FuzzTaskName = FuzzTaskInfo["program_name"]
    ProjectID = "analyze_fuzz_results"
    binary_cmd = FuzzTaskInfo["bin_cmd"]

    # 创建 Docker 客户端
    Mainclient = docker.from_env()
    bind_mount = {f'{CurrentTaskPath}': '/tmp'}
    dockername = f"{FuzzTaskName}_{ProjectID}"  # 避免测试同一个项目时发生冲突
    Currentcontainer = CreateAFLDocker(Mainclient, dockername, bind_mount, use_existing=True)

    # 查找目标可执行文件并转换路径
    targetbinname = binary_cmd.split()[0]
    hosttargetbinpath = find_executable_in_directory(CurrentTaskPath, targetbinname)
    dokcertargetbinpath = convert_path(hosttargetbinpath, bind_mount,to_docker=True)
    newbinary_cmd = f"{dokcertargetbinpath} {binary_cmd[len(targetbinname):]}"

    # 开始最后的整理Crash样本文件
    classify_crashes(Currentcontainer, newbinary_cmd, CurrentTaskPath,bind_mount)

    #结束docker容器的运行
    if Currentcontainer:
        check_and_stop_container(Mainclient,Currentcontainer.id)  # 使用容器的 ID


