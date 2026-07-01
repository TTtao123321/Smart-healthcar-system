package com.hospital.hms.service.impl;

import cn.hutool.core.bean.BeanUtil;
import cn.hutool.core.date.DateUtil;
import cn.hutool.core.map.MapUtil;
import com.hospital.common.exception.GlobalException;
import com.hospital.hms.common.Constants;
import com.hospital.hms.common.OperationMessage;
import com.hospital.hms.controller.form.DoctorScheduleSlotVO;
import com.hospital.hms.dao.DoctorWorkPlanScheduleDao;
import com.hospital.hms.event.HmsDomainEvent;
import com.hospital.hms.event.HmsDomainEventPublisher;
import com.hospital.hms.event.ScheduleEventPayload;
import com.hospital.hms.pojo.DoctorWorkPlanSchedule;
import com.hospital.hms.service.DoctorWorkPlanScheduleService;
import lombok.extern.log4j.Log4j2;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.*;
import java.util.stream.Collectors;

import static com.hospital.hms.common.Constants.WORK_PLAN_SCHEDULE_KEY;

@Log4j2
@Service
public class DoctorWorkPlanScheduleServiceImpl implements DoctorWorkPlanScheduleService {
    @Autowired
    private DoctorWorkPlanScheduleDao doctorWorkPlanScheduleDao;

    @Autowired
    private RedisTemplate redisTemplate;

    @Autowired
    private HmsDomainEventPublisher eventPublisher;

    @Override
    public ArrayList<HashMap> selectDoctorScheduleByDeptSubIdAndDate(Map<String, Object> map) {
        ArrayList<HashMap> list = doctorWorkPlanScheduleDao.selectDoctorScheduleByDeptSubIdAndDate(map);
        LinkedHashMap<Integer, HashMap> doctorMap = new LinkedHashMap<>();
        for (HashMap hashMap : list) {
            int doctorId = MapUtil.getInt(hashMap, "doctorId");
            int slot = MapUtil.getInt(hashMap, "slot");
            HashMap doctor = doctorMap.computeIfAbsent(doctorId, k -> {
                HashMap newDoctor = new HashMap<>(hashMap);
                newDoctor.put("slot", new ArrayList<Boolean>(Collections.nCopies(15, Boolean.FALSE)));
                return newDoctor;
            });
            ArrayList<Boolean> slotList = (ArrayList<Boolean>) doctor.get("slot");
            if (slot >= 1 && slot <= 15) {
                slotList.set(slot - 1, Boolean.TRUE);
            }
        }
        return new ArrayList<>(doctorMap.values());
    }

    @Override
    public HashMap selectScheduleByWorkPlanId(Integer workPlanId) {
        ArrayList<HashMap> list = doctorWorkPlanScheduleDao.selectScheduleByWorkPlanId(workPlanId);
        if (list.isEmpty()) {
            return new HashMap();
        }
        HashMap result = new HashMap();
        HashMap firstRecord = list.get(0);
        result.put("doctorId", MapUtil.getInt(firstRecord, "doctorId"));
        result.put("maximum", MapUtil.getInt(firstRecord, "maximum"));
        result.put("scheduleStatus", MapUtil.getStr(firstRecord, "scheduleStatus", "ACTIVE"));
        ArrayList<HashMap> temp = new ArrayList<>();
        int totalNum = 0;
        for (HashMap map : list) {
            int maximum = MapUtil.getInt(map, "maximum");
            int num = MapUtil.getInt(map, "num");
            totalNum += num;
            temp.add(new HashMap<>() {{
                put("scheduleId", MapUtil.getInt(map, "scheduleId"));
                put("slot", MapUtil.getInt(map, "slot"));
                put("num", num);
                put("maximum", maximum);
                put("remaining", Math.max(maximum - num, 0));
            }});
        }
        result.put("num", totalNum);
        result.put("slots", temp);
        return result;
    }

    @Override
    @Transactional
    public void updateSchedule(Map<String, Object> map) {
        doctorWorkPlanScheduleDao.updateMaximum(map);
        Integer workPlanId = MapUtil.getInt(map, "workPlanId");
        ArrayList<DoctorScheduleSlotVO> slots = (ArrayList<DoctorScheduleSlotVO>) map.get("slots");
        ArrayList<DoctorWorkPlanSchedule> addList = new ArrayList<>();
        ArrayList<Integer> removeList = new ArrayList<>();
        slots.forEach(slot -> {
            if ("insert".equals(slot.getOperate())) {
                DoctorWorkPlanSchedule entity = new DoctorWorkPlanSchedule();
                entity.setWorkPlanId(workPlanId);
                entity.setMaximum(slot.getMaximum());
                entity.setSlot(slot.getSlot());
                addList.add(entity); // 时间段保存到添加列表
            } else {
                removeList.add(slot.getScheduleId()); // 时间段保存到删除列表
            }
        });
        addSchedules(addList);
        deleteSchedules(removeList);
        eventPublisher.publishAfterCommit(buildScheduleEvent("schedule.updated", workPlanId, slots));
    }

