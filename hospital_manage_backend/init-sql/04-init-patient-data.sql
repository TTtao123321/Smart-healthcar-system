-- ============================================
-- 患者管理测试数据
-- 包含：患者信息、挂号记录、门诊病历、处方、处方明细
-- ============================================

SET NAMES utf8mb4;
SET CHARACTER_SET_CONNECTION=utf8mb4;

-- 创建缺失的表（如果 01-init.sql 未包含）
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

-- 清理旧数据
DELETE FROM prescription_item;
DELETE FROM prescription;
DELETE FROM medical_record;
DELETE FROM medical_registration WHERE patient_card_id BETWEEN 1 AND 8;
DELETE FROM patient_user_info WHERE id BETWEEN 1 AND 8;

-- 1. 患者基本信息
INSERT INTO `patient_user_info` (`id`, `uuid`, `name`, `sex`, `pid`, `tel`, `birthday`, `password`, `medical_history`, `allergy_history`, `family_history`, `insurance_type`) VALUES
(1, 'a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6', '张伟', '男', '110101199001011234', '13800138001', '1990-01-01', 'E10ADC3949BA59ABBE56E057F20F883E', '高血压2年，规律服药中', '青霉素过敏', '父亲有高血压病史', 1),
(2, 'b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7', '李娜', '女', '110102198505052345', '13800138002', '1985-05-05', 'E10ADC3949BA59ABBE56E057F20F883E', '糖尿病5年，口服降糖药', '磺胺类药物过敏', '母亲有糖尿病病史', 1),
(3, 'c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8', '王强', '男', '110103197808083456', '13800138003', '1978-08-08', 'E10ADC3949BA59ABBE56E057F20F883E', '冠心病3年，支架术后', '无', '父亲冠心病，母亲高血压', 2),
(4, 'd4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9', '赵敏', '女', '110104199203034567', '13800138004', '1992-03-03', 'E10ADC3949BA59ABBE56E057F20F883E', '无', '海鲜过敏、花粉过敏', '无特殊家族史', 0),
(5, 'e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0', '陈静', '女', '110105198812125678', '13800138005', '1988-12-12', 'E10ADC3949BA59ABBE56E057F20F883E', '甲状腺功能减退2年', '无', '姐姐甲状腺疾病', 3),
(6, 'f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1', '刘洋', '男', '110106199506066789', '13800138006', '1995-06-06', 'E10ADC3949BA59ABBE56E057F20F883E', '无', '头孢类过敏', '无', 4),
(7, 'a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2', '孙丽', '女', '110107198211117890', '13800138007', '1982-11-11', 'E10ADC3949BA59ABBE56E057F20F883E', '慢性胃炎3年', '无', '母亲胃癌', 1),
(8, 'b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3', '周磊', '男', '110108197604048901', '13800138008', '1976-04-04', 'E10ADC3949BA59ABBE56E057F20F883E', '高血脂、脂肪肝', '无', '父亲脑梗塞', 2);

-- 2. 挂号记录（medical_registration）
-- doctor_id 对应已有医生：1=李雨萌, 2=张佳欣, 3=王文彦, 4=刘梦琪, 7=吴子萱, 9=许文彬
-- dept_sub_id 对应已有诊室：2=眼科门诊, 20=皮肤病门诊, 18=心脏外科门诊
INSERT INTO `medical_registration` (`id`, `patient_card_id`, `work_plan_id`, `doctor_schedule_id`, `doctor_id`, `dept_sub_id`, `date`, `slot`, `status`, `payment_status`) VALUES
(1,  1, 1, NULL, 1, 2,  '2026-06-14', 3, 2, 1),
(2,  1, 2, NULL, 2, 20, '2026-06-15', 5, 2, 1),
(3,  2, 3, NULL, 3, 2,  '2026-06-15', 7, 2, 1),
(4,  2, 4, NULL, 1, 2,  '2026-06-16', 1, 1, 1),
(5,  3, 5, NULL, 4, 18, '2026-06-14', 9, 2, 1),
(6,  3, 6, NULL, 4, 18, '2026-06-16', 3, 0, 1),
(7,  4, 7, NULL, 7, 2,  '2026-06-15', 2, 2, 1),
(8,  5, 8, NULL, 9, 20, '2026-06-14', 4, 2, 1),
(9,  5, 9, NULL, 9, 20, '2026-06-16', 6, 1, 1),
(10, 6, 10, NULL, 2, 20, '2026-06-15', 8, 2, 1),
(11, 7, 11, NULL, 3, 2,  '2026-06-14', 10, 2, 1),
(12, 8, 12, NULL, 1, 2,  '2026-06-16', 2, 0, 1);

