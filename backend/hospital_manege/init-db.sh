#!/bin/bash
# ============================================================
# 智慧医院管理系统 - 数据库一键初始化脚本
# 支持 Docker Compose 自动初始化 & 手动执行
# ============================================================

set -e

MYSQL_HOST="${MYSQL_HOST:-127.0.0.1}"
MYSQL_PORT="${MYSQL_PORT:-4307}"
MYSQL_USER="${MYSQL_USER:-root}"
MYSQL_PASS="${MYSQL_PASS:-123456}"
SQL_FILE="init-sql/init.sql"

usage() {
    echo "用法: $0 [选项]"
    echo ""
    echo "一键初始化 fm_hospital 数据库"
    echo ""
    echo "选项:"
    echo "  -h <host>     MySQL 主机地址 (默认: $MYSQL_HOST)"
    echo "  -P <port>     MySQL 端口 (默认: $MYSQL_PORT)"
    echo "  -u <user>     MySQL 用户名 (默认: $MYSQL_USER)"
    echo "  -p <pass>     MySQL 密码 (默认: $MYSQL_PASS)"
    echo "  --docker      直接通过 Docker Compose 初始化 (docker compose up -d)"
    echo "  --help        显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0                        使用默认配置初始化"
    echo "  $0 -h 192.168.1.100 -P 3306 -u root -p mypass"
    echo "  $0 --docker              启动 Docker 服务并自动初始化"
    exit 0
}

# 解析参数
while [[ $# -gt 0 ]]; do
    case "$1" in
        -h) MYSQL_HOST="$2"; shift 2 ;;
        -P) MYSQL_PORT="$2"; shift 2 ;;
        -u) MYSQL_USER="$2"; shift 2 ;;
        -p) MYSQL_PASS="$2"; shift 2 ;;
        --docker) MODE="docker"; shift ;;
        --help) usage ;;
        *) echo "未知参数: $1"; usage ;;
    esac
done

# 切换到脚本所在目录
cd "$(dirname "$0")"

if [[ "$MODE" == "docker" ]]; then
    echo "============================================"
    echo "  通过 Docker Compose 启动所有服务"
    echo "============================================"
    echo ""
    echo "创建数据挂载目录..."
    sudo mkdir -p /home/hospital_manage/{mysql,redis,rabbitmq,minio}
    echo ""
    echo "启动 Docker 容器..."
    docker compose up -d
    echo ""
    echo "============================================"
    echo "  服务启动完成！"
    echo "  MySQL:   127.0.0.1:4307"
    echo "  Redis:   127.0.0.1:7379"
    echo "  RabbitMQ: 127.0.0.1:5672 (管理台: 15672)"
    echo "  MinIO:   127.0.0.1:9000 (控制台: 9001)"
    echo ""
    echo "  MySQL 数据库初始化由 Docker 自动完成"
    echo "============================================"
else
    if [[ ! -f "$SQL_FILE" ]]; then
        echo "错误: 未找到 $SQL_FILE"
        echo "请确保在项目根目录 (backend/hospital_manege) 下运行此脚本"
        exit 1
    fi

    echo "============================================"
    echo "  初始化 fm_hospital 数据库"
    echo "  主机: $MYSQL_HOST:$MYSQL_PORT"
    echo "  用户: $MYSQL_USER"
    echo "============================================"
    echo ""

    # 确认
    read -r -p "即将重建数据库 fm_hospital，所有现有数据将丢失，是否继续？[y/N] " confirm
    if [[ ! "$confirm" =~ ^[yY] ]]; then
        echo "已取消。"
        exit 0
    fi

    echo "开始导入数据..."
    if [[ -n "$MYSQL_PASS" ]]; then
        mysql -h "$MYSQL_HOST" -P "$MYSQL_PORT" -u "$MYSQL_USER" -p"$MYSQL_PASS" < "$SQL_FILE"
    else
        mysql -h "$MYSQL_HOST" -P "$MYSQL_PORT" -u "$MYSQL_USER" < "$SQL_FILE"
    fi

    echo ""
    echo "============================================"
    echo "  数据库初始化完成！"
    echo "  共导入 21 张表"
    echo "============================================"
fi
