# 智慧医院管理系统(Smart-healthcar-system)

智慧医院管理系统 + 患者智能助手 Agent。一条命令启动全栈,无需在宿主机安装 JDK / Maven / Node / Python / Redis。

## 子系统

- **HMS 后端**(`hospital_manage_backend/`):Spring Boot 2.5.2 + MyBatis + Sa-Token + MySQL + Redis + RabbitMQ + MinIO
- **HMS 前端**(`hospital_manage_frontend/`):Vue 3 + Vite + Element Plus(管理后台)
- **Agent 后端**(`patient_agent_backend/`):FastAPI + LangGraph + Redis 对话记忆
- **Agent 前端**(`patient_agent_frontend/`):React 19 + Vite + Tailwind 4

## 项目结构

```
Smart-healthcar-system/
├── docker-compose.yml          # 一键启动入口(9 个服务)
├── .env.example                # 顶层环境变量示例
├── hospital_manage_backend/    # HMS Java 后端 + init-sql/(数据库自动建表脚本)
│   ├── Dockerfile
│   ├── hospital_hms_api/
│   ├── common/
│   └── init-sql/               # init.sql / init-rbac.sql / init-agent-tables.sql / init-patient-data.sql
├── hospital_manage_frontend/   # HMS Vue 管理后台
├── patient_agent_backend/      # Patient Agent FastAPI 后端
│   ├── Dockerfile
│   └── .env.example
└── patient_agent_frontend/     # Patient Agent React 前端
```

## 一键启动(推荐)

### 前置条件

- Docker 20+(或 Docker Desktop)
- Docker Compose v2

无需在宿主机安装 JDK / Maven / Node / Python / Redis。

### 步骤

```bash
git clone https://github.com/TTtao123321/Smart-healthcar-system.git
cd Smart-healthcar-system

# 1. 准备环境变量(填入 OPENAI_API_KEY)
cp .env.example .env
vim .env

# 2. 一键启动全部 9 个服务
docker compose up -d --build

# 3. 查看状态
docker compose ps
```

首次启动需 1-2 分钟拉镜像与构建,之后可直接 `docker compose up -d`。

### 数据自动初始化(开箱即用)

- **MySQL**:首次启动会按字典序自动执行 `hospital_manage_backend/init-sql/*.sql`,完成建库 + 21+ 张表 + 初始化数据(RBAC/患者/Agent)
- **MinIO**:`minio-init` 一次性服务自动创建 `hospital` bucket 并设置匿名读权限,完成后退出
- **重置数据**:`docker compose down -v && docker compose up -d`(清空 `./data/` 数据卷会再次触发自动初始化)

## 服务端口表

| 服务 | 容器端口 | 宿主端口 | 访问入口 |
|---|---|---|---|
| MySQL | 3306 | 4307 | `localhost:4307` (root / 123456) |
| Redis | 6379 | 7379 | `localhost:7379` (密码 123456) |
| RabbitMQ | 5672 / 15672 | 5672 / 15672 | 管理台 `http://localhost:15672` (root / 123456) |
| MinIO | 9000 / 9001 | 9000 / 9001 | 控制台 `http://localhost:9001` (root / 12345678abc) |
| hospital_hms_api | 9091 | 9091 | API 文档 `http://localhost:9091/hms/doc-api.html` |
| hospital_manage_frontend | 4000 | 4000 | 管理后台 `http://localhost:4000/hms-vue` |
| patient_agent_backend | 8000 | 8001 | 健康检查 `http://localhost:8001/health` |
| patient_agent_frontend | 5174 | 5174 | 患者助手 `http://localhost:5174` |
| minio-init | - | - | 一次性,完成后 `Exited (0)` 即正常 |

## 默认登录账号

| 系统 | 用户名 | 密码 | 角色 |
|---|---|---|---|
| HMS 管理后台 | zhangsan | zhangsan | 超级管理员 |
| HMS 管理后台 | admin | admin123 | 超级管理员 |
| Agent 前端 | 短信验证码登录 | - | 患者(MVP 阶段) |

## 常见操作

```bash
# 查看某个服务日志
docker compose logs -f hospital_hms_api
docker compose logs -f patient_agent_backend

# 重启某个服务
docker compose restart hospital_hms_api

# 停止所有(保留数据)
docker compose down

# 停止并清空数据卷(慎用)
docker compose down -v

# 仅重新执行 MinIO bucket 初始化
docker compose run --rm minio-init
```

## 本地 IDE 直跑(可选)

`hospital_hms_api/src/main/resources/application.yml` 中所有外部连接均使用 `${ENV:default}` 占位,默认值指向本机宿主端口(4307/7379/5672/9000),与 Docker 一键启动同时兼容,无需改文件即可在 IDE 直接 Run。

```bash
# IDE 直跑前:确保中间件已起来(用 Docker 跑中间件即可)
docker compose up -d mysql redis rabbitmq minio minio-init

# 然后 IDEA 直接 Run HmsApiApplication;前端目录 npm install && npm run dev
```

## 安全提示

- `.env` 已在 `.gitignore` 中,严禁提交到 git
- 默认 MySQL/Redis/RabbitMQ/MinIO 密码仅适用于本地开发,生产部署请改用 secrets

## 不在本仓库范围内

- Kubernetes 生产部署
- HTTPS / 镜像仓库推送
- 微信小程序端(已下线)
