#!/usr/bin/env python3
"""生成一周（7天）医生出诊排班 + 挂号测试数据 SQL
日期使用 CURDATE() + DATE_ADD() 动态计算，执行时自动取当天 ~ 当天+6天
"""
from datetime import date

OUTPUT = "/Users/bytedance/Desktop/mywork/Smart-healthcar-system/hospital_manage_backend/init-sql/05-init-schedule-test-data.sql"

# === 配置 ===
DAYS = 7  # 生成天数

# 活跃医生 → 诊室 映射（status=1 且在 medical_dept_sub_doctor 中）
DOCTORS = [
    # (doctor_id, name, dept_sub_id, dept_sub_name)
    (1,  "李雨萌", 2,  "口腔颌面内科"),
    (2,  "张佳欣", 20, "皮肤病门诊"),
    (3,  "王文彦", 9,  "呼吸内科门诊"),
    (4,  "刘梦琪", 19, "整形外科门诊"),
    (6,  "周嘉欣", 26, "肿瘤科门诊"),
    (7,  "吴子萱", 4,  "白内障诊疗中心"),
    (11, "冯佳雨", 14, "风湿免疫门诊"),
    (12, "蔡心怡", 14, "风湿免疫门诊"),
    (13, "朱宇琪", 14, "风湿免疫门诊"),
    (14, "曾子轩", 13, "肾内科门诊"),
    (15, "翟婷婷", 26, "肿瘤科门诊"),
    (19, "袁文斌", 1,  "口腔颌面外科"),
    (20, "韩倩倩", 1,  "口腔颌面外科"),
]

# 每天出诊的医生（doctor_id 列表）
# 涵盖全部 9 个诊室，每位医生一周出诊 3-4 天
DAILY_SCHEDULE = {
    0: [1, 2, 3, 4, 6, 7, 11, 14, 19, 20],   # 6/24 周三
    1: [1, 2, 3, 6, 7, 12, 15, 19, 20],       # 6/25 周四
    2: [1, 4, 6, 7, 11, 13, 14, 20],           # 6/26 周五
    3: [2, 3, 7, 12, 15, 19],                   # 6/27 周六
    4: [1, 4, 6, 11, 14, 20],                   # 6/28 周日
    5: [2, 3, 6, 7, 12, 13, 15, 19],            # 6/29 周一
    6: [1, 4, 7, 11, 14, 19, 20],               # 6/30 周二
}

# 挂号记录：患者 × 医生 × 日期 × 状态
# (patient_id, patient_name, doctor_id, day_offset, slot, status)
# status: 0=待就诊, 1=就诊中, 2=已就诊, 3=复诊中
REGISTRATIONS = [
    # --- 6/24 ---
    (1, "张伟", 1,  0, 1, 0),   # 待就诊
    (1, "张伟", 20, 0, 1, 1),   # 就诊中
    (2, "李娜", 7,  0, 1, 2),   # 已就诊
    (3, "王强", 3,  0, 1, 0),   # 待就诊
    (4, "赵敏", 1,  0, 2, 0),   # 待就诊
    (5, "陈静", 20, 0, 2, 1),   # 就诊中
    (6, "刘洋", 19, 0, 1, 3),   # 复诊中
    (7, "孙丽", 2,  0, 1, 2),   # 已就诊
    # --- 6/25 ---
    (1, "张伟", 1,  1, 1, 0),
    (2, "李娜", 20, 1, 1, 0),
    (3, "王强", 3,  1, 1, 0),
    (8, "周磊", 7,  1, 1, 0),
    # --- 6/26 ---
    (4, "赵敏", 1,  2, 1, 0),
    (5, "陈静", 20, 2, 1, 0),
    (6, "刘洋", 7,  2, 1, 0),
    (7, "孙丽", 14, 2, 1, 0),
    # --- 6/27 ---
    (8, "周磊", 2,  3, 1, 0),
    (1, "张伟", 7,  3, 1, 0),
    (2, "李娜", 19, 3, 1, 0),
    # --- 6/28 ---
    (3, "王强", 1,  4, 1, 0),
    (4, "赵敏", 20, 4, 1, 0),
    (5, "陈静", 11, 4, 1, 0),
    # --- 6/29 ---
    (6, "刘洋", 2,  5, 1, 0),
    (7, "孙丽", 7,  5, 1, 0),
    (8, "周磊", 19, 5, 1, 0),
    # --- 6/30 ---
    (1, "张伟", 1,  6, 1, 0),
    (2, "李娜", 20, 6, 1, 0),
    (3, "王强", 7,  6, 1, 0),
]

