# 患者管理数据表结构设计

## 背景

现有 `patient_user_info` 表结构简单，缺少医保类型、过敏史等关键字段；`doctor_consultation_report` 仅包含诊断和处方文本，无法支持完整门诊病历；处方信息无结构化存储。需要重新设计以支持"医生在系统中增删改查患者就诊信息"的功能。

## 设计决策

- **方案选择**：方案 A（改造现有表），保持与现有挂号、排班模块兼容
- **就诊信息范围**：完整门诊病历（主诉、现病史、体格检查、诊断、处方、医嘱等）
- **处方存储**：结构化处方表（处方主表 + 处方明细表）
- **病史存储**：固定字段（既往史、过敏史、家族史作为 `patient_user_info` 的字段）

## 表结构设计

### 1. `patient_user_info` — 患者基本信息（改造）

```sql
DROP TABLE IF EXISTS `patient_user_info`;
CREATE TABLE `patient_user_info` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键',
  `uuid` char(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '患者就诊卡编号',
  `name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '姓名',
  `sex` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '性别',
  `pid` varchar(18) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '身份证号',
  `tel` varchar(11) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '手机号码',
  `birthday` date NULL DEFAULT NULL COMMENT '出生日期',
  `password` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '登录密码',
  `medical_history` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '既往史',
  `allergy_history` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '过敏史',
  `family_history` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '家族史',
  `insurance_type` tinyint(4) NULL DEFAULT NULL COMMENT '医保类型: 0=自费, 1=城镇职工, 2=城乡居民, 3=新农合, 4=商业保险',
  `create_time` datetime(0) NULL DEFAULT CURRENT_TIMESTAMP(0) COMMENT '创建时间',
  `update_time` datetime(0) NULL DEFAULT CURRENT_TIMESTAMP(0) ON UPDATE CURRENT_TIMESTAMP(0) COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_pid` (`pid`) USING BTREE,
  INDEX `idx_tel` (`tel`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;
```

**变更说明**：
- `medical_history` 扩容 varchar(255) → varchar(500)
- 新增 `allergy_history` 过敏史
- 新增 `family_history` 家族史
- 新增 `insurance_type` 医保类型
- 新增 `create_time`、`update_time` 时间戳
- 新增 `pid`、`tel` 索引

### 2. `medical_registration` — 挂号记录（不变）

保持现有结构，作为挂号流程表。通过 `registration_id` 与 `medical_record` 关联。

```sql
-- 保持现有结构不变
CREATE TABLE `medical_registration` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键',
  `patient_card_id` int(11) NULL DEFAULT NULL COMMENT '患者就诊卡ID',
  `work_plan_id` int(11) NULL DEFAULT NULL COMMENT '医生出诊计划ID',
  `doctor_schedule_id` int(11) NULL DEFAULT NULL COMMENT '医生排班时段ID',
  `doctor_id` int(11) NULL DEFAULT NULL COMMENT '医生ID',
  `dept_sub_id` int(11) NULL DEFAULT NULL COMMENT '诊室ID',
  `date` date NULL DEFAULT NULL COMMENT '就诊日期',
  `slot` tinyint(4) NULL DEFAULT NULL COMMENT '时间段',
  `status` tinyint(4) NULL DEFAULT 0 COMMENT '就诊状态: 0=待就诊, 1=就诊中, 2=已就诊, 3=复诊中',
  `payment_status` tinyint(4) NULL DEFAULT NULL COMMENT '支付状态',
  `create_time` datetime(0) NULL DEFAULT CURRENT_TIMESTAMP(0) COMMENT '创建时间',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;
```

### 3. `medical_record` — 门诊病历（改造，原 `doctor_consultation_report`）

