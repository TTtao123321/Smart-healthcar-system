ARG REGISTRY_PREFIX=docker.io/library
FROM ${REGISTRY_PREFIX}/python:3.12-slim

WORKDIR /app

# 可选:配置 Debian + pip 镜像加速(默认空,使用官方源)
# 在 docker compose / build 时传入:
#   --build-arg DEBIAN_MIRROR_URL=https://mirrors.aliyun.com
#   --build-arg PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
ARG DEBIAN_MIRROR_URL=""
ARG PIP_INDEX_URL=""

RUN if [ -n "$DEBIAN_MIRROR_URL" ]; then \
        sed -i "s|http://deb.debian.org|${DEBIAN_MIRROR_URL}|g; s|http://security.debian.org|${DEBIAN_MIRROR_URL}|g" /etc/apt/sources.list.d/debian.sources; \
    fi \
    && if [ -n "$PIP_INDEX_URL" ]; then \
        pip config set global.index-url "$PIP_INDEX_URL"; \
        host=$(echo "$PIP_INDEX_URL" | awk -F[/:] '{print $4}'); \
        pip config set install.trusted-host "$host"; \
    fi

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 先复制项目配置和源码,再安装依赖
COPY pyproject.toml .
COPY app/ app/

RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
