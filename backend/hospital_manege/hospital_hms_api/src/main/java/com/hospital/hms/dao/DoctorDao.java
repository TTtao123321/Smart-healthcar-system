package com.hospital.hms.dao;

import com.hospital.hms.pojo.Doctor;
import org.springframework.stereotype.Repository;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Repository
public interface DoctorDao {
    /**
     *
     * @param map
     * @return
     */
    Long selectConditionByPageCount(Map<String, Object> map);

    /**
     *
     * @param map
     * @return
     */
    List<HashMap<String, Object>> selectConditionByPage(Map<String, Object> map);

    /**
     *
     * @param doctor
     */
    void insert(Doctor doctor);

    /**
     *
     * @param id
     * @return
     */
    HashMap selectById(Integer id);

    /**
     *
     * @param param
     */
    void update(Map<String, Object> param);

    /**
     *
     * @param ids
     */
    void deleteByIds(Integer[] ids);

    /**
     *
     * @param deptSubId
     * @return
     */
    ArrayList<HashMap> selectDoctorsBySubId(Integer deptSubId);

    /**
     *
     * @param updateParams
     */
    void updatePicture(HashMap<String, Object> updateParams);

    /**
     *
     * @param id
     * @return
     */
    HashMap selectDoctorDetailById(Integer id);
}
