#!/bin/bash
python3 /home/win10/liyong/AutoFuzz/BuildFuzzTool/CrateAFLdocker.py --local_dir $1

# 获取容器名称，默认是 my_afl_container
CONTAINER_NAME="my_afl_container"

# 等待一会，确保容器启动
sleep 5

# 查找 Docker 容器的 ID
CONTAINER_ID=$(docker ps -q -f name="$CONTAINER_NAME")

# 检查容器是否存在
if [ -z "$CONTAINER_ID" ]; then
    echo "未找到容器 $CONTAINER_NAME."
    exit 1
fi

# 进入容器
docker exec -it "$CONTAINER_ID" bash