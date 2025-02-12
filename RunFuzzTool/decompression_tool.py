import os
import subprocess
import magic
from zipfile import ZipFile

def decompressionALL(zip_path, FuzzWorkPath):
    """
    智能识别压缩包类型并解压
    :param zip_path: 压缩文件的绝对路径
    :param FuzzWorkPath: 解压目标路径的绝对路径
    :return: 解压后的目录路径
    """
    print("-----------------------------------------------------------------")
    print(f"Detecting and decompressing {zip_path} to {FuzzWorkPath}...")

    # 使用 magic 模块检测文件类型
    m = magic.Magic(uncompress=True)
    try:
        file_type = m.from_file(zip_path)
        print(f"Detected file type: {file_type}")

        # 根据文件类型调用相应的解压函数
        if "Zip archive data" in file_type:
            return unzip_zipfile(zip_path, FuzzWorkPath)
        elif "gzip compressed data" in file_type or "tar archive" in file_type:
            return unzip_targzfile(zip_path, FuzzWorkPath)
        elif "7-zip archive data" in file_type:
            return unzip_7z_file(zip_path, FuzzWorkPath)
        elif "RPM" in file_type:
            return unzip_RPMfile(zip_path, FuzzWorkPath)
        elif "Debian binary package" in file_type:
            return unzip_deb_file(zip_path, FuzzWorkPath)
        elif "Microsoft Cabinet archive" in file_type:
            return unzip_cab_file(zip_path, FuzzWorkPath)
        else:
            print(f"Unsupported file type: {file_type}")
            return None
    except Exception as e:
        print(f"Failed to detect or decompress {zip_path}: {e}")
        return None

def unzip_zipfile(file_path, output_dir):
    """
    解压 ZIP 文件到指定目录
    :param file_path: 压缩文件的绝对路径
    :param output_dir: 解压目标路径的绝对路径
    :return: 解压后的目录路径
    """
    print("-----------------------------------------------------------------")
    print(f"Unzipping {file_path} to {output_dir}...")
    try:
        m = magic.Magic(uncompress=True)
        file_type = m.from_file(file_path)
        if "Zip archive data" in file_type:
            os.makedirs(output_dir, exist_ok=True)
            with ZipFile(file_path, "r") as zp:
                zp.extractall(output_dir)
            print(f"Successfully unzipped {file_path} to {output_dir}.")
            return output_dir
        else:
            print(f"{file_path} is not a valid ZIP file.")
            return None
    except Exception as e:
        print(f"Failed to unzip {file_path}: {e}")
        return None

def unzip_targzfile(file_path, output_dir):
    """
    解压 tar.gz 文件到指定目录
    :param file_path: 压缩文件的绝对路径
    :param output_dir: 解压目标路径的绝对路径
    :return: 解压后的目录路径
    """
    print("-----------------------------------------------------------------")
    print(f"Unzipping {file_path} to {output_dir}...")
    try:
        m = magic.Magic(uncompress=True)
        file_type = m.from_file(file_path)
        if "gzip compressed data" in file_type or "tar archive" in file_type:
            os.makedirs(output_dir, exist_ok=True)
            cmd = f"tar -xzf {file_path} -C {output_dir}"
            subprocess.run(cmd, shell=True, check=True)
            print(f"Successfully unzipped {file_path} to {output_dir}.")
            return output_dir
        else:
            print(f"{file_path} is not a valid tar.gz file.")
            return None
    except Exception as e:
        print(f"Failed to unzip {file_path}: {e}")
        return None

def unzip_7z_file(file_path, output_dir):
    """
    解压 7z 文件到指定目录
    :param file_path: 压缩文件的绝对路径
    :param output_dir: 解压目标路径的绝对路径
    :return: 解压后的目录路径
    """
    print("-----------------------------------------------------------------")
    print(f"Unzipping {file_path} to {output_dir}...")
    try:
        m = magic.Magic(uncompress=True)
        file_type = m.from_file(file_path)
        if "7-zip archive data" in file_type:
            os.makedirs(output_dir, exist_ok=True)
            cmd = f"7z x {file_path} -o{output_dir}"
            subprocess.run(cmd, shell=True, check=True)
            print(f"Successfully unzipped {file_path} to {output_dir}.")
            return output_dir
        else:
            print(f"{file_path} is not a valid 7z file.")
            return None
    except Exception as e:
        print(f"Failed to unzip {file_path}: {e}")
        return None

def unzip_RPMfile(file_path, output_dir):
    """
    解压 RPM 文件到指定目录
    :param file_path: 压缩文件的绝对路径
    :param output_dir: 解压目标路径的绝对路径
    :return: 解压后的目录路径
    """
    print("-----------------------------------------------------------------")
    print(f"Unzipping {file_path} to {output_dir}...")
    try:
        m = magic.Magic(uncompress=True)
        file_type = m.from_file(file_path)
        if "RPM" in file_type:
            os.makedirs(output_dir, exist_ok=True)
            cmd = f"rpm2cpio {file_path} | cpio -idmv -D {output_dir}"
            subprocess.run(cmd, shell=True, check=True)
            print(f"Successfully unzipped {file_path} to {output_dir}.")
            return output_dir
        else:
            print(f"{file_path} is not a valid RPM file.")
            return None
    except Exception as e:
        print(f"Failed to unzip {file_path}: {e}")
        return None

def unzip_deb_file(file_path, output_dir):
    """
    解压 DEB 文件到指定目录
    :param file_path: 压缩文件的绝对路径
    :param output_dir: 解压目标路径的绝对路径
    :return: 解压后的目录路径
    """
    print("-----------------------------------------------------------------")
    print(f"Unzipping {file_path} to {output_dir}...")
    try:
        m = magic.Magic(uncompress=True)
        file_type = m.from_file(file_path)
        if "Debian binary package" in file_type:
            os.makedirs(output_dir, exist_ok=True)
            cmd = f"dpkg-deb -x {file_path} {output_dir}"
            subprocess.run(cmd, shell=True, check=True)
            print(f"Successfully unzipped {file_path} to {output_dir}.")
            return output_dir
        else:
            print(f"{file_path} is not a valid DEB file.")
            return None
    except Exception as e:
        print(f"Failed to unzip {file_path}: {e}")
        return None

def unzip_cab_file(file_path, output_dir):
    """
    解压 CAB 文件到指定目录
    :param file_path: 压缩文件的绝对路径
    :param output_dir: 解压目标路径的绝对路径
    :return: 解压后的目录路径
    """
    print("-----------------------------------------------------------------")
    print(f"Unzipping {file_path} to {output_dir}...")
    try:
        m = magic.Magic(uncompress=True)
        file_type = m.from_file(file_path)
        if "Microsoft Cabinet archive" in file_type:
            os.makedirs(output_dir, exist_ok=True)
            cmd = f"cabextract {file_path} -d {output_dir}"
            subprocess.run(cmd, shell=True, check=True)
            print(f"Successfully unzipped {file_path} to {output_dir}.")
            return output_dir
        else:
            print(f"{file_path} is not a valid CAB file.")
            return None
    except Exception as e:
        print(f"Failed to unzip {file_path}: {e}")
        return None

