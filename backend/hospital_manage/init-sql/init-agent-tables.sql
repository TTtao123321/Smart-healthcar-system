-- ============================================================
-- 智慧医疗助手 Agent 所需表结构
-- 创建时间: 2026-06-17
-- 说明: 包含症状-科室映射、医生标签、FAQ知识库、对话会话、对话消息、用药提醒 6 张表
-- 注意: dept_id 参考 medical_dept 表的实际数据
--       1=口腔科 2=眼科 3=耳鼻喉科 4=内科 5=外科
--       6=皮肤科 7=妇科 8=儿科 9=神经科 10=肿瘤科
--       11=产科 12=骨科
-- ============================================================

SET NAMES utf8mb4;

-- ----------------------------
-- 1. 症状-科室映射规则
-- ----------------------------
CREATE TABLE IF NOT EXISTS symptom_dept_mapping (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symptom_keyword VARCHAR(50) NOT NULL COMMENT '症状关键词',
    dept_id BIGINT NOT NULL COMMENT '关联科室ID(参考medical_dept.id)',
    clarify_question VARCHAR(200) COMMENT '澄清问题',
    clarify_answer_branch VARCHAR(100) COMMENT '澄清回答分支',
    priority INT DEFAULT 0 COMMENT '优先级',
    status TINYINT DEFAULT 1 COMMENT '0-禁用 1-启用',
    reviewed_by VARCHAR(50) COMMENT '医务科审核人',
    reviewed_at DATETIME COMMENT '审核时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_symptom (symptom_keyword),
    INDEX idx_dept (dept_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='症状-科室映射规则';

-- ----------------------------
-- 2. 医生标签
-- ----------------------------
CREATE TABLE IF NOT EXISTS doctor_tag (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    doctor_id BIGINT NOT NULL COMMENT '关联医生ID(参考doctor.id)',
    tag VARCHAR(50) NOT NULL COMMENT '标签',
    tag_type VARCHAR(20) NOT NULL COMMENT '标签类型(specialty/disease/symptom)',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_doctor (doctor_id),
    INDEX idx_tag (tag),
    INDEX idx_tag_type (tag_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='医生标签';

-- ----------------------------
-- 3. 常见问题知识库
-- ----------------------------
CREATE TABLE IF NOT EXISTS faq (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    question VARCHAR(500) NOT NULL COMMENT '问题',
    answer TEXT NOT NULL COMMENT '回答',
    category VARCHAR(50) COMMENT '分类(流程/政策/导航)',
    keywords VARCHAR(200) COMMENT '关键词(逗号分隔)',
    embedding BLOB COMMENT '向量嵌入',
    status TINYINT DEFAULT 1 COMMENT '0-禁用 1-启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_category (category),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='常见问题知识库';

-- ----------------------------
-- 4. 对话会话
-- ----------------------------
CREATE TABLE IF NOT EXISTS chat_session (
    id VARCHAR(36) PRIMARY KEY COMMENT 'UUID',
    patient_id BIGINT NOT NULL COMMENT '患者ID(参考patient_user_info.id)',
    status VARCHAR(20) DEFAULT 'active' COMMENT 'active/closed',
    current_intent VARCHAR(30) COMMENT '当前意图',
    fsm_state VARCHAR(30) COMMENT 'FSM当前状态',
    fsm_context JSON COMMENT 'FSM上下文数据',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_patient (patient_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='对话会话';

-- ----------------------------
-- 5. 对话消息
-- ----------------------------
CREATE TABLE IF NOT EXISTS chat_message (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL COMMENT '关联会话(参考chat_session.id)',
    role VARCHAR(10) NOT NULL COMMENT 'user/assistant/system',
    content TEXT NOT NULL COMMENT '消息内容',
    intent VARCHAR(30) COMMENT '识别的意图',
    action_taken VARCHAR(50) COMMENT '执行的动作',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session (session_id),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='对话消息';

-- ----------------------------
-- 6. 用药提醒
-- ----------------------------
CREATE TABLE IF NOT EXISTS medication_reminder (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    patient_id BIGINT NOT NULL COMMENT '患者ID(参考patient_user_info.id)',
    prescription_id BIGINT COMMENT '关联处方ID(参考prescription.id, HIS数据驱动)',
    medicine_name VARCHAR(100) NOT NULL COMMENT '药品名称',
    dosage VARCHAR(50) COMMENT '剂量',
    frequency VARCHAR(50) COMMENT '频次',
    remind_times JSON COMMENT '提醒时间列表',
    remind_method VARCHAR(20) DEFAULT 'push' COMMENT 'push/sms/wechat',
    status VARCHAR(20) DEFAULT 'active' COMMENT 'active/paused/completed',
    start_date DATE COMMENT '开始日期',
    end_date DATE COMMENT '结束日期',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_patient (patient_id),
    INDEX idx_status (status),
    INDEX idx_prescription (prescription_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用药提醒';

-- ============================================================
-- 种子数据
-- ============================================================

-- ----------------------------
-- 症状-科室映射种子数据（需经医务科审核）
-- dept_id 对应 medical_dept 表: 4=内科 9=神经科 5=外科 6=皮肤科 12=骨科
-- 如科室ID有变动，请根据实际数据调整
-- ----------------------------
INSERT INTO symptom_dept_mapping (symptom_keyword, dept_id, clarify_question, clarify_answer_branch, priority, reviewed_by, reviewed_at) VALUES
('肚子疼', 4, '疼痛部位？是否伴随呕吐？', '上腹痛→消化内科；右下腹痛→普外科', 1, 'system', NOW()),
('头疼', 9, '头痛部位？伴随症状？', '偏头痛→神经内科；鼻塞伴头痛→耳鼻喉科', 1, 'system', NOW()),
('胸闷', 4, '是否活动后加重？', '活动后加重→心内科；咳嗽伴胸闷→呼吸内科', 1, 'system', NOW()),
('咳嗽', 4, '是否有痰？痰的颜色？', '干咳→呼吸内科；黄痰→呼吸内科', 1, 'system', NOW()),
('胃痛', 4, '是否反酸？饭前还是饭后痛？', '反酸→消化内科；饭后痛→消化内科', 2, 'system', NOW()),
('头晕', 9, '是否天旋地转？是否伴随耳鸣？', '天旋地转→神经内科；耳鸣→耳鼻喉科', 1, 'system', NOW()),
('心悸', 4, '是否活动后加重？持续时间？', '活动后加重→心内科；短暂发作→心内科', 1, 'system', NOW()),
('腰痛', 5, '是否伴随尿频尿急？是否有外伤？', '尿频尿急→泌尿外科；外伤→骨科', 1, 'system', NOW()),
('皮疹', 6, '是否瘙痒？分布部位？', '瘙痒→皮肤科；全身性→皮肤科', 1, 'system', NOW()),
('失眠', 9, '入睡困难还是早醒？是否焦虑？', '入睡困难→神经内科；焦虑→心理科', 2, 'system', NOW());

-- ----------------------------
-- FAQ种子数据
-- ----------------------------
INSERT INTO faq (question, answer, category, keywords) VALUES
('医院几点上班？', '门诊时间：周一至周五 8:00-17:00，周六 8:00-12:00，周日休息。急诊24小时开放。', '流程', '上班时间,门诊时间,几点开门'),
('怎么挂号？', '您可以通过以下方式挂号：1. 在线挂号（推荐）；2. 自助机挂号；3. 人工窗口挂号。在线挂号请点击"挂号"按钮。', '流程', '挂号,预约,怎么挂号'),
('体检在哪里？', '体检中心位于门诊楼2楼A区，请空腹前往，建议早上8点前到达。', '导航', '体检,体检中心,体检在哪'),
('医保怎么用？', '请携带医保卡就诊，挂号和缴费时选择"医保结算"。具体报销比例请咨询医保窗口（门诊1楼C区）。', '政策', '医保,报销,医保卡'),
('报告多久出？', '常规检验报告一般2-4小时出具，影像检查报告一般1-2个工作日出具。您可以在"报告查询"中查看。', '流程', '报告,出报告,多久出报告');
