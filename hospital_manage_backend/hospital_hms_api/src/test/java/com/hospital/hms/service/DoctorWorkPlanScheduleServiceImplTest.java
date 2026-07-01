package com.hospital.hms.service;

import com.hospital.hms.controller.form.DoctorScheduleSlotVO;
import com.hospital.hms.event.HmsDomainEventPublisher;
import com.hospital.hms.event.ScheduleEventPayload;
import com.hospital.hms.service.impl.DoctorWorkPlanScheduleServiceImpl;
import com.hospital.hms.dao.DoctorWorkPlanScheduleDao;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.redis.core.RedisTemplate;

import java.util.ArrayList;
import java.util.HashMap;

import static org.mockito.ArgumentMatchers.argThat;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
public class DoctorWorkPlanScheduleServiceImplTest {

    @Mock
    private DoctorWorkPlanScheduleDao doctorWorkPlanScheduleDao;

    @Mock
    private RedisTemplate redisTemplate;

    @Mock
    private HmsDomainEventPublisher eventPublisher;

    @InjectMocks
    private DoctorWorkPlanScheduleServiceImpl doctorWorkPlanScheduleService;

    @Test
    @DisplayName("updateSchedule_修改排班后发布更新事件")
    void updateSchedule_修改排班后发布更新事件() {
        DoctorScheduleSlotVO slot = new DoctorScheduleSlotVO();
        slot.setScheduleId(11);
        slot.setSlot(2);
        slot.setMaximum(5);
        slot.setOperate("delete");
        ArrayList<DoctorScheduleSlotVO> slots = new ArrayList<>();
        slots.add(slot);

        HashMap<String, Object> param = new HashMap<>();
        param.put("workPlanId", 8);
        param.put("maximum", 10);
        param.put("slots", slots);

        when(doctorWorkPlanScheduleDao.selectSumNumByIds(argThat(ids -> ids.size() == 1 && ids.contains(11)))).thenReturn(0L);

        doctorWorkPlanScheduleService.updateSchedule(param);

        verify(eventPublisher).publishAfterCommit(argThat(event ->
                "schedule.updated".equals(event.eventType())
                        && event.payload() instanceof ScheduleEventPayload
                        && ((ScheduleEventPayload) event.payload()).getWorkPlanId().equals(8)
        ));
    }

    @Test
    @DisplayName("deleteWorkPlan_删除排班后发布停诊事件")
    void deleteWorkPlan_删除排班后发布停诊事件() {
        when(doctorWorkPlanScheduleDao.selectNumByWorkPlanId(8)).thenReturn(0L);
        when(doctorWorkPlanScheduleDao.selectScheduleIdsByWorkPlanId(8)).thenReturn(new ArrayList<>());

        doctorWorkPlanScheduleService.deleteWorkPlan(8);

        verify(eventPublisher).publishAfterCommit(argThat(event ->
                "schedule.suspended".equals(event.eventType())
                        && event.payload() instanceof ScheduleEventPayload
                        && ((ScheduleEventPayload) event.payload()).getWorkPlanId().equals(8)
        ));
    }
}