    private void deleteSchedules(ArrayList<Integer> removeList) {
        if (removeList == null || removeList.isEmpty()) {
            return;
        }
        long sum = doctorWorkPlanScheduleDao.selectSumNumByIds(removeList);
        if (sum > 0) {
            throw new GlobalException(OperationMessage.PLAN_EXISTS.toString()+",不可删除！");
        }
        doctorWorkPlanScheduleDao.deleteByIds(removeList);
        removeList.forEach(scheduleId -> redisTemplate.delete(Constants.WORK_PLAN_SCHEDULE_KEY + scheduleId));
    }

    private void addSchedules(ArrayList<DoctorWorkPlanSchedule> addList) {
        if (addList == null || addList.isEmpty()) {
            return;
        }
        int workPlanId = addList.get(0).getWorkPlanId();
        String date = doctorWorkPlanScheduleDao.selectScheduleDate(workPlanId);
        for (DoctorWorkPlanSchedule schedule : addList) {
            doctorWorkPlanScheduleDao.insert(schedule);
            int id = schedule.getId();
            int slot = schedule.getSlot();
            String key = (String) Constants.WORK_PLAN_SCHEDULE_KEY + id;
            Map<String, Object> scheduleMap = BeanUtil.beanToMap(schedule);
            redisTemplate.opsForHash().putAll(key, scheduleMap);
            String time = Constants.APPOINTMENT_SLOT.get(String.valueOf(slot));
            Date expirationTime = DateUtil.parse(date + " " + time);
            redisTemplate.expireAt(key, expirationTime);
        }
    }

    @Override
    @Transactional
    public void deleteWorkPlan(Integer workPlanId) {
        try {
            long num = doctorWorkPlanScheduleDao.selectNumByWorkPlanId(workPlanId);
            if (num != 0) {
                throw new GlobalException(OperationMessage.PATIENT_REGISTRATION_EXISTS.toString()+",不可删除！");
            }
            //问题：这个步骤放在doctorWorkPlanScheduleDao.deleteScheduleByWorkPlanId(workPlanId);后面会不执行
            doctorWorkPlanScheduleDao.deletePlanByWorkPlanId(workPlanId);
            ArrayList<Integer> scheduleIds = doctorWorkPlanScheduleDao.selectScheduleIdsByWorkPlanId(workPlanId);
            try {
                for (Integer scheduleId : scheduleIds) {
                    if (scheduleId != null) {
                        String key = WORK_PLAN_SCHEDULE_KEY + scheduleId;
                        redisTemplate.delete(key);
                    }
                }
            } catch (Exception e) {
                log.error("删除redis缓存失败!");
            }
            doctorWorkPlanScheduleDao.deleteScheduleByWorkPlanId(workPlanId);
            eventPublisher.publishAfterCommit(buildScheduleEvent("schedule.suspended", workPlanId, listToSlots(scheduleIds)));
        } catch (GlobalException e) {
            throw new GlobalException("删除失败！"+ e.getMessage());
        }
    }

    private ArrayList<DoctorScheduleSlotVO> listToSlots(ArrayList<Integer> scheduleIds) {
        ArrayList<DoctorScheduleSlotVO> slots = new ArrayList<>();
        if (scheduleIds == null) {
            return slots;
        }
        scheduleIds.forEach(id -> {
            DoctorScheduleSlotVO slot = new DoctorScheduleSlotVO();
            slot.setScheduleId(id);
            slots.add(slot);
        });
        return slots;
    }

    private HmsDomainEvent<ScheduleEventPayload> buildScheduleEvent(
            String eventType, Integer workPlanId, List<DoctorScheduleSlotVO> slots) {
        List<Integer> scheduleIds = slots == null
                ? Collections.emptyList()
                : slots.stream()
                .map(DoctorScheduleSlotVO::getScheduleId)
                .filter(Objects::nonNull)
                .collect(Collectors.toList());
        return new HmsDomainEvent<>(
                UUID.randomUUID().toString(),
                eventType,
                Instant.now(),
                UUID.randomUUID().toString(),
                "system",
                null,
                new ScheduleEventPayload(workPlanId, scheduleIds, eventType, Collections.emptyMap(), Collections.emptyMap(), Collections.emptyList())
        );
    }
}
