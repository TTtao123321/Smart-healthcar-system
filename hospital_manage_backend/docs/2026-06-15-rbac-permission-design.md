# RBAC 权限模型设计

## 概述

在现有 Sa-Token + JSON字段 结构上扩展 RBAC 权限模型，实现三个角色（超级管理员、医生、运营）的权限控制，并为超级管理员增加系统管理模块（角色管理、用户管理、权限管理）。

## 角色与权限矩阵

| 权限字符串 | 说明 | 超级管理员 | 医生 | 运营 |
|---|---|---|---|---|
| `ROOT` | 超级权限，绕过所有检查 | ✅ | - | - |
| `ORG:SELECT` | 组织管理-查看 | ✅ | ✅ | ✅ |
| `ORG:INSERT` | 组织管理-添加 | ✅ | - | ✅ |
| `ORG:UPDATE` | 组织管理-修改 | ✅ | - | ✅ |
| `ORG:DELETE` | 组织管理-删除 | ✅ | - | ✅ |
| `MEDICAL:SELECT` | 医护管理-查看 | ✅ | ✅ | ✅ |
| `MEDICAL:INSERT` | 医护管理-添加 | ✅ | - | ✅ |
| `MEDICAL:UPDATE` | 医护管理-修改 | ✅ | - | ✅ |
| `MEDICAL:DELETE` | 医护管理-删除 | ✅ | - | ✅ |
| `SCHEDULE:SELECT` | 出诊管理-查看 | ✅ | ✅ | ✅ |
| `SCHEDULE:INSERT` | 出诊管理-添加 | ✅ | - | ✅ |
| `SCHEDULE:UPDATE` | 出诊管理-修改 | ✅ | - | ✅ |
| `SCHEDULE:DELETE` | 出诊管理-删除 | ✅ | - | ✅ |
| `ROLE:SELECT` | 角色管理-查看 | ✅ | - | - |
| `ROLE:INSERT` | 角色管理-添加 | ✅ | - | - |
| `ROLE:UPDATE` | 角色管理-修改 | ✅ | - | - |
| `ROLE:DELETE` | 角色管理-删除 | ✅ | - | - |
| `USER:SELECT` | 用户管理-查看 | ✅ | - | - |
| `USER:INSERT` | 用户管理-添加 | ✅ | - | - |
| `USER:UPDATE` | 用户管理-修改 | ✅ | - | - |
| `USER:DELETE` | 用户管理-删除 | ✅ | - | - |
| `PERMISSION:SELECT` | 权限管理-查看 | ✅ | - | - |

## 数据库变更

### module 表（重新定义）

| ID | module_code | module_name |
|---|---|---|
| 1 | ORG | 组织管理 |
| 2 | MEDICAL | 医护管理 |
| 3 | SCHEDULE | 出诊管理 |
| 4 | SYSTEM | 系统管理 |

### action 表（保持不变）

INSERT, DELETE, UPDATE, SELECT, APPROVAL, EXPORT, BACKUP, ARCHIVE

### permission 表（重新定义）

22个权限 + ROOT，权限名格式为 `MODULE:ACTION`，与前端注解完全对齐。

### role 表（重新定义）

| ID | role_name | permissions | systemic |
|---|---|---|---|
| 1 | 超级管理员 | [ROOT的permission_id] | 1 |
| 2 | 医生 | [ORG:SELECT, MEDICAL:SELECT, SCHEDULE:SELECT的permission_id] | 1 |
| 3 | 运营 | [ORG/MEDICAL/SCHEDULE的SELECT~DELETE的permission_id] | 1 |

### users 表

现有用户的 `role` JSON字段更新为对应角色ID。

## 后端变更

### 新增文件

1. **RoleController** — 角色CRUD接口
2. **PermissionController** — 权限查询接口
3. **RoleDao / RoleDao.xml** — 角色数据访问
4. **RoleService / RoleServiceImpl** — 角色业务逻辑
5. **PermissionDao / PermissionDao.xml** — 权限数据访问
6. **PermissionService / PermissionServiceImpl** — 权限业务逻辑
7. **相关Form类** — 请求参数校验

### 修改文件

1. **UserController** — 扩展用户CRUD接口
2. **UserDao / UserDao.xml** — 新增用户CRUD方法和SQL
3. **UserService / UserServiceImpl** — 新增用户CRUD方法
4. **StpInterfaceConfig** — 实现 getRoleList 方法
5. **现有Controller** — 更新权限注解对齐新权限字符串

### 权限注解映射

| 旧权限字符串 | 新权限字符串 | Controller |
|---|---|---|
| MEDICAL_DEPT:SELECT/INSERT/UPDATE/DELETE | ORG:SELECT/INSERT/UPDATE/DELETE | DeptController |
| MEDICAL_DEPT_SUB:SELECT/INSERT/UPDATE/DELETE | ORG:SELECT/INSERT/UPDATE/DELETE | DeptSubController |
| DOCTOR:SELECT/INSERT/UPDATE/DELETE | MEDICAL:SELECT/INSERT/UPDATE/DELETE | DoctorController |
| DOCTOR_WORK_PLAN:SELECT/INSERT | SCHEDULE:SELECT/INSERT | DoctorWorkPlanController |
| DOCTOR_WORK_PLAN_SCHEDULE:SELECT/UPDATE/DELETE | SCHEDULE:SELECT/UPDATE/DELETE | DoctorWorkPlanScheduleController |
| PATIENT:SELECT | MEDICAL:SELECT | PatientController |
| DOCTOR_PRICE:SELECT | MEDICAL:SELECT | (诊费设置) |

## 前端变更

### 新增页面

1. **role.vue** — 角色管理
2. **user_manage.vue** — 用户管理
3. **permission.vue** — 权限管理

### 修改文件

1. **router/index.js** — 新增3个路由
2. **main.vue** — 侧边栏新增"系统管理"菜单，导航栏用户名动态显示
3. **现有页面** — 按钮级权限控制
4. **login.vue** — 存储用户角色信息

### 侧边栏菜单结构

```
首页
组织管理
  ├── 医疗科室管理
  └── 医疗诊室管理
医护管理
  ├── 医生管理
  ├── 患者管理
  └── 诊费设置
出诊管理
  ├── 门诊日程表
  └── 医生出诊表
系统管理（仅超级管理员可见）
  ├── 角色管理
  ├── 用户管理
  └── 权限管理
```

## 权限控制流程

```
用户登录 → 后端查询用户角色 → 通过角色查询权限列表 → 返回权限集合给前端
→ 前端存入 localStorage → isAuth() 控制菜单/按钮显示
→ 后端 @SaCheckPermission 校验每个API请求
```
