# HMS 诊费管理模块 - 设计文档

**日期：** 2026-06-24
**范围：** hospital_manage_backend 后端 API

## 概述

为 `doctor_price` 表开发完整的 CRUD 后端接口，对接现有前端页面 `doctor_price.vue` 和 `doctor_price-update.vue`。

## 数据库

表 `doctor_price` 已存在：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int(11) PK | 自增主键 |
| doctor_id | int(11) | 医生 ID |
| level | varchar(200) | 职称级别 |
| price_1 | decimal(10,2) | 门诊挂号费 |
| price_2 | decimal(10,2) | 视频问诊挂号费 |

## 文件清单

所有文件位于 `hospital_hms_api/src/main/java/com/hospital/hms/` 下：

| 层 | 文件 | 路径 |
|---|------|------|
| Pojo | DoctorPrice.java | pojo/ |
| Dao | DoctorPriceDao.java | dao/ |
| Mapper XML | DoctorPriceDao.xml | resources/mapper/ |
| Service 接口 | DoctorPriceService.java | service/ |
| Service 实现 | DoctorPriceServiceImpl.java | service/impl/ |
| Controller | DoctorPriceController.java | controller/ |
| Form | SelectDoctorPriceByPageForm.java | controller/form/ |
| Form | InsertDoctorPriceForm.java | controller/form/ |
| Form | UpdateDoctorPriceForm.java | controller/form/ |
| Form | DeleteDoctorPriceByIdsForm.java | controller/form/ |

## API 接口

Base path: `/doctor_price`

### 1. 分页查询

```
POST /doctor_price/selectByPage
权限: ROOT / MEDICAL:SELECT
```

请求体：
```json
{
  "name": "医生姓名（可选）",
  "deptId": "科室ID（可选）",
  "job": "职称（可选）",
  "status": "状态（可选，1在职/2离职/3退休）",
  "page": 1,
  "length": 10
}
```

返回：分页列表，每行包含 `doctorName, sex, job, deptName, deptSubName, price_1, price_2, doctorId`。

查询逻辑：`doctor_price` LEFT JOIN `doctor` LEFT JOIN `medical_dept_sub_doctor` LEFT JOIN `medical_dept_sub` LEFT JOIN `medical_dept`。

### 2. 新增诊费

```
POST /doctor_price/insert
权限: ROOT / MEDICAL:INSERT
```

请求体：`{ doctorId, level, price_1, price_2 }`

### 3. 更新诊费

```
POST /doctor_price/update
权限: ROOT / MEDICAL:UPDATE
```

请求体：`{ id, price_1, price_2, level }`

### 4. 批量删除

```
POST /doctor_price/deleteByIds
权限: ROOT / MEDICAL:DELETE
```

请求体：`{ ids: [1, 2, 3] }`

## 技术约定

- 遵循现有 Doctor 模块的代码风格和命名规范
- 使用 MyBatis XML Mapper
- 使用 Sa-Token 权限注解
- 使用 Swagger `@Tag` / `@Operation` 注解
- 使用 Lombok `@Data` / `@Slf4j`
- 返回统一 `CommonResult` 格式
- 参数校验使用 `@Valid` + Form 类中的 JSR-303 注解