# === 生成 SQL ===

# 构建 doctor lookup
doc_map = {d[0]: d for d in DOCTORS}

# 1. 生成 work_plan
wp_id = 200
wp_records = []          # [(wp_id, doctor_id, dept_sub_id, day_offset, maximum, num)]
wp_day_map = {}          # {(doctor_id, day_offset): wp_id}
wp_num = {}              # wp_id → num (挂号数)

for day_offset in range(DAYS):
    doc_ids = DAILY_SCHEDULE.get(day_offset, [])
    for did in doc_ids:
        wp_records.append((wp_id, did, doc_map[did][2], day_offset, 30, 0))
        wp_day_map[(did, day_offset)] = wp_id
        wp_num[wp_id] = 0
        wp_id += 1

# 2. 统计每个 work_plan 的挂号数
for reg in REGISTRATIONS:
    _pid, _pname, did, day_offset, _slot, _status = reg
    wp = wp_day_map.get((did, day_offset))
    if wp:
        wp_num[wp] = wp_num.get(wp, 0) + 1

# 更新 wp_records 中的 num
wp_records = [(wpid, did, dsid, doff, maxn, wp_num.get(wpid, 0)) for wpid, did, dsid, doff, maxn, _ in wp_records]

# 3. 生成 schedule 段
sched_id = 900
sched_records = []       # [(sched_id, wp_id, slot, maximum, num)]
sched_map = {}           # {(wp_id, slot): sched_id}
sched_num = {}           # {(wp_id, slot): num}

# 初始化每个 wp 的 3 个 slot
for wpid, _, _, _, _, _ in wp_records:
    for slot in (1, 2, 3):
        sched_records.append((sched_id, wpid, slot, 10, 0))
        sched_map[(wpid, slot)] = sched_id
        sched_num[(wpid, slot)] = 0
        sched_id += 1

# 统计每个 slot 的挂号数
reg_slot_map = {}  # (did, day_offset, slot) → count
for reg in REGISTRATIONS:
    _pid, _pname, did, day_offset, slot, _status = reg
    key = (did, day_offset, slot)
    reg_slot_map[key] = reg_slot_map.get(key, 0) + 1

for (did, day_offset, slot), cnt in reg_slot_map.items():
    wp = wp_day_map.get((did, day_offset))
    if wp and (wp, slot) in sched_num:
        sched_num[(wp, slot)] = sched_num.get((wp, slot), 0) + cnt

sched_records = [
    (sid, wpid, slot, maxn, sched_num.get((wpid, slot), 0))
    for sid, wpid, slot, maxn, _ in sched_records
]

# 4. 生成 registration
reg_id = 13
reg_records = []
for reg in REGISTRATIONS:
    pid, pname, did, day_offset, slot, status = reg
    wp = wp_day_map.get((did, day_offset))
    if not wp:
        continue
    sch = sched_map.get((wp, slot))
    if not sch:
        continue
    d = doc_map[did]
    dsid = d[2]
    reg_records.append((reg_id, pid, wp, sch, did, dsid, day_offset, slot, status))
    reg_id += 1

# === 输出 SQL 文件 ===
lines = []
lines.append("-- ============================================")
lines.append(f"-- 医生出诊排班 + 挂号全流程测试数据")
lines.append(f"-- 日期范围: 当天 ~ 当天+{DAYS-1}天（{DAYS}天，动态计算）")
lines.append(f"-- 涵盖诊室: 口腔颌面外科/内科、白内障、呼吸内科、肾内科、风湿免疫、整形外科、皮肤病、肿瘤科（共9个诊室）")
lines.append(f"-- 生成时间: {date.today()}")
lines.append("-- ============================================")
lines.append("")
lines.append("SET NAMES utf8mb4;")
lines.append("SET CHARACTER_SET_CONNECTION=utf8mb4;")
lines.append("")
lines.append("-- 动态日期变量（执行时自动取当天）")
for i in range(DAYS):
    if i == 0:
        lines.append(f"SET @d{i} = CURDATE();")
    else:
        lines.append(f"SET @d{i} = DATE_ADD(CURDATE(), INTERVAL {i} DAY);")
