#!/bin/bash

# 定义目录路径
input_dir="/home/win10/liyong/AutoFuzz/BuildFuzzTool/Work/"
output_dir="/home/win10/liyong/AutoFuzz/BuildFuzzTool/output"
build_script="/home/win10/liyong/AutoFuzz/BuildFuzzTool/Work/Build.sh"
archive_name="output.tar.gz"

# 创建输出目录
mkdir -p "$output_dir"

# 解压第一级的压缩包
for file in "$input_dir"/*; do
    if [[ "$file" =~ \.zip$|\.tar\.gz$|\.tar$|\.gz$ ]]; then
        echo "解压文件: $file"
        tar -xzf "$file" -C "$output_dir"
    fi
done

# 复制整个input文件夹到输出目录
echo "复制input文件夹"
cp -r "$input_dir/input" "$output_dir"

# 复制Build.sh到输出目录
echo "复制Build.sh"
cp "$build_script" "$output_dir"

# 打包压缩输出目录
echo "打包压缩输出目录"
tar -czf "$archive_name" -C "$(dirname "$output_dir")" "$(basename "$output_dir")"

echo "操作完成，压缩包为: $archive_name"
rm -rf "$output_dir"
echo "删除输出目录"