-- 3. 门诊病历（medical_record）
-- registration_id 关联挂号单，patient_id 冗余患者ID
INSERT INTO `medical_record` (`id`, `uuid`, `registration_id`, `patient_id`, `doctor_id`, `dept_sub_id`, `chief_complaint`, `present_illness`, `physical_exam`, `diagnosis`, `doctor_advice`, `remark`) VALUES
(1, 'aa11bb22cc33dd44ee55ff66aa77bb88', 1,  1, 1, 2,  '双眼视力下降1月', '患者1月前无明显诱因出现双眼视力下降，以左眼为著，伴眼前黑影飘动，无眼红眼痛，无头痛恶心。既往高血压2年，规律服药。', '视力：右0.8 左0.4，眼压：右16mmHg 左17mmHg，晶体透明，眼底视盘边界清，黄斑区未见明显水肿', '左眼老年性白内障', '1. 左眼白内障手术待定\n2. 术前常规检查\n3. 控制血压至140/90mmHg以下', '择期手术'),
(2, 'bb22cc33dd44ee55ff66aa77bb88cc99', 2,  1, 2, 20, '全身皮疹伴瘙痒1周', '患者1周前进食海鲜后出现全身红色丘疹，伴剧烈瘙痒，以躯干和四肢为主，无发热，无关节痛。既往高血压病史。', '全身皮肤可见散在红色丘疹，以躯干及四肢伸侧为主，部分融合成片，有抓痕及血痂', '荨麻疹', '1. 氯雷他定片 10mg 每日1次\n2. 炉甘石洗剂 外用\n3. 避免接触过敏原', '注意饮食'),
(3, 'cc33dd44ee55ff66aa77bb88cc99dd00', 3,  2, 3, 2,  '右眼红痛3天', '患者3天前出现右眼红痛，伴异物感、流泪，视力轻度下降，无分泌物增多。糖尿病5年，口服降糖药控制。', '视力：右0.6 左0.8，右眼球结膜充血(++)，角膜上皮点状剥脱，前房清，瞳孔圆', '右眼角膜炎', '1. 左氧氟沙星滴眼液 每日4次\n2. 更昔洛韦眼用凝胶 每日3次\n3. 一周后复查', '监测血糖'),
(4, 'dd44ee55ff66aa77bb88cc99dd00ee11', 5,  3, 4, 18, '胸闷气短2天', '患者2天前活动后出现胸闷气短，休息后可缓解，无胸痛，无晕厥。冠心病3年，支架术后规律服药。', 'BP 135/85mmHg，HR 78次/分，律齐，各瓣膜区未闻及杂音，双肺呼吸音清', '冠心病 稳定型心绞痛', '1. 继续规律口服阿司匹林、他汀类药物\n2. 硝酸甘油片 舌下含服 必要时\n3. 避免剧烈活动', '定期复查冠脉CTA'),
(5, 'ee55ff66aa77bb88cc99dd00ee11ff22', 7,  4, 7, 2,  '双眼干涩不适2周', '患者2周来双眼干涩不适，有异物感，视疲劳明显，尤以用眼后为著。无特殊既往史。', '视力：右1.0 左1.0，泪膜破裂时间：右5s 左4s，角膜荧光素染色(-)，Schirmer试验：右6mm 左5mm', '干眼症', '1. 玻璃酸钠滴眼液 每日4次\n2. 热敷双眼 每日2次\n3. 减少电子屏幕使用时间', '2周后复查'),
(6, 'ff66aa77bb88cc99dd00ee11ff22aa33', 8,  5, 9, 20, '面部红斑1月', '患者1月前面部出现红斑，日晒后加重，伴轻度瘙痒，无关节痛，无口腔溃疡。甲减2年，口服左甲状腺素。', '面部双颊可见对称性蝶形红斑，边界清楚，表面少许鳞屑，无萎缩性瘢痕', '面部皮炎', '1. 羟氯喹片 0.2g 每日2次\n2. 丁酸氢化可的松乳膏 外用 每日2次\n3. 严格防晒', '排查结缔组织病'),
(7, 'aa77bb88cc99dd00ee11ff22aa33bb44', 10, 6, 2, 20, '右手皮疹2周', '患者2周前右手出现环形红斑，逐渐扩大，伴轻度脱屑和瘙痒。', '右手背可见2cm×3cm环形红斑，边缘隆起，中央消退，有少许鳞屑', '体癣', '1. 特比萘芬乳膏 外用 每日2次\n2. 连续用药2-4周\n3. 保持皮肤清洁干燥', '真菌镜检阳性'),
(8, 'bb88cc99dd00ee11ff22aa33bb44cc55', 11, 7, 3, 2,  '左眼视物模糊1周', '患者1周来左眼视物模糊，伴眼前闪光感，无眼红眼痛。慢性胃炎3年。', '视力：右1.0 左0.5，左眼玻璃体混浊(+)，眼底见上方视网膜扁平隆起，未见裂孔', '左眼视网膜浅脱离', '1. 眼底激光光凝待定\n2. 避免剧烈运动和重体力劳动\n3. 半卧位休息', '紧急安排眼底检查');

