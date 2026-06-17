package com.hospital.hms.service.impl;

import cn.hutool.core.bean.BeanUtil;
import cn.hutool.core.date.DateField;
import cn.hutool.core.date.DateRange;
import cn.hutool.core.date.DateTime;
import cn.hutool.core.date.DateUtil;
import cn.hutool.core.map.MapUtil;
import com.hospital.common.exception.GlobalException;
import com.hospital.hms.common.OperationMessage;
import com.hospital.hms.dao.DoctorWorkPlanDao;
import com.hospital.hms.dao.DoctorWorkPlanScheduleDao;
import com.hospital.hms.pojo.DoctorWorkPlan;
import com.hospital.hms.pojo.DoctorWorkPlanSchedule;
import com.hospital.hms.service.DoctorWorkPlanService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.*;

@Service
public class DoctorWorkPlanServiceImpl implements DoctorWorkPlanService {
    @Autowired
    private DoctorWorkPlanDao doctorWorkPlanDao;

    @Autowired
    private DoctorWorkPlanScheduleDao doctorWorkPlanScheduleDao;

    @Autowired
    private RedisTemplate redisTemplate;

    @Override
    public Collection<HashMap> selectWorkPlanByTime(Map<String, Object> map, ArrayList<String> dateList) {
        //获取日期范围内doctor_work_plan表的门诊记录(不包括没有出诊的日期)
        ArrayList<HashMap> list = doctorWorkPlanDao.selectWorkPlanByTime(map);
        //将结果转化为key为诊室id，value为内容集合的集合
        Map<Integer, HashMap> tempResult = new HashMap<>();
        //构造初始结果集，此时plan的内容key为日期，value为多个医生
        for (HashMap one : list) {
            String deptName = MapUtil.getStr(one, "deptName");
            int deptSubId = MapUtil.getInt(one, "deptSubId");
            String deptSubName = MapUtil.getStr(one, "deptSubName");
            String doctorName = MapUtil.getStr(one, "doctorName");
            String date = MapUtil.getStr(one, "date");
            if (!tempResult.containsKey(deptSubId)) {
                HashMap temp = new HashMap() {{
                    put("deptName", deptName);
                    put("deptSubId", deptSubId);
                    put("deptSubName", deptSubName);
                    put("plan", new LinkedHashMap<>() {{
                        put(date, new ArrayList<>() {{
                            add(doctorName);
                        }});
                    }});
                }};
                tempResult.put(deptSubId, temp);
            } else {
                HashMap tempMap = tempResult.get(deptSubId);
                LinkedHashMap plan = (LinkedHashMap) tempMap.get("plan");
                if (!plan.containsKey(date)) {
                    plan.put(date, new ArrayList<>());
                }
                ArrayList doctors = (ArrayList) plan.get(date);
                doctors.add(doctorName);
            }
        }
        //对结果集中的"plan"的没有出诊计划的日期赋予空的集合
        tempResult.values().forEach(map1 -> {
            LinkedHashMap plan = (LinkedHashMap) map1.get("plan");
            dateList.forEach(date -> plan.putIfAbsent(date, new ArrayList<>()));
        });
        tempResult.values().forEach(map2 -> {
            //将结果集中的"plan"的数据按日期从前到后排序，此时sortedPlan的key为date，value为医生集合
            TreeMap<String, ArrayList> sortedPlan = new TreeMap<>((d1, d2) -> new DateTime(d1).isAfter(new DateTime(d2)) ? 1 : -1);
            LinkedHashMap plan = (LinkedHashMap) map2.get("plan");
            sortedPlan.putAll(plan);
            //将结果集中的"plan"的内容转化为前端需要的格式
            map2.replace("plan", new ArrayList<>());
            sortedPlan.forEach((date, doctors) -> {
                ((ArrayList) map2.get("plan")).add(new HashMap<String, Object>() {{
                    put("date", date);
                    put("doctors", doctors);
                }});
            });
        });
        return tempResult.values();
        //如果要返回ArrayList，则为：return new ArrayList<HashMap>(tempResult.values());
    }

