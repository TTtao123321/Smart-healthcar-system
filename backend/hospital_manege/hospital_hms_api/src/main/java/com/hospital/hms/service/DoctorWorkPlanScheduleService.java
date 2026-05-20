package com.hospital.hms.service;

import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

@Service
public interface DoctorWorkPlanScheduleService {
    /**
     *
     * @param map
     * @return
     */
    ArrayList<HashMap> selectDoctorScheduleByDeptSubIdAndDate(Map<String, Object> map);

    /**
     *
     * @param workPlanId
     * @return
     */
    HashMap selectScheduleByWorkPlanId(Integer workPlanId);

    /**
     *
     * @param map
     */
    void updateSchedule(Map<String, Object> map);

    /**
     *
     * @param workPlanId
     */
    void deleteWorkPlan(Integer workPlanId);
}
