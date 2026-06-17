package com.hospital.hms.service;

import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.Collection;
import java.util.HashMap;
import java.util.Map;

@Service
public interface DoctorWorkPlanService {
    /**
     * @param map
     * @param dateList
     * @return
     */
    Collection<HashMap> selectWorkPlanByTime(Map<String, Object> map, ArrayList<String> dateList);

    /**
     *
     * @param startDate
     * @param endDate
     * @param b
     * @return
     */
    ArrayList<String> getDateList(String startDate, String endDate, boolean b);

    /**
     * @param map
     * @return
     */
    String insert(Map<String, Object> map);
}