    @Override
    public ArrayList<String> getDateList(String startDate, String endDate, boolean isFormatted) {
        DateRange range = DateUtil.range(new DateTime(startDate), new DateTime(endDate), DateField.DAY_OF_MONTH);
        ArrayList<String> dateList = new ArrayList<>();
        range.forEach(date -> {
            if (isFormatted) {
                // 格式化日期，如：03月19日（星期一）
                dateList.add(date.toString("MM月dd日") + " (" + date.dayOfWeekEnum().toChinese() + ") ");
            } else {
                // 原始日期字符串
                dateList.add(date.toDateStr());
            }
        });
        return dateList;
    }

    @Override
    @Transactional
    public String insert(Map<String, Object> map) {
        Integer id = doctorWorkPlanDao.selectWorkPlanToday(map);
        if (id != null) {
            return OperationMessage.PLAN_EXISTS.toString();
        }
        try {
            DoctorWorkPlan doctorWorkPlan = new DoctorWorkPlan();
            doctorWorkPlan.setDoctorId((Integer) map.get("doctorId"));
            doctorWorkPlan.setDeptSubId((Integer) map.get("deptSubId"));
            doctorWorkPlan.setDate((String) map.get("date"));
            doctorWorkPlan.setMaximum((Integer) map.get("totalMaximum"));
            doctorWorkPlanDao.insert(doctorWorkPlan);
            Integer[] slots = (Integer[]) map.get("slots");
            Integer workPlanId = doctorWorkPlan.getId();
            String date = doctorWorkPlan.getDate();
            Integer maximum = (Integer) map.get("slotMaximum");
            for (Integer slot : slots) {
                DoctorWorkPlanSchedule schedule = new DoctorWorkPlanSchedule();
                schedule.setWorkPlanId(workPlanId);
                schedule.setSlot(slot);
                schedule.setMaximum(maximum);
                schedule.setNum(0);
                doctorWorkPlanScheduleDao.insert(schedule);
                Integer scheduleId = schedule.getId();
                //避免患者端挂号出现超售的现象，将诊计划保存到redis中
                addScheduleCacheToRedis(schedule,scheduleId,date);
            }
        } catch (Exception e) {
            throw new GlobalException("添加出诊计划时段时出错");
        }
        return OperationMessage.PLAN_SAVE_OK.toString();
    }

    private static final String WORK_PLAN_SCHEDULE_KEY = "work_plan_schedule_";

    private static final Map<String, String> APPOINTMENT_SLOT = Map.ofEntries(
            new AbstractMap.SimpleEntry<>("1", "08:00"),
            new AbstractMap.SimpleEntry<>("2", "08:30"),
            new AbstractMap.SimpleEntry<>("3", "09:00"),
            new AbstractMap.SimpleEntry<>("4", "09:30"),
            new AbstractMap.SimpleEntry<>("5", "10:00"),
            new AbstractMap.SimpleEntry<>("6", "10:30"),
            new AbstractMap.SimpleEntry<>("7", "11:00"),
            new AbstractMap.SimpleEntry<>("8", "11:30"),
            new AbstractMap.SimpleEntry<>("9", "13:00"),
            new AbstractMap.SimpleEntry<>("10", "13:30"),
            new AbstractMap.SimpleEntry<>("11", "14:00"),
            new AbstractMap.SimpleEntry<>("12", "14:30"),
            new AbstractMap.SimpleEntry<>("13", "15:00"),
            new AbstractMap.SimpleEntry<>("14", "15:30"),
            new AbstractMap.SimpleEntry<>("15", "16:00")
    );

    private void addScheduleCacheToRedis(DoctorWorkPlanSchedule schedule, Integer scheduleId, String date) {
        // 定义缓存记录的Key
        String key = (String) WORK_PLAN_SCHEDULE_KEY + scheduleId;
        Map<String, Object> map = BeanUtil.beanToMap(schedule);
        // 将出诊详细信息段缓存到Redis
        redisTemplate.opsForHash().putAll(key, map);
        // 获取时间段对应的起始时间
        String time = APPOINTMENT_SLOT.get(String.valueOf(schedule.getSlot()));
        // 解析出诊时间，设置缓存过期时间
        Date expirationTime = DateUtil.parse(date + " " + time);
        redisTemplate.expireAt(key, expirationTime);
    }
}
