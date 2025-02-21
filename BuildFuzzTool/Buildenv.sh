#!/bin/bash

# 定义固定目录和输入目录
FIXED_DIR="/home/win10/liyong/AutoFuzz/BuildFuzzTool/Work"  # 请替换为实际的固定目录路径
INPUT_DIR="$FIXED_DIR/input"

# 创建固定目录和输入目录
mkdir -p "$FIXED_DIR"
mkdir -p "$INPUT_DIR"

# 检查是否传入了参数
if [ -z "$1" ]; then
    echo "请提供一个 URL 或 Git 链接."
    exit 1
fi

URL="$1"

# 判断文件类型
if [[ $URL == *.git ]]; then
    # 处理 Git 链接
    REPO_NAME=$(basename "$URL" .git)
    git clone "$URL" "$FIXED_DIR/$REPO_NAME"
    # 打包备份
    tar -czvf "$FIXED_DIR/${REPO_NAME}_backup.tar.gz" -C "$FIXED_DIR" "$REPO_NAME"
elif [[ $URL == *.zip || $URL == *.tar.gz || $URL == *.tar ]]; then
    # 处理压缩包链接
    FILENAME=$(basename "$URL")
    wget -O "$FIXED_DIR/$FILENAME" "$URL"
    # 根据文件类型解压
    if [[ $FILENAME == *.zip ]]; then
        unzip "$FIXED_DIR/$FILENAME" -d "$FIXED_DIR"
    else
        tar -xzvf "$FIXED_DIR/$FILENAME" -C "$FIXED_DIR"
    fi
else
    echo "不支持的链接类型."
    exit 1
fi

# 下载其他链接到 input 文件夹
shift  # 移除第一个参数
for SAMPLE_URL in "$@"; do
    wget -P "$INPUT_DIR" "$SAMPLE_URL"
done

echo "下载完成."