-- 4. 处方主表（prescription）
INSERT INTO `prescription` (`id`, `uuid`, `medical_record_id`, `patient_id`, `doctor_id`, `type`, `status`) VALUES
(1, 'cc99dd00ee11ff22aa33bb44cc55dd66', 1, 1, 1, 0, 1),
(2, 'dd00ee11ff22aa33bb44cc55dd66ee77', 2, 1, 2, 0, 1),
(3, 'ee11ff22aa33bb44cc55dd66ee77ff88', 3, 2, 3, 0, 0),
(4, 'ff22aa33bb44cc55dd66ee77ff88aa99', 4, 3, 4, 0, 1),
(5, 'aa33bb44cc55dd66ee77ff88aa99bb00', 5, 4, 7, 0, 0),
(6, 'bb44cc55dd66ee77ff88aa99bb00cc11', 6, 5, 9, 0, 0),
(7, 'cc55dd66ee77ff88aa99bb00cc11dd22', 6, 5, 9, 1, 1),
(8, 'dd66ee77ff88aa99bb00cc11dd22ee33', 7, 6, 2, 0, 1),
(9, 'ee77ff88aa99bb00cc11dd22ee33ff44', 8, 7, 3, 0, 0);

-- 5. 处方明细（prescription_item）
INSERT INTO `prescription_item` (`id`, `prescription_id`, `drug_name`, `specification`, `quantity`, `dosage`, `frequency`, `days`, `remark`) VALUES
-- 处方1：张伟-白内障术前用药
(1,  1, '左氧氟沙星滴眼液', '5ml:15mg', 1, '每次1-2滴', '每日4次', 7, '术前3天开始使用'),
(2,  1, '双氯芬酸钠滴眼液', '5ml:5mg', 1, '每次1-2滴', '每日3次', 7, '消炎止痛'),
-- 处方2：张伟-荨麻疹
(3,  2, '氯雷他定片', '10mg×6片', 2, '每次1片', '每日1次', 14, '睡前服用'),
(4,  2, '炉甘石洗剂', '100ml', 1, '外涂患处', '每日3-4次', 7, '摇匀后使用'),
-- 处方3：李娜-角膜炎
(5,  3, '左氧氟沙星滴眼液', '5ml:15mg', 1, '每次1-2滴', '每日4次', 7, NULL),
(6,  3, '更昔洛韦眼用凝胶', '2g:2mg', 1, '每次约1cm', '每日3次', 7, '睡前使用'),
-- 处方4：王强-冠心病
(7,  4, '阿司匹林肠溶片', '100mg×30片', 1, '每次1片', '每日1次', 30, '饭后服用'),
(8,  4, '阿托伐他汀钙片', '20mg×7片', 4, '每次1片', '每晚1次', 30, '监测肝功能'),
(9,  4, '硝酸甘油片', '0.5mg×100片', 1, '舌下含服', '必要时', NULL, '心绞痛发作时使用'),
-- 处方5：赵敏-干眼症
(10, 5, '玻璃酸钠滴眼液', '5ml:5mg', 2, '每次1-2滴', '每日4次', 14, NULL),
-- 处方6：陈静-面部皮炎（西药）
(11, 6, '羟氯喹片', '0.2g×10片', 2, '每次1片', '每日2次', 20, '饭后服用'),
(12, 6, '丁酸氢化可的松乳膏', '10g:10mg', 1, '外涂患处', '每日2次', 7, '薄涂即可'),
-- 处方7：陈静-面部皮炎（中药）
(13, 7, '消风散加减', '7剂', 1, '每日1剂 水煎分2次服', '每日2次', 7, '早晚温服'),
-- 处方8：刘洋-体癣
(14, 8, '特比萘芬乳膏', '10g:1%', 1, '外涂患处', '每日2次', 14, '连续使用2-4周'),
(15, 8, '伊曲康唑胶囊', '100mg×14粒', 1, '每次1粒', '每日1次', 14, '餐后立即服用'),
-- 处方9：孙丽-视网膜浅脱离
(16, 9, '甲钴胺片', '0.5mg×20片', 2, '每次1片', '每日3次', 14, '营养神经'),
(17, 9, '七叶洋地黄双苷滴眼液', '0.4ml:0.04mg', 1, '每次1-2滴', '每日3次', 14, '改善微循环');
