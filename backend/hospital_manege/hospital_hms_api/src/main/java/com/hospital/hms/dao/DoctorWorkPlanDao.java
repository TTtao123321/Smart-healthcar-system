package com.hospital.hms.dao;

import com.hospital.hms.pojo.DoctorWorkPlan;
import org.springframework.stereotype.Repository;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

@Repository
public interface DoctorWorkPlanDao {
    /**
     *
     * @param map
     * @return
     */
    ArrayList<HashMap> selectWorkPlanByTime(Map<String, Object> map);

    /**
     *
     * @param map
     * @return
     */
    Integer selectWorkPlanToday(Map<String, Object> map);

    /**
     *
     * @param map
     */
    void insert(DoctorWorkPlan map);
}
