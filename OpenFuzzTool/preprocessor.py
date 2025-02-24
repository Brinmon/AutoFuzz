import os
import magic
import subprocess
from zipfile import ZipFile
import py7zr
import rarfile
import shutil
from tqdm import tqdm
import logging
from pathlib import Path

class FilePreprocessor:
    # 配置日志记录
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    def clean_workspace(self, workspace: str):
        """安全清空工作目录"""
        if os.path.exists(workspace):
            shutil.rmtree(workspace)
        os.makedirs(workspace, exist_ok=True)

    def copy_files_to_workspace(self, source_dir, destination_dir):
        # 处理Build.sh文件
        if destination_dir is not None:
            build_sh_found = False
            for root, dirs, files in os.walk(destination_dir):
                if 'Build.sh' in files:
                    build_dir = root
                    build_sh_found = True
                    break
            
            if build_sh_found:
                try:
                    print(f"Copying Build.sh directory from {build_dir} to {destination_dir}...")
                    # 使用dirs_exist_ok=True避免覆盖错误（Python 3.8+）
                    shutil.copytree(build_dir, destination_dir, dirs_exist_ok=True)
                    print("Build directory copied successfully.")
                except Exception as e:
                    print(f"Error copying Build directory: {e}")
            else:
                print("No Build.sh file found in the extracted package.")

    def get_file_extension(self, file_path):
        """获取文件扩展名"""
        return Path(file_path).suffix.lower()

    def decompressionALL(self, zip_path, FuzzWorkPath):
        """智能识别压缩包类型并解压
        :param zip_path: 压缩文件的绝对路径
        :param FuzzWorkPath: 解压目标路径的绝对路径
        :return: 解压后的目录路径
        """
        logging.info(f"开始处理文件: {zip_path}")
        
        # 使用 magic 模块检测文件类型
        m = magic.Magic(uncompress=True)
        try:
            file_type = m.from_file(zip_path)
            ext = self.get_file_extension(zip_path)
            logging.info(f"检测到文件类型: {file_type}，扩展名: {ext}")

            # 根据文件类型和扩展名调用相应的解压函数
            if "Zip archive data" in file_type or ext == '.zip':
                return self.unzip_zipfile(zip_path, FuzzWorkPath)
            elif "gzip compressed data" in file_type or "tar archive" in file_type or ext in ['.tar', '.gz', '.tgz']:
                return self.unzip_targzfile(zip_path, FuzzWorkPath)
            elif "7-zip archive data" in file_type or ext == '.7z':
                return self.unzip_7z_file(zip_path, FuzzWorkPath)
            elif "RAR archive data" in file_type or ext == '.rar':
                return self.unzip_rar_file(zip_path, FuzzWorkPath)
            elif "XZ compressed data" in file_type or ext == '.xz':
                return self.unzip_xz_file(zip_path, FuzzWorkPath)
            elif "bzip2 compressed data" in file_type or ext == '.bz2':
                return self.unzip_bz2_file(zip_path, FuzzWorkPath)
            elif "ISO 9660" in file_type or ext == '.iso':
                return self.unzip_iso_file(zip_path, FuzzWorkPath)
            elif "RPM" in file_type or ext == '.rpm':
                return self.unzip_RPMfile(zip_path, FuzzWorkPath)
            elif "Debian binary package" in file_type or ext == '.deb':
                return self.unzip_deb_file(zip_path, FuzzWorkPath)
            elif "Microsoft Cabinet archive" in file_type or ext == '.cab':
                return self.unzip_cab_file(zip_path, FuzzWorkPath)
            else:
                logging.error(f"不支持的文件类型: {file_type}")
                return None
        except Exception as e:
            logging.error(f"文件检测或解压失败 {zip_path}: {str(e)}")
            return None

    def show_progress(self, filename, total_size):
        """显示解压进度"""
        return tqdm(
            desc=f"解压 {filename}",
            total=total_size,
            unit='B',
            unit_scale=True
        )

    def unzip_zipfile(self,file_path, output_dir):
        """解压 ZIP 文件到指定目录"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            with ZipFile(file_path, "r") as zp:
                total_size = sum(info.file_size for info in zp.filelist)
                with self.show_progress(Path(file_path).name, total_size) as pbar:
                    for member in zp.filelist:
                        zp.extract(member, output_dir)
                        pbar.update(member.file_size)
            logging.info(f"成功解压 {file_path} 到 {output_dir}")
            return output_dir
        except Exception as e:
            logging.error(f"ZIP解压失败 {file_path}: {str(e)}")
            return None

    def unzip_targzfile(self,file_path, output_dir):
        """解压 tar.gz 文件到指定目录"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            cmd = f"tar -xzf {file_path} -C {output_dir}"
            subprocess.run(cmd, shell=True, check=True)
            logging.info(f"成功解压 {file_path} 到 {output_dir}")
            return output_dir
        except Exception as e:
            logging.error(f"TAR.GZ解压失败 {file_path}: {str(e)}")
            return None

    def unzip_7z_file(self, file_path, output_dir):
        """解压 7z 文件到指定目录"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            with py7zr.SevenZipFile(file_path, 'r') as sz:
                sz.extractall(output_dir)
            logging.info(f"成功解压 {file_path} 到 {output_dir}")
            return output_dir
        except Exception as e:
            logging.error(f"7Z解压失败 {file_path}: {str(e)}")
            return None

    def unzip_rar_file(self, file_path, output_dir):
        """解压 RAR 文件到指定目录"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            with rarfile.RarFile(file_path) as rf:
                rf.extractall(output_dir)
            logging.info(f"成功解压 {file_path} 到 {output_dir}")
            return output_dir
        except Exception as e:
            logging.error(f"RAR解压失败 {file_path}: {str(e)}")
            return None

    def unzip_xz_file(self, file_path, output_dir):
        """解压 XZ 文件到指定目录"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            cmd = f"xz -d -k {file_path} -c > {output_dir}/{Path(file_path).stem}"
            subprocess.run(cmd, shell=True, check=True)
            logging.info(f"成功解压 {file_path} 到 {output_dir}")
            return output_dir
        except Exception as e:
            logging.error(f"XZ解压失败 {file_path}: {str(e)}")
            return None

    def unzip_bz2_file(self, file_path, output_dir):
        """解压 BZ2 文件到指定目录"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            cmd = f"bzip2 -d -k {file_path} -c > {output_dir}/{Path(file_path).stem}"
            subprocess.run(cmd, shell=True, check=True)
            logging.info(f"成功解压 {file_path} 到 {output_dir}")
            return output_dir
        except Exception as e:
            logging.error(f"BZ2解压失败 {file_path}: {str(e)}")
            return None

    def unzip_iso_file(self, file_path, output_dir):
        """解压 ISO 文件到指定目录"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            cmd = f"7z x {file_path} -o{output_dir}"
            subprocess.run(cmd, shell=True, check=True)
            logging.info(f"成功解压 {file_path} 到 {output_dir}")
            return output_dir
        except Exception as e:
            logging.error(f"ISO解压失败 {file_path}: {str(e)}")
            return None

    def unzip_RPMfile(self, file_path, output_dir):
        """解压 RPM 文件到指定目录"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            cmd = f"rpm2cpio {file_path} | cpio -idmv -D {output_dir}"
            subprocess.run(cmd, shell=True, check=True)
            logging.info(f"成功解压 {file_path} 到 {output_dir}")
            return output_dir
        except Exception as e:
            logging.error(f"RPM解压失败 {file_path}: {str(e)}")
            return None

    def unzip_deb_file(self, file_path, output_dir):
        """解压 DEB 文件到指定目录"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            cmd = f"dpkg-deb -x {file_path} {output_dir}"
            subprocess.run(cmd, shell=True, check=True)
            logging.info(f"成功解压 {file_path} 到 {output_dir}")
            return output_dir
        except Exception as e:
            logging.error(f"DEB解压失败 {file_path}: {str(e)}")
            return None

    def unzip_cab_file(self, file_path, output_dir):
        """解压 CAB 文件到指定目录"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            cmd = f"cabextract -d {output_dir} {file_path}"
            subprocess.run(cmd, shell=True, check=True)
            logging.info(f"成功解压 {file_path} 到 {output_dir}")
            return output_dir
        except Exception as e:
            logging.error(f"CAB解压失败 {file_path}: {str(e)}")
            return None

    def recursive_decompress(self,file_path, output_dir):
        """递归解压文件
        :param file_path: 压缩文件的绝对路径
        :param output_dir: 解压目标路径的绝对路径
        :return: 最终解压后的目录路径列表
        """
        result_dirs = []
        initial_dir = self.decompressionALL(file_path, output_dir)
        
        if initial_dir:
            result_dirs.append(initial_dir)
            # 遍历解压后的目录，查找嵌套的压缩文件
            for root, _, files in os.walk(initial_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    if any(file.lower().endswith(ext) for ext in 
                        ['.zip', '.tar.gz', '.tgz', '.7z', '.rar', '.xz', '.bz2', 
                            '.iso', '.rpm', '.deb', '.cab']):
                        nested_output_dir = os.path.join(root, 'nested_' + Path(file).stem)
                        nested_result = self.decompressionALL(file_path, nested_output_dir)
                        if nested_result:
                            result_dirs.append(nested_result)
        
        return result_dirs