```sql
DROP TABLE IF EXISTS `medical_record`;
CREATE TABLE `medical_record` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键',
  `uuid` char(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '唯一编号',
  `registration_id` int(11) NULL DEFAULT NULL COMMENT '关联挂号单ID',
  `patient_id` int(11) NULL DEFAULT NULL COMMENT '患者ID',
  `doctor_id` int(11) NULL DEFAULT NULL COMMENT '医生ID',
  `dept_sub_id` int(11) NULL DEFAULT NULL COMMENT '诊室ID',
  `chief_complaint` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '主诉',
  `present_illness` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '现病史',
  `physical_exam` varchar(1000) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '体格检查',
  `diagnosis` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '诊断结果',
  `doctor_advice` varchar(1000) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '医嘱',
  `remark` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '备注',
  `create_time` datetime(0) NULL DEFAULT CURRENT_TIMESTAMP(0) COMMENT '创建时间',
  `update_time` datetime(0) NULL DEFAULT CURRENT_TIMESTAMP(0) ON UPDATE CURRENT_TIMESTAMP(0) COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_registration_id` (`registration_id`) USING BTREE,
  INDEX `idx_patient_id` (`patient_id`) USING BTREE,
  INDEX `idx_doctor_id` (`doctor_id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;
```

**变更说明**：
- 原表 `doctor_consultation_report` 重命名为 `medical_record`
- 新增 `patient_id` 冗余字段加速查询
- 新增 `chief_complaint` 主诉
- 新增 `present_illness` 现病史
- 新增 `physical_exam` 体格检查
- 新增 `doctor_advice` 医嘱
- 新增 `remark` 备注
- `diagnosis` 扩容 varchar(255) → varchar(500)
- 移除 `rp` 字段（处方信息迁移到 `prescription` 表）
- 新增 `create_time`、`update_time` 时间戳
- 新增 `registration_id`、`patient_id`、`doctor_id` 索引

### 4. `prescription` — 处方主表（新增）

```sql
DROP TABLE IF EXISTS `prescription`;
CREATE TABLE `prescription` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键',
  `uuid` char(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '处方编号',
  `medical_record_id` int(11) NULL DEFAULT NULL COMMENT '关联病历ID',
  `patient_id` int(11) NULL DEFAULT NULL COMMENT '患者ID',
  `doctor_id` int(11) NULL DEFAULT NULL COMMENT '开方医生ID',
  `type` tinyint(4) NULL DEFAULT 0 COMMENT '处方类型: 0=西药, 1=中药',
  `status` tinyint(4) NULL DEFAULT 0 COMMENT '状态: 0=待取药, 1=已取药, 2=已退药',
  `create_time` datetime(0) NULL DEFAULT CURRENT_TIMESTAMP(0) COMMENT '创建时间',
  `update_time` datetime(0) NULL DEFAULT CURRENT_TIMESTAMP(0) ON UPDATE CURRENT_TIMESTAMP(0) COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_medical_record_id` (`medical_record_id`) USING BTREE,
  INDEX `idx_patient_id` (`patient_id`) USING BTREE,
  INDEX `idx_doctor_id` (`doctor_id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;
```

### 5. `prescription_item` — 处方明细（新增）

```sql
DROP TABLE IF EXISTS `prescription_item`;
CREATE TABLE `prescription_item` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键',
  `prescription_id` int(11) NULL DEFAULT NULL COMMENT '关联处方ID',
  `drug_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '药品名称',
  `specification` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '规格',
  `quantity` int(11) NULL DEFAULT NULL COMMENT '数量',
  `dosage` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '用法用量',
  `frequency` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '频次',
  `days` int(11) NULL DEFAULT NULL COMMENT '天数',
  `remark` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '备注',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_prescription_id` (`prescription_id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;
```

## 表关系图

```
patient_user_info (1)───(N) medical_registration (1)───(1) medical_record (1)───(N) prescription (1)───(N) prescription_item
       │                           │                            │                        │
       └───────────────────────────┘                            └────────────────────────┘
                     patient_id 冗余                                   patient_id 冗余
```

## 索引策略

| 表 | 索引 | 用途 |
|----|------|------|
| `patient_user_info` | `idx_pid` | 按身份证号查询患者 |
| `patient_user_info` | `idx_tel` | 按手机号查询患者 |
| `medical_record` | `idx_registration_id` | 按挂号单查病历 |
| `medical_record` | `idx_patient_id` | 按患者查所有病历 |
| `medical_record` | `idx_doctor_id` | 按医生查所有病历 |
| `prescription` | `idx_medical_record_id` | 按病历查处方 |
| `prescription` | `idx_patient_id` | 按患者查所有处方 |
| `prescription` | `idx_doctor_id` | 按医生查所有处方 |
| `prescription_item` | `idx_prescription_id` | 按处方查明细 |

## 迁移注意事项

1. `doctor_consultation_report` → `medical_record`：需要迁移现有数据，`rp` 字段内容迁移到 `prescription` 表
2. `patient_user_info` 新增字段：`allergy_history`、`family_history`、`insurance_type` 默认为 NULL，不影响现有数据
3. `medical_history` 字段扩容 varchar(255) → varchar(500)，无需数据迁移
4. 现有 `PatientDao.xml` 中的 SQL 引用了 `doctor_consultation_report`，需要同步更新为 `medical_record`
