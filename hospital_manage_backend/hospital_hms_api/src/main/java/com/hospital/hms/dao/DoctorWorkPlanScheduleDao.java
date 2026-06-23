package com.hospital.hms.dao;

import com.hospital.hms.pojo.DoctorWorkPlanSchedule;
import org.springframework.stereotype.Repository;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

@Repository
public interface DoctorWorkPlanScheduleDao {
    /**
     *
     * @param schedule
     */
    void insert(DoctorWorkPlanSchedule schedule);

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
    ArrayList<HashMap> selectScheduleByWorkPlanId(Integer workPlanId);

    /**
     *
     * @param map
     */
    void updateMaximum(Map<String, Object> map);

    /**
     *
     * @param workPlanId
     * @return
     */
    String selectScheduleDate(int workPlanId);

    /**
     *
     * @param removeList
     * @return
     */
    long selectSumNumByIds(ArrayList<Integer> removeList);

    /**
     *
     * @param removeList
     */
    void deleteByIds(ArrayList<Integer> removeList);

    /**
     *
     * @param workPlanId
     * @return
     */
    long selectNumByWorkPlanId(Integer workPlanId);

    /**
     *
     * @param workPlanId
     */
    void deletePlanByWorkPlanId(Integer workPlanId);

    /**
     *
     * @param workPlanId
     */
    void deleteScheduleByWorkPlanId(Integer workPlanId);

    /**
     *
     * @param workPlanId
     * @return
     */
    ArrayList<Integer> selectScheduleIdsByWorkPlanId(Integer workPlanId);
}
