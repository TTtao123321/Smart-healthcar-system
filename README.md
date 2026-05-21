# 智慧医院管理系统

医院后台管理系统，覆盖科室管理、医生排班、患者管理、诊费设置、视频问诊等功能。

- **后端**：Spring Boot 2.5.2 + MyBatis + Sa-Token + MySQL + Redis + RabbitMQ + MinIO
- **前端**：Vue 3 + Vite + Element Plus（管理后台）
- **患者端**：待重新开发（原有微信小程序端已移除）

## 功能模块

```
首页
├── 组织管理
│   ├── 医疗科室管理
│   └── 医疗诊室管理
├── 医护管理
│   ├── 医生管理
│   ├── 患者管理        ← 新增
│   └── 诊费设置
├── 出诊管理
│   ├── 门诊日程表
│   ├── 医生出诊表
│   └── 视频问诊
└── 系统设置
```

### 患者管理

支持按姓名、性别、科室、诊室、就诊医师、就诊状态（待就诊/就诊中/已就诊/复诊中）进行分页查询，可查看患者基本信息及历史就诊记录。

## 项目结构

```
├── backend/
│   └── hospital_manege/        # 后端服务
│       ├── common/              # 公共模块
│       ├── hospital_hms_api/    # 主 API 服务
│       │   └── src/main/java/com/hospital/hms/
│       │       ├── controller/  # 控制器（含 PatientController）
│       │       ├── service/     # 服务层
│       │       ├── dao/         # 数据访问层（含 PatientDao）
│       │       └── pojo/        # 实体类（含 PatientUserInfo）
│       ├── pom.xml              # 父 POM（聚合模块）
│       ├── Dockerfile           # 后端容器构建
│       ├── docker-compose.yml   # 全服务编排
│       ├── fm_hospital.sql      # 数据库 SQL 备份
│       └── init-db.sh           # 数据库初始化脚本
├── frontend/
│   └── hospital_manege/        # 前端管理后台
│       ├── src/
│       │   ├── views/           # 页面组件（含 patient.vue）
│       │   └── router/          # 路由配置
│       ├── Dockerfile           # 前端容器构建
│       └── nginx.conf           # Nginx 配置
└── README.md
```

## 数据库核心表

### 患者相关（已精简）

| 表名 | 说明 |
|------|------|
| `patient_user_info` | 患者信息（就诊卡号、姓名、性别、身份证、手机、密码、疾病史） |
| `medical_registration` | 门诊挂号记录（关联患者、医生、诊室、就诊状态） |
| `doctor_consultation_report` | 就诊报告（诊断结果、处方，通过 registration_id 关联挂号单） |

> 已移除的表：`patient_user`（微信账号）、`patient_face_auth`（人脸认证）、`patient_video_diagnosis`（视频问诊记录）、`patient_video_diagnosis_files`

## 本地运行

### 前置条件

| 工具 | 版本要求 |
|------|---------|
| Docker | 任意版本（跑中间件） |
| JDK | 17（项目目标版本） |
| Maven | 3.6+ |
| Node.js | 16+ |
| npm | 8+ |

### 1. 启动基础设施（Docker）

在 `backend/hospital_manege/` 目录下运行：

```bash
cd backend/hospital_manege
docker compose up -d mysql redis rabbitmq minio
```

这将会启动 4 个容器：

| 服务 | 端口 | 认证 |
|------|------|------|
| MySQL | 4307:3306 | root / 123456 |
| Redis | 7379:6379 | 密码 123456 |
| RabbitMQ | 5672:5672 | root / 123456 |
| MinIO | 9000:9000 | root / 12345678abc |

启动前需确保已创建数据库初始化文件：

```bash
mkdir -p init-sql
cp fm_hospital.sql init-sql/init.sql
```

Docker 启动时会自动执行 `init-sql/init.sql` 完成建库建表。

> **注意**：Mac 用户首次启动可能遇到 `/home/hospital_manage/` 路径挂载问题，可以创建 `docker-compose.override.yml` 将卷路径改为本地目录（如 `./data/mysql:/var/lib/mysql`），该文件已被 .gitignore 忽略。

### 2. 启动后端

```bash
# 在 backend/hospital_manege 目录下

# 先安装 common 模块到本地仓库
mvn clean install -pl common -am -Dmaven.test.skip=true

# 启动后端 API
mvn -pl hospital_hms_api spring-boot:run -Dmaven.test.skip=true
```

后端运行在 `http://localhost:9091/hms`。

API 文档：`http://localhost:9091/hms/doc-api.html`

### 3. 启动前端

```bash
# 在 frontend/hospital_manege 目录下

npm install
npm run dev
```

前端运行在 `http://localhost:4000/hms-vue`。

### 4. MinIO 初始化（首次）

MinIO 首次启动后，需通过控制台创建 `hospital` 存储桶：

- 地址：`http://localhost:9001`
- 账号：`root` / `12345678abc`
- 创建名为 `hospital` 的 bucket

### 5. 访问系统

- 前端管理后台：`http://localhost:4000/hms-vue`
- 默认账号：`zhangsan` / `zhangsan`

### 首次运行快速脚本

```bash
# 1. 基础设施
cd backend/hospital_manege
mkdir -p init-sql && cp fm_hospital.sql init-sql/init.sql
docker compose up -d mysql redis rabbitmq minio
sleep 10  # 等待 MySQL 就绪

# 2. 后端
mvn clean install -pl common -am -Dmaven.test.skip=true
mvn -pl hospital_hms_api spring-boot:run -Dmaven.test.skip=true &

# 3. 前端
cd ../../frontend/hospital_manege
npm install
npm run dev
```

## 一键部署（Docker 生产模式）

如需完整的 Docker 部署（包含后端和前端容器）：

```bash
cd backend/hospital_manege
sudo mkdir -p /home/hospital_manage/{mysql,redis,rabbitmq,minio}
cp fm_hospital.sql init-sql/init.sql
docker compose up -d
```

访问 `http://localhost:4000/hms-vue`。

## 默认账号

| 用户名 | 密码 | 角色 |
|--------|------|------|
| zhangsan | zhangsan | 超级管理员 |
| admin | admin123 | 超级管理员 |
