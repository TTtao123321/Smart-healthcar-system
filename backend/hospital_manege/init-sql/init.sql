-- ============================================================
-- 智慧医院管理系统 - 数据库一键初始化脚本
-- 兼容 MySQL 5.7+ / 8.0
-- 适用于 Docker 自动初始化 或 手动导入
-- ============================================================

-- 创建数据库（Docker 环境下 MYSQL_DATABASE 已自动创建，此句无影响）
CREATE DATABASE IF NOT EXISTS `fm_hospital` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `fm_hospital`;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table: action（行为表）
-- ----------------------------
DROP TABLE IF EXISTS `action`;
CREATE TABLE `action` (
  `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
  `action_code` varchar(200) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '行为编号',
  `action_name` varchar(200) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '行为名称',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `unq_action_name`(`action_name`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 9 CHARACTER SET = utf8 COLLATE = utf8_general_ci COMMENT = '行为表' ROW_FORMAT = Dynamic;

INSERT INTO `action` VALUES (1, 'INSERT', '添加');
INSERT INTO `action` VALUES (2, 'DELETE', '删除');
INSERT INTO `action` VALUES (3, 'UPDATE', '修改');
INSERT INTO `action` VALUES (4, 'SELECT', '查询');
INSERT INTO `action` VALUES (5, 'APPROVAL', '审批');
INSERT INTO `action` VALUES (6, 'EXPORT', '导出');
INSERT INTO `action` VALUES (7, 'BACKUP', '备份');
INSERT INTO `action` VALUES (8, 'ARCHIVE', '归档');

-- ----------------------------
-- Table: dept（部门表）
-- ----------------------------
DROP TABLE IF EXISTS `dept`;
CREATE TABLE `dept` (
  `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
  `dept_name` varchar(200) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '部门名称',
  `tel` varchar(20) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL COMMENT '部门电话',
  `email` varchar(200) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL COMMENT '部门邮箱',
  `desc` varchar(20) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL COMMENT '备注',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `unq_dept_name`(`dept_name`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 107 CHARACTER SET = utf8 COLLATE = utf8_general_ci COMMENT = '部门表' ROW_FORMAT = Dynamic;

INSERT INTO `dept` VALUES (1, '总裁部', '020-12345678', '111222@163.com', '管理部负责管理公司所有事务');
INSERT INTO `dept` VALUES (2, '行政部', '020-12345678', '111222@163.com', '负责行政管理');
INSERT INTO `dept` VALUES (3, '技术部', '020-12345678', '111222@163.com', '负责产品技术开发');
INSERT INTO `dept` VALUES (4, '市场部', '020-12345678', '111222@163.com', '负责市场管理');
INSERT INTO `dept` VALUES (5, '后勤部', '020-12345678', '111222@163.com', '负责后勤管理');
INSERT INTO `dept` VALUES (6, '人事部', '020-12345678', '111222@qq.com', '负责人事相关事宜管理');
INSERT INTO `dept` VALUES (106, '测试', '020-12345678', '222@aa.com', '111222');

-- ----------------------------
-- Table: doctor（医生表）
-- ----------------------------
DROP TABLE IF EXISTS `doctor`;
CREATE TABLE `doctor` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键',
  `name` varchar(20) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL COMMENT '姓名',
  `pid` varchar(200) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL COMMENT '身份证ID',
  `uuid` varchar(200) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL COMMENT '工牌号',
  `sex` varchar(200) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL COMMENT '性别',
  `photo` varchar(200) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL COMMENT '照片存储地址',
  `birthday` date DEFAULT NULL COMMENT '生日',
  `school` varchar(200) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL COMMENT '毕业院校',
  `degree` varchar(200) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL COMMENT '学位',
  `tel` varchar(11) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL COMMENT '电话',
  `address` varchar(200) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL COMMENT '地址',
  `email` varchar(200) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL COMMENT '邮箱',
  `job` varchar(200) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL COMMENT '职位',
  `remark` varchar(200) CHARACTER SET utf16le COLLATE utf16le_general_ci DEFAULT NULL COMMENT '备注信息',
  `description` varchar(200) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL COMMENT '详细介绍',
  `hiredate` date DEFAULT NULL COMMENT '入职日期',
  `tag` varchar(200) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL COMMENT '特长',
  `recommended` tinyint(1) DEFAULT NULL COMMENT '是否是优秀医生',
  `status` bigint(1) NOT NULL COMMENT '1在职，2离职，3退休，4隐藏（逻辑删除）',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 93 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

INSERT INTO `doctor` VALUES (1, '李雨萌', '360201198609151112', '2F0EB81AF9094277A958A41B59139DE1', '女', '/doctor/doctor-1.jpg', '1968-08-08', '重庆医科大学', '研究生', '13593812531', '北京市西城区北三环中路14-1号', 'chengchunmei@hospital.com', '副主任医师', '首都医科大学博士生导师', '擅长诊疗：心脏血管外科...', '2004-02-15', '[\"人很好\",\"哈哈\"]', 1, 1, '2024-03-06 00:00:00');
INSERT INTO `doctor` VALUES (2, '张佳欣', '460201197611302855', 'F1FDE764A9BB405596895722F1CCDB06', '男', '/doctor/doctor-2.jpg', '1959-05-03', '中国医科大学', '博士', '15179382777', '北京市海淀区龙翔路9号', 'qinxinyuan@hospital.com', '主任医师', '陆军军医大学研究生导师', '擅长诊疗：下肢静脉曲张的微创治疗...', '2004-12-11', '[\"从业46年\",\"领域专家\",\"快速回复\"]', 1, 1, '2024-03-06 00:00:00');
INSERT INTO `doctor` VALUES (3, '王文彦', '370101197707304145', '2AE43F717E444031BC0CBB5878932B07', '男', '/doctor/doctor-3.jpg', '1976-11-28', '北京协和医学院', '博士', '18658678090', '北京市朝阳区三里屯路北1楼', 'xiongjiayu@hospital.com', '主任医师', '国家远程医疗医学中心主任委员', '擅长诊疗：慢性咳嗽、喘息性/呼吸困难性疾病...', '2005-08-04', '[\"从业27年\",\"领域专家\",\"快速回复\"]', 1, 1, '2024-03-06 00:00:00');
INSERT INTO `doctor` VALUES (4, '刘梦琪', '370101197707304145', '50595ADEF85C4B35A114A462B0FA0CDA', '女', '/doctor/doctor-4.jpg', '1977-06-14', '北京协和医学院', '研究生', '14580412494', '北京市海淀区花园东路8号院', 'mengmingyuan@hospital.com', '主任医师', '北京医科大学研究生导师', '擅长诊疗：面神经修复与面部整形重建...', '2005-08-04', '[\"快速回复\",\"很厉害\"]', 1, 1, '2024-03-06 00:00:00');
INSERT INTO `doctor` VALUES (5, '赵晓雨', '520201198509071764', 'B762C0BF9F994D23B5695EA78AE3F4F7', '女', '/doctor/doctor-5.jpg', '1978-12-31', '北京协和医学院', '博士', '15597529530', '北京市西城区大乘巷1号', 'fangjiayi@hospital.com', '主任医师', '北京医科大学、北京中医药大学研究生导师', '擅长诊疗：泌尿系肿瘤...', '2005-08-04', '[\"从业24年\",\"领域专家\",\"温暖贴心\"]', 1, 4, '2024-03-06 00:00:00');
INSERT INTO `doctor` VALUES (6, '周嘉欣', '500101200212123472', '9718C444BE3646818DD264FB26EC8181', '男', '/doctor/doctor-6.jpg', '1974-01-07', '北京协和医学院', '博士', '17723959830', '北京市西城区滨河里34号', 'huangtao@hospital.com', '主任医师', '北京医科大学硕士研究生导师', '擅长诊疗：临床常见恶性肿瘤的放射治疗...', '2005-08-04', '[\"从业26年\",\"领域专家\",\"温暖贴心\"]', 1, 1, '2024-03-06 00:00:00');
INSERT INTO `doctor` VALUES (7, '吴子萱', '620101197707093458', '126A2D95DF2E42E4BD093FB9299623FB', '女', '/doctor/doctor-7.jpg', '1977-05-03', '解放军第三军医大学', '博士', '18362319314', '北京市海淀区复兴路12号8楼', 'wumengmeng@hospital.com', '主任医师', '中国医师协会微无创专业委员会委员', '擅长诊疗：青光眼和白内障的临床诊断及治疗...', '2005-08-04', '[\"从业26年\",\"领域专家\",\"温暖贴心\"]', 1, 1, '2024-03-06 00:00:00');
INSERT INTO `doctor` VALUES (8, '黄思雨', '130201200402256643', 'A1F9664A527F4DCBA48ADF312AFBC421', '女', '/doctor/doctor-8.jpg', '1972-07-28', '广州医科大学', '博士', '18576200235', '北京市海淀区太平路22号', 'tianfang@hospital.com', '主任医师', '中国医药教育协会肿瘤专家委员会委员', '擅长诊疗：头颈肿瘤的外科及综合治疗...', '2005-08-04', '[\"从业31年\",\"领域专家\",\"温暖贴心\"]', 1, 4, '2024-03-06 00:00:00');
INSERT INTO `doctor` VALUES (9, '许文彬', '420101199510078280', '3D3F7F2204204E30AD2F23C28A569B9A', '男', '/doctor/doctor-9.jpg', '1977-02-14', '哈尔滨医科大学', '博士', '13822560280', '北京市西城区车站西街15号院-5号楼', 'majie@hospital.com', '主任医师', '北京医师协会皮肤病专业专家委员会委员', '擅长诊疗：以皮肤病理为专长...', '2005-08-04', '[\"从业22年\",\"领域专家\",\"温暖贴心\"]', 1, 4, '2024-03-06 00:00:00');
INSERT INTO `doctor` VALUES (10, '郑雅琪', '510101198806215034', 'CD2C65C455564181ADFF84BD6A2F35C7', '女', '/doctor/doctor-10.jpg', '1978-06-22', '南京医科大学', '研究生', '19738130796', '北京市丰台区望园东路2928号', 'dujiayu@hospital.com', '主治医师', '参加多项国家级、省部级多项科研课题', '擅长诊疗：应用中西医优势互补方法治疗糖尿病...', '2005-08-04', '[\"从业17年\",\"领域专家\",\"温暖贴心\"]', 1, 1, '2024-03-06 00:00:00');
INSERT INTO `doctor` VALUES (11, '冯佳雨', '530201199301048406', 'FFBA296720C8495785E8A78B379C9B05', '男', '/doctor/doctor-11.jpg', '1975-11-11', '天津医科大学', '博士', '13777571218', '北京市石景山区重聚路40号院-3号', 'dengguodong@hospital.com', '副主任医师', '北京医师协会风湿免疫专科分会理事', '擅长诊疗：系统性红斑狼疮、多发性肌炎...', '2005-08-04', '[\"从业19年\",\"领域专家\",\"温暖贴心\"]', 1, 1, '2024-03-06 00:00:00');
INSERT INTO `doctor` VALUES (12, '蔡心怡', '120201198705219290', '0255BFF8CCC1479C898E21D1D3B0A8E7', '男', '/doctor/doctor-12.jpg', '1978-12-16', '中国医科大学', '研究生', '13069020752', '北京市海淀区玉泉路16号院', 'longzeyuan@hospital.com', '副主治医师', '参与多项国家自然科学基金课题研究', '擅长诊疗：多发性肌炎，皮肌炎...', '2005-08-04', '[\"从业15年\",\"领域专家\",\"温暖贴心\"]', 1, 1, '2024-03-06 00:00:00');
INSERT INTO `doctor` VALUES (13, '朱宇琪', '650201198402246623', '0370428B5452441C9F64658F2B7BC7F1', '女', '/doctor/doctor-13.jpg', '1970-12-16', '中国医科大学', '博士', '15977965686', '北京市西城区马连道南街1号院', 'songxiuying@hospital.com', '主治医师', '中华医学会风湿病分会会员', '擅长诊疗：从事风湿免疫疾病临床诊断...', '2005-08-04', '[\"从业28年\",\"领域专家\",\"温暖贴心\"]', 1, 1, '2024-03-06 00:00:00');
INSERT INTO `doctor` VALUES (14, '曾子轩', '450201198007308399', '6BD7AB9AE6AD417A90042FF3536ECC6C', '男', '/doctor/doctor-14.jpg', '1971-01-07', '中国医科大学', '博士', '15589198858', '北京市石景山区八角南路19号楼', 'xuerongrun@hospital.com', '主治医师', '北京市泌尿外科分会结石感染组委员', '擅长诊疗：经皮肾镜、输尿管镜微创治疗...', '2005-08-04', '[\"从业26年\",\"领域专家\",\"温暖贴心\"]', 1, 1, '2024-03-06 00:00:00');
INSERT INTO `doctor` VALUES (15, '翟婷婷', '610201197909271420', '6B4A32C097BA44F1B052B6F85C2D3E7B', '男', '/doctor/doctor-15.jpg', '1968-01-07', '南京医科大学', '博士', '13923984769', '北京市丰台区久敬庄路乙1号', 'tanshang@hospital.com', '主治医师', '北京医科大学硕士研究生导师', '擅长诊疗：熟练掌握胸外科专业各类疾病的诊断...', '2005-08-04', '[\"从业36年\",\"领域专家\",\"温暖贴心\"]', 1, 1, '2024-03-06 00:00:00');
INSERT INTO `doctor` VALUES (16, '彭俊豪', '420201198903179411', '43E06B95BD364ACD890C73D91D9881BF', '男', '/doctor/doctor-16.jpg', '1972-03-17', '首都医科大学', '博士', '18068672244', '北京市朝阳区东三环北路辛2号', 'renzhenguo@hospital.com', '主治医师', '北京口腔临床技术研究会理事', '擅长诊疗：成人正畸、隐形正畸...', '2005-08-04', '[\"从业29年\",\"领域专家\",\"温暖贴心\"]', 1, 1, '2024-03-06 00:00:00');
INSERT INTO `doctor` VALUES (17, '潘佳慧', '220101200306063805', 'DDAF4F5F849B4D2AB6DB8CA442794A5C', '女', '/doctor/doctor-17.jpg', '1973-05-08', '首都医科大学', '博士', '17267270501', '北京市东城区和平里北街21号', 'xujingqi@hospital.com', '主治医师', '北京口腔临床技术研究会理事', '擅长诊疗：擅长龋齿、牙髓病和根尖周病的诊断...', '2005-08-04', '[\"从业26年\",\"领域专家\",\"温暖贴心\"]', 1, 1, '2024-03-06 00:00:00');
INSERT INTO `doctor` VALUES (18, '袁文斌', '630201198312155601', '6B946B8B0C4A42DA8DE05E62A6CDE8E6', '男', '/doctor/doctor-19.jpg', '1974-12-24', '北京大学口腔医学院', '博士', '13773287399', '北京市东城区北新桥三条甲58号', 'lvchenglong@hospital.com', '主治医师', '北京口腔临床技术研究会理事', '擅长诊疗：口腔科常见病、多发病的诊疗工作...', '2005-08-04', '[\"从业25年\",\"领域专家\",\"温暖贴心\"]', 1, 1, '2024-03-06 00:00:00');
INSERT INTO `doctor` VALUES (19, '韩倩倩', '421081199204014300', '70AD20F195C741568C070CF8EF579622', '男', '/doctor/doctor-20.jpg', '1992-10-17', '华中科技大学', '本科', '15002789592', '北京市海淀区', '43281991@qq.com', '主治医师', '国家远程医疗医学中心主任委员', '擅长诊疗：熟练掌握胸外科专业各类疾病的诊断...', '2024-03-12', '[\"棒棒哒\",\"领域专家\",\"温暖贴心\",\"医术高超\"]', 1, 1, '2024-03-13 14:33:50');
INSERT INTO `doctor` VALUES (20, '赵六', '433081198204014211', '1F787A5B234049249B7DDC9D26E0ACA5', '女', NULL, '2024-12-04', '华中科技大学', '研究生', '15002781111', '北京市海淀区', '1811191@qq.com', '主任医师', '国家远程医疗医学中心主任委员', '很厉害', '2024-12-26', '[\"棒棒哒\",\"领域专家\",\"温暖贴心\"]', 1, 1, '2024-12-17 10:48:49');
INSERT INTO `doctor` VALUES (88, '测试二', '433081198204014211', 'A976E2363B614A0EB9A48E9C920A02A5', '女', NULL, '2024-12-17', '华中科技大学', '研究生', '15002781111', '北京市海淀区', '1811191@qq.com', '主任医师', '国家远程医疗医学中心主任委员', '很厉害', '2024-12-16', '[\"啊啊\"]', 1, 4, '2024-12-17 20:23:12');
INSERT INTO `doctor` VALUES (89, '测试三', '433081198204014211', '884DEC2A79F8461D8758968303CC74E0', '男', NULL, '2024-12-18', '华中科技大学', '博士', '15002781111', '北京市海淀区', '1811191@qq.com', '副主任医师', '国家远程医疗医学中心主任委员', '很厉害', '2024-12-18', '[\"呵呵\"]', 1, 4, '2024-12-17 20:24:00');
INSERT INTO `doctor` VALUES (90, '测试一', '433081198204014211', '813A1CFF54074301AFC334B4DE4A25BC', '女', NULL, '2006-12-13', '华中科技大学', '研究生', '15002781111', '北京市海淀区', '1811191@qq.com', '主任医师', '国家远程医疗医学中心主任委员', '很厉害', '2024-12-09', '[\"很厉害\",\"领域专家\",\"棒棒哒\"]', 1, 4, '2024-12-26 15:43:27');
INSERT INTO `doctor` VALUES (91, '测试三', '433081198204014211', '3947A69E181D40E78F46C1B3931EA86A', '女', NULL, '2019-12-24', '华中科技大学', '研究生', '15002781111', '北京市海淀区', '88881991@qq.com', '副主任医师', '国家远程医疗医学中心主任委员', '很厉害', '2024-12-29', '[\"温暖贴心\"]', 0, 4, '2024-12-26 17:45:06');

-- ----------------------------
-- Table: doctor_consultation_report（就诊报告表）
-- ----------------------------
DROP TABLE IF EXISTS `doctor_consultation_report`;
CREATE TABLE `doctor_consultation_report` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键',
  `uuid` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '唯一编号',
  `patient_card_id` int(11) DEFAULT NULL COMMENT '就诊卡ID',
  `diagnosis` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '诊断结果',
  `sub_dept_id` int(11) DEFAULT NULL COMMENT '诊室ID',
  `doctor_id` int(11) DEFAULT NULL COMMENT '医生ID',
  `registration_id` int(11) DEFAULT NULL COMMENT '门诊挂号单ID',
  `rp` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '药品处方',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 2 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

INSERT INTO `doctor_consultation_report` VALUES (1, '0FD7398377B0408A9A6DCA84C7D44770', 3, '急性牙髓炎', 2, 18, 1, '[{\"method\":\"1片/次；每日三次；口服\",\"num\":1,\"spec\":\"200mg×24片\",\"name\":\"甲硝唑片\"},{\"method\":\"1片/次；每日两次；口服\",\"num\":1,\"spec\":\"250mg×24片\",\"name\":\"头孢拉定胶囊\"}]');

-- ----------------------------
-- Table: doctor_price（医生挂号价格表）
-- ----------------------------
DROP TABLE IF EXISTS `doctor_price`;
CREATE TABLE `doctor_price` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `doctor_id` int(11) DEFAULT NULL,
  `level` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `price_1` decimal(10, 2) DEFAULT NULL COMMENT '门诊挂号费',
  `price_2` decimal(10, 2) DEFAULT NULL COMMENT '视频问诊挂号费',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 21 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

INSERT INTO `doctor_price` VALUES (1, 1, '主任医师', 30.00, 100.00);
INSERT INTO `doctor_price` VALUES (2, 2, '主任医师', 30.00, 100.00);
INSERT INTO `doctor_price` VALUES (3, 3, '主任医师', 30.00, 100.00);
INSERT INTO `doctor_price` VALUES (4, 4, '主任医师', 30.00, 100.00);
INSERT INTO `doctor_price` VALUES (5, 5, '主任医师', 30.00, 100.00);
INSERT INTO `doctor_price` VALUES (6, 6, '主任医师', 30.00, 100.00);
INSERT INTO `doctor_price` VALUES (7, 7, '主任医师', 30.00, 100.00);
INSERT INTO `doctor_price` VALUES (8, 8, '主任医师', 30.00, 100.00);
INSERT INTO `doctor_price` VALUES (9, 9, '主任医师', 30.00, 100.00);
INSERT INTO `doctor_price` VALUES (10, 10, '普通', 10.00, 100.00);
INSERT INTO `doctor_price` VALUES (11, 11, '副主任医师', 20.00, 100.00);
INSERT INTO `doctor_price` VALUES (12, 12, '副主任医师', 20.00, 80.00);
INSERT INTO `doctor_price` VALUES (13, 13, '普通', 10.00, 80.00);
INSERT INTO `doctor_price` VALUES (14, 14, '普通', 10.00, 80.00);
INSERT INTO `doctor_price` VALUES (15, 15, '普通', 10.00, 80.00);
INSERT INTO `doctor_price` VALUES (16, 16, '普通', 10.00, 80.00);
INSERT INTO `doctor_price` VALUES (17, 17, '普通', 10.00, 80.00);
INSERT INTO `doctor_price` VALUES (18, 18, '普通', 10.00, 80.00);
INSERT INTO `doctor_price` VALUES (19, 19, '主任医师', 30.00, 10.00);
INSERT INTO `doctor_price` VALUES (20, 20, '主任医师', 30.00, 100.00);

-- ----------------------------
-- Table: doctor_work_plan（医生出诊计划表）
-- ----------------------------
DROP TABLE IF EXISTS `doctor_work_plan`;
CREATE TABLE `doctor_work_plan` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键',
  `doctor_id` int(11) DEFAULT NULL COMMENT '医生ID',
  `dept_sub_id` int(11) DEFAULT NULL COMMENT '诊室ID',
  `date` date DEFAULT NULL COMMENT '出诊日期',
  `maximum` int(11) DEFAULT NULL COMMENT '该医生当天挂号人数上限',
  `num` int(11) DEFAULT 0 COMMENT '该医生当天实际挂号人数',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 190 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

INSERT INTO `doctor_work_plan` VALUES (1, 16, 2, '2024-07-02', 45, 5);
INSERT INTO `doctor_work_plan` VALUES (2, 17, 2, '2024-03-23', 45, 6);
INSERT INTO `doctor_work_plan` VALUES (3, 18, 2, '2024-03-23', 45, 1);
INSERT INTO `doctor_work_plan` VALUES (4, 16, 2, '2024-03-24', 45, 2);
INSERT INTO `doctor_work_plan` VALUES (5, 16, 2, '2023-03-25', 45, 3);
INSERT INTO `doctor_work_plan` VALUES (6, 16, 2, '2024-03-26', 45, 4);
INSERT INTO `doctor_work_plan` VALUES (7, 1, 18, '2024-03-23', 45, 7);
INSERT INTO `doctor_work_plan` VALUES (8, 2, 20, '2024-03-23', 45, 0);
INSERT INTO `doctor_work_plan` VALUES (9, 9, 20, '2024-03-23', 45, 0);
INSERT INTO `doctor_work_plan` VALUES (10, 9, 20, '2024-03-24', 45, 0);
INSERT INTO `doctor_work_plan` VALUES (11, 9, 20, '2024-03-25', 45, 0);
INSERT INTO `doctor_work_plan` VALUES (12, 8, 3, '2024-03-18', 45, 0);
INSERT INTO `doctor_work_plan` VALUES (14, 9, 4, '2024-03-19', 45, 0);
INSERT INTO `doctor_work_plan` VALUES (15, 10, 5, '2024-03-24', 45, 0);
INSERT INTO `doctor_work_plan` VALUES (16, 3, 6, '2024-03-24', 45, 0);
INSERT INTO `doctor_work_plan` VALUES (17, 4, 7, '2024-03-21', 57, 0);
INSERT INTO `doctor_work_plan` VALUES (18, 5, 8, '2024-03-22', 55, 0);
INSERT INTO `doctor_work_plan` VALUES (19, 6, 9, '2024-03-19', 50, 0);
INSERT INTO `doctor_work_plan` VALUES (20, 26, 8, '2024-03-28', 15, 0);
INSERT INTO `doctor_work_plan` VALUES (22, 26, 8, '2024-03-18', 15, 0);
INSERT INTO `doctor_work_plan` VALUES (23, 26, 8, '2024-03-19', 15, 0);
INSERT INTO `doctor_work_plan` VALUES (24, 26, 8, '2024-03-22', 21, 0);
INSERT INTO `doctor_work_plan` VALUES (25, 26, 8, '2024-03-23', 6, 0);
INSERT INTO `doctor_work_plan` VALUES (26, 26, 8, '2024-03-29', 15, 0);
INSERT INTO `doctor_work_plan` VALUES (27, 26, 8, '2024-03-24', 36, 0);
INSERT INTO `doctor_work_plan` VALUES (28, 7, 4, '2024-03-18', 24, 0);
INSERT INTO `doctor_work_plan` VALUES (29, 7, 4, '2024-03-22', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (30, 7, 4, '2024-03-29', 12, 0);
INSERT INTO `doctor_work_plan` VALUES (31, 7, 4, '2024-03-30', 12, 0);
INSERT INTO `doctor_work_plan` VALUES (32, 5, 4, '2024-03-29', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (33, 5, 4, '2024-03-30', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (34, 5, 4, '2024-03-31', 45, 0);
INSERT INTO `doctor_work_plan` VALUES (35, 20, 1, '2024-04-08', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (36, 36, 1, '2024-04-08', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (37, 7, 4, '2024-04-08', 6, 0);
INSERT INTO `doctor_work_plan` VALUES (38, 5, 4, '2024-04-08', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (39, 5, 4, '2024-04-09', 63, 0);
INSERT INTO `doctor_work_plan` VALUES (40, 7, 4, '2024-04-09', 24, 0);
INSERT INTO `doctor_work_plan` VALUES (41, 5, 4, '2024-04-10', 48, 0);
INSERT INTO `doctor_work_plan` VALUES (42, 7, 4, '2024-04-10', 42, 0);
INSERT INTO `doctor_work_plan` VALUES (43, 7, 4, '2024-04-11', 18, 0);
INSERT INTO `doctor_work_plan` VALUES (44, 5, 4, '2024-04-11', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (48, 20, 1, '2024-04-09', 6, 0);
INSERT INTO `doctor_work_plan` VALUES (49, 36, 1, '2024-04-10', 6, 0);
INSERT INTO `doctor_work_plan` VALUES (50, 36, 1, '2024-04-11', 15, 0);
INSERT INTO `doctor_work_plan` VALUES (52, 36, 1, '2024-04-13', 24, 0);
INSERT INTO `doctor_work_plan` VALUES (53, 18, 2, '2024-04-10', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (54, 20, 1, '2024-04-10', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (55, 3, 9, '2024-04-10', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (56, 5, 26, '2024-04-10', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (57, 3, 9, '2024-04-11', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (58, 3, 9, '2024-04-12', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (59, 43, 2, '2024-04-11', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (60, 35, 2, '2024-04-11', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (61, 7, 4, '2024-04-15', 27, 0);
INSERT INTO `doctor_work_plan` VALUES (62, 20, 1, '2024-04-11', 3, 0);
INSERT INTO `doctor_work_plan` VALUES (63, 20, 1, '2024-04-12', 6, 0);
INSERT INTO `doctor_work_plan` VALUES (64, 20, 1, '2024-04-01', 3, 0);
INSERT INTO `doctor_work_plan` VALUES (65, 20, 1, '2024-04-13', 25, 0);
INSERT INTO `doctor_work_plan` VALUES (66, 20, 1, '2024-04-14', 12, 0);
INSERT INTO `doctor_work_plan` VALUES (67, 20, 1, '2024-04-02', 3, 0);
INSERT INTO `doctor_work_plan` VALUES (74, 1, 2, '2024-04-12', 8, 0);
INSERT INTO `doctor_work_plan` VALUES (78, 20, 1, '2024-04-24', 14, 0);
INSERT INTO `doctor_work_plan` VALUES (79, 7, 4, '2024-04-24', 12, 0);
INSERT INTO `doctor_work_plan` VALUES (80, 36, 1, '2024-04-25', 6, 0);
INSERT INTO `doctor_work_plan` VALUES (81, 20, 1, '2024-04-25', 6, 0);
INSERT INTO `doctor_work_plan` VALUES (82, 36, 1, '2024-04-24', 6, 0);
INSERT INTO `doctor_work_plan` VALUES (83, 20, 1, '2024-04-26', 12, 0);
INSERT INTO `doctor_work_plan` VALUES (84, 36, 1, '2024-04-26', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (85, 20, 1, '2024-04-27', 15, 0);
INSERT INTO `doctor_work_plan` VALUES (87, 20, 1, '2024-05-06', 18, 0);
INSERT INTO `doctor_work_plan` VALUES (88, 36, 1, '2024-05-06', 18, 0);
INSERT INTO `doctor_work_plan` VALUES (89, 20, 1, '2024-05-07', 18, 0);
INSERT INTO `doctor_work_plan` VALUES (90, 36, 1, '2024-05-07', 12, 0);
INSERT INTO `doctor_work_plan` VALUES (91, 20, 1, '2024-05-08', 10, 0);
INSERT INTO `doctor_work_plan` VALUES (92, 36, 1, '2024-05-08', 6, 0);
INSERT INTO `doctor_work_plan` VALUES (93, 20, 1, '2024-05-09', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (94, 36, 1, '2024-05-09', 6, 0);
INSERT INTO `doctor_work_plan` VALUES (95, 20, 1, '2024-05-10', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (96, 36, 1, '2024-05-10', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (97, 20, 1, '2024-05-11', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (98, 36, 1, '2024-05-11', 10, 0);
INSERT INTO `doctor_work_plan` VALUES (99, 20, 1, '2024-05-12', 12, 0);
INSERT INTO `doctor_work_plan` VALUES (100, 20, 1, '2024-06-15', 45, 0);
INSERT INTO `doctor_work_plan` VALUES (101, 18, 2, '2024-06-15', 45, 0);
INSERT INTO `doctor_work_plan` VALUES (102, 36, 1, '2024-06-18', 45, 0);
INSERT INTO `doctor_work_plan` VALUES (103, 44, 1, '2024-06-18', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (104, 64, 3, '2024-06-18', 90, 0);
INSERT INTO `doctor_work_plan` VALUES (105, 36, 1, '2024-09-21', 16, 0);
INSERT INTO `doctor_work_plan` VALUES (106, 1, 2, '2024-09-21', 18, 0);
INSERT INTO `doctor_work_plan` VALUES (107, 36, 1, '2024-09-23', 30, 0);
INSERT INTO `doctor_work_plan` VALUES (108, 1, 2, '2025-01-13', 4, 0);
INSERT INTO `doctor_work_plan` VALUES (109, 20, 1, '2025-01-14', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (110, 20, 1, '2025-01-15', 6, 0);
INSERT INTO `doctor_work_plan` VALUES (111, 1, 2, '2025-01-15', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (112, 88, 1, '2025-01-14', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (113, 88, 1, '2025-01-15', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (114, 20, 1, '2025-01-16', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (115, 20, 1, '2025-01-18', 12, 0);
INSERT INTO `doctor_work_plan` VALUES (117, 20, 1, '2025-02-12', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (118, 1, 2, '2025-02-11', 12, 0);
INSERT INTO `doctor_work_plan` VALUES (119, 20, 1, '2025-02-13', 18, 0);
INSERT INTO `doctor_work_plan` VALUES (120, 20, 1, '2025-02-11', 6, 0);
INSERT INTO `doctor_work_plan` VALUES (121, 20, 1, '2025-02-14', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (122, 20, 1, '2025-02-15', 6, 0);
INSERT INTO `doctor_work_plan` VALUES (123, 88, 1, '2025-02-12', 6, 0);
INSERT INTO `doctor_work_plan` VALUES (124, 1, 2, '2025-02-13', 6, 0);
INSERT INTO `doctor_work_plan` VALUES (125, 6, 26, '2025-02-13', 6, 0);
INSERT INTO `doctor_work_plan` VALUES (126, 88, 1, '2025-02-13', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (127, 88, 1, '2025-02-14', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (128, 88, 1, '2025-02-15', 6, 0);
INSERT INTO `doctor_work_plan` VALUES (129, 20, 1, '2025-02-18', 18, 0);
INSERT INTO `doctor_work_plan` VALUES (130, 88, 1, '2025-02-18', 18, 0);
INSERT INTO `doctor_work_plan` VALUES (131, 20, 1, '2025-02-19', 18, 0);
INSERT INTO `doctor_work_plan` VALUES (135, 20, 1, '2025-02-20', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (136, 88, 1, '2025-02-20', 6, 0);
INSERT INTO `doctor_work_plan` VALUES (137, 20, 1, '2025-02-21', 12, 0);
INSERT INTO `doctor_work_plan` VALUES (141, 20, 1, '2025-02-22', 6, 0);
INSERT INTO `doctor_work_plan` VALUES (142, 88, 1, '2025-02-22', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (143, 20, 1, '2025-02-23', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (144, 88, 1, '2025-02-23', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (145, 9, 1, '2025-02-22', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (146, 9, 1, '2025-02-23', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (147, 9, 1, '2025-02-24', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (148, 20, 1, '2025-02-24', 6, 0);
INSERT INTO `doctor_work_plan` VALUES (149, 88, 1, '2025-02-24', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (150, 19, 1, '2025-02-26', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (151, 20, 1, '2025-02-26', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (152, 19, 1, '2025-02-27', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (153, 20, 1, '2025-02-27', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (154, 19, 1, '2025-02-28', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (155, 20, 1, '2025-02-28', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (156, 19, 1, '2025-03-01', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (157, 20, 1, '2025-03-01', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (158, 19, 1, '2025-03-02', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (159, 20, 1, '2025-03-02', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (160, 19, 1, '2025-03-14', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (161, 20, 1, '2025-03-13', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (162, 20, 1, '2025-03-14', 9, 3);
INSERT INTO `doctor_work_plan` VALUES (163, 19, 1, '2025-03-15', 9, 2);
INSERT INTO `doctor_work_plan` VALUES (164, 20, 1, '2025-03-15', 9, 1);
INSERT INTO `doctor_work_plan` VALUES (165, 19, 1, '2025-03-24', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (169, 19, 1, '2025-03-25', 6, 1);
INSERT INTO `doctor_work_plan` VALUES (170, 19, 1, '2025-03-26', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (171, 20, 1, '2025-03-25', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (172, 20, 1, '2025-03-26', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (173, 19, 1, '2025-04-01', 9, 1);
INSERT INTO `doctor_work_plan` VALUES (174, 20, 1, '2025-04-01', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (175, 19, 1, '2025-04-02', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (176, 20, 1, '2025-04-02', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (177, 19, 1, '2025-04-06', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (178, 20, 1, '2025-04-06', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (181, 19, 1, '2025-04-07', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (182, 20, 1, '2025-04-07', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (183, 19, 1, '2025-04-08', 9, 1);
INSERT INTO `doctor_work_plan` VALUES (184, 20, 1, '2025-04-08', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (185, 19, 1, '2025-04-09', 12, 0);
INSERT INTO `doctor_work_plan` VALUES (186, 20, 1, '2025-04-09', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (187, 19, 1, '2025-04-10', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (188, 20, 1, '2025-04-10', 9, 0);
INSERT INTO `doctor_work_plan` VALUES (189, 7, 4, '2025-04-11', 45, 0);

-- ----------------------------
-- Table: doctor_work_plan_schedule（医生出诊排班明细表）
-- ----------------------------
DROP TABLE IF EXISTS `doctor_work_plan_schedule`;
CREATE TABLE `doctor_work_plan_schedule` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `work_plan_id` int(11) DEFAULT NULL COMMENT '关联work_plan_id',
  `slot` tinyint(4) DEFAULT NULL COMMENT '时间段，比如1对应08:00~08:30时间段',
  `maximum` int(11) DEFAULT NULL COMMENT '该时段挂号人数上限',
  `num` int(11) DEFAULT 0 COMMENT '该时段实际挂号人数',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 814 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

INSERT INTO `doctor_work_plan_schedule` VALUES (1, 1, 2, 3, 0),(2, 1, 2, 3, 0),(3, 1, 3, 3, 0),(4, 1, 4, 3, 0),(5, 1, 5, 3, 0),(6, 1, 6, 3, 0),(7, 1, 7, 3, 0),(8, 1, 8, 3, 0),(9, 1, 9, 3, 0),(10, 1, 10, 3, 0),(11, 1, 11, 3, 0),(12, 1, 12, 3, 0),(13, 1, 13, 3, 0),(14, 1, 14, 3, 0),(15, 1, 15, 3, 0),(16, 2, 1, 3, 0),(17, 2, 2, 3, 0),(18, 2, 4, 3, 0),(19, 2, 8, 3, 0),(20, 5, 1, 3, 0),(21, 6, 1, 3, 0),(22, 3, 8, 3, 0),(23, 3, 1, 3, 0),(24, 23, 1, 5, 0),(25, 23, 2, 5, 0),(26, 23, 3, 5, 0),(27, 24, 1, 7, 0),(28, 24, 2, 7, 0),(29, 24, 3, 7, 0),(30, 25, 1, 3, 0),(31, 25, 2, 3, 0),(32, 26, 1, 5, 0),(33, 26, 2, 5, 0),(34, 26, 3, 5, 0),(35, 27, 4, 6, 0),(36, 27, 5, 6, 0),(37, 27, 2, 6, 0),(38, 27, 1, 6, 0),(39, 27, 3, 6, 0),(40, 27, 6, 6, 0),(41, 28, 1, 4, 0),(42, 28, 2, 4, 0),(43, 28, 5, 4, 0),(44, 28, 4, 4, 0),(45, 28, 3, 4, 0),(46, 28, 6, 4, 0),(47, 29, 1, 3, 0),(48, 29, 2, 3, 0),(49, 29, 3, 3, 0),(50, 30, 12, 3, 0),(51, 30, 13, 3, 0),(52, 30, 14, 3, 0),(53, 30, 15, 3, 0),(54, 31, 1, 4, 0),(55, 31, 2, 4, 0),(56, 31, 3, 4, 0),(57, 32, 13, 3, 0),(58, 32, 14, 3, 0),(59, 32, 15, 3, 0),(60, 33, 1, 3, 0),(61, 33, 2, 3, 0),(62, 33, 3, 3, 0),(63, 34, 1, 3, 0),(64, 34, 2, 3, 0),(65, 34, 3, 3, 0),(66, 34, 4, 3, 0),(67, 34, 5, 3, 0),(68, 34, 6, 3, 0),(69, 34, 7, 3, 0),(70, 34, 8, 3, 0),(71, 34, 9, 3, 0),(72, 34, 10, 3, 0),(73, 34, 11, 3, 0),(74, 34, 12, 3, 0),(75, 34, 13, 3, 0),(76, 34, 14, 3, 0),(77, 34, 15, 3, 0),(78, 35, 1, 3, 0),(79, 35, 2, 3, 0),(80, 35, 3, 3, 0),(81, 36, 1, 3, 0),(82, 36, 2, 3, 0),(83, 36, 3, 3, 0),(84, 37, 7, 3, 0),(85, 37, 10, 3, 0),(86, 38, 1, 3, 0),(87, 38, 2, 3, 0),(88, 38, 3, 3, 0),(89, 39, 1, 7, 0),(90, 39, 2, 7, 0),(91, 39, 3, 7, 0),(92, 39, 4, 7, 0),(93, 39, 5, 7, 0),(94, 39, 6, 7, 0),(95, 39, 7, 7, 0),(96, 39, 8, 7, 0),(97, 39, 9, 7, 0),(98, 40, 1, 4, 0),(99, 40, 2, 4, 0),(100, 40, 3, 4, 0),(101, 40, 4, 4, 0),(102, 40, 5, 4, 0),(103, 40, 6, 4, 0),(104, 41, 1, 6, 0),(105, 41, 2, 6, 0),(106, 41, 3, 6, 0),(107, 41, 4, 6, 0),(108, 41, 5, 6, 0),(109, 41, 6, 6, 0),(110, 41, 8, 6, 0),(111, 41, 7, 6, 0),(112, 42, 9, 6, 0),(113, 42, 10, 6, 0),(114, 42, 11, 6, 0),(115, 42, 12, 6, 0),(116, 42, 13, 6, 0),(117, 42, 14, 6, 0),(118, 42, 15, 6, 0),(119, 43, 1, 3, 0),(120, 43, 2, 3, 0),(121, 43, 3, 3, 0),(122, 43, 4, 3, 0),(123, 43, 5, 3, 0),(124, 43, 6, 3, 0),(125, 44, 1, 3, 0),(126, 44, 2, 3, 0),(127, 44, 3, 3, 0),(142, 48, 1, 3, 0),(143, 48, 4, 3, 0),(144, 49, 1, 3, 0),(145, 49, 4, 3, 0),(146, 50, 8, 5, 0),(147, 50, 14, 5, 0),(148, 50, 11, 5, 0),(152, 52, 8, 6, 0),(153, 52, 12, 6, 0),(154, 52, 15, 6, 0),(155, 52, 14, 6, 0),(156, 53, 1, 3, 0),(157, 53, 2, 3, 0),(158, 53, 3, 3, 0),(159, 54, 1, 3, 0),(162, 55, 1, 3, 0),(163, 55, 2, 3, 0),(164, 55, 3, 3, 0),(165, 56, 1, 3, 0),(166, 56, 2, 3, 0),(167, 56, 3, 3, 0),(168, 57, 1, 3, 0),(169, 57, 2, 3, 0),(170, 57, 3, 3, 0),(171, 58, 1, 3, 0),(172, 58, 2, 3, 0),(173, 58, 3, 3, 0),(174, 59, 1, 3, 0),(175, 59, 2, 3, 0),(176, 59, 3, 3, 0),(177, 60, 1, 3, 0),(178, 60, 2, 3, 0),(179, 60, 3, 3, 0),(183, 62, 9, 3, 0),(184, 63, 1, 3, 0),(185, 63, 7, 3, 0),(186, 64, 12, 3, 0),(187, 65, 2, 5, 0),(188, 65, 5, 5, 0),(189, 65, 8, 5, 0),(190, 65, 11, 5, 0),(191, 65, 1, 5, 0),(192, 66, 1, 4, 0),(193, 66, 2, 4, 0),(194, 66, 3, 4, 0),(205, 67, 4, 3, 0),(209, 54, 3, 18, 0),(213, 54, 3, 9, 0),(219, 54, 2, 9, 0),(220, 61, 1, 27, 0),(221, 61, 2, 27, 0),(222, 61, 3, 27, 0),(295, 74, 1, 4, 0),(296, 74, 2, 4, 0),(318, 79, 1, 2, 0),(319, 79, 2, 2, 0),(320, 79, 3, 2, 0),(321, 79, 4, 2, 0),(322, 79, 5, 2, 0),(323, 79, 6, 2, 0),(324, 80, 1, 2, 0),(325, 80, 2, 2, 0),(326, 80, 3, 2, 0),(327, 81, 7, 2, 0),(328, 81, 8, 2, 0),(329, 81, 9, 2, 0),(330, 82, 10, 2, 0),(331, 82, 11, 2, 0),(332, 82, 12, 2, 0),(336, 84, 7, 3, 0),(337, 84, 8, 3, 0),(338, 84, 9, 3, 0),(344, 85, 1, 3, 0),(345, 85, 2, 3, 0),(346, 85, 3, 3, 0),(347, 85, 4, 3, 0),(348, 85, 5, 3, 0),(361, 87, 1, 3, 0),(362, 87, 2, 3, 0),(363, 87, 3, 3, 0),(364, 87, 4, 3, 0),(365, 87, 5, 3, 0),(366, 87, 6, 3, 0),(367, 88, 1, 3, 0),(368, 88, 2, 3, 0),(369, 88, 3, 3, 0),(370, 88, 4, 3, 0),(371, 88, 5, 3, 0),(372, 88, 6, 3, 0),(373, 89, 1, 3, 0),(374, 89, 2, 3, 0),(375, 89, 3, 3, 0),(376, 89, 4, 3, 0),(377, 89, 5, 3, 0),(378, 89, 6, 3, 0),(379, 90, 1, 2, 0),(380, 90, 2, 2, 0),(381, 90, 3, 2, 0),(382, 90, 4, 2, 0),(383, 90, 5, 2, 0),(384, 90, 6, 2, 0),(385, 91, 1, 2, 0),(386, 91, 2, 2, 0),(387, 91, 3, 2, 0),(388, 91, 4, 2, 0),(389, 91, 5, 2, 0),(390, 92, 1, 2, 0),(391, 92, 2, 2, 0),(392, 92, 3, 2, 0),(393, 93, 1, 3, 0),(394, 93, 2, 3, 0),(395, 93, 3, 3, 0),(396, 94, 15, 3, 0),(397, 94, 11, 6, 0),(398, 95, 1, 3, 0),(399, 95, 2, 3, 0),(400, 95, 3, 3, 0),(401, 96, 7, 3, 0),(402, 96, 8, 3, 0),(403, 96, 9, 3, 0),(404, 97, 1, 3, 0),(405, 97, 2, 3, 0),(406, 97, 3, 3, 0),(407, 98, 11, 2, 0),(408, 98, 12, 2, 0),(409, 98, 13, 2, 0),(410, 98, 14, 2, 0),(411, 98, 15, 2, 0),(412, 99, 1, 2, 0),(413, 99, 2, 2, 0),(414, 99, 3, 2, 0),(415, 99, 4, 2, 0),(416, 99, 5, 2, 0),(417, 99, 6, 2, 0),(418, 100, 1, 3, 0),(419, 100, 2, 3, 0),(420, 100, 3, 3, 0),(421, 100, 4, 3, 0),(422, 100, 5, 3, 0),(423, 100, 6, 3, 0),(424, 100, 7, 3, 0),(425, 100, 8, 3, 0),(426, 100, 9, 3, 0),(427, 100, 10, 3, 0),(428, 100, 11, 3, 0),(429, 100, 12, 3, 0),(430, 100, 13, 3, 0),(431, 100, 14, 3, 0),(432, 100, 15, 3, 0),(433, 101, 1, 3, 0),(434, 101, 2, 3, 0),(435, 101, 3, 3, 0),(436, 101, 4, 3, 0),(437, 101, 5, 3, 0),(438, 101, 6, 3, 0),(439, 101, 7, 3, 0),(440, 101, 8, 3, 0),(441, 101, 9, 3, 0),(442, 101, 10, 3, 0),(443, 101, 11, 3, 0),(444, 101, 12, 3, 0),(445, 101, 13, 3, 0),(446, 101, 14, 3, 0),(447, 101, 15, 3, 0),(448, 102, 1, 3, 0),(449, 102, 2, 3, 0),(450, 102, 3, 3, 0),(451, 102, 4, 3, 0),(452, 102, 5, 3, 0),(453, 102, 6, 3, 0),(454, 102, 7, 3, 0),(455, 102, 8, 3, 0),(456, 102, 9, 3, 0),(457, 102, 10, 3, 0),(458, 102, 11, 3, 0),(459, 102, 12, 3, 0),(460, 102, 13, 3, 0),(461, 102, 14, 3, 0),(462, 102, 15, 3, 0),(463, 103, 1, 3, 0),(466, 103, 4, 3, 0),(474, 103, 12, 3, 0),(478, 104, 1, 6, 0),(479, 104, 2, 6, 0),(480, 104, 3, 6, 0),(481, 104, 4, 6, 0),(482, 104, 5, 6, 0),(483, 104, 6, 6, 0),(484, 104, 7, 6, 0),(485, 104, 8, 6, 0),(486, 104, 9, 6, 0),(487, 104, 10, 6, 0),(488, 104, 11, 6, 0),(489, 104, 12, 6, 0),(490, 104, 13, 6, 0),(491, 104, 14, 6, 0),(492, 104, 15, 6, 0),(493, 105, 1, 8, 0),(494, 105, 3, 8, 0),(495, 106, 1, 6, 0),(496, 106, 2, 6, 0),(497, 106, 3, 6, 0),(498, 107, 1, 10, 0),(499, 107, 2, 10, 0),(500, 107, 3, 10, 0),(501, 108, 1, 2, 0),(502, 108, 2, 2, 0),(503, 109, 1, 3, 0),(504, 109, 2, 3, 0),(505, 109, 3, 3, 0),(506, 110, 1, 2, 0),(507, 110, 2, 2, 0),(508, 110, 3, 2, 0),(509, 111, 1, 3, 0),(510, 111, 2, 3, 0),(511, 111, 3, 3, 0),(512, 112, 10, 3, 0),(513, 112, 11, 3, 0),(514, 112, 12, 3, 0),(515, 113, 1, 3, 0),(516, 113, 2, 3, 0),(517, 113, 3, 3, 0),(518, 114, 1, 3, 0),(519, 114, 2, 3, 0),(520, 114, 3, 3, 0),(521, 115, 1, 2, 0),(522, 115, 2, 2, 0),(523, 115, 3, 2, 0),(524, 115, 4, 2, 0),(525, 115, 5, 2, 0),(526, 115, 6, 2, 0),(530, 117, 1, 3, 0),(531, 117, 2, 3, 0),(532, 117, 3, 3, 0),(533, 118, 1, 2, 0),(534, 118, 2, 2, 0),(535, 118, 3, 2, 0),(536, 118, 4, 2, 0),(537, 118, 5, 2, 0),(538, 118, 6, 2, 0),(539, 119, 1, 2, 0),(540, 119, 5, 2, 0),(541, 119, 2, 2, 0),(542, 119, 3, 2, 0),(543, 119, 6, 2, 0),(544, 119, 4, 2, 0),(545, 119, 7, 2, 0),(546, 119, 8, 2, 0),(547, 119, 9, 2, 0),(548, 120, 2, 2, 0),(549, 120, 1, 2, 0),(550, 120, 3, 2, 0),(551, 121, 1, 3, 0),(552, 121, 2, 3, 0),(553, 121, 3, 3, 0),(554, 122, 2, 2, 0),(555, 122, 1, 2, 0),(556, 122, 3, 2, 0),(557, 123, 1, 2, 0),(558, 123, 2, 2, 0),(559, 123, 3, 2, 0),(560, 124, 1, 2, 0),(561, 124, 2, 2, 0),(562, 124, 3, 2, 0),(563, 125, 1, 2, 0),(564, 125, 2, 2, 0),(565, 125, 3, 2, 0),(566, 126, 1, 3, 0),(567, 126, 2, 3, 0),(568, 126, 3, 3, 0),(569, 127, 1, 3, 0),(570, 127, 2, 3, 0),(571, 127, 3, 3, 0),(572, 128, 1, 2, 0),(573, 128, 2, 2, 0),(574, 128, 3, 2, 0),(575, 129, 1, 3, 0),(576, 129, 2, 3, 0),(577, 129, 3, 3, 0),(581, 131, 4, 3, 0),(595, 130, 4, 3, 0),(596, 130, 5, 3, 0),(597, 130, 6, 3, 0),(598, 130, 7, 3, 0),(599, 130, 8, 3, 0),(600, 130, 9, 3, 0),(607, 129, 4, 3, 0),(608, 129, 5, 3, 0),(609, 129, 6, 3, 0),(610, 131, 1, 3, 0),(611, 131, 2, 3, 0),(612, 131, 3, 3, 0),(613, 131, 5, 3, 0),(614, 131, 6, 3, 0),(624, 135, 1, 3, 0),(625, 135, 2, 3, 0),(626, 135, 3, 3, 0),(627, 136, 1, 2, 0),(628, 136, 2, 2, 0),(629, 136, 3, 2, 0),(633, 137, 10, 2, 0),(634, 137, 11, 2, 0),(635, 137, 12, 2, 0),(639, 137, 7, 2, 0),(640, 137, 8, 2, 0),(641, 137, 9, 2, 0),(654, 141, 1, 2, 0),(655, 141, 2, 2, 0),(656, 141, 3, 2, 0),(657, 142, 1, 3, 0),(658, 142, 2, 3, 0),(659, 142, 3, 3, 0),(660, 143, 1, 3, 0),(661, 143, 2, 3, 0),(662, 143, 3, 3, 0),(663, 144, 1, 3, 0),(664, 144, 2, 3, 0),(665, 144, 3, 3, 0),(666, 145, 1, 3, 0),(667, 145, 2, 3, 0),(668, 145, 3, 3, 0),(669, 146, 4, 3, 0),(670, 146, 5, 3, 0),(671, 146, 6, 3, 0),(672, 147, 1, 3, 0),(673, 147, 2, 3, 0),(674, 147, 3, 3, 0),(675, 148, 1, 2, 0),(676, 148, 2, 2, 0),(677, 148, 3, 2, 0),(678, 149, 1, 3, 0),(679, 149, 2, 3, 0),(680, 149, 3, 3, 0),(681, 150, 2, 3, 0),(682, 150, 1, 3, 0),(683, 150, 3, 3, 0),(684, 151, 1, 3, 0),(685, 151, 2, 3, 0),(686, 151, 3, 3, 0),(687, 152, 1, 3, 0),(688, 152, 2, 3, 0),(689, 152, 3, 3, 0),(690, 153, 1, 3, 0),(691, 153, 2, 3, 0),(692, 153, 3, 3, 0),(693, 154, 1, 3, 0),(694, 154, 2, 3, 0),(695, 154, 3, 3, 0),(696, 155, 1, 3, 0),(697, 155, 2, 3, 0),(698, 155, 3, 3, 0),(699, 156, 1, 3, 0),(700, 156, 2, 3, 0),(701, 156, 3, 3, 0),(702, 157, 1, 3, 0),(703, 157, 2, 3, 0),(704, 157, 3, 3, 0),(705, 158, 1, 3, 0),(706, 158, 2, 3, 0),(707, 158, 3, 3, 0),(708, 159, 1, 3, 0),(709, 159, 2, 3, 0),(710, 159, 3, 3, 0),(711, 160, 1, 3, 0),(712, 160, 2, 3, 0),(713, 160, 3, 3, 0),(714, 161, 1, 3, 0),(715, 161, 2, 3, 0),(716, 161, 3, 3, 0),(717, 162, 2, 3, 2),(718, 162, 3, 3, 1),(719, 162, 1, 3, 0),(720, 163, 1, 3, 2),(721, 163, 2, 3, 0),(722, 163, 3, 3, 0),(723, 164, 1, 3, 0),(724, 164, 2, 3, 0),(725, 164, 3, 3, 1),(726, 165, 1, 3, 0),(727, 165, 2, 3, 0),(728, 165, 3, 3, 0),(738, 169, 1, 2, 1),(739, 169, 2, 2, 0),(740, 169, 3, 2, 0),(741, 170, 1, 3, 0),(742, 170, 2, 3, 0),(743, 170, 3, 3, 0),(744, 171, 1, 3, 0),(745, 171, 2, 3, 0),(746, 171, 3, 3, 0),(747, 172, 1, 3, 0),(748, 172, 2, 3, 0),(749, 172, 3, 3, 0),(750, 173, 1, 3, 1),(751, 173, 2, 3, 0),(752, 173, 3, 3, 0),(753, 174, 1, 3, 0),(754, 174, 2, 3, 0),(755, 174, 3, 3, 0),(756, 175, 1, 3, 0),(757, 175, 2, 3, 0),(758, 175, 3, 3, 0),(759, 176, 1, 3, 0),(760, 176, 2, 3, 0),(761, 176, 3, 3, 0),(762, 177, 1, 3, 0),(763, 177, 2, 3, 0),(764, 177, 3, 3, 0),(765, 178, 1, 3, 0),(766, 178, 2, 3, 0),(767, 178, 3, 3, 0),(774, 181, 1, 3, 0),(775, 181, 2, 3, 0),(776, 181, 3, 3, 0),(777, 182, 1, 3, 0),(778, 182, 2, 3, 0),(779, 182, 3, 3, 0),(780, 183, 1, 3, 1),(781, 183, 2, 3, 0),(782, 183, 3, 3, 0),(783, 184, 1, 3, 0),(784, 184, 2, 3, 0),(785, 184, 3, 3, 0),(786, 185, 1, 3, 0),(787, 185, 2, 3, 0),(788, 185, 3, 3, 0),(789, 186, 1, 3, 0),(790, 186, 2, 3, 0),(791, 186, 3, 3, 0),(792, 185, 4, 3, 0),(793, 187, 2, 3, 0),(794, 187, 1, 3, 0),(795, 187, 3, 3, 0),(796, 188, 1, 3, 0),(797, 188, 2, 3, 0),(798, 188, 3, 3, 0),(799, 189, 1, 3, 0),(800, 189, 2, 3, 0),(801, 189, 3, 3, 0),(802, 189, 4, 3, 0),(803, 189, 5, 3, 0),(804, 189, 6, 3, 0),(805, 189, 7, 3, 0),(806, 189, 8, 3, 0),(807, 189, 9, 3, 0),(808, 189, 10, 3, 0),(809, 189, 11, 3, 0),(810, 189, 12, 3, 0),(811, 189, 13, 3, 0),(812, 189, 14, 3, 0),(813, 189, 15, 3, 0);

-- ----------------------------
-- Table: medical_dept（医学科室表）
-- ----------------------------
DROP TABLE IF EXISTS `medical_dept`;
CREATE TABLE `medical_dept` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL COMMENT '科室名称',
  `outpatient` tinyint(1) DEFAULT NULL COMMENT '是否为门诊',
  `description` varchar(500) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL COMMENT '详细注释',
  `recommended` tinyint(1) DEFAULT NULL COMMENT '是否为优秀科室',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 13 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

INSERT INTO `medical_dept` VALUES (1, '口腔科', 1, '目前已经成为在国内外具有一定影响力的大型医疗科室...', 0);
INSERT INTO `medical_dept` VALUES (2, '眼科', 1, '全科共有医护人员及技师共67人...', 1);
INSERT INTO `medical_dept` VALUES (3, '耳鼻喉科', 1, '科室设有耳科、鼻科、咽喉头颈外科3个专业组...', 1);
INSERT INTO `medical_dept` VALUES (4, '内科', 1, '目前已经成为在国内外具有一定影响力的大型医疗科室...', 1);
INSERT INTO `medical_dept` VALUES (5, '外科', 1, '科室现有医生52名，教授8人，副教授9人...', 1);
INSERT INTO `medical_dept` VALUES (6, '皮肤科', 1, '皮肤科成立于1977年...', 1);
INSERT INTO `medical_dept` VALUES (7, '妇科', 1, '妇科现有职工89人...', 1);
INSERT INTO `medical_dept` VALUES (8, '儿科', 1, '目前共有医护人员49名...', 1);
INSERT INTO `medical_dept` VALUES (9, '神经科', 1, '科室拥有一支专业的神经科诊断技术团队...', 1);
INSERT INTO `medical_dept` VALUES (10, '肿瘤科', 1, '肿瘤内科建科于1964年...', 1);
INSERT INTO `medical_dept` VALUES (11, '产科', 0, '产科现有专业医护人员50余名...', 0);
INSERT INTO `medical_dept` VALUES (12, '骨科', 0, '科室设置规范、布局合理...', 0);

-- ----------------------------
-- Table: medical_dept_sub（医学子科室/诊室表）
-- ----------------------------
DROP TABLE IF EXISTS `medical_dept_sub`;
CREATE TABLE `medical_dept_sub` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(20) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `dept_id` int(11) NOT NULL,
  `location` varchar(20) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 29 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

INSERT INTO `medical_dept_sub` VALUES (1, '口腔颌面外科', 1, '1号楼5层A区111');
INSERT INTO `medical_dept_sub` VALUES (2, '口腔颌面内科', 1, '1号楼2层B区');
INSERT INTO `medical_dept_sub` VALUES (3, '眼科门诊', 2, '1号楼3层A区');
INSERT INTO `medical_dept_sub` VALUES (4, '白内障诊疗中心', 2, '1号楼3层B区');
INSERT INTO `medical_dept_sub` VALUES (5, '屈光中心门诊', 2, '1号楼3层C区');
INSERT INTO `medical_dept_sub` VALUES (6, '眼激光门诊', 2, '1号楼3层D区');
INSERT INTO `medical_dept_sub` VALUES (7, '耳鼻喉门诊', 3, '1号楼3层E区');
INSERT INTO `medical_dept_sub` VALUES (8, '内分泌门诊', 4, '1号楼4层A区');
INSERT INTO `medical_dept_sub` VALUES (9, '呼吸内科门诊', 4, '1号楼4层B区');
INSERT INTO `medical_dept_sub` VALUES (10, '心血管门诊', 4, '1号楼4层C区');
INSERT INTO `medical_dept_sub` VALUES (11, '消化内科门诊', 4, '1号楼4层D区');
INSERT INTO `medical_dept_sub` VALUES (12, '糖尿病门诊', 4, '1号楼5层A区');
INSERT INTO `medical_dept_sub` VALUES (13, '肾内科门诊', 4, '1号楼5层B区');
INSERT INTO `medical_dept_sub` VALUES (14, '风湿免疫门诊', 4, '1号楼5层C区');
INSERT INTO `medical_dept_sub` VALUES (15, '普通外科门诊', 5, '1号楼5层D区');
INSERT INTO `medical_dept_sub` VALUES (16, '胸外科门诊', 5, '1号楼5层E区');
INSERT INTO `medical_dept_sub` VALUES (17, '泌尿外科门诊', 5, '1号楼6层A区');
INSERT INTO `medical_dept_sub` VALUES (18, '心脏外科门诊', 5, '1号楼5层B区');
INSERT INTO `medical_dept_sub` VALUES (19, '整形外科门诊', 5, '1号楼5层C区');
INSERT INTO `medical_dept_sub` VALUES (20, '皮肤病门诊', 6, '1号楼5层D区');
INSERT INTO `medical_dept_sub` VALUES (21, '妇科门诊', 7, '1号楼6层A区');
INSERT INTO `medical_dept_sub` VALUES (22, '不孕病门诊', 7, '1号楼6层B区');
INSERT INTO `medical_dept_sub` VALUES (23, '儿科门诊', 8, '1号楼6层C区');
INSERT INTO `medical_dept_sub` VALUES (24, '神经内科门诊', 9, '1号楼7层A区');
INSERT INTO `medical_dept_sub` VALUES (25, '神经外科门诊', 9, '1号楼7层B区');
INSERT INTO `medical_dept_sub` VALUES (26, '肿瘤科门诊', 10, '2号楼2层A区');
INSERT INTO `medical_dept_sub` VALUES (27, '产科门诊', 11, '2号楼3层A区');
INSERT INTO `medical_dept_sub` VALUES (28, '骨科门诊', 12, '2号楼4层A区');

-- ----------------------------
-- Table: medical_dept_sub_doctor（科室-医生关联表）
-- ----------------------------
DROP TABLE IF EXISTS `medical_dept_sub_doctor`;
CREATE TABLE `medical_dept_sub_doctor` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `dept_sub_id` int(11) NOT NULL,
  `doctor_id` int(11) NOT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 32 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

INSERT INTO `medical_dept_sub_doctor` VALUES (1, 2, 1),(2, 20, 2),(3, 9, 3),(4, 19, 4),(6, 26, 6),(7, 4, 7),(8, 1, 19),(9, 1, 20),(11, 14, 11),(12, 14, 12),(13, 14, 13),(14, 13, 14),(15, 26, 15),(18, 2, 18),(25, 9, 27),(26, 23, 28),(27, 21, 29),(28, 20, 30),(29, 4, 6),(31, 3, 31);

-- ----------------------------
-- Table: medical_registration（门诊挂号表）
-- ----------------------------
DROP TABLE IF EXISTS `medical_registration`;
CREATE TABLE `medical_registration` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `patient_card_id` int(11) DEFAULT NULL,
  `work_plan_id` int(11) DEFAULT NULL,
  `doctor_schedule_id` int(11) DEFAULT NULL,
  `doctor_id` int(11) DEFAULT NULL,
  `dept_sub_id` int(11) DEFAULT NULL,
  `date` date DEFAULT NULL,
  `slot` tinyint(4) DEFAULT NULL,
  `amount` decimal(10, 2) DEFAULT NULL,
  `out_trade_no` char(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `prepay_id` char(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `transaction_id` char(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `payment_status` tinyint(4) DEFAULT NULL,
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 21 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

INSERT INTO `medical_registration` VALUES (20, 14, 187, 794, 19, 1, '2025-04-10', 1, 30.00, '65F346D21D7D4AE9BDF2161CB1433702', 'wx201410272009395522657a690389285100', NULL, 2, '2025-04-09 11:35:55');

-- ----------------------------
-- Table: module（模块资源表）
-- ----------------------------
DROP TABLE IF EXISTS `module`;
CREATE TABLE `module` (
  `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
  `module_code` varchar(200) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '模块编号',
  `module_name` varchar(200) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '模块名称',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `unq_module_id`(`module_code`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 12 CHARACTER SET = utf8 COLLATE = utf8_general_ci COMMENT = '模块资源表' ROW_FORMAT = Dynamic;

INSERT INTO `module` VALUES (1, 'USER', '用户管理');
INSERT INTO `module` VALUES (2, 'EMPLOYEE', '员工管理');
INSERT INTO `module` VALUES (3, 'DEPT', '部门管理');
INSERT INTO `module` VALUES (4, 'MEETING', '会议管理');
INSERT INTO `module` VALUES (5, 'WORKFLOW', '工作流管理');
INSERT INTO `module` VALUES (6, 'MEETING_ROOM', '会议室管理');
INSERT INTO `module` VALUES (7, 'ROLE', '角色管理');
INSERT INTO `module` VALUES (8, 'LEAVE', '请假管理');
INSERT INTO `module` VALUES (9, 'FILE', '诊室管理');
INSERT INTO `module` VALUES (10, 'AMECT', '科室管理');
INSERT INTO `module` VALUES (11, 'REIM', '医生管理');

-- ----------------------------
-- Table: patient_face_auth（患者人脸认证表）
-- ----------------------------
DROP TABLE IF EXISTS `patient_face_auth`;
CREATE TABLE `patient_face_auth` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `patient_card_id` int(11) DEFAULT NULL,
  `date` date DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 4 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

INSERT INTO `patient_face_auth` VALUES (3, 14, '2025-03-24');

-- ----------------------------
-- Table: patient_user（微信患者用户表）
-- ----------------------------
DROP TABLE IF EXISTS `patient_user`;
CREATE TABLE `patient_user` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键',
  `open_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '微信唯一授权字符串',
  `nickname` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '微信昵称',
  `photo` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '微信头像',
  `sex` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '性别',
  `status` tinyint(4) DEFAULT NULL COMMENT '状态：1代表正常，2代表禁用',
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建日期',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 13 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

INSERT INTO `patient_user` VALUES (3, 'ociqy6_5hhmjVvMdCB5zq0PXTrdA', '海风', 'https://thirdwx.qlogo.cn/mmopen/vi_32/PiajxSqBRaEIFyVQYGJ8G1tgzm3mKZHFKSb1arL86xaoktNFEibiceoPGB3OBBIpOxzG6rB3eVjnaNLcrzJ0tc7ApLXyqv6n2Zia2Wa2lHibPYBIC5UkpV2KHtg/132', '男', 1, '2024-12-30 12:13:54');
INSERT INTO `patient_user` VALUES (6, 'oLdPw5PtSKCPJRLbYWeHLm8PJ2fE', '微信用户', 'https://thirdwx.qlogo.cn/mmopen/vi_32/POgEwh4mIHO4nibH0KlMECNjjGxQUq24ZEaGT4poC6icRiccVGKSyXwibcPq4BWmiaIGuG1icwxaQX6grC9VemZoJ8rg/132', '男', 1, '2024-06-24 11:28:40');
INSERT INTO `patient_user` VALUES (7, 'o56Mf7VAAGJdK7gZRIoZXrdwjrFk', '2003.秋', 'https://thirdwx.qlogo.cn/mmopen/vi_32/PiajxSqBRaEKlDFzNk8WjzU9tmYDewSnGXqn3gHiaA3mMSmRTBzrtNVmSiah1uofyOrGiaCNST6ToddNrzs0KA2sjOicEzlVY8via9KsAdlNA3nic3icR2cwtIicX5Q/132', '男', 1, '2024-07-02 16:27:00');
INSERT INTO `patient_user` VALUES (9, 'opowR7fOSJ64x4d_J8Y6saPu6APg', '比屋教育_王老师', 'https://thirdwx.qlogo.cn/mmopen/vi_32/zvvtvGbucBurxNdiaIiapwrmk4cJ43uefHJvciaicMwlL3u3AHSlVqUFQ5aPFlMxqkjBQ0jQBBHMZoHH8b24AYu9Az7CP6Cias07Y9Kaj6qcpUZg/132', '男', 1, '2025-01-18 14:54:01');
INSERT INTO `patient_user` VALUES (10, 'oqC4p5GvSfrvSkt2Ug5WmzC2QfKM', '随缘', 'https://thirdwx.qlogo.cn/mmopen/vi_32/AHukDxPf2pBGf12DZCvrPMjRxe3d5hoTG0IuD9u66ngFNgyFKPibt9CH63LUGW1Yz5VK8uNlsvkfHzzYad1HjZGJCG5mz6E5ps3jE3tjmtuo/132', '男', 1, '2025-02-12 15:01:38');
INSERT INTO `patient_user` VALUES (11, 'ojYyd6_ZY526GAOM5twEYnEmwI-I', '.', 'https://thirdwx.qlogo.cn/mmopen/vi_32/Il4ibIxLp13P3OylGQowajEZ6p8xpYV3E5Dw0WK7E4uaeh1UpuXnPQDu21h6Mo6AYZ9b579DYBhib059mszEU3e3eEdsibo2ibS4nTOZhdgDjvk/132', '男', 1, '2025-04-11 11:22:46');
INSERT INTO `patient_user` VALUES (12, 'orkAE7Pe2guuO7Q78o8QhsX69CqY', '微信用户', 'https://thirdwx.qlogo.cn/mmopen/vi_32/POgEwh4mIHO4nibH0KlMECNjjGxQUq24ZEaGT4poC6icRiccVGKSyXwibcPq4BWmiaIGuG1icwxaQX6grC9VemZoJ8rg/132', '男', 1, '2025-04-12 13:56:59');

-- ----------------------------
-- Table: patient_user_info（患者详细信息表）
-- ----------------------------
DROP TABLE IF EXISTS `patient_user_info`;
CREATE TABLE `patient_user_info` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键',
  `user_id` int(11) DEFAULT NULL COMMENT '患者ID',
  `uuid` char(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '患者就诊卡编号',
  `name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '姓名',
  `sex` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '性别',
  `pid` varchar(18) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '身份证号',
  `tel` varchar(11) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '手机号码',
  `birthday` date DEFAULT NULL COMMENT '出生日期',
  `medical_history` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '疾病史',
  `insurance_type` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '保险类型',
  `exist_face_model` tinyint(1) DEFAULT NULL COMMENT '是否录入面部信息',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 17 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

INSERT INTO `patient_user_info` VALUES (4, 6, '6424ccffb77149239531726a6067b3cb', '阿狸', '男', '522424200106224854', '12233104410', '1923-01-01', '[\"无\"]', '社会基本医疗保险', 0);
INSERT INTO `patient_user_info` VALUES (7, 4, 'e285ec6eed3a49069c5efd7e67062cd4', '王梦凡', '女', '130622199204132023', '15530260413', '1900-01-01', '[\"高血压\"]', '社会基本医疗保险', 0);
INSERT INTO `patient_user_info` VALUES (9, 5, '8306e145c1a444838a2824ae6a2d3f51', '张三四', '女', '430512198908131367', '15002502050', '1981-01-01', '[\"糖尿病\",\"脑出血\",\"脑中风\"]', '社会基本医疗保险', 0);
INSERT INTO `patient_user_info` VALUES (13, 10, 'f9f05639398443a5ad0a88a1a99edbc9', '张三', '男', '430512198908131367', '15002502050', '1903-01-01', '[\"脑中风\"]', '新型农村合作医疗', 0);
INSERT INTO `patient_user_info` VALUES (14, 3, '246790c306394374ae420d2571c993fb', '张三', '男', '430512198908131367', '15002502050', '1995-01-01', '[\"脑出血\",\"肾病\"]', '社会基本医疗保险', 1);
INSERT INTO `patient_user_info` VALUES (15, 11, 'd74f922ecc4b4558bbf7983d89633977', '馬光連', '男', '371481200210106059', '18853417234', '1900-01-01', '[\"无\"]', '无', 0);
INSERT INTO `patient_user_info` VALUES (16, 12, '5823fe9742954735a8fb732f83a2a9b9', '杀杀杀', '男', '148556202509110158', '17782107439', '1903-02-01', '[\"糖尿病\",\"高血压\",\"脑出血\",\"脑中风\"]', '社会基本医疗保险', 0);

-- ----------------------------
-- Table: patient_video_diagnosis（患者视频问诊表）
-- ----------------------------
DROP TABLE IF EXISTS `patient_video_diagnosis`;
CREATE TABLE `patient_video_diagnosis` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `patient_card_id` int(11) DEFAULT NULL,
  `doctor_id` int(11) DEFAULT NULL,
  `out_trade_no` char(32) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `amount` decimal(10, 2) DEFAULT NULL,
  `payment_status` tinyint(4) DEFAULT NULL,
  `prepay_id` char(64) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `transaction_id` char(32) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `expect_start` date DEFAULT NULL,
  `expect_end` date DEFAULT NULL,
  `real_start` date DEFAULT NULL,
  `real_end` date DEFAULT NULL,
  `status` tinyint(4) DEFAULT NULL,
  `create_time` date DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 2 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

INSERT INTO `patient_video_diagnosis` VALUES (1, 14, 1, 'BF9712DA0E824BAC91D07EEBF2651CDE', 100.00, NULL, 'wx201410272009395522657a690389285100', NULL, '2025-03-21', '2025-03-21', NULL, NULL, 1, '2025-03-21');

-- ----------------------------
-- Table: patient_video_diagnosis_files（视频问诊文件表）
-- ----------------------------
DROP TABLE IF EXISTS `patient_video_diagnosis_files`;
CREATE TABLE `patient_video_diagnosis_files` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `video_diagnose_id` int(11) DEFAULT NULL,
  `filename` varchar(100) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `path` varchar(300) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `create_time` datetime DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table: permission（权限表）
-- ----------------------------
DROP TABLE IF EXISTS `permission`;
CREATE TABLE `permission` (
  `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
  `permission_name` varchar(200) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '权限',
  `module_id` int(10) UNSIGNED NOT NULL COMMENT '模块ID',
  `action_id` int(10) UNSIGNED NOT NULL COMMENT '行为ID',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `unq_permission`(`permission_name`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 39 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

INSERT INTO `permission` VALUES (1, 'USER:INSERT', 1, 1),(2, 'USER:DELETE', 1, 2),(3, 'USER:UPDATE', 1, 3),(4, 'USER:SELECT', 1, 4),(5, 'EMPLOYEE:INSERT', 2, 1),(6, 'EMPLOYEE:DELETE', 2, 2),(7, 'EMPLOYEE:UPDATE', 2, 3),(8, 'EMPLOYEE:SELECT', 2, 4),(9, 'DEPT:INSERT', 3, 1),(10, 'DEPT:DELETE', 3, 2),(11, 'DEPT:UPDATE', 3, 3),(12, 'DEPT:SELECT', 3, 4),(13, 'MEETING:INSERT', 4, 1),(14, 'MEETING:DELETE', 4, 2),(15, 'MEETING:UPDATE', 4, 3),(16, 'MEETING:SELECT', 4, 4),(17, 'WORKFLOW:APPROVAL', 5, 5),(19, 'MEETING_ROOM:INSERT', 6, 1),(20, 'MEETING_ROOM:DELETE', 6, 2),(21, 'MEETING_ROOM:UPDATE', 6, 3),(22, 'MEETING_ROOM:SELECT', 6, 4),(23, 'ROLE:INSERT', 7, 1),(24, 'ROLE:DELETE', 7, 2),(25, 'ROLE:UPDATE', 7, 3),(26, 'ROLE:SELECT', 7, 4),(27, 'LEAVE:SELECT', 8, 4),(28, 'FILE:ARCHIVE', 9, 8),(29, 'AMECT:INSERT', 10, 1),(30, 'AMECT:DELETE', 10, 2),(31, 'AMECT:UPDATE', 10, 3),(32, 'AMECT:SELECT', 10, 4),(33, 'REIM:INSERT', 11, 1),(34, 'REIM:DELETE', 11, 2),(35, 'REIM:UPDATE', 11, 3),(36, 'REIM:SELECT', 11, 4),(38, 'ROOT', 0, 0);

-- ----------------------------
-- Table: role（角色表）
-- ----------------------------
DROP TABLE IF EXISTS `role`;
CREATE TABLE `role` (
  `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
  `role_name` varchar(200) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '角色名称',
  `permissions` json NOT NULL COMMENT '权限集合',
  `desc` varchar(200) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL COMMENT '描述',
  `default_permissions` json DEFAULT NULL COMMENT '系统角色内置权限',
  `systemic` tinyint(1) DEFAULT 0 COMMENT '是否为系统内置角色',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `unq_role_name`(`role_name`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 16 CHARACTER SET = utf8 COLLATE = utf8_general_ci COMMENT = '角色表' ROW_FORMAT = Dynamic;

INSERT INTO `role` VALUES (1, '院长', '[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 27, 29, 30, 31, 32]', '院长职责描述信息', '[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 27]', 1);
INSERT INTO `role` VALUES (2, '科室主任', '[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 17, 27, 29, 30, 31, 32]', NULL, '[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 17, 27]', 1);
INSERT INTO `role` VALUES (3, '医师', '[1, 2, 3, 4, 5, 6, 7, 8]', NULL, '[1, 2, 3, 4, 5, 6, 7, 8]', 1);
INSERT INTO `role` VALUES (4, 'HR', '[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]', NULL, '[1, 2, 3, 4, 5, 6, 7, 8, 28, 27]', 1);
INSERT INTO `role` VALUES (5, '财务', '[1, 2, 3, 4, 5, 6, 7, 8, 28, 36, 17]', NULL, '[1, 2, 3, 4, 5, 6, 7, 8, 28, 36, 17]', 1);
INSERT INTO `role` VALUES (6, '测试角色', '[36, 17]', '测试角色', '[36, 17]', 1);
INSERT INTO `role` VALUES (7, '超级管理员', '[38]', '超级管理员用户不能删除和修改', '[38]', 1);
INSERT INTO `role` VALUES (15, '测试护士', '[4, 8, 12, 13, 14, 15, 16, 19, 20, 21, 22, 26, 27, 28, 29, 30, 31, 32, 36]', '测试护士角色', NULL, 0);

-- ----------------------------
-- Table: users（用户表）
-- ----------------------------
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键',
  `username` varchar(200) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL COMMENT '用户名',
  `password` varchar(2000) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL COMMENT '密码',
  `name` varchar(20) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL COMMENT '姓名',
  `sex` enum('男','女') CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL COMMENT '性别',
  `tel` char(11) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL COMMENT '手机号码',
  `email` varchar(200) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL COMMENT '邮箱',
  `job` varchar(200) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL COMMENT '职位',
  `role` json NOT NULL COMMENT '角色',
  `root` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否是超级管理员',
  `dept_id` int(10) UNSIGNED DEFAULT NULL COMMENT '部门编号',
  `status` tinyint(4) NOT NULL COMMENT '状态',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '创建时间',
  `doctor_id` int(11) DEFAULT NULL COMMENT '关联的doctor_id',
  `hiredate` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '生日',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `unq_username`(`username`) USING BTREE,
  INDEX `unq_email`(`email`) USING BTREE,
  INDEX `idx_dept_id`(`dept_id`) USING BTREE,
  INDEX `idx_status`(`status`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 22 CHARACTER SET = utf8 COLLATE = utf8_general_ci COMMENT = '用户表' ROW_FORMAT = Dynamic;

INSERT INTO `users` VALUES (1, 'admin', '68943c12b127b7d5b22750b32d0e89f7', 'admin', '男', '15055555551', 'admin@163.com', '医生', '[7]', 1, 1, 1, '2025-03-09 19:07:42', 1, '2025-03-09 19:07:42');
INSERT INTO `users` VALUES (2, 'zhangsan', '7044670653a6ff0662d4def3e2dd4979', 'root', '女', '15055555552', 'zhangsan@163.com', '医生', '[7]', 1, 1, 1, '2025-02-18 10:34:06', 1, '2025-02-18 10:34:06');
INSERT INTO `users` VALUES (3, 'lisi', 'd1c3ef3d450532d24ab676e8edd05184', 'lisi', '男', '15055555553', 'lisi@163.com', '医生', '[3, 4, 5]', 0, 5, 1, '2024-09-27 16:44:15', 1, '2025-01-05 11:45:38');
INSERT INTO `users` VALUES (4, 'lisi1', '841A3261CDB4F1282B81A1C9C74BE834', '李四一', '男', '15055555553', 'lisi@163.com', '医生', '[5, 4]', 0, 3, 1, '2024-09-27 16:44:16', 1, '2025-01-05 11:45:38');
INSERT INTO `users` VALUES (18, 'zhaoliu', '1275D389213EC634AC4299F130BF685F', '赵六', '女', '15055555553', '432@qq.com', '医生', '[2]', 0, 3, 1, '2024-09-27 16:44:19', 1, '2025-01-05 11:45:38');
INSERT INTO `users` VALUES (19, 'shunqi', 'AB3C7A427BE783CEDD574202C57A320D', '孙七', '女', '15055555553', '432@qq.com', '医生', '[5]', 0, 4, 1, '2024-09-27 16:44:19', 1, '2025-01-05 11:45:38');
INSERT INTO `users` VALUES (20, 'linan', '189DCCF8BCF7FA1ABE5C5913728AF04F', '李楠', '男', '15055555553', '432@qq.com', '医生', '[1]', 0, 5, 1, '2024-09-27 16:44:20', 1, '2025-01-05 11:45:38');
INSERT INTO `users` VALUES (21, 'xiaowang', 'AA244867DAF5B2B5D4BB3CB0F3C1F4EB', '小王', '男', '15055555553', '432@qq.com', '医生', '[3, 5]', 0, 6, 1, '2024-09-27 16:44:21', 1, '2025-01-05 11:45:38');

SET FOREIGN_KEY_CHECKS = 1;