lines.append("")
lines.append("-- 清理旧测试数据")
lines.append(f"DELETE FROM medical_registration WHERE id BETWEEN 13 AND {reg_id - 1};")
lines.append(f"DELETE FROM doctor_work_plan_schedule WHERE id BETWEEN 900 AND {sched_id - 1};")
lines.append(f"DELETE FROM doctor_work_plan WHERE id BETWEEN 200 AND {wp_id - 1};")
lines.append("")

# Work plans
lines.append("-- ============================================")
lines.append(f"-- 1. 医生出诊排班（{len(wp_records)} 条）")
lines.append("-- ============================================")
lines.append("INSERT INTO `doctor_work_plan` (`id`, `doctor_id`, `dept_sub_id`, `date`, `maximum`, `num`) VALUES")
wp_lines = []
for wpid, did, dsid, doff, maxn, num in wp_records:
    wp_lines.append(f"({wpid}, {did:>2}, {dsid:>2}, @d{doff}, {maxn}, {num:>2})")
lines.append(",\n".join(wp_lines) + ";")
# 添加注释说明
lines.append("-- 医生出诊对应关系：")
for d in DOCTORS:
    lines.append(f"--   {d[0]:>2} = {d[1]} / {d[3]} (dept_sub={d[2]})")
lines.append("")

# Schedules
lines.append("-- ============================================")
lines.append(f"-- 2. 排班时段（{len(sched_records)} 条）")
lines.append("-- ============================================")
lines.append("INSERT INTO `doctor_work_plan_schedule` (`id`, `work_plan_id`, `slot`, `maximum`, `num`) VALUES")
sch_lines = []
for sid, wpid, slot, maxn, num in sched_records:
    sch_lines.append(f"({sid}, {wpid}, {slot}, {maxn}, {num})")
# Group by schedule ID ranges for readability
lines.append(",\n".join(sch_lines) + ";")
lines.append("")

# Registrations
lines.append("-- ============================================")
lines.append(f"-- 3. 挂号记录（{len(reg_records)} 条，覆盖 0=待就诊/1=就诊中/2=已就诊/3=复诊中）")
lines.append("-- ============================================")
lines.append("INSERT INTO `medical_registration` (`id`, `patient_id`, `work_plan_id`, `doctor_schedule_id`, `doctor_id`, `dept_sub_id`, `date`, `slot`, `status`, `payment_status`) VALUES")
reg_lines = []
for rid, pid, wp, sch, did, dsid, doff, slot, status in reg_records:
    reg_lines.append(
        f"({rid:>2}, {pid}, {wp}, {sch}, {did:>2}, {dsid:>2}, @d{doff}, {slot}, {status}, 1)"
    )
lines.append(",\n".join(reg_lines) + ";")
lines.append("")

# 验证查询
lines.append("-- ============================================")
lines.append("-- 验证查询（可选）")
lines.append("-- ============================================")
lines.append("-- 每日出诊医生数")
lines.append("-- SELECT date, COUNT(*) AS doctor_count FROM doctor_work_plan WHERE id BETWEEN 200 AND " + str(wp_id - 1) + " GROUP BY date ORDER BY date;")
lines.append("--")
lines.append("-- 挂号状态分布")
lines.append("-- SELECT status, CASE status WHEN 0 THEN '待就诊' WHEN 1 THEN '就诊中' WHEN 2 THEN '已就诊' WHEN 3 THEN '复诊中' END, COUNT(*) FROM medical_registration WHERE id BETWEEN 13 AND " + str(reg_id - 1) + " GROUP BY status ORDER BY status;")

with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

print(f"Generated: {OUTPUT}")
print(f"  Work plans: {len(wp_records)}")
print(f"  Schedules:  {len(sched_records)}")
print(f"  Registrations: {len(reg_records)}")
print(f"  ID ranges: WP 200-{wp_id-1}, Sched 900-{sched_id-1}, Reg 13-{reg_id-1